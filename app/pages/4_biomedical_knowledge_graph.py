"""Page 4 — Biomedical Knowledge Graph: network explorer, Cypher queries, protein deep-dive."""
import json
import math
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[2] / ".env")

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from components.styles import page_hero

# Inject Streamlit Cloud secrets into os.environ
for _k in ("NEO4J_URI", "NEO4J_USERNAME", "NEO4J_PASSWORD"):
    try:
        if _k in st.secrets and not os.environ.get(_k):
            os.environ[_k] = st.secrets[_k]
    except Exception:
        pass

# ---------------------------------------------------------------------------
# Theme constants
# ---------------------------------------------------------------------------
_BG     = "#0D1829"
_LINE   = "#16243C"
_INDIGO = "#818CF8"
_ROSE   = "#F472B6"
_GREEN  = "#34D399"
_AMBER  = "#FBBF24"
_SLATE  = "#475569"
_MID    = "#4E637A"
_TEXT   = "#94A3B8"
_LIGHT  = "#CBD5E1"
_RED    = "#F87171"

_PLOTLY_LAYOUT = dict(
    paper_bgcolor="#0f172a",
    plot_bgcolor="#0f172a",
    font=dict(family="Inter", color=_TEXT),
)

# ---------------------------------------------------------------------------
# Neo4j connection
# ---------------------------------------------------------------------------
@st.cache_resource(ttl=300)
def get_driver():
    from neo4j import GraphDatabase
    uri      = os.getenv("NEO4J_URI")
    user     = os.getenv("NEO4J_USERNAME", "neo4j")
    password = os.getenv("NEO4J_PASSWORD")
    if not uri or not password:
        return None, "NEO4J credentials not set — add NEO4J_URI and NEO4J_PASSWORD to .env"
    try:
        driver = GraphDatabase.driver(uri, auth=(user, password))
        driver.verify_connectivity()
        return driver, None
    except Exception as e:
        return None, str(e)

driver, conn_error = get_driver()

# ---------------------------------------------------------------------------
# Live KG stats (or static fallback)
# ---------------------------------------------------------------------------
@st.cache_data(ttl=300)
def _live_stats():
    if driver is None:
        return None
    LABELS = ["Gene","Protein","Disease","Tissue","Drug","ClinicalTrial",
               "PatientGroup","CellLine","AnalysisResult","Publication","Pathway","DataSource"]
    try:
        with driver.session() as sess:
            counts = {}
            for lbl in LABELS:
                r = sess.run(f"MATCH (n:{lbl}) RETURN count(n) AS c")
                counts[lbl] = r.single()["c"]
            total_nodes = sum(counts.values())
            total_rels  = sess.run("MATCH ()-[r]->() RETURN count(r) AS c").single()["c"]
        return {"counts": counts, "total_nodes": total_nodes, "total_rels": total_rels}
    except Exception:
        return None

stats = _live_stats()

_total_nodes = f"{stats['total_nodes']:,}"            if stats else "~3,912"
_total_rels  = f"{stats['total_rels']:,}"             if stats else "~14,880"
_drug_count  = str(stats["counts"].get("Drug", 10))   if stats else "10"
_disease_ct  = str(stats["counts"].get("Disease",797)) if stats else "797"

# ---------------------------------------------------------------------------
# Page hero
# ---------------------------------------------------------------------------
st.markdown(
    page_hero(
        icon="🕸️",
        module_name="Biomedical Knowledge Graph",
        purpose=(
            "Neo4j AuraDB · genes, proteins, diseases, drugs, clinical trials, patient cohorts "
            "· interactive force-directed graph + Cypher interface + protein structural biology"
        ),
        kpi_chips=[
            ("KG Nodes",      _total_nodes),
            ("KG Edges",      _total_rels),
            ("Drug Nodes",    _drug_count),
            ("Disease Links", _disease_ct),
        ],
        source_badges=["UniProt", "OpenTargets", "ChEMBL", "STRING", "ClinicalTrials"],
    ),
    unsafe_allow_html=True,
)

if conn_error:
    st.warning(
        f"AuraDB not connected: {conn_error}  "
        "Set NEO4J_URI / NEO4J_PASSWORD in `.env` to enable live queries.",
    )
else:
    st.success("Connected to AuraDB knowledge graph")

k1, k2, k3, k4 = st.columns(4)
k1.metric("Total Nodes",         _total_nodes, "genes, proteins, diseases, drugs")
k2.metric("Total Relationships", _total_rels,  "typed biological edges")
k3.metric("Drug Nodes",          _drug_count,  "CD46-targeting agents")
k4.metric("Disease Nodes",       _disease_ct,  "linked to CD46")
st.markdown("---")

# ---------------------------------------------------------------------------
# Tabs
# ---------------------------------------------------------------------------
tab_net, tab_query, tab_protein = st.tabs([
    "Network Explorer",
    "Cypher Query Explorer",
    "Protein and Evidence",
])

