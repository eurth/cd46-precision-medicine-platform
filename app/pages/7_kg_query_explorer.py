"""
Page 7 — Knowledge Graph Query Explorer.

A live research interface to the AuraDB knowledge graph.
Three modes:
  1. Visual Query Builder — pre-built templates with dropdowns
  2. Cypher Editor — write and run raw Cypher
  3. Natural Language → Cypher — ask a question, LLM translates to Cypher + runs it

Shows results as tables, metric cards, and optionally a Plotly network graph.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import os
import json
import time
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from components.styles import inject_global_css, page_hero
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[2] / ".env")

for _k in ("NEO4J_URI", "NEO4J_USERNAME", "NEO4J_PASSWORD", "OPENAI_API_KEY", "GEMINI_API_KEY"):
    try:
        if _k in st.secrets and not os.environ.get(_k):
            os.environ[_k] = st.secrets[_k]
    except Exception:
        pass

# ---------------------------------------------------------------------------
# AuraDB connection
# ---------------------------------------------------------------------------

@st.cache_resource(ttl=300)
def get_driver():
    from neo4j import GraphDatabase
    uri  = os.environ.get("NEO4J_URI", "")
    user = os.environ.get("NEO4J_USERNAME", "neo4j")
    pwd  = os.environ.get("NEO4J_PASSWORD", "")
    if not uri or not pwd:
        return None
    return GraphDatabase.driver(uri, auth=(user, pwd))


def run_cypher(cypher: str, params: dict | None = None) -> list[dict]:
    """Execute Cypher and return list of row dicts."""
    driver = get_driver()
    if driver is None:
        return []
    try:
        with driver.session() as s:
            result = s.run(cypher, **(params or {}))
            return [dict(r) for r in result]
    except Exception as e:
        st.error(f"Cypher error: {e}")
        return []


def get_schema() -> dict:
    """Return dict of {label: [properties], ...} and relationship types."""
    driver = get_driver()
    if driver is None:
        return {}
    with driver.session() as s:
        labels = [r["label"] for r in s.run("CALL db.labels() YIELD label RETURN label ORDER BY label")]
        rel_types = [r["relationshipType"] for r in s.run("CALL db.relationshipTypes() YIELD relationshipType RETURN relationshipType ORDER BY relationshipType")]
        counts = {}
        for lbl in labels:
            c = s.run(f"MATCH (n:`{lbl}`) RETURN count(n) AS c").single()["c"]
            counts[lbl] = c
    return {"labels": labels, "rel_types": rel_types, "counts": counts}

# ---------------------------------------------------------------------------
# Pre-built query templates
# ---------------------------------------------------------------------------

QUERY_TEMPLATES = {
    "🎯 CD46 expression: Which cancers have highest CD46?": {
        "description": "Lists all Disease nodes sorted by CD46 median TPM, showing the top targets.",
        "cypher": """
MATCH (d:Disease)
WHERE d.cd46_median_tpm_log2 IS NOT NULL
RETURN d.tcga_code AS cancer_type,
       round(d.cd46_median_tpm_log2, 3) AS cd46_median_log2,
       d.tcga_sample_count AS n_samples,
       d.cd46_prognostic AS prognostic_significance
ORDER BY d.cd46_median_tpm_log2 DESC
LIMIT 25
""",
        "params": {},
    },
    "📈 Survival impact: Which cancers show CD46-High = worse prognosis?": {
        "description": "SurvivalResult nodes with HR > 1.0 and p < 0.05. High CD46 = worse survival.",
        "cypher": """
MATCH (d:Disease)-[:HAS_SURVIVAL_RESULT]->(sr:SurvivalResult)
WHERE sr.hazard_ratio > 1.0
  AND sr.p_value < 0.05
  AND sr.endpoint = 'OS'
RETURN d.tcga_code AS cancer,
       round(sr.hazard_ratio, 3) AS hazard_ratio,
       round(sr.p_value, 5) AS p_value,
       sr.n_high AS n_cd46_high,
       sr.n_low AS n_cd46_low
ORDER BY sr.hazard_ratio DESC
""",
        "params": {},
    },
    "📚 Publications: What evidence supports CD46 as a target in PRAD?": {
        "description": "Publications linked to PRAD via SUPPORTS relationship.",
        "cypher": """
