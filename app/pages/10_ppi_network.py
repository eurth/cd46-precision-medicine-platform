"""Page 10 — CD46 Protein–Protein Interaction Network Explorer.

Visualises the STRING DB v12.0 high-confidence PPI network centred on CD46.
Data is read directly from AuraDB (Neo4j KG) via INTERACTS_WITH relationships
loaded by scripts/load_kg_string.py.

Source: STRING DB https://string-db.org  (CC BY 4.0)
KG load: scripts/load_kg_string.py (30 Gene nodes, 103 INTERACTS_WITH rels)
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

# Inject Streamlit Cloud secrets -> os.environ
for _k in ("NEO4J_URI", "NEO4J_USERNAME", "NEO4J_PASSWORD"):
    try:
        if _k in st.secrets and not os.environ.get(_k):
            os.environ[_k] = st.secrets[_k]
    except Exception:
        pass


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
    except Exception as e:
        st.error(f"AuraDB connection failed: {e}")
        return None


@st.cache_data(ttl=3600, show_spinner="Loading PPI network from knowledge graph...")
def load_ppi_from_kg() -> tuple[list, list]:
    driver = get_driver()
    if driver is None:
        return [], []
    try:
        with driver.session() as session:
            node_result = session.run("""
                MATCH (g:Gene)
                WHERE EXISTS { (g)-[:INTERACTS_WITH]-() }
                   OR g.symbol = 'CD46'
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
        return nodes, edges
    except Exception as e:
        st.error(f"KG query failed: {e}")
        return [], []


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
    "CD46 (Hub)":            "#f97316",
    "Complement System":     "#3b82f6",
    "Immune / T-cell":       "#22c55e",
    "Viral Entry Receptor":  "#a855f7",
    "Notch / Oncogenic":     "#ec4899",
    "Coagulation Crosstalk": "#ef4444",
    "Cell Surface / Adhesion": "#06b6d4",
    "Structural":            "#94a3b8",
}

GENE_INSIGHTS: dict[str, str] = {
    "C3":       "Central complement node. Cleavage by C3b/C4b is inactivated by CD46, enabling cancer immune evasion.",
    "CFI":      "Complement Factor I. Works with CD46 as cofactor to inactivate C3b — key mechanistic partner.",
    "CR1":      "Complement Receptor 1 (CD35). Also cleaves C3b; co-expressed with CD46 on immune and tumour cells.",
    "CD55":     "Decay-accelerating factor. Second major complement regulator co-overexpressed with CD46 in many tumours.",
    "CD59":     "Protectin. Inhibits MAC (C5b-9) formation — third layer of complement evasion on tumour surface.",
    "THBD":     "Thrombomodulin. Links complement to coagulation; overexpressed in aggressive cancers.",
    "JAG1":     "Jagged-1 (Notch ligand). CD46-Notch cross-talk implicated in EMT and stem-like cancer phenotype.",
    "CD4":      "T-cell coreceptor. CD46 modulates CD4+ Treg induction, converting anti-tumour T cells to immunosuppressive.",
    "SLAMF1":   "Signalling lymphocyte activation molecule. Co-receptor in measles virus biology; co-expressed in haematological malignancies.",
    "SERPING1": "C1-Inhibitor. Regulates classical complement pathway; correlates with immune-cold tumour microenvironments.",
    "CFB":      "Complement Factor B. Alternative pathway amplifier.",
}


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


# ── Page header ───────────────────────────────────────────────────────────────

st.markdown(
    page_hero(
        icon="🕸️",
        module_name="PPI Network Explorer",
        purpose="CD46 protein–protein interaction network · STRING DB v12.0 · 30 partners · 103 interactions · visualised from AuraDB",
        kpi_chips=[
            ("PPI Partners", "30"),
            ("Interactions", "103"),
            ("Source", "STRING DB"),
            ("Confidence", "High (≥0.7)"),
        ],
        source_badges=["STRING", "UniProt"],
    ),
    unsafe_allow_html=True,
)
st.markdown(
    "**CD46 protein-protein interaction neighbourhood** | "
    "Source: [STRING DB](https://string-db.org) v12.0 | CC BY 4.0 | "
    "Human CD46 (UniProt P15529) | Score >= 0.70 = high confidence | "
    "Data queried live from AuraDB knowledge graph."
)

kg_nodes, kg_edges = load_ppi_from_kg()

if not kg_nodes or not kg_edges:
    st.error(
        "No PPI data found in the knowledge graph. "
        "Run `scripts/load_kg_string.py` to load STRING interactions into AuraDB."
    )
    st.stop()

