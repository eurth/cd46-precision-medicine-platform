"""Floating right rail — pure HTML overlay (no Streamlit columns / zero layout width)."""
from __future__ import annotations

import html as html_lib

import streamlit as st

from components.targets import ensure_session_target, get_active_symbol, list_symbols
from components.ui_kit import dimension_links

# Streamlit navigation titles → URL slugs (st.navigation multipage)
_DIM_HREF: dict[str, str] = {
    "Home": "/",
    "Target": "/Expression_Atlas",
    "Biomarkers": "/Biomarker_Panel",
    "Proteins": "/PPI_Network_Explorer",
    "Patients": "/Patient_Selection",
    "Drugs": "/Drug_Pipeline",
    "Survival": "/Survival_Outcomes",
    "Graph": "/Knowledge_Graph",
    "Strategy": "/Clinical_Strategy_Engine",
}

_DIM_SHORT: dict[str, str] = {
    "Home": "Home",
    "Target": "Tgt",
    "Biomarkers": "Bio",
    "Proteins": "Pro",
    "Patients": "Pts",
    "Drugs": "Rx",
    "Survival": "Surv",
    "Graph": "KG",
    "Strategy": "Str",
}

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
        from components.targets import set_active_symbol

        set_active_symbol(sym)


def _rail_html() -> str:
    current = get_active_symbol()
    targets = "".join(
        f'<a class="ob-rail-a ob-rail-tgt{" ob-rail-on" if s == current else ""}" '
        f'href="?target={html_lib.escape(s)}" title="{html_lib.escape(s)}">'
        f"{html_lib.escape(_TGT_LABEL.get(s, s))}</a>"
        for s in list_symbols()
    )
    dims = "".join(
        f'<a class="ob-rail-a ob-rail-dim" href="{html_lib.escape(_DIM_HREF.get(label, "/"))}" '
        f'title="{html_lib.escape(label)} perspective">'
        f"{html_lib.escape(_DIM_SHORT.get(label, label[:3]))}</a>"
        for label, _path in dimension_links()
    )
    return (
        f'<nav id="ob-right-rail-dock" class="ob-right-rail-dock" aria-label="Target and dimension">'
        f'<div class="ob-rail-kicker">Target</div>{targets}'
        f'<div class="ob-rail-kicker">Dimension</div>{dims}'
        f"</nav>"
    )


def render_floating_right_rail() -> str:
    """Fixed overlay dock — must run after page content; takes no horizontal space."""
    sync_target_from_query()
    st.markdown(_rail_html(), unsafe_allow_html=True)
    return get_active_symbol()


if __name__ == "__main__":
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    assert len(_DIM_SHORT) == len(dimension_links()) == len(_DIM_HREF)
    print("right_rail_ok")
