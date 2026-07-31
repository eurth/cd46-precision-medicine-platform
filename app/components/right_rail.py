"""Thin floating right rail — native Streamlit widgets (U1 architecture).

Architecture (do not "simplify" without re-testing layout):
- Rendered AFTER pg.run() at the bottom of the script.
- Uses st.columns([24, 1]) so the rail lives in its own column.
- CSS (theme_css) zeros the horizontal block and position:fixed the
  column that contains .ob-right-rail-host — that is what pins it right.
- Must use st.button / st.page_link (not components.html) — sandboxed
  iframes cannot navigate the parent window.
"""
from __future__ import annotations

import streamlit as st

from components.targets import (
    ensure_session_target,
    get_active_symbol,
    list_symbols,
    set_active_symbol,
)
from components.ui_kit import dimension_links

# Short labels fit the fixed ~56px rail (U1). Full names via button help / title.
_TGT_LABEL: dict[str, str] = {
    "CD46": "CD46",
    "FOLH1": "PSMA",
    "FAP": "FAP",
    "SSTR2": "SST",
    "GRPR": "GRP",
}

_DIM_SHORT: dict[str, str] = {
    "Home": "Ho",
    "Target": "Ta",
    "Biomarkers": "Bi",
    "Proteins": "Pr",
    "Patients": "Pt",
    "Drugs": "Dr",
    "Survival": "Su",
    "Graph": "Gx",
    "Strategy": "St",
}


def sync_target_from_query() -> None:
    """Apply ?target=SYM into session when present."""
    ensure_session_target()
    raw = st.query_params.get("target")
    if not raw:
        return
    sym = str(raw).upper()
    if sym in list_symbols():
        set_active_symbol(sym)


def render_floating_right_rail() -> str:
    """Fixed narrow rail — targets (top) + dimension page links (bottom)."""
    sync_target_from_query()
    current = get_active_symbol()

    _pad, rail = st.columns([24, 1], gap="small")
    with _pad:
        # Marker for CSS: collapse this horizontal block out of document flow
        st.markdown('<div id="ob-rail-flow-anchor"></div>', unsafe_allow_html=True)
    with rail:
        # Marker for CSS: position:fixed this column to the viewport right
        st.markdown('<div class="ob-right-rail-host"></div>', unsafe_allow_html=True)
        st.markdown('<div class="ob-rail-kicker">Target</div>', unsafe_allow_html=True)
        for sym in list_symbols():
            label = _TGT_LABEL.get(sym, sym)
            if st.button(
                label,
                key=f"ob_rail_tgt_{sym}",
                type="primary" if sym == current else "secondary",
                use_container_width=True,
                help=f"Research target: {sym}",
            ):
                if sym != current:
                    set_active_symbol(sym)
                    st.query_params["target"] = sym
                    st.rerun()
        st.markdown('<div class="ob-rail-kicker">Dim</div>', unsafe_allow_html=True)
        for label, path in dimension_links():
            short = _DIM_SHORT.get(label, label[:2])
            try:
                st.page_link(path, label=short, use_container_width=True)
            except TypeError:
                st.page_link(path, label=short)

    return get_active_symbol()


if __name__ == "__main__":
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    assert len(_DIM_SHORT) == len(dimension_links())
    assert len(_TGT_LABEL) == len(list_symbols())
    print("right_rail_ok")
