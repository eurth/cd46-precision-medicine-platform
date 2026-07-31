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
from components.styles import inject_global_css
from components.ui_kit import apply_theme, breadcrumb, render_recent_modules, track_recent_page
from components.right_rail import render_floating_right_rail, sync_target_from_query
from components.sidebar_nav import inject_sidebar_nav_defaults

st.set_page_config(
    page_title="OncoBridge Intelligence",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="auto",
)

inject_global_css()
apply_theme()

# ---------------------------------------------------------------------------
# Research target — PRIMARY control (main area, sticky). Sidebar is a mirror.
# ---------------------------------------------------------------------------
from components.targets import render_sidebar_target_selector
from components.feedback import render_sidebar_feedback

# ---------------------------------------------------------------------------
# Navigation — dimension-grouped (all pages retained)
# ---------------------------------------------------------------------------
pg = st.navigation(
    {
        "Home": [
            st.Page(
                "pages/0_platform_overview.py",
                title="Platform Overview",
                icon="🔬",
                default=True,
            ),
        ],
        "Target / Cancer": [
            st.Page("pages/1_cd46_expression_atlas.py", title="Expression Atlas", icon="📊"),
            st.Page("pages/9_competitive_landscape.py", title="Compare Targets", icon="🏆"),
        ],
        "Biomarkers": [
            st.Page("pages/6_biomarker_panel.py", title="Biomarker Panel", icon="🧬"),
        ],
        "Proteins": [
            st.Page("pages/10_ppi_network.py", title="PPI Network Explorer", icon="🕸️"),
            st.Page("pages/14_cd46_diagnostics.py", title="Diagnostics & Early Detection", icon="🧪"),
        ],
        "Patients": [
            st.Page("pages/2_patient_selection.py", title="Patient Selection", icon="🎯"),
            st.Page("pages/8_patient_eligibility.py", title="Eligibility Scorer", icon="🎯"),
        ],
        "Drugs / Safety": [
            st.Page("pages/11_drug_pipeline.py", title="Drug Pipeline", icon="💊"),
            st.Page("pages/12_dosimetry_safety.py", title="Dosimetry & Safety Index", icon="⚗️"),
        ],
        "Survival": [
            st.Page("pages/3_survival_outcomes.py", title="Survival Outcomes", icon="📈"),
        ],
        "Graph / Ask": [
            st.Page(
                "pages/4_biomedical_knowledge_graph.py",
                title="Knowledge Graph",
                icon="🕸️",
            ),
            st.Page("pages/7_kg_query_explorer.py", title="KG Query Explorer", icon="🔍"),
            st.Page("pages/5_research_assistant.py", title="Research Assistant", icon="🤖"),
        ],
        "Strategy": [
            st.Page("pages/13_clinical_strategy_engine.py", title="Clinical Strategy Engine", icon="🔬"),
        ],
        # Zero-width-space key → invisible group header; CSS below hides the link too
        "​": [
            st.Page("pages/99_admin_logs.py", title="Admin Logs", icon="🔒"),
        ],
    }
)

breadcrumb(pg.title)
track_recent_page(pg.title)

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
sync_target_from_query()
pg.run()

inject_sidebar_nav_defaults(pg.title)

with st.sidebar:
    render_sidebar_target_selector()
    render_recent_modules()
    render_sidebar_feedback()

# ponytail: HTML dock after pg.run(); sync_target_from_query runs before pg.run()
render_floating_right_rail()
