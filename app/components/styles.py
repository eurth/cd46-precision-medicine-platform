"""
Shared presentation — inject CSS and page hero HTML.
"""
from __future__ import annotations

import streamlit as st

from components.theme import TEXT_MUTED
from components.theme_css import global_css

_BADGE_COLORS = {
    "TCGA": "#2563EB", "HPA": "#7C3AED", "DepMap": "#059669", "ChEMBL": "#D97706",
    "GENIE": "#DB2777", "UniProt": "#4F46E5", "STRING": "#0891B2", "OpenTargets": "#16A34A",
    "ClinicalTrials": "#DC2626", "cBioPortal": "#EA580C", "mCRPC": "#64748B",
    "GTEx": "#9333EA", "ClinVar": "#E11D48",
}


def inject_global_css() -> None:
    """Inject platform CSS + top app bar."""
    st.markdown(global_css(), unsafe_allow_html=True)
    st.markdown(
        '<div id="ob-topbar">'
        '<div class="ob-tb-sidebar-zone">'
        '<span class="ob-tb-brand">OncoBridge Intelligence</span>'
        '</div>'
        '<div class="ob-tb-main-zone">'
        '<span class="ob-tb-ctx">Open theranostics research · multi-target workbench</span>'
        '<span class="ob-tb-spacer"></span>'
        '<span class="ob-tb-live"><span class="ob-tb-dot"></span>Research data live</span>'
        '</div>'
        '</div>',
        unsafe_allow_html=True,
    )


def page_hero(
    icon: str,
    module_name: str,
    purpose: str,
    kpi_chips: list[tuple[str, str]],
    source_badges: list[str],
) -> str:
    """Return HTML for the module page hero."""
    chip_html = "".join(
        f'<div class="hero-chip"><span class="chip-val">{value}</span>'
        f'<span class="chip-lbl">{label}</span></div>'
        for label, value in kpi_chips
    )
    badge_html = "".join(
        f'<span class="src-badge">'
        f'<span style="display:inline-block;width:6px;height:6px;border-radius:50%;'
        f'background:{_BADGE_COLORS.get(src, TEXT_MUTED)};margin-right:5px;"></span>'
        f'{src}</span>'
        for src in source_badges
    )
    return (
        '<div class="page-hero">'
        f'<div class="hero-top"><span class="hero-icon">{icon}</span>'
        f'<h1 class="hero-title">{module_name}</h1></div>'
        f'<div class="hero-purpose">{purpose}</div>'
        f'<div class="hero-chips">{chip_html}</div>'
        f'<div class="hero-badges">{badge_html}</div>'
        '</div>'
    )
