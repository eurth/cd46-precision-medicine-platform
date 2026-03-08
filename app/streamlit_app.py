"""
CD46 Precision Medicine Platform — navigation controller.

Run: streamlit run app/streamlit_app.py
"""
import sys
from pathlib import Path

# Ensure project root on path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import streamlit as st

st.set_page_config(
    page_title="CD46 Precision Medicine Platform",
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
          <h2 style="color:#38bdf8; margin:0;">🔬 CD46 Platform</h2>
          <p style="color:#64748b; font-size:0.8em; margin:4px 0;">
            Prof. Bobba Naidu Research Program
          </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("---")
    st.markdown("**Integrated Data Sources**")
    st.markdown(
        """
        - ✅ TCGA Pan-Cancer Cohort (33 cancers, ~11K patients)
        - ✅ Human Protein Atlas (30 tissues)
        - ✅ mCRPC Clinical Cohort (n=1,183)
        - ✅ CRISPR Functional Screen (DepMap)
        - ✅ ClinicalTrials.gov
        - ✅ Drug-Target Database (ChEMBL)
        - ✅ Open Targets Disease Evidence
        - 🔜 AACR GENIE Genomics (Phase 2)
        """
    )

    st.markdown("---")
    st.markdown(
        """
        <div style="color:#64748b; font-size:0.75em;">
          <b>Target Gene:</b> CD46 (Membrane Cofactor Protein)<br>
          <b>Chromosome:</b> 1q32.2<br>
          <b>Biology:</b> Complement C3b/C4b regulator<br>
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
            st.Page("pages/1_cd46_expression_atlas.py", title="CD46 Expression Atlas", icon="📊"),
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
    }
)
pg.run()
