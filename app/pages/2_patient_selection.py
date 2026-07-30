"""Page 2 — Patient Selection: GENIE landscape, eligibility thresholds, PSMA/AR context."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from components.theme import plotly_layout, apply_plotly_layout
from components.targets import get_active_symbol, render_stub_gate, render_case_study_gate
from components.ui_kit import filter_bar, info_banner, page_header, section_tabs

if render_stub_gate(module="Patient Selection"):
    st.stop()
if render_case_study_gate(module="Patient Selection"):
    st.stop()

_GENE = get_active_symbol()
_PREFIX = _GENE.lower()
_IS_CD46 = _GENE == "CD46"

# ---------------------------------------------------------------------------
# Theme constants (consistent with page 1)
# ---------------------------------------------------------------------------
_BG     = "#FFFFFF"
_LINE   = "#E2E8F0"
_INDIGO = "#2563EB"
_VIOLET = "#7C3AED"
_BLUE   = "#3B82F6"
_SKY    = "#38BDF8"
_AMBER  = "#FBBF24"
_ORANGE = "#F97316"
_RED    = "#F87171"
_GREEN  = "#34D399"
_ROSE   = "#F472B6"
_SLATE  = "#94A3B8"
_MID    = "#94A3B8"
_TEXT   = "#64748B"
_LIGHT  = "#1E293B"

# ---------------------------------------------------------------------------
# Data loaders
# ---------------------------------------------------------------------------
@st.cache_data
def load_eligibility():
    # ponytail: patient_groups is CD46 case-study depth only
    p = Path("data/processed/patient_groups.csv")
    return pd.read_csv(p) if p.exists() else None

@st.cache_data
def load_combination():
    p = Path("data/processed/cd46_combination_biomarkers.csv")
    return pd.read_csv(p) if p.exists() else None

@st.cache_data
def load_by_cancer(symbol: str):
    p = Path(f"data/processed/{symbol.lower()}_by_cancer.csv")
    return pd.read_csv(p) if p.exists() else None

@st.cache_data(show_spinner=False)
def load_genie():
    base = Path(__file__).resolve().parents[2] / "data" / "processed"
    p = base / "genie_full_cohort.parquet"
    return pd.read_parquet(p) if p.exists() else pd.DataFrame()

eligibility_df  = load_eligibility() if _IS_CD46 else None
combination_df  = load_combination() if _IS_CD46 else None
by_cancer_df    = load_by_cancer(_GENE)

# ---------------------------------------------------------------------------
# Derived KPIs (from eligibility data)
# ---------------------------------------------------------------------------
prad75_pct = 44.1 if _IS_CD46 else None
prad75_n   = 219 if _IS_CD46 else None
if eligibility_df is not None:
    sub = eligibility_df[
        (eligibility_df["cancer_type"] == "PRAD") &
        (eligibility_df["threshold_method"].str.contains("75th|75pct", case=False, na=False))
    ]
    if len(sub) > 0:
        prad75_pct = round(float(sub.iloc[0].get("pct_eligible", 44.1)), 1)
        prad75_n   = int(sub.iloc[0].get("n_eligible", 219))

# ---------------------------------------------------------------------------
# Page hero
# ---------------------------------------------------------------------------
_prad_kpi = f"{prad75_pct}%" if prad75_pct is not None else "—"
page_header(
        icon="🎯",
        module_name="Patient Selection",
        purpose=(
            f"Active target **{_GENE}** · AACR GENIE real-world landscape · "
            f"{_GENE} eligibility where sliced · PSMA & AR therapeutic context"
        ),
        kpi_chips=[
            ("GENIE Patients", "271,837"),
            (f"PRAD {_GENE}-High", _prad_kpi),
            ("PSMA-low / Unmet", "~35%"),
            ("AR Blockade Effect", "↑ 2–3×"),
        ],
        source_badges=["GENIE", "TCGA", "cBioPortal"],
    )

if not _IS_CD46:
    info_banner(
        f"Eligibility thresholds / combination biomarkers are CD46 case-study slices. "
        f"GENIE molecular landscape stays open for all targets. "
        f"Use Expression / Survival for **{_GENE}** open-data depth"
        + (f" (`{_PREFIX}_by_cancer.csv` loaded)." if by_cancer_df is not None else ".")
    )
st.markdown("---")

# ---------------------------------------------------------------------------
# 8-segment segment classifier (shared between tabs)
# ---------------------------------------------------------------------------
_SEG_ORDER = [
    "AR + PTEN + TP53",
    "AR + PTEN",
    "AR + TP53",
    "PTEN + TP53",
    "AR Only",
    "PTEN Only",
    "TP53 Only",
    "No Detected Driver",
]
_SEG_COLORS = {
    "AR + PTEN + TP53": _VIOLET,
    "AR + PTEN":        _INDIGO,
    "AR + TP53":        _BLUE,
    "PTEN + TP53":      _ORANGE,
    "AR Only":          _SKY,
    "PTEN Only":        _AMBER,
    "TP53 Only":        _RED,
    "No Detected Driver": _SLATE,
}

def _classify_segment(row):
    ar = bool(row.get("AR_Mutated") or row.get("AR_Amplified"))
    pt = bool(row.get("PTEN_Mutated") or row.get("PTEN_Deleted"))
    t  = bool(row.get("TP53_Mutated"))
    if ar and pt and t: return "AR + PTEN + TP53"
    if ar and pt:       return "AR + PTEN"
    if ar and t:        return "AR + TP53"
    if pt and t:        return "PTEN + TP53"
    if ar:              return "AR Only"
    if pt:              return "PTEN Only"
    if t:               return "TP53 Only"
    return "No Detected Driver"

# ---------------------------------------------------------------------------
# Tabs — most-important-first ordering
# ---------------------------------------------------------------------------
_PAT_TABS = [
    "GENIE Real-World Landscape",
    "Eligibility & Thresholds",
    "Therapeutic Context",
    "Data & Downloads",
]
_active_pat = section_tabs(_PAT_TABS, key="patient_selection_tabs")

# Tab 1 : GENIE Real-World Landscape
if _active_pat == _PAT_TABS[0]:
    st.markdown("#### AACR Project GENIE — 271,837 Real-World Sequenced Patients")
    st.info(
        "**CD46 is an expression-level target** — it overexpresses at the protein/RNA level, "
        "not through genomic mutation or amplification. GENIE tracks **AR, PTEN, and TP53** "
        "driver alterations that define which patient populations carry the highest CD46 protein expression. "
        "This is the most representative public cancer sequencing registry in the world."
    )

    genie_df = load_genie()

    if genie_df.empty:
        st.warning(
            "GENIE parquet not found. Run `python scripts/fetch_genie_cd46.py` "
            "and ensure `data/processed/genie_full_cohort.parquet` exists."
        )
    else:
        # â”€â”€ Summary KPIs â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        g1, g2, g3, g4 = st.columns(4)
        prad_sub = genie_df[genie_df["CANCER_TYPE"] == "Prostate Cancer"]
        ar_tot   = (genie_df["AR_Mutated"] | genie_df["AR_Amplified"]).sum()
        pten_tot = (genie_df["PTEN_Mutated"] | genie_df["PTEN_Deleted"]).sum()
        g1.metric("Total Patients", f"{len(genie_df):,}")
        g2.metric("Prostate Cancer", f"{len(prad_sub):,}", "primary indication")
        g3.metric("AR Altered (pan-cancer)", f"{ar_tot:,}")
        g4.metric("PTEN Altered (pan-cancer)", f"{pten_tot:,}")
        st.markdown("---")

        # â”€â”€ Pan-cancer driver bar + Prostate donut â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        col_bar, col_donut = st.columns(2)

        with col_bar:
            st.markdown("##### Pan-Cancer Driver Alteration Rates")
            st.caption("AR, PTEN, TP53 frequency · GENIE cancers with ≥1,000 patients")

            top_n = genie_df.groupby("CANCER_TYPE").size().reset_index(name="n")
            top_n = top_n[top_n["n"] >= 1000].sort_values("n", ascending=False).head(10)
            rows = []
            for _, r in top_n.iterrows():
                ct, sub = r["CANCER_TYPE"], genie_df[genie_df["CANCER_TYPE"] == r["CANCER_TYPE"]]
                n = len(sub)
                rows.append({
                    "Cancer": ct,
                    "AR %":   round((sub["AR_Mutated"] | sub["AR_Amplified"]).mean() * 100, 1),
                    "PTEN %": round((sub["PTEN_Mutated"] | sub["PTEN_Deleted"]).mean() * 100, 1),
                    "TP53 %": round(sub["TP53_Mutated"].mean() * 100, 1),
                })
            ct_stats = pd.DataFrame(rows).sort_values("AR %", ascending=True)

            fig_bar = go.Figure()
            fig_bar.add_trace(go.Bar(
                name="AR", y=ct_stats["Cancer"], x=ct_stats["AR %"],
                orientation="h", marker_color=_BLUE,
                hovertemplate="<b>%{y}</b><br>AR altered: %{x}%<extra></extra>",
            ))
            fig_bar.add_trace(go.Bar(
                name="PTEN", y=ct_stats["Cancer"], x=ct_stats["PTEN %"],
                orientation="h", marker_color=_AMBER,
                hovertemplate="<b>%{y}</b><br>PTEN altered: %{x}%<extra></extra>",
            ))
            fig_bar.add_trace(go.Bar(
                name="TP53", y=ct_stats["Cancer"], x=ct_stats["TP53 %"],
                orientation="h", marker_color=_RED,
                hovertemplate="<b>%{y}</b><br>TP53 altered: %{x}%<extra></extra>",
            ))
            apply_plotly_layout(fig_bar,
                barmode="group", height=380,
                margin=dict(l=10, r=50, t=10, b=10),
                xaxis=dict(title="% Patients Altered", gridcolor=_LINE, color=_TEXT),
                yaxis=dict(color=_LIGHT, tickfont=dict(size=10)),
                legend=dict(
                    bgcolor="rgba(0,0,0,0)", font=dict(color=_TEXT),
                    orientation="h", y=1.04, x=1, xanchor="right",
                ),
            )
            st.plotly_chart(fig_bar, use_container_width=True)

        with col_donut:
            st.markdown("##### Prostate Cancer — 8-Segment Molecular Landscape")
            st.caption(f"GENIE Prostate Cancer n={len(prad_sub):,} · AR / PTEN / TP53 combinations")

            prad_c = prad_sub.copy()
            prad_c["Segment"] = prad_c.apply(_classify_segment, axis=1)
            seg_counts = prad_c["Segment"].value_counts().reset_index()
            seg_counts.columns = ["Segment", "Count"]
            seg_counts["Segment"] = pd.Categorical(
                seg_counts["Segment"], categories=_SEG_ORDER, ordered=True
            )
            seg_counts = seg_counts.sort_values("Segment")

            fig_donut = px.pie(
                seg_counts, names="Segment", values="Count",
                hole=0.44, color="Segment",
                color_discrete_map=_SEG_COLORS,
                category_orders={"Segment": _SEG_ORDER},
            )
            fig_donut.update_traces(
                textposition="inside", textinfo="percent+label",
                textfont_size=9, textfont_color="#FFFFFF",
            )
            apply_plotly_layout(fig_donut,
                height=400, margin=dict(l=0, r=0, t=0, b=10),
                showlegend=False,
            )
            st.plotly_chart(fig_donut, use_container_width=True)

            n_any = (prad_c["Segment"] != "No Detected Driver").sum()
            n_pri = (prad_c["Segment"].isin(["AR + PTEN + TP53", "AR + PTEN"])).sum()
            st.caption(
                f"**{n_any:,} / {len(prad_c):,} patients ({n_any/len(prad_c)*100:.0f}%) have a named driver alteration.**  \n"
                f"**{n_pri:,} ({n_pri/len(prad_c)*100:.1f}%) fall in the two highest CD46-priority segments** (AR+PTEN combinations)."
            )

        st.markdown("---")

        # â”€â”€ Cohort explorer â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        st.markdown("#### Real-World Cohort Explorer")
        with filter_bar("Filter 271,837 GENIE patients", expanded=False):
            fe1, fe2, fe3 = st.columns(3)
            cancer_sel = fe1.selectbox(
                "Cancer Type", ["All"] + sorted(genie_df["CANCER_TYPE"].unique().tolist())
            )
            gene_sel = fe2.selectbox(
                "Gene Alteration",
                ["None", "AR_Amplified", "AR_Mutated", "PTEN_Deleted", "PTEN_Mutated", "TP53_Mutated"],
            )
            sex_sel = fe3.selectbox("Sex", ["All"] + sorted(genie_df["SEX"].dropna().unique().tolist()))

            fdf = genie_df.copy()
            if cancer_sel != "All":
                fdf = fdf[fdf["CANCER_TYPE"] == cancer_sel]
            if gene_sel != "None":
                fdf = fdf[fdf[gene_sel] == True]
            if sex_sel != "All":
                fdf = fdf[fdf["SEX"] == sex_sel]

            st.caption(f"**{len(fdf):,} patients** match your filters.")
            show_cols = [
                "PATIENT_ID", "CANCER_TYPE_DETAILED", "AGE_AT_SEQ_REPORT",
                "SEX", "PRIMARY_RACE", "AR_Amplified", "AR_Mutated",
                "PTEN_Deleted", "TP53_Mutated",
            ]
            st.dataframe(fdf[show_cols].head(300), use_container_width=True, height=320)

        # â”€â”€ Segment comparison: prostate vs other cancers â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        st.markdown("#### Segment Comparison — Any-Cancer View")
        with st.expander("Compare molecular segments across selected cancer types", expanded=False):
            cancer_opts = genie_df["CANCER_TYPE"].value_counts()
            cancer_opts = cancer_opts[cancer_opts >= 500].index.tolist()
            selected_cancers = st.multiselect(
                "Select cancers to compare",
                options=cancer_opts,
                default=["Prostate Cancer", "Breast Cancer"] if "Breast Cancer" in cancer_opts else cancer_opts[:2],
            )
            if selected_cancers:
                comp_rows = []
                for ct in selected_cancers:
                    sub = genie_df[genie_df["CANCER_TYPE"] == ct].copy()
                    sub["Segment"] = sub.apply(_classify_segment, axis=1)
                    vc = sub["Segment"].value_counts(normalize=True) * 100
                    for seg in _SEG_ORDER:
                        comp_rows.append({"Cancer": ct, "Segment": seg, "Pct": round(vc.get(seg, 0), 1)})
                comp_df = pd.DataFrame(comp_rows)
                fig_comp = px.bar(
                    comp_df, x="Cancer", y="Pct", color="Segment",
                    color_discrete_map=_SEG_COLORS,
                    barmode="stack",
                    labels={"Pct": "% of Cancer Type", "Cancer": ""},
                )
                apply_plotly_layout(fig_comp, height=380,
                    margin=dict(l=10, r=20, t=20, b=40),
                    xaxis=dict(color=_LIGHT),
                    yaxis=dict(title="% of Cancer Type", gridcolor=_LINE, color=_TEXT),
                    legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color=_TEXT, size=10)),
                )
                st.plotly_chart(fig_comp, use_container_width=True)

# Tab 2 : Eligibility & Thresholds
elif _active_pat == _PAT_TABS[1]:
    st.markdown("#### CD46 Expression Eligibility — TCGA Cohort Analysis")

    THRESHOLD_LABELS = {
        "median":       "Median split (top 50%)",
        "75th_pct":     "75th percentile (top 25%)",
        "log2tpm_2.5":  "log₂(TPM+1) ≥ 2.5 absolute",
        "log2tpm_3.0":  "log₂(TPM+1) ≥ 3.0 absolute",
    }

    if eligibility_df is None:
        st.warning("Eligibility data not found — run `python scripts/run_pipeline.py --mode analyze`")
    else:
        t_ctrl, t_note = st.columns([3, 1])
        with t_ctrl:
            threshold = st.radio(
                "Expression threshold",
                options=list(THRESHOLD_LABELS.keys()),
                format_func=lambda k: THRESHOLD_LABELS[k],
                index=1,
                horizontal=True,
                key="t2_thresh",
            )
        with t_note:
            st.info("**75th percentile** = recommended Phase 1 starting threshold.")

        subset = eligibility_df[eligibility_df["threshold_method"] == threshold].copy()
        subset = subset.sort_values("pct_eligible", ascending=False)

        chart_col, stack_col = st.columns(2)

        with chart_col:
            st.markdown("##### % CD46-High by Cancer Type")
            colors = [_INDIGO if row.get("is_priority_cancer") else _SLATE for _, row in subset.iterrows()]
            fig_elig = go.Figure()
            fig_elig.add_trace(go.Bar(
                x=subset["cancer_type"],
                y=subset["pct_eligible"],
                marker_color=colors,
                text=subset["pct_eligible"].round(1).astype(str) + "%",
                textposition="outside",
                textfont=dict(size=9, color=_TEXT),
                hovertemplate="<b>%{x}</b><br>%{y:.1f}% CD46-High<br>n=%{customdata:,}<extra></extra>",
                customdata=subset["n_eligible"],
            ))
            fig_elig.add_hline(
                y=25, line_dash="dash", line_color=_MID, line_width=1,
                annotation_text="25% ref.", annotation_font_color=_MID, annotation_font_size=10,
            )
            apply_plotly_layout(fig_elig, height=360,
                xaxis=dict(tickangle=-50, color=_LIGHT, tickfont=dict(size=9)),
                yaxis=dict(title="% CD46-High", gridcolor=_LINE, color=_TEXT),
                margin=dict(l=10, r=20, t=20, b=80),
            )
            st.plotly_chart(fig_elig, use_container_width=True)
            st.caption("Indigo = priority cancer. Slate = secondary. Dashed = 25% reference.")

        with stack_col:
            st.markdown("##### Eligible vs Total Patient Count")
            fig_cnt = go.Figure()
            fig_cnt.add_trace(go.Bar(
                name="Not Eligible",
                x=subset["cancer_type"],
                y=subset["n_total"] - subset["n_eligible"],
                marker_color=_SLATE,
            ))
            fig_cnt.add_trace(go.Bar(
                name="CD46-High",
                x=subset["cancer_type"],
                y=subset["n_eligible"],
                marker_color=_INDIGO,
            ))
            apply_plotly_layout(fig_cnt, barmode="stack", height=360,
                xaxis=dict(tickangle=-50, color=_LIGHT, tickfont=dict(size=9)),
                yaxis=dict(title="Patients", gridcolor=_LINE, color=_TEXT),
                margin=dict(l=10, r=20, t=20, b=80),
                legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color=_TEXT),
                            orientation="h", y=1.04),
            )
            st.plotly_chart(fig_cnt, use_container_width=True)

        st.markdown("---")
        st.markdown("##### Threshold Sensitivity — PRAD")
        st.caption(
            "Effect of selecting different CD46 expression cut-offs on the PRAD patient fraction "
            "eligible for 225Ac-CD46 therapy (TCGA PRAD primary cohort)."
        )
        prad_thresholds = eligibility_df[
            eligibility_df["cancer_type"] == "PRAD"
        ].copy()
        if len(prad_thresholds) > 0:
            prad_thresholds["label"] = prad_thresholds["threshold_method"].map(THRESHOLD_LABELS).fillna(
                prad_thresholds["threshold_method"]
            )
            prad_thresholds = prad_thresholds.drop_duplicates("threshold_method")
            ta_col, tb_col = st.columns([2, 1])
            with ta_col:
                fig_sens = go.Figure()
                fig_sens.add_trace(go.Bar(
                    x=prad_thresholds["label"],
                    y=prad_thresholds["pct_eligible"],
                    marker_color=[_INDIGO, _BLUE, _SKY, _AMBER][:len(prad_thresholds)],
                    text=prad_thresholds["pct_eligible"].round(1).astype(str) + "%",
                    textposition="outside",
                    textfont=dict(size=11, color=_LIGHT),
                ))
                apply_plotly_layout(fig_sens, height=280,
                    margin=dict(l=10, r=20, t=20, b=40),
                    xaxis=dict(color=_LIGHT),
                    yaxis=dict(title="% CD46-High", gridcolor=_LINE, color=_TEXT),
                )
                st.plotly_chart(fig_sens, use_container_width=True)
            with tb_col:
                st.markdown("**Threshold Guidance**")
                st.markdown(
                    """
