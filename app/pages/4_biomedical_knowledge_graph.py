"""Page 4 — Knowledge Graph Explorer (PyVis + Cypher query runner)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import json
import os

from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parents[2] / ".env")

import streamlit as st


st.title("🕸️ Biomedical Knowledge Graph")
st.markdown(
    "**Neo4j AuraDB knowledge network — genes, proteins, diseases, drugs, clinical trials, and patient cohorts. "
    "Interactive graph visualization and Cypher query interface.**"
)

# ---------------------------------------------------------------------------
# Connection check
# ---------------------------------------------------------------------------

@st.cache_resource
def get_driver():
    from neo4j import GraphDatabase

    uri = os.getenv("NEO4J_URI")
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

st.markdown("---")
st.markdown(
    "<div style='color:#64748b; font-size:0.8em;'>"
    "Knowledge graph: 1,452 nodes · 353 relationships · Gene, Protein, Disease, Drug, PatientGroup, CellLine, Pathway, Tissue node types. "
    "Phase 2 expansion: AACR GENIE genomics integration."
    "</div>",
    unsafe_allow_html=True,
)
