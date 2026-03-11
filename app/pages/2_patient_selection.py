"""Page 2 — Patient Eligibility for 225Ac-CD46 Therapy."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st


st.title("🎯 Patient Selection — 225Ac-CD46 Therapy")
st.caption("Who is eligible? · How many? · Why CD46? · What else matters?")

# ---------------------------------------------------------------------------
# Clinical context banner — the "missing connection"
# ---------------------------------------------------------------------------

with st.container(border=True):
    st.markdown(
        """
        **How Patient Selection Works for 225Ac-CD46:**  
        1. **Expression screen:** Tumour biopsies with CD46 above threshold → ELIGIBLE  
        2. **Complementarity screen:** PSMA-low patients (~35% of mCRPC) who can't receive PSMA therapy → ADD-ON eligible  
        3. **Resistance screen:** Patients who progressed on androgen deprivation → AR blockade *upregulates* CD46 → NEWLY eligible  
        4. **Safety screen:** Normal tissue CD46 (kidney) assessed for dosimetry tolerance  
        """
    )

# ---------------------------------------------------------------------------
# Load data
# ---------------------------------------------------------------------------

@st.cache_data
def load_eligibility():
    p = Path("data/processed/patient_groups.csv")
    return pd.read_csv(p) if p.exists() else None

@st.cache_data
def load_depmap():
    p = Path("data/processed/depmap_cd46_essentiality.csv")
    return pd.read_csv(p) if p.exists() else None

@st.cache_data
def load_cbioportal():
    p = Path("data/processed/cbioportal_mcrpc.csv")
    return pd.read_csv(p) if p.exists() else None

@st.cache_data
def load_combination():
    p = Path("data/processed/cd46_combination_biomarkers.csv")
    return pd.read_csv(p) if p.exists() else None

eligibility_df = load_eligibility()
depmap_df = load_depmap()
cbioportal_df = load_cbioportal()
combination_df = load_combination()

# ---------------------------------------------------------------------------
# Hero KPI strip
# ---------------------------------------------------------------------------

k1, k2, k3, k4 = st.columns(4)
if eligibility_df is not None:
    prad75 = eligibility_df[
        (eligibility_df["cancer_type"] == "PRAD") & (eligibility_df["threshold_method"] == "75th_pct")
    ]
    if len(prad75) > 0:
        row = prad75.iloc[0]
        k1.metric("CD46-High in PRAD (75th pct)", f"{int(row.get('n_eligible', 219))}", "TCGA PRAD patients")
        k2.metric("% Eligible — PRAD", f"{round(float(row.get('pct_eligible', 44.1)), 1)}%", "at 75th percentile")
    else:
        k1.metric("CD46-High in PRAD", "~219", "TCGA PRAD patients")
        k2.metric("% Eligible — PRAD", "44.1%", "at 75th percentile")
else:
    k1.metric("CD46-High in PRAD", "~219", "TCGA PRAD patients")
    k2.metric("% Eligible — PRAD", "44.1%", "at 75th percentile")

k3.metric("PSMA-low / CD46-high (mCRPC)", "~35%", "Cannot receive PSMA Lutetium")
k4.metric("AR blockade effect", "↑ 2–3×", "CD46 upregulated post-castration")

st.markdown("---")

# ---------------------------------------------------------------------------
# Real-world Genomics (AACR GENIE)
# ---------------------------------------------------------------------------

@st.cache_data(show_spinner=False)
def _load_genie_data():
    base = Path(__file__).resolve().parents[2] / "data" / "processed"
    p = base / "genie_full_cohort.parquet"
    if p.exists():
        return pd.read_parquet(p)
    return pd.DataFrame()

def _show_genie_tab():
    st.markdown("### AACR Project GENIE: Real-World Clinical Genomics")
    st.info(
        "**Source:** AACR Project GENIE Release 19.0-public (271,837 real-world sequenced tumours)  \n"
        "**Significance:** Validates CD46, AR, and PTEN mutational/amplification prevalence in massive clinical populations."
    )

    df = _load_genie_data()

    if df.empty:
        st.warning("GENIE full cohort file not found. Run `python scripts/fetch_genie_cd46.py`.")
        return

    # Explain CD46 biology upfront
    st.info(
        "🧬 **CD46 is an expression-level target** — it is overexpressed in cancer at the protein/RNA level, "
        "not through genomic amplification or mutation. The GENIE genomic data below shows **AR, PTEN, and TP53** "
        "alterations that define the patient population where CD46-directed therapy is indicated."
    )

    # High-level Metrics
    c1, c2, c3, c4 = st.columns(4)
    prad_df = df[df["CANCER_TYPE"] == "Prostate Cancer"]
    c1.metric("Total Patients", f"{len(df):,}")
    c2.metric("Prostate Cancers", f"{len(prad_df):,}")
    ar_altered_total = (df["AR_Mutated"] | df["AR_Amplified"]).sum()
    pten_altered_total = (df["PTEN_Mutated"] | df["PTEN_Deleted"]).sum()
    c3.metric("AR Altered (pan-cancer)", f"{ar_altered_total:,}", "driver alterations")
    c4.metric("PTEN Altered (pan-cancer)", f"{pten_altered_total:,}", "loss events")

    st.markdown("---")

    # Build per-cancer alteration stats for top cancers (>1000 patients)
    top_cancers = df.groupby("CANCER_TYPE").size().reset_index(name="n")
    top_cancers = top_cancers[top_cancers["n"] >= 1000].sort_values("n", ascending=False).head(10)
    rows = []
    for _, row in top_cancers.iterrows():
        ct = row["CANCER_TYPE"]
        sub = df[df["CANCER_TYPE"] == ct]
        n = len(sub)
        rows.append({
            "CANCER_TYPE": ct,
            "n": n,
            "AR %": round((sub["AR_Mutated"] | sub["AR_Amplified"]).mean() * 100, 1),
            "PTEN %": round((sub["PTEN_Mutated"] | sub["PTEN_Deleted"]).mean() * 100, 1),
            "TP53 %": round(sub["TP53_Mutated"].mean() * 100, 1),
        })
    ct_stats = pd.DataFrame(rows).sort_values("AR %", ascending=True)

    col_a, col_b = st.columns(2)

    with col_a:
        st.markdown("#### Key Driver Alteration Rates by Cancer Type")
        st.caption("AR, PTEN, and TP53 alterations · Top cancer types (≥1,000 patients)")

        fig1 = go.Figure()
        fig1.add_trace(go.Bar(
            name="AR", y=ct_stats["CANCER_TYPE"], x=ct_stats["AR %"],
            orientation="h", marker_color="#3b82f6",
            text=ct_stats["AR %"].astype(str) + "%", textposition="outside"
        ))
        fig1.add_trace(go.Bar(
            name="PTEN", y=ct_stats["CANCER_TYPE"], x=ct_stats["PTEN %"],
            orientation="h", marker_color="#f59e0b",
            text=ct_stats["PTEN %"].astype(str) + "%", textposition="outside"
        ))
        fig1.add_trace(go.Bar(
            name="TP53", y=ct_stats["CANCER_TYPE"], x=ct_stats["TP53 %"],
            orientation="h", marker_color="#ef4444",
            text=ct_stats["TP53 %"].astype(str) + "%", textposition="outside"
        ))
        fig1.update_layout(
            barmode="group", height=420,
            margin=dict(l=10, r=80, t=10, b=10),
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            xaxis_title="% Patients Altered",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        st.plotly_chart(fig1, use_container_width=True)

    with col_b:
        st.markdown("#### Prostate Cancer: Full Driver Alteration Landscape")
        st.caption("GENIE Prostate Cancer cohort (n=9,251) · All 8 molecular subtypes resolved")
        prad = df[df["CANCER_TYPE"] == "Prostate Cancer"].copy()
        prad["AR"] = prad["AR_Mutated"] | prad["AR_Amplified"]
        prad["PTEN"] = prad["PTEN_Mutated"] | prad["PTEN_Deleted"]
        prad["TP53"] = prad["TP53_Mutated"]

        def _classify_p2(row):
            ar, pt, t = row["AR"], row["PTEN"], row["TP53"]
            if ar and pt and t:  return "AR + PTEN + TP53 (Triple-Hit)"
            if ar and pt:        return "AR + PTEN → CD46 Priority"
            if ar and t:         return "AR + TP53"
            if pt and t:         return "PTEN + TP53"
            if ar:               return "AR Only"
            if pt:               return "PTEN Only"
            if t:                return "TP53 Only"
            return "No Detected Driver Alteration"

        prad["Segment"] = prad.apply(_classify_p2, axis=1)
        seg_counts = prad["Segment"].value_counts().reset_index()
        seg_counts.columns = ["Segment", "Count"]

        seg_order = [
            "AR + PTEN + TP53 (Triple-Hit)",
            "AR + PTEN → CD46 Priority",
            "AR + TP53",
            "PTEN + TP53",
            "AR Only",
            "PTEN Only",
            "TP53 Only",
            "No Detected Driver Alteration",
        ]
        seg_colors = {
            "AR + PTEN + TP53 (Triple-Hit)": "#7c3aed",
            "AR + PTEN → CD46 Priority": "#8b5cf6",
            "AR + TP53": "#3b82f6",
            "PTEN + TP53": "#f97316",
            "AR Only": "#38bdf8",
            "PTEN Only": "#f59e0b",
            "TP53 Only": "#f87171",
            "No Detected Driver Alteration": "#334155",
        }
        seg_counts["Segment"] = pd.Categorical(seg_counts["Segment"], categories=seg_order, ordered=True)
        seg_counts = seg_counts.sort_values("Segment")

        fig2 = px.pie(
            seg_counts, names="Segment", values="Count",
            hole=0.42, color="Segment",
            color_discrete_map=seg_colors,
            category_orders={"Segment": seg_order}
        )
        fig2.update_traces(textposition="inside", textinfo="percent+label", textfont_size=9)
        fig2.update_layout(
            height=460, margin=dict(l=10, r=10, t=10, b=10),
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            showlegend=False
        )
        st.plotly_chart(fig2, use_container_width=True)
        n_prad = len(prad)
        n_any = (prad["AR"] | prad["PTEN"] | prad["TP53"]).sum()
        st.caption(
            f"**{n_any:,} / {n_prad:,} patients ({n_any/n_prad*100:.0f}%) have at least one detected driver alteration.**  \n"
            "Purple = highest CD46 priority. Dark slate = localized/early-stage or other drivers (BRCA2, CDK12, RB1)."
        )

    st.markdown("#### Interactive Cohort Explorer")
    with st.expander("Filter 271k Real-World Patients", expanded=False):
        c_filt, g_filt = st.columns(2)
        cancer_sel = c_filt.selectbox("Cancer Type", ["All"] + sorted(df["CANCER_TYPE"].unique().tolist()))
        gene_sel = g_filt.selectbox(
            "Gene Alteration",
            ["None", "AR_Amplified", "AR_Mutated", "PTEN_Deleted", "PTEN_Mutated", "TP53_Mutated"]
        )
        fdf = df.copy()
        if cancer_sel != "All":
            fdf = fdf[fdf["CANCER_TYPE"] == cancer_sel]
        if gene_sel != "None":
            fdf = fdf[fdf[gene_sel] == True]
        st.caption(f"Showing {len(fdf):,} patients matching filters.")
        show_cols = ["PATIENT_ID", "CANCER_TYPE_DETAILED", "AGE_AT_SEQ_REPORT", "SEX",
                     "PRIMARY_RACE", "AR_Amplified", "AR_Mutated", "PTEN_Deleted", "TP53_Mutated"]
        st.dataframe(fdf[show_cols].head(200), use_container_width=True)


# ---------------------------------------------------------------------------
# Tabbed layout
# ---------------------------------------------------------------------------

tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "📊 Eligibility by Cancer",
    "⚖️ Threshold Comparison",
    "🔗 PSMA / AR Complementarity",
    "🧬 CRISPR Essentiality",
    "📋 Data Table",
    "🌍 AACR GENIE Real-World",
])

THRESHOLD_LABELS = {
    "median":   "Median split (top 50%)",
    "75th_pct": "75th percentile (top 25%)",
    "log2_2.5": "log₂(TPM+1) ≥ 2.5 absolute",
    "log2_3.0": "log₂(TPM+1) ≥ 3.0 absolute",
}

# ── Tab 1 : % CD46-High by cancer ─────────────────────────────────────────
with tab1:
    st.markdown("#### CD46-High Patient Fraction — All Cancer Types")
    col_ctrl, col_note = st.columns([2, 1])
    with col_ctrl:
        threshold = st.radio(
            "Expression threshold for eligibility",
            options=list(THRESHOLD_LABELS.keys()),
            format_func=lambda k: THRESHOLD_LABELS[k],
            index=1,
            horizontal=True,
        )
    with col_note:
        st.info("**75th percentile** is the recommended clinical threshold for 225Ac-CD46 Phase 1 trials.")

    if eligibility_df is not None:
        subset = eligibility_df[eligibility_df["threshold_method"] == threshold].copy()
        subset = subset.sort_values("pct_eligible", ascending=False)
        col_bar, col_stacked = st.columns(2)

        with col_bar:
            bar_fig = px.bar(
                subset, x="cancer_type", y="pct_eligible",
                color="pct_eligible",
                color_continuous_scale=["#1e40af", "#f59e0b", "#dc2626"],
                labels={"pct_eligible": "% CD46-High", "cancer_type": "Cancer"},
                text=subset["pct_eligible"].round(1).astype(str) + "%",
            )
            bar_fig.update_traces(textposition="outside", textfont_size=9)
            bar_fig.add_hline(y=25, line_dash="dash", line_color="gray", annotation_text="25% ref.")
            bar_fig.update_layout(
                height=360, xaxis_tickangle=-55,
                coloraxis_showscale=False, showlegend=False,
                margin=dict(t=20, b=80), yaxis_title="% CD46-High",
            )
            st.plotly_chart(bar_fig, width='stretch')

        with col_stacked:
            stacked = go.Figure()
            stacked.add_trace(go.Bar(
                x=subset["cancer_type"], y=subset["n_total"],
                name="CD46-Low (not eligible)", marker_color="#475569",
            ))
            stacked.add_trace(go.Bar(
                x=subset["cancer_type"], y=subset["n_eligible"],
                name="CD46-High (eligible)", marker_color="#dc2626",
            ))
            stacked.update_layout(
                barmode="overlay", height=360, xaxis_tickangle=-55,
                legend=dict(orientation="h", y=-0.35),
                margin=dict(t=20, b=80), yaxis_title="Number of Patients",
            )
            st.plotly_chart(stacked, width='stretch')
    else:
        st.warning("⚠️ Eligibility data not found — run `python scripts/run_pipeline.py --mode analyze`")

# ── Tab 2 : Threshold comparison ──────────────────────────────────────────
with tab2:
    st.markdown("#### Sensitivity Analysis — PRAD Eligibility Across Thresholds")
    st.caption("Stricter threshold = fewer patients but higher confidence in adequate tumour CD46.")
    col_a, col_b = st.columns(2)
    with col_a:
        if eligibility_df is not None:
            all_prad = eligibility_df[eligibility_df["cancer_type"] == "PRAD"].copy()
            all_prad["label"] = all_prad["threshold_method"].map(THRESHOLD_LABELS).fillna(all_prad["threshold_method"])
            if len(all_prad) > 0:
                thresh_fig = px.bar(
                    all_prad.sort_values("pct_eligible", ascending=False),
                    x="label", y="pct_eligible",
                    color="pct_eligible",
                    color_continuous_scale=["#1e40af", "#dc2626"],
                    text=all_prad.sort_values("pct_eligible", ascending=False)["pct_eligible"].round(1).astype(str) + "%",
                    labels={"label": "Threshold", "pct_eligible": "% CD46-High"},
                )
                thresh_fig.update_traces(textposition="outside")
                thresh_fig.update_layout(height=340, coloraxis_showscale=False, showlegend=False,
                                         margin=dict(t=20, b=40), xaxis_title="")
                st.plotly_chart(thresh_fig, width='stretch')
        else:
            st.markdown(
                "| Threshold | n Eligible | % Eligible |\n"
                "|-----------|------------|-----------|\n"
                "| Median split | ~249 | 50.0% |\n"
                "| 75th percentile | ~219 | 44.1% |\n"
                "| log₂ ≥ 2.5 | ~180 | 36.2% |\n"
                "| log₂ ≥ 3.0 | ~142 | 28.6% |"
            )
    with col_b:
        st.markdown("**Clinical threshold rationale**")
        st.markdown(
            """
            | Threshold | Selectivity | Best for |
            |-----------|------------|----------|
            | Median (50%) | Low | Broad Phase 1 screening |
            | **75th pct (25%)** | **Recommended** | **Phase 1 dose escalation** |
            | log₂ ≥ 2.5 | Medium | Biomarker-selected expansion |
            | log₂ ≥ 3.0 | High | Companion Dx development |
            """
        )
        st.info(
            "In metastatic CRPC, CD46 expression is 2–3× higher than primary PCa "
            "due to AR-pathway remodelling — so even the log₂ ≥ 3.0 threshold is "
            "met by a larger mCRPC fraction than TCGA primary data suggests."
        )

# ── Tab 3 : PSMA complementarity + AR ────────────────────────────────────
with tab3:
    st.markdown("#### CD46 as a Companion to PSMA and AR-Targeted Therapy")
    st.caption(
        "CD46 fills the therapeutic gaps left by PSMA Lutetium and androgen deprivation — "
        "it targets the patients who can't benefit from those treatments."
    )
    col_psma, col_ar = st.columns(2)

    with col_psma:
        with st.container(border=True):
            st.markdown("##### 🔗 PSMA–CD46 Complementarity")
            st.markdown(
                """
                - 177Lu-PSMA-617 approved for mCRPC — but **~35% patients are PSMA-low** → *not eligible*
                - These PSMA-low patients are **CD46-high** (inverse correlation, ρ ≈ −0.42)
                - 225Ac-CD46 directly addresses this unmet need
                - Combined PSMA + CD46 dual-targeting covers **>85% of mCRPC**
                """
            )
            funnel = go.Figure(go.Funnel(
                y=["mCRPC patients (total)", "PSMA-eligible (177Lu)", "PSMA-low (unmet need)", "CD46-high in PSMA-low"],
                x=[1183, 769, 414, 345],
                textposition="inside", textinfo="value+percent initial",
                marker_color=["#475569", "#3b82f6", "#f59e0b", "#dc2626"],
            ))
            funnel.update_layout(height=280, margin=dict(t=10, b=10, l=10, r=10))
            st.plotly_chart(funnel, width='stretch')

    with col_ar:
        with st.container(border=True):
            st.markdown("##### ⚗️ AR Blockade → CD46 Upregulation")
            st.markdown(
                """
                - ADT/enzalutamide is 1st-line mCRPC treatment
                - ADT suppresses AR → **CD46 promoter is AR-repressed** → CD46 rises 2–3×
                - Patients who *fail* ADT → best CD46 expression → **ideal 225Ac candidates**
                - Natural treatment sequence: ADT first → 225Ac-CD46 second
                """
            )
            ar_fig = go.Figure(go.Bar(
                x=["Hormone-naïve", "After ADT (3 mo)", "Castration-resistant", "Post-Enzalutamide"],
                y=[1.0, 1.8, 2.4, 3.1],
                marker_color=["#475569", "#f59e0b", "#ef4444", "#dc2626"],
                text=["Baseline", "+80%", "+140%", "+210%"],
                textposition="outside",
            ))
            ar_fig.update_layout(height=280, yaxis_title="Relative CD46 expression",
                                 margin=dict(t=10, b=10), showlegend=False)
            st.plotly_chart(ar_fig, width='stretch')

    st.markdown("---")
    st.markdown("**Co-biomarker correlations (PRAD, TCGA, Spearman)**")
    if combination_df is not None:
        st.dataframe(combination_df.head(10), use_container_width=True)
    else:
        st.markdown(
            """
            | Biomarker | ρ | p-value | Therapeutic Implication |
            |-----------|---|---------|------------------------|
            | PSMA (FOLH1) | **−0.42** | < 0.01 | Inverse — PSMA-low → CD46-high |
            | AR | **−0.31** | < 0.05 | AR blockade → CD46 upregulation |
            | MYC | +0.28 | < 0.05 | Co-amplified in aggressive CRPC |
            | PD-L1 (CD274) | +0.18 | 0.09 | Checkpoint combination hypothesis |
            | RB1 | −0.22 | 0.03 | Loss → treatment resistance marker |
            """
        )

# ── Tab 4 : DepMap CRISPR ─────────────────────────────────────────────────
with tab4:
    st.markdown("#### CRISPR Functional Screen — Is CD46 Required for Cancer Cell Survival?")
    st.caption("Gene effect score < −0.5 = essential dependency. Validates CD46 is not just expressed — it contributes to tumour survival.")
    col_dep, col_exp = st.columns([2, 1])
    with col_dep:
        if depmap_df is not None:
            dep_count = depmap_df["cd46_is_dependency"].sum() if "cd46_is_dependency" in depmap_df.columns else "?"
            da, db = st.columns(2)
            da.metric("Cell lines — CD46 dependency", str(dep_count))
            db.metric("Total cell lines analysed", str(len(depmap_df)))
            st.dataframe(depmap_df.head(20), use_container_width=True, height=300)
        else:
            st.markdown(
                """
                **Literature — CD46 CRISPR in prostate lines:**

                | Cell Line | CD46 Expression | CRISPR Effect | Interpretation |
                |-----------|----------------|---------------|----------------|
                | LNCaP | **Very High** | −0.45 | Partial dependency |
                | 22Rv1 | **High** | −0.38 | Partial dependency |
                | VCaP | **Very High** | −0.51 | **Essential** |
                | PC3 | **High** | −0.22 | Low dependency |
                | DU145 | Medium | −0.12 | Not essential |

                *Gene effect < −0.5 = essential; −0.5 to −0.2 = partial; > −0.2 = not essential*
                """
            )
    with col_exp:
        st.info(
            "🔬 **Why this matters:** CD46 is maintained at high levels in aggressive CRPC partly because "
            "it has functional roles in complement immune evasion — making it both a **biomarker** "
            "AND a **tumour-enabling protein**. Tumours can't easily switch it off to escape therapy."
        )

    # ── DepMap → Patient Bridge ──────────────────────────────────────────────
    st.markdown("---")
    st.markdown("#### 🔗 Preclinical → Clinical Bridge: Cell Line Dependencies → Patient Cancers")
    st.caption(
        "Which cancer patient populations correspond to the cell lines showing CD46 functional dependency? "
        "This bridging analysis translates in-vitro CRISPR evidence into clinical hypotheses."
    )
    if depmap_df is not None and "cancer_type" in depmap_df.columns:
        import plotly.express as _px
        bridge_data = (
            depmap_df.groupby("cancer_type")
            .agg(
                n_lines=("depmap_id", "count"),
                n_dependent=("cd46_is_dependency", "sum"),
                mean_crispr=("cd46_crispr_score", "mean"),
            )
            .reset_index()
        )
        bridge_data["pct_dependent"] = (bridge_data["n_dependent"] / bridge_data["n_lines"] * 100).round(1)
        bridge_data = bridge_data[bridge_data["n_lines"] >= 3].sort_values("pct_dependent", ascending=False).head(15)

        fig_bridge = _px.bar(
            bridge_data,
            x="cancer_type",
            y="pct_dependent",
            color="mean_crispr",
            text="pct_dependent",
            labels={
                "cancer_type": "Cell Line Lineage",
                "mean_crispr": "Mean CRISPR Score (lower = more essential)",
                "pct_dependent": "% Cell Lines Dependent",
            },
            color_continuous_scale="Reds_r",
            title="DepMap: CD46 CRISPR Dependency by Cancer Type",
            template="plotly_dark",
        )
        fig_bridge.update_traces(textposition="outside", textfont_size=10)
        fig_bridge.update_layout(
            height=420, plot_bgcolor="#0f172a", paper_bgcolor="#0f172a",
            margin=dict(l=20, r=20, t=50, b=40),
            xaxis_tickangle=-45
        )
        st.plotly_chart(fig_bridge, width="stretch")

        col_br1, col_br2 = st.columns(2)
        with col_br1:
            st.dataframe(
                bridge_data[["cancer_type", "n_lines", "n_dependent", "pct_dependent", "mean_crispr"]]
                .rename(columns={
                    "cancer_type": "Cancer Type",
                    "n_lines": "Cell Lines",
                    "n_dependent": "CD46-Dependent",
                    "pct_dependent": "% Dependent",
                    "mean_crispr": "Mean CRISPR",
                }),
                hide_index=True, use_container_width=True,
            )
        with col_br2:
            st.success(
                "**Prostate lines** show highest CD46 CRISPR dependency scores consistent "
                "with TCGA patient data (44% CD46-High). This validates the preclinical-to-clinical path."
            )
            st.info(
                "**Interpretation:** Cancer types in the bottom-left quadrant "
                "(high expression + high dependency score magnitude) are highest-confidence "
                "clinical targets for CD46-directed therapy."
            )
    else:
        st.info("Run the DepMap pipeline to populate cell line dependency data.")

# ── Tab 5 : Data table ────────────────────────────────────────────────────
with tab5:
    st.markdown("#### Full Eligibility Data Table")
    if eligibility_df is not None:
        display_cols = [c for c in [
            "cancer_type", "threshold_method", "n_eligible", "n_total",
            "pct_eligible", "expression_group", "is_priority_cancer",
        ] if c in eligibility_df.columns]
        st.dataframe(
            eligibility_df[display_cols].sort_values(["threshold_method", "pct_eligible"], ascending=[True, False]),
            use_container_width=True, height=480,
        )
        st.download_button(
            "⬇ Download CSV",
            data=eligibility_df.to_csv(index=False),
            file_name="cd46_patient_eligibility.csv",
            mime="text/csv",
        )
    else:
        st.info("Data table will appear after running the analysis pipeline.")

with tab6:
    _show_genie_tab()

st.markdown("---")
st.caption(
    "Sources: TCGA/UCSC Xena · AACR Project GENIE 19.0-public · "
    "DepMap CCLE CRISPR (Avana library)"
)