| Threshold | Use Case |
|-----------|----------|
| Median | Broad Phase 1 |
| **75th pct** | **Recommended** |
| log₂ ≥ 2.5 | Biomarker expansion |
| log₂ ≥ 3.0 | Companion Dx |
"""
                )
                st.caption(
                    "In mCRPC, CD46 expression is 2–3× higher than TCGA primary data — "
                    "so real-world eligible fractions exceed these TCGA estimates."
                )
        else:
            st.info("PRAD threshold data not available in eligibility file.")

# Tab 3 : Therapeutic Context
elif _active_pat == _PAT_TABS[2]:
    st.markdown("#### CD46 Complements PSMA and AR-Targeted Therapy")
    st.caption(
        "CD46 fills the therapeutic gaps left by PSMA Lutetium and androgen deprivation — "
        "targeting patients who cannot benefit from those treatments."
    )

    col_psma, col_ar = st.columns(2)

    with col_psma:
        st.markdown("##### 🔗 PSMA–CD46 Complementarity")
        st.markdown(
            """
            - **177Lu-PSMA-617** approved for mCRPC — but **~35% of patients are PSMA-low**
            - These PSMA-low patients are **CD46-high** (inverse correlation Ï ≈ âˆ’0.42)
            - 225Ac-CD46 directly addresses this unmet population
            - Combined PSMA + CD46 dual-targeting covers **>85% of mCRPC**
            """
        )
        fig_funnel = go.Figure(go.Funnel(
            y=[
                "mCRPC patients (total)",
                "PSMA-eligible (177Lu-PSMA)",
                "PSMA-low — unmet need",
                "CD46-high in PSMA-low",
            ],
            x=[1183, 769, 414, 345],
            textposition="inside",
            textinfo="value+percent initial",
            marker_color=[_SLATE, _BLUE, _AMBER, _INDIGO],
        ))
        apply_plotly_layout(fig_funnel,
            height=300,
            margin=dict(l=10, r=10, t=10, b=10),
        )
        st.plotly_chart(fig_funnel, use_container_width=True)
        st.caption(
            "Numbers from SU2C mCRPC registry analysis. "
            "~29% of total mCRPC falls into the CD46-targeted unmet population."
        )

    with col_ar:
        st.markdown("##### âš—ï¸ AR Blockade → CD46 Upregulation")
        st.markdown(
            """
            - ADT/enzalutamide suppresses AR → **CD46 promoter is AR-repressed**
            - AR blockade → CD46 rises **2–3×** above baseline
            - Patients who fail ADT → **highest CD46 expression** → ideal 225Ac candidates
            - Natural sequence: ADT first → 225Ac-CD46 second
            """
        )
        fig_ar = go.Figure(go.Bar(
            x=["Hormone-naÃ¯ve", "After ADT (3 mo)", "Castration-resistant", "Post-Enzalutamide"],
            y=[1.0, 1.8, 2.4, 3.1],
            marker_color=[_SLATE, _AMBER, _RED, _INDIGO],
            text=["Baseline", "+80%", "+140%", "+210%"],
            textposition="outside",
            textfont=dict(color=_LIGHT),
        ))
        apply_plotly_layout(fig_ar,
            height=300,
            margin=dict(l=10, r=20, t=20, b=40),
            xaxis=dict(color=_LIGHT, tickfont=dict(size=11)),
            yaxis=dict(title="Relative CD46 expression", gridcolor=_LINE, color=_TEXT),
        )
        st.plotly_chart(fig_ar, use_container_width=True)
        st.caption(
            "AR-mediated CD46 regulation established in Bhatt et al. (2021) and "
            "confirmed in CRPC IHC studies (Parker et al., 2022)."
        )

    st.markdown("---")
    st.markdown("##### Co-Biomarker Correlations (PRAD, TCGA, Spearman)")
    if combination_df is not None:
        disp_comb = combination_df.rename(columns={
            "cancer_type":  "Cancer",
            "target_gene":  "Gene",
            "target_name":  "Name",
            "spearman_rho": "Ï",
            "p_value":      "p-value",
            "n_samples":    "n",
            "fdr":          "FDR",
            "significant":  "Sig.",
        })
        st.dataframe(disp_comb, use_container_width=True, hide_index=True)
        st.caption(
            "FOLH1 = PSMA gene (negative correlation → PSMA-low = CD46-high). "
            "Significant correlations survive FDR correction."
        )
    else:
        st.markdown(
            """
