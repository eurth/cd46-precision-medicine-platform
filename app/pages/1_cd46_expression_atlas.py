"""Page 1 — Pan-cancer CD46 Expression Map."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pandas as pd
import streamlit as st
from components.styles import inject_global_css, page_hero

inject_global_css()

# ---------------------------------------------------------------------------
# Page header
# ---------------------------------------------------------------------------

st.markdown(
    page_hero(
        icon="📊",
        module_name="Expression Atlas",
        purpose="Pan-cancer mRNA + protein expression · TCGA (33 cancers) · Human Protein Atlas (30 tissues) · CD46 case study",
        kpi_chips=[
            ("Cancer Types", "33"),
            ("Top Indicator", "PRAD"),
            ("HPA Tissues", "30"),
            ("Threshold", "log₂≥2.5"),
        ],
        source_badges=["TCGA", "HPA"],
    ),
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Load data
# ---------------------------------------------------------------------------

@st.cache_data
def load_expression():
    p = Path("data/processed/cd46_by_cancer.csv")
    return pd.read_csv(p) if p.exists() else None

@st.cache_data
def load_hpa():
    p = Path("data/processed/hpa_cd46_protein.csv")
    return pd.read_csv(p) if p.exists() else None

@st.cache_data
def load_priority():
    p = Path("data/processed/priority_score.csv")
    return pd.read_csv(p) if p.exists() else None

expr_df = load_expression()
hpa_df = load_hpa()
priority_df = load_priority()

# ---------------------------------------------------------------------------
# Summary KPI strip
# ---------------------------------------------------------------------------

k1, k2, k3, k4 = st.columns(4)
k1.metric("Cancer types profiled", "33", "TCGA cohort")
k2.metric("Top indicator", "PRAD", "Prostate highest CD46")
k3.metric("HPA tissues", "30", "Tumor + normal pairs")
k4.metric("Therapeutic threshold", "log₂ ≥ 2.5", "225Ac selection cut-off")

st.markdown("---")

# ---------------------------------------------------------------------------
# Tabbed layout
# ---------------------------------------------------------------------------

tab1, tab2, tab3, tab4 = st.tabs([
    "🔬 mRNA Expression",
    "🧬 Priority Score",
    "🔴 Protein Atlas",
    "📋 Data Table",
])

# ── Tab 1 : mRNA expression bar chart ──────────────────────────────────────
with tab1:
    st.markdown("#### CD46 Median mRNA Expression — Ranked by Cancer Type")
    if expr_df is None:
        st.warning("⚠️ Data not found — run `python scripts/run_pipeline.py --mode analyze`")
        st.info(
            "CD46 is overexpressed in prostate (PRAD), ovarian (OV), and bladder (BLCA) cancers "
            "relative to normal tissue. Median log₂(TPM+1) in PRAD ≈ 4.5."
        )
    else:
        try:
            from src.visualization.cd46_plots import plot_pan_cancer_boxplot

            col_ctrl, col_info = st.columns([2, 1])
            with col_ctrl:
                sort_by = st.radio(
                    "Sort by",
                    ["Median expression", "Priority score", "Cancer type (A-Z)"],
                    horizontal=True,
                )
            with col_info:
                st.info("Bars show median log₂(TPM+1). Dashed line = 225Ac eligibility threshold.")

            fig = plot_pan_cancer_boxplot(expr_df, sort_by=sort_by, return_fig=True)
            fig.update_layout(height=380, margin=dict(t=30, b=60))
            st.plotly_chart(fig, width='stretch')
        except Exception as e:
            st.error(f"Visualization error: {e}")
            st.dataframe(expr_df.head(10))

# ── Tab 2 : Priority heatmap + ranking ─────────────────────────────────────
with tab2:
    st.markdown("#### CD46 Priority Score Heatmap — Top 20 Cancer Types")
    st.caption(
        "Priority score combines expression rank, protein evidence, CNA frequency, "
        "survival impact, and clinical trial activity."
    )
    if priority_df is None:
        st.warning("Priority score data not available.")
        st.markdown(
            """
            | Rank | Cancer | Score | Key Driver |
            |------|--------|-------|------------|
            | 1 | PRAD | 0.61 | High expression + AR upregulation |
            | 2 | LUAD | 0.60 | High expression + survival impact |
            | 3 | COAD | 0.58 | High expression + CRISPR data |
            | 4 | BRCA | 0.53 | Protein evidence + CNA |
            | 5 | BLCA | 0.50 | High expression + tumour microenvironment |
            """
        )
    else:
        try:
            from src.visualization.cd46_plots import plot_priority_heatmap
            col_heat, col_rank = st.columns([3, 2])
            with col_heat:
                fig2 = plot_priority_heatmap(priority_df, return_fig=True)
                fig2.update_layout(height=360, margin=dict(t=30, b=40))
                st.plotly_chart(fig2, width='stretch')
            with col_rank:
                st.markdown("**Top 10 Priority Cancers**")
                top10 = priority_df.sort_values("priority_score", ascending=False).head(10) if "priority_score" in priority_df.columns else priority_df.head(10)
                st.dataframe(top10, use_container_width=True, height=310)
        except Exception as e:
            st.error(f"Priority heatmap error: {e}")

# ── Tab 3 : HPA protein expression ─────────────────────────────────────────
with tab3:
    st.markdown("#### CD46 Protein Expression — Tumor vs Normal Tissues")
    if hpa_df is None:
        st.warning("⚠️ HPA data not found.")
        col_tum, col_norm = st.columns(2)
        with col_tum:
            st.markdown(
                "**Tumor tissues (high CD46):**\n"
                "- Prostate → **High**\n"
                "- Ovary → **High**\n"
                "- Bladder → **High**\n"
                "- Breast → Medium\n"
                "- Colon → Medium"
            )
        with col_norm:
            st.markdown(
                "**Normal tissues (reference):**\n"
                "- Kidney → High (physiological)\n"
                "- Liver → Medium\n"
                "- Brain → Low\n"
                "- Bone marrow → Low\n"
                "- Skeletal muscle → Low"
            )
        st.info(
            "225Ac-CD46 selectivity depends on differential expression: "
            "tumour HIGH vs normal LOW/MEDIUM. Kidney is the primary normal-tissue concern."
        )
    else:
        try:
            from src.visualization.cd46_plots import plot_hpa_protein
            col_l, col_r = st.columns(2)
            with col_l:
                fig3 = plot_hpa_protein(hpa_df, return_fig=True)
                fig3.update_layout(height=360, margin=dict(t=30, b=40))
                st.plotly_chart(fig3, width='stretch')
            with col_r:
                st.markdown("**Interpretation**")
                st.markdown(
                    """
                    - **Prostate, Lung, Ovary, Bladder** show highest tumour staining (score 3)
                    - **Kidney** shows highest normal-tissue staining — dosimetry concern
                    - Tumour-to-normal ratio drives therapeutic window
                    - IHC score 0–3: Not detected / Low / Medium / High
                    """
                )
                st.dataframe(hpa_df, use_container_width=True, height=240)
        except Exception as e:
            st.error(f"HPA plot error: {e}")
            st.dataframe(hpa_df)

# ── Tab 4 : Raw data table ──────────────────────────────────────────────────
with tab4:
    if expr_df is not None:
        st.markdown("#### Raw Expression Statistics by Cancer Type")
        st.dataframe(expr_df, use_container_width=True, height=450)
        st.download_button(
            "⬇ Download CSV",
            data=expr_df.to_csv(index=False),
            file_name="cd46_expression_by_cancer.csv",
            mime="text/csv",
        )
    else:
        st.info("Data table will appear after running the analysis pipeline.")

st.markdown("---")
st.caption(
    "Sources: TCGA gene expression via UCSC Xena (RNAseqv2, log₂(TPM+1)) · "
    "Human Protein Atlas IHC (antibody-based: Not detected / Low / Medium / High)"
)