MATCH (pub:Publication)-[:SUPPORTS]->(d:Disease {tcga_code: 'PRAD'})
RETURN pub.title AS title,
       pub.authors AS authors,
       pub.journal AS journal,
       pub.year AS year,
       pub.evidence_type AS evidence_type,
       pub.pubmed_id AS pmid
ORDER BY pub.year DESC
""",
        "params": {},
    },
    "💊 Drugs: Which therapies target CD46-expressing cancers?": {
        "description": "Drugs indicated for diseases where CD46 is overexpressed.",
        "cypher": """
MATCH (drug:Drug)-[:INDICATED_FOR]->(d:Disease)
OPTIONAL MATCH (d)-[:HAS_SURVIVAL_RESULT]->(sr:SurvivalResult {endpoint: 'OS'})
RETURN drug.name AS drug,
       drug.drug_type AS type,
       drug.payload AS payload,
       drug.developer AS developer,
       d.tcga_code AS cancer,
       d.cd46_median_tpm_log2 AS cd46_expression,
       CASE WHEN sr IS NOT NULL THEN round(sr.hazard_ratio, 3) ELSE null END AS hr_cd46_high
ORDER BY d.cd46_median_tpm_log2 DESC
""",
        "params": {},
    },
    "🧪 Clinical Trials: What trials are investigating CD46 targets?": {
        "description": "All ClinicalTrial nodes with their investigational diseases.",
        "cypher": """
MATCH (t:ClinicalTrial)-[:INVESTIGATES]->(d:Disease)
RETURN t.nct_id AS nct_id,
       t.phase AS phase,
       t.sponsor AS sponsor,
       t.status AS status,
       d.tcga_code AS cancer,
       t.target AS target,
       t.updated_at AS last_updated
ORDER BY t.phase
""",
        "params": {},
    },
    "🔬 Co-expression: Which genes correlate with CD46 in PRAD?": {
        "description": "Genes with Spearman correlations to CD46 in PRAD cohort.",
        "cypher": """
MATCH (cd46:Gene {symbol: 'CD46'})-[r:CORRELATED_WITH]->(g:Gene)
RETURN g.symbol AS biomarker,
       g.name AS biomarker_name,
       round(r.spearman_rho, 4) AS spearman_rho,
       round(r.p_value, 6) AS p_value,
       r.cancer_type AS cancer_type,
       r.significant AS fdr_significant
ORDER BY abs(r.spearman_rho) DESC
""",
        "params": {},
    },
    "🧬 Protein: What is the CD46 protein network?": {
        "description": "CD46 protein properties and pathway memberships.",
        "cypher": """
MATCH (g:Gene {symbol: 'CD46'})
OPTIONAL MATCH (p:Protein {symbol: 'CD46'})
OPTIONAL MATCH (g)-[:PARTICIPATES_IN]->(pw:Pathway)
OPTIONAL MATCH (g)-[:ENCODES]->(prot:Protein)
RETURN g.symbol AS gene,
       g.chromosome AS chromosome,
       g.therapeutic_rationale AS rationale,
       p.molecular_weight_kda AS protein_mw_kda,
       p.surface_expressed AS surface_expressed,
       collect(DISTINCT pw.name) AS pathways
""",
        "params": {},
    },
    "🏥 Patient Groups: Which cancer-threshold combinations have most eligible patients?": {
        "description": "PatientGroup nodes sorted by eligible patient count with survival context.",
        "cypher": """
MATCH (pg:PatientGroup)-[:HAS_SURVIVAL_DATA]->(sr:SurvivalResult)
WHERE pg.expression_group = 'CD46_High'
  AND sr.endpoint = 'OS'
  AND pg.n_eligible > 50
RETURN pg.cancer_type AS cancer,
       pg.threshold_method AS method,
       round(pg.threshold_value, 2) AS threshold,
       pg.n_eligible AS n_eligible,
       pg.n_total AS n_total,
       round(toFloat(pg.n_eligible) / pg.n_total * 100, 1) AS pct_eligible,
       round(sr.hazard_ratio, 3) AS hr_cd46_high_vs_low,
       sr.significant AS significant
