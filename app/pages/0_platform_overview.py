"""Platform Overview — home page content."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import streamlit as st

st.title("🔬 CD46 Precision Medicine Platform")
st.markdown(
    "**225Ac-CD46 Radioimmunotherapy Research | Prof. Bobba Naidu | Phase 1 Analysis**"
)
st.markdown("---")

# Hero metrics
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("mCRPC CD46-High (75th percentile)", "~44%", "Primary target population")
with col2:
    st.metric("Cancer Types Analysed", "33", "Full TCGA pan-cancer cohort")
with col3:
    st.metric("Total Patients Profiled", "~11,000", "CD46 expression sequenced")
with col4:
    st.metric("Knowledge Graph Nodes", "1,452", "Genes, drugs, diseases, cohorts")

st.markdown("---")
st.subheader("Navigate the Platform")

card_col1, card_col2, card_col3 = st.columns(3)

with card_col1:
    with st.container(border=True):
        st.markdown("### 📊 CD46 Expression Atlas")
        st.markdown(
            "Pan-cancer CD46 mRNA + protein expression across 33 TCGA cancers "
            "and 30 Human Protein Atlas tissues. Ranked expression, heatmaps, "
            "tumor vs normal comparisons."
        )
        st.page_link("pages/1_cd46_expression_atlas.py", label="Open Expression Atlas →")

    with st.container(border=True):
        st.markdown("### 🎯 Patient Selection Criteria")
        st.markdown(
            "CD46-High patient proportions at 4 expression thresholds across all cancers. "
            "DepMap CRISPR functional validation. Biomarker co-expression landscape from "
            "mCRPC clinical cohort."
        )
        st.page_link("pages/2_patient_selection.py", label="Open Patient Selection →")

with card_col2:
    with st.container(border=True):
        st.markdown("### 📈 Survival Outcomes")
        st.markdown(
            "Kaplan-Meier survival curves and Cox proportional hazard forest plot "
            "for all 33 cancer types. Overall Survival and Progression-Free Interval "
            "endpoints. CD46-High vs CD46-Low stratification."
        )
        st.page_link("pages/3_survival_outcomes.py", label="Open Survival Outcomes →")

    with st.container(border=True):
        st.markdown("### 🕸️ Biomedical Knowledge Graph")
        st.markdown(
            "Interactive network of genes, proteins, diseases, drugs, patient cohorts, "
            "and biological pathways. Tabbed query explorer with 15+ preset queries "
            "covering all dimensions of CD46 biology."
        )
        st.page_link("pages/4_biomedical_knowledge_graph.py", label="Open Knowledge Graph →")

with card_col3:
    with st.container(border=True):
        st.markdown("### 🤖 Research Assistant")
        st.markdown(
            "GPT-4o powered natural language interface with integrated context from "
            "all datasets and the knowledge graph. Ask clinical or biological questions "
            "and receive data-grounded answers."
        )
        st.page_link("pages/5_research_assistant.py", label="Open Research Assistant →")

    with st.container(border=True):
        st.markdown("### 📋 Key Findings")
        st.markdown(
            """
            - **PRAD, OV, BLCA** are top priority indications
            - **PSMA-CD46 complementarity**: 35% of mCRPC are PSMA-low CD46-high
            - **Androgen blockade** upregulates CD46 — resistance mechanism
            - **225Ac alpha particles**: 4 orders of magnitude higher LET than beta
            - **Median OS HR**: 0.77 in PRAD (CD46-High protective in primary PCa)
            """
        )

st.markdown("---")
st.markdown(
    "<div style='color:#64748b; font-size:0.8em;'>"
    "Data: TCGA/UCSC Xena · Human Protein Atlas · cBioPortal mCRPC · DepMap CRISPR · "
    "ClinicalTrials.gov · ChEMBL · Open Targets | Phase 2: AACR GENIE (requires Synapse DUA)"
    "</div>",
    unsafe_allow_html=True,
)
