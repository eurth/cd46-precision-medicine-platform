"""Page 10 — CD46 Protein–Protein Interaction Network Explorer.

Visualises the STRING DB v12.0 high-confidence PPI network centred on CD46
(UniProt P15529 / 9606.ENSP00000313875).

Source: STRING DB https://string-db.org  (CC BY 4.0)
Data:   data/raw/apis/string_cd46.json  (fetched by scripts/load_kg_string.py)
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import networkx as nx
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import streamlit as st

# ── Pathway / category annotation ───────────────────────────────────────────
# Each gene in the STRING neighbourhood is manually assigned a biological
# context relevant to CD46 biology (complement, immune evasion, etc.)
PATHWAY_MAP: dict[str, str] = {
    "CD46":     "CD46 (Hub)",
    # Complement cascade
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
    # Immune interaction
    "CD4":      "Immune / T-cell",
    "SLAMF1":   "Immune / T-cell",
    # Viral entry / oncogenic receptors
    "CXADR":    "Viral Entry Receptor",
    "DSG2":     "Viral Entry Receptor",
    "NECTIN4":  "Viral Entry Receptor",
    "ERVW-1":   "Viral Entry Receptor",
    # Developmental / oncogenic signalling
    "JAG1":     "Notch / Oncogenic",
    # Coagulation — complement-coagulation crosstalk
    "ADAMTS13": "Coagulation Crosstalk",
    "DGKE":     "Coagulation Crosstalk",
    # Cell surface / adhesion
    "CD81":     "Cell Surface / Adhesion",
    "CD9":      "Cell Surface / Adhesion",
    "MSN":      "Cell Surface / Adhesion",
    # Structural / cytoskeletal
    "GOPC":     "Structural",
    "MYBPH":    "Structural",
    "MYOM2":    "Structural",
    "AGBL3":    "Structural",
}

COLORS: dict[str, str] = {
    "CD46 (Hub)":           "#f97316",   # orange — focal point
    "Complement System":    "#3b82f6",   # blue — core biology
    "Immune / T-cell":      "#22c55e",   # green — immune response
    "Viral Entry Receptor": "#a855f7",   # purple — receptor biology
    "Notch / Oncogenic":    "#ec4899",   # pink — oncogenic signalling
    "Coagulation Crosstalk":"#ef4444",   # red — crosstalk
    "Cell Surface / Adhesion": "#06b6d4",# cyan — membrane biology
    "Structural":           "#94a3b8",   # slate — background
}

# Short biological summaries for the insight panel (curated)
GENE_INSIGHTS: dict[str, str] = {
    "C3":   "Central complement node. Cleavage by C3b/C4b is inactivated by CD46, enabling cancer immune evasion.",
    "CFI":  "Complement Factor I. Works *with* CD46 as cofactor to inactivate C3b — key CD46 mechanism partner.",
    "CR1":  "Complement Receptor 1 (CD35). Also cleaves C3b; co-expressed with CD46 on immune cells and tumour cells.",
    "CD55": "Decay-accelerating factor. Second major complement regulator co-overexpressed with CD46 in many tumours.",
    "CD59": "Protectin. Inhibits MAC (C5b-9) formation — third layer of complement evasion on tumour surface.",
    "THBD": "Thrombomodulin. Links complement to coagulation; overexpressed in aggressive cancers.",
    "JAG1": "Jagged-1 (Notch ligand). CD46 cross-talk with Notch implicated in EMT and stem-like cancer phenotype.",
    "CD4":  "T-cell coreceptor. CD46 modulates CD4+ Treg induction, converting anti-tumour T cells to immunosuppressive.",
    "SLAMF1": "Signalling lymphocyte activation molecule. CD46 and SLAMF1 share measles virus receptor biology; co-expressed in haematological malignancies.",
    "SERPING1": "C1-Inhibitor (C1-INH). Regulates classical complement pathway; overexpression correlates with immune-cold tumour microenvironments.",
    "CFB":  "Complement Factor B. Alternative pathway amplifier — CD46 overexpression shifts balance away from C3 activation.",
}

DATA_FILE = Path("data/raw/apis/string_cd46.json")


@st.cache_data(ttl=3600)
def load_string_data() -> tuple[list, dict]:
    if not DATA_FILE.exists():
        return [], {}
    raw = json.loads(DATA_FILE.read_text())
    return raw.get("edges", []), raw.get("annotations", {})


def get_cat(sym: str) -> str:
    return PATHWAY_MAP.get(sym, "Structural")


def build_graph(edges: list, min_score: float) -> nx.Graph:
    G = nx.Graph()
    for e in edges:
        a, b = e["preferredName_A"], e["preferredName_B"]
        sc = e.get("score", 0)
        if sc < min_score:
            continue
        G.add_node(a)
        G.add_node(b)
        G.add_edge(a, b, score=sc,
                   escore=round(e.get("escore", 0), 4),
                   tscore=round(e.get("tscore", 0), 4),
                   dscore=round(e.get("dscore", 0), 4))
    return G


def get_annotation(sym: str, annotations: dict) -> str:
    for _, adata in annotations.items():
        if adata.get("name") == sym:
            return adata.get("annotation", "")
    return ""


# ── Page header ──────────────────────────────────────────────────────────────
st.title("🕸️ CD46 PPI Network Explorer")
st.markdown(
    "**CD46 protein–protein interaction neighbourhood** · "
    "Source: [STRING DB](https://string-db.org) v12.0 · CC BY 4.0 · "
    "Human CD46 (UniProt P15529) · Score ≥ 0.70 = high confidence"
)

all_edges, annotations = load_string_data()

if not all_edges:
    st.error("STRING data not found. Run `scripts/load_kg_string.py` first.")
    st.stop()

# ── Sidebar controls ─────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🔧 Network Controls")
    min_score = st.slider(
        "Minimum STRING Score",
        min_value=0.70, max_value=0.99,
        value=0.70, step=0.01, format="%.2f",
        help="STRING combined confidence score. 0.70=high · 0.90=very high · 0.99=highest",
    )
    all_cats = list(COLORS.keys())
    show_categories = st.multiselect(
        "Pathway Categories",
        options=all_cats,
        default=all_cats,
        help="Filter which biological categories appear in the network",
    )
    layout_seed = st.number_input(
        "Layout seed (reproducibility)", value=42, min_value=0, max_value=9999,
        help="Change to rearrange node positions",
    )
    show_labels = st.checkbox("Show gene labels", value=True)

# ── Build filtered graph ──────────────────────────────────────────────────────
G_full = build_graph(all_edges, min_score)
visible_nodes = {n for n in G_full.nodes() if get_cat(n) in show_categories}
G = G_full.subgraph(visible_nodes).copy()

n_nodes = G.number_of_nodes()
n_edges = G.number_of_edges()
complement_genes = [n for n in G.nodes() if get_cat(n) == "Complement System"]

# ── Top metrics ───────────────────────────────────────────────────────────────
m1, m2, m3, m4 = st.columns(4)
m1.metric("PPI Partners", n_nodes - 1 if "CD46" in G else n_nodes,
          "unique interacting proteins")
m2.metric("Interactions", n_edges, f"score ≥ {min_score:.2f}")
m3.metric("Complement Genes", len(complement_genes), "immune evasion network")
m4.metric("Highest Score", f"{max((e[2]['score'] for e in G.edges(data=True)), default=0):.3f}",
          "combined confidence")

st.markdown("---")

# ── Tabs ─────────────────────────────────────────────────────────────────────
tab_net, tab_table, tab_pathway, tab_biology = st.tabs([
    "🌐 Network Graph", "📋 Partner Table", "🥧 Pathway Breakdown", "🧬 Biology Narrative"
])

# ──────────────────────────────────────────────────────────────────────────────
# TAB 1 — Interactive Network Graph
# ──────────────────────────────────────────────────────────────────────────────
with tab_net:
    if n_nodes == 0:
        st.warning("No nodes match current filters. Reduce score threshold or add pathway categories.")
        st.stop()

    # Compute spring layout
    pos = nx.spring_layout(G, seed=int(layout_seed), k=0.55, iterations=100)

    fig = go.Figure()

    # ── Edges (drawn first, behind nodes) ────────────────────────────────────
    # Group edges by score tier for colour gradient
    score_tiers = [
        (0.90, 1.01, "#475569", 1.8),   # very high: brighter
        (0.80, 0.90, "#334155", 1.2),   # high
        (0.70, 0.80, "#1e293b", 0.8),   # moderate-high
    ]
    for lo, hi, color, width in score_tiers:
        ex, ey = [], []
        for u, v, data in G.edges(data=True):
            sc = data.get("score", 0)
            if lo <= sc < hi and u in pos and v in pos:
                x0, y0 = pos[u]
                x1, y1 = pos[v]
                ex += [x0, x1, None]
                ey += [y0, y1, None]
        if ex:
            fig.add_trace(go.Scatter(
                x=ex, y=ey, mode="lines",
                line=dict(width=width, color=color),
                hoverinfo="none", showlegend=False,
            ))

    # ── Nodes (grouped by category for legend) ───────────────────────────────
    for cat in show_categories:
        cat_nodes = [n for n in G.nodes() if get_cat(n) == cat and n in pos]
        if not cat_nodes:
            continue

        nx_vals = [pos[n][0] for n in cat_nodes]
        ny_vals = [pos[n][1] for n in cat_nodes]

        # Size: CD46 hub = 40, others scaled by degree
        sizes = []
        for n in cat_nodes:
            if n == "CD46":
                sizes.append(42)
            else:
                deg = G.degree(n)
                sizes.append(max(14, min(32, deg * 5 + 12)))

        hover_texts = []
        for n in cat_nodes:
            deg = G.degree(n)
            ann = get_annotation(n, annotations)[:180]
            insight = GENE_INSIGHTS.get(n, "")
            edges_to = sorted(
                [v for u, v in G.edges(n)] + [u for u, v in G.edges(n) if v == n],
                key=lambda x: G[n].get(x, {}).get("score", 0), reverse=True
            )[:5]
            hover_texts.append(
                f"<b>{n}</b><br>"
                f"Category: {cat}<br>"
                f"Connections: {deg}<br>"
                f"{'<br><i>' + insight + '</i><br>' if insight else ''}"
                f"{'<br><small>' + ann + '...</small>' if ann else ''}"
            )

        label_texts = cat_nodes if show_labels else [""] * len(cat_nodes)

        fig.add_trace(go.Scatter(
            x=nx_vals, y=ny_vals,
            mode="markers+text" if show_labels else "markers",
            marker=dict(
                size=sizes,
                color=COLORS.get(cat, "#94a3b8"),
                line=dict(width=2, color="white"),
                opacity=0.92,
            ),
            text=label_texts,
            textposition="top center",
            textfont=dict(size=9, color="#e2e8f0"),
            hovertext=hover_texts,
            hoverinfo="text",
            name=cat,
        ))

    fig.update_layout(
        showlegend=True,
        legend=dict(
            orientation="v",
            x=1.01, y=1,
            bgcolor="rgba(15,23,42,0.85)",
            bordercolor="#334155",
            borderwidth=1,
            font=dict(color="white", size=11),
        ),
        plot_bgcolor="#0f172a",
        paper_bgcolor="#0f172a",
        font=dict(color="white"),
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False,
                   scaleanchor="y", constrain="domain"),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        height=640,
        margin=dict(l=10, r=220, t=20, b=10),
        hoverlabel=dict(bgcolor="#1e293b", bordercolor="#475569",
                        font=dict(color="white", size=12)),
    )

    st.plotly_chart(fig, width="stretch")

    st.caption(
        "**Node size** = number of STRING interactions · "
        "**Edge brightness** = confidence score (brighter = higher confidence) · "
        "Hover nodes for biological annotation. "
        "Use sidebar to adjust score threshold and categories."
    )

# ──────────────────────────────────────────────────────────────────────────────
# TAB 2 — Partner Table
# ──────────────────────────────────────────────────────────────────────────────
with tab_table:
    st.subheader("CD46 Interaction Partners — Ranked by STRING Score")

    # Build partner rows: interactions involving CD46 specifically
    partner_rows = []
    for e in all_edges:
        a, b = e["preferredName_A"], e["preferredName_B"]
        partner = None
        if a == "CD46":
            partner = b
        elif b == "CD46":
            partner = a
        if partner is None:
            continue
        ann = get_annotation(partner, annotations)[:200]
        partner_rows.append({
            "Gene": partner,
            "Category": PATHWAY_MAP.get(partner, "Structural"),
            "Combined Score": round(e.get("score", 0), 3),
            "Experimental": round(e.get("escore", 0), 3),
            "Text Mining": round(e.get("tscore", 0), 3),
            "Database": round(e.get("dscore", 0), 3),
            "Annotation": ann or "—",
        })

    if partner_rows:
        df_partners = pd.DataFrame(partner_rows).sort_values(
            "Combined Score", ascending=False
        ).reset_index(drop=True)

        # Filter by category
        cats_in_table = df_partners["Category"].unique().tolist()
        sel_cats = st.multiselect(
            "Filter by category", options=cats_in_table,
            default=cats_in_table, key="table_cat_filter"
        )
        df_show = df_partners[df_partners["Category"].isin(sel_cats)]

        st.dataframe(
            df_show.style.background_gradient(
                subset=["Combined Score"], cmap="Blues", vmin=0.65, vmax=1.0
            ).background_gradient(
                subset=["Experimental"], cmap="Greens", vmin=0, vmax=0.5
            ),
            use_container_width=True,
            height=420,
        )
        st.caption(f"Showing {len(df_show)} of {len(df_partners)} direct CD46 interaction partners")
    else:
        st.info("No direct CD46 edges found in current data.")

    st.markdown("---")
    st.subheader("All Network Edges")
    st.markdown(
        "The network contains interactions between **all 30 proteins** in the neighbourhood "
        "(not just CD46), revealing how the complement/immune cluster self-organises."
    )
    df_all = pd.DataFrame([{
        "Gene A": e["preferredName_A"],
        "Gene B": e["preferredName_B"],
        "Score": round(e.get("score", 0), 3),
        "Experimental": round(e.get("escore", 0), 3),
        "Text Mining": round(e.get("tscore", 0), 3),
    } for e in all_edges]).sort_values("Score", ascending=False)

    col_f1, col_f2 = st.columns(2)
    score_filter = col_f1.slider(
        "Min score", 0.70, 1.0, 0.70, 0.01, key="all_edges_score"
    )
    df_all = df_all[df_all["Score"] >= score_filter]
    col_f2.metric("Edges shown", len(df_all))
    st.dataframe(df_all, use_container_width=True, height=350)

# ──────────────────────────────────────────────────────────────────────────────
# TAB 3 — Pathway Breakdown
# ──────────────────────────────────────────────────────────────────────────────
with tab_pathway:
    col_donut, col_bar = st.columns(2)

    # Donut — node count per category
    with col_donut:
        st.subheader("Proteins by Pathway Category")
        cat_counts: dict[str, int] = {}
        for n in G_full.nodes():
            cat = get_cat(n)
            cat_counts[cat] = cat_counts.get(cat, 0) + 1

        fig_donut = go.Figure(go.Pie(
            labels=list(cat_counts.keys()),
            values=list(cat_counts.values()),
            marker=dict(colors=[COLORS.get(c, "#94a3b8") for c in cat_counts.keys()],
                        line=dict(color="#0f172a", width=2)),
            hole=0.55,
            textinfo="label+value",
            textfont=dict(size=11, color="white"),
            hovertemplate="<b>%{label}</b><br>Proteins: %{value}<br>%{percent}<extra></extra>",
        ))
        fig_donut.update_layout(
            paper_bgcolor="#0f172a", plot_bgcolor="#0f172a",
            font=dict(color="white"),
            showlegend=False,
            margin=dict(l=20, r=20, t=20, b=20),
            height=300,
            annotations=[dict(text=f"<b>{G_full.number_of_nodes()}<br>proteins</b>",
                              x=0.5, y=0.5, font_size=15, font_color="white",
                              showarrow=False)],
        )
        st.plotly_chart(fig_donut, width="stretch")

    # Bar — average score per category
    with col_bar:
        st.subheader("Avg. STRING Score by Category")
        cat_scores: dict[str, list] = {}
        for e in all_edges:
            for sym in [e["preferredName_A"], e["preferredName_B"]]:
                cat = get_cat(sym)
                cat_scores.setdefault(cat, []).append(e["score"])
        cat_avg = {c: round(sum(v)/len(v), 3) for c, v in cat_scores.items()}
        df_avg = pd.DataFrame(
            [{"Category": c, "Avg Score": v} for c, v in cat_avg.items()]
        ).sort_values("Avg Score", ascending=True)

        fig_bar = go.Figure(go.Bar(
            x=df_avg["Avg Score"],
            y=df_avg["Category"],
            orientation="h",
            marker=dict(
                color=[COLORS.get(c, "#94a3b8") for c in df_avg["Category"]],
                line=dict(color="#0f172a", width=1),
            ),
            text=[f"{v:.3f}" for v in df_avg["Avg Score"]],
            textposition="outside",
            textfont=dict(color="white"),
        ))
        fig_bar.update_layout(
            paper_bgcolor="#0f172a", plot_bgcolor="#0f172a",
            font=dict(color="white"),
            xaxis=dict(range=[0.65, 1.0], showgrid=True, gridcolor="#1e293b",
                       title="Average combined confidence"),
            yaxis=dict(showgrid=False),
            margin=dict(l=10, r=80, t=20, b=40),
            height=300,
        )
        st.plotly_chart(fig_bar, width="stretch")

    st.markdown("---")

    # Score evidence breakdown for CD46-direct partners
    st.subheader("Evidence Type Breakdown (CD46-direct partners)")
    direct_cd46 = [
        e for e in all_edges
        if e["preferredName_A"] == "CD46" or e["preferredName_B"] == "CD46"
    ]
    if direct_cd46:
        ev_types = ["escore", "tscore", "dscore"]
        ev_labels = {"escore": "Experimental", "tscore": "Text Mining", "dscore": "Database"}
        partners_sorted = sorted(
            direct_cd46, key=lambda x: x["score"], reverse=True
        )[:15]
        partners_names = [
            e["preferredName_B"] if e["preferredName_A"] == "CD46" else e["preferredName_A"]
            for e in partners_sorted
        ]

        fig_ev = go.Figure()
        ev_colors = {"escore": "#22c55e", "tscore": "#3b82f6", "dscore": "#f97316"}
        for ev in ev_types:
            fig_ev.add_trace(go.Bar(
                name=ev_labels[ev],
                x=partners_names,
                y=[e.get(ev, 0) for e in partners_sorted],
                marker_color=ev_colors[ev],
            ))
        fig_ev.update_layout(
            barmode="stack",
            paper_bgcolor="#0f172a", plot_bgcolor="#0f172a",
            font=dict(color="white"),
            legend=dict(bgcolor="rgba(15,23,42,0.8)", bordercolor="#334155",
                        borderwidth=1),
            xaxis=dict(showgrid=False, tickangle=-30),
            yaxis=dict(title="Score component", showgrid=True, gridcolor="#1e293b"),
            margin=dict(l=20, r=20, t=30, b=80),
            height=360,
        )
        st.plotly_chart(fig_ev, width="stretch")
        st.caption(
            "**Experimental** = physical interaction assays · "
            "**Text Mining** = co-occurrence in publications · "
            "**Database** = curated pathway databases"
        )

# ──────────────────────────────────────────────────────────────────────────────
# TAB 4 — Biology Narrative (Complement Evasion Story)
# ──────────────────────────────────────────────────────────────────────────────
with tab_biology:
    st.subheader("🧬 Why the CD46 PPI Network Matters for Cancer Therapy")

    st.markdown("""
    The STRING network reveals that CD46 is not an isolated surface antigen — it sits at the
    **hub of a multi-layered complement evasion system** that cancer cells exploit to escape
    immune destruction. Understanding this network is essential for designing effective
    225Ac-CD46 radiopharmaceutical therapy.
    """)

    col_a, col_b = st.columns(2)

    with col_a:
        st.markdown("#### The Complement Evasion Cluster")
        st.markdown("""
        CD46 co-expresses and physically interacts with a coordinated cluster of complement
        regulators on the tumour surface:

        | Gene | Function | Interaction with CD46 |
        |------|----------|----------------------|
        | **CFI** | Cleaves C3b (requires CD46 as cofactor) | Mechanistic partner — direct co-factor |
        | **CR1** | Also cleaves C3b, binds C1q | Parallel pathway — redundant evasion |
        | **CD55** | Accelerates C3/C5 convertase decay | Co-upregulated in same cancers |
        | **CD59** | Blocks MAC (C5b-9) pore assembly | Third layer — post-convertase protection |
        | **SERPING1** | Inactivates C1r/C1s (classical) | Upstream gatekeeper |
        | **THBD** | Converts C3b → non-lytic | Coagulation–complement crosstalk |

        > **Therapeutic implication**: Tumours with high CD46 expression often simultaneously
        > upregulate CFI, CD55, and CD59, creating a **multi-layer complement shield**.
        > 225Ac-delivered DNA damage bypasses this entire cascade — alpha particles are
        > cytotoxic regardless of complement activity.
        """)

    with col_b:
        st.markdown("#### Immune Evasion Beyond Complement")
        st.markdown("""
        The network identifies two additional immune-relevant interactions:

        **CD46 → CD4 / T-regulatory axis**
        - CD46 binding to its ligands (C3b, MBL) triggers signalling through the cytoplasmic
          tails (CYT-1 or CYT-2 splice forms)
        - CD4+ T cells engaged through CD46 are converted to **IL-10-secreting Tr1 cells**
          (regulatory T cells) — immunosuppressive phenotype
        - In the tumour microenvironment, this converts CD46-expressing tumour-infiltrating
          T cells into tolerogenic suppressors
        - **Implication**: CD46-high tumours may have an immune-cold/suppressed TME,
          making radiopharmaceutical approaches (which bypass T-cell immunity) particularly
          suited as primary treatment

        **CD46 ↔ SLAMF1**
        - Both are measles virus entry receptors; their co-expression on B-cell malignancies
          and myeloma cells makes this population particularly tractable for CD46-targeted RLT
        - STRING experimental score: 0.151 (validated co-receptor biology)
        """)

    st.markdown("---")

    st.markdown("#### Viral Receptor / Oncogenic Receptor Co-cluster")
    st.markdown("""
    A striking finding in the STRING network is the clustering of CD46 with a set of
    well-established **viral entry receptors** repurposed in oncology:

    | Gene | Virus/Biology | Cancer Relevance |
    |------|--------------|-----------------|
    | **CXADR** | Coxsackievirus & Adenovirus Receptor | Oncolytic virus therapy target; downregulated in advanced prostate cancer |
    | **DSG2** | Adenovirus 3/7/11/14 receptor — Desmoglein-2 | Cell adhesion, EMT; high expression in NSCLC, breast, head & neck |
    | **NECTIN4** | Measles F-protein receptor | FDA-approved Enfortumab vedotin ADC target (urothelial cancer) |
    | **ERVW-1** | Syncytin-1 (endogenous retrovirus) | Mediates cell fusion; upregulated in multiple myeloma, breast, colorectal |

    > NECTIN4 is particularly notable — it is already an approved ADC target (Enfortumab vedotin,
    > bladder cancer). Its STRING co-association with CD46 suggests shared membrane biology
    > in tumours co-expressing both targets. **CD46+/NECTIN4+ tumours** could be identified
    > as a combinatorial biomarker window.
    """)

    st.markdown("---")

    with st.expander("📖 Data Provenance & Methods"):
        st.markdown("""
        **Data source**: STRING DB v12.0 (https://string-db.org) · CC BY 4.0 licence  
        **Seed protein**: Human CD46 / MCP (UniProt P15529 · ENSP00000313875)  
        **Confidence threshold**: ≥ 0.70 (STRING "high confidence" band)  
        **Network scope**: Top-50 interaction partners by combined score  
        **Evidence channels**: Experimental co-expression, text-mining, curated databases,
        neighbourhood co-occurrence, gene fusion, co-occurrence  
        **KG integration**: All 30 partner Gene nodes + 103 INTERACTS_WITH rels loaded into
        AuraDB (Neo4j) with score properties  
        **Fetch script**: `scripts/load_kg_string.py`  
        **Fetched**: March 9, 2026  
        """)