ORDER BY pg.n_eligible DESC
LIMIT 20
""",
        "params": {},
    },
    "🔗 Full path: Gene → Pathway → Disease evidence chain": {
        "description": "Multi-hop path from CD46 gene through complement pathway to supported diseases.",
        "cypher": """
MATCH path = (g:Gene {symbol: 'CD46'})-[:PARTICIPATES_IN]->(pw:Pathway)
MATCH (pub:Publication)-[:SUPPORTS]->(d:Disease)
MATCH (d)-[:HAS_SURVIVAL_RESULT]->(sr:SurvivalResult {endpoint: 'OS'})
WHERE sr.significant = true
RETURN g.symbol AS gene,
       pw.name AS pathway,
       d.tcga_code AS disease,
       round(d.cd46_median_tpm_log2, 3) AS cd46_expression,
       round(sr.hazard_ratio, 3) AS hazard_ratio,
       count(DISTINCT pub) AS n_supporting_pubs
ORDER BY sr.hazard_ratio DESC
""",
        "params": {},
    },
    "📊 Cell lines: Which cancer cell lines depend on CD46?": {
        "description": "DepMap cell lines where CD46 is a dependency (CRISPR score < -0.5).",
        "cypher": """
MATCH (cl:CellLine)
WHERE cl.cd46_is_dependency = true
RETURN cl.name AS cell_line,
       cl.cancer_type AS cancer_type,
       round(cl.cd46_crispr_score, 4) AS crispr_score,
       round(cl.cd46_expression_tpm, 3) AS cd46_expression_tpm