# ==========================================================================
# TAB 1 — Network Explorer
# ==========================================================================
with tab_net:
    st.markdown("#### Biomedical Knowledge Graph — Force-Directed Network")
    st.caption(
        "Select a biological dimension, then click Load Network to render the live graph. "
        "Drag nodes to rearrange. Hover for metadata. Colour-coded by entity type."
    )

    COLOR_MAP = {
        "Gene":          "#6366F1",
        "Protein":       "#6366F1",
        "Disease":       "#EF4444",
        "Tissue":        "#22C55E",
        "Drug":          "#F59E0B",
        "ClinicalTrial": "#F59E0B",
        "Pathway":       "#0EA5E9",
        "DataSource":    "#94A3B8",
        "PatientGroup":  "#22C55E",
        "CellLine":      "#94A3B8",
        "Publication":   "#34D399",
    }

    NETWORK_SCENARIOS = {
        "CD46 Gene — All Direct Connections": {
            "description": "CD46 gene radiating to proteins, drugs, pathways, diseases, and publications.",
            "two_hop":    False,
            "multi_edge": False,
        },
        "Disease — Patient Groups (75th pct)": {
            "description": "Cancer types connected to CD46-High patient cohorts at 75th percentile threshold.",
            "cypher": (
                "MATCH (d:Disease)-[:HAS_PATIENT_GROUP]->(pg:PatientGroup) "
                "WHERE pg.threshold_method = '75th_pct' RETURN d, pg LIMIT 40"
            ),
            "two_hop":    False,
            "multi_edge": True,
        },
        "Cell Lines — CD46 Dependency": {
            "description": "Cancer cell lines where CRISPR knockout of CD46 reduces fitness.",
            "cypher": (
                "MATCH (cl:CellLine)-[:DEPENDS_ON]->(g:Gene {symbol: 'CD46'}) "
                "RETURN cl, g LIMIT 30"
            ),
            "two_hop":    False,
            "multi_edge": True,
        },
        "Full CD46 Ecosystem (two-hop, 50 nodes)": {
            "description": "Panoramic: genes, proteins, diseases, drugs, pathways all connected via CD46.",
            "cypher": (
                "MATCH (g:Gene {symbol: 'CD46'})-[r1]->(a) "
                "OPTIONAL MATCH (a)-[r2]->(b) "
                "RETURN g, type(r1) AS rel1, a, type(r2) AS rel2, b LIMIT 50"
            ),
            "two_hop":    True,
            "multi_edge": False,
        },
    }

    def _node_display(n):
        for key in ["symbol", "tcga_code", "name", "tissue_name", "depmap_id", "nct_id"]:
            val = n.get(key)
            if val and str(val).strip():
                return str(val)[:22]
        return "node"

    def _node_id(n, label):
        for key in ["symbol", "tcga_code", "uniprot_id", "depmap_id", "nct_id", "name"]:
            val = n.get(key)
            if val:
                return f"{label}_{val}"
        return f"{label}_{id(n)}"

    scen_col, _ = st.columns([2, 3])
    scenario_sel = scen_col.selectbox(
        "Choose a network view", options=list(NETWORK_SCENARIOS.keys()), index=0
    )
    scenario = NETWORK_SCENARIOS[scenario_sel]
    st.info(scenario["description"])
    st.caption(
        "Blue = Gene/Protein  |  Red = Disease  |  Yellow = Drug/Trial  "
        "|  Green = Tissue/PatientGroup  |  Cyan = Pathway"
    )

    if driver is None:
        st.markdown(
            """
**Knowledge graph relationship types:**

| Relationship | Meaning |
|---|---|
| `EXPRESSED_IN` | CD46 mRNA/protein detected in this cancer/tissue |
| `TARGETS` | Drug or antibody binds CD46 |
| `PARTICIPATES_IN` | CD46 participates in this pathway (complement, immune evasion) |
| `INTERACTS_WITH` | Protein-protein interaction (STRING, score > 0.4) |
| `HAS_PATIENT_GROUP` | Cancer type connected to CD46-High patient cohort |
| `DEPENDS_ON` | Cell line fitness reduced by CD46 CRISPR knockout |
| `HAS_EVIDENCE_FROM` | Claim sourced from this publication / trial |

Each node carries full metadata as properties: expression values, p-values,
UniProt IDs, ClinicalTrials NCT numbers, DepMap scores.
"""
        )
    else:
        if st.button("Load Network", key="load_network"):
            try:
                from pyvis.network import Network
                import streamlit.components.v1 as components

                net = Network(
                    height="560px", width="100%",
                    bgcolor="#0B1120", font_color="#F8FAFC", directed=True,
                )
                net.set_options(
                    '{"physics":{"barnesHut":{"gravitationalConstant":-6000,"springLength":120},'
                    '"stabilization":{"iterations":120}},'
                    '"nodes":{"font":{"size":11,"face":"Inter, sans-serif","color":"#F8FAFC"},'
                    '"borderWidth":2},'
                    '"edges":{"color":{"color":"#1E293B"},"smooth":{"type":"continuous"},'
                    '"arrows":{"to":{"enabled":true,"scaleFactor":0.5}}}}'
                )
                added_nodes = set()

                def add_node(node, label_override=None):
                    labels = list(node.labels) if hasattr(node, "labels") else []
                    lbl = label_override or (labels[0] if labels else "Node")
                    nid = _node_id(node, lbl)
                    if nid not in added_nodes:
                        color = COLOR_MAP.get(lbl, "#e2e8f0")
                        size  = 24 if lbl in ("Gene", "Protein") else 14
                        title = (
                            f"<b>{lbl}</b><br>"
                            + "<br>".join(
                                f"{k}: {v}" for k, v in dict(node).items() if v is not None
                            )[:400]
                        )
                        net.add_node(nid, label=_node_display(node), color=color,
                                     size=size, title=title, font={"size": 11})
                        added_nodes.add(nid)
                    return nid

                with driver.session() as sess:
                    scn = scenario
                    if scn.get("two_hop"):
                        for rec in sess.run(scn["cypher"]):
                            g, a = rec["g"], rec["a"]
                            rel1 = rec.get("rel1", "RELATED")
                            gid  = add_node(g)
                            aid  = add_node(a)
                            net.add_edge(gid, aid, label=rel1, color="#475569", title=rel1)
                            b, rel2 = rec.get("b"), rec.get("rel2")
                            if b is not None and rel2:
                                net.add_edge(aid, add_node(b), label=rel2, color="#334155", title=rel2)
                    elif scn.get("multi_edge"):
                        for rec in sess.run(scn["cypher"]):
                            keys = list(rec.keys())
                            net.add_edge(add_node(rec[keys[0]]), add_node(rec[keys[1]]), color="#475569")
                    else:
                        for rec in sess.run(
                            "MATCH (g:Gene {symbol:'CD46'})-[r]->(n) "
                            "RETURN g, type(r) AS rel_type, n, 'out' AS direction LIMIT 30 "
                            "UNION "
                            "MATCH (n)-[r]->(g:Gene {symbol:'CD46'}) "
                            "RETURN g, type(r) AS rel_type, n, 'in' AS direction LIMIT 20"
                        ):
                            g  = rec["g"]
                            n  = rec["n"]
                            rt = rec["rel_type"]
                            gid = add_node(g, "Gene")
                            nid = add_node(n)
                            if rec.get("direction", "out") == "out":
                                net.add_edge(gid, nid, label=rt, color="#475569", title=rt)
                            else:
                                net.add_edge(nid, gid, label=rt, color="#64748b", title=rt)

                if len(added_nodes) == 0:
                    st.warning("No nodes returned — this graph view may not have data yet.")
                else:
                    st.caption(f"Rendered {len(added_nodes)} nodes. Drag to rearrange. Hover for details.")
                    components.html(net.generate_html(), height=580)
            except ImportError:
                st.error("PyVis not installed — run: pip install pyvis")
            except Exception as e:
                st.error(f"Network render error: {e}")

    st.markdown("---")
    st.markdown("#### Knowledge Graph Node Summary")
    sum_c1, sum_c2 = st.columns(2)

    with sum_c1:
        if stats:
            count_items = sorted(stats["counts"].items(), key=lambda x: x[1], reverse=True)
            labels_bar  = [k for k, _ in count_items]
            values_bar  = [v for _, v in count_items]
            fig_counts  = go.Figure(go.Bar(
                x=values_bar, y=labels_bar, orientation="h",
                marker_color=[COLOR_MAP.get(lb, "#64748b") for lb in labels_bar],
                hovertemplate="<b>%{y}</b><br>Count: %{x:,}<extra></extra>",
            ))
            fig_counts.update_layout(
                **_PLOTLY_LAYOUT, height=320,
                xaxis=dict(title="Node count", gridcolor=_LINE, color=_TEXT),
                yaxis=dict(color=_LIGHT, autorange="reversed"),
                margin=dict(l=0, r=0, t=10, b=30),
            )
            st.plotly_chart(fig_counts, use_container_width=True)
        else:
            st.markdown(
                "| Node type | Count |\n|---|---|\n"
                "| Disease | 797 |\n| PatientGroup | ~600 |\n| CellLine | ~600 |\n"
                "| AnalysisResult | ~400 |\n| Publication | 55 |\n| ClinicalTrial | 14 |\n"
                "| Protein | 12 |\n| Drug | 10 |\n| Pathway | 8 |\n| Gene | 1 |"
            )

    with sum_c2:
        st.markdown(
            """
**Node types in the CD46 knowledge graph:**

| Type | Description |
|---|---|
| **Gene** | CD46 (MRC; Ensembl ENSG00000117335) |
| **Protein** | STA-1, STA-2, LCA-1, LCA-2 isoforms (UniProt P15529) |
| **Disease** | 24+ TCGA cancers with expression + survival stats |
| **Drug** | CD46-targeting agents (225Ac-PSMA-CD46, mAbs, bispecifics) |
| **ClinicalTrial** | 14 active trials from ClinicalTrials.gov |
| **PatientGroup** | CD46-High/Low cohorts at median, 75th, 90th percentile |
| **CellLine** | 1,186 DepMap cell lines with CRISPR + mRNA scores |
| **Pathway** | Complement system, immune evasion, MAPK, PI3K-Akt |
| **Publication** | 55 curated PubMed papers |
| **Tissue** | HPA + GTEx tissue expression nodes |

**Edge types:** EXPRESSED_IN · TARGETS · PARTICIPATES_IN · INTERACTS_WITH
· HAS_PATIENT_GROUP · DEPENDS_ON · HAS_EVIDENCE_FROM · ENCODES
"""
        )

