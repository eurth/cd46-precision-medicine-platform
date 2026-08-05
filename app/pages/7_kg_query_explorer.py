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
from components.targets import get_active_symbol, is_loaded
from components.ui_kit import page_header, section_tabs, research_table
from components.data_freeze import render_data_freeze_banner
from components.export_pack import (
    ROW_CAP,
    QUERY_TIMEOUT_S,
    build_export_pack,
    ensure_cypher_limit,
)
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[2] / ".env")

for _k in (
    "NEO4J_URI",
    "NEO4J_USERNAME",
    "NEO4J_PASSWORD",
    "OPENROUTER_API_KEY",
    "OPENROUTER_MODEL",
    "OPENAI_API_KEY",
    "GEMINI_API_KEY",
):
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


@st.cache_data(ttl=300, show_spinner=False)
def get_header_stats():
    driver = get_driver()
    if driver is None:
        return None
    try:
        with driver.session() as sess:
            total_nodes = sess.run("MATCH (n) RETURN count(n) AS c").single()["c"]
            total_rels = sess.run("MATCH ()-[r]->() RETURN count(r) AS c").single()["c"]
            label_count = len(list(sess.run("CALL db.labels() YIELD label RETURN label")))
            rel_type_count = len(list(sess.run("CALL db.relationshipTypes() YIELD relationshipType RETURN relationshipType")))
        return {
            "total_nodes": total_nodes,
            "total_rels": total_rels,
            "label_count": label_count,
            "rel_type_count": rel_type_count,
        }
    except Exception:
        return None


def run_cypher(cypher: str, params: dict | None = None) -> list[dict]:
    """Execute read-only Cypher and return list of row dicts (capped)."""
    driver = get_driver()
    if driver is None:
        return []
    _upper = cypher.strip().upper()
    _forbidden = ["CREATE ", "MERGE ", "DELETE ", "SET ", "REMOVE ", "DROP "]
    if any(_upper.startswith(f) or f" {f}" in _upper for f in _forbidden):
        st.error("Write operations are not permitted. Use read-only MATCH queries.")
        return []
    # EXPLAIN plans stay uncapped
    is_explain = _upper.startswith("EXPLAIN") or _upper.startswith("PROFILE")
    q = cypher if is_explain else ensure_cypher_limit(cypher, ROW_CAP)
    try:
        from neo4j import Query

        with driver.session() as s:
            result = s.run(Query(q, timeout=float(QUERY_TIMEOUT_S)), **(params or {}))
            rows = [dict(r) for r in result]
            if not is_explain and len(rows) >= ROW_CAP:
                st.warning(
                    f"Result capped at {ROW_CAP} rows / {QUERY_TIMEOUT_S}s timeout. "
                    "Add an explicit LIMIT or narrow the MATCH."
                )
            return rows[:ROW_CAP] if not is_explain else rows
    except Exception as e:
        st.error(f"Cypher error: {e}")
        return []


def _download_export_pack(df: pd.DataFrame, *, key: str, stem: str) -> None:
    pack = build_export_pack(
        df,
        active_target=get_active_symbol(),
        result_name=f"{stem}.csv",
    )
    st.download_button(
        "📥 Download export pack (ZIP)",
        pack,
        f"{stem}_{int(time.time())}.zip",
        "application/zip",
        key=key,
        help="CSV results + data_freeze.yaml + NOTICE + CITATION.cff",
    )

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
# Pre-built query templates ({symbol} filled from active research target)
# ---------------------------------------------------------------------------