ORDER BY cl.cd46_crispr_score
LIMIT 30
""",
        "params": {},
    },
}

# ---------------------------------------------------------------------------
# Page layout
# ---------------------------------------------------------------------------

inject_global_css()

st.markdown(
    page_hero(
        icon="🔍",
        module_name="KG Query Explorer",
        purpose="Live research interface to the CD46 AuraDB knowledge graph · pre-built queries · Cypher editor · natural language → Cypher",
        kpi_chips=[
            ("Query Templates", "10"),
            ("KG Nodes", "3,047"),
            ("Node Labels", "12"),
            ("Rel Types", "15+"),
        ],
        source_badges=["UniProt", "OpenTargets", "ClinicalTrials", "STRING"],
    ),
    unsafe_allow_html=True,
)

driver = get_driver()
if driver is None:
    st.error("⚠️ NEO4J_URI / NEO4J_PASSWORD not configured. Set in .env or Streamlit Cloud secrets.")
    st.stop()

# Schema sidebar summary
with st.sidebar:
    st.markdown("---")
    st.markdown("**🗄️ Knowledge Graph Schema**")
    try:
        schema = get_schema()
        for lbl in schema.get("labels", []):
            cnt = schema["counts"].get(lbl, 0)
            st.markdown(f"<span style='color:#38bdf8;'>●</span> `{lbl}`: **{cnt:,}**", unsafe_allow_html=True)
        st.markdown("**Relationship types:**")
        for rt in schema.get("rel_types", []):
            st.markdown(f"<span style='color:#4ade80;'>→</span> `{rt}`", unsafe_allow_html=True)
    except Exception:
        st.markdown("*Connect to graph to view schema*")

# Tabs
tab_builder, tab_cypher, tab_nl, tab_graph = st.tabs([
    "📋 Query Templates",
    "💻 Cypher Editor",
    "🤖 Natural Language",
    "🕸️ Graph Visualizer",
])

# ===========================================================================
# TAB 1 — QUERY TEMPLATES
# ===========================================================================
with tab_builder:
    st.markdown(
        "<div style='background:#1e293b;border-left:3px solid #38bdf8;padding:12px 16px;"
        "border-radius:6px;margin-bottom:14px;'>"
        "<b style='color:#38bdf8;'>Pre-Built Research Queries</b><br>"
        "<span style='color:#94a3b8;'>10 curated Cypher queries covering the key research questions. "
        "Select → run → see results. Designed to reveal the most clinically important graph patterns.</span>"
        "</div>",
        unsafe_allow_html=True,
    )

    selected_q = st.selectbox(
        "Choose a research question:",
        options=list(QUERY_TEMPLATES.keys()),
        index=0,
    )

    tpl = QUERY_TEMPLATES[selected_q]
    st.markdown(f"**What this query does:** {tpl['description']}")

    with st.expander("View Cypher", expanded=False):
        st.code(tpl["cypher"].strip(), language="cypher")

    c1, c2, c3 = st.columns([1, 1, 4])
    run_tpl = c1.button("▶️ Run Query", type="primary", key="run_tpl")
    if c2.button("📋 Copy to Editor", key="copy_tpl"):
        st.session_state["cypher_editor"] = tpl["cypher"].strip()
        st.info("Query copied to Cypher Editor tab.")

    if run_tpl:
        with st.spinner("Querying AuraDB..."):
            t0 = time.time()
            rows = run_cypher(tpl["cypher"], tpl.get("params", {}))
            elapsed = time.time() - t0

        if rows:
            st.success(f"✅ {len(rows)} results in {elapsed:.2f}s")
            df_result = pd.DataFrame(rows)

            # Metrics row for numeric-heavy results
            numeric_cols = df_result.select_dtypes(include="number").columns.tolist()
            if numeric_cols and len(df_result) > 1:
                ncols = min(len(numeric_cols), 4)
                metric_cols = st.columns(ncols)
                for i, col in enumerate(numeric_cols[:ncols]):
                    val = df_result[col].iloc[0]
                    metric_cols[i].metric(col.replace("_", " ").title(), f"{val:.3f}" if isinstance(val, float) else str(val))

            st.dataframe(df_result, use_container_width=True, hide_index=True)

            # Download button
            st.download_button(
                "📥 Download CSV",
                df_result.to_csv(index=False),
                f"kg_query_{int(time.time())}.csv",
                "text/csv",
                key="dl_tpl",
            )

            # Auto-plot if result has a good chart structure
            if "cancer" in df_result.columns and len(numeric_cols) >= 1:
                chart_col = next((c for c in ["hazard_ratio", "cd46_expression", "cd46_median_log2", "n_eligible", "crispr_score"] if c in df_result.columns), numeric_cols[0])
                with st.expander("📊 Quick Chart", expanded=True):
                    fig = go.Figure(go.Bar(
                        x=df_result["cancer"] if "cancer" in df_result.columns else df_result.iloc[:, 0],
                        y=df_result[chart_col],
                        marker_color="#38bdf8",
                        text=df_result[chart_col].round(3).astype(str),
                        textposition="outside",
                    ))
                    fig.update_layout(
                        height=350, paper_bgcolor="#0f172a", plot_bgcolor="#0f172a",
                        xaxis=dict(color="#94a3b8"),
                        yaxis=dict(title=chart_col.replace("_", " "), color="#94a3b8", gridcolor="#1e293b"),
                        margin=dict(l=10, r=10, t=30, b=10),
                    )
                    st.plotly_chart(fig, width='stretch')
        else:
            st.info("No results returned — the graph may not have matching nodes yet, or the query returned empty results.")

# ===========================================================================
# TAB 2 — CYPHER EDITOR
# ===========================================================================
with tab_cypher:
    st.markdown(
        "<div style='background:#1e293b;border-left:3px solid #4ade80;padding:12px 16px;"
        "border-radius:6px;margin-bottom:14px;'>"
        "<b style='color:#4ade80;'>Direct Cypher Query Editor</b><br>"
        "<span style='color:#94a3b8;'>Write any Cypher query against the live AuraDB instance. "
        "Use MATCH, WHERE, RETURN. CREATE/DELETE/MERGE are allowed for power users.</span>"
        "</div>",
        unsafe_allow_html=True,
    )

    # Schema quick reference
    with st.expander("📖 Schema Quick Reference"):
        st.markdown("""
| Node Label | Key Properties | Count |
|---|---|---|
| `Disease` | `tcga_code`, `cd46_median_tpm_log2`, `cd46_prognostic` | 25 |
| `SurvivalResult` | `cancer_type`, `endpoint`, `hazard_ratio`, `p_value`, `significant` | 53 |
| `Publication` | `pubmed_id`, `title`, `year`, `evidence_type` | 8 |
| `ClinicalTrial` | `nct_id`, `phase`, `sponsor`, `status` | 14 |
| `PatientGroup` | `cancer_type`, `expression_group`, `n_eligible`, `threshold_value` | 200 |
| `Drug` | `name`, `drug_type`, `payload`, `developer` | 3 |
| `Gene` | `symbol`, `chromosome`, `therapeutic_rationale` | 2+ |
| `Protein` | `symbol`, `molecular_weight_kda`, `surface_expressed` | 4 |
| `Pathway` | `name`, `reactome_id`, `go_id` | 3 |
| `CellLine` | `name`, `cancer_type`, `cd46_crispr_score`, `cd46_is_dependency` | 1,186 |
| `Tissue` | `name`, `type`, `staining_intensity` | 24 |