# ── Sidebar controls ───────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### Network Controls")
    min_score = st.slider("Minimum STRING Score", 0.70, 0.99, 0.70, 0.01, format="%.2f",
                          help="0.70=high | 0.90=very high | 0.99=highest")
    all_cats = list(COLORS.keys())
    show_categories = st.multiselect("Pathway Categories", options=all_cats, default=all_cats)
    layout_seed = st.number_input("Layout seed", value=42, min_value=0, max_value=9999)
    show_labels = st.checkbox("Show gene labels", value=True)

# ── Build graph ────────────────────────────────────────────────────────────────
G_full = build_graph(kg_nodes, kg_edges, min_score=0.70)
visible = {n for n in G_full.nodes() if get_cat(n) in show_categories}
G_sub   = G_full.subgraph(visible).copy()
# Re-apply score filter after subgraph
G = nx.Graph()
G.add_nodes_from(G_sub.nodes(data=True))
for u, v, d in G_sub.edges(data=True):
    if d.get("score", 0) >= min_score:
        G.add_edge(u, v, **d)

n_nodes = G.number_of_nodes()
n_edges = G.number_of_edges()
complement_genes = [n for n in G.nodes() if get_cat(n) == "Complement System"]
edge_scores = [d["score"] for _, _, d in G.edges(data=True)]

m1, m2, m3, m4 = st.columns(4)
m1.metric("PPI Partners", n_nodes - (1 if "CD46" in G else 0), "interacting proteins")
m2.metric("Interactions", n_edges, f"score >= {min_score:.2f}")
m3.metric("Complement Genes", len(complement_genes), "immune evasion network")
m4.metric("Highest Score", f"{max(edge_scores):.3f}" if edge_scores else "n/a", "combined confidence")

st.markdown("---")

tab_net, tab_table, tab_pathway, tab_biology = st.tabs([
    "Network Graph", "Partner Table", "Pathway Breakdown", "Biology Narrative"
])

# ── TAB 1: Network Graph ───────────────────────────────────────────────────────
with tab_net:
    if n_nodes == 0:
        st.warning("No nodes match current filters.")
        st.stop()

    pos = nx.spring_layout(G, seed=int(layout_seed), k=0.55, iterations=100)

    fig = go.Figure()
    for lo, hi, color, width in [(0.90, 1.01, "#475569", 1.8),
                                   (0.80, 0.90, "#334155", 1.2),
                                   (0.70, 0.80, "#1e293b", 0.8)]:
        ex, ey = [], []
        for u, v, d in G.edges(data=True):
            if lo <= d.get("score", 0) < hi and u in pos and v in pos:
                x0, y0 = pos[u]; x1, y1 = pos[v]
                ex += [x0, x1, None]; ey += [y0, y1, None]
        if ex:
            fig.add_trace(go.Scatter(x=ex, y=ey, mode="lines",
                                     line=dict(width=width, color=color),
                                     hoverinfo="none", showlegend=False))

    for cat in show_categories:
        cat_nodes = [n for n in G.nodes() if get_cat(n) == cat and n in pos]
        if not cat_nodes:
            continue
        sizes = [42 if n == "CD46" else max(14, min(32, G.degree(n)*5+12)) for n in cat_nodes]
        hover_texts = [
            f"<b>{n}</b><br>Category: {cat}<br>Connections: {G.degree(n)}<br>"
            f"{'<i>' + GENE_INSIGHTS[n] + '</i><br>' if n in GENE_INSIGHTS else ''}"
            f"<small>{G.nodes[n].get('annotation','')[:160]}...</small>"
            for n in cat_nodes
        ]
        fig.add_trace(go.Scatter(
            x=[pos[n][0] for n in cat_nodes],
            y=[pos[n][1] for n in cat_nodes],
            mode="markers+text" if show_labels else "markers",
            marker=dict(size=sizes, color=COLORS.get(cat, "#94a3b8"),
                        line=dict(width=2, color="white"), opacity=0.92),
            text=cat_nodes if show_labels else [""] * len(cat_nodes),
            textposition="top center",
            textfont=dict(size=9, color="#e2e8f0"),
            hovertext=hover_texts, hoverinfo="text", name=cat,
        ))

    fig.update_layout(
        showlegend=True,
        legend=dict(orientation="v", x=1.01, y=1, bgcolor="rgba(15,23,42,0.85)",
                    bordercolor="#334155", borderwidth=1, font=dict(color="white", size=11)),
        plot_bgcolor="#0f172a", paper_bgcolor="#0f172a", font=dict(color="white"),
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False,
                   scaleanchor="y", constrain="domain"),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        height=640, margin=dict(l=10, r=220, t=20, b=10),
        hoverlabel=dict(bgcolor="#1e293b", bordercolor="#475569",
                        font=dict(color="white", size=12)),
    )
    st.plotly_chart(fig, width="stretch")
    st.caption("Node size = connections | Edge brightness = confidence | Hover for annotations")