# ==========================================================================
# TAB 2 — Cypher Query Explorer
# ==========================================================================
with tab_query:
    st.markdown("#### Cypher Query Explorer — Live Biological Reasoning")
    st.caption(
        "Select a pre-built query or write your own. "
        "Only read-only MATCH queries are permitted. "
        "Results stream from the AuraDB knowledge graph."
    )
    if conn_error:
        st.warning("AuraDB not connected — queries shown for reference, cannot execute.")

    def _run_query(cypher: str):
        if driver is None:
            st.error("Knowledge graph not connected — check credentials.")
            return
        cypher_upper = cypher.strip().upper()
        forbidden = ["CREATE", "MERGE", "DELETE", "SET ", "REMOVE", "DROP"]
        if any(cypher_upper.startswith(k) or f" {k} " in cypher_upper for k in forbidden):
            st.error("Write operations are not permitted. Use read-only MATCH queries.")
            return
        try:
            with driver.session() as sess:
                records = [dict(rec) for rec in sess.run(cypher)]
            if records:
                st.dataframe(pd.DataFrame(records), use_container_width=True)
                st.caption(f"{len(records)} records returned")
            else:
                st.info("Query returned no results — data may not yet be in the graph.")
        except Exception as e:
            st.error(f"Query error: {e}")

    QUERY_GROUPS = {
        "Cancer Prioritisation": {
            "Top cancers by CD46 priority score": (
                "MATCH (d:Disease) WHERE d.priority_score IS NOT NULL "
                "RETURN d.tcga_code AS cancer, d.name AS name, "
                "round(d.priority_score * 100) / 100 AS priority_score, "
                "d.priority_label AS priority_label "
                "ORDER BY d.priority_score DESC LIMIT 10",
                "Ranks cancer types by composite CD46 therapeutic opportunity score.",
            ),
            "All cancers with CD46 expression levels": (
                "MATCH (d:Disease) WHERE d.cd46_mean_tpm_log2 IS NOT NULL "
                "RETURN d.tcga_code AS cancer, d.name AS name, "
                "round(d.cd46_mean_tpm_log2 * 100) / 100 AS cd46_mean_log2, "
                "d.cd46_expression_rank AS rank "
                "ORDER BY d.cd46_mean_tpm_log2 DESC",
                "All 25 cancer types with mean CD46 log2 expression.",
            ),
            "Survival impact by cancer type": (
                "MATCH (d:Disease) WHERE d.cd46_survival_hr IS NOT NULL "
                "RETURN d.tcga_code AS cancer, "
                "round(d.cd46_survival_hr * 100) / 100 AS hazard_ratio, "
                "round(d.cd46_survival_pval * 1000) / 1000 AS p_value "
                "ORDER BY d.cd46_survival_hr DESC",
                "Cox hazard ratio for CD46-High vs CD46-Low across cancer types.",
            ),
        },
        "Drug Targets": {
            "CD46-targeting drugs": (
                "MATCH (dr:Drug)-[:TARGETS]->(g:Gene {symbol: 'CD46'}) "
                "RETURN dr.name AS drug, dr.drug_type AS modality, "
                "dr.clinical_stage AS stage, dr.mechanism AS mechanism, dr.isotope AS isotope",
                "All therapeutic agents in the knowledge graph targeting CD46.",
            ),
            "Drug mechanisms of action": (
                "MATCH (dr:Drug)-[:TARGETS]->(g:Gene {symbol: 'CD46'}) "
                "RETURN dr.name AS drug, dr.mechanism AS mechanism, dr.developer AS developer",
                "Detailed mechanism and developer for each CD46-targeting therapy.",
            ),
            "CD46 gene and its pathways": (
                "MATCH (g:Gene {symbol: 'CD46'})-[:PARTICIPATES_IN]->(pw:Pathway) "
                "RETURN g.symbol AS gene, pw.name AS pathway, pw.category AS category, "
                "pw.reactome_id AS reactome_id",
                "Biological pathways where CD46 participates.",
            ),
        },
        "Patient Cohorts": {
            "PRAD patient eligibility by threshold": (
                "MATCH (d:Disease {tcga_code: 'PRAD'})-[:HAS_PATIENT_GROUP]->(pg:PatientGroup) "
                "RETURN pg.threshold_method AS threshold, pg.expression_group AS cd46_group, "
                "pg.n_patients AS n_patients ORDER BY pg.expression_group",
                "CD46-High patient counts in PRAD at each expression threshold.",
            ),
            "Top 10 diseases by eligible patients (75th pct)": (
                "MATCH (d:Disease)-[:HAS_PATIENT_GROUP]->(pg:PatientGroup) "
                "WHERE pg.threshold_method = '75th_pct' AND pg.expression_group = 'CD46-High' "
                "RETURN d.tcga_code AS cancer, d.name AS name, pg.n_patients AS cd46_high_patients "
                "ORDER BY pg.n_patients DESC LIMIT 10",
                "Diseases with most CD46-High patients at the 75th percentile threshold.",
            ),
            "All patient groups — median split": (
                "MATCH (pg:PatientGroup) WHERE pg.threshold_method = 'median' "
                "AND pg.expression_group = 'CD46-High' "
                "RETURN pg.cancer_type AS cancer, pg.n_patients AS eligible "
                "ORDER BY pg.n_patients DESC",
                "CD46-High patient counts across all cancers using median split.",
            ),
        },
        "Biology and Tissue": {
            "Tumour tissues with CD46 protein": (
                "MATCH (p:Protein)-[e:EXPRESSED_IN]->(t:Tissue) WHERE t.type = 'tumor' "
                "RETURN t.name AS tissue, p.symbol AS protein, p.isoform AS isoform "
                "ORDER BY t.name",
                "Tumour tissue types where CD46 protein is expressed (HPA).",
            ),
            "Normal tissues expressing CD46": (
                "MATCH (p:Protein)-[e:EXPRESSED_IN]->(t:Tissue) WHERE t.type = 'normal' "
                "RETURN t.name AS tissue, p.symbol AS protein, p.isoform AS isoform "
                "ORDER BY t.name",
                "Normal tissue distribution — key for therapeutic window assessment.",
            ),
            "CD46 protein isoforms": (
                "MATCH (g:Gene {symbol: 'CD46'})-[:ENCODES]->(p:Protein) "
                "RETURN g.symbol AS gene, p.uniprot_id AS uniprot_id, p.isoform AS isoform, "
                "p.molecular_weight_kda AS mol_weight_kDa, p.surface_expressed AS surface_expressed",
                "CD46 isoforms STA-1, STA-2, LCA-1, LCA-2 and their properties.",
            ),
        },
        "Cell Lines and Dependency": {
            "Cell lines where CD46 is a dependency": (
                "MATCH (cl:CellLine)-[:DEPENDS_ON]->(g:Gene {symbol: 'CD46'}) "
                "RETURN cl.name AS cell_line, cl.cancer_type AS cancer, "
                "round(cl.cd46_crispr_score * 1000) / 1000 AS crispr_score "
                "ORDER BY cl.cd46_crispr_score ASC LIMIT 20",
                "Cancer cell lines where CD46 CRISPR knockout reduces fitness.",
            ),
            "High CD46 expression cell lines": (
                "MATCH (cl:CellLine) WHERE cl.cd46_expression_tpm > 0 "
                "RETURN cl.name AS cell_line, cl.cancer_type AS cancer, "
                "round(cl.cd46_expression_tpm * 100) / 100 AS cd46_tpm, "
                "cl.cd46_is_dependency AS is_dependency "
                "ORDER BY cl.cd46_expression_tpm DESC LIMIT 20",
                "Cell lines ranked by CD46 mRNA expression level.",
            ),
            "PRAD-specific cell lines": (
                "MATCH (cl:CellLine) WHERE cl.cancer_type = 'Prostate Cancer' "
                "RETURN cl.name AS cell_line, cl.cancer_type AS cancer, "
                "cl.cd46_expression_tpm AS cd46_tpm, cl.cd46_is_dependency AS is_dependency",
                "Prostate cancer cell lines with CD46 expression and essentiality data.",
            ),
        },
        "Custom Query": {},
    }

    q_tabs = st.tabs(list(QUERY_GROUPS.keys()))
    for q_tab, (group_name, queries) in zip(q_tabs, QUERY_GROUPS.items()):
        with q_tab:
            if group_name == "Custom Query":
                st.markdown("Write any read-only MATCH Cypher query below.")
                st.code(
                    "MATCH (g:Gene {symbol:'CD46'})-[r]-(t) "
                    "RETURN type(r), count(t) ORDER BY count(t) DESC",
                    language="cypher",
                )
                custom_q = st.text_area(
                    "Your Cypher query",
                    value="MATCH (g:Gene) RETURN g.symbol, g.ensembl_id LIMIT 5",
                    height=120,
                    key="custom_cypher",
                )
                if st.button("Run", key="run_custom"):
                    _run_query(custom_q)
            else:
                for q_name, (cypher, description) in queries.items():
                    with st.expander(f"**{q_name}**", expanded=False):
                        st.caption(description)
                        st.code(cypher, language="cypher")
                        if st.button(f"Run: {q_name}", key=f"btn_{q_name}"):
                            _run_query(cypher)

    st.markdown("---")
    st.markdown(
        "> **Why Cypher?** Graph databases use pattern-matching queries that read like natural language. "
        "`MATCH (g:Gene)-[:TARGETS]->(d:Drug)` is immediately interpretable. "
        "The knowledge graph is the factual backbone for the AI Research Assistant on page 5 — "
        "the LLM retrieves structured facts, not hallucinations."
    )

