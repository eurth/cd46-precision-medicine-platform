"""
OncoBridge UI kit — themed native Streamlit/HTML components.

Pages import from here only. No shadcn iframes (Clinical Slate light theme).
"""
from __future__ import annotations

import hashlib
import html
import sys
from contextlib import contextmanager
from pathlib import Path

_APP = Path(__file__).resolve().parents[1]
if str(_APP) not in sys.path:
    sys.path.insert(0, str(_APP))

import streamlit as st

from components.theme import (
    BORDER,
    PRIMARY,
    PRIMARY_SOFT,
    TEXT,
    TEXT_FAINT,
    TEXT_MUTED,
)

_BANNER_VARIANTS = {
    "info": (PRIMARY_SOFT, PRIMARY, "#1E40AF"),
    "warning": ("#FEF3C7", "#D97706", "#92400E"),
    "error": ("#FEE2E2", "#DC2626", "#991B1B"),
    "success": ("#D1FAE5", "#059669", "#065F46"),
}

# First page per sidebar dimension group (st.page_link paths)
_DIMENSION_LINKS: list[tuple[str, str]] = [
    ("Home", "pages/0_platform_overview.py"),
    ("Target", "pages/1_cd46_expression_atlas.py"),
    ("Biomarkers", "pages/6_biomarker_panel.py"),
    ("Proteins", "pages/10_ppi_network.py"),
    ("Patients", "pages/2_patient_selection.py"),
    ("Drugs", "pages/11_drug_pipeline.py"),
    ("Survival", "pages/3_survival_outcomes.py"),
    ("Graph", "pages/4_biomedical_knowledge_graph.py"),
    ("Strategy", "pages/13_clinical_strategy_engine.py"),
]

_PAGE_DIMENSION: dict[str, str] = {
    "Platform Overview": "Home",
    "Expression Atlas": "Target / Cancer",
    "Compare Targets": "Target / Cancer",
    "Biomarker Panel": "Biomarkers",
    "PPI Network Explorer": "Proteins",
    "Diagnostics & Early Detection": "Proteins",
    "Patient Selection": "Patients",
    "Eligibility Scorer": "Patients",
    "Drug Pipeline": "Drugs / Safety",
    "Dosimetry & Safety Index": "Drugs / Safety",
    "Survival Outcomes": "Survival",
    "Knowledge Graph": "Graph / Ask",
    "KG Query Explorer": "Graph / Ask",
    "Research Assistant": "Graph / Ask",
    "Clinical Strategy Engine": "Strategy",
}

_TITLE_PATHS: dict[str, str] = {
    "Platform Overview": "pages/0_platform_overview.py",
    "Expression Atlas": "pages/1_cd46_expression_atlas.py",
    "Patient Selection": "pages/2_patient_selection.py",
    "Survival Outcomes": "pages/3_survival_outcomes.py",
    "Knowledge Graph": "pages/4_biomedical_knowledge_graph.py",
    "Research Assistant": "pages/5_research_assistant.py",
    "Biomarker Panel": "pages/6_biomarker_panel.py",
    "KG Query Explorer": "pages/7_kg_query_explorer.py",
    "Eligibility Scorer": "pages/8_patient_eligibility.py",
    "Compare Targets": "pages/9_competitive_landscape.py",
    "PPI Network Explorer": "pages/10_ppi_network.py",
    "Drug Pipeline": "pages/11_drug_pipeline.py",
    "Dosimetry & Safety Index": "pages/12_dosimetry_safety.py",
    "Clinical Strategy Engine": "pages/13_clinical_strategy_engine.py",
    "Diagnostics & Early Detection": "pages/14_cd46_diagnostics.py",
}

_RECENT_KEY = "ob_recent_pages"
_MAX_RECENT = 3


def apply_theme() -> None:
    """Reserved hook — global theme lives in styles.inject_global_css()."""
    pass


def shadcn_available() -> bool:
    """Deprecated: we use native themed components."""
    return False


def page_header(
    icon: str,
    module_name: str,
    purpose: str,
    kpi_chips: list[tuple[str, str]],
    source_badges: list[str],
) -> None:
    """Module page header — delegates to styles.page_hero."""
    from components.styles import page_hero

    st.markdown(
        page_hero(icon, module_name, purpose, kpi_chips, source_badges),
        unsafe_allow_html=True,
    )


def dimension_rail() -> None:
    """Compact dimension wayfinding row (~36px) under the target bar."""
    st.markdown('<div class="ob-dim-rail">', unsafe_allow_html=True)
    st.markdown(
        '<span class="ob-dim-rail-label">Dimension</span>',
        unsafe_allow_html=True,
    )
    cols = st.columns(len(_DIMENSION_LINKS))
    for col, (label, path) in zip(cols, _DIMENSION_LINKS):
        with col:
            try:
                st.page_link(path, label=label, use_container_width=True)
            except TypeError:
                st.page_link(path, label=label)
    st.markdown("</div>", unsafe_allow_html=True)


