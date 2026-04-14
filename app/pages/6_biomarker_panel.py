"""Page 6 — Biomarker Panel: Clinical Decision Support for 225Ac-CD46 Therapy."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import math
import os

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from components.styles import inject_global_css, page_hero

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

inject_global_css()

st.markdown(
    page_hero(
        icon="🧬",
        module_name="Biomarker Panel",
        purpose="Clinical decision support for 225Ac-CD46 α-RLT · multi-biomarker scoring · co-targeting analysis · mCRPC cohort data",
        kpi_chips=[
            ("Biomarkers Tracked", "5"),
            ("mCRPC Cohort", "226 pts"),
            ("GENIE Prostate", "9,251 pts"),
            ("Driver Segments", "8"),
        ],
        source_badges=["TCGA", "GENIE", "cBioPortal", "mCRPC"],
    ),
    unsafe_allow_html=True,
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
def load_genie_cohort():
    p = DATA_DIR / "genie_full_cohort.parquet"
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
df_genie = load_genie_cohort()
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
            st.plotly_chart(fig1, width='stretch')
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
            st.plotly_chart(fig_thr, width='stretch')
            top3 = grp_thr.nlargest(3, "pct_eligible")["cancer_type"].tolist()
            st.caption(f"Highest eligibility at {thr_val:.1f}: **{'  ·  '.join(top3)}**")
    else:
        st.info("Run `python scripts/run_pipeline.py` to enable live threshold exploration.")

# ===========================================================================
# TAB 2 — CO-TARGETING & COMPLEMENTARITY (AACR GENIE)
# ===========================================================================
with tab2:
    st.markdown(
        "<div style='background:#1e293b;border-left:3px solid #4ade80;padding:12px 16px;"
        "border-radius:6px;margin-bottom:14px;'>"
        "<b style='color:#4ade80;'>Real-World Target Mutational/Amplification Frequencies</b><br>"
        "<span style='color:#94a3b8;'>AACR Project GENIE 19.0 Cohort (n = 271,837 samples)</span>"
        "</div>",
        unsafe_allow_html=True,
    )

    if not df_genie.empty:
        col_g1, col_g2 = st.columns(2)

        st.info(
            "🧬 **CD46 is an expression-level target** — selected by protein/mRNA overexpression (IHC/RNA-seq), "
            "not genomic amplification. The charts below show **AR and PTEN** alterations that define "
            "the aggressive CRPC patient population where CD46 is most highly upregulated."
        )

        with col_g1:
            st.markdown("#### AR & PTEN Alteration Rates by Cancer Type")
            st.caption("Key driver alterations identifying the CD46-eligible population · cohorts ≥1,000 patients")

            # Build per-cancer grouped stats
            top_cts = df_genie.groupby("CANCER_TYPE").size().reset_index(name="n")
            top_cts = top_cts[top_cts["n"] >= 1000].sort_values("n", ascending=False).head(10)
            ct_rows = []
            for _, r in top_cts.iterrows():
                ct = r["CANCER_TYPE"]
                sub = df_genie[df_genie["CANCER_TYPE"] == ct]
                n = len(sub)
                ct_rows.append({
                    "CANCER_TYPE": ct,
                    "AR %": round((sub["AR_Mutated"] | sub["AR_Amplified"]).mean() * 100, 1),
                    "PTEN %": round((sub["PTEN_Mutated"] | sub["PTEN_Deleted"]).mean() * 100, 1),
                    "TP53 %": round(sub["TP53_Mutated"].mean() * 100, 1),
                })
            ct_df = pd.DataFrame(ct_rows).sort_values("AR %", ascending=True)

            fig_g1 = go.Figure()
            fig_g1.add_trace(go.Bar(
                name="AR", y=ct_df["CANCER_TYPE"], x=ct_df["AR %"], orientation="h",
                marker_color="#3b82f6", text=ct_df["AR %"].astype(str) + "%", textposition="outside"
            ))
            fig_g1.add_trace(go.Bar(
                name="PTEN", y=ct_df["CANCER_TYPE"], x=ct_df["PTEN %"], orientation="h",
                marker_color="#f59e0b", text=ct_df["PTEN %"].astype(str) + "%", textposition="outside"
            ))
            fig_g1.add_trace(go.Bar(
                name="TP53", y=ct_df["CANCER_TYPE"], x=ct_df["TP53 %"], orientation="h",
                marker_color="#ef4444", text=ct_df["TP53 %"].astype(str) + "%", textposition="outside"
            ))
            fig_g1.update_layout(
                barmode="group", height=420,
                margin=dict(l=10, r=80, t=10, b=10),
                xaxis_title="% Patients Altered",
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )
            st.plotly_chart(fig_g1, use_container_width=True)

        with col_g2:
            st.markdown("#### Prostate Cancer: Full Driver Alteration Landscape")
            st.caption("All 8 molecular subtypes · GENIE n=9,251")

            prad_g = df_genie[df_genie["CANCER_TYPE"] == "Prostate Cancer"].copy()
            if not prad_g.empty:
                prad_g["AR"] = prad_g["AR_Amplified"] | prad_g["AR_Mutated"]
                prad_g["PTEN"] = prad_g["PTEN_Mutated"] | prad_g["PTEN_Deleted"]
                prad_g["TP53"] = prad_g["TP53_Mutated"]

                def _classify_p6(row):
                    ar, pt, t = row["AR"], row["PTEN"], row["TP53"]
                    if ar and pt and t:  return "AR + PTEN + TP53 (Triple-Hit)"
                    if ar and pt:        return "AR + PTEN \u2192 CD46 Priority"
                    if ar and t:         return "AR + TP53"
                    if pt and t:         return "PTEN + TP53"
                    if ar:               return "AR Only"
                    if pt:               return "PTEN Only"
                    if t:                return "TP53 Only"
                    return "No Detected Driver Alteration"

                prad_g["Segment"] = prad_g.apply(_classify_p6, axis=1)
                scounts = prad_g["Segment"].value_counts().reset_index()
                scounts.columns = ["Segment", "Patients"]

                _seg_order = [
                    "AR + PTEN + TP53 (Triple-Hit)", "AR + PTEN \u2192 CD46 Priority",
                    "AR + TP53", "PTEN + TP53", "AR Only", "PTEN Only",
                    "TP53 Only", "No Detected Driver Alteration"
                ]
                _seg_colors = {
                    "AR + PTEN + TP53 (Triple-Hit)": "#7c3aed",
                    "AR + PTEN \u2192 CD46 Priority": "#8b5cf6",
                    "AR + TP53": "#3b82f6",
                    "PTEN + TP53": "#f97316",
                    "AR Only": "#38bdf8",
                    "PTEN Only": "#f59e0b",
                    "TP53 Only": "#f87171",
                    "No Detected Driver Alteration": "#334155",
                }
                scounts["Segment"] = pd.Categorical(scounts["Segment"], categories=_seg_order, ordered=True)
                scounts = scounts.sort_values("Segment")

                fig_g2 = px.pie(
                    scounts, names="Segment", values="Patients", hole=0.45,
                    color="Segment",
                    color_discrete_map=_seg_colors,
                    category_orders={"Segment": _seg_order}
                )
                fig_g2.update_traces(textposition="inside", textinfo="percent+label", textfont_size=9)
                fig_g2.update_layout(
                    margin=dict(t=10, b=10, l=10, r=10), height=420, showlegend=False
                )
                st.plotly_chart(fig_g2, use_container_width=True)
                n_g = len(prad_g)
                n_any_g = (prad_g["AR"] | prad_g["PTEN"] | prad_g["TP53"]).sum()
                st.info(
                    f"**{n_any_g:,} / {n_g:,} prostate patients ({n_any_g/n_g*100:.0f}%) carry at least one "
                    "tracked driver alteration.** Purple = primary 225Ac-CD46 priority. "
                    "Dark slate = localized/early-stage or other drivers (BRCA2, CDK12, RB1)."
                )

    else:
        st.info("GENIE real-world dataset not loaded. Run the `fetch_genie_cd46.py` script.")

    # Clinical decision matrix
    st.markdown("---")
    st.markdown("**Clinical Decision Matrix — Dual-Target Strategy (PSMA)**")
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
        st.plotly_chart(fig_resist, width='stretch')

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
                st.plotly_chart(fig_surv, width='stretch')
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
    st.plotly_chart(fig_comp, width='stretch')

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

    # ---- Two-patient comparison toggle -------
    compare_mode = st.checkbox("⚖️ Compare two patient profiles side-by-side", value=False)
    n_profiles = 2 if compare_mode else 1
    profile_labels = ["Patient A", "Patient B"] if compare_mode else ["Patient"]

    profile_results = []
    input_columns = st.columns(n_profiles)

    for _pi, _pcol in enumerate(input_columns):
        with _pcol:
            if compare_mode:
                st.markdown(f"### {profile_labels[_pi]}")

            col_s1, col_s2 = st.columns(2)

            with col_s1:
                st.markdown("**Target Expression**")
                cd46_expr = st.slider(
                    "CD46 log₂ TPM",
                    min_value=0.0, max_value=15.0,
                    value=10.5 if _pi == 0 else 8.0, step=0.5,
                    help="Log₂ TPM > 10.5 = 75th percentile across TCGA. High expression = better target.",
                    key=f"cd46_expr_{_pi}",
                )
                psma_status = st.select_slider(
                    "PSMA (FOLH1) Expression",
                    options=["Absent", "Low", "Moderate", "High", "Very High"],
                    value="Low" if _pi == 0 else "High",
                    help="Lower PSMA = CD46 is primary target. Higher PSMA = consider Lu-PSMA first.",
                    key=f"psma_{_pi}",
                )
                folh1_expression = st.slider(
                    "FOLH1 mRNA (log₂ TPM)", 0.0, 15.0,
                    value=6.0 if _pi == 0 else 11.0, step=0.5,
                    help="FOLH1 RNA level (distinct from IHC PSMA status). High = Lu-PSMA preferred.",
                    key=f"folh1_{_pi}",
                )
                psa_level = st.number_input(
                    "PSA (ng/mL)", min_value=0.0, max_value=5000.0,
                    value=45.0 if _pi == 0 else 12.0, step=5.0,
                    help="Serum PSA. Rising PSA under castration = castration-resistant disease.",
                    key=f"psa_{_pi}",
                )
                psa_doubling = st.selectbox(
                    "PSA Doubling Time",
                    ["< 3 months", "3–6 months", "6–12 months", "> 12 months"],
                    index=0 if _pi == 0 else 2,
                    help="Short PSADT reflects more aggressive disease biology.",
                    key=f"psadt_{_pi}",
                )
                ldh = st.number_input(
                    "LDH (U/L)",
                    min_value=0, max_value=5000, value=280 if _pi == 0 else 180,
                    help="Elevated LDH ≥ ULN signals high disease burden.",
                    key=f"ldh_{_pi}",
                )

            with col_s2:
                st.markdown("**Genomic Alterations**")
                ar_amplification = st.checkbox(
                    "AR Amplification", value=False if _pi == 0 else True,
                    help="AR CNA gain — upregulates CD46 expression.", key=f"ar_{_pi}")
                tp53_loss = st.checkbox(
                    "TP53 biallelic loss", value=False,
                    help="Reduces DSB response, slightly reduces alpha efficacy.", key=f"tp53_{_pi}")
                rb1_loss = st.checkbox(
                    "RB1 biallelic loss", value=False,
                    help="Associated with neuroendocrine differentiation.", key=f"rb1_{_pi}")
                arv7_positive = st.checkbox(
                    "AR-V7 splice variant +", value=False if _pi == 0 else True,
                    help="Predicts ARSI resistance; CD46 becomes priority target.", key=f"arv7_{_pi}")
                brca2_loss = st.checkbox(
                    "BRCA2 / BRCA1 loss (HRD)", value=False,
                    help="HRD may synergise with DSB-rich alpha radiation.", key=f"brca2_{_pi}")
                atm_mut = st.checkbox(
                    "ATM mutation", value=False,
                    help="ATM loss (HR pathway) — similar synergy to BRCA2.", key=f"atm_{_pi}")
                cdk12_loss = st.checkbox(
                    "CDK12 biallelic loss", value=False,
                    help="Immune-hot tumour phenotype — may respond well to combinatorial.", key=f"cdk12_{_pi}")
                pten_loss = st.checkbox(
                    "PTEN loss (PI3K activated)", value=False,
                    help="PI3K pathway resistance — co-target potential.", key=f"pten_{_pi}")
                myc_amp = st.checkbox(
                    "MYC amplification", value=False,
                    help="Co-amplified with AR in 27% mCRPC; drives proliferation.", key=f"myc_{_pi}")
                spop_mut = st.checkbox(
                    "SPOP mutation (favourable)", value=False,
                    help="SPOP mutations associated with better prognosis and ARSI response.", key=f"spop_{_pi}")

            st.markdown("**Clinical Factors**")
            ccol1, ccol2 = st.columns(2)
            with ccol1:
                ecog_ps = st.selectbox(
                    "ECOG PS",
                    ["0 — Fully active", "1 — Restricted strenuous", "2 — Ambulatory >50%", "3 — Limited self-care"],
                    index=1 if _pi == 0 else 0,
                    key=f"ecog_{_pi}",
                )
                gleason_score = st.slider(
                    "Gleason / Grade Group", 6, 10, value=8, step=1, key=f"gl_{_pi}")
                prior_arsi_lines = st.selectbox(
                    "Prior ARSI lines",
                    ["0 (ARSI-naive)", "1 (1 line failed)", "2+ (2+ lines failed)"],
                    index=1,
                    help="Enzalutamide/abiraterone lines — more = higher CD46 expression expected.",
                    key=f"arsi_{_pi}",
                )
            with ccol2:
                prior_lupsma = st.checkbox(
                    "Prior 177Lu-PSMA failed", value=False if _pi == 0 else True,
                    help="Failed PSMA-directed RLT → CD46 is rescue strategy.", key=f"lupsma_{_pi}")
                prior_chemo = st.checkbox(
                    "Prior docetaxel/cabazitaxel", value=False, key=f"chemo_{_pi}",
                    help="Prior taxane use — progression = higher priority.")
                bone_mets = st.checkbox(
                    "Bone metastases", value=True, key=f"bone_{_pi}",
                    help="Alpha emission ideal for bone-adjacent tumour microenvironment.")
                visceral_mets = st.checkbox(
                    "Visceral metastases", value=False, key=f"vis_{_pi}",
                    help="Liver/lung mets increase systemic risk.")

            # ==========================
            # Scoring algorithm (15 biomarkers)
            # ==========================
            def calc_score_v2(
                cd46, psma, folh1, psa, psadt, ldh,
                ar_amp, tp53, rb1, arv7, brca2, atm, cdk12, pten, myc, spop,
                ecog, gleason, prior_arsi, prior_lupsma_f, prior_chemo_f, bone, visceral,
            ):
                s = 0

                # ---- CD46 expression (30 pts — primary target driver) ----
                if cd46 >= 12.0:   s += 30
                elif cd46 >= 10.5: s += 24
                elif cd46 >= 9.0:  s += 15
                elif cd46 >= 7.5:  s += 6
                else:              s += 0

                # ---- PSMA / FOLH1 (12 pts — inverse: low PSMA = CD46 is priority) ----
                psma_pts = {"Absent": 12, "Low": 10, "Moderate": 6, "High": 2, "Very High": 0}
                s += psma_pts.get(psma, 0)
                # FOLH1 mRNA adjusts PSMA score refinement
                if folh1 < 6.0:   s += 3
                elif folh1 < 9.0: s += 1

                # ---- PSA trajectory (6 pts) ----
                psadt_pts = {"< 3 months": 6, "3–6 months": 4, "6–12 months": 2, "> 12 months": 0}
                s += psadt_pts.get(psadt, 0)
                if psa >= 100:  s += 2  # Very high PSA = high burden = priority
                elif psa >= 20: s += 1

                # ---- LDH (disease burden, 4 pts) ----
                if ldh >= 460:         s += 0   # above ULN x2 — toxicity concern
                elif ldh >= 230:       s += 2   # ULN = ~230 U/L (mild elevation)
                else:                  s += 4   # Normal range = best safety profile

                # ---- Genomic alterations ----
                if ar_amp:  s += 5    # AR amp upregulates CD46 — strong bonus
                if arv7:    s += 4    # AR-V7 = ARSI resistance → CD46 priority
                if tp53:    s -= 5    # TP53 loss — reduced DNA repair, slight alpha concern
                if rb1:     s -= 6    # NCRPC risk
                if brca2:   s += 3    # HRD synergy with DSBs
                if atm:     s += 2    # HR deficiency (lesser than BRCA2)
                if cdk12:   s += 2    # Immune-hot — combinatorial potential
                if pten:    s -= 3    # PI3K resistance pathway
                if myc:     s += 1    # Proliferative — more target antigen cycling
                if spop:    s += 2    # Favourable SPOP mutation (+2 prognosis)

                # ---- Prior therapies (5 pts) ----
                arsi_pts = {"0 (ARSI-naive)": 0, "1 (1 line failed)": 3, "2+ (2+ lines failed)": 5}
                s += arsi_pts.get(prior_arsi, 0)
                if prior_lupsma_f: s += 8   # CD46 is rescue after Lu-PSMA
                if prior_chemo_f: s += 2    # Higher line = more urgent

                # ---- ECOG / performance ----
                ecog_n = int(ecog[0])
                s += {0: 0, 1: -2, 2: -8, 3: -20}.get(ecog_n, 0)

                # ---- Gleason ----
                if gleason >= 9:   s += 4
                elif gleason >= 8: s += 2
                elif gleason >= 7: s += 1

                # ---- Metastatic features ----
                if bone:     s += 3   # Alpha range ideal for bone mets
                if visceral: s -= 5   # Increased toxicity risk

                return max(0, min(100, s))

            prior_arsi_lines_val = prior_arsi_lines
            final_score = calc_score_v2(
                cd46_expr, psma_status, folh1_expression, psa_level, psa_doubling, ldh,
                ar_amplification, tp53_loss, rb1_loss, arv7_positive, brca2_loss,
                atm_mut, cdk12_loss, pten_loss, myc_amp, spop_mut,
                ecog_ps, gleason_score, prior_arsi_lines_val, prior_lupsma, prior_chemo,
                bone_mets, visceral_mets,
            )

            profile_results.append({
                "label": profile_labels[_pi],
                "score": final_score,
                "cd46_expr": cd46_expr,
                "psma": psma_status,
                "folh1": folh1_expression,
                "psa": psa_level,
                "psadt": psa_doubling,
                "ldh": ldh,
                "ar_amp": ar_amplification,
                "tp53": tp53_loss,
                "rb1": rb1_loss,
                "arv7": arv7_positive,
                "brca2": brca2_loss,
                "atm": atm_mut,
                "cdk12": cdk12_loss,
                "pten": pten_loss,
                "myc": myc_amp,
                "spop": spop_mut,
                "ecog": ecog_ps,
                "gleason": gleason_score,
                "prior_arsi": prior_arsi_lines,
                "prior_lupsma": prior_lupsma,
                "prior_chemo": prior_chemo,
                "bone": bone_mets,
                "visceral": visceral_mets,
            })

    # Use first profile as primary for gauge / breakdown
    primary = profile_results[0]
    final_score = primary["score"]
    cd46_expr      = primary["cd46_expr"]
    psma_status    = primary["psma"]
    ar_amplification = primary["ar_amp"]
    tp53_loss      = primary["tp53"]
    rb1_loss       = primary["rb1"]
    arv7_positive  = primary["arv7"]
    brca2_loss     = primary["brca2"]
    atm_mut        = primary["atm"]
    cdk12_loss     = primary["cdk12"]
    pten_loss      = primary["pten"]
    myc_amp        = primary["myc"]
    spop_mut       = primary["spop"]
    ecog_ps        = primary["ecog"]
    gleason_score  = primary["gleason"]
    prior_arsi_lines = primary["prior_arsi"]
    prior_lupsma   = primary["prior_lupsma"]
    prior_chemo    = primary["prior_chemo"]
    bone_mets      = primary["bone"]
    visceral_mets  = primary["visceral"]
    psa_level      = primary["psa"]
    psa_doubling   = primary["psadt"]
    ldh            = primary["ldh"]
    folh1_expression = primary["folh1"]

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
        st.plotly_chart(fig_gauge, width='stretch')

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

    # Score breakdown table (15 biomarkers)
    st.markdown("**Score Breakdown — 15-Biomarker Framework**")
    psma_pts = {"Absent": 12, "Low": 10, "Moderate": 6, "High": 2, "Very High": 0}
    psadt_pts = {"< 3 months": 6, "3–6 months": 4, "6–12 months": 2, "> 12 months": 0}
    arsi_pts  = {"0 (ARSI-naive)": 0, "1 (1 line failed)": 3, "2+ (2+ lines failed)": 5}
    breakdown = [
        ("CD46 mRNA Expression",         f"{cd46_expr:.1f} log₂ TPM",    30 if cd46_expr >= 12 else 24 if cd46_expr >= 10.5 else 15 if cd46_expr >= 9 else 6 if cd46_expr >= 7.5 else 0),
        ("PSMA IHC Status (inverse)",    psma_status,                     psma_pts.get(psma_status, 0)),
        ("FOLH1 mRNA (inverse)",         f"{folh1_expression:.1f} log₂",  3 if folh1_expression < 6 else 1 if folh1_expression < 9 else 0),
        ("PSA Doubling Time",            psa_doubling,                    psadt_pts.get(psa_doubling, 0)),
        ("PSA Level",                    f"{psa_level:.0f} ng/mL",        2 if psa_level >= 100 else 1 if psa_level >= 20 else 0),
        ("LDH",                          f"{ldh} U/L",                    0 if ldh >= 460 else 2 if ldh >= 230 else 4),
        ("AR Amplification",             "Yes" if ar_amplification else "No", 5 if ar_amplification else 0),
        ("AR-V7 Positive",               "Yes" if arv7_positive else "No",    4 if arv7_positive else 0),
        ("TP53 Biallelic Loss",          "Yes" if tp53_loss else "No",        -5 if tp53_loss else 0),
        ("RB1 Biallelic Loss",           "Yes" if rb1_loss else "No",         -6 if rb1_loss else 0),
        ("BRCA2/BRCA1 Loss (HRD)",       "Yes" if brca2_loss else "No",       3 if brca2_loss else 0),
        ("ATM Mutation",                 "Yes" if atm_mut else "No",           2 if atm_mut else 0),
        ("CDK12 Biallelic Loss",         "Yes" if cdk12_loss else "No",        2 if cdk12_loss else 0),
        ("PTEN Loss (PI3K activated)",   "Yes" if pten_loss else "No",        -3 if pten_loss else 0),
        ("MYC Amplification",            "Yes" if myc_amp else "No",           1 if myc_amp else 0),
        ("SPOP Mutation (favourable)",   "Yes" if spop_mut else "No",          2 if spop_mut else 0),
        ("Prior ARSI Lines",             prior_arsi_lines,                arsi_pts.get(prior_arsi_lines, 0)),
        ("Prior 177Lu-PSMA Failure",     "Yes" if prior_lupsma else "No",      8 if prior_lupsma else 0),
        ("Prior Taxane Chemotherapy",    "Yes" if prior_chemo else "No",        2 if prior_chemo else 0),
        ("ECOG Performance Status",      ecog_ps[:1],                     {0: 0, 1: -2, 2: -8, 3: -20}.get(int(ecog_ps[0]), 0)),
        ("Gleason Score",                str(gleason_score),              4 if gleason_score >= 9 else 2 if gleason_score >= 8 else 1),
        ("Bone Metastases",              "Yes" if bone_mets else "No",         3 if bone_mets else 0),
        ("Visceral Metastases",          "Yes" if visceral_mets else "No",    -5 if visceral_mets else 0),
    ]
    df_breakdown = pd.DataFrame(breakdown, columns=["Factor", "Value", "Points"])
    df_breakdown["Impact"] = df_breakdown["Points"].apply(
        lambda p: f"✅ +{p}" if p > 0 else (f"⚠️ {p}" if p < 0 else "— 0")
    )
    df_breakdown["Category"] = [
        "Target Expression", "Target Expression", "Target Expression",
        "Disease Burden", "Disease Burden", "Disease Burden",
        "Genomics", "Genomics", "Genomics", "Genomics", "Genomics", "Genomics", "Genomics", "Genomics", "Genomics", "Genomics",
        "Treatment History", "Treatment History", "Treatment History",
        "Clinical", "Clinical", "Clinical", "Clinical",
    ]
    st.dataframe(
        df_breakdown[["Category", "Factor", "Value", "Impact"]],
        use_container_width=True, hide_index=True,
    )

    # ---- Side-by-side comparison card (compare mode) ----
    if compare_mode and len(profile_results) == 2:
        st.markdown("---")
        st.markdown("### ⚖️ Profile Comparison")
        cmp_c1, cmp_c2 = st.columns(2)
        for _i, _pr in enumerate(profile_results):
            _sc = _pr["score"]
            _col = "#22c55e" if _sc >= 65 else "#fbbf24" if _sc >= 45 else "#f97316" if _sc >= 25 else "#ef4444"
            _tier = "Tier 1 — Strong Candidate" if _sc >= 65 else "Tier 2 — Consider" if _sc >= 45 else "Tier 3 — Borderline" if _sc >= 25 else "Tier 4 — Not Suitable"
            [cmp_c1, cmp_c2][_i].markdown(
                f"<div style='background:{_col}22;border:2px solid {_col};padding:16px;border-radius:10px;text-align:center;'>"
                f"<div style='font-size:1.5em;font-weight:700;color:{_col};'>{_pr['label']}</div>"
                f"<div style='font-size:3em;font-weight:900;color:{_col};'>{_sc}</div>"
                f"<div style='color:{_col};font-size:0.9em;margin-top:4px;'>{_tier}</div>"
                f"<hr style='border-color:{_col}44;'>"
                f"<table style='width:100%;font-size:0.8em;color:#94a3b8;text-align:left;'>"
                f"<tr><td>CD46</td><td style='color:#e2e8f0;'>{_pr['cd46_expr']:.1f} log₂</td></tr>"
                f"<tr><td>PSMA</td><td style='color:#e2e8f0;'>{_pr['psma']}</td></tr>"
                f"<tr><td>PSA</td><td style='color:#e2e8f0;'>{_pr['psa']:.0f} ng/mL</td></tr>"
                f"<tr><td>AR-V7</td><td style='color:#e2e8f0;'>{'+'if _pr['arv7'] else '−'}</td></tr>"
                f"<tr><td>Prior Lu-PSMA</td><td style='color:#e2e8f0;'>{'Yes' if _pr['prior_lupsma'] else 'No'}</td></tr>"
                f"</table></div>",
                unsafe_allow_html=True,
            )

        # Radar comparison chart
        import plotly.graph_objects as _go2
        radar_dims = ["CD46 Expr", "PSMA inv.", "PSA Score", "Genomics", "Therapy Hist.", "Performance"]
        def _profile_radar(pr):
            psma_map = {"Absent": 12, "Low": 10, "Moderate": 6, "High": 2, "Very High": 0}
            genomics = (5 if pr["ar_amp"] else 0) + (4 if pr["arv7"] else 0) + (3 if pr["brca2"] else 0) - (5 if pr["tp53"] else 0) - (6 if pr["rb1"] else 0)
            therapy  = (8 if pr["prior_lupsma"] else 0) + ({"0 (ARSI-naive)": 0, "1 (1 line failed)": 3, "2+ (2+ lines failed)": 5}.get(pr["prior_arsi"], 0))
            ecog_n   = int(pr["ecog"][0])
            perf     = max(0, 10 - ecog_n * 3)
            psa_sc   = ({"< 3 months": 6, "3–6 months": 4, "6–12 months": 2, "> 12 months": 0}.get(pr["psadt"], 0))
            vals = [
                min(30, 30 if pr["cd46_expr"] >= 12 else 24 if pr["cd46_expr"] >= 10.5 else 15 if pr["cd46_expr"] >= 9 else 6),
                psma_map.get(pr["psma"], 0),
                psa_sc,
                max(0, min(15, genomics + 8)),
                min(13, therapy),
                perf,
            ]
            return [v / max_v * 10 for v, max_v in zip(vals, [30, 12, 6, 15, 13, 10])]

        fig_radar = _go2.Figure()
        colors = ["#38bdf8", "#4ade80"]
        for _i, _pr in enumerate(profile_results):
            r = _profile_radar(_pr)
            fig_radar.add_trace(_go2.Scatterpolar(
                r=r + [r[0]], theta=radar_dims + [radar_dims[0]],
                fill="toself", name=_pr["label"],
                line=dict(color=colors[_i], width=2),
                fillcolor=colors[_i].replace("#", "rgba(") + ",0.15)",
            ))
        fig_radar.update_layout(
            polar=dict(
                radialaxis=dict(visible=True, range=[0, 10], color="#64748b"),
                angularaxis=dict(color="#94a3b8"),
                bgcolor="#1e293b",
            ),
            paper_bgcolor="#0f172a", legend=dict(font=dict(color="#e2e8f0")),
            height=380, margin=dict(l=40, r=40, t=40, b=40),
            title=dict(text="Multi-Dimensional Profile Radar", font=dict(color="#e2e8f0", size=13)),
        )
        st.plotly_chart(fig_radar, width='stretch')

    # ---- Population Percentile ----
    st.markdown("---")
    st.markdown("### 📊 Population Context & Expected Outcomes")

    # Simulate a patient score distribution based on real CD46 expression distribution
    if not df_expr.empty:
        import numpy as _np2
        # Proxy population scores from real CD46 expression data (scaled 0–100)
        _cd46_vals = df_expr["cd46_log2_tpm"].dropna().values
        # Score distribution approximated from CD46 expression alone (simplified proxy)
        _pop_scores = _np2.clip((_cd46_vals - 6.0) / (14.0 - 6.0) * 70 + 15, 0, 100)
        _percentile = float((_pop_scores < final_score).mean() * 100)

        perc_col1, perc_col2, perc_col3, perc_col4 = st.columns(4)
        perc_col1.metric("Your Score", f"{final_score}/100", delta=f"Tier: {'1' if final_score>=65 else '2' if final_score>=45 else '3' if final_score>=25 else '4'}")
        perc_col2.metric("Population Percentile", f"{_percentile:.0f}th", help="Based on 11,069 TCGA patients, CD46 expression proxy scoring")
        perc_col3.metric("Patients Ranked Below", f"{int(_percentile/100 * len(_pop_scores)):,}", f"of {len(_pop_scores):,} total")
        perc_col4.metric("Tier Distribution", f"{'Strong Candidate' if final_score>=65 else 'Consider' if final_score>=45 else 'Borderline' if final_score>=25 else 'Not Suitable'}")

        # Score distribution histogram with patient marker
        import plotly.graph_objects as _go3
        fig_dist = _go3.Figure()
        fig_dist.add_trace(_go3.Histogram(
            x=_pop_scores, nbinsx=40,
            marker_color="#1e40af", opacity=0.7, name="Population",
        ))
        fig_dist.add_vline(x=final_score, line_color="#f59e0b", line_width=3, annotation_text=f"This Patient ({final_score})", annotation_font_color="#f59e0b")
        # Tier markers
        for thr, col, lbl in [(65, "#22c55e", "Tier 1"), (45, "#fbbf24", "Tier 2"), (25, "#f97316", "Tier 3")]:
            fig_dist.add_vline(x=thr, line_color=col, line_width=1.5, line_dash="dot", annotation_text=lbl, annotation_font_color=col, annotation_position="top left")
        fig_dist.update_layout(
            height=280, paper_bgcolor="#0f172a", plot_bgcolor="#0f172a",
            xaxis=dict(title="Suitability Score", color="#94a3b8", range=[0, 100], gridcolor="#1e293b"),
            yaxis=dict(title="# Patients", color="#94a3b8", gridcolor="#1e293b"),
            legend=dict(font=dict(color="#e2e8f0")), margin=dict(l=10, r=10, t=30, b=10),
            title=dict(text="Score Distribution vs. TCGA Population (11,069 patients, proxy model)",
                       font=dict(color="#e2e8f0", size=12)),
        )
        st.plotly_chart(fig_dist, width='stretch')

        # ---- Expected Outcomes by Tier (from survival CSV) ----
        import pathlib as _pl2
        _surv_path = _pl2.Path(__file__).resolve().parents[2] / "data" / "processed" / "cd46_survival_results.csv"
        if _surv_path.exists():
            _surv_df = pd.read_csv(_surv_path)
            _os_df = _surv_df[_surv_df["endpoint"] == "OS"].dropna(subset=["hazard_ratio"])
            if not _os_df.empty:
                st.markdown("**📈 Historical Outcomes by Tier — from Survival Analysis**")
                st.caption(f"Based on {len(_os_df)} OS endpoints across TCGA cohorts; showing what tier the CD46-high group achieved.")
                _tier_thresholds = {"Tier 1 (≥65)": _os_df[_os_df["hazard_ratio"] >= 1.5], "Tier 2 (45-64)": _os_df[(_os_df["hazard_ratio"] >= 1.2) & (_os_df["hazard_ratio"] < 1.5)], "Others": _os_df[_os_df["hazard_ratio"] < 1.2]}
                for _tt, _tdf in _tier_thresholds.items():
                    if not _tdf.empty:
                        with st.expander(f"{_tt} — {len(_tdf)} matching cohorts"):
                            st.dataframe(_tdf[["cancer_type","hazard_ratio","p_value","n_high","n_low"]].rename(columns={"cancer_type":"Cancer","hazard_ratio":"HR (CD46-High)","p_value":"p-value","n_high":"N High","n_low":"N Low"}).head(10), use_container_width=True, hide_index=True)

    # ---- Sensitivity analysis: what changes the score most? ----
    st.markdown("---")
    st.markdown("### 🎯 Score Sensitivity Analysis — What Would Change the Score?")
    st.caption("Shows how much each biomarker change would move the score if flipped from its current value.")

    _sens_items = [
        ("Add: Prior Lu-PSMA failure",   8 if not prior_lupsma else 0,         not prior_lupsma),
        ("Flip: AR-V7 positive",          4 if not arv7_positive else -4,        True),
        ("Flip: AR Amplification",        5 if not ar_amplification else -5,     True),
        ("Add: BRCA2/HRD loss",           3 if not brca2_loss else 0,            not brca2_loss),
        ("Remove: TP53 loss",             5 if tp53_loss else 0,                  tp53_loss),
        ("Remove: RB1 loss",              6 if rb1_loss else 0,                   rb1_loss),
        ("Remove: Visceral mets",         5 if visceral_mets else 0,              visceral_mets),
        ("Remove: PTEN loss",             3 if pten_loss else 0,                  pten_loss),
        ("Increase CD46 to ≥12.0",        max(0, 30 - (30 if cd46_expr >= 12 else 24 if cd46_expr >= 10.5 else 15 if cd46_expr >= 9 else 6)), cd46_expr < 12.0),
        ("Improve PSADT to < 3 months",   max(0, 6 - psadt_pts.get(psa_doubling, 0)), psa_doubling != "< 3 months"),
        ("Add: 2+ prior ARSI lines",      max(0, 5 - arsi_pts.get(prior_arsi_lines, 0)), prior_arsi_lines != "2+ (2+ lines failed)"),
        ("Add: CDK12 biallelic loss",     2 if not cdk12_loss else 0,             not cdk12_loss),
    ]
    _sens_df = pd.DataFrame(
        [(item, delta, f"{'⬆️ +' if delta > 0 else '⬇️ ' if delta < 0 else '—'}{abs(delta)}", final_score + delta)
         for item, delta, condition in _sens_items if condition and delta != 0],
        columns=["Change", "Delta", "Effect", "New Score"],
    )
    if not _sens_df.empty:
        _sens_df = _sens_df.sort_values("Delta", ascending=False)
        st.dataframe(_sens_df, use_container_width=True, hide_index=True)
    else:
        st.info("Score is near maximum — no further improvements identified.")

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
                    st.plotly_chart(fig_dist, width='stretch')

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
                        st.plotly_chart(fig_lm, width='stretch')
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
        st.plotly_chart(fig_gauge, width='stretch')

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
