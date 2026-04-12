"""Page 4 — Knowledge Graph Explorer (PyVis + Cypher query runner)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import json
import os

from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parents[2] / ".env")

import streamlit as st

# Inject Streamlit Cloud secrets into os.environ (no-op when running locally with .env)
for _k in ("NEO4J_URI", "NEO4J_USERNAME", "NEO4J_PASSWORD"):
    try:
        if _k in st.secrets and not os.environ.get(_k):
            os.environ[_k] = st.secrets[_k]
    except Exception:
        pass


st.title("🕸️ Biomedical Knowledge Graph")
st.markdown(
    "**Neo4j AuraDB knowledge network — genes, proteins, diseases, drugs, clinical trials, and patient cohorts. "
    "Interactive graph visualization and Cypher query interface.**"
)

# ---------------------------------------------------------------------------
# Connection check
# ---------------------------------------------------------------------------

@st.cache_resource(ttl=300)
def get_driver():
    user = os.getenv("NEO4J_USERNAME", "neo4j")
    password = os.getenv("NEO4J_PASSWORD")

    if not uri or not password:
        return None, "NEO4J_URI and NEO4J_PASSWORD not set — AuraDB not connected"

    try:
        driver = GraphDatabase.driver(uri, auth=(user, password))
        driver.verify_connectivity()
        return driver, None
    except Exception as e:
        return None, str(e)


driver, conn_error = get_driver()

if conn_error:
    st.warning(
        f"⚠️ Knowledge graph not connected: {conn_error}\n\n"
        "Set graph database credentials in the .env file and restart the app."
    )
    st.info("Graph statistics and network visualizations require a live connection.")
else:
    st.success("✅ Connected to Biomedical Knowledge Graph")

# ---------------------------------------------------------------------------
# Graph statistics
# ---------------------------------------------------------------------------

st.subheader("Graph Statistics")

if driver is not None:
    try:
        with driver.session() as session:
            counts = {}
            for label in [
                "Gene", "Protein", "Disease", "Tissue", "Drug",
                "ClinicalTrial", "PatientGroup", "CellLine",
                "AnalysisResult", "Publication", "Pathway", "DataSource",
            ]:
                result = session.run(f"MATCH (n:{label}) RETURN count(n) AS c")
                counts[label] = result.single()["c"]

            total_nodes = sum(counts.values())
            total_rels = session.run("MATCH ()-[r]->() RETURN count(r) AS c").single()["c"]

        col1, col2 = st.columns(2)
        col1.metric("Total Nodes", f"{total_nodes:,}")
        col2.metric("Total Relationships", f"{total_rels:,}")

        # Node type breakdown
        count_items = sorted(counts.items(), key=lambda x: x[1], reverse=True)
        col_labels = [f"{k}: {v}" for k, v in count_items]
        st.markdown("**Nodes by type:** " + " · ".join(col_labels))
    except Exception as e:
        st.error(f"Could not fetch graph stats: {e}")
else:
    # Static stats
    col1, col2 = st.columns(2)
    col1.metric("Total Nodes (Phase 1 est.)", "~3,912")
    col2.metric("Total Relationships (est.)", "~14,880")

# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# Query Explorer — tabbed layout
# ---------------------------------------------------------------------------

st.subheader("Query Explorer")

# Grouped queries by clinical theme
QUERY_GROUPS = {
    "🎯 Cancer Prioritisation": {
        "Top cancers by CD46 priority score": (
            "MATCH (d:Disease) WHERE d.priority_score IS NOT NULL "
            "RETURN d.tcga_code AS cancer, d.name AS name, "
            "round(d.priority_score * 100) / 100 AS priority_score, "
            "d.priority_label AS priority_label "
            "ORDER BY d.priority_score DESC LIMIT 10",
            "Ranks cancer types by composite CD46 therapeutic opportunity score."
        ),
        "All cancers with CD46 expression levels": (
            "MATCH (d:Disease) WHERE d.cd46_mean_tpm_log2 IS NOT NULL "
            "RETURN d.tcga_code AS cancer, d.name AS name, "
            "round(d.cd46_mean_tpm_log2 * 100) / 100 AS cd46_mean_log2, "
            "d.cd46_expression_rank AS rank "
            "ORDER BY d.cd46_mean_tpm_log2 DESC",
            "All 25 cancer types with mean CD46 log2 expression, ranked highest to lowest."
        ),
        "Survival impact by cancer type": (
            "MATCH (d:Disease) WHERE d.cd46_survival_hr IS NOT NULL "
            "RETURN d.tcga_code AS cancer, "
            "round(d.cd46_survival_hr * 100) / 100 AS hazard_ratio, "
            "round(d.cd46_survival_pval * 1000) / 1000 AS p_value "
            "ORDER BY d.cd46_survival_hr DESC",
            "Cox hazard ratio for CD46-High vs CD46-Low across cancer types."
        ),
    },
    "💊 Drug Targets": {
        "CD46-targeting drugs": (
            "MATCH (dr:Drug)-[:TARGETS]->(g:Gene {symbol: 'CD46'}) "
            "RETURN dr.name AS drug, dr.drug_type AS modality, "
            "dr.clinical_stage AS stage, dr.mechanism AS mechanism, dr.isotope AS isotope",
            "All therapeutic agents in the knowledge graph that target CD46."
        ),
        "Drug mechanisms of action": (
            "MATCH (dr:Drug)-[:TARGETS]->(g:Gene {symbol: 'CD46'}) "
            "RETURN dr.name AS drug, dr.mechanism AS mechanism, dr.developer AS developer",
            "Detailed mechanism and developer for each CD46-targeting therapy."
        ),
        "CD46 gene and its pathways": (
            "MATCH (g:Gene {symbol: 'CD46'})-[:PARTICIPATES_IN]->(pw:Pathway) "
            "RETURN g.symbol AS gene, pw.name AS pathway, pw.category AS category, pw.reactome_id AS reactome_id",
            "Biological pathways where CD46 participates (complement, immune evasion)."
        ),
    },
    "👥 Patient Cohorts": {
        "PRAD patient eligibility by threshold": (
            "MATCH (d:Disease {tcga_code: 'PRAD'})-[:HAS_PATIENT_GROUP]->(pg:PatientGroup) "
            "RETURN pg.threshold_method AS threshold, pg.expression_group AS cd46_group, "
            "pg.n_patients AS n_patients "
            "ORDER BY pg.expression_group",
            "CD46-High patient counts in PRAD at each expression threshold."
        ),
        "Top 10 diseases by eligible patients (75th pct)": (
            "MATCH (d:Disease)-[:HAS_PATIENT_GROUP]->(pg:PatientGroup) "
            "WHERE pg.threshold_method = '75th_pct' AND pg.expression_group = 'CD46-High' "
            "RETURN d.tcga_code AS cancer, d.name AS name, pg.n_patients AS cd46_high_patients "
            "ORDER BY pg.n_patients DESC LIMIT 10",
            "Diseases with most CD46-High patients at the 75th percentile threshold."
        ),
        "All patient groups (CD46-High, median split)": (
            "MATCH (pg:PatientGroup) WHERE pg.threshold_method = 'median' "
            "AND pg.expression_group = 'CD46-High' "
            "RETURN pg.cancer_type AS cancer, pg.n_patients AS eligible "
            "ORDER BY pg.n_patients DESC",
            "CD46-High patient counts across all cancers using median split."
        ),
    },
    "🧬 Biology & Tissue": {
        "Tumor tissues with CD46 protein": (
            "MATCH (p:Protein)-[e:EXPRESSED_IN]->(t:Tissue) "
            "WHERE t.type = 'tumor' "
            "RETURN t.name AS tissue, p.symbol AS protein, p.isoform AS isoform "
            "ORDER BY t.name",
            "Tumor tissue types where CD46 protein is expressed (Human Protein Atlas)."
        ),
        "Normal tissues expressing CD46": (
            "MATCH (p:Protein)-[e:EXPRESSED_IN]->(t:Tissue) "
            "WHERE t.type = 'normal' "
            "RETURN t.name AS tissue, p.symbol AS protein, p.isoform AS isoform "
            "ORDER BY t.name",
            "Normal tissue distribution of CD46 — key for therapeutic window assessment."
        ),
        "CD46 protein isoforms": (
            "MATCH (g:Gene {symbol: 'CD46'})-[:ENCODES]->(p:Protein) "
            "RETURN g.symbol AS gene, p.uniprot_id AS uniprot_id, p.isoform AS isoform, "
            "p.molecular_weight_kda AS mol_weight_kDa, p.surface_expressed AS surface_expressed",
            "CD46 protein isoforms (STA-1, STA-2, LCA-1, LCA-2) and their properties."
        ),
    },
    "🔬 Cell Lines & Dependency": {
        "Cell lines where CD46 is a dependency": (
            "MATCH (cl:CellLine)-[:DEPENDS_ON]->(g:Gene {symbol: 'CD46'}) "
            "RETURN cl.name AS cell_line, cl.cancer_type AS cancer, "
            "round(cl.cd46_crispr_score * 1000) / 1000 AS crispr_score "
            "ORDER BY cl.cd46_crispr_score ASC LIMIT 20",
            "Cancer cell lines where CRISPR knockout of CD46 reduces fitness."
        ),
        "High CD46 expression cell lines": (
            "MATCH (cl:CellLine) WHERE cl.cd46_expression_tpm > 0 "
            "RETURN cl.name AS cell_line, cl.cancer_type AS cancer, "
            "round(cl.cd46_expression_tpm * 100) / 100 AS cd46_tpm, "
            "cl.cd46_is_dependency AS is_dependency "
            "ORDER BY cl.cd46_expression_tpm DESC LIMIT 20",
            "Cell lines ranked by CD46 mRNA expression level."
        ),
        "PRAD-specific cell lines": (
            "MATCH (cl:CellLine) WHERE cl.cancer_type = 'Prostate Cancer' "
            "RETURN cl.name AS cell_line, cl.cancer_type AS cancer, "
            "cl.cd46_expression_tpm AS cd46_tpm, cl.cd46_is_dependency AS is_dependency",
            "Prostate cancer cell lines with CD46 expression and essentiality data."
        ),
    },
    "📋 Custom Query": {},
}

# Build tabs from group names
tab_labels = list(QUERY_GROUPS.keys())
tabs = st.tabs(tab_labels)

def _run_query(cypher: str):
    """Execute a read-only Cypher query and display results."""
    if driver is None:
        st.error("Knowledge graph not connected — check credentials.")
        return
    cypher_upper = cypher.strip().upper()
    forbidden_ops = ["CREATE", "MERGE", "DELETE", "SET ", "REMOVE", "DROP"]
    if any(cypher_upper.startswith(kw) or f" {kw} " in cypher_upper for kw in forbidden_ops):
        st.error("⛔ Write operations are not permitted. Use read-only MATCH queries.")
        return
    try:
        with driver.session() as session:
            result = session.run(cypher)
            records = [dict(rec) for rec in result]
        if records:
            import pandas as pd
            df = pd.DataFrame(records)
            st.dataframe(df, use_container_width=True)
            st.caption(f"↳ {len(records)} records returned")
        else:
            st.info("Query returned no results — the data may not yet be in the graph.")
    except Exception as e:
        st.error(f"Query error: {e}")

for tab, (group_name, queries) in zip(tabs, QUERY_GROUPS.items()):
    with tab:
        if group_name == "📋 Custom Query":
            st.markdown("Write any read-only `MATCH` Cypher query below.")
            custom_q = st.text_area(
                "Cypher Query",
                value="MATCH (g:Gene) RETURN g.symbol, g.ensembl_id LIMIT 5",
                height=120,
                key="custom_cypher",
            )
            if st.button("▶️ Run", key="run_custom"):
                _run_query(custom_q)
        else:
            for q_name, (cypher, description) in queries.items():
                with st.expander(f"**{q_name}**", expanded=False):
                    st.caption(description)
                    st.code(cypher, language="cypher")
                    if st.button(f"▶️ Run — {q_name}", key=f"btn_{q_name}"):
                        _run_query(cypher)

# ---------------------------------------------------------------------------
# Network Visualization — multi-scenario explorer
# ---------------------------------------------------------------------------

st.subheader("Network Visualization")
st.markdown(
    "Select a biological dimension to explore as an interactive graph. "
    "Hover over nodes for details. Drag to rearrange."
)

NETWORK_SCENARIOS = {
    "🧬 CD46 Gene → All Direct Connections": {
        "description": "Central view: CD46 gene radiating to proteins, pathways, and drugs directly connected to it.",
        "cypher": """
            MATCH (g:Gene {symbol: 'CD46'})-[r]->(n)
            RETURN g, type(r) AS rel_type, n, 'out' AS direction
            LIMIT 30
            UNION
            MATCH (n)-[r]->(g:Gene {symbol: 'CD46'})
            RETURN g, type(r) AS rel_type, n, 'in' AS direction
            LIMIT 20
        """,
        "center": "CD46",
        "center_label": "Gene",
    },
    "💊 Drug → Target → Disease Pathway": {
        "description": "Therapeutic landscape: drugs targeting CD46, connected through to the diseases they may treat.",
        "cypher": """
            MATCH (dr:Drug)-[:TARGETS]->(g:Gene {symbol: 'CD46'})
            RETURN dr AS n, 'Drug' AS src_label, g AS g, 'TARGETS' AS rel_type, 'out' AS direction
            LIMIT 10
            UNION
            MATCH (g:Gene {symbol: 'CD46'})-[:PARTICIPATES_IN]->(pw:Pathway)
            RETURN g AS n, 'Gene' AS src_label, pw AS g, 'PARTICIPATES_IN' AS rel_type, 'out' AS direction
            LIMIT 10
        """,
        "center": "CD46",
        "center_label": "Gene",
        "alt_query": True,
        "queries": [
            ("MATCH (dr:Drug)-[:TARGETS]->(g:Gene {symbol: 'CD46'}) RETURN dr, g LIMIT 10", "Drug-Gene"),
            ("MATCH (g:Gene {symbol: 'CD46'})-[:PARTICIPATES_IN]->(pw:Pathway) RETURN g, pw LIMIT 10", "Gene-Pathway"),
            ("MATCH (g:Gene {symbol: 'CD46'})-[:ENCODES]->(p:Protein) RETURN g, p LIMIT 10", "Gene-Protein"),
        ],
    },
    "🏥 Disease → Patient Groups": {
        "description": "Clinical lens: cancer types connected to CD46-High and CD46-Low patient cohorts.",
        "cypher": """
            MATCH (d:Disease)-[:HAS_PATIENT_GROUP]->(pg:PatientGroup)
            WHERE pg.threshold_method = '75th_pct'
            RETURN d, pg LIMIT 40
        """,
        "center": None,
        "multi_edge": True,
    },
    "🔬 Cell Lines → CD46 Dependency": {
        "description": "Functional genomics: cancer cell lines dependent on CD46 for survival (CRISPR screen).",
        "cypher": """
            MATCH (cl:CellLine)-[:DEPENDS_ON]->(g:Gene {symbol: 'CD46'})
            RETURN cl, g LIMIT 30
        """,
        "center": "CD46",
        "center_label": "Gene",
        "multi_edge": True,
    },
    "🌐 Full CD46 Ecosystem (50 nodes)": {
        "description": "Panoramic view: genes, proteins, diseases, drugs, pathways, and patient groups all connected.",
        "cypher": """
            MATCH (g:Gene {symbol: 'CD46'})-[r1]->(a)
            OPTIONAL MATCH (a)-[r2]->(b)
            RETURN g, type(r1) AS rel1, a, type(r2) AS rel2, b
            LIMIT 50
        """,
        "center": "CD46",
        "center_label": "Gene",
        "two_hop": True,
    },
}

COLOR_MAP = {
    "Gene": "#38bdf8", "Protein": "#818cf8", "Disease": "#f87171",
    "Tissue": "#4ade80", "Drug": "#fbbf24", "ClinicalTrial": "#fb923c",
    "Pathway": "#a78bfa", "DataSource": "#94a3b8",
    "PatientGroup": "#34d399", "CellLine": "#f472b6",
}

def _node_display(n, fallback="node"):
    """Get a short readable label for a Neo4j node."""
    for key in ["symbol", "tcga_code", "name", "tissue_name", "depmap_id", "nct_id"]:
        val = n.get(key)
        if val and str(val).strip():
            return str(val)[:22]
    return fallback

def _node_id(n, label):
    for key in ["symbol", "tcga_code", "uniprot_id", "depmap_id", "nct_id", "name"]:
        val = n.get(key)
        if val:
            return f"{label}_{val}"
    return f"{label}_{id(n)}"

def _build_net(records, scenario_key):
    from pyvis.network import Network
    net = Network(
        height="540px", width="100%",
        bgcolor="#0f172a", font_color="#e2e8f0",
        directed=True,
    )
    net.set_options(
        '{"physics": {"barnesHut": {"gravitationalConstant": -6000, "springLength": 120},'
        '"stabilization": {"iterations": 120}},'
        '"nodes": {"font": {"size": 12}, "borderWidth": 2},'
        '"edges": {"smooth": {"type": "continuous"}, "arrows": {"to": {"enabled": true, "scaleFactor": 0.5}}}}'
    )
    return net

scenario_sel = st.selectbox(
    "Choose a network view",
    options=list(NETWORK_SCENARIOS.keys()),
    index=0,
)
scenario = NETWORK_SCENARIOS[scenario_sel]
st.caption(scenario["description"])

if driver is not None:
    if st.button("🔄 Load Network", key="load_network"):
        try:
            from pyvis.network import Network
            import streamlit.components.v1 as components

            net = _build_net([], scenario_sel)
            added_nodes = set()

            def add_node(node, label_override=None):
                labels = list(node.labels) if hasattr(node, "labels") else []
                lbl = label_override or (labels[0] if labels else "Node")
                nid = _node_id(node, lbl)
                if nid not in added_nodes:
                    color = COLOR_MAP.get(lbl, "#e2e8f0")
                    size = 22 if lbl == "Gene" else 14
                    title = f"<b>{lbl}</b><br>" + "<br>".join(
                        f"{k}: {v}" for k, v in dict(node).items() if v is not None
                    )[:400]
                    net.add_node(nid, label=_node_display(node), color=color,
                                  size=size, title=title, font={"size": 11})
                    added_nodes.add(nid)
                return nid

            with driver.session() as session:
                cypher = scenario["cypher"].strip()

                if scenario.get("two_hop"):
                    # Two-hop: g→a→b
                    recs = list(session.run(cypher))
                    for rec in recs:
                        g, a = rec["g"], rec["a"]
                        rel1 = rec.get("rel1", "RELATED")
                        gid = add_node(g)
                        aid = add_node(a)
                        net.add_edge(gid, aid, label=rel1, color="#475569", title=rel1)
                        b = rec.get("b")
                        rel2 = rec.get("rel2")
                        if b is not None and rel2:
                            bid = add_node(b)
                            net.add_edge(aid, bid, label=rel2, color="#334155", title=rel2)

                elif scenario.get("multi_edge"):
                    # Flat two-node pattern: (a)-[r]->(b)
                    recs = list(session.run(cypher))
                    for rec in recs:
                        keys = list(rec.keys())
                        a_node = rec[keys[0]]
                        b_node = rec[keys[1]]
                        aid = add_node(a_node)
                        bid = add_node(b_node)
                        net.add_edge(aid, bid, color="#475569")

                else:
                    # Standard: g + rel_type + n + direction
                    recs = list(session.run(
                        "MATCH (g:Gene {symbol: 'CD46'})-[r]->(n) "
                        "RETURN g, type(r) AS rel_type, n, 'out' AS direction LIMIT 30 "
                        "UNION "
                        "MATCH (n)-[r]->(g:Gene {symbol: 'CD46'}) "
                        "RETURN g, type(r) AS rel_type, n, 'in' AS direction LIMIT 20"
                    ))
                    for rec in recs:
                        g = rec["g"]
                        n = rec["n"]
                        rel_type = rec["rel_type"]
                        direction = rec.get("direction", "out")
                        gid = add_node(g, "Gene")
                        nid = add_node(n)
                        if direction == "out":
                            net.add_edge(gid, nid, label=rel_type, color="#475569", title=rel_type)
                        else:
                            net.add_edge(nid, gid, label=rel_type, color="#64748b", title=rel_type)

            if len(added_nodes) == 0:
                st.warning("No nodes returned — the graph may not contain data for this view yet.")
            else:
                st.caption(f"Rendered {len(added_nodes)} nodes. Drag nodes to explore. Hover for details.")
                html = net.generate_html()
                components.html(html, height=560)

        except Exception as e:
            st.error(f"Network error: {e}")
else:
    st.info("Connect to the knowledge graph to enable network visualization.")

# ---------------------------------------------------------------------------
# Protein Structures & Networks (AlphaFold + STRING)
# ---------------------------------------------------------------------------

st.subheader("🧬 Protein Structures & Interaction Networks")

af_tab, str_tab, pub_tab = st.tabs([
    "🔬 AlphaFold Structure",
    "🌐 STRING Protein Network",
    "📚 Key Publications",
])

with af_tab:
    # ── helpers ──────────────────────────────────────────────────────────────
    _DATA_ROOT = Path(__file__).resolve().parents[2] / "data" / "raw"

    @st.cache_data(ttl=3_600, show_spinner=False)
    def _load_uniprot() -> dict:
        p = _DATA_ROOT / "apis" / "uniprot_cd46.json"
        if p.exists():
            with open(p, encoding="utf-8") as f:
                return json.load(f)
        return {}

    @st.cache_data(ttl=3_600, show_spinner=False)
    def _load_open_targets() -> list:
        p = _DATA_ROOT / "apis" / "open_targets_cd46.json"
        if p.exists():
            with open(p, encoding="utf-8") as f:
                d = json.load(f)
            return d.get("data", {}).get("target", {}).get("associatedDiseases", {}).get("rows", [])
        return []

    @st.cache_data(ttl=86_400, show_spinner=False)
    def _fetch_alphafold() -> dict:
        try:
            import requests as _req
            r = _req.get("https://alphafold.ebi.ac.uk/api/prediction/P15529", timeout=12)
            if r.status_code == 200:
                data = r.json()
                return data[0] if data else {}
        except Exception:
            pass
        return {}

    uni = _load_uniprot()
    ot_rows = _load_open_targets()

    # ── parse UniProt data ───────────────────────────────────────────────────
    comments = uni.get("comments", [])

    # Function description
    func_text = next(
        (c["texts"][0]["value"] for c in comments
         if c.get("commentType") == "FUNCTION" and c.get("texts")), ""
    )

    # Annotation score and sequence length
    annot_score = uni.get("annotationScore", 5.0)
    sequence = uni.get("sequence", {})
    seq_len = sequence.get("length", 392)

    # Gene names
    gene_names_block = uni.get("genes", [{}])
    gene_primary = gene_names_block[0].get("geneName", {}).get("value", "CD46") if gene_names_block else "CD46"

    # Features: domains + variants
    features = uni.get("features", [])
    nat_variants = [f for f in features if f.get("type") == "Natural variant"]
    domains_raw = [f for f in features if f.get("type") in ("Signal", "Domain", "Transmembrane", "Topological domain")]

    # Isoforms
    alt_products = next((c for c in comments if c.get("commentType") == "ALTERNATIVE PRODUCTS"), {})
    isoforms = alt_products.get("isoforms", [])
    isoform_note = alt_products.get("note", {}).get("texts", [{}])[0].get("value", "")

    # ── SECTION 1: Protein Overview ──────────────────────────────────────────
    st.markdown(
        "<div style='background:#1e293b;border-left:3px solid #38bdf8;padding:14px 18px;"
        "border-radius:8px;margin-bottom:18px;'>"
        "<span style='font-size:1.15em;font-weight:700;color:#38bdf8;'>CD46 — Membrane Cofactor Protein (MCP)</span>"
        "&nbsp;&nbsp;<span style='background:#0f172a;color:#94a3b8;font-size:0.78em;padding:2px 9px;"
        "border-radius:12px;'>UniProt P15529 · Homo sapiens</span>"
        "</div>",
        unsafe_allow_html=True,
    )

    ov_c1, ov_c2, ov_c3, ov_c4 = st.columns(4)
    ov_c1.metric("Sequence Length", f"{seq_len} aa")
    ov_c2.metric("Apparent MW", "56–66 kDa")
    ov_c3.metric("UniProt Annotation", f"{annot_score:.0f}/5 ⭐")
    ov_c4.metric("Natural Variants", len(nat_variants))

    if func_text:
        st.markdown(
            f"<div style='background:#0f172a;border:1px solid #334155;padding:12px 16px;"
            f"border-radius:6px;color:#cbd5e1;font-size:0.88em;line-height:1.6;margin-bottom:6px;'>"
            f"<b style='color:#38bdf8;'>Function:</b> {func_text}</div>",
            unsafe_allow_html=True,
        )

    # ── SECTION 2: Linear Domain Map ─────────────────────────────────────────
    st.markdown("#### 🗺️ Protein Domain Architecture")

    import plotly.graph_objects as _go

    DOMAIN_SEGMENTS = [
        ("Signal peptide",   1,   34,  "#64748b"),
        ("SCR / Sushi 1",   35,   96,  "#3b82f6"),
        ("SCR / Sushi 2",   97,  159,  "#6366f1"),
        ("SCR / Sushi 3",  160,  225,  "#8b5cf6"),
        ("SCR / Sushi 4",  226,  285,  "#a855f7"),
        ("STP-rich / O-glycan", 286, 343, "#ec4899"),
        ("Transmembrane",  344,  366,  "#f59e0b"),
        ("Cytoplasmic tail", 367, 392, "#10b981"),
    ]

    dom_fig = _go.Figure()
    for name, start, end, color in DOMAIN_SEGMENTS:
        dom_fig.add_trace(_go.Bar(
            x=[end - start + 1],
            y=["CD46"],
            base=[start - 1],
            orientation="h",
            marker_color=color,
            name=name,
            hovertemplate=f"<b>{name}</b><br>Residues {start}–{end}<br>Length: {end - start + 1} aa<extra></extra>",
        ))

    dom_fig.update_layout(
        barmode="stack",
        height=120,
        margin=dict(l=0, r=0, t=10, b=30),
        paper_bgcolor="#0f172a",
        plot_bgcolor="#0f172a",
        xaxis=dict(
            title="Residue position", color="#94a3b8",
            gridcolor="#1e293b", range=[0, seq_len + 5],
        ),
        yaxis=dict(showticklabels=False, showgrid=False),
        legend=dict(
            orientation="h", y=-0.6, x=0, font=dict(size=10, color="#94a3b8"),
            bgcolor="rgba(0,0,0,0)",
        ),
        showlegend=True,
    )
    st.plotly_chart(dom_fig, width='stretch')

    # ── SECTION 3: Natural Variants ───────────────────────────────────────────
    st.markdown("#### 🔬 Natural Variants (13 SNPs)")

    if nat_variants:
        import pandas as _pd
        var_rows = []
        for v in nat_variants:
            pos = v.get("location", {}).get("start", {}).get("value", "?")
            alt_seq = v.get("alternativeSequence", {})
            orig = alt_seq.get("originalSequence", "?")
            alts = alt_seq.get("alternativeSequences", ["?"])
            variant_aa = alts[0] if alts else "?"
            cross_refs = v.get("featureCrossReferences", [])
            dbsnp = next((r["id"] for r in cross_refs if r.get("database") == "dbSNP"), "")
            desc = v.get("description", "")
            disease = ""
            if "in " in desc:
                parts = [p.strip() for p in desc.split(";") if not p.strip().startswith("dbSNP")]
                disease = "; ".join(p.replace("in ", "") for p in parts if p and not p.startswith("dbSNP")).strip()
            var_rows.append({
                "Position": pos,
                "Change": f"{orig} → {variant_aa}",
                "dbSNP": dbsnp,
                "Disease / Note": disease if disease else "-",
            })
        df_var = _pd.DataFrame(var_rows).sort_values("Position")
        st.dataframe(df_var, use_container_width=True, hide_index=True)
    else:
        st.info("Natural variant data not available — check uniprot_cd46.json")

    # ── SECTION 4: Isoforms ───────────────────────────────────────────────────
    st.markdown("#### 🧬 Protein Isoforms")

    if isoform_note:
        st.caption(isoform_note)

    if isoforms:
        iso_rows = []
        for iso in isoforms:
            name = iso.get("name", {}).get("value", "?")
            synonyms = [s.get("value", "") for s in iso.get("synonyms", [])]
            syn_str = ", ".join(synonyms) if synonyms else "-"
            iso_id = iso.get("isoformIds", ["?"])[0]
            status = iso.get("isoformSequenceStatus", "?")
            iso_rows.append({
                "Isoform": name,
                "Synonym(s)": syn_str,
                "UniProt ID": iso_id,
                "Sequence Status": status,
            })
        df_iso = _pd.DataFrame(iso_rows)
        st.dataframe(df_iso, use_container_width=True, hide_index=True)
    else:
        st.info("Isoform data not available — check uniprot_cd46.json")

    # ── SECTION 5: Open Targets Disease Associations ──────────────────────────
    st.markdown("#### 🎯 Disease Associations (Open Targets — top 25 of 772)")

    if ot_rows:
        top25 = sorted(ot_rows, key=lambda r: r.get("score", 0), reverse=True)[:25]
        ot_names = [r["disease"]["name"] for r in top25]
        ot_scores = [round(r.get("score", 0), 4) for r in top25]
        ot_areas = [
            r["disease"].get("therapeuticAreas", [{}])[0].get("name", "other")
            for r in top25
        ]

        AREA_COLORS = {
            "hematologic disease": "#f87171",
            "genetic, familial or congenital disease": "#fb923c",
            "immune system disease": "#fbbf24",
            "neoplasm": "#4ade80",
            "cancer": "#4ade80",
            "infectious disease": "#a78bfa",
            "nervous system disease": "#38bdf8",
            "urinary system disease": "#818cf8",
        }
        bar_colors = [
            AREA_COLORS.get(a.lower(), "#64748b") for a in ot_areas
        ]

        ot_fig = _go.Figure(_go.Bar(
            x=ot_scores,
            y=ot_names,
            orientation="h",
            marker_color=bar_colors,
            hovertemplate="<b>%{y}</b><br>Score: %{x:.4f}<extra></extra>",
        ))
        ot_fig.update_layout(
            height=max(380, len(top25) * 18),
            margin=dict(l=0, r=0, t=10, b=0),
            paper_bgcolor="#0f172a",
            plot_bgcolor="#0f172a",
            xaxis=dict(title="Overall Association Score", color="#94a3b8",
                       gridcolor="#1e293b", range=[0, 1]),
            yaxis=dict(color="#e2e8f0", tickfont=dict(size=10), autorange="reversed"),
        )
        st.plotly_chart(ot_fig, width='stretch')
        st.caption("Source: Open Targets Platform — 772 total associations. Colors: red=hematologic, orange=genetic, yellow=immune, green=cancer, purple=infectious. Score 0–1.")
    else:
        st.info("Open Targets data not available — check data/raw/apis/open_targets_cd46.json")

    # ── SECTION 6: AlphaFold pLDDT ───────────────────────────────────────────
    st.markdown("#### 📊 AlphaFold Structural Confidence (pLDDT)")

    with st.spinner("Loading AlphaFold pLDDT…"):
        af = _fetch_alphafold()

    plddt = af.get("plddt") if af else None

    if isinstance(plddt, list) and len(plddt) > 0:
        import numpy as _np
        mean_conf = float(_np.mean(plddt))
        c_plddt1, c_plddt2, c_plddt3 = st.columns(3)
        c_plddt1.metric("Mean pLDDT", f"{mean_conf:.1f} / 100")
        c_plddt2.metric("Very High (>90)", f"{sum(1 for v in plddt if v > 90)} residues")
        c_plddt3.metric("Low (<70)", f"{sum(1 for v in plddt if v < 70)} residues")

        plddt_fig = _go.Figure(_go.Bar(
            y=plddt,
            marker_color=[
                "#3b82f6" if v > 90 else "#22c55e" if v > 70 else "#eab308" if v > 50 else "#ef4444"
                for v in plddt
            ],
            hovertemplate="Residue %{x}<br>pLDDT: %{y:.1f}<extra></extra>",
        ))
        plddt_fig.update_layout(
            height=200, margin=dict(l=0, r=0, t=10, b=0),
            paper_bgcolor="#0f172a", plot_bgcolor="#0f172a",
            xaxis=dict(title="Residue index", color="#94a3b8", showgrid=False),
            yaxis=dict(title="pLDDT", color="#94a3b8", range=[0, 100], gridcolor="#1e293b"),
        )
        st.plotly_chart(plddt_fig, width='stretch')
        st.caption("Blue > 90 (very high) · Green 70–90 (high) · Yellow 50–70 (low) · Red < 50 (very low)")
    else:
        st.info("pLDDT data unavailable (AlphaFold EBI API timeout). SCR domains 1–4 typically score > 85.")

    # ── SECTION 7: 3D Structure Viewer ────────────────────────────────────────
    st.markdown("#### 🔭 Interactive 3D Structure (AlphaFold DB)")
    st.markdown(
        "<iframe src='https://alphafold.ebi.ac.uk/entry/P15529' "
        "width='100%' height='620px' style='border:1px solid #334155;border-radius:8px;'>"
        "</iframe>",
        unsafe_allow_html=True,
    )
    st.link_button("Open Full AlphaFold Entry ↗", "https://alphafold.ebi.ac.uk/entry/P15529")

with str_tab:
    st.markdown(
        "<div style='background:#1e293b;border-left:3px solid #818cf8;padding:12px 16px;"
        "border-radius:6px;margin-bottom:14px;'>"
        "<b style='color:#818cf8;'>CD46 Protein Interaction Network — STRING Database</b><br>"
        "<span style='color:#94a3b8;'>Homo sapiens (taxid: 9606) · Combined score > 400 · "
        "Physical + functional interactions</span>"
        "</div>",
        unsafe_allow_html=True,
    )

    @st.cache_data(ttl=86_400, show_spinner=False)
    def _fetch_string() -> list:
        try:
            import requests as _req
            resp = _req.get(
                "https://string-db.org/api/json/interaction_partners",
                params={
                    "identifiers": "CD46",
                    "species": 9606,
                    "limit": 25,
                    "caller_identity": "cd46_precision_medicine_platform",
                },
                timeout=15,
            )
            if resp.status_code == 200:
                return resp.json()
        except Exception:
            pass
        return []

    with st.spinner("Loading STRING interaction network…"):
        string_data = _fetch_string()

    if string_data:
        st.success(f"✅ {len(string_data)} interaction partners loaded (STRING DB)")

    if string_data:
        import pandas as pd
        import plotly.graph_objects as go
        import math

        interactions = string_data
        df_str = pd.DataFrame(interactions)

        # Key complement pathway genes to highlight
        COMPLEMENT_GENES = {"CD55", "CD59", "CR2", "C3", "C4A", "C4B", "C1QA", "CFH", "MCP", "CR1"}

        # Display table
        if not df_str.empty:
            display_cols = ["preferredName_B", "score", "nscore", "escore", "fscore", "tscore"]
            available = [c for c in display_cols if c in df_str.columns]
            df_show = df_str[available].copy()
            df_show.columns = [c.replace("preferredName_B", "Partner").replace("score", "Combined").replace(
                "nscore", "Neighborhood").replace("escore", "Experiment").replace(
                "fscore", "Co-occurrence").replace("tscore", "Text-mining") for c in available]
            df_show["Complement?"] = df_show["Partner"].apply(
                lambda x: "🔴" if x in COMPLEMENT_GENES else ""
            )
            st.dataframe(
                df_show.sort_values("Combined", ascending=False).head(25),
                use_container_width=True,
                hide_index=True,
            )

            # Plotly network graph
            partner_names = [r.get("preferredName_B", "") for r in interactions[:20]]
            scores = [r.get("score", 0) / 1000 for r in interactions[:20]]

            # Arrange partners in a circle around CD46
            n = len(partner_names)
            angles = [2 * math.pi * i / n for i in range(n)]
            cx, cy = [math.cos(a) for a in angles], [math.sin(a) for a in angles]

            node_x = [0] + cx
            node_y = [0] + cy
            node_text = ["CD46"] + partner_names
            node_colors = ["#38bdf8"] + [
                "#f87171" if p in COMPLEMENT_GENES else "#818cf8"
                for p in partner_names
            ]
            node_sizes = [28] + [12 + int(s * 10) for s in scores]

            edge_x, edge_y = [], []
            for i in range(n):
                edge_x += [0, cx[i], None]
                edge_y += [0, cy[i], None]

            fig_str = go.Figure()
            fig_str.add_trace(go.Scatter(
                x=edge_x, y=edge_y,
                mode="lines",
                line=dict(width=0.8, color="#334155"),
                hoverinfo="none",
                showlegend=False,
            ))
            fig_str.add_trace(go.Scatter(
                x=node_x, y=node_y,
                mode="markers+text",
                marker=dict(size=node_sizes, color=node_colors, line=dict(width=1, color="#0f172a")),
                text=node_text,
                textposition="top center",
                textfont=dict(size=9, color="#e2e8f0"),
                hovertext=[
                    f"CD46 — hub node" if i == 0
                    else f"{partner_names[i-1]}<br>Score: {scores[i-1]:.3f}"
                    for i in range(n + 1)
                ],
                hoverinfo="text",
                showlegend=False,
            ))
            fig_str.update_layout(
                height=440,
                paper_bgcolor="#0f172a",
                plot_bgcolor="#0f172a",
                xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                margin=dict(l=10, r=10, t=30, b=10),
                title=dict(
                    text="CD46 Protein Interaction Network (STRING DB)",
                    font=dict(color="#e2e8f0", size=13),
                ),
            )
            st.plotly_chart(fig_str, width='stretch')
            st.caption("🔴 Red = Complement pathway partners · 🔵 Blue = CD46 hub · Purple = Other interactions")

    st.info(
        "💡 CD46 physically interacts with complement proteins C3b, C4b, and factor I. "
        "It also associates with measles virus receptor complex — a known therapeutic vulnerability. "
        "STRING combined score > 0.7 indicates high-confidence interaction."
    )
    st.link_button(
        "Open CD46 in STRING ↗",
        "https://string-db.org/network/9606.ENSP00000317276",
    )

with pub_tab:
    st.markdown(
        "<div style='background:#1e293b;border-left:3px solid #4ade80;padding:12px 16px;"
        "border-radius:6px;margin-bottom:14px;'>"
        "<b style='color:#4ade80;'>Curated CD46 Evidence Base</b><br>"
        "<span style='color:#94a3b8;'>Peer-reviewed publications from AuraDB knowledge graph · "
        "Foundational papers for 225Ac-CD46 program</span>"
        "</div>",
        unsafe_allow_html=True,
    )

    # Load from AuraDB if connected
    pub_records = []
    if driver is not None:
        try:
            with driver.session() as session:
                result = session.run(
                    "MATCH (pub:Publication) RETURN pub ORDER BY pub.year DESC"
                )
                pub_records = [dict(rec["pub"]) for rec in result]
        except Exception as e:
            st.warning(f"Could not load publications from KG: {e}")

    if not pub_records:
        st.info("No publications in knowledge graph yet — run `scripts/load_kg_extras.py` to populate.")
    else:
        # Evidence type filter
        ev_types = sorted({p.get("evidence_type", "Other") for p in pub_records})
        sel_types = st.multiselect("Filter by evidence type", ev_types, default=ev_types)
        filtered = [p for p in pub_records if p.get("evidence_type", "Other") in sel_types]

        for pub in filtered:
            pmid = pub.get("pubmed_id", "")
            url = f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/" if pmid else "#"
            ev_color = {
                "Experimental": "#f87171",
                "Clinical trial": "#fb923c",
                "Clinical-translational": "#fbbf24",
                "Biomarker": "#4ade80",
                "Preclinical": "#818cf8",
                "Bioinformatics": "#38bdf8",
                "Review": "#94a3b8",
            }.get(pub.get("evidence_type", ""), "#64748b")

            st.markdown(
                f"""
                <div style='background:#1e293b;border:1px solid #334155;border-left:4px solid {ev_color};
                padding:14px 16px;margin:8px 0;border-radius:6px;'>
                <span style='background:{ev_color}22;color:{ev_color};font-size:0.75em;
                padding:2px 8px;border-radius:12px;font-weight:600;'>
                {pub.get('evidence_type','').upper()}</span>
                <b style='color:#e2e8f0;display:block;margin-top:8px;font-size:1.0em;'>
                {pub.get('title','')}</b>
                <span style='color:#94a3b8;font-size:0.84em;'>
                {', '.join(pub.get('authors', [])) if isinstance(pub.get('authors'), list) else pub.get('authors','')}</span><br>
                <span style='color:#64748b;font-size:0.82em;'>
                {pub.get('journal','')} &middot; {pub.get('year','')}</span><br>
                <span style='color:#38bdf8;font-size:0.84em;margin-top:6px;display:block;'>
                \u2192 {pub.get('key_finding','')}</span>
                </div>
                """,
                unsafe_allow_html=True,
            )
            if pmid and pmid != "#":
                st.link_button(f"PubMed {pmid} ↗", url)

st.markdown("---")
st.markdown(
    "<div style='color:#64748b; font-size:0.8em;'>"
    "Knowledge graph: 1,452+ nodes · Gene, Protein, Disease, Drug, PatientGroup, CellLine, "
    "Pathway, Tissue, Publication, ClinicalTrial node types. "
    "AlphaFold: EBI structure prediction (pLDDT confidence). "
    "STRING: protein–protein interaction network (Homo sapiens)."
    "</div>",
    unsafe_allow_html=True,
)