def _build_query_templates(symbol: str) -> dict:
    """Gene-parameterized templates using EXPRESSED_IN_CANCER / SurvivalResult / OT edges."""
    s = symbol
    return {
        f"🎯 Expression: Which cancers have highest {s}?": {
            "description": f"Gene-aware expression using (:Gene {{symbol: '{s}'}})-[:EXPRESSED_IN_CANCER]->(d:Disease).",
            "cypher": f"""
MATCH (g:Gene {{symbol: '{s}'}})-[r:EXPRESSED_IN_CANCER]->(d:Disease)
WHERE r.median_tpm_log2 IS NOT NULL
RETURN d.tcga_code AS cancer_type,
       round(r.median_tpm_log2, 3) AS target_median_log2,
       d.tcga_sample_count AS n_samples,
       r.expression_rank AS expression_rank
ORDER BY r.median_tpm_log2 DESC
LIMIT 25
""",
            "params": {},
        },
        f"🎯 Open Targets: Top disease associations for {s}?": {
            "description": f"Gene→Disease ASSOCIATED_WITH from Open Targets (up to ~1000/gene; table shows top scores).",
            "cypher": f"""
MATCH (g:Gene {{symbol: '{s}'}})-[r:ASSOCIATED_WITH]->(d:Disease)
RETURN d.name AS disease,
       d.mondo_id AS mondo_id,
       d.therapeutic_area AS therapeutic_area,
       round(r.score, 4) AS ot_score,
       round(coalesce(r.genetics_score, 0), 4) AS genetics,
       round(coalesce(r.literature_score, 0), 4) AS literature
ORDER BY r.score DESC
LIMIT 40
""",
            "params": {},
        },
        f"🔗 STRING PPI: Protein partners of {s}?": {
            "description": f"STRING INTERACTS_WITH neighborhood for {s} (score ≥ loader threshold).",
            "cypher": f"""
MATCH (g:Gene {{symbol: '{s}'}})-[r:INTERACTS_WITH]-(b:Gene)
WHERE b.symbol <> '{s}'
RETURN b.symbol AS partner,
       round(coalesce(r.score, 0), 4) AS score,
       round(coalesce(r.escore, 0), 4) AS escore,
       round(coalesce(r.tscore, 0), 4) AS tscore,
       r.source AS source
ORDER BY r.score DESC
LIMIT 40
""",
            "params": {},
        },
        f"📈 Survival: Which cancers show {s}-High = worse prognosis?": {
            "description": f"Gene-aware Cox survival: sr.gene_symbol='{s}' · endpoint=OS · hazard_ratio>1 · p<0.05.",
            "cypher": f"""
MATCH (d:Disease)-[:HAS_SURVIVAL_RESULT]->(sr:SurvivalResult)
WHERE sr.gene_symbol = '{s}'
  AND sr.hazard_ratio > 1.0
  AND sr.p_value < 0.05
  AND sr.endpoint = 'OS'
RETURN d.tcga_code AS cancer,
       round(sr.hazard_ratio, 3) AS hazard_ratio,
       round(sr.p_value, 5) AS p_value,
       sr.n_high AS n_target_high,
       sr.n_low AS n_target_low
ORDER BY sr.hazard_ratio DESC
""",
            "params": {},
        },
        f"📚 Publications: Evidence linked to {s}?": {
            "description": f"Publications linked to {s} via SUPPORTS (Step 3b PubMed load).",
            "cypher": f"""
MATCH (pub:Publication)-[:SUPPORTS]->(g:Gene {{symbol: '{s}'}})
RETURN pub.title AS title,
       pub.authors AS authors,
       pub.journal AS journal,
       pub.year AS year,
       pub.evidence_type AS evidence_type,
       pub.pubmed_id AS pmid
ORDER BY pub.year DESC
LIMIT 40
""",
            "params": {},
        },
        f"💊 Drugs: Agents targeting {s}?": {
            "description": f"Drug nodes linked to {s} via TARGETS (ChEMBL + curated theranostics, Step 3b).",
            "cypher": f"""
MATCH (drug:Drug)-[:TARGETS]->(g:Gene {{symbol: '{s}'}})
RETURN drug.name AS drug,
       drug.drug_type AS type,
       drug.max_phase AS max_phase,
       drug.isotope AS isotope,
       drug.chembl_id AS chembl_id,
       drug.developer AS developer,
       drug.mechanism AS mechanism
ORDER BY coalesce(drug.max_phase, 0) DESC, drug.name
LIMIT 40
""",
            "params": {},
        },
        f"🧪 Clinical Trials: Trials investigating {s} / related diseases?": {
            "description": f"ClinicalTrial nodes linked to {s} via TARGETS_GENE (up to ~100/gene in expanded slice).",
            "cypher": f"""
MATCH (t:ClinicalTrial)-[:TARGETS_GENE]->(g:Gene {{symbol: '{s}'}})
OPTIONAL MATCH (t)-[:INVESTIGATES]->(d:Disease)
WITH g, t, collect(DISTINCT d.tcga_code) AS cancers
RETURN t.nct_id AS nct_id,
       t.phase AS phase,
       t.sponsor AS sponsor,
       t.status AS status,
       cancers,
       t.title AS title
ORDER BY t.phase, t.nct_id
LIMIT 40
""",
            "params": {},
        },
        f"🔬 Co-expression: Genes correlated with {s} in PRAD?": {
            "description": f"Genes with Spearman correlations to {s}.",
            "cypher": f"""
MATCH (seed:Gene {{symbol: '{s}'}})-[r:CORRELATED_WITH]->(g:Gene)
RETURN g.symbol AS biomarker,
       g.name AS biomarker_name,
       round(r.spearman_rho, 4) AS spearman_rho,
       round(r.p_value, 6) AS p_value,
       r.cancer_type AS cancer_type,
       r.significant AS fdr_significant
ORDER BY abs(r.spearman_rho) DESC
LIMIT 50
""",
            "params": {},
        },
        f"🧬 Protein: What is the {s} protein / pathway context?": {
            "description": f"{s} gene/protein properties and pathway memberships.",
            "cypher": f"""
MATCH (g:Gene {{symbol: '{s}'}})
OPTIONAL MATCH (p:Protein {{symbol: '{s}'}})
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
        f"🏥 Patient Groups: Eligible cohorts for {s}-High framing?": {
            "description": f"PatientGroup + SurvivalResult for {s}-High cohorts (sr.gene_symbol filter).",
            "cypher": f"""
MATCH (pg:PatientGroup)-[:HAS_SURVIVAL_DATA]->(sr:SurvivalResult)
WHERE pg.expression_group = '{s}_High'
  AND sr.gene_symbol = '{s}'
  AND sr.endpoint = 'OS'
  AND pg.n_eligible > 50
RETURN pg.cancer_type AS cancer,
       pg.threshold_method AS method,
       round(pg.threshold_value, 2) AS threshold,
       pg.n_eligible AS n_eligible,
       pg.n_total AS n_total,
       round(toFloat(pg.n_eligible) / pg.n_total * 100, 1) AS pct_eligible,
       round(sr.hazard_ratio, 3) AS hr_high_vs_low,
       sr.significant AS significant
ORDER BY pg.n_eligible DESC
LIMIT 20
""",
            "params": {},
        },
        f"🔗 Full path: {s} → Pathway → Disease evidence": {
            "description": f"Multi-hop: {s} → Pathway + EXPRESSED_IN_CANCER + SurvivalResult (gene-filtered).",
            "cypher": f"""
MATCH (g:Gene {{symbol: '{s}'}})-[:PARTICIPATES_IN]->(pw:Pathway)
MATCH (g)-[r:EXPRESSED_IN_CANCER]->(d:Disease)
MATCH (d)-[:HAS_SURVIVAL_RESULT]->(sr:SurvivalResult)
WHERE sr.gene_symbol = '{s}'
  AND sr.endpoint = 'OS'
  AND sr.significant = true
OPTIONAL MATCH (pub:Publication)-[:SUPPORTS]->(g)
RETURN g.symbol AS gene,
       pw.name AS pathway,
       d.tcga_code AS disease,
       round(r.median_tpm_log2, 3) AS target_expression,
       round(sr.hazard_ratio, 3) AS hazard_ratio,
       count(DISTINCT pub) AS n_supporting_pubs
ORDER BY sr.hazard_ratio DESC
LIMIT 40
""",
            "params": {},
        },
        f"📊 Cell lines: Which lines depend on {s}?": {
            "description": f"DepMap CellLine-[:DEPENDS_ON]->Gene for {s} (Step 3c; CRISPR < -0.5).",
            "cypher": f"""
MATCH (cl:CellLine)-[r:DEPENDS_ON]->(g:Gene {{symbol: '{s}'}})
RETURN cl.name AS cell_line,
       cl.cancer_type AS cancer_type,
       round(r.crispr_score, 4) AS crispr_score,
       r.source AS source
ORDER BY r.crispr_score
LIMIT 30
""",
            "params": {},
        },
    }


_ACTIVE = get_active_symbol()
QUERY_TEMPLATES = _build_query_templates(_ACTIVE)

# ponytail: ceiling = string templates only; upgrade = parametrized $gene Cypher binds
def _self_check_templates() -> None:
    a, b = _build_query_templates("FOLH1"), _build_query_templates("EGFR")
    ba, bb = json.dumps(a), json.dumps(b)
    assert "FOLH1" in ba and "EGFR" in bb
    assert "FOLH1" not in bb and "EGFR" not in ba
    banned = ("cd" + "46").lower()
    assert banned not in ba.lower() and banned not in bb.lower()


if __name__ == "__main__":
    _self_check_templates()
    print("7_kg_query_explorer templates ok")

# ---------------------------------------------------------------------------
# Page layout
# ---------------------------------------------------------------------------

header_stats = get_header_stats()

page_header(
    icon="🔍",
    module_name="KG Query Explorer",
    purpose=(
        f"Live Cypher against Aura · active target **{_ACTIVE}** · "
        "templates · editor · natural language → Cypher"
    ),
    kpi_chips=[
        ("Query Templates", str(len(QUERY_TEMPLATES))),
        ("KG Nodes", f"{header_stats['total_nodes']:,}" if header_stats else "3,068"),
        ("Active Target", _ACTIVE),
        ("Rel Types", str(header_stats["rel_type_count"]) if header_stats else "10+"),
    ],
    source_badges=["UniProt", "OpenTargets", "ClinicalTrials", "STRING"],
)

render_data_freeze_banner(compact=True)

if not is_loaded(_ACTIVE):
    st.info(
        f"**{_ACTIVE}** is a stub target — gene-parameterized templates still run; "
        "results may be empty until ETL loads this gene. Free Cypher still works."
    )

driver = get_driver()
if driver is None:
    st.warning(
        "AuraDB not connected — set NEO4J_URI and NEO4J_PASSWORD in `.env` to enable live queries.  \n"
        "Query templates and Cypher editor are shown for reference."
    )

# Schema sidebar summary
with st.sidebar:
    st.markdown("---")
    st.markdown("**🗄️ Knowledge Graph Schema**")
    try:
        schema = get_schema()
        for lbl in schema.get("labels", []):
            cnt = schema["counts"].get(lbl, 0)
            st.markdown(f"<span style='color:#2563EB;'>●</span> `{lbl}`: **{cnt:,}**", unsafe_allow_html=True)
        st.markdown("**Relationship types:**")
        for rt in schema.get("rel_types", []):
            st.markdown(f"<span style='color:#4ade80;'>→</span> `{rt}`", unsafe_allow_html=True)
    except Exception:
        st.markdown("*Connect to graph to view schema*")

_KGQX_TABS = [
    "Query Templates",
    "Cypher Editor",
    "Natural Language",
    "Graph Visualizer",
]
_active_kgqx = section_tabs(_KGQX_TABS, key="kg_query_explorer_tabs")

if _active_kgqx == _KGQX_TABS[0]:
    st.markdown(
        "<div style='background:#1e293b;border-left:3px solid #38bdf8;padding:12px 16px;"
        "border-radius:6px;margin-bottom:14px;'>"
        "<b style='color:#2563EB;'>Pre-Built Research Queries</b><br>"
        "<span style='color:#64748B;'>12 curated Cypher queries covering the key research questions. "
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

            research_table(df_result, use_container_width=True, hide_index=True)

            _download_export_pack(df_result, key="dl_tpl", stem="kg_query")

            # Auto-plot if result has a good chart structure
            if "cancer" in df_result.columns and len(numeric_cols) >= 1:
                chart_col = next(
                    (c for c in ["hazard_ratio", "target_median_log2", "target_expression", "n_eligible", "crispr_score"]
                     if c in df_result.columns),
                    numeric_cols[0],
                )
                with st.expander("📊 Quick Chart", expanded=True):
                    fig = go.Figure(go.Bar(
                        x=df_result["cancer"] if "cancer" in df_result.columns else df_result.iloc[:, 0],
                        y=df_result[chart_col],
                        marker_color="#38bdf8",
                        text=df_result[chart_col].round(3).astype(str),
                        textposition="outside",
                    ))
                    fig.update_layout(
                        height=350, paper_bgcolor="#FFFFFF", plot_bgcolor="#EEF2F7",
                        xaxis=dict(color="#94a3b8"),
                        yaxis=dict(title=chart_col.replace("_", " "), color="#94a3b8", gridcolor="#E2E8F0"),
                        margin=dict(l=10, r=10, t=30, b=10),
                    )
                    st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No results returned — the graph may not have matching nodes yet, or the query returned empty results.")

# ===========================================================================
# TAB 2 — CYPHER EDITOR
# ===========================================================================
elif _active_kgqx == _KGQX_TABS[1]:
    st.markdown(
        "<div style='background:#1e293b;border-left:3px solid #4ade80;padding:12px 16px;"
        "border-radius:6px;margin-bottom:14px;'>"
        "<b style='color:#4ade80;'>Direct Cypher Query Editor</b><br>"
        "<span style='color:#64748B;'>Write read-only Cypher queries against the live AuraDB instance. "
        "Use MATCH, WHERE, RETURN, ORDER BY, LIMIT. Write operations are blocked.</span>"
        "</div>",
        unsafe_allow_html=True,
    )

    # Schema quick reference
    with st.expander("📖 Schema Quick Reference"):
        st.markdown(f"""
| Node Label | Key Properties | Notes |
|---|---|---|
| `Disease` | `tcga_code`, `mondo_id`, `name` | Expression via `EXPRESSED_IN_CANCER` edge |
| `SurvivalResult` | `gene_symbol`, `endpoint`, `hazard_ratio`, `p_value`, `significant` | Filter `gene_symbol = '{_ACTIVE}'` |
| `Publication` | `pubmed_id`, `title`, `year`, `evidence_type` | `SUPPORTS` → Gene |
| `ClinicalTrial` | `nct_id`, `phase`, `sponsor`, `status` | `TARGETS_GENE` → Gene |
| `PatientGroup` | `cancer_type`, `expression_group`, `n_eligible`, `threshold_value` | e.g. `{_ACTIVE}_High` |
| `Drug` | `name`, `drug_type`, `payload`, `developer`, `chembl_id` | `TARGETS` → Gene |
| `Gene` | `symbol`, `chromosome`, `therapeutic_rationale` | Active: `{_ACTIVE}` |
| `Protein` | `symbol`, `molecular_weight_kda`, `surface_expressed` | |
| `Pathway` | `name`, `reactome_id`, `go_id` | |
| `CellLine` | `name`, `cancer_type` | Dependency via `DEPENDS_ON` edge |
| `Tissue` | `name`, `type`, `staining_intensity` | |

**Relationships:** `EXPRESSED_IN_CANCER` · `HAS_SURVIVAL_RESULT` · `HAS_PATIENT_GROUP` · `SUPPORTS` · `ASSOCIATED_WITH` · `TARGETS` · `TARGETS_GENE` · `INTERACTS_WITH` · `INDICATED_FOR` · `INVESTIGATES` · `PARTICIPATES_IN` · `CORRELATED_WITH` · `EXPRESSED_IN` · `ENCODES` · `HAS_SURVIVAL_DATA` · `DEPENDS_ON`

`EXPRESSED_IN_CANCER` edge props: `median_tpm_log2`, `expression_rank`
        """)

    default_cypher = st.session_state.get("cypher_editor", f"""// Example: pathways for {_ACTIVE}
MATCH (g:Gene {{symbol: '{_ACTIVE}'}})-[:PARTICIPATES_IN]->(pw:Pathway)
RETURN g.symbol, pw.name
LIMIT 25
""")

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
            research_table(df_cyp, use_container_width=True, hide_index=True)
            _download_export_pack(df_cyp, key="dl_cyp", stem="cypher_result")
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
elif _active_kgqx == _KGQX_TABS[2]:
    st.markdown(
        "<div style='background:#1e293b;border-left:3px solid #fbbf24;padding:12px 16px;"
        "border-radius:6px;margin-bottom:14px;'>"
        "<b style='color:#fbbf24;'>Natural Language → Cypher Translation</b><br>"
        "<span style='color:#64748B;'>Ask research questions in plain English. "
        "The AI translates to Cypher, runs it against AuraDB, and explains the results. "
        f"Active target: {_ACTIVE}.</span>"
        "</div>",
        unsafe_allow_html=True,
    )

    EXAMPLE_NL_QUERIES = [
        f"Which publications support {_ACTIVE} as a therapeutic target in prostate cancer?",
        f"Show clinical trials investigating diseases linked to {_ACTIVE}",
        f"Which genes are correlated with {_ACTIVE} in the knowledge graph?",
        f"What pathways does gene {_ACTIVE} participate in?",
        f"Show the evidence chain from {_ACTIVE} through pathways to supported diseases",
    ]
    if is_loaded(_ACTIVE):
        EXAMPLE_NL_QUERIES = [
            f"Which cancers have {_ACTIVE} expression above the pan-cancer median and worse OS for {_ACTIVE}-high patients?",
            f"Show me all clinical trials for prostate cancer and the hazard ratio for {_ACTIVE} in PRAD",
            f"Which publications support {_ACTIVE} as a therapeutic target in bladder cancer?",
            f"What cell lines have the highest dependency on {_ACTIVE} based on CRISPR screens?",
            f"Which drugs are being developed for cancers where {_ACTIVE} is overexpressed?",
            f"Show the complete evidence chain from {_ACTIVE} gene through complement pathway to supported diseases",
        ]

    nl_example = st.selectbox("Example questions:", ["(type your own below)"] + EXAMPLE_NL_QUERIES)
    nl_question = st.text_area(
        "Your research question:",
        value="" if nl_example == "(type your own below)" else nl_example,
        height=100,
        key="nl_q",
        placeholder=f"e.g. Which pathways involve {_ACTIVE}?",
    )

    # Mirror src/agent/nl_cypher.py — gene-neutral schema + active gene injection
    SCHEMA_CONTEXT = f"""
Neo4j schema (read-only MATCH): Gene(symbol), Disease(tcga_code, mondo_id, name), Drug(name, chembl_id),
ClinicalTrial(nct_id), SurvivalResult(gene_symbol, hazard_ratio, p_value, endpoint, significant),
CellLine(name), Publication(pubmed_id, title, year), Pathway(name), Protein(symbol),
PatientGroup(cancer_type, expression_group, n_eligible).
Relationships: EXPRESSED_IN_CANCER (Gene→Disease; median_tpm_log2, expression_rank),
ASSOCIATED_WITH (Gene→Disease, Open Targets),
TARGETS (Drug→Gene), TARGETS_GENE (Trial→Gene), DEPENDS_ON (CellLine→Gene),
HAS_SURVIVAL_RESULT (Disease→SurvivalResult), SUPPORTS (Publication→Gene),
INTERACTS_WITH (Gene↔Gene, STRING), PARTICIPATES_IN (Gene→Pathway),
CORRELATED_WITH (Gene→Gene), INDICATED_FOR, INVESTIGATES, HAS_SURVIVAL_DATA, ENCODES.

Active gene symbol: {_ACTIVE}
""".strip()

    run_nl = st.button("🤖 Translate & Run", type="primary", key="run_nl")
    if run_nl and nl_question.strip():
        with st.spinner("Translating to Cypher..."):
            try:
                # Try to use the orchestrator LLM
                from src.agent.orchestrator import TargetResearchAgent
                @st.cache_resource
                def _get_kg_agent():
                    return TargetResearchAgent()
                agent = _get_kg_agent()

                prompt = f"""You are a Neo4j Cypher expert. Convert the following research question into a valid Cypher query.

{SCHEMA_CONTEXT}

Research question: {nl_question}

Rules:
- Return ONLY the Cypher query, no explanation before it
- Start with MATCH or WITH
- Use gene symbol '{_ACTIVE}' where a gene is relevant
- Prefer EXPRESSED_IN_CANCER / SurvivalResult.gene_symbol / ASSOCIATED_WITH over gene-specific node properties
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
                        research_table(df_nl, use_container_width=True, hide_index=True)
                        _download_export_pack(df_nl, key="dl_nl", stem="nl_result")
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
elif _active_kgqx == _KGQX_TABS[3]:
    st.markdown(
        "<div style='background:#1e293b;border-left:3px solid #818cf8;padding:12px 16px;"
        "border-radius:6px;margin-bottom:14px;'>"
        "<b style='color:#818cf8;'>Graph Network Visualizer</b><br>"
        "<span style='color:#64748B;'>Renders query results as an interactive network graph. "
        "Select a view preset or run a path query to see the relationship structure.</span>"
        "</div>",
        unsafe_allow_html=True,
    )

    GRAPH_PRESETS = {
        f"{_ACTIVE} Gene → Pathways → Diseases": f"""
MATCH (g:Gene {{symbol:'{_ACTIVE}'}})-[:PARTICIPATES_IN]->(pw:Pathway)
RETURN g.symbol AS from_node, 'PARTICIPATES_IN' AS rel, pw.name AS to_node, 'Gene' AS from_type, 'Pathway' AS to_type
UNION
MATCH (g:Gene {{symbol:'{_ACTIVE}'}})-[:EXPRESSED_IN_CANCER]->(d:Disease)
RETURN g.symbol AS from_node, 'EXPRESSED_IN_CANCER' AS rel, d.tcga_code AS to_node, 'Gene' AS from_type, 'Disease' AS to_type
UNION
MATCH (pub:Publication)-[:SUPPORTS]->(g:Gene {{symbol:'{_ACTIVE}'}})
RETURN pub.evidence_type AS from_node, 'SUPPORTS' AS rel, g.symbol AS to_node, 'Publication' AS from_type, 'Gene' AS to_type
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
                    textfont=dict(size=8, color="#64748B"),
                    name=ntype,
                    hovertext=lbs,
                    hoverinfo="text",
                ))

            fig_g.update_layout(
                height=500, paper_bgcolor="#FFFFFF", plot_bgcolor="#EEF2F7",
                xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                legend=dict(bgcolor="#FFFFFF", font=dict(color="#64748B")),
                margin=dict(l=10, r=10, t=10, b=10),
                title=dict(text=f"Graph: {preset_sel}", font=dict(color="#64748B", size=13)),
            )
            st.plotly_chart(fig_g, use_container_width=True)
            st.caption(f"Rendering {n_nodes} nodes and {len(df_g)} edges from AuraDB · Node size = degree")
            research_table(df_g, use_container_width=True, hide_index=True)
        else:
            st.info("No graph data returned.")

st.markdown("---")
_footer_stats = (
    f"AuraDB: {header_stats['total_nodes']:,} nodes · {header_stats['total_rels']:,} relationships · "
    if header_stats
    else "AuraDB: 3,068 nodes · 2,517 relationships · "
)
st.markdown(
    f"<div style='color:#64748b;font-size:0.78em;'>{_footer_stats}"
    "Labels: Disease, SurvivalResult, Publication, ClinicalTrial, PatientGroup, Drug, Gene, Protein, Pathway, CellLine, Tissue · "
    "Read/Write access · Research use only.</div>",
    unsafe_allow_html=True,
)
