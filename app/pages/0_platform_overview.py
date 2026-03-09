"""Platform Overview — home page content."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import streamlit as st

st.title("🔬 CD46 Precision Medicine Platform")
st.markdown(
    "**225Ac-CD46 Radiopharmaceutical Therapy | Pan-Cancer Evidence Platform | Research Use**"
)
st.markdown("---")

# Hero metrics
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("mCRPC CD46-High (75th percentile)", "~44%", "Primary target population")
with col2:
    st.metric("Cancer Types Analysed", "25", "TCGA pan-cancer cohort")
with col3:
    st.metric("Total Patients Profiled", "~2,800", "CD46 expression sequenced")
with col4:
    st.metric("Knowledge Graph Nodes", "1,701", "Genes, drugs, diseases, cohorts")

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

# ---------------------------------------------------------------------------
# Investor Summary
# ---------------------------------------------------------------------------

with st.expander("📈 Investor Summary — 225Ac-CD46 Target Evidence", expanded=False):
    st.markdown(
        """
        ### Why CD46 as a Radiopharmaceutical Target?

        CD46 (Membrane Cofactor Protein) is a complement-regulatory surface protein
        **significantly overexpressed** in multiple solid tumours relative to normal tissue.
        Unlike PSMA — the current gold-standard RLT target — CD46 is pan-tumour and
        expressed in PSMA-low/negative disease, representing a **distinct and complementary
        patient population**.
        """
    )

    inv1, inv2, inv3, inv4 = st.columns(4)
    inv1.metric("Cancer types with elevated CD46", "25", "TCGA pan-cancer (public data)")
    inv2.metric("Active CD46 clinical trials", "14", "ClinicalTrials.gov, March 2026")
    inv3.metric("Cell lines profiled (DepMap)", "1,186", "CRISPR + expression")
    inv4.metric("Peer-reviewed publications", "55", "PubMed, CD46 oncology")

    st.markdown("**Top 5 Indications by CD46 Expression (TCGA)**")

    import pandas as pd
    from pathlib import Path as _Path
    _p = _Path("data/processed/cd46_by_cancer.csv")
    if _p.exists():
        _df = pd.read_csv(_p).sort_values("expression_rank").head(5)
        _cancer_labels = {
            "LUAD": "Lung Adenocarcinoma", "PRAD": "Prostate Adenocarcinoma",
            "COAD": "Colorectal Adenocarcinoma", "BRCA": "Breast Carcinoma",
            "BLCA": "Bladder Urothelial Carcinoma", "ACC": "Adrenocortical Carcinoma",
        }
        _df["Label"] = _df["cancer_type"].map(lambda c: f"{c} — {_cancer_labels.get(c, c)}")
        st.dataframe(
            _df[["Label", "cd46_median", "expression_rank", "n_samples"]].rename(
                columns={"Label": "Cancer Type", "cd46_median": "Median log\u2082 TPM",
                         "expression_rank": "CD46 Rank", "n_samples": "TCGA Patients"}
            ).reset_index(drop=True),
            use_container_width=True,
            hide_index=True,
        )

    st.markdown(
        """
        **Why CD46 Adds Value in a Crowded RLT Market**
        - PSMA-targeted RLT (Pluvicto) is FDA-approved but leaves **~30–40% of mCRPC patients** with low/absent PSMA unserved
        - CD46 is **independently overexpressed** in PSMA-low disease — not a competitor to PSMA, a complement
        - **Complement evasion** mechanism provides a novel biological rationale distinct from all approved RLT
        - 14 active NCT trials validate CD46 as a de-risked, druggable target
        - Alpha-particle payload (²²⁵Ac) delivers ~4 orders of magnitude higher LET than ¹⁷⁷Lu beta therapy
        """
    )
    st.caption(
        "All data sourced from publicly available datasets: TCGA, HPA, DepMap, ClinicalTrials.gov, PubMed. "
        "For research and demonstration purposes only."
    )

st.markdown("---")
st.markdown(
    "<div style='color:#64748b; font-size:0.8em;'>"
    "Data: TCGA/UCSC Xena · Human Protein Atlas · cBioPortal mCRPC · DepMap CRISPR · "
    "ClinicalTrials.gov · ChEMBL · Open Targets | Phase 2: AACR GENIE (requires Synapse DUA)"
    "</div>",
    unsafe_allow_html=True,
)