# ── TAB 2: Partner Table ───────────────────────────────────────────────────────
with tab_table:
    st.subheader("CD46 Direct Interaction Partners")
    direct = [
        {"Gene": e["sym_b"] if e["sym_a"] == "CD46" else e["sym_a"],
         "Category": get_cat(e["sym_b"] if e["sym_a"] == "CD46" else e["sym_a"]),
         "Combined Score": round(e["score"], 3),
         "Experimental": round(e["escore"], 3),
         "Text Mining": round(e["tscore"], 3),
         "Database": round(e["dscore"], 3)}
        for e in kg_edges if e["sym_a"] == "CD46" or e["sym_b"] == "CD46"
    ]
    if direct:
        df_p = pd.DataFrame(direct).sort_values("Combined Score", ascending=False).reset_index(drop=True)
        sel = st.multiselect("Filter by category", df_p["Category"].unique().tolist(),
                              default=df_p["Category"].unique().tolist(), key="tab2_cat")
        df_show = df_p[df_p["Category"].isin(sel)]
        st.dataframe(
            df_show.style.background_gradient(subset=["Combined Score"], cmap="Blues", vmin=0.65, vmax=1.0)
                         .background_gradient(subset=["Experimental"], cmap="Greens", vmin=0, vmax=0.5),
            use_container_width=True, height=420)
        st.caption(f"{len(df_show)} direct CD46 partners shown")
    else:
        st.info("No direct CD46 edges in KG.")
    st.markdown("---")
    st.subheader("All Network Edges")
    df_all = pd.DataFrame([{"Gene A": e["sym_a"], "Gene B": e["sym_b"],
                              "Score": round(e["score"], 3),
                              "Experimental": round(e["escore"], 3),
                              "Text Mining": round(e["tscore"], 3)}
                            for e in kg_edges]).sort_values("Score", ascending=False)
    c1, c2 = st.columns(2)
    sf = c1.slider("Min score", 0.70, 1.0, 0.70, 0.01, key="all_score")
    df_all = df_all[df_all["Score"] >= sf]
    c2.metric("Edges shown", len(df_all))
    st.dataframe(df_all, use_container_width=True, height=350)

# ── TAB 3: Pathway Breakdown ───────────────────────────────────────────────────
with tab_pathway:
    col_donut, col_bar = st.columns(2)
    with col_donut:
        st.subheader("Proteins by Pathway")
        cat_counts: dict[str, int] = {}
        for n in G_full.nodes():
            c = get_cat(n); cat_counts[c] = cat_counts.get(c, 0) + 1
        fig_d = go.Figure(go.Pie(
            labels=list(cat_counts.keys()), values=list(cat_counts.values()),
            marker=dict(colors=[COLORS.get(c, "#94a3b8") for c in cat_counts],
                        line=dict(color="#0f172a", width=2)),
            hole=0.55, textinfo="label+value", textfont=dict(size=11, color="white"),
        ))
        fig_d.update_layout(paper_bgcolor="#0f172a", plot_bgcolor="#0f172a",
                             font=dict(color="white"), showlegend=False,
                             margin=dict(l=20, r=20, t=20, b=20), height=300,
                             annotations=[dict(text=f"<b>{G_full.number_of_nodes()}<br>proteins</b>",
                                               x=0.5, y=0.5, font_size=15, font_color="white", showarrow=False)])
        st.plotly_chart(fig_d, width="stretch")

    with col_bar:
        st.subheader("Avg Score by Category")
        cat_sc: dict[str, list] = {}
        for e in kg_edges:
            for sym in [e["sym_a"], e["sym_b"]]:
                cat_sc.setdefault(get_cat(sym), []).append(e["score"])
        df_avg = pd.DataFrame([{"Category": c, "Avg Score": round(sum(v)/len(v), 3)}
                                for c, v in cat_sc.items()]).sort_values("Avg Score")
        fig_b = go.Figure(go.Bar(
            x=df_avg["Avg Score"], y=df_avg["Category"], orientation="h",
            marker=dict(color=[COLORS.get(c, "#94a3b8") for c in df_avg["Category"]],
                        line=dict(color="#0f172a", width=1)),
            text=[f"{v:.3f}" for v in df_avg["Avg Score"]], textposition="outside",
            textfont=dict(color="white"),
        ))
        fig_b.update_layout(paper_bgcolor="#0f172a", plot_bgcolor="#0f172a",
                             font=dict(color="white"),
                             xaxis=dict(range=[0.65, 1.0], showgrid=True, gridcolor="#1e293b",
                                        title="Avg combined confidence"),
                             yaxis=dict(showgrid=False),
                             margin=dict(l=10, r=80, t=20, b=40), height=300)
        st.plotly_chart(fig_b, width="stretch")

    st.markdown("---")
    st.subheader("Evidence Type Breakdown (CD46-direct partners)")
    direct_cd46 = sorted(
        [e for e in kg_edges if e["sym_a"] == "CD46" or e["sym_b"] == "CD46"],
        key=lambda x: x["score"], reverse=True)[:15]
    if direct_cd46:
        pnames = [e["sym_b"] if e["sym_a"] == "CD46" else e["sym_a"] for e in direct_cd46]
        fig_ev = go.Figure()
        for ev, label, color in [("escore", "Experimental", "#22c55e"),
                                   ("tscore", "Text Mining", "#3b82f6"),
                                   ("dscore", "Database", "#f97316")]:
            fig_ev.add_trace(go.Bar(name=label, x=pnames,
                                    y=[e.get(ev, 0) for e in direct_cd46],
                                    marker_color=color))
        fig_ev.update_layout(barmode="stack", paper_bgcolor="#0f172a", plot_bgcolor="#0f172a",
                              font=dict(color="white"),
                              legend=dict(bgcolor="rgba(15,23,42,0.8)"),
                              xaxis=dict(showgrid=False, tickangle=-30),
                              yaxis=dict(title="Score component", gridcolor="#1e293b"),
                              margin=dict(l=20, r=20, t=30, b=80), height=360)
        st.plotly_chart(fig_ev, width="stretch")
        st.caption("Experimental = physical assays | Text Mining = co-publication | Database = curated pathways")

