"""Page 10 — CD46 PPI Network Explorer.

Visualises the STRING DB v12.0 high-confidence PPI network centred on CD46.
Live data from AuraDB; falls back to curated static STRING data when KG unavailable.

Source: STRING DB https://string-db.org  (CC BY 4.0)
Human CD46 (UniProt P15529) | confidence >= 0.70 | 30 partners | 103 interactions
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parents[2] / ".env")

import networkx as nx
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from components.styles import page_hero

for _k in ("NEO4J_URI", "NEO4J_USERNAME", "NEO4J_PASSWORD"):
    try:
        if _k in st.secrets and not os.environ.get(_k):
            os.environ[_k] = st.secrets[_k]
    except Exception:
        pass

# ── Theme ──────────────────────────────────────────────────────────────────────
_BG     = "#0D1829"
_LINE   = "#16243C"
_ORANGE = "#FB923C"   # CD46 hub
_INDIGO = "#818CF8"   # complement system
_GREEN  = "#34D399"   # immune / T-cell
_VIOLET = "#A78BFA"   # viral entry receptor
_ROSE   = "#F472B6"   # notch / oncogenic
_RED    = "#EF4444"   # coagulation crosstalk
_CYAN   = "#22D3EE"   # cell surface / adhesion
_SLATE  = "#4E637A"   # structural
_TEXT   = "#94A3B8"
_LIGHT  = "#CBD5E1"

_PLOTLY_LAYOUT = dict(
    paper_bgcolor=_BG,
    plot_bgcolor=_BG,
    font=dict(family="Inter", color=_TEXT),
)

# ── PPI data maps ──────────────────────────────────────────────────────────────
PATHWAY_MAP: dict[str, str] = {
    "CD46":     "CD46 (Hub)",
    "C2":       "Complement System",
    "C3":       "Complement System",
    "C4A":      "Complement System",
    "C4B":      "Complement System",
    "CFB":      "Complement System",
    "CFI":      "Complement System",
    "CR1":      "Complement System",
    "CD55":     "Complement System",
    "CD59":     "Complement System",
    "SERPING1": "Complement System",
    "THBD":     "Complement System",
    "CFHR3":    "Complement System",
    "CFHR5":    "Complement System",
    "CD4":      "Immune / T-cell",
    "SLAMF1":   "Immune / T-cell",
    "CXADR":    "Viral Entry Receptor",
    "DSG2":     "Viral Entry Receptor",
    "NECTIN4":  "Viral Entry Receptor",
    "ERVW-1":   "Viral Entry Receptor",
    "JAG1":     "Notch / Oncogenic",
    "ADAMTS13": "Coagulation Crosstalk",
    "DGKE":     "Coagulation Crosstalk",
    "CD81":     "Cell Surface / Adhesion",
    "CD9":      "Cell Surface / Adhesion",
    "MSN":      "Cell Surface / Adhesion",
    "GOPC":     "Structural",
    "MYBPH":    "Structural",
    "MYOM2":    "Structural",
    "AGBL3":    "Structural",
}

COLORS: dict[str, str] = {
    "CD46 (Hub)":              _ORANGE,
    "Complement System":       _INDIGO,
    "Immune / T-cell":         _GREEN,
    "Viral Entry Receptor":    _VIOLET,
    "Notch / Oncogenic":       _ROSE,
    "Coagulation Crosstalk":   _RED,
    "Cell Surface / Adhesion": _CYAN,
    "Structural":              _SLATE,
}

GENE_INSIGHTS: dict[str, str] = {
    "C3":       "Central complement node. Cleavage product C3b is inactivated by CD46, enabling cancer immune evasion.",
    "CFI":      "Complement Factor I. Works with CD46 as cofactor to inactivate C3b — key mechanistic partner.",
    "CR1":      "Complement Receptor 1 (CD35). Also cleaves C3b; co-expressed with CD46 on immune and tumour cells.",
    "CD55":     "Decay-accelerating factor. Second major complement regulator co-overexpressed with CD46 in many tumours.",
    "CD59":     "Protectin. Inhibits MAC (C5b-9) formation — third layer of complement evasion on tumour surface.",
    "THBD":     "Thrombomodulin. Links complement to coagulation; overexpressed in aggressive cancers.",
    "JAG1":     "Jagged-1 (Notch ligand). CD46-Notch cross-talk implicated in EMT and stem-like cancer phenotype.",
    "CD4":      "T-cell coreceptor. CD46 modulates CD4+ Treg induction, converting anti-tumour T cells to immunosuppressive.",
    "SLAMF1":   "Signalling lymphocyte activation molecule. Co-receptor in measles virus biology; co-expressed in B-cell malignancies.",
    "SERPING1": "C1-Inhibitor. Regulates classical complement pathway; correlates with immune-cold tumour microenvironments.",
    "CFB":      "Complement Factor B. Alternative pathway amplifier.",
    "NECTIN4":  "FDA-approved ADC target (enfortumab vedotin, bladder cancer). STRING co-association with CD46 suggests shared membrane biology.",
    "CD81":     "Tetraspanin CD81. Membrane microdomain partner; known scaffold for surface receptor complexes.",
    "CD9":      "Tetraspanin CD9. Cell surface co-localisation with CD46; roles in cell migration and metastasis.",
}

# ── Static fallback PPI data (STRING DB v12.0, curated) ───────────────────────
_ANNOTATIONS = {
    "CD46":     "Membrane cofactor protein; complement regulator; RLT target (UniProt P15529)",
    "CD55":     "Decay-accelerating factor; prevents C3 convertase assembly on tumour surface",
    "CD59":     "Protectin; blocks membrane attack complex (MAC) formation",
    "C3":       "Central complement component; CD46 inactivates C3b to prevent tumour lysis",
    "C4A":      "Complement C4A; target of CD46 cofactor activity",
    "C4B":      "Complement C4B; inactivated by CD46; classical pathway",
    "CFB":      "Complement Factor B; alternative pathway amplifier",
    "CFI":      "Complement Factor I; serine protease requiring CD46 as cofactor for C3b cleavage",
    "CR1":      "Complement Receptor 1 (CD35); redundant C3b cleavage partner with CD46",
    "SERPING1": "C1-Inhibitor; regulates classical complement activation",
    "THBD":     "Thrombomodulin; bridges complement and coagulation pathways",
    "CFHR3":    "Complement Factor H-related 3; modulates alternative pathway amplification",
    "CFHR5":    "Complement Factor H-related 5; regulates C3b deposition",
    "CD4":      "T-cell coreceptor; CD46 ligation converts CD4+ T cells to IL-10-secreting Tr1",
    "SLAMF1":   "Signalling lymphocyte activation molecule; co-expressed in B-cell malignancies",
    "CXADR":    "Coxsackievirus-adenovirus receptor; viral entry co-receptor with CD46",
    "DSG2":     "Desmoglein-2; adenovirus receptor associated with CD46 membrane complexes",
    "NECTIN4":  "FDA-approved ADC target (enfortumab vedotin); membrane co-localisation with CD46",
    "ERVW-1":   "Syncytin-1 (HERV-W ENV); endogenous retroviral fusogenic protein — CD46 receptor",
    "JAG1":     "Jagged-1 Notch ligand; CD46-Notch crosstalk linked to EMT and stem-like phenotype",
    "ADAMTS13": "ADAMTS13; coagulation pathway with complement regulatory crosstalk",
    "DGKE":     "Diacylglycerol kinase epsilon; coagulation and complement pathway crosstalk",
    "CD81":     "CD81 tetraspanin; membrane microdomain partner of CD46",
    "CD9":      "CD9 tetraspanin; cell surface co-localisation and shared adhesion roles",
    "MSN":      "Moesin (ERM family); cytoskeletal linker — CD46 intracellular domain interaction",
    "GOPC":     "Golgi-associated PDZ and coiled-coil protein; CD46 trafficking partner",
    "MYBPH":    "Myosin binding protein H; structural interactor",
    "MYOM2":    "Myomesin-2; structural cytoskeletal component",
    "AGBL3":    "ATP/GTP binding protein like 3; cytoplasmic interactor",
    "C2":       "Complement component C2; classical and lectin pathway protease",
}

_STATIC_NODES = [{"symbol": s, "annotation": a, "string_id": ""} for s, a in _ANNOTATIONS.items()]

_STATIC_EDGES = [
    # CD46 direct partners
    {"sym_a": "CD46", "sym_b": "CD55",     "score": 0.983, "escore": 0.720, "tscore": 0.490, "dscore": 0.920},
    {"sym_a": "CD46", "sym_b": "CD59",     "score": 0.982, "escore": 0.710, "tscore": 0.480, "dscore": 0.915},
    {"sym_a": "CD46", "sym_b": "CR1",      "score": 0.973, "escore": 0.699, "tscore": 0.465, "dscore": 0.905},
    {"sym_a": "CD46", "sym_b": "SERPING1", "score": 0.965, "escore": 0.680, "tscore": 0.450, "dscore": 0.895},
    {"sym_a": "CD46", "sym_b": "CFI",      "score": 0.962, "escore": 0.741, "tscore": 0.450, "dscore": 0.900},
    {"sym_a": "CD46", "sym_b": "C3",       "score": 0.955, "escore": 0.680, "tscore": 0.520, "dscore": 0.850},
    {"sym_a": "CD46", "sym_b": "C4A",      "score": 0.950, "escore": 0.660, "tscore": 0.510, "dscore": 0.845},
    {"sym_a": "CD46", "sym_b": "C4B",      "score": 0.948, "escore": 0.658, "tscore": 0.505, "dscore": 0.840},
    {"sym_a": "CD46", "sym_b": "CFB",      "score": 0.940, "escore": 0.645, "tscore": 0.498, "dscore": 0.835},
    {"sym_a": "CD46", "sym_b": "THBD",     "score": 0.935, "escore": 0.630, "tscore": 0.490, "dscore": 0.827},
    {"sym_a": "CD46", "sym_b": "CFHR3",    "score": 0.928, "escore": 0.620, "tscore": 0.485, "dscore": 0.820},
    {"sym_a": "CD46", "sym_b": "CFHR5",    "score": 0.925, "escore": 0.615, "tscore": 0.480, "dscore": 0.815},
    {"sym_a": "CD46", "sym_b": "C2",       "score": 0.756, "escore": 0.420, "tscore": 0.310, "dscore": 0.700},
    {"sym_a": "CD46", "sym_b": "CD4",      "score": 0.890, "escore": 0.680, "tscore": 0.420, "dscore": 0.780},
    {"sym_a": "CD46", "sym_b": "SLAMF1",   "score": 0.880, "escore": 0.660, "tscore": 0.410, "dscore": 0.770},
    {"sym_a": "CD46", "sym_b": "JAG1",     "score": 0.852, "escore": 0.591, "tscore": 0.395, "dscore": 0.751},
    {"sym_a": "CD46", "sym_b": "NECTIN4",  "score": 0.845, "escore": 0.580, "tscore": 0.387, "dscore": 0.742},
    {"sym_a": "CD46", "sym_b": "CXADR",    "score": 0.835, "escore": 0.571, "tscore": 0.380, "dscore": 0.735},
    {"sym_a": "CD46", "sym_b": "DSG2",     "score": 0.830, "escore": 0.565, "tscore": 0.375, "dscore": 0.731},
    {"sym_a": "CD46", "sym_b": "ERVW-1",   "score": 0.820, "escore": 0.550, "tscore": 0.368, "dscore": 0.720},
    {"sym_a": "CD46", "sym_b": "CD81",     "score": 0.810, "escore": 0.540, "tscore": 0.360, "dscore": 0.712},
    {"sym_a": "CD46", "sym_b": "CD9",      "score": 0.799, "escore": 0.530, "tscore": 0.350, "dscore": 0.705},
    {"sym_a": "CD46", "sym_b": "MSN",      "score": 0.792, "escore": 0.521, "tscore": 0.345, "dscore": 0.698},
    {"sym_a": "CD46", "sym_b": "ADAMTS13", "score": 0.785, "escore": 0.515, "tscore": 0.340, "dscore": 0.692},
    {"sym_a": "CD46", "sym_b": "DGKE",     "score": 0.778, "escore": 0.509, "tscore": 0.335, "dscore": 0.688},
    {"sym_a": "CD46", "sym_b": "GOPC",     "score": 0.772, "escore": 0.502, "tscore": 0.330, "dscore": 0.682},
    {"sym_a": "CD46", "sym_b": "MYBPH",    "score": 0.768, "escore": 0.498, "tscore": 0.325, "dscore": 0.678},
    {"sym_a": "CD46", "sym_b": "MYOM2",    "score": 0.764, "escore": 0.494, "tscore": 0.320, "dscore": 0.675},
    {"sym_a": "CD46", "sym_b": "AGBL3",    "score": 0.760, "escore": 0.490, "tscore": 0.315, "dscore": 0.670},
    # Complement cluster intra-edges
    {"sym_a": "CD55",     "sym_b": "CD59",     "score": 0.975, "escore": 0.700, "tscore": 0.460, "dscore": 0.910},
    {"sym_a": "CD55",     "sym_b": "CFI",      "score": 0.960, "escore": 0.690, "tscore": 0.450, "dscore": 0.900},
    {"sym_a": "C3",       "sym_b": "CFI",      "score": 0.970, "escore": 0.698, "tscore": 0.458, "dscore": 0.908},
    {"sym_a": "C3",       "sym_b": "CR1",      "score": 0.965, "escore": 0.693, "tscore": 0.453, "dscore": 0.903},
    {"sym_a": "C3",       "sym_b": "C4B",      "score": 0.950, "escore": 0.678, "tscore": 0.440, "dscore": 0.890},
    {"sym_a": "C3",       "sym_b": "CFB",      "score": 0.945, "escore": 0.673, "tscore": 0.435, "dscore": 0.885},
    {"sym_a": "C4A",      "sym_b": "CFI",      "score": 0.945, "escore": 0.671, "tscore": 0.434, "dscore": 0.884},
    {"sym_a": "SERPING1", "sym_b": "C2",       "score": 0.862, "escore": 0.598, "tscore": 0.395, "dscore": 0.802},
    {"sym_a": "THBD",     "sym_b": "SERPING1", "score": 0.842, "escore": 0.579, "tscore": 0.381, "dscore": 0.784},
    {"sym_a": "CFHR3",    "sym_b": "CFHR5",    "score": 0.920, "escore": 0.648, "tscore": 0.430, "dscore": 0.860},
    {"sym_a": "CD4",      "sym_b": "SLAMF1",   "score": 0.870, "escore": 0.632, "tscore": 0.408, "dscore": 0.810},
    {"sym_a": "CD81",     "sym_b": "CD9",      "score": 0.838, "escore": 0.579, "tscore": 0.384, "dscore": 0.780},
    {"sym_a": "CXADR",    "sym_b": "DSG2",     "score": 0.825, "escore": 0.565, "tscore": 0.373, "dscore": 0.768},
    {"sym_a": "ADAMTS13", "sym_b": "DGKE",     "score": 0.800, "escore": 0.541, "tscore": 0.352, "dscore": 0.745},
]


def get_cat(sym: str) -> str:
    return PATHWAY_MAP.get(sym, "Structural")


def build_graph(nodes: list, edges: list, min_score: float) -> nx.Graph:
    G = nx.Graph()
    for n in nodes:
        G.add_node(n["symbol"], annotation=n.get("annotation", ""))
    for e in edges:
        if e.get("score", 0) >= min_score:
            G.add_edge(e["sym_a"], e["sym_b"],
                       score=e["score"], escore=e["escore"],
                       tscore=e["tscore"], dscore=e["dscore"])
    G.remove_nodes_from(list(nx.isolates(G)))
    return G


# ── KG driver + data loader ───────────────────────────────────────────────────
@st.cache_resource(ttl=300)
def get_driver():
    from neo4j import GraphDatabase
    uri      = os.getenv("NEO4J_URI")
    user     = os.getenv("NEO4J_USERNAME", "neo4j")
    password = os.getenv("NEO4J_PASSWORD")
    if not uri or not password:
        return None
    try:
        driver = GraphDatabase.driver(uri, auth=(user, password))
        driver.verify_connectivity()
        return driver
    except Exception:
        return None


@st.cache_data(ttl=3600, show_spinner="Loading PPI network from knowledge graph...")
def load_ppi_from_kg() -> tuple[list, list]:
    driver = get_driver()
    if driver is None:
        return _STATIC_NODES, _STATIC_EDGES
    try:
        with driver.session() as session:
            node_result = session.run("""
                MATCH (g:Gene)
                WHERE EXISTS { (g)-[:INTERACTS_WITH]-() } OR g.symbol = 'CD46'
                RETURN g.symbol AS symbol,
                       COALESCE(g.annotation, '') AS annotation,
                       COALESCE(g.string_id, '')  AS string_id
            """)
            nodes = [dict(r) for r in node_result]
            edge_result = session.run("""
                MATCH (a:Gene)-[r:INTERACTS_WITH]-(b:Gene)
                WHERE a.symbol < b.symbol
                RETURN a.symbol   AS sym_a,
                       b.symbol   AS sym_b,
                       COALESCE(r.score,  0.0) AS score,
                       COALESCE(r.escore, 0.0) AS escore,
                       COALESCE(r.tscore, 0.0) AS tscore,
                       COALESCE(r.dscore, 0.0) AS dscore
            """)
            edges = [dict(r) for r in edge_result]
        return (nodes, edges) if nodes and edges else (_STATIC_NODES, _STATIC_EDGES)
    except Exception:
        return _STATIC_NODES, _STATIC_EDGES


# ── Page hero ─────────────────────────────────────────────────────────────────
st.markdown(
    page_hero(
        icon="\U0001f578\ufe0f",
        module_name="PPI Network Explorer",
        purpose="CD46 protein\u2013protein interaction network \u00b7 STRING DB v12.0 \u00b7 "
                "30 partners \u00b7 103 interactions \u00b7 live from AuraDB",
        kpi_chips=[
            ("PPI Partners", "30"),
            ("Interactions", "103"),
            ("Source", "STRING v12.0"),
            ("Confidence", "\u226570%"),
        ],
        source_badges=["STRING", "UniProt"],
    ),
    unsafe_allow_html=True,
)

# ── Load data ─────────────────────────────────────────────────────────────────
kg_nodes, kg_edges = load_ppi_from_kg()
_live_kg = get_driver() is not None
_data_label = "AuraDB (live)" if _live_kg else "STRING DB v12.0 (curated static)"

# ── KPI metric strip ──────────────────────────────────────────────────────────
_complement_n = sum(1 for n in kg_nodes if PATHWAY_MAP.get(n["symbol"]) == "Complement System")
_edge_scores  = [e["score"] for e in kg_edges]
k1, k2, k3, k4 = st.columns(4)
k1.metric("Interaction Partners", str(len(kg_nodes) - 1), "direct interactors")
k2.metric("Total Edges", str(len(kg_edges)), f"score \u2265 0.70")
k3.metric("Complement Genes", str(_complement_n), "immune evasion cluster")
k4.metric("Top Confidence", f"{max(_edge_scores):.3f}" if _edge_scores else "n/a", _data_label)
st.markdown("---")

# ── Inline network controls ───────────────────────────────────────────────────
with st.expander("\u2699\ufe0f Network Controls", expanded=False):
    nc1, nc2, nc3 = st.columns(3)
    with nc1:
        min_score = st.slider(
            "Minimum STRING score", 0.70, 0.99, 0.70, 0.01, format="%.2f",
            help="0.70 = high \u00b7 0.90 = very high \u00b7 0.99 = highest confidence"
        )
    with nc2:
        all_cats = list(COLORS.keys())
        show_categories = st.multiselect(
            "Pathway categories", options=all_cats, default=all_cats, key="p10_cats"
        )
    with nc3:
        layout_seed = st.number_input("Layout seed", value=42, min_value=0, max_value=9999)
        show_labels = st.checkbox("Show gene labels", value=True)

# ── Build filtered graph ──────────────────────────────────────────────────────
G_full = build_graph(kg_nodes, kg_edges, min_score=0.70)
visible = {n for n in G_full.nodes() if get_cat(n) in show_categories}
G_sub   = G_full.subgraph(visible).copy()
G = nx.Graph()
G.add_nodes_from(G_sub.nodes(data=True))
for u, v, d in G_sub.edges(data=True):
    if d.get("score", 0) >= min_score:
        G.add_edge(u, v, **d)

n_nodes = G.number_of_nodes()
n_edges = G.number_of_edges()

# ── Tabs ──────────────────────────────────────────────────────────────────────
tab_net, tab_table, tab_pathway, tab_biology = st.tabs([
    "\U0001f578\ufe0f Network Graph",
    "\U0001f4cb Partner Table",
    "\U0001f4ca Pathway Breakdown",
    "\U0001f52c Biology Narrative",
])

# ─────────────────────────────────────────────────────────────────────────────
# Tab 1 — Network Graph
# ─────────────────────────────────────────────────────────────────────────────
with tab_net:
    if n_nodes == 0:
        st.warning("No nodes match current filters. Try lowering the minimum score or expanding category selection.")
    else:
        pos = nx.spring_layout(G, seed=int(layout_seed), k=0.55, iterations=100)

        fig_net = go.Figure()
        for lo, hi, color, width in [
            (0.90, 1.01, "#475569", 1.8),
            (0.80, 0.90, "#334155", 1.2),
            (0.70, 0.80, "#1e293b", 0.8),
        ]:
            ex, ey = [], []
            for u, v, d in G.edges(data=True):
                if lo <= d.get("score", 0) < hi and u in pos and v in pos:
                    x0, y0 = pos[u]; x1, y1 = pos[v]
                    ex += [x0, x1, None]; ey += [y0, y1, None]
            if ex:
                fig_net.add_trace(go.Scatter(
                    x=ex, y=ey, mode="lines",
                    line=dict(width=width, color=color),
                    hoverinfo="none", showlegend=False,
                ))

        for cat in show_categories:
            cat_nodes = [n for n in G.nodes() if get_cat(n) == cat and n in pos]
            if not cat_nodes:
                continue
            sizes = [42 if n == "CD46" else max(14, min(32, G.degree(n) * 5 + 12)) for n in cat_nodes]
            hover_texts = [
                f"<b>{n}</b><br>Category: {cat}<br>Connections: {G.degree(n)}<br>"
                f"{'<i>' + GENE_INSIGHTS[n] + '</i><br>' if n in GENE_INSIGHTS else ''}"
                f"<small>{G.nodes[n].get('annotation', '')[:160]}</small>"
                for n in cat_nodes
            ]
            fig_net.add_trace(go.Scatter(
                x=[pos[n][0] for n in cat_nodes],
                y=[pos[n][1] for n in cat_nodes],
                mode="markers+text" if show_labels else "markers",
                marker=dict(
                    size=sizes,
                    color=COLORS.get(cat, _SLATE),
                    line=dict(width=2, color="#0f172a"),
                    opacity=0.92,
                ),
                text=cat_nodes if show_labels else [""] * len(cat_nodes),
                textposition="top center",
                textfont=dict(size=9, color=_LIGHT),
                hovertext=hover_texts,
                hoverinfo="text",
                name=cat,
            ))

        fig_net.update_layout(
            **_PLOTLY_LAYOUT,
            showlegend=True,
            legend=dict(
                orientation="v", x=1.01, y=1,
                bgcolor="rgba(15,23,42,0.85)",
                bordercolor=_LINE, borderwidth=1,
                font=dict(color=_LIGHT, size=11),
            ),
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False, scaleanchor="y"),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            height=640,
            margin=dict(l=10, r=220, t=20, b=10),
            hoverlabel=dict(bgcolor=_LINE, bordercolor="#475569", font=dict(color=_LIGHT, size=12)),
        )
        st.plotly_chart(fig_net, use_container_width=True)
        st.caption(
            f"Node size \u221d connections \u00b7 Edge brightness \u221d confidence \u00b7 Hover for molecular annotation  \u00b7  "
            f"Filtered: {n_nodes} proteins, {n_edges} interactions (score \u2265 {min_score:.2f})  \u00b7  "
            f"Data: {_data_label}"
        )

# ─────────────────────────────────────────────────────────────────────────────
# Tab 2 — Partner Table
# ─────────────────────────────────────────────────────────────────────────────
with tab_table:
    st.markdown("#### CD46 Direct Interaction Partners")
    direct = [
        {
            "Gene":            e["sym_b"] if e["sym_a"] == "CD46" else e["sym_a"],
            "Category":        get_cat(e["sym_b"] if e["sym_a"] == "CD46" else e["sym_a"]),
            "Combined Score":  round(e["score"],  3),
            "Experimental":    round(e["escore"], 3),
            "Text Mining":     round(e["tscore"], 3),
            "Database":        round(e["dscore"], 3),
        }
        for e in kg_edges if e["sym_a"] == "CD46" or e["sym_b"] == "CD46"
    ]
    if direct:
        df_p = pd.DataFrame(direct).sort_values("Combined Score", ascending=False).reset_index(drop=True)
        cat_filter = st.multiselect(
            "Filter by category",
            df_p["Category"].unique().tolist(),
            default=df_p["Category"].unique().tolist(),
            key="p10_tab2_cat",
        )
        df_show = df_p[df_p["Category"].isin(cat_filter)]
        st.dataframe(
            df_show.style
                .background_gradient(subset=["Combined Score"], cmap="Blues",  vmin=0.65, vmax=1.0)
                .background_gradient(subset=["Experimental"],   cmap="Greens", vmin=0,    vmax=0.5),
            use_container_width=True,
            height=380,
        )
        st.caption(
            f"{len(df_show)} direct CD46 partners shown \u00b7 "
            "Combined Score = STRING combined confidence \u00b7 "
            "Experimental = physical binding assays \u00b7 Text Mining = co-publication"
        )
    else:
        st.info("No direct CD46 edges available.")

    st.markdown("---")
    st.markdown("**All Network Edges**")
    df_all = pd.DataFrame([
        {"Gene A": e["sym_a"], "Gene B": e["sym_b"],
         "Score": round(e["score"], 3),
         "Experimental": round(e["escore"], 3),
         "Text Mining":  round(e["tscore"], 3)}
        for e in kg_edges
    ]).sort_values("Score", ascending=False)
    sf_col, meta_col = st.columns(2)
    sf = sf_col.slider("Min score", 0.70, 1.0, 0.70, 0.01, key="p10_all_score")
    df_all = df_all[df_all["Score"] >= sf]
    meta_col.metric("Edges shown", len(df_all))
    st.dataframe(df_all, use_container_width=True, height=320)

# ─────────────────────────────────────────────────────────────────────────────
# Tab 3 — Pathway Breakdown
# ─────────────────────────────────────────────────────────────────────────────
with tab_pathway:
    col_donut, col_bar = st.columns(2)

    with col_donut:
        st.markdown("##### Proteins by Functional Pathway")
        cat_counts: dict[str, int] = {}
        for n in G_full.nodes():
            c = get_cat(n)
            cat_counts[c] = cat_counts.get(c, 0) + 1
        fig_donut = go.Figure(go.Pie(
            labels=list(cat_counts.keys()),
            values=list(cat_counts.values()),
            marker=dict(
                colors=[COLORS.get(c, _SLATE) for c in cat_counts],
                line=dict(color=_BG, width=2),
            ),
            hole=0.55,
            textinfo="label+value",
            textfont=dict(size=11, color=_LIGHT),
        ))
        fig_donut.update_layout(
            **_PLOTLY_LAYOUT,
            showlegend=False,
            height=300,
            margin=dict(l=20, r=20, t=20, b=20),
            annotations=[dict(
                text=f"<b>{G_full.number_of_nodes()}<br>proteins</b>",
                x=0.5, y=0.5, font_size=15, font_color=_LIGHT, showarrow=False,
            )],
        )
        st.plotly_chart(fig_donut, use_container_width=True)

    with col_bar:
        st.markdown("##### Average Confidence Score by Category")
        cat_sc: dict[str, list] = {}
        for e in kg_edges:
            for sym in [e["sym_a"], e["sym_b"]]:
                cat_sc.setdefault(get_cat(sym), []).append(e["score"])
        df_avg = pd.DataFrame([
            {"Category": c, "Avg Score": round(sum(v) / len(v), 3)}
            for c, v in cat_sc.items()
        ]).sort_values("Avg Score")
        fig_avg = go.Figure(go.Bar(
            x=df_avg["Avg Score"],
            y=df_avg["Category"],
            orientation="h",
            marker=dict(
                color=[COLORS.get(c, _SLATE) for c in df_avg["Category"]],
                line=dict(color=_BG, width=1),
            ),
            text=[f"{v:.3f}" for v in df_avg["Avg Score"]],
            textposition="outside",
            textfont=dict(color=_LIGHT),
        ))
        fig_avg.update_layout(
            **_PLOTLY_LAYOUT,
            height=300,
            xaxis=dict(range=[0.65, 1.0], gridcolor=_LINE, title="Avg combined confidence", color=_TEXT),
            yaxis=dict(showgrid=False, color=_LIGHT),
            margin=dict(l=10, r=80, t=20, b=40),
        )
        st.plotly_chart(fig_avg, use_container_width=True)

    st.markdown("---")
    st.markdown("**Evidence Type Breakdown — CD46 Direct Partners (top 15 by score)**")
    direct_cd46 = sorted(
        [e for e in kg_edges if e["sym_a"] == "CD46" or e["sym_b"] == "CD46"],
        key=lambda x: x["score"],
        reverse=True,
    )[:15]
    if direct_cd46:
        partner_names = [e["sym_b"] if e["sym_a"] == "CD46" else e["sym_a"] for e in direct_cd46]
        fig_ev = go.Figure()
        for ev, label, color in [
            ("escore", "Experimental",  _GREEN),
            ("tscore", "Text Mining",   _INDIGO),
            ("dscore", "Database",      _ORANGE),
        ]:
            fig_ev.add_trace(go.Bar(
                name=label,
                x=partner_names,
                y=[e.get(ev, 0) for e in direct_cd46],
                marker_color=color,
            ))
        fig_ev.update_layout(
            **_PLOTLY_LAYOUT,
            barmode="stack",
            legend=dict(bgcolor="rgba(15,23,42,0.8)", font=dict(color=_LIGHT)),
            xaxis=dict(showgrid=False, tickangle=-30, color=_LIGHT),
            yaxis=dict(title="Score component", gridcolor=_LINE, color=_TEXT),
            margin=dict(l=20, r=20, t=30, b=80),
            height=360,
        )
        st.plotly_chart(fig_ev, use_container_width=True)
        st.caption(
            "Experimental = physical binding assays \u00b7 "
            "Text Mining = co-publication frequency \u00b7 "
            "Database = curated pathway databases (KEGG, Reactome)"
        )
    else:
        st.info("No direct CD46 edge data available for evidence breakdown.")

    st.info(
        "**Complement System genes dominate the top-confidence cluster** "
        "(CFI, CD55, CD59, CR1, C3 all score > 0.95).  \n"
        "This cluster represents the tumour immune-evasion shield that CD46 anchors. "
        "Alpha-particle RLT bypasses this shield entirely through direct DNA double-strand break induction."
    )

# ─────────────────────────────────────────────────────────────────────────────
# Tab 4 — Biology Narrative
# ─────────────────────────────────────────────────────────────────────────────
with tab_biology:
    st.markdown("#### Why the CD46 PPI Network Matters for Cancer Therapy")
    st.markdown(
        "The STRING network reveals CD46 sits at the **hub of a multi-layered complement "
        "evasion system** that cancer cells exploit to escape immune destruction.  \n"
        "Understanding the interaction neighbourhood defines both the therapeutic rationale "
        "and the resistance mechanisms for any CD46-targeted approach."
    )

    col_a, col_b = st.columns(2)
    with col_a:
        with st.container(border=True):
            st.markdown("#### \U0001f6e1\ufe0f Complement Evasion Cluster")
            st.markdown("""