**Relationships:** `HAS_SURVIVAL_RESULT` · `HAS_PATIENT_GROUP` · `SUPPORTS` · `INDICATED_FOR` · `INVESTIGATES` · `PARTICIPATES_IN` · `CORRELATED_WITH` · `EXPRESSED_IN` · `ENCODES` · `HAS_SURVIVAL_DATA` · `DEPENDS_ON`
        """)

    default_cypher = st.session_state.get("cypher_editor", """// Example: Find CD46-high cancers with significant OS impact
MATCH (d:Disease)-[:HAS_SURVIVAL_RESULT]->(sr:SurvivalResult {endpoint: 'OS'})
WHERE sr.hazard_ratio > 1.0 AND sr.significant = true
RETURN d.tcga_code AS cancer,
       d.cd46_median_tpm_log2 AS cd46_expression,
       sr.hazard_ratio AS hr,
       sr.p_value AS p_value
ORDER BY sr.hazard_ratio DESC""")

    cypher_input = st.text_area(
        "Cypher Query:",
        value=default_cypher,
        height=200,
        key="cypher_txt",
        help="Write valid Cypher. Use backtick-quoted labels for labels with spaces.",
    )

    col_run, col_explain, col_clear = st.columns([1, 1, 1])
    run_cypher_btn = col_run.button("▶️ Run", type="primary", key="run_cypher_btn")
    explain_btn    = col_explain.button("🔍 Explain Plan", key="explain_btn")

    if run_cypher_btn and cypher_input.strip():
        with st.spinner("Running..."):
            t0 = time.time()
            rows = run_cypher(cypher_input)
            elapsed = time.time() - t0
        if rows:
            st.success(f"✅ {len(rows)} rows · {elapsed:.2f}s")
            df_cyp = pd.DataFrame(rows)
            st.dataframe(df_cyp, use_container_width=True, hide_index=True)
            st.download_button(
                "📥 Download CSV",
                df_cyp.to_csv(index=False),
                f"cypher_result_{int(time.time())}.csv",
                "text/csv",
                key="dl_cyp",
            )
        else:
            st.info("Query returned no results.")

    if explain_btn and cypher_input.strip():
        rows = run_cypher(f"EXPLAIN {cypher_input}")
        if rows:
            st.json(rows)

    # History / saved queries
    if "query_history" not in st.session_state:
        st.session_state["query_history"] = []

    if run_cypher_btn and cypher_input.strip():
        st.session_state["query_history"].insert(0, {"query": cypher_input, "ts": time.strftime("%H:%M:%S")})
        st.session_state["query_history"] = st.session_state["query_history"][:10]

    if st.session_state["query_history"]:
        with st.expander("🕐 Recent Queries"):
            for i, h in enumerate(st.session_state["query_history"][:5]):
                st.markdown(f"**{h['ts']}**")
                st.code(h["query"][:300] + ("..." if len(h["query"]) > 300 else ""), language="cypher")
                if st.button(f"Re-run", key=f"rerun_{i}"):
                    st.session_state["cypher_editor"] = h["query"]

# ===========================================================================
# TAB 3 — NATURAL LANGUAGE → CYPHER
# ===========================================================================
with tab_nl:
    st.markdown(
        "<div style='background:#1e293b;border-left:3px solid #fbbf24;padding:12px 16px;"
        "border-radius:6px;margin-bottom:14px;'>"
        "<b style='color:#fbbf24;'>Natural Language → Cypher Translation</b><br>"
        "<span style='color:#94a3b8;'>Ask research questions in plain English. "
        "The AI translates to Cypher, runs it against AuraDB, and explains the results. "
        "Powered by the CD46 research assistant.</span>"
        "</div>",
        unsafe_allow_html=True,
    )

    EXAMPLE_NL_QUERIES = [
        "Which cancers have CD46 expression above the pan-cancer median and also show worse overall survival for CD46-high patients?",
        "Show me all clinical trials for prostate cancer and the hazard ratio for CD46 in PRAD",
        "Which publications support CD46 as a therapeutic target in bladder cancer?",
        "What cell lines have the highest dependency on CD46 based on CRISPR screens?",
        "Which drugs are being developed for cancers where CD46 is overexpressed?",
        "Show the complete evidence chain from CD46 gene through complement pathway to supported diseases",
    ]

    nl_example = st.selectbox("Example questions:", ["(type your own below)"] + EXAMPLE_NL_QUERIES)
    nl_question = st.text_area(
        "Your research question:",
        value="" if nl_example == "(type your own below)" else nl_example,
        height=100,
        key="nl_q",
        placeholder="e.g. Which cancers show CD46-high patients have significantly worse survival?",
    )

    SCHEMA_CONTEXT = """
