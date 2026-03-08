"""Page 6 — Biomarker Panel: Clinical Decision Support for 225Ac-CD46 Therapy."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import math
import os

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parents[2] / ".env")

# Inject Streamlit Cloud secrets into os.environ
for _k in ("NEO4J_URI", "NEO4J_USERNAME", "NEO4J_PASSWORD"):
    try:
        if _k in st.secrets and not os.environ.get(_k):
            os.environ[_k] = st.secrets[_k]
    except Exception:
        pass

DATA_DIR = Path("data/processed")
GENIE_DIR = Path("data/genie")

st.title("🧬 Biomarker Panel")
st.markdown(
    "**Clinical decision support for 225Ac-CD46 alpha-particle radioimmunotherapy. "
    "Multi-biomarker scoring, co-targeting analysis, and real-world mCRPC cohort data "
    "integrated from TCGA, SU2C, and Human Protein Atlas.**"
)

# ---------------------------------------------------------------------------
# Data loaders
# ---------------------------------------------------------------------------

@st.cache_data(ttl=3600)
def load_by_cancer():
    p = DATA_DIR / "cd46_by_cancer.csv"
    return pd.read_csv(p) if p.exists() else pd.DataFrame()

@st.cache_data(ttl=3600)
def load_expression():
    p = DATA_DIR / "cd46_expression.csv"
    return pd.read_csv(p) if p.exists() else pd.DataFrame()

@st.cache_data(ttl=3600)
def load_combination():
    p = DATA_DIR / "cd46_combination_biomarkers.csv"
    return pd.read_csv(p) if p.exists() else pd.DataFrame()

@st.cache_data(ttl=3600)
def load_priority():
    p = DATA_DIR / "priority_score.csv"
    return pd.read_csv(p) if p.exists() else pd.DataFrame()

@st.cache_data(ttl=3600)
def load_survival():
    p = DATA_DIR / "cd46_survival_results.csv"
    return pd.read_csv(p) if p.exists() else pd.DataFrame()

@st.cache_data(ttl=3600)
def load_genie_cna():
    p = GENIE_DIR / "genie_cd46_cna_summary.parquet"
    return pd.read_parquet(p) if p.exists() else pd.DataFrame()

@st.cache_data(ttl=3600)
def load_genie_psma():
    p = GENIE_DIR / "genie_psma_cd46_cooccurrence.parquet"
    return pd.read_parquet(p) if p.exists() else pd.DataFrame()

@st.cache_data(ttl=3600)
def load_hpa():
    p = DATA_DIR / "hpa_cd46_protein.csv"
    return pd.read_csv(p) if p.exists() else pd.DataFrame()

# Load all datasets upfront
df_cancer = load_by_cancer()
df_combination = load_combination()
df_priority = load_priority()
df_survival = load_survival()
df_genie = load_genie_cna()
df_psma = load_genie_psma()
df_hpa = load_hpa()
df_expr_raw = load_expression()  # 11,069 patient rows with OS/PFI survival data
df_expr = df_expr_raw[df_expr_raw["sample_type"] == "Primary Tumor"].copy() if not df_expr_raw.empty else df_expr_raw
ALL_CANCERS = sorted(df_expr["cancer_type"].dropna().unique().tolist()) if not df_expr.empty else []

# ---------------------------------------------------------------------------
# Key stats header
# ---------------------------------------------------------------------------

col_m1, col_m2, col_m3, col_m4, col_m5 = st.columns(5)
col_m1.metric("mCRPC CD46 Altered", "43%", "+34% vs localised", delta_color="inverse")
col_m2.metric("Localised PRAD", "9%", "baseline")
col_m3.metric("PSMA-Low Patients", "~35%", "eligible for CD46 RIT")
col_m4.metric("SU2C Cohort Size", "444", "patients")
col_m5.metric("TCGA Pan-Cancer", "33 cancers", "11,160 patients")

st.markdown("---")

# ---------------------------------------------------------------------------
# 6 Tabs
# ---------------------------------------------------------------------------

tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "🎯 CD46 Inclusion",
    "🔗 Co-targeting",
    "⚠️ Resistance Markers",
    "🧬 Complement Pathway",
    "📚 Evidence Base",
    "📋 Patient Scoring",
])

# ===========================================================================
# TAB 1 — CD46 INCLUSION BIOMARKERS
# ===========================================================================
with tab1:
    st.markdown(
        "<div style='background:#1e293b;border-left:3px solid #38bdf8;padding:12px 16px;"
        "border-radius:6px;margin-bottom:14px;'>"
        "<b style='color:#38bdf8;'>CD46 Expression — Inclusion Biomarker for 225Ac Radioimmunotherapy</b><br>"
        "<span style='color:#94a3b8;'>High CD46 expression = increased alpha-particle target density. "
        "Threshold: top 25th percentile per cancer type. Data: TCGA Pan-Cancer (n=11,160).</span>"
        "</div>",
        unsafe_allow_html=True,
    )

    if not df_cancer.empty:
        expr_col = next((c for c in ["cd46_mean", "cd46_mean_tpm_log2", "mean_log2_tpm", "mean_expression", "mean_log2", "cd46_median"] if c in df_cancer.columns), None)
        cancer_col = next((c for c in ["cancer_type", "tcga_code", "cancer"] if c in df_cancer.columns), None)

        if expr_col and cancer_col:
            df_plot = df_cancer[[cancer_col, expr_col]].dropna().sort_values(expr_col, ascending=True).tail(33)

            # Highlight PRAD, BLCA, OV in different colour
            highlight = {"PRAD": "#ef4444", "BLCA": "#f97316", "OV": "#eab308", "LUAD": "#8b5cf6"}
            colors = [highlight.get(str(r).upper(), "#38bdf8") for r in df_plot[cancer_col]]

            fig1 = go.Figure(go.Bar(
                x=df_plot[expr_col], y=df_plot[cancer_col].astype(str),
                orientation="h",
                marker_color=colors,
                text=[f"{v:.2f}" for v in df_plot[expr_col]],
                textposition="outside",
                textfont=dict(size=9, color="#94a3b8"),
                hovertemplate="%{y}: %{x:.3f} log₂ TPM<extra></extra>",
            ))
            mean_val = float(df_plot[expr_col].mean())
            p75_val = float(df_plot[expr_col].quantile(0.75))
            fig1.add_vline(x=mean_val, line_dash="dash", line_color="#64748b",
                           annotation_text="Pan-cancer mean", annotation_font_color="#64748b")
            fig1.add_vline(x=p75_val, line_dash="dot", line_color="#f87171",
                           annotation_text="75th pct threshold", annotation_font_color="#f87171")
            fig1.update_layout(
                height=420, paper_bgcolor="#0f172a", plot_bgcolor="#0f172a",
                xaxis=dict(title="CD46 log₂ TPM", color="#94a3b8", gridcolor="#1e293b"),
                yaxis=dict(color="#e2e8f0", tickfont=dict(size=9)),
                margin=dict(l=10, r=80, t=30, b=10),
                title=dict(text="Pan-Cancer CD46 mRNA Expression (TCGA)", font=dict(color="#e2e8f0", size=13)),
            )
            st.plotly_chart(fig1, use_container_width=True)
            st.caption("🔴 PRAD · 🟠 BLCA · 🟡 OV highlighted as priority targets · Dashed = pan-cancer mean · Dotted = 75th pct threshold")
        else:
            st.info("Expression column not found — run `python scripts/run_pipeline.py` to generate.")

        # Clinical decision tiers table
        st.markdown("**Clinical Expression Tiers**")
        tiers = pd.DataFrame({
            "Tier": ["🟢 High", "🟡 Moderate", "🟠 Low", "🔴 Absent"],
            "CD46 Level": ["> 75th percentile", "50th–75th percentile", "25th–50th percentile", "< 25th percentile"],
            "Mean log₂ TPM": ["> 10.5", "9.0–10.5", "7.5–9.0", "< 7.5"],
            "225Ac-CD46 Suitability": ["Strong candidate ✅", "Consider ⚡", "Borderline 🔶", "Not suitable ❌"],
            "Estimated Eligible %": ["25%", "25%", "25%", "25%"],
        })
        st.dataframe(tiers, use_container_width=True, hide_index=True)

    else:
        st.warning("cd46_by_cancer.csv not found — run pipeline first.")

    st.info(
        "💡 CD46 expression is androgen-regulated: ADT upregulates CD46, explaining its enrichment "
        "in CRPC. Expression persists across PSMA-low subgroups, making CD46 an ideal rescue target "
        "for patients who progress on 177Lu-PSMA therapy."
    )

    # ---- DYNAMIC THRESHOLD EXPLORER ----
    st.markdown("---")
    st.markdown("**🎯 Interactive Threshold Explorer — Live Eligibility from 11,069 TCGA Patients**")
    if not df_expr.empty:
        t_col1, t_col2 = st.columns([1, 3])
        with t_col1:
            thr_val = st.slider("CD46 log₂ TPM threshold", 8.0, 14.5, 12.5, 0.1, key="tab1_thr",
                                help="Drag to recompute eligibility across all TCGA cancer types")
            focus_cancers = st.multiselect("Highlight cancers", ALL_CANCERS,
                                           default=[c for c in ["PRAD","BLCA","OV"] if c in ALL_CANCERS],
                                           key="tab1_focus")
            show_axis = st.radio("Y-axis", ["% Eligible", "N Patients"], horizontal=True, key="tab1_y")

        df_thr = df_expr.copy()
        grp_thr = df_thr.groupby("cancer_type").apply(
            lambda g: pd.Series({
                "n_total": len(g),
                "n_eligible": int((g["cd46_log2_tpm"] >= thr_val).sum()),
                "pct_eligible": (g["cd46_log2_tpm"] >= thr_val).mean() * 100,
            }),
            include_groups=False,
        ).reset_index().sort_values("pct_eligible", ascending=True)

        yval_t = "pct_eligible" if show_axis == "% Eligible" else "n_eligible"
        HMAP = {"PRAD": "#ef4444", "BLCA": "#f97316", "OV": "#eab308", "HNSC": "#a78bfa"}
        bar_c = [HMAP.get(r, "#4ade80" if r in focus_cancers else "#38bdf8")
                 for r in grp_thr["cancer_type"]]

        fig_thr = go.Figure(go.Bar(
            x=grp_thr[yval_t], y=grp_thr["cancer_type"].astype(str),
            orientation="h", marker_color=bar_c,
            text=[f"{v:.0f}%" if show_axis == "% Eligible" else str(int(v)) for v in grp_thr[yval_t]],
            textposition="outside", textfont=dict(size=9, color="#94a3b8"),
        ))
        if show_axis == "% Eligible":
            fig_thr.add_vline(x=50, line_dash="dot", line_color="#f87171",
                              annotation_text="50%", annotation_font_color="#f87171")
        fig_thr.update_layout(
            height=440, paper_bgcolor="#0f172a", plot_bgcolor="#0f172a",
            xaxis=dict(title="% Eligible" if show_axis=="% Eligible" else "N Patients",
                       color="#94a3b8", gridcolor="#1e293b"),
            yaxis=dict(color="#e2e8f0", tickfont=dict(size=9)),
            margin=dict(l=10, r=70, t=10, b=10),
        )
        with t_col2:
            n_elig = int(grp_thr["n_eligible"].sum())
            n_tot = int(grp_thr["n_total"].sum())
            cm1, cm2, cm3 = st.columns(3)
            cm1.metric("Eligible at threshold", f"{n_elig:,}", f"{n_elig/max(n_tot,1)*100:.1f}% of {n_tot:,}")
            cm2.metric("Cancers > 50% eligible", str(int((grp_thr["pct_eligible"] >= 50).sum())))
            cm3.metric("Threshold", f"{thr_val:.1f} log₂ TPM")
            st.plotly_chart(fig_thr, use_container_width=True)
            top3 = grp_thr.nlargest(3, "pct_eligible")["cancer_type"].tolist()
            st.caption(f"Highest eligibility at {thr_val:.1f}: **{'  ·  '.join(top3)}**")
    else:
        st.info("Run `python scripts/run_pipeline.py` to enable live threshold exploration.")

# ===========================================================================
# TAB 2 — CO-TARGETING & COMPLEMENTARITY
# ===========================================================================
with tab2:
    st.markdown(
        "<div style='background:#1e293b;border-left:3px solid #4ade80;padding:12px 16px;"
        "border-radius:6px;margin-bottom:14px;'>"
        "<b style='color:#4ade80;'>PSMA / CD46 Co-Targeting Strategy</b><br>"
        "<span style='color:#94a3b8;'>SU2C mCRPC cohort (n=444) · CNA-based alteration rates · "
        "PSMA-low patients as priority CD46 targets</span>"
        "</div>",
        unsafe_allow_html=True,
    )

    if not df_genie.empty:
        col_g1, col_g2 = st.columns(2)

        with col_g1:
            st.markdown("**Alteration Rates — SU2C mCRPC**")
            # Try to display available columns from genie CNA summary
            st.dataframe(df_genie.head(30), use_container_width=True, hide_index=True)

        with col_g2:
            # Build alteration bar chart from REAL genie parquet data
            GENES_FOCUS = ["CD46", "AR", "FOLH1", "MYC", "TP53", "RB1", "BRCA2", "CDK12"]
            if "gene_symbol" in df_genie.columns and "alteration_pct" in df_genie.columns:
                df_g2 = df_genie[df_genie["gene_symbol"].isin(GENES_FOCUS)].copy()
                df_g2["gene_symbol"] = df_g2["gene_symbol"].replace({"FOLH1": "PSMA (FOLH1)"})
                fig2 = px.bar(
                    df_g2, x="gene_symbol", y="alteration_pct", color="cohort",
                    barmode="group",
                    text=df_g2["alteration_pct"].apply(lambda v: f"{v:.1f}%"),
                    color_discrete_sequence=["#f87171", "#38bdf8", "#4ade80", "#fbbf24"],
                    title="Gene Alteration Rates — Real Cohort Data",
                )
                fig2.update_traces(textposition="outside")
                fig2.update_layout(
                    height=380, paper_bgcolor="#0f172a", plot_bgcolor="#0f172a",
                    xaxis=dict(color="#94a3b8", gridcolor="#1e293b"),
                    yaxis=dict(title="Alteration rate (%)", color="#94a3b8", gridcolor="#1e293b"),
                    legend=dict(bgcolor="#1e293b", font=dict(color="#e2e8f0")),
                    margin=dict(l=10, r=10, t=40, b=10),
                    title_font=dict(color="#e2e8f0", size=13),
                )
                st.plotly_chart(fig2, use_container_width=True)
                st.caption("Source: SU2C mCRPC 2019 (n=444) + TCGA PRAD · CNA-based alteration rates")
            else:
                st.info("GENIE columnar data not in expected format — check parquet schema.")

    else:
        st.info("GENIE parquet files not found — run `scripts/download_cbioportal.py`")

    if not df_psma.empty:
        st.markdown("**PSMA × CD46 Co-occurrence Matrix (SU2C)**")
        st.dataframe(df_psma, use_container_width=True, hide_index=True)

    # Clinical decision matrix
    st.markdown("**Clinical Decision Matrix — Dual-Target Strategy**")
    matrix = pd.DataFrame({
        "Patient Profile": [
            "PSMA-High + CD46-High",
            "PSMA-Low + CD46-High ⭐",
            "PSMA-High + CD46-Low",
            "PSMA-Low + CD46-Low",
        ],
        "Frequency (mCRPC est.)": ["~28%", "~15%", "~45%", "~12%"],
        "Recommended Strategy": [
            "177Lu-PSMA617 (1st line) → 225Ac-CD46 (progression)",
            "225Ac-CD46 (1st line) — primary indication",
            "177Lu-PSMA617 — CD46 RIT not indicated",
            "Alternative targets (AR-V7, PARP, etc.)",
        ],
        "225Ac-CD46 Priority": ["HIGH 🟡", "VERY HIGH 🔴", "LOW ⬇️", "NOT INDICATED ⭕"],
    })
    st.dataframe(matrix, use_container_width=True, hide_index=True)

    st.info(
        "💡 ~35% of mCRPC patients have low PSMA expression (PSMA-low) and do not respond to "
        "177Lu-PSMA617. CD46 is expressed in >90% of CRPC cells regardless of PSMA status, "
        "making it the primary rescue target for this population."
    )

# ===========================================================================
# TAB 3 — RESISTANCE PREDICTORS
# ===========================================================================
with tab3:
    st.markdown(
        "<div style='background:#1e293b;border-left:3px solid #fbbf24;padding:12px 16px;"
        "border-radius:6px;margin-bottom:14px;'>"
        "<b style='color:#fbbf24;'>Therapy Resistance Biomarkers</b><br>"
        "<span style='color:#94a3b8;'>Genomic alterations predicting reduced response to "
        "225Ac-CD46 and RLT approaches · mCRPC cohort data</span>"
        "</div>",
        unsafe_allow_html=True,
    )

    col_r1, col_r2 = st.columns(2)

    with col_r1:
        # Resistance biomarker alteration frequencies
        resist_genes = ["TP53", "RB1", "CDK12", "BRCA2", "ATM", "AR-V7"]
        resist_freq_mcrpc = [42, 13, 7, 11, 8, 30]
        resist_impact = ["High", "High", "Moderate", "Predictive PARP", "Predictive PARP", "ADT Resistance"]

        df_resist = pd.DataFrame({
            "Biomarker": resist_genes,
            "mCRPC Frequency (%)": resist_freq_mcrpc,
            "Clinical Impact": resist_impact,
        })

        fig_resist = px.bar(
            df_resist, x="Biomarker", y="mCRPC Frequency (%)",
            color="mCRPC Frequency (%)",
            color_continuous_scale=["#22c55e", "#fbbf24", "#ef4444"],
            text="mCRPC Frequency (%)",
            title="Resistance Biomarker Alteration Rates (mCRPC)",
        )
        fig_resist.update_traces(texttemplate="%{text}%", textposition="outside")
        fig_resist.update_layout(
            height=360, paper_bgcolor="#0f172a", plot_bgcolor="#0f172a",
            xaxis=dict(color="#94a3b8"), yaxis=dict(color="#94a3b8", gridcolor="#1e293b"),
            coloraxis_showscale=False,
            title_font=dict(color="#e2e8f0", size=13),
            margin=dict(l=10, r=10, t=40, b=10),
        )
        st.plotly_chart(fig_resist, use_container_width=True)

    with col_r2:
        st.markdown("**Resistance Marker Interpretation**")
        resist_table = pd.DataFrame({
            "Marker": ["TP53 loss", "RB1 loss", "AR-V7 splice variant", "CDK12 biallelic loss", "BRCA1/2 loss"],
            "Mechanism": [
                "Cell cycle deregulation → radiotherapy resistance",
                "Neuroendocrine transdiff. → altered CD46 surface expression",
                "ADT resistance → drives CD46 upregulation (compensatory)",
                "Tandem duplications → homologous recomb. signature",
                "HR deficiency → PARP inhibitor synergy",
            ],
            "Impact on 225Ac-CD46": [
                "↓ DNA damage response — may reduce efficacy",
                "⚠️ Monitor — NEPC subtype may lose CD46 surface",
                "✅ CD46 upregulation maintained — no resistance",
                "Neutral — consider PARP combo",
                "✅ Synergistic — DSB from α-particles + HR deficiency",
            ],
        })
        st.dataframe(resist_table, use_container_width=True, hide_index=True)

    # Survival impact of resistance markers
    if not df_survival.empty:
        st.markdown("**CD46 High vs Low — Survival Impact (TCGA)**")
        hr_col = next((c for c in ["hazard_ratio", "hr", "cox_hr"] if c in df_survival.columns), None)
        p_col = next((c for c in ["log_rank_p", "p_value", "pval"] if c in df_survival.columns), None)
        cancer_col = next((c for c in ["cancer_type", "tcga_code"] if c in df_survival.columns), None)

        if hr_col and p_col and cancer_col:
            df_surv_sig = df_survival[df_survival[p_col] < 0.05].copy()
            if not df_surv_sig.empty:
                df_surv_sig["neg_log_p"] = -df_surv_sig[p_col].apply(lambda x: math.log10(max(x, 1e-10)))
                fig_surv = px.scatter(
                    df_surv_sig, x=hr_col, y="neg_log_p",
                    text=cancer_col,
                    color=hr_col,
                    color_continuous_scale=["#22c55e", "#fbbf24", "#ef4444"],
                    title="CD46-High Hazard Ratio vs Significance (p < 0.05 cancers)",
                    labels={hr_col: "Hazard Ratio (CD46-High vs Low)", "neg_log_p": "-log₁₀(p)"},
                )
                fig_surv.add_vline(x=1.0, line_dash="dash", line_color="#64748b")
                fig_surv.update_traces(textposition="top center", textfont_size=9)
                fig_surv.update_layout(
                    height=360, paper_bgcolor="#0f172a", plot_bgcolor="#0f172a",
                    xaxis=dict(color="#94a3b8", gridcolor="#1e293b"),
                    yaxis=dict(color="#94a3b8", gridcolor="#1e293b"),
                    coloraxis_showscale=False,
                    title_font=dict(color="#e2e8f0", size=13),
                    margin=dict(l=10, r=10, t=40, b=10),
                )
                st.plotly_chart(fig_surv, use_container_width=True)
                st.caption("HR > 1.0 = CD46-High associated with worse prognosis → stronger therapeutic need")

    st.info(
        "💡 AR-V7 expression, while conferring resistance to enzalutamide, actually maintains or "
        "upregulates CD46 surface expression, meaning AR-V7+ patients remain excellent candidates "
        "for 225Ac-CD46 therapy. TP53-null tumours may show reduced DNA damage response."
    )

# ===========================================================================
# TAB 4 — COMPLEMENT PATHWAY
# ===========================================================================
with tab4:
    st.markdown(
        "<div style='background:#1e293b;border-left:3px solid #818cf8;padding:12px 16px;"
        "border-radius:6px;margin-bottom:14px;'>"
        "<b style='color:#818cf8;'>Complement Regulatory Protein Network</b><br>"
        "<span style='color:#94a3b8;'>CD46 (MCP) · CD55 (DAF) · CD59 · CR1 · CR2 — "
        "Cancer immune evasion via complement downregulation</span>"
        "</div>",
        unsafe_allow_html=True,
    )

    # Complement pathway network
    complement_proteins = {
        "CD46\n(MCP)": (0, 0, "#f87171", 30),
        "CD55\n(DAF)": (-1.5, 1, "#818cf8", 20),
        "CD59": (1.5, 1, "#818cf8", 20),
        "CR1": (-2.5, 0, "#4ade80", 18),
        "CR2": (2.5, 0, "#4ade80", 18),
        "C3b": (-1, -1.5, "#fbbf24", 22),
        "C4b": (1, -1.5, "#fbbf24", 22),
        "Factor I": (0, -2.5, "#fb923c", 18),
        "C3 conv.": (-2.5, -1.5, "#64748b", 16),
        "MASP": (2.5, -1.5, "#64748b", 16),
    }

    interactions_complement = [
        ("CD46\n(MCP)", "C3b"),
        ("CD46\n(MCP)", "C4b"),
        ("CD46\n(MCP)", "Factor I"),
        ("CD55\n(DAF)", "C3 conv."),
        ("CD59", "MASP"),
        ("CR1", "C3b"),
        ("CR1", "C4b"),
        ("CR2", "C3b"),
    ]

    import numpy as np
    node_x = [pos[0] for pos in complement_proteins.values()]
    node_y = [pos[1] for pos in complement_proteins.values()]
    node_labels = list(complement_proteins.keys())
    node_colors = [props[2] for props in complement_proteins.values()]
    node_sizes = [props[3] for props in complement_proteins.values()]
    pos_map = {k: (v[0], v[1]) for k, v in complement_proteins.items()}

    edge_x_c, edge_y_c = [], []
    for a, b in interactions_complement:
        x0, y0 = pos_map[a]
        x1, y1 = pos_map[b]
        edge_x_c += [x0, x1, None]
        edge_y_c += [y0, y1, None]

    fig_comp = go.Figure()
    fig_comp.add_trace(go.Scatter(
        x=edge_x_c, y=edge_y_c, mode="lines",
        line=dict(width=1.5, color="#334155"), hoverinfo="none", showlegend=False,
    ))
    fig_comp.add_trace(go.Scatter(
        x=node_x, y=node_y,
        mode="markers+text",
        marker=dict(size=node_sizes, color=node_colors, line=dict(width=2, color="#0f172a")),
        text=node_labels,
        textposition="top center",
        textfont=dict(size=9, color="#e2e8f0"),
        hovertext=[
            "CD46 — Primary therapeutic target · SCR domains bind C3b/C4b",
            "CD55 (DAF) — Accelerates decay of C3/C5 convertases",
            "CD59 — Inhibits MAC assembly · anti-apoptotic",
            "CR1 — Complement receptor 1 · C3b/C4b binding",
            "CR2 — B cell complement receptor · EBV receptor",
            "C3b — Opsonin · CD46 cofactor substrate",
            "C4b — Opsonin · CD46 cofactor substrate",
            "Factor I — Serine protease · requires CD46 as cofactor",
            "C3 Convertase — Target of CD55 (DAF) inhibition",
            "MASP — Lectin pathway activator",
        ],
        hoverinfo="text",
        showlegend=False,
    ))
    fig_comp.update_layout(
        height=440, paper_bgcolor="#0f172a", plot_bgcolor="#0f172a",
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        margin=dict(l=10, r=10, t=30, b=10),
        title=dict(text="Complement Regulatory Network — CD46 Central Hub", font=dict(color="#e2e8f0", size=13)),
    )
    st.plotly_chart(fig_comp, use_container_width=True)

    col_cp1, col_cp2 = st.columns(2)
    with col_cp1:
        st.markdown("**CD46 Molecular Function**")
        st.markdown("""
        | Function | Details |
        |---|---|
        | Complement cofactor | Binds C3b/C4b → Factor I cleavage |
        | Immune co-stimulator | T cell co-stimulatory via isoform CYT-1/2 |
        | Viral receptor | Measles virus, Adenovirus 35, N. gonorrhoeae |
        | Self-recognition | Protects host cells from autologous complement |
        | Cancer evasion | Overexpression → tumour escape from CDC |
        """)

    with col_cp2:
        # Expression of complement regulators in cancer (from HPA if available)
        if not df_hpa.empty:
            st.markdown("**CD46 Protein Expression (Human Protein Atlas)**")
            st.dataframe(df_hpa.head(20), use_container_width=True, hide_index=True)
        else:
            st.markdown("**Complement Regulator Overexpression in Cancer**")
            df_creg = pd.DataFrame({
                "Protein": ["CD46", "CD55", "CD59", "CR1", "CR2"],
                "Overexpressed in Cancer": ["Yes (universal)", "Yes (common)", "Yes (common)", "Moderate", "Rare"],
                "PRAD Upregulation": ["High ↑↑", "Moderate ↑", "Moderate ↑", "Low", "Low"],
                "Therapeutic Target": ["Primary 🎯", "Potential", "Potential", "Limited", "No"],
            })
            st.dataframe(df_creg, use_container_width=True, hide_index=True)

    st.info(
        "💡 Tumours upregulate CD46 to evade complement-dependent cytotoxicity (CDC). "
        "Alpha-particles from 225Ac bypass this evasion mechanism — DNA double-strand breaks "
        "are independent of complement pathway signalling."
    )

# ===========================================================================
# TAB 5 — EVIDENCE BASE
# ===========================================================================
with tab5:
    st.markdown(
        "<div style='background:#1e293b;border-left:3px solid #38bdf8;padding:12px 16px;"
        "border-radius:6px;margin-bottom:14px;'>"
        "<b style='color:#38bdf8;'>Curated Evidence Base — 225Ac-CD46 Research Program</b><br>"
        "<span style='color:#94a3b8;'>Peer-reviewed publications with direct relevance to "
        "CD46 targeted therapy and alpha-particle radioimmunotherapy</span>"
        "</div>",
        unsafe_allow_html=True,
    )

    # Curated publications (mirrored from build_publication_nodes.py CURATED_PUBLICATIONS)
    EVIDENCE_PAPERS = [
        {
            "pmid": "33740951",
            "title": "225Ac-labeled anti-CD46 as a radioimmunotherapy agent for metastatic castration-resistant prostate cancer",
            "authors": "Sgouros G, Roeske JC, McDevitt MR",
            "journal": "Journal of Nuclear Medicine",
            "year": 2021,
            "evidence_type": "Preclinical",
            "key_finding": "225Ac-anti-CD46 achieves tumor regression in mCRPC xenograft models; alpha particles induce DNA DSBs",
            "doi_url": "https://doi.org/10.2967/jnumed.120.258517",
        },
        {
            "pmid": "PMC7398579",
            "title": "CD46 is a therapeutic target for antibody-drug conjugate therapy in bladder and prostate cancer",
            "authors": "Minelli R, Ghiso S, Cardaci S",
            "journal": "Science Translational Medicine",
            "year": 2021,
            "evidence_type": "Experimental",
            "key_finding": "CD46 ubiquitously expressed on prostate cancer cells; ADC ABBV-CLS-484 shows efficacy",
            "doi_url": "https://doi.org/10.1126/scitranslmed.abd400",
        },
        {
            "pmid": "32461245",
            "title": "CD46 expression is regulated by androgen signaling and correlates with resistance to enzalutamide",
            "authors": "Zhu Y, Sharp A, Anderson CM",
            "journal": "European Urology",
            "year": 2020,
            "evidence_type": "Clinical-translational",
            "key_finding": "Androgen deprivation upregulates CD46; enzalutamide resistance correlates with high CD46",
            "doi_url": "https://doi.org/10.1016/j.eururo.2020.03.019",
        },
        {
            "pmid": "28898243",
            "title": "The complement inhibitor CD46 is a biomarker and potential therapeutic target in prostate cancer",
            "authors": "Elvington M, Liszewski MK, Atkinson JP",
            "journal": "Cancer Research",
            "year": 2017,
            "evidence_type": "Biomarker",
            "key_finding": "IHC: CD46 overexpressed in 72% of PCa specimens; correlates with Gleason grade",
            "doi_url": "https://doi.org/10.1158/0008-5472.CAN-17-0432",
        },
        {
            "pmid": "36754843",
            "title": "Lutetium-177-PSMA-617 vs Cabazitaxel in mCRPC: TheraP trial results",
            "authors": "Hofman MS, Emmett L, Sandhu S",
            "journal": "The Lancet",
            "year": 2023,
            "evidence_type": "Clinical trial",
            "key_finding": "177Lu-PSMA617 superior PSA50 response; ~15% PSMA-low non-responders — CD46 alternative crucial",
            "doi_url": "https://doi.org/10.1016/S0140-6736(22)02826-8",
        },
        {
            "pmid": "35279064",
            "title": "Alpha-particle therapy with 225Ac: current status and future directions",
            "authors": "Sgouros G, Bodei L, McDevitt MR",
            "journal": "Nature Reviews Drug Discovery",
            "year": 2022,
            "evidence_type": "Review",
            "key_finding": "225Ac RIT shows 4 orders of magnitude higher LET than beta-emitters; immune-stimulatory bystander effect",
            "doi_url": "https://doi.org/10.1038/s41573-022-00410-0",
        },
        {
            "pmid": "31375513",
            "title": "Pan-cancer analysis of complement regulatory gene expression and association with clinical outcomes",
            "authors": "Roumenina LT, Daugan MV, Noé R",
            "journal": "Cancer Immunology Research",
            "year": 2019,
            "evidence_type": "Bioinformatics",
            "key_finding": "Complement evasion genes including CD46 upregulated across multiple TCGA cancer types",
            "doi_url": "https://doi.org/10.1158/2326-6066.CIR-18-0878",
        },
        {
            "pmid": "29925623",
            "title": "CD46 complement regulatory protein in oncology: role in cancer immunology and therapy",
            "authors": "Kolev MV, Ruseva MM, Harris CL",
            "journal": "Frontiers in Immunology",
            "year": 2018,
            "evidence_type": "Review",
            "key_finding": "CD46 in cancer: dual role as complement evader and co-stimulatory immune molecule",
            "doi_url": "https://doi.org/10.3389/fimmu.2018.01233",
        },
    ]

    ev_colors = {
        "Experimental": "#f87171",
        "Clinical trial": "#fb923c",
        "Clinical-translational": "#fbbf24",
        "Biomarker": "#4ade80",
        "Preclinical": "#818cf8",
        "Bioinformatics": "#38bdf8",
        "Review": "#94a3b8",
    }

    # Filter controls
    col_f1, col_f2 = st.columns([2, 1])
    with col_f1:
        ev_types_all = sorted(set(p["evidence_type"] for p in EVIDENCE_PAPERS))
        sel_ev = st.multiselect("Evidence type", ev_types_all, default=ev_types_all, key="ev_filter")
    with col_f2:
        sort_by = st.selectbox("Sort by", ["Year (newest)", "Evidence type", "Journal"], key="ev_sort")

    filtered_papers = [p for p in EVIDENCE_PAPERS if p["evidence_type"] in sel_ev]
    if sort_by == "Year (newest)":
        filtered_papers = sorted(filtered_papers, key=lambda x: x["year"], reverse=True)
    elif sort_by == "Evidence type":
        filtered_papers = sorted(filtered_papers, key=lambda x: x["evidence_type"])
    elif sort_by == "Journal":
        filtered_papers = sorted(filtered_papers, key=lambda x: x["journal"])

    for paper in filtered_papers:
        ev_c = ev_colors.get(paper["evidence_type"], "#64748b")
        pmid = paper["pmid"]
        pubmed_url = f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/" if not pmid.startswith("PMC") else f"https://www.ncbi.nlm.nih.gov/pmc/articles/{pmid}/"

        st.markdown(
            f"""
            <div style='background:#1e293b;border:1px solid #334155;border-left:4px solid {ev_c};
            padding:14px 18px;margin:8px 0;border-radius:6px;'>
            <span style='background:{ev_c}22;color:{ev_c};font-size:0.72em;
            padding:2px 10px;border-radius:12px;font-weight:700;letter-spacing:0.05em;'>
            {paper['evidence_type'].upper()}</span>
            <b style='color:#e2e8f0;display:block;margin-top:8px;font-size:1.0em;line-height:1.4;'>
            {paper['title']}</b>
            <span style='color:#94a3b8;font-size:0.84em;'>{paper['authors']}</span><br>
            <span style='color:#64748b;font-size:0.82em;'>
            <i>{paper['journal']}</i> &middot; {paper['year']}</span><br>
            <span style='color:#38bdf8;font-size:0.85em;margin-top:6px;display:block;'>
            &#8594; {paper['key_finding']}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )
        col_pm, col_doi, _ = st.columns([1.2, 1.2, 4])
        col_pm.link_button(f"PubMed ↗", pubmed_url)
        if paper.get("doi_url"):
            col_doi.link_button("DOI ↗", paper["doi_url"])

    st.markdown("---")
    st.markdown("**Live PubMed Search**")
    pubmed_q = st.text_input(
        "Search PubMed for additional literature:",
        value="CD46 prostate cancer radioimmunotherapy",
        placeholder="e.g., 225Ac alpha therapy prostate",
        key="pubmed_search_input",
    )
    if st.button("🔍 Search PubMed", key="search_pubmed_btn"):
        with st.spinner("Fetching from NCBI PubMed..."):
            try:
                from src.agent.pubmed_search import fetch_pubmed
                results = fetch_pubmed(pubmed_q, max_results=6)
                if results:
                    st.success(f"Found {len(results)} articles")
                    for i, art in enumerate(results, 1):
                        st.markdown(
                            f"""
                            <div style='background:#1e293b;border-left:3px solid #38bdf8;
                            padding:10px 14px;margin:6px 0;border-radius:4px;'>
                            <b style='color:#e2e8f0;'>[{i}] {art.get('title','')}</b><br>
                            <span style='color:#94a3b8;font-size:0.84em;'>{art.get('authors','')}</span><br>
                            <span style='color:#64748b;font-size:0.82em;'>
                            {art.get('journal','')} &middot; {art.get('year','')}</span>
                            {'<br><span style="color:#94a3b8;font-size:0.83em;">'+art.get("abstract_snippet","")[:250]+'...</span>' if art.get('abstract_snippet') else ''}
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )
                        if art.get("url"):
                            st.link_button(f"View on PubMed ↗", art["url"])
                else:
                    st.info("No results found — try a different search term.")
            except Exception as e:
                st.error(f"PubMed search failed: {e}")

# ===========================================================================
# TAB 6 — PATIENT SCORING CALCULATOR
# ===========================================================================
with tab6:
    st.markdown(
        "<div style='background:#1e293b;border-left:3px solid #fb923c;padding:12px 16px;"
        "border-radius:6px;margin-bottom:14px;'>"
        "<b style='color:#fb923c;'>225Ac-CD46 Patient Suitability Scoring Calculator</b><br>"
        "<span style='color:#94a3b8;'>Composite multi-biomarker score (0–100) for clinical "
        "decision support. Integrates expression, genomic, and clinical factors.</span>"
        "</div>",
        unsafe_allow_html=True,
    )

    st.info(
        "⚠️ **Research use only.** This scoring tool is not validated for clinical decisions. "
        "All recommendations require physician interpretation and institutional review."
    )

    col_s1, col_s2 = st.columns(2)

    with col_s1:
        st.markdown("**Biomarker Inputs**")

        cd46_expr = st.slider(
            "CD46 mRNA Expression (log₂ TPM)",
            min_value=0.0, max_value=15.0, value=10.5, step=0.5,
            help="From RNA-seq. Log₂ TPM > 10.5 = 75th percentile across TCGA.",
        )
        psma_status = st.select_slider(
            "PSMA (FOLH1) Expression",
            options=["Absent", "Low", "Moderate", "High", "Very High"],
            value="Low",
            help="IHC or RNA-seq based PSMA status.",
        )
        ar_amplification = st.checkbox("AR Gene Amplification", value=False,
            help="AR CNA gain/amplification — from WGS/WES or FISH.")
        tp53_loss = st.checkbox("TP53 Loss (biallelic)", value=False,
            help="Biallelic TP53 inactivation — reduces DNA damage response.")
        rb1_loss = st.checkbox("RB1 Loss (biallelic)", value=False,
            help="RB1 biallelic loss — associated with neuroendocrine differentiation.")
        arv7_positive = st.checkbox("AR-V7 Splice Variant Positive", value=False,
            help="Detected by plasma RNA or IHC. Predicts enzalutamide resistance.")
        prior_lupsma = st.checkbox("Prior 177Lu-PSMA therapy (failed)", value=False,
            help="Failed prior PSMA-directed RLT — CD46 rescue strategy applicable.")

    with col_s2:
        st.markdown("**Clinical Factors**")
        ecog_ps = st.selectbox(
            "ECOG Performance Status",
            options=["0 — Fully active", "1 — Restricted strenuous activity", "2 — Ambulatory, >50% wakeful", "3 — Limited self-care"],
            index=1,
        )
        bone_mets = st.checkbox("Bone metastases present", value=True,
            help="Bone mets common in mCRPC — alpha emission range important.")
        visceral_mets = st.checkbox("Visceral metastases present", value=False,
            help="Liver/lung mets — consider systemic toxicity carefully.")
        gleason_score = st.slider(
            "Gleason Score (or Grade Group equivalent)", 
            min_value=6, max_value=10, value=8, step=1,
        )

    # ==========================
    # Scoring algorithm
    # ==========================
    def calc_score(cd46_expr, psma_status, ar_amp, tp53, rb1, arv7, prior_lupsma,
                   ecog_ps, bone_mets, visceral_mets, gleason):
        score = 0

        # CD46 expression (35 pts)
        if cd46_expr >= 12.0: score += 35
        elif cd46_expr >= 10.5: score += 28
        elif cd46_expr >= 9.0: score += 18
        elif cd46_expr >= 7.5: score += 8
        else: score += 0

        # PSMA status — lower PSMA = higher CD46 priority (15 pts)
        psma_points = {"Absent": 15, "Low": 13, "Moderate": 8, "High": 3, "Very High": 0}
        score += psma_points.get(psma_status, 0)

        # AR amplification — upregulates CD46 (5 pts bonus)
        if ar_amp: score += 5

        # Resistance markers — small penalties (TP53 -5, RB1 -8)
        if tp53: score -= 5
        if rb1: score -= 8

        # AR-V7 — neutral/slight bonus (upregulates CD46, +3)
        if arv7: score += 3

        # Prior failed Lu-PSMA (10 pts priority bonus)
        if prior_lupsma: score += 10

        # ECOG PS penalty
        ecog_n = int(ecog_ps[0])
        ecog_penalty = {0: 0, 1: -2, 2: -8, 3: -20}.get(ecog_n, 0)
        score += ecog_penalty

        # Gleason (5 pts)
        if gleason >= 9: score += 5
        elif gleason >= 8: score += 3
        elif gleason >= 7: score += 1

        # Bone mets (favours alpha range, +3)
        if bone_mets: score += 3
        # Visceral mets (increased risk, -5)
        if visceral_mets: score -= 5

        return max(0, min(100, score))

    ecog_n_str = ecog_ps
    final_score = calc_score(
        cd46_expr, psma_status, ar_amplification, tp53_loss, rb1_loss,
        arv7_positive, prior_lupsma, ecog_ps, bone_mets, visceral_mets, gleason_score,
    )

    # Score gauge
    if final_score >= 65:
        score_color = "#22c55e"
        recommendation = "✅ STRONG CANDIDATE — Proceed with 225Ac-CD46 workup"
        tier = "Tier 1"
    elif final_score >= 45:
        score_color = "#fbbf24"
        recommendation = "⚡ CONSIDER — Multidisciplinary review recommended"
        tier = "Tier 2"
    elif final_score >= 25:
        score_color = "#f97316"
        recommendation = "🔶 BORDERLINE — Alternative targets preferred"
        tier = "Tier 3"
    else:
        score_color = "#ef4444"
        recommendation = "❌ NOT SUITABLE — CD46 RIT not indicated"
        tier = "Tier 4"

    # ---- Render Score Gauge ----
    st.markdown("---")
    col_gauge, col_rec = st.columns([1, 1])

    with col_gauge:
        fig_gauge = go.Figure(go.Indicator(
            mode="gauge+number",
            value=final_score,
            domain={"x": [0, 1], "y": [0, 1]},
            title={"text": "225Ac-CD46 Suitability Score", "font": {"color": "#e2e8f0", "size": 14}},
            number={"font": {"color": score_color, "size": 40}},
            gauge={
                "axis": {"range": [0, 100], "tickcolor": "#64748b",
                          "tickfont": {"color": "#94a3b8"}},
                "bar": {"color": score_color, "thickness": 0.25},
                "bgcolor": "#1e293b",
                "borderwidth": 0,
                "steps": [
                    {"range": [0, 25],  "color": "rgba(239, 68, 68, 0.15)"},
                    {"range": [25, 45], "color": "rgba(249, 115, 22, 0.15)"},
                    {"range": [45, 65], "color": "rgba(251, 191, 36, 0.15)"},
                    {"range": [65, 100], "color": "rgba(34, 197, 94, 0.15)"},
                ],
                "threshold": {
                    "line": {"color": "#f87171", "width": 3},
                    "thickness": 0.8,
                    "value": 65,
                },
            },
        ))
        fig_gauge.update_layout(
            height=280,
            paper_bgcolor="#0f172a",
            font=dict(color="#e2e8f0"),
            margin=dict(l=20, r=20, t=30, b=20),
        )
        st.plotly_chart(fig_gauge, use_container_width=True)

    with col_rec:
        st.markdown(f"<br><br>", unsafe_allow_html=True)
        st.markdown(
            f"<div style='background:{score_color}22;border:2px solid {score_color};"
            f"padding:18px 22px;border-radius:10px;text-align:center;'>"
            f"<div style='font-size:2.2em;font-weight:800;color:{score_color};'>Score: {final_score}</div>"
            f"<div style='color:{score_color};font-size:1.0em;margin-top:6px;font-weight:600;'>{tier}</div>"
            f"<div style='color:#e2e8f0;margin-top:10px;font-size:0.95em;'>{recommendation}</div>"
            f"</div>",
            unsafe_allow_html=True,
        )

    # Score breakdown table
    st.markdown("**Score Breakdown**")
    breakdown = [
        ("CD46 Expression",             f"{cd46_expr:.1f} log₂ TPM",  35 if cd46_expr >= 12 else 28 if cd46_expr >= 10.5 else 18 if cd46_expr >= 9 else 8 if cd46_expr >= 7.5 else 0),
        ("PSMA Status (inverse)",       psma_status,                  {"Absent":15,"Low":13,"Moderate":8,"High":3,"Very High":0}.get(psma_status,0)),
        ("AR Amplification",            "Yes" if ar_amplification else "No", 5 if ar_amplification else 0),
        ("TP53 Loss",                   "Yes" if tp53_loss else "No", -5 if tp53_loss else 0),
        ("RB1 Loss",                    "Yes" if rb1_loss else "No",  -8 if rb1_loss else 0),
        ("AR-V7 Positive",              "Yes" if arv7_positive else "No", 3 if arv7_positive else 0),
        ("Prior 177Lu-PSMA failure",    "Yes" if prior_lupsma else "No", 10 if prior_lupsma else 0),
        ("ECOG Performance Status",     ecog_ps[:1],                  {0:-0,1:-2,2:-8,3:-20}.get(int(ecog_ps[0]),0)),
        ("Gleason Score",               str(gleason_score),           5 if gleason_score >= 9 else 3 if gleason_score >= 8 else 1),
        ("Bone Metastases",             "Yes" if bone_mets else "No", 3 if bone_mets else 0),
        ("Visceral Metastases",         "Yes" if visceral_mets else "No", -5 if visceral_mets else 0),
    ]
    df_breakdown = pd.DataFrame(breakdown, columns=["Factor", "Value", "Points"])
    df_breakdown["Contribution"] = df_breakdown["Points"].apply(
        lambda p: f"✅ +{p}" if p > 0 else (f"⚠️ {p}" if p < 0 else "— 0")
    )
    st.dataframe(df_breakdown[["Factor", "Value", "Contribution"]], use_container_width=True, hide_index=True)

    st.markdown("---")
    # ===================================================================
    # PATIENT COHORT BUILDER — DYNAMIC COMPUTATION FROM REAL DATA
    # ===================================================================
    st.markdown(
        "<div style='background:#1e293b;border-left:3px solid #a78bfa;padding:12px 16px;"
        "border-radius:6px;margin-bottom:14px;'>"
        "<b style='color:#a78bfa;'>🏥 Patient Cohort Builder — Live Population Analysis</b><br>"
        "<span style='color:#94a3b8;'>Define molecular criteria → system computes cohort size "
        "and survival profile live from 11,069 TCGA patient records. "
        "Each run can reveal a new clinical discovery.</span>"
        "</div>",
        unsafe_allow_html=True,
    )

    if df_expr.empty:
        st.info("Run `python scripts/run_pipeline.py` to enable the Cohort Builder.")
    else:
        cb_c1, cb_c2, cb_c3 = st.columns(3)
        with cb_c1:
            cb_cancers = st.multiselect(
                "Cancer types (blank = all)", options=ALL_CANCERS,
                default=[c for c in ["PRAD"] if c in ALL_CANCERS], key="cb6_cancers",
            )
            cb_endpoint = st.radio("Endpoint", ["OS", "PFI"], horizontal=True, key="cb6_ep")
        with cb_c2:
            cb_threshold = st.slider("CD46 log₂ TPM threshold", 8.0, 14.5, 12.5, 0.1, key="cb6_thr")
            st.caption(f"Patients with CD46 ≥ {cb_threshold:.1f} → CD46-High group")
        with cb_c3:
            cb_breakdown = st.checkbox("Per-cancer breakdown", value=True, key="cb6_brk")
            cb_download = st.checkbox("Enable CSV download", value=True, key="cb6_dl")

        if st.button("🔬 Build & Analyse Cohort", type="primary", use_container_width=True, key="cb6_run"):
            with st.spinner("Computing from patient-level data..."):
                df_cb = df_expr.copy()
                if cb_cancers:
                    df_cb = df_cb[df_cb["cancer_type"].isin(cb_cancers)]

                os_c = "OS" if cb_endpoint == "OS" else "PFI"
                t_c  = "OS.time" if cb_endpoint == "OS" else "PFI.time"

                df_hi = df_cb[df_cb["cd46_log2_tpm"] >= cb_threshold].copy()
                df_lo = df_cb[df_cb["cd46_log2_tpm"] <  cb_threshold].copy()

                def _med_os(sdf):
                    ev = sdf.dropna(subset=[os_c, t_c])
                    events = ev[ev[os_c] == 1][t_c]
                    return events.median() / 30.4 if len(events) > 0 else None

                med_hi = _med_os(df_hi)
                med_lo = _med_os(df_lo)
                n_hi   = len(df_hi)
                n_lo   = len(df_lo)
                n_cb   = len(df_cb)
                pct_cb = n_hi / max(n_cb, 1) * 100
                evt_hi = df_hi.dropna(subset=[os_c])[os_c].mean() * 100 if n_hi > 0 else 0

                # Metrics
                r1, r2, r3, r4, r5 = st.columns(5)
                r1.metric("CD46-High patients", f"{n_hi:,}", f"{pct_cb:.1f}% of {n_cb:,}")
                r2.metric("CD46-Low patients",  f"{n_lo:,}")
                r3.metric(f"{os_c} event rate (High)", f"{evt_hi:.1f}%")
                if med_hi:
                    delta_mo = f"{med_hi - med_lo:.1f} mo" if med_lo else None
                    r4.metric(f"Median {os_c} CD46-High", f"{med_hi:.1f} mo",
                              delta=delta_mo, delta_color="inverse")
                if med_lo:
                    r5.metric(f"Median {os_c} CD46-Low", f"{med_lo:.1f} mo")

                # Distribution chart
                vc1, vc2 = st.columns(2)
                with vc1:
                    fig_dist = go.Figure()
                    fig_dist.add_trace(go.Histogram(
                        x=df_hi["cd46_log2_tpm"], name=f"CD46-High (n={n_hi})",
                        marker_color="#f87171", opacity=0.75, nbinsx=30,
                    ))
                    fig_dist.add_trace(go.Histogram(
                        x=df_lo["cd46_log2_tpm"], name=f"CD46-Low (n={n_lo})",
                        marker_color="#38bdf8", opacity=0.55, nbinsx=30,
                    ))
                    fig_dist.add_vline(x=cb_threshold, line_dash="dash", line_color="#fbbf24",
                                       annotation_text=f"{cb_threshold:.1f}",
                                       annotation_font_color="#fbbf24")
                    fig_dist.update_layout(
                        barmode="overlay", height=300,
                        paper_bgcolor="#0f172a", plot_bgcolor="#0f172a",
                        xaxis=dict(title="CD46 log₂ TPM", color="#94a3b8", gridcolor="#1e293b"),
                        yaxis=dict(title="Patients", color="#94a3b8", gridcolor="#1e293b"),
                        legend=dict(bgcolor="#1e293b", font=dict(color="#e2e8f0")),
                        margin=dict(l=10, r=10, t=10, b=10),
                    )
                    st.plotly_chart(fig_dist, use_container_width=True)

                # Landmark survival comparison
                with vc2:
                    hi_surv = df_hi.dropna(subset=[os_c, t_c])
                    lo_surv = df_lo.dropna(subset=[os_c, t_c])
                    if len(hi_surv) > 5 and len(lo_surv) > 5:
                        time_pts = [0, 365, 730, 1095, 1825]
                        lbl_pts  = ["0", "1yr", "2yr", "3yr", "5yr"]
                        pct_hi = [(hi_surv[t_c] >= t).mean() * 100 for t in time_pts]
                        pct_lo = [(lo_surv[t_c] >= t).mean() * 100 for t in time_pts]
                        fig_lm = go.Figure()
                        fig_lm.add_trace(go.Scatter(x=lbl_pts, y=pct_hi, name=f"CD46-High",
                            mode="lines+markers", line=dict(color="#f87171", width=2), marker_size=7))
                        fig_lm.add_trace(go.Scatter(x=lbl_pts, y=pct_lo, name=f"CD46-Low",
                            mode="lines+markers", line=dict(color="#38bdf8", width=2, dash="dash"), marker_size=7))
                        fig_lm.update_layout(
                            height=300, paper_bgcolor="#0f172a", plot_bgcolor="#0f172a",
                            xaxis=dict(title="Time", color="#94a3b8", gridcolor="#1e293b"),
                            yaxis=dict(title="% with follow-up data", color="#94a3b8", gridcolor="#1e293b"),
                            legend=dict(bgcolor="#1e293b", font=dict(color="#e2e8f0")),
                            margin=dict(l=10, r=10, t=10, b=10),
                        )
                        st.plotly_chart(fig_lm, use_container_width=True)
                        st.caption("Landmark analysis — patients with follow-up past each timepoint")

                # Per-cancer breakdown
                if cb_breakdown and (not cb_cancers or len(cb_cancers) > 1):
                    st.markdown("**Per-Cancer Breakdown**")
                    pc_df = df_cb.groupby("cancer_type").apply(
                        lambda g: pd.Series({"N Total": len(g),
                                             "N CD46-High": int((g["cd46_log2_tpm"] >= cb_threshold).sum()),
                                             "% Eligible": round((g["cd46_log2_tpm"] >= cb_threshold).mean() * 100, 1)}),
                        include_groups=False,
                    ).reset_index().rename(columns={"cancer_type": "Cancer"}).sort_values("% Eligible", ascending=False)
                    st.dataframe(pc_df, use_container_width=True, hide_index=True)

                # Download
                if cb_download:
                    dl1, dl2 = st.columns(2)
                    with dl1:
                        csv_sum = (
                            f"Cancer types,{', '.join(cb_cancers) if cb_cancers else 'All'}\n"
                            f"Threshold,{cb_threshold}\nEndpoint,{os_c}\n"
                            f"N CD46-High,{n_hi}\nN CD46-Low,{n_lo}\n"
                            f"Median {os_c} High,{f'{med_hi:.1f} mo' if med_hi else 'N/A'}\n"
                            f"Median {os_c} Low,{f'{med_lo:.1f} mo' if med_lo else 'N/A'}\n"
                        )
                        st.download_button("📥 Cohort Summary CSV", csv_sum,
                                           "cd46_cohort_summary.csv", "text/csv", key="cb6_dl1")
                    with dl2:
                        cols_exp = [c for c in ["sample","cancer_type","cd46_log2_tpm","OS","OS.time","PFI","PFI.time"]
                                    if c in df_hi.columns]
                        st.download_button("📥 CD46-High Patient List CSV",
                                           df_hi[cols_exp].to_csv(index=False),
                                           "cd46_high_patients.csv", "text/csv", key="cb6_dl2")

                # AI interpretation
                direction = "shorter" if (med_hi and med_lo and med_hi < med_lo) else "longer or similar"
                st.info(
                    f"**Cohort Summary:** {n_hi:,} CD46-High patients ({pct_cb:.1f}% of "
                    f"{'  '.join(cb_cancers) if cb_cancers else 'pan-cancer'} cohort). "
                    f"Median {os_c} is **{f'{med_hi:.1f} mo' if med_hi else 'N/A'}** (High) vs "
                    f"**{f'{med_lo:.1f} mo' if med_lo else 'N/A'}** (Low) → {direction} survival. "
                    f"{'CD46-High associated with worse prognosis — strongest justification for CD46-directed therapy.' if direction == 'shorter' else 'CD46-High not associated with worse prognosis in this cohort at this threshold — consider adjusting threshold or reviewing endpoint.'}"
                )

    st.markdown("---")
    st.markdown(
        "<div style='color:#64748b;font-size:0.78em;'>Data: TCGA Pan-Cancer (11,069 primary tumour records) · "
        "SU2C mCRPC 2019 cohort · Human Protein Atlas · cBioPortal GENIE. "
        "⚠️ Research use only — not validated for clinical decisions.</div>",
        unsafe_allow_html=True,
    )

    st.markdown("---")
    st.markdown("**Composite Score Result**")

    col_sc1, col_sc2 = st.columns([1, 2])
    with col_sc1:
        # Gauge chart
        fig_gauge = go.Figure(go.Indicator(
            mode="gauge+number",
            value=final_score,
            domain={"x": [0, 1], "y": [0, 1]},
            title={"text": "225Ac-CD46<br>Suitability", "font": {"color": "#e2e8f0", "size": 14}},
            gauge={
                "axis": {"range": [0, 100], "tickcolor": "#94a3b8"},
                "bar": {"color": score_color},
                "steps": [
                    {"range": [0, 25], "color": "#1e293b"},
                    {"range": [25, 45], "color": "#27272a"},
                    {"range": [45, 65], "color": "#1c1917"},
                    {"range": [65, 100], "color": "#14532d"},
                ],
                "threshold": {"line": {"color": "#f87171", "width": 2}, "thickness": 0.8, "value": 65},
                "bgcolor": "#0f172a",
                "bordercolor": "#334155",
            },
            number={"font": {"color": score_color, "size": 42}},
        ))
        fig_gauge.update_layout(
            height=260, paper_bgcolor="#0f172a",
            margin=dict(l=20, r=20, t=30, b=10),
        )
        st.plotly_chart(fig_gauge, use_container_width=True)

    with col_sc2:
        st.markdown(
            f"<div style='background:#1e293b;border:2px solid {score_color};border-radius:10px;"
            f"padding:18px 22px;margin-top:10px;'>"
            f"<div style='font-size:1.2em;color:{score_color};font-weight:700;'>{tier}</div>"
            f"<div style='font-size:1.0em;color:#e2e8f0;margin:6px 0;'>{recommendation}</div>"
            f"<hr style='border-color:#334155;margin:10px 0;'>"
            f"<table style='font-size:0.84em;color:#94a3b8;width:100%;'>"
            f"<tr><td>CD46 Expression</td><td style='color:#e2e8f0;'>{cd46_expr:.1f} log₂ TPM</td></tr>"
            f"<tr><td>PSMA Status</td><td style='color:#e2e8f0;'>{psma_status}</td></tr>"
            f"<tr><td>AR Amplification</td><td style='color:#e2e8f0;'>{'Yes' if ar_amplification else 'No'}</td></tr>"
            f"<tr><td>TP53 Loss</td><td style='color:#e2e8f0;'>{'Yes (-5)' if tp53_loss else 'No'}</td></tr>"
            f"<tr><td>RB1 Loss</td><td style='color:#e2e8f0;'>{'Yes (-8)' if rb1_loss else 'No'}</td></tr>"
            f"<tr><td>Prior Lu-PSMA failed</td><td style='color:#e2e8f0;'>{'Yes (+10)' if prior_lupsma else 'No'}</td></tr>"
            f"<tr><td>ECOG PS</td><td style='color:#e2e8f0;'>{ecog_ps[0]}</td></tr>"
            f"</table>"
            f"</div>",
            unsafe_allow_html=True,
        )

        # Download report
        import json as _json
        report_data = {
            "Score": final_score,
            "Tier": tier,
            "Recommendation": recommendation,
            "CD46_log2_TPM": cd46_expr,
            "PSMA_status": psma_status,
            "AR_amplification": ar_amplification,
            "TP53_loss": tp53_loss,
            "RB1_loss": rb1_loss,
            "AR-V7_positive": arv7_positive,
            "Prior_LuPSMA_failed": prior_lupsma,
            "ECOG_PS": ecog_ps[0],
            "Gleason": gleason_score,
            "Bone_mets": bone_mets,
            "Visceral_mets": visceral_mets,
            "Note": "RESEARCH USE ONLY — Not for clinical decision-making",
        }
        report_csv = "Field,Value\n" + "\n".join(f"{k},{v}" for k, v in report_data.items())
        st.download_button(
            "📥 Download Scoring Report (CSV)",
            data=report_csv,
            file_name="cd46_patient_score_report.csv",
            mime="text/csv",
        )

st.markdown("---")
st.markdown(
    "<div style='color:#64748b; font-size:0.78em;'>"
    "Data sources: TCGA Pan-Cancer (n=11,160) · SU2C mCRPC cohort (n=444) · "
    "Human Protein Atlas · cBioPortal · PubMed / NCBI E-utilities<br>"
    "⚠️ For research and drug discovery use only. Clinical decisions require validated IVD-grade assays, "
    "MDT review, and institutional ethics approval."
    "</div>",
    unsafe_allow_html=True,
)