@contextmanager
def filter_bar(title: str = "Filters", *, expanded: bool = True):
    """Collapsible filter region for analytical pages."""
    with st.expander(title, expanded=expanded):
        yield


def breadcrumb(page_title: str | None) -> None:
    """Home › dimension › current module."""
    if not page_title or page_title in ("Platform Overview", "Unknown", "Admin Logs"):
        return
    dim = _PAGE_DIMENSION.get(page_title, "Research")
    st.markdown(
        f'<nav class="ob-crumb" aria-label="Breadcrumb">'
        f"Home &rsaquo; {html.escape(dim)} &rsaquo; "
        f'<span class="ob-crumb-cur">{html.escape(page_title)}</span>'
        f"</nav>",
        unsafe_allow_html=True,
    )


def track_recent_page(page_title: str | None) -> None:
    """Remember last few modules for sidebar quick return."""
    if not page_title or page_title in ("Unknown", "Admin Logs"):
        return
    recent: list[str] = st.session_state.get(_RECENT_KEY, [])
    recent = [t for t in recent if t != page_title]
    recent.insert(0, page_title)
    st.session_state[_RECENT_KEY] = recent[:_MAX_RECENT]


def render_recent_modules() -> None:
    """Sidebar list of recently visited modules."""
    recent: list[str] = st.session_state.get(_RECENT_KEY, [])
    if not recent:
        return
    st.markdown('<div class="ob-recent">', unsafe_allow_html=True)
    st.markdown('<div class="ob-recent-title">Recent modules</div>', unsafe_allow_html=True)
    for title in recent:
        path = _TITLE_PATHS.get(title)
        if path:
            try:
                st.page_link(path, label=title)
            except TypeError:
                st.page_link(path, label=title)
        else:
            st.caption(f"· {title}")
    st.markdown("</div>", unsafe_allow_html=True)


def export_research_pack(
    df,
    *,
    key: str,
    label: str = "Download research pack (ZIP)",
    result_name: str = "results.csv",
) -> None:
    """ZIP export: table + data freeze + NOTICE + CITATION."""
    if df is None or getattr(df, "empty", True):
        return
    from components.export_pack import build_export_pack
    from components.targets import get_active_symbol

    pack = build_export_pack(
        df,
        active_target=get_active_symbol(),
        result_name=result_name,
    )
    st.download_button(
        label,
        data=pack,
        file_name="oncobridge_research_export.zip",
        mime="application/zip",
        key=key,
    )


def _metric_card_html(title: str, content: str, description: str = "") -> str:
    desc = (
        f'<div class="ob-kpi-desc">{html.escape(description)}</div>'
        if description
        else ""
    )
    return (
        f'<div class="ob-kpi-card">'
        f'<div class="ob-kpi-title">{html.escape(title)}</div>'
        f'<div class="ob-kpi-value">{html.escape(content)}</div>'
        f"{desc}"
        f"</div>"
    )


def metric_row(items: list[dict[str, str]], *, key_prefix: str = "kpi") -> None:
    """Render a row of KPI cards on the page surface color."""
    if not items:
        return
    cols = st.columns(len(items))
    for i, (col, item) in enumerate(zip(cols, items)):
        with col:
            st.markdown(
                _metric_card_html(
                    item["title"],
                    item["content"],
                    item.get("description", ""),
                ),
                unsafe_allow_html=True,
            )


def section_tabs(
    options: list[str],
    *,
    key: str,
    default: str | None = None,
) -> str:
    """Compact horizontal section selector (styled native radio)."""
    if not options:
        return ""
    default_val = default or options[0]
    idx = options.index(default_val) if default_val in options else 0
    return st.radio(
        "Section",
        options=options,
        index=idx,
        horizontal=True,
        key=f"ob_tabs_{key}",
        label_visibility="collapsed",
    )


def info_banner(message: str, *, variant: str = "info") -> None:
    """Themed callout — same surface family as the page."""
    bg, border, fg = _BANNER_VARIANTS.get(variant, _BANNER_VARIANTS["info"])
    uid = hashlib.md5(f"{variant}:{message}".encode()).hexdigest()[:8]
    st.markdown(
        f'<div class="ob-banner" id="ob-banner-{uid}" '
        f'style="background:{bg};border-color:{border};color:{fg};">'
        f"{message}</div>",
        unsafe_allow_html=True,
    )


def assert_ui_kit_smoke() -> None:
    assert callable(metric_row)
    assert callable(section_tabs)
    assert callable(page_header)
    assert callable(dimension_rail)
    assert callable(breadcrumb)
    assert callable(export_research_pack)
    assert "ob-kpi-card" in _metric_card_html("T", "1", "d")
    assert len(_DIMENSION_LINKS) == 9


if __name__ == "__main__":
    assert_ui_kit_smoke()
    print("ui_kit_smoke_ok")