AuraDB Neo4j Knowledge Graph Schema:
Nodes: Disease (tcga_code, cd46_median_tpm_log2, cd46_prognostic), 
       SurvivalResult (cancer_type, endpoint, hazard_ratio, p_value, significant, n_high, n_low),
       Publication (pubmed_id, title, year, evidence_type, journal, authors),
       ClinicalTrial (nct_id, phase, sponsor, status, target),
       PatientGroup (cancer_type, expression_group, n_eligible, n_total, threshold_value),
       Drug (name, drug_type, payload, developer),
       Gene (symbol, chromosome, therapeutic_rationale),
       Protein (symbol, molecular_weight_kda, surface_expressed),
       Pathway (name, reactome_id, go_id),
       CellLine (name, cancer_type, cd46_crispr_score, cd46_is_dependency, cd46_expression_tpm),
       Tissue (name, type, staining_intensity)
Relationships: HAS_SURVIVAL_RESULT, HAS_PATIENT_GROUP, SUPPORTS (pub→disease), 
               INDICATED_FOR (drug→disease), INVESTIGATES (trial→disease),
               PARTICIPATES_IN (gene→pathway), CORRELATED_WITH (gene→gene),
               EXPRESSED_IN, ENCODES, HAS_SURVIVAL_DATA, DEPENDS_ON
"""

    run_nl = st.button("🤖 Translate & Run", type="primary", key="run_nl")
    if run_nl and nl_question.strip():
        with st.spinner("Translating to Cypher..."):
            try:
                # Try to use the orchestrator LLM
                from src.agent.orchestrator import CD46Agent
                @st.cache_resource
                def _get_kg_agent():
                    return CD46Agent()
                agent = _get_kg_agent()

                prompt = f"""You are a Neo4j Cypher expert. Convert the following research question into a valid Cypher query.

{SCHEMA_CONTEXT}

Research question: {nl_question}

Rules:
- Return ONLY the Cypher query, no explanation before it
- Start with MATCH or WITH
- Use backticks only if property names have spaces
- Return meaningful column aliases
- LIMIT to 50 rows unless asked for all
- After the Cypher, add two newlines then write "## Explanation:" and one sentence describing what the query does

