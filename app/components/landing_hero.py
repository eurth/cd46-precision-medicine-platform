"""U2 landing — target spotlight tabs + quick-start row."""
from __future__ import annotations

import html as html_lib

import streamlit as st

from components.target_narratives import strategy_context
from components.targets import data_tier, get_active_symbol, is_case_study, list_symbols


def _slide_body(sym: str) -> str:
    ctx = strategy_context(sym)
    tier = data_tier(sym)
    case = " · deep case study" if is_case_study(sym) else ""
    return (
        f'<div class="lp-spotlight">'
        f'<div class="lp-carousel-tag">Research target</div>'
        f'<div class="lp-carousel-gene">{html_lib.escape(sym)}</div>'
        f'<div class="lp-carousel-name">{html_lib.escape(ctx["name"])}</div>'
        f'<div class="lp-carousel-line">'
        f'{html_lib.escape(ctx["indication"])} · {html_lib.escape(ctx["modality"])}'
        f"</div>"
        f'<div class="lp-carousel-meta">'
        f"Data tier: {html_lib.escape(tier)}{html_lib.escape(case)}"
        f" · {html_lib.escape(ctx['trial_focus'])}"
        f"</div>"
        f'<div class="lp-carousel-hint-inline">'
        f"Active selection: <strong>{html_lib.escape(get_active_symbol())}</strong> (right rail)"
        f"</div>"
        f"</div>"
    )


def render_target_carousel() -> None:
    """Target spotlight tabs — always visible (no empty CSS carousel)."""
    symbols = list_symbols()
    tabs = st.tabs(symbols)
    for sym, tab in zip(symbols, tabs):
        with tab:
            st.markdown(_slide_body(sym), unsafe_allow_html=True)


def render_start_here() -> None:
    """Three high-value entry points for demos."""
    st.markdown('<div class="lp-start-label">Start here</div>', unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(
            '<div class="lp-start-card lp-start-ind">'
            '<div class="lp-start-title">Compare Targets</div>'
            '<div class="lp-start-desc">All five genes side-by-side — lead every demo here.</div>'
            "</div>",
            unsafe_allow_html=True,
        )
        try:
            st.page_link("pages/9_competitive_landscape.py", label="Open →", use_container_width=True)
        except TypeError:
            st.page_link("pages/9_competitive_landscape.py", label="Open →")
    with c2:
        st.markdown(
            '<div class="lp-start-card lp-start-sky">'
            '<div class="lp-start-title">KG Query Explorer</div>'
            '<div class="lp-start-desc">Live Cypher templates — rotate gene in the right rail.</div>'
            "</div>",
            unsafe_allow_html=True,
        )
        try:
            st.page_link("pages/7_kg_query_explorer.py", label="Open →", use_container_width=True)
        except TypeError:
            st.page_link("pages/7_kg_query_explorer.py", label="Open →")
    with c3:
        st.markdown(
            '<div class="lp-start-card lp-start-vio">'
            '<div class="lp-start-title">Research Assistant</div>'
            '<div class="lp-start-desc">Retrieval-augmented Q&A for the active target.</div>'
            "</div>",
            unsafe_allow_html=True,
        )
        try:
            st.page_link("pages/5_research_assistant.py", label="Open →", use_container_width=True)
        except TypeError:
            st.page_link("pages/5_research_assistant.py", label="Open →")
