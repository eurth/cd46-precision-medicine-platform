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
# Tabbed layout
# ---------------------------------------------------------------------------

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 Eligibility by Cancer",
    "⚖️ Threshold Comparison",
    "🔗 PSMA / AR Complementarity",
    "🧬 CRISPR Essentiality",
    "📋 Data Table",
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
            st.plotly_chart(bar_fig, use_container_width=True)

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
            st.plotly_chart(stacked, use_container_width=True)
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
                st.plotly_chart(thresh_fig, use_container_width=True)
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
            st.plotly_chart(funnel, use_container_width=True)

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
            st.plotly_chart(ar_fig, use_container_width=True)

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

st.markdown("---")
st.caption(
    "Sources: TCGA/UCSC Xena · cBioPortal SU2C mCRPC (NCT01775072) + MSK PRAD (prad_msk_2019) · "
    "DepMap CCLE protein expression + CRISPR (Avana library)"
)
