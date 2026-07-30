"""Floating right rail — pure HTML overlay (no Streamlit columns / zero layout width)."""
from __future__ import annotations

import html as html_lib

import streamlit as st
import streamlit.components.v1 as components

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
    # ponytail: buttons not <a> — Streamlit markdown rewrites anchors to target=_blank
    current = get_active_symbol()
    targets = "".join(
        f'<button type="button" class="ob-rail-a ob-rail-tgt{" ob-rail-on" if s == current else ""}" '
        f'data-ob-target="{html_lib.escape(s)}" title="{html_lib.escape(s)}">'
        f"{html_lib.escape(_TGT_LABEL.get(s, s))}</button>"
        for s in list_symbols()
    )
    dims = "".join(
        f'<button type="button" class="ob-rail-a ob-rail-dim" '
        f'data-ob-dim="{html_lib.escape(page_path_to_slug(path))}" '
        f'title="{html_lib.escape(label)} perspective">'
        f"{html_lib.escape(label)}</button>"
        for label, path in dimension_links()
    )
    return (
        f'<nav id="ob-right-rail-dock" class="ob-right-rail-dock" aria-label="Target and dimension" '
        f'title="Hover to expand target & dimension rail">'
        f'<div class="ob-rail-grip" aria-hidden="true"></div>'
        f'<div class="ob-rail-body">'
        f'<div class="ob-rail-kicker">Target</div>{targets}'
        f'<div class="ob-rail-kicker">Dimension</div>{dims}'
        f"</div></nav>"
    )


def _inject_rail_nav_js() -> None:
    """Wire rail buttons — same-tab nav with ?target= preserved."""
    components.html(
        """
<script>
(function () {
  const win = window.parent;
  const doc = win.document;
  const dock = doc.getElementById("ob-right-rail-dock");
  if (!dock) return;

  dock.querySelectorAll("[data-ob-target]").forEach((btn) => {
    btn.onclick = () => {
      const u = new URL(win.location.href);
      u.searchParams.set("target", btn.dataset.obTarget);
      win.location.assign(u.toString());
    };
  });

  dock.querySelectorAll("[data-ob-dim]").forEach((btn) => {
    btn.onclick = () => {
      const u = new URL(win.location.origin + btn.dataset.obDim);
      const cur = new URL(win.location.href).searchParams.get("target");
      if (cur) u.searchParams.set("target", cur);
      win.location.assign(u.toString());
    };
  });
})();
</script>
        """,
        height=0,
        scrolling=False,
    )


def render_floating_right_rail() -> str:
    """Fixed overlay dock — must run after page content; takes no horizontal space."""
    sync_target_from_query()
    st.markdown(_rail_html(), unsafe_allow_html=True)
    _inject_rail_nav_js()
    return get_active_symbol()


if __name__ == "__main__":
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    html = _rail_html()
    assert "data-ob-target=\"CD46\"" in html
    assert "data-ob-dim=\"/cd46_expression_atlas\"" in html
    assert "target=\"_blank\"" not in html
    assert "<a " not in html
    print("right_rail_ok")