# ==========================================================================
# TAB 3 — Protein and Evidence
# ==========================================================================
with tab_protein:
    af_sub, str_sub, pub_sub = st.tabs([
        "AlphaFold Structure",
        "STRING Network",
        "Publications",
    ])

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
            rows = (
                d.get("data", {})
                 .get("target", {})
                 .get("associatedDiseases", {})
                 .get("rows", [])
            )
            return rows
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

    uni     = _load_uniprot()
    ot_rows = _load_open_targets()

    # ------------------------------------------------------------------
    with af_sub:
        st.markdown(
            "<div style='background:#1e293b;border-left:3px solid #38bdf8;"
            "padding:14px 18px;border-radius:8px;margin-bottom:18px;'>"
            "<span style='font-size:1.1em;font-weight:700;color:#38bdf8;'>"
            "CD46 — Membrane Cofactor Protein (MCP)</span>"
            "&nbsp;&nbsp;<span style='background:#0f172a;color:#94a3b8;"
            "font-size:0.78em;padding:2px 9px;border-radius:12px;'>"
            "UniProt P15529 · Homo sapiens</span></div>",
            unsafe_allow_html=True,
        )

        comments     = uni.get("comments", [])
        func_text    = next(
            (c["texts"][0]["value"] for c in comments
             if c.get("commentType") == "FUNCTION" and c.get("texts")), ""
        )
        annot_score  = uni.get("annotationScore", 5.0)
        seq_len      = uni.get("sequence", {}).get("length", 392)
        features     = uni.get("features", [])
        nat_variants = [f for f in features if f.get("type") == "Natural variant"]
        alt_products = next(
            (c for c in comments if c.get("commentType") == "ALTERNATIVE PRODUCTS"), {}
        )
        isoforms     = alt_products.get("isoforms", [])
        isoform_note = (
            alt_products.get("note", {}).get("texts", [{}])[0].get("value", "")
        )

        pc1, pc2, pc3, pc4 = st.columns(4)
        pc1.metric("Sequence Length",  f"{seq_len} aa")
        pc2.metric("Apparent MW",      "56-66 kDa")
        pc3.metric("UniProt Score",    f"{annot_score:.0f}/5")
        pc4.metric("Natural Variants", len(nat_variants))

        if func_text:
            st.markdown(
                f"<div style='background:#0f172a;border:1px solid #334155;"
                f"padding:12px 16px;border-radius:6px;color:#cbd5e1;"
                f"font-size:0.88em;line-height:1.6;'>"
                f"<b style='color:#38bdf8;'>Function:</b> {func_text}</div>",
                unsafe_allow_html=True,
            )

        st.markdown("#### Protein Domain Architecture")
        DOMAIN_SEGMENTS = [
            ("Signal peptide",      1,   34, "#64748b"),
            ("SCR / Sushi 1",      35,   96, "#3b82f6"),
            ("SCR / Sushi 2",      97,  159, "#6366f1"),
            ("SCR / Sushi 3",     160,  225, "#8b5cf6"),
            ("SCR / Sushi 4",     226,  285, "#a855f7"),
            ("STP-rich O-glycan", 286,  343, "#ec4899"),
            ("Transmembrane",     344,  366, "#f59e0b"),
            ("Cytoplasmic tail",  367,  392, "#10b981"),
        ]
        dom_fig = go.Figure()
        for dname, dstart, dend, dcolor in DOMAIN_SEGMENTS:
            dom_fig.add_trace(go.Bar(
                x=[dend - dstart + 1], y=["CD46"], base=[dstart - 1],
                orientation="h", marker_color=dcolor, name=dname,
                hovertemplate=(
                    f"<b>{dname}</b><br>"
                    f"Residues {dstart}-{dend}<br>"
                    f"Length: {dend - dstart + 1} aa<extra></extra>"
                ),
            ))
        dom_fig.update_layout(
            barmode="stack", height=120,
            margin=dict(l=0, r=0, t=10, b=30),
            paper_bgcolor="#0f172a", plot_bgcolor="#0f172a",
            xaxis=dict(title="Residue position", color=_TEXT, gridcolor=_LINE, range=[0, seq_len + 5]),
            yaxis=dict(showticklabels=False, showgrid=False),
            legend=dict(
                orientation="h", y=-0.7, x=0,
                font=dict(size=10, color=_TEXT), bgcolor="rgba(0,0,0,0)",
            ),
        )
        st.plotly_chart(dom_fig, use_container_width=True)

        st.markdown("#### Natural Variants")
        if nat_variants:
            var_rows = []
            for v in nat_variants:
                pos    = v.get("location", {}).get("start", {}).get("value", "?")
                alt_s  = v.get("alternativeSequence", {})
                orig   = alt_s.get("originalSequence", "?")
                alts   = alt_s.get("alternativeSequences", ["?"])
                var_aa = alts[0] if alts else "?"
                cross  = v.get("featureCrossReferences", [])
                dbsnp  = next((r["id"] for r in cross if r.get("database") == "dbSNP"), "")
                desc   = v.get("description", "")
                dis    = ""
                if "in " in desc:
                    pts = [p.strip() for p in desc.split(";") if not p.strip().startswith("dbSNP")]
                    dis = "; ".join(p.replace("in ", "") for p in pts if p and not p.startswith("dbSNP")).strip()
                var_rows.append({
                    "Position": pos,
                    "Change":   f"{orig} -> {var_aa}",
                    "dbSNP":    dbsnp,
                    "Disease / Note": dis or "-",
                })
            st.dataframe(pd.DataFrame(var_rows).sort_values("Position"), use_container_width=True, hide_index=True)
        else:
            st.info("Natural variant data not available — check data/raw/apis/uniprot_cd46.json")

        st.markdown("#### Protein Isoforms")
        if isoform_note:
            st.caption(isoform_note)
        if isoforms:
            iso_rows = []
            for iso in isoforms:
                iname = iso.get("name", {}).get("value", "?")
                syns  = [s.get("value", "") for s in iso.get("synonyms", [])]
                iso_rows.append({
                    "Isoform":         iname,
                    "Synonym(s)":      ", ".join(syns) or "-",
                    "UniProt ID":      iso.get("isoformIds", ["?"])[0],
                    "Sequence Status": iso.get("isoformSequenceStatus", "?"),
                })
            st.dataframe(pd.DataFrame(iso_rows), use_container_width=True, hide_index=True)
        else:
            st.info("Isoform data not available — check data/raw/apis/uniprot_cd46.json")

        st.markdown("#### Disease Associations (Open Targets — top 25)")
        if ot_rows:
            top25 = sorted(ot_rows, key=lambda r: r.get("score", 0), reverse=True)[:25]
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
            ot_names  = [r["disease"]["name"] for r in top25]
            ot_scores = [round(r.get("score", 0), 4) for r in top25]
            ot_areas  = [
                r["disease"].get("therapeuticAreas", [{}])[0].get("name", "other")
                for r in top25
            ]
            ot_fig = go.Figure(go.Bar(
                x=ot_scores, y=ot_names, orientation="h",
                marker_color=[AREA_COLORS.get(a.lower(), "#64748b") for a in ot_areas],
                hovertemplate="<b>%{y}</b><br>Score: %{x:.4f}<extra></extra>",
            ))
            ot_fig.update_layout(
                height=max(380, len(top25) * 18),
                margin=dict(l=0, r=0, t=10, b=0),
                paper_bgcolor="#0f172a", plot_bgcolor="#0f172a",
                xaxis=dict(title="Overall Association Score", color=_TEXT, gridcolor=_LINE, range=[0, 1]),
                yaxis=dict(color=_LIGHT, tickfont=dict(size=10), autorange="reversed"),
            )
            st.plotly_chart(ot_fig, use_container_width=True)
            st.caption(
                "Open Targets Platform: 772 total associations. "
                "Colors: red=hematologic, orange=genetic, yellow=immune, "
                "green=cancer, purple=infectious, cyan=nervous system. Score 0-1."
            )
        else:
            st.info("Open Targets data not available — check data/raw/apis/open_targets_cd46.json")

        st.markdown("#### AlphaFold Structural Confidence (pLDDT)")
        with st.spinner("Loading AlphaFold pLDDT..."):
            af    = _fetch_alphafold()
        plddt = af.get("plddt") if af else None

        if isinstance(plddt, list) and len(plddt) > 0:
            import numpy as _np
            mean_conf = float(_np.mean(plddt))
            lc1, lc2, lc3 = st.columns(3)
            lc1.metric("Mean pLDDT",    f"{mean_conf:.1f} / 100")
            lc2.metric("Very High >90", f"{sum(1 for v in plddt if v > 90)} residues")
            lc3.metric("Low <70",       f"{sum(1 for v in plddt if v < 70)} residues")
            plddt_fig = go.Figure(go.Bar(
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
                xaxis=dict(title="Residue index", color=_TEXT, showgrid=False),
                yaxis=dict(title="pLDDT", color=_TEXT, range=[0, 100], gridcolor=_LINE),
            )
            st.plotly_chart(plddt_fig, use_container_width=True)
            st.caption("Blue >90 (very high) | Green 70-90 (high) | Yellow 50-70 (low) | Red <50 (very low)")
        else:
            st.info("pLDDT data unavailable (AlphaFold EBI API timeout). SCR domains 1-4 typically score >85.")

        st.markdown("#### Interactive 3D Structure (AlphaFold DB)")
        st.markdown(
            "<iframe src='https://alphafold.ebi.ac.uk/entry/P15529' "
            "width='100%' height='620px' "
            "style='border:1px solid #334155;border-radius:8px;'></iframe>",
            unsafe_allow_html=True,
        )
        st.link_button("Open Full AlphaFold Entry", "https://alphafold.ebi.ac.uk/entry/P15529")

    # ------------------------------------------------------------------
    with str_sub:
        st.markdown(
            "<div style='background:#1e293b;border-left:3px solid #818cf8;"
            "padding:12px 16px;border-radius:6px;margin-bottom:14px;'>"
            "<b style='color:#818cf8;'>CD46 Protein Interaction Network — STRING DB</b><br>"
            "<span style='color:#94a3b8;'>Homo sapiens (taxid: 9606) · "
            "Combined score > 400 · Physical + functional interactions</span>"
            "</div>",
            unsafe_allow_html=True,
        )

        with st.spinner("Loading STRING interaction data..."):
            string_data = _fetch_string()

        COMPLEMENT_GENES = {
            "CD55", "CD59", "CR2", "C3", "C4A", "C4B", "C1QA", "CFH", "MCP", "CR1"
        }

        if string_data:
            st.success(f"{len(string_data)} interaction partners loaded (STRING DB)")
            df_str = pd.DataFrame(string_data)
            if not df_str.empty:
                disp_cols = ["preferredName_B", "score", "nscore", "escore", "fscore", "tscore"]
                avail     = [c for c in disp_cols if c in df_str.columns]
                df_show   = df_str[avail].copy()
                df_show.columns = [
                    c.replace("preferredName_B", "Partner")
                     .replace("score", "Combined")
                     .replace("nscore", "Neighborhood")
                     .replace("escore", "Experiment")
                     .replace("fscore", "Co-occurrence")
                     .replace("tscore", "Text-mining")
                    for c in avail
                ]
                df_show["Complement?"] = df_show["Partner"].apply(
                    lambda x: "YES" if x in COMPLEMENT_GENES else ""
                )
                st.dataframe(
                    df_show.sort_values("Combined", ascending=False).head(25),
                    use_container_width=True, hide_index=True,
                )

                interactions  = string_data[:20]
                pnames        = [r.get("preferredName_B", "") for r in interactions]
                pscores       = [r.get("score", 0) / 1000 for r in interactions]
                n             = len(pnames)
                angles        = [2 * math.pi * i / n for i in range(n)]
                cx            = [math.cos(a) for a in angles]
                cy            = [math.sin(a) for a in angles]
                edge_x, edge_y = [], []
                for i in range(n):
                    edge_x += [0, cx[i], None]
                    edge_y += [0, cy[i], None]

                fig_str = go.Figure()
                fig_str.add_trace(go.Scatter(
                    x=edge_x, y=edge_y, mode="lines",
                    line=dict(width=0.8, color="#334155"), hoverinfo="none", showlegend=False,
                ))
                fig_str.add_trace(go.Scatter(
                    x=[0] + cx, y=[0] + cy, mode="markers+text",
                    marker=dict(
                        size=[28] + [12 + int(s * 10) for s in pscores],
                        color=["#38bdf8"] + [
                            "#f87171" if p in COMPLEMENT_GENES else "#818cf8"
                            for p in pnames
                        ],
                        line=dict(width=1, color="#0f172a"),
                    ),
                    text=["CD46"] + pnames,
                    textposition="top center",
                    textfont=dict(size=9, color="#e2e8f0"),
                    hovertext=[
                        "CD46 hub node" if i == 0
                        else f"{pnames[i-1]}<br>Score: {pscores[i-1]:.3f}"
                        for i in range(n + 1)
                    ],
                    hoverinfo="text", showlegend=False,
                ))
                fig_str.update_layout(
                    height=440, paper_bgcolor="#0f172a", plot_bgcolor="#0f172a",
                    margin=dict(l=10, r=10, t=30, b=10),
                    xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                    yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                    title=dict(
                        text="CD46 Protein Interaction Network (STRING)",
                        font=dict(color="#e2e8f0", size=13),
                    ),
                )
                st.plotly_chart(fig_str, use_container_width=True)
                st.caption("Red = Complement pathway partners | Cyan = CD46 hub | Purple = Other interactions")
        else:
            st.info(
                "STRING data unavailable (API timeout). "
                "Known key interactions: CD55, CD59, C3b/C4b cofactors, CR1."
            )

        st.info(
            "CD46 physically interacts with complement proteins C3b and C4b, "
            "cofactoring with Factor I for their cleavage — the core complement regulatory mechanism. "
            "CD46 also serves as the measles virus H protein receptor (therapeutic vulnerability). "
            "STRING combined score > 0.7 = high-confidence interaction."
        )
        st.link_button(
            "Open CD46 in STRING", "https://string-db.org/network/9606.ENSP00000317276"
        )

    # ------------------------------------------------------------------
    with pub_sub:
        st.markdown(
            "<div style='background:#1e293b;border-left:3px solid #4ade80;"
            "padding:12px 16px;border-radius:6px;margin-bottom:14px;'>"
            "<b style='color:#4ade80;'>Curated CD46 Evidence Base</b><br>"
            "<span style='color:#94a3b8;'>Peer-reviewed publications from AuraDB "
            "knowledge graph — foundational papers for 225Ac-CD46 program</span>"
            "</div>",
            unsafe_allow_html=True,
        )

        pub_records = []
        if driver is not None:
            try:
                with driver.session() as sess:
                    pub_records = [
                        dict(rec["pub"])
                        for rec in sess.run(
                            "MATCH (pub:Publication) RETURN pub ORDER BY pub.year DESC"
                        )
                    ]
            except Exception as e:
                st.warning(f"Could not load publications from KG: {e}")

        if not pub_records:
            st.info(
                "No publications in knowledge graph yet — "
                "run scripts/load_kg_extras.py to populate."
            )
        else:
            ev_types  = sorted({p.get("evidence_type", "Other") for p in pub_records})
            sel_types = st.multiselect("Filter by evidence type", ev_types, default=ev_types)
            filtered  = [p for p in pub_records if p.get("evidence_type", "Other") in sel_types]

            EV_COLORS = {
                "Experimental":           "#f87171",
                "Clinical trial":         "#fb923c",
                "Clinical-translational": "#fbbf24",
                "Biomarker":              "#4ade80",
                "Preclinical":            "#818cf8",
                "Bioinformatics":         "#38bdf8",
                "Review":                 "#94a3b8",
            }

            for pub in filtered:
                pmid     = pub.get("pubmed_id", "")
                url      = f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/" if pmid else "#"
                ev_color = EV_COLORS.get(pub.get("evidence_type", ""), "#64748b")
                authors  = pub.get("authors", "")
                auth_str = ", ".join(authors) if isinstance(authors, list) else authors
                st.markdown(
                    f"<div style='background:#1e293b;border:1px solid #334155;"
                    f"border-left:4px solid {ev_color};"
                    f"padding:14px 16px;margin:8px 0;border-radius:6px;'>"
                    f"<span style='background:{ev_color}22;color:{ev_color};"
                    f"font-size:0.75em;padding:2px 8px;border-radius:12px;font-weight:600;'>"
                    f"{pub.get('evidence_type','').upper()}</span>"
                    f"<b style='color:#e2e8f0;display:block;margin-top:8px;'>"
                    f"{pub.get('title','')}</b>"
                    f"<span style='color:#94a3b8;font-size:0.84em;'>{auth_str}</span><br>"
                    f"<span style='color:#64748b;font-size:0.82em;'>"
                    f"{pub.get('journal','')} &middot; {pub.get('year','')}</span><br>"
                    f"<span style='color:#38bdf8;font-size:0.84em;"
                    f"margin-top:6px;display:block;'>"
                    f"-> {pub.get('key_finding','')}</span>"
                    f"</div>",
                    unsafe_allow_html=True,
                )
                if pmid and pmid != "#":
                    st.link_button(f"PubMed {pmid}", url)

st.markdown("---")
st.caption(
    "Knowledge graph: Neo4j AuraDB. "
    "Node types: Gene, Protein, Disease, Drug, PatientGroup, CellLine, "
    "Pathway, Tissue, Publication, ClinicalTrial. "
    "AlphaFold: EBI structure prediction (pLDDT). "
    "STRING: protein-protein interaction network (Homo sapiens, taxid 9606)."
)