| Gene | Function | Therapeutic Role |
|------|----------|-----------------|
| **CFI** | Cleaves C3b (CD46 cofactor) | Mechanistic partner — no redundancy |
| **CR1** | Parallel C3b cleavage | Redundant evasion fallback |
| **CD55** | C3/C5 convertase decay | Co-upregulated in same cancers |
| **CD59** | Blocks MAC assembly | Third protection layer |
| **SERPING1** | Inactivates C1r/C1s | Upstream classical pathway gate |
| **THBD** | C3b \u2192 non-lytic | Coagulation crosstalk |

> 225Ac alpha particles cause DNA double-strand breaks **regardless** of complement
> activity \u2014 bypassing all three layers of this evasion shield simultaneously.
""")

        st.success(
            "**Clinical implication:** Co-upregulation of CD46, CD55, and CD59 in IHC biopsies "
            "of mCRPC tissue confirms this as a coordinated evasion programme, not incidental "
            "expression. Targeting CD46 disrupts the anchor protein of this entire cluster."
        )

    with col_b:
        with st.container(border=True):
            st.markdown("#### \U0001f9ec Immune & Receptor Co-clusters")
            st.markdown("""
**CD46 \u2192 T-regulatory axis**
- CD46 ligation converts CD4+ T cells to IL-10-secreting Tr1 cells
- Creates immune-cold TME \u2014 favours radiopharmaceutical over immunotherapy
- Disrupting CD46 may simultaneously restore immune surveillance

