"""U2 landing — hero band (U3) + target spotlight tabs + quick-start row."""
from __future__ import annotations

import html as html_lib

import streamlit as st

from components.target_narratives import strategy_context
from components.targets import data_tier, get_active_symbol, get_target, is_case_study, list_symbols
from components.tooltip_generator import lookup


def _hero_visual(sym: str) -> tuple[str, str]:
    """AlphaFold PAE tile + short caption for the hero band."""
    hit = lookup(sym) or {}
    pae = str(hit.get("alphafold_pae_image_url") or "").strip()
    caption = str(hit.get("summary_short") or get_target(sym).get("name") or sym)
    return pae, caption


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
        f"Active selection: <strong>{html_lib.escape(sym)}</strong> (right rail)"
        f"</div>"
        f"</div>"
    )


def render_hero_zone() -> None:
    """Target-synced hero — AlphaFold PAE imagery + gene context (U3)."""
    sym = get_active_symbol()
    ctx = strategy_context(sym)
    pae_url, caption = _hero_visual(sym)
    sym_cls = html_lib.escape(sym.lower())
    pae_attr = html_lib.escape(pae_url) if pae_url else ""
    st.markdown(
        f'<div class="lp-hero-zone lp-hero-{sym_cls}"'
        f' data-target="{html_lib.escape(sym)}"'
        f' style="--lp-hero-pae: url(\'{pae_attr}\');">'
        f'<div class="lp-hero-zone-inner">'
        f'<div class="lp-hero-zone-kicker">Theranostics target</div>'
        f'<div class="lp-hero-zone-title">{html_lib.escape(sym)}</div>'
        f'<div class="lp-hero-zone-sub">{html_lib.escape(ctx["name"])}</div>'
        f'<div class="lp-hero-zone-caption">{html_lib.escape(caption)}</div>'
        f"</div></div>",
        unsafe_allow_html=True,
    )


def render_target_carousel() -> None:
    """Target spotlight — synced with active target (right rail / sidebar / ?target=)."""
    from components.targets import set_active_symbol

    symbols = list_symbols()
    active = get_active_symbol()
    idx = symbols.index(active) if active in symbols else 0

    # ponytail: no widget key — st.tabs/st.radio keys stick on CD46 after rail switch
    picked = st.radio(
        "Target",
        symbols,
        index=idx,
        horizontal=True,
        label_visibility="collapsed",
    )
    if picked != active:
        set_active_symbol(picked)
        st.query_params["target"] = picked
        st.rerun()

    st.markdown(_slide_body(picked), unsafe_allow_html=True)


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
