"""
CD46 Precision Medicine Platform — navigation controller.

Run: streamlit run app/streamlit_app.py
"""
import sys
from pathlib import Path

# Ensure project root and app/ dir are both on path
_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent))  # project root
sys.path.insert(0, str(_HERE))         # app/ dir (for utils.tracker etc.)

import streamlit as st
from utils.tracker import log_page_visit

st.set_page_config(
    page_title="OncoBridge Intelligence",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Sidebar branding
# ---------------------------------------------------------------------------

with st.sidebar:
    st.markdown(
        """
        <div style="text-align: center; padding: 8px 0 16px;">
          <h2 style="color:#38bdf8; margin:0;">🔬 OncoBridge Intelligence</h2>
          <p style="color:#64748b; font-size:0.8em; margin:4px 0;">
            Pan-Cancer Target Intelligence · EurthTech Research
          </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("---")
    st.markdown("**Integrated Data Sources** _(CD46 case study)_")
    st.markdown(
        """
        - ✅ TCGA Pan-Cancer Cohort (25 cancers, ~2,800 patients)
        - ✅ Human Protein Atlas (81 tissues)
        - ✅ mCRPC Clinical Cohort (n=226)
        - ✅ CRISPR Functional Screen (DepMap, 1,186 cell lines)
        - ✅ ClinicalTrials.gov (14 CD46 RLT trials)
        - ✅ Drug-Target Database (ChEMBL)
        - ✅ Open Targets Disease Evidence (772 associations)
        - ✅ STRING DB PPI Network (30 partners, 103 interactions)
        - ✅ Drug Pipeline (10 agents, 3 classes)
        - 🔜 AACR GENIE Genomics (Phase 2)
        """
    )

    st.markdown("---")
    st.markdown(
        """
        <div style="color:#64748b; font-size:0.75em;">
          <b>Case Study Target:</b> CD46 (Membrane Cofactor Protein)<br>
          <b>Chromosome:</b> 1q32.2<br>
          <b>Biology:</b> Complement C3b/C4b regulator · immune evasion<br>
          <b>Therapeutic modality:</b> 225Ac alpha-particle radioimmunotherapy
        </div>
        """,
        unsafe_allow_html=True,
    )

# ---------------------------------------------------------------------------
# Navigation — controls the left-nav labels and page routing
# ---------------------------------------------------------------------------
pg = st.navigation(
    {
        "Overview": [
            st.Page(
                "pages/0_platform_overview.py",
                title="Platform Overview",
                icon="🔬",
                default=True,
            ),
        ],
        "Research Modules": [
            st.Page("pages/1_cd46_expression_atlas.py", title="Expression Atlas", icon="📊"),
            st.Page("pages/2_patient_selection.py", title="Patient Selection", icon="🎯"),
            st.Page("pages/3_survival_outcomes.py", title="Survival Outcomes", icon="📈"),
            st.Page(
                "pages/4_biomedical_knowledge_graph.py",
                title="Biomedical Knowledge Graph",
                icon="🕸️",
            ),
            st.Page("pages/5_research_assistant.py", title="Research Assistant", icon="🤖"),
            st.Page("pages/6_biomarker_panel.py", title="Biomarker Panel", icon="🧬"),
            st.Page("pages/7_kg_query_explorer.py", title="KG Query Explorer", icon="🔍"),
        ],
        "Clinical Tools": [
            st.Page("pages/8_patient_eligibility.py", title="Patient Eligibility Scorer", icon="🎯"),
            st.Page("pages/9_competitive_landscape.py", title="Competitive Landscape", icon="🏆"),
        ],
        "Biology & Pipeline": [
            st.Page("pages/10_ppi_network.py", title="PPI Network Explorer", icon="🕸️"),
            st.Page("pages/11_drug_pipeline.py", title="Drug Pipeline", icon="💊"),
            st.Page("pages/12_dosimetry_safety.py", title="Dosimetry & Safety Index", icon="⚗️"),
        ],
        "Clinical Strategy": [
            st.Page("pages/13_clinical_strategy_engine.py", title="Clinical Strategy Engine", icon="🔬"),
            st.Page("pages/14_cd46_diagnostics.py", title="Diagnostics & Early Detection", icon="🧪"),
        ],
        # Zero-width-space key → invisible group header; CSS below hides the link too
        "​": [
            st.Page("pages/99_admin_logs.py", title="Admin Logs", icon="🔒"),
        ],
    }
)

# Hide admin page from sidebar nav (accessible via direct URL only)
st.markdown(
    """
    <style>
    /* Hide the Admin Logs nav link and its parent list item */
    section[data-testid="stSidebar"] a[href*="Admin_Logs"],
    section[data-testid="stSidebar"] a[href*="admin_logs"],
    section[data-testid="stSidebar"] li:has(a[href*="Admin_Logs"]),
    section[data-testid="stSidebar"] li:has(a[href*="admin_logs"]) {
        display: none !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

log_page_visit(pg.title or "Unknown")
pg.run()
