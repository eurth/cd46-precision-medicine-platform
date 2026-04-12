"""Platform Overview — home page content."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import streamlit as st

st.title("🔬 OncoBridge Intelligence")
st.markdown(
    "**Pan-Cancer Target Intelligence Platform · CD46 Case Study · Knowledge Graph + AI Research · EurthTech**"
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
    st.metric("Knowledge Graph Nodes", "3,047", "Genes, drugs, diseases, cohorts")

st.markdown("---")

# ── End-to-End Development Engine ─────────────────────────────────────────────
st.subheader("🔬 End-to-End Development Engine")
st.markdown("From discovery biology to global registration — all evidence in one connected platform.")

st.markdown("""
<style>
.pipeline-stages {
    display: flex; gap: .5rem; margin: .6rem 0 1rem 0; flex-wrap: wrap;
}
.pipe-stage {
    flex: 1; min-width: 170px;
    background: #1e293b; border: 1px solid #334155;
    border-radius: 10px; padding: .9rem 1rem; text-align: center;
}
.pipe-stage .icon { font-size: 1.6rem; }
.pipe-stage .phase { font-size: .72rem; font-weight: 700; letter-spacing: .08em;
                     color: #94a3b8; margin: .2rem 0; }
.pipe-stage .title { font-size: .9rem; font-weight: 700; color: #f8fafc; margin: .2rem 0; }
.pipe-stage .desc  { font-size: .74rem; color: #64748b; margin-top: .3rem; line-height: 1.4; }
.pipe-stage .status-done   { color: #22c55e; font-size: .75rem; font-weight: 700; margin-top:.4rem; }
.pipe-stage .status-active { color: #f97316; font-size: .75rem; font-weight: 700; margin-top:.4rem; }
.pipe-stage .status-ready  { color: #38bdf8; font-size: .75rem; font-weight: 700; margin-top:.4rem; }
.pipe-arrow { display: flex; align-items: center; color: #475569; font-size: 1.4rem;
              padding-top: 1rem; flex-shrink: 0; }
</style>
<div class="pipeline-stages">
  <div class="pipe-stage">
    <div class="icon">🧬</div>
    <div class="phase">PRECLINICAL</div>
    <div class="title">AI-guided Biology</div>
    <div class="desc">CD46 target validation · 797 disease associations · PPI network · 16 isoforms · DepMap CRISPR</div>
    <div class="status-done">✅ Complete</div>
  </div>
  <div class="pipe-arrow">→</div>
  <div class="pipe-stage">
    <div class="icon">⚗️</div>
    <div class="phase">PHASE I</div>
    <div class="title">Safety & Dose</div>
    <div class="desc">HPA dosimetry · Therapeutic index · FOR46 n=56 completed · DLT monitoring protocol</div>
    <div class="status-active">▶ FOR46 Phase I done; 225Ac design-ready</div>
  </div>
  <div class="pipe-arrow">→</div>
  <div class="pipe-stage">
    <div class="icon">📊</div>
    <div class="phase">PHASE II</div>
    <div class="title">Proof-of-Concept</div>
    <div class="desc">OS HR=1.65 (PRAD) · 789 real mCRPC patients · Patient funnel: 11% eligible per 1,000 screened</div>
    <div class="status-ready">◉ Evidence-strong · Design-ready</div>
  </div>
  <div class="pipe-arrow">→</div>
  <div class="pipe-stage">
    <div class="icon">🌍</div>
    <div class="phase">PHASE III</div>
    <div class="title">Global Registration</div>
    <div class="desc">Pluvicto precedent (FDA 2022) · CD46 CAR-T Phase III n=412 · PSMA-low unmet need</div>
    <div class="status-ready">○ Pipeline visibility</div>
  </div>
  <div class="pipe-arrow">→</div>
  <div class="pipe-stage">
    <div class="icon">🏥</div>
    <div class="phase">APPROVAL</div>
    <div class="title">Target 2030</div>
    <div class="desc">Indication: PSMA-low mCRPC post-ARPI · CD46 IHC companion Dx · Accelerated pathway eligible</div>
    <div class="status-ready">○ Strategic milestone</div>
  </div>
</div>
""", unsafe_allow_html=True)

# Per-stage quick-links beneath the pipeline diagram
_nav_cols = st.columns(5)
with _nav_cols[0]:
    st.caption("🧬 Preclinical")
    st.page_link("pages/1_cd46_expression_atlas.py",      label="Expression Atlas")
    st.page_link("pages/4_biomedical_knowledge_graph.py", label="Knowledge Graph")
    st.page_link("pages/10_ppi_network.py",               label="PPI Network")
with _nav_cols[1]:
    st.caption("⚗️ Phase I")
    st.page_link("pages/12_dosimetry_safety.py", label="Dosimetry & Safety")
with _nav_cols[2]:
    st.caption("📊 Phase II")
    st.page_link("pages/2_patient_selection.py",  label="Patient Selection")
    st.page_link("pages/3_survival_outcomes.py",  label="Survival Outcomes")
    st.page_link("pages/8_patient_eligibility.py", label="Patient Eligibility")
with _nav_cols[3]:
    st.caption("🌍 Phase III")
    st.page_link("pages/9_competitive_landscape.py", label="Competitive Landscape")
    st.page_link("pages/11_drug_pipeline.py",        label="Drug Pipeline")
with _nav_cols[4]:
    st.caption("🏥 Approval")
    st.page_link("pages/13_clinical_strategy_engine.py", label="Clinical Strategy Engine")
    st.page_link("pages/14_cd46_diagnostics.py",         label="Diagnostics & Early Detection")

st.markdown("---")
st.subheader("Navigate the Platform")

card_col1, card_col2, card_col3 = st.columns(3)

with card_col1:
    with st.container(border=True):
        st.markdown("### 📊 Expression Atlas")
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

with st.expander("📈 Research Summary — CD46 Target Evidence", expanded=False):
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
    inv1b, inv2b = st.columns(2)
    inv1b.metric("Disease associations (Open Targets)", "772", "CD46 → disease evidence links")
    inv2b.metric("Knowledge Graph nodes", "3,047", "Across 15 node types")

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