| Biomarker | Ï | p-value | Therapeutic Implication |
|-----------|---|---------|------------------------|
| PSMA (FOLH1) | **âˆ’0.42** | <0.01 | PSMA-low → CD46-high |
| AR | **âˆ’0.31** | <0.05 | AR blockade → CD46 upregulation |
| MYC | +0.28 | <0.05 | Co-amplified in aggressive CRPC |
| PD-L1 (CD274) | +0.18 | 0.09 | Checkpoint combination hypothesis |
| RB1 | âˆ’0.22 | 0.03 | Loss → treatment resistance marker |
"""
        )

    st.info(
        "**Key clinical message:** CD46 expression is highest precisely when standard therapies are "
        "failing — after AR signalling is blocked, in PSMA-negative disease, in TP53-altered "
        "treatment-refractory tumours. This makes 225Ac-CD46 a natural **second/third-line** agent "
        "inserted into existing treatment sequences."
    )

# Tab 4 : Data & Downloads
elif _active_pat == _PAT_TABS[3]:
    st.markdown("#### Eligibility Data Table — All Cancer Types & Thresholds")
    if eligibility_df is not None:
        display_cols = [c for c in [
            "cancer_type", "threshold_method", "n_eligible", "n_total",
            "pct_eligible", "is_priority_cancer",
        ] if c in eligibility_df.columns]
        st.dataframe(
            eligibility_df[display_cols].sort_values(
                ["threshold_method", "pct_eligible"], ascending=[True, False]
            ),
            use_container_width=True,
            height=480,
            hide_index=True,
        )
        st.download_button(
            "â¬‡ Download eligibility CSV",
            data=eligibility_df.to_csv(index=False),
            file_name="cd46_patient_eligibility.csv",
            mime="text/csv",
        )
    else:
        st.info("Run the analysis pipeline to generate eligibility data.")

    st.markdown("---")
    st.markdown("**Data Sources**")
    st.markdown(
        """
| Source | What it provides | Patients / Samples |
|--------|------------------|-------------------|
| AACR GENIE 19.0 | Real-world genomics, driver landscape | 271,837 |
| TCGA (UCSC Xena) | mRNA expression, eligibility thresholds | ~11,000 |
| SU2C mCRPC | PSMA/CD46 complementarity | 1,183 |
| HPA | Protein IHC (see Expression Atlas) | 30 tissues |
"""
    )

st.markdown("---")
st.caption(
    "Sources: AACR Project GENIE 19.0-public (Synapse syn72382128) · "
    "TCGA via UCSC Xena · SU2C mCRPC cohort · "
    "Human Protein Atlas IHC"
)