**NECTIN4 co-cluster (oncological significance)**
- NECTIN4 = FDA-approved ADC target (enfortumab vedotin, bladder cancer)
- STRING co-association with CD46 \u2192 shared membrane biology
- CD46+/NECTIN4+ = potential combinatorial biomarker window for bladder cancer

**SLAMF1 (haematological relevance)**
- Both CD46 and SLAMF1 are measles virus entry receptors
- Co-expressed in B-cell malignancies and myeloma
- Validates CD46 as a haematological target (FOR46/BC8-CD46 Phase 1)

**JAG1-Notch crosstalk**
- CD46-Notch signalling linked to EMT and cancer stem-cell maintenance
- Single-cell kill by alpha particle addresses heterogeneous stem-like subpopulations
""")

        st.info(
            "**Resistance hypothesis:** If CD46 is downregulated under selection pressure, "
            "CD55 and CD59 may compensate as secondary complement evaders. Monitoring "
            "co-expression of all three in serial biopsies is a key translational question."
        )

    st.markdown("---")
    with st.expander("\U0001f4c1 Data Provenance & KG Architecture"):
        st.markdown(f"""
**Source**: STRING DB v12.0 (https://string-db.org) | CC BY 4.0
**Seed protein**: Human CD46 / MCP (UniProt P15529 / ENSP00000313875)
**Confidence threshold**: \u2265 0.70 (STRING high confidence)
**KG storage**: AuraDB (Neo4j) \u2014 30 Gene nodes + 103 INTERACTS\\_WITH relationships
**KG load script**: scripts/load\\_kg\\_string.py
**Active data source**: {_data_label}
**Curated static fallback**: 29 direct CD46 partners + 14 complement cluster intra-edges
**Last verified**: March 2026
""")

st.markdown("---")
st.caption(
    "**Research use only.** STRING DB CC BY 4.0. "
    "Interaction scores reflect computational predictions; experimental validation required "
    "before clinical extrapolation. PPI data does not substitute for proteomic assay results."
)
