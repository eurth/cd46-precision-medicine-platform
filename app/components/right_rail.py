"""Right rail — fixed HTML dock in the main document (no Streamlit columns, no iframe).

Architecture:
- Pure HTML + inline onclick (same document → no sandbox SecurityError).
- Injected via st.markdown after pg.run(); zero layout footprint.
- sync_target_from_query() runs in streamlit_app BEFORE pg.run().
"""
from __future__ import annotations

import html as html_lib

import streamlit as st

from components.targets import ensure_session_target, get_active_symbol, list_symbols
from components.ui_kit import dimension_links, page_path_to_slug

_TGT_LABEL: dict[str, str] = {
    "CD46": "CD46",
    "FOLH1": "PSMA",
    "FAP": "FAP",
    "SSTR2": "SSTR2",
    "GRPR": "GRPR",
}


def sync_target_from_query() -> None:
    """Apply ?target=SYM into session when present."""
    ensure_session_target()
    raw = st.query_params.get("target")
    if not raw:
        return
    sym = str(raw).upper()
    if sym in list_symbols():
        from components.targets import set_active_symbol

        set_active_symbol(sym)


def _onclick_target(sym: str) -> str:
    s = html_lib.escape(sym, quote=True)
    return (
        "var u=new URL(window.location.href);"
        f"u.searchParams.set('target','{s}');"
        "window.location.assign(u.href);"
    )


def _onclick_dim(slug: str) -> str:
    slug_esc = html_lib.escape(slug, quote=True)
    return (
        f"var u=new URL(window.location.origin+'{slug_esc}');"
        "var c=new URL(window.location.href).searchParams.get('target');"
        "if(c)u.searchParams.set('target',c);"
        "window.location.assign(u.href);"
    )


def _rail_html() -> str:
    current = get_active_symbol()
    targets = "".join(
        f'<button type="button" class="ob-rail-a ob-rail-tgt{" ob-rail-on" if s == current else ""}" '
        f'onclick="{_onclick_target(s)}" title="{html_lib.escape(s)}">'
        f"{html_lib.escape(_TGT_LABEL.get(s, s))}</button>"
        for s in list_symbols()
    )
    dims = "".join(
        f'<button type="button" class="ob-rail-a ob-rail-dim" '
        f'onclick="{_onclick_dim(page_path_to_slug(path))}" '
        f'title="{html_lib.escape(label)} perspective">'
        f"{html_lib.escape(label)}</button>"
        for label, path in dimension_links()
    )
    return (
        f'<nav id="ob-right-rail-dock" class="ob-right-rail-dock" aria-label="Target and dimension" '
        f'title="Hover to expand target &amp; dimension rail">'
        f'<div class="ob-rail-grip" aria-hidden="true"></div>'
        f'<div class="ob-rail-body">'
        f'<div class="ob-rail-kicker">Target</div>{targets}'
        f'<div class="ob-rail-kicker">Dimension</div>{dims}'
        f"</div></nav>"
    )


def render_floating_right_rail() -> str:
    """Fixed overlay dock — HTML only, no layout width."""
    st.markdown(_rail_html(), unsafe_allow_html=True)
    return get_active_symbol()


if __name__ == "__main__":
    html = _rail_html()
    assert "ob-right-rail-dock" in html
    assert "onclick=" in html
    assert "data-ob-target" not in html
    assert "components.html" not in html
    assert "/cd46_expression_atlas" in html or "Target" in html
    print("right_rail_ok")