Cypher:"""

                full_response = ""
                for token in agent.stream(prompt):
                    full_response += token

                # Parse cypher vs explanation
                if "## Explanation:" in full_response:
                    cypher_part, explanation = full_response.split("## Explanation:", 1)
                else:
                    cypher_part = full_response
                    explanation = ""

                # Clean up cypher - remove markdown code blocks if present
                cypher_clean = cypher_part.strip()
                if cypher_clean.startswith("```"):
                    lines = cypher_clean.split("\n")
                    cypher_clean = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])
                cypher_clean = cypher_clean.replace("```cypher", "").replace("```", "").strip()

                st.markdown("**Generated Cypher:**")
                st.code(cypher_clean, language="cypher")
                if explanation:
                    st.markdown(f"**What this does:** {explanation.strip()}")

                col_nl1, col_nl2 = st.columns([1, 2])
                if col_nl1.button("▶️ Run this Cypher", key="run_nl_cypher"):
                    with st.spinner("Querying AuraDB..."):
                        rows = run_cypher(cypher_clean)
                    if rows:
                        st.success(f"✅ {len(rows)} results")
                        df_nl = pd.DataFrame(rows)
                        st.dataframe(df_nl, use_container_width=True, hide_index=True)
                        st.download_button("📥 CSV", df_nl.to_csv(index=False),
                                           f"nl_result_{int(time.time())}.csv", "text/csv", key="dl_nl")
                    else:
                        st.info("No results returned.")
                if col_nl2.button("📋 Copy to Cypher Editor", key="nl_to_editor"):
                    st.session_state["cypher_editor"] = cypher_clean
                    st.info("Copied to Cypher Editor tab.")

            except Exception as e:
                st.warning(f"AI translation unavailable: {e}. Using pattern matching instead.")
                # Fallback: simple keyword matching to pre-built queries
                q_lower = nl_question.lower()
                best_match = None
                for q_name, q_tpl in QUERY_TEMPLATES.items():
                    keywords = q_name.lower().split()
                    if any(kw in q_lower for kw in keywords):
                        best_match = q_tpl
                        st.info(f"Closest matching template: **{q_name}**")
                        break
                if best_match:
                    st.code(best_match["cypher"].strip(), language="cypher")
                else:
                    st.info("No matching template found. Try the Cypher Editor tab.")

# ===========================================================================
# TAB 4 — GRAPH VISUALIZER
# ===========================================================================
with tab_graph:
    st.markdown(
        "<div style='background:#1e293b;border-left:3px solid #818cf8;padding:12px 16px;"
        "border-radius:6px;margin-bottom:14px;'>"
        "<b style='color:#818cf8;'>Graph Network Visualizer</b><br>"
        "<span style='color:#94a3b8;'>Renders query results as an interactive network graph. "
        "Select a view preset or run a path query to see the relationship structure.</span>"
        "</div>",
        unsafe_allow_html=True,
    )

    GRAPH_PRESETS = {
        "CD46 Gene → Pathways → Diseases": """
MATCH (g:Gene {symbol:'CD46'})-[:PARTICIPATES_IN]->(pw:Pathway)
MATCH (pub:Publication)-[:SUPPORTS]->(d:Disease)
WHERE d.cd46_median_tpm_log2 > 12.5
RETURN g.symbol AS from_node, 'PARTICIPATES_IN' AS rel, pw.name AS to_node, 'Gene' AS from_type, 'Pathway' AS to_type
UNION
MATCH (pub:Publication)-[:SUPPORTS]->(d:Disease)
WHERE d.cd46_median_tpm_log2 > 12.5
RETURN pub.evidence_type AS from_node, 'SUPPORTS' AS rel, d.tcga_code AS to_node, 'Publication' AS from_type, 'Disease' AS to_type
LIMIT 40
""",
        "Drug → Disease → Survival network": """
MATCH (drug:Drug)-[:INDICATED_FOR]->(d:Disease)-[:HAS_SURVIVAL_RESULT]->(sr:SurvivalResult {endpoint:'OS'})
WHERE sr.significant = true
RETURN drug.name AS from_node, 'INDICATED_FOR' AS rel, d.tcga_code AS to_node, 'Drug' AS from_type, 'Disease' AS to_type
UNION
MATCH (drug:Drug)-[:INDICATED_FOR]->(d:Disease)-[:HAS_SURVIVAL_RESULT]->(sr:SurvivalResult {endpoint:'OS'})
WHERE sr.significant = true
RETURN d.tcga_code AS from_node, 'HAS_SURVIVAL_RESULT' AS rel, sr.label AS to_node, 'Disease' AS from_type, 'SurvivalResult' AS to_type
LIMIT 40
""",
        "Trial → Disease evidence web": """
