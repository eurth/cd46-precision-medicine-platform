"""Thin floating right rail — research target + dimension perspective (U1)."""
from __future__ import annotations

import streamlit as st

from components.targets import (
    ensure_session_target,
    get_active_symbol,
    list_symbols,
    set_active_symbol,
)
from components.ui_kit import dimension_links

# ponytail: ≤4 chars so labels don't wrap vertically in 52px rail
_TGT_LABEL: dict[str, str] = {
    "CD46": "CD46",
    "FOLH1": "PSMA",
    "FAP": "FAP",
    "SSTR2": "S2",
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


def render_floating_right_rail() -> str:
    """Fixed narrow rail over main content — targets (top) + dimensions (bottom)."""
    ensure_session_target()
    current = get_active_symbol()
    symbols = list_symbols()

    _pad, rail = st.columns([24, 1], gap="small")
    with _pad:
        st.markdown('<div id="ob-rail-flow-anchor"></div>', unsafe_allow_html=True)
    with rail:
        st.markdown('<div class="ob-right-rail-host">', unsafe_allow_html=True)
        st.markdown('<div class="ob-rail-kicker">Target</div>', unsafe_allow_html=True)
        for sym in symbols:
            label = _TGT_LABEL.get(sym, sym[:4])
            if st.button(
                label,
                key=f"ob_rail_tgt_{sym}",
                type="primary" if sym == current else "secondary",
                use_container_width=True,
                help=f"Research target: {sym}",
            ):
                if sym != current:
                    set_active_symbol(sym)
                    st.rerun()
        st.markdown('<div class="ob-rail-kicker">Dim</div>', unsafe_allow_html=True)
        for label, path in dimension_links():
            short = _DIM_SHORT.get(label, label[:2])
            try:
                st.page_link(path, label=short, use_container_width=True)
            except TypeError:
                st.page_link(path, label=short)
        st.markdown("</div>", unsafe_allow_html=True)

    return get_active_symbol()


if __name__ == "__main__":
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    assert len(_DIM_SHORT) == len(dimension_links())
    print("right_rail_ok")