# ── TAB 4: Biology Narrative ───────────────────────────────────────────────────
with tab_biology:
    st.subheader("Why the CD46 PPI Network Matters for Cancer Therapy")
    st.markdown("""
    The STRING network (queried live from AuraDB) reveals CD46 sits at the **hub of a
    multi-layered complement evasion system** that cancer cells exploit to escape immune destruction.
    """)
    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown("""#### Complement Evasion Cluster
| Gene | Function | Role |
|------|----------|------|
| **CFI** | Cleaves C3b (CD46 cofactor) | Mechanistic partner |
| **CR1** | Parallel C3b cleavage | Redundant evasion |
| **CD55** | C3/C5 convertase decay | Co-upregulated in same cancers |
| **CD59** | Blocks MAC assembly | Third protection layer |
| **SERPING1** | Inactivates C1r/C1s | Upstream gatekeeper |
| **THBD** | C3b -> non-lytic | Coagulation crosstalk |

> 225Ac alpha particles cause DNA double-strand breaks regardless of complement
> activity -- bypassing all layers of this evasion shield.
""")
    with col_b:
        st.markdown("""#### Immune & Receptor Co-clusters
**CD46 -> T-regulatory axis**
- CD46 ligation converts CD4+ T cells to IL-10-secreting Tr1 cells
- Creates immune-cold TME -- favours radiopharmaceutical over immunotherapy

**NECTIN4 co-cluster (oncological significance)**
- NECTIN4 = FDA-approved ADC target (Enfortumab vedotin, bladder cancer)
- STRING co-association with CD46 suggests shared membrane biology
- CD46+/NECTIN4+ = potential combinatorial biomarker window

**SLAMF1 (haematological relevance)**
- Both CD46 and SLAMF1 are measles virus receptors
- Co-expressed in B-cell malignancies and myeloma
""")
    st.markdown("---")
    with st.expander("Data Provenance & KG Architecture"):
        st.markdown("""
**Source**: STRING DB v12.0 (https://string-db.org) | CC BY 4.0
**Seed**: Human CD46 / MCP (UniProt P15529 / ENSP00000313875)
**Confidence threshold**: >= 0.70 (STRING high confidence)
**KG storage**: AuraDB (Neo4j) -- 30 Gene nodes + 103 INTERACTS_WITH rels
**Query**: `MATCH (a:Gene)-[r:INTERACTS_WITH]-(b:Gene) RETURN ...`
**Raw JSON**: NOT committed to git (data/raw/ is gitignored) -- AuraDB is the system of record
**Load script**: scripts/load_kg_string.py
**Fetched**: March 9, 2026
""")
