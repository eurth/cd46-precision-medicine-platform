"""Floating right rail — native Streamlit widgets in an isolated column."""
from __future__ import annotations

import streamlit as st

from components.targets import (
    ensure_session_target,
    get_active_symbol,
    list_symbols,
    set_active_symbol,
)
from components.ui_kit import dimension_links

_TGT_LABEL: dict[str, str] = {
    "CD46": "CD46",
    "FOLH1": "PSMA",
    "FAP": "FAP",
    "SSTR2": "SSTR2",
    "GRPR": "GRPR",
}


def sync_target_from_query() -> None:
    """Apply ?target=SYM from rail links into session (survives page nav)."""
    ensure_session_target()
    raw = st.query_params.get("target")
    if not raw:
        return
    sym = str(raw).upper()
    if sym in list_symbols():
        set_active_symbol(sym)


def render_floating_right_rail() -> str:
    """Fixed overlay dock — isolated column so CSS cannot swallow main content."""
    sync_target_from_query()
    current = get_active_symbol()

    _pad, rail_col = st.columns([24, 1], gap="small")
    with _pad:
        st.markdown('<div id="ob-rail-flow-anchor"></div>', unsafe_allow_html=True)
    with rail_col:
        st.markdown('<div id="ob-rail-host" class="ob-rail-host"></div>', unsafe_allow_html=True)
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

        st.markdown('<div class="ob-rail-kicker">Dimension</div>', unsafe_allow_html=True)
        for label, path in dimension_links():
            try:
                st.page_link(path, label=label, use_container_width=True)
            except TypeError:
                st.page_link(path, label=label)

    return get_active_symbol()


if __name__ == "__main__":
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    assert len(_TGT_LABEL) == len(list_symbols())
    assert len(dimension_links()) == 9
    print("right_rail_ok")