MATCH (t:ClinicalTrial)-[:INVESTIGATES]->(d:Disease)
RETURN t.nct_id AS from_node, 'INVESTIGATES' AS rel, d.tcga_code AS to_node, 'ClinicalTrial' AS from_type, 'Disease' AS to_type
UNION
MATCH (pub:Publication)-[:SUPPORTS]->(d:Disease)
RETURN pub.pubmed_id AS from_node, 'SUPPORTS' AS rel, d.tcga_code AS to_node, 'Publication' AS from_type, 'Disease' AS to_type
LIMIT 50
""",
    }

    preset_sel = st.selectbox("Graph preset:", list(GRAPH_PRESETS.keys()))
    load_graph = st.button("🕸️ Load Graph", type="primary", key="load_graph")

    if load_graph:
        with st.spinner("Fetching graph data..."):
            rows = run_cypher(GRAPH_PRESETS[preset_sel])

        if rows:
            df_g = pd.DataFrame(rows)

            # Build Plotly network
            NODE_COLORS = {
                "Gene": "#f87171", "Disease": "#38bdf8", "Pathway": "#818cf8",
                "Publication": "#4ade80", "Drug": "#fb923c", "ClinicalTrial": "#fbbf24",
                "SurvivalResult": "#a78bfa", "PatientGroup": "#34d399",
            }

            all_nodes = {}
            for _, row in df_g.iterrows():
                for side in ["from_node", "to_node"]:
                    t_col = "from_type" if side == "from_node" else "to_type"
                    label = str(row[side])
                    ntype = row.get(t_col, "Unknown")
                    if label not in all_nodes:
                        all_nodes[label] = {"type": ntype, "degree": 0}
                    all_nodes[label]["degree"] += 1

            import math
            n_nodes = len(all_nodes)
            node_list = list(all_nodes.items())
            # Layout: circular
            angles = [2 * math.pi * i / max(n_nodes, 1) for i in range(n_nodes)]
            node_pos = {label: (math.cos(a) * 2, math.sin(a) * 2) for (label, _), a in zip(node_list, angles)}

            # Edges
            edge_x, edge_y = [], []
            for _, row in df_g.iterrows():
                x0, y0 = node_pos.get(str(row["from_node"]), (0, 0))
                x1, y1 = node_pos.get(str(row["to_node"]), (0, 0))
                edge_x += [x0, x1, None]
                edge_y += [y0, y1, None]

            fig_g = go.Figure()
            fig_g.add_trace(go.Scatter(
                x=edge_x, y=edge_y, mode="lines",
                line=dict(width=1, color="#334155"),
                hoverinfo="none", showlegend=False,
            ))

            for ntype, color in NODE_COLORS.items():
                nodes_of_type = [(lbl, pos) for lbl, pos in node_pos.items()
                                 if all_nodes.get(lbl, {}).get("type") == ntype]
                if not nodes_of_type:
                    continue
                lbs = [n[0] for n in nodes_of_type]
                xs  = [n[1][0] for n in nodes_of_type]
                ys  = [n[1][1] for n in nodes_of_type]
                sizes = [max(12, min(30, all_nodes[l]["degree"] * 5)) for l in lbs]

                fig_g.add_trace(go.Scatter(
                    x=xs, y=ys, mode="markers+text",
                    marker=dict(size=sizes, color=color, line=dict(width=1.5, color="#0f172a")),
                    text=[l[:20] for l in lbs],
                    textposition="top center",
                    textfont=dict(size=8, color="#e2e8f0"),
                    name=ntype,
                    hovertext=lbs,
                    hoverinfo="text",
                ))

            fig_g.update_layout(
                height=500, paper_bgcolor="#0f172a", plot_bgcolor="#0f172a",
                xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                legend=dict(bgcolor="#1e293b", font=dict(color="#e2e8f0")),
                margin=dict(l=10, r=10, t=10, b=10),
                title=dict(text=f"Graph: {preset_sel}", font=dict(color="#e2e8f0", size=13)),
            )
            st.plotly_chart(fig_g, width='stretch')
            st.caption(f"Rendering {n_nodes} nodes and {len(df_g)} edges from AuraDB · Node size = degree")
            st.dataframe(df_g, use_container_width=True, hide_index=True)
        else:
            st.info("No graph data returned.")

st.markdown("---")
st.markdown(
    "<div style='color:#64748b;font-size:0.78em;'>AuraDB: 3,047 nodes · 2,552 relationships · "
    "Labels: Disease, SurvivalResult, Publication, ClinicalTrial, PatientGroup, Drug, Gene, Protein, Pathway, CellLine, Tissue · "
    "Read/Write access · Research use only.</div>",
    unsafe_allow_html=True,
)
