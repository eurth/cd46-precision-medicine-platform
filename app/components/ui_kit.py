"""
OncoBridge UI kit — thin wrappers over streamlit-shadcn-ui with native fallbacks.

Pages should import from here, not directly from streamlit_shadcn_ui.
"""
from __future__ import annotations

from typing import Any

import streamlit as st

# OncoBridge brand tokens (match styles.py)
_BG = "#07101F"
_CARD = "#0D1829"
_BORDER = "#16243C"
_PRIMARY = "#818CF8"
_TEXT = "#CBD5E1"
_MUTED = "#64748B"

_THEME_CSS = f"""
<style>
/* shadcn iframe hosts sit on our dark canvas */
[data-testid="stMain"] iframe {{
    border-radius: 8px;
}}
.ob-ui-section-label {{
    font-size: 10px; letter-spacing: 0.08em; text-transform: uppercase;
    color: {_MUTED}; font-weight: 600; margin: 0 0 6px 0;
}}
</style>
"""


def apply_theme() -> None:
    """Inject minimal OncoBridge tokens for shadcn component hosts."""
    st.markdown(_THEME_CSS, unsafe_allow_html=True)


def shadcn_available() -> bool:
    try:
        import streamlit_shadcn_ui  # noqa: F401
        return True
    except ImportError:
        return False


def metric_row(items: list[dict[str, str]], *, key_prefix: str = "kpi") -> None:
    """
    Render a row of KPI cards.

    Each item: title, content, description (optional), key (optional).
    """
    if not items:
        return
    if shadcn_available():
        import streamlit_shadcn_ui as ui

        cols = st.columns(len(items))
        for i, (col, item) in enumerate(zip(cols, items)):
            with col:
                ui.metric_card(
                    title=item["title"],
                    content=item["content"],
                    description=item.get("description", ""),
                    key=item.get("key", f"{key_prefix}_{i}"),
                )
        return
    cols = st.columns(len(items))
    for col, item in zip(cols, items):
        with col:
            st.metric(item["title"], item["content"], item.get("description"))


def section_tabs(
    options: list[str],
    *,
    key: str,
    default: str | None = None,
) -> str:
    """
    Return the selected tab label.

    Uses shadcn tabs when installed; compact horizontal radio as fallback.
    """
    if not options:
        return ""
    default_val = default or options[0]
    if shadcn_available():
        import streamlit_shadcn_ui as ui

        sel = ui.tabs(options=options, default_value=default_val, key=key)
        return str(sel) if sel else default_val
    return st.radio(
        "Section",
        options=options,
        index=options.index(default_val) if default_val in options else 0,
        horizontal=True,
        key=f"{key}_fallback",
        label_visibility="collapsed",
    )


def info_banner(message: str, *, variant: str = "info") -> None:
    """Alert banner with shadcn styling when available."""
    if shadcn_available():
        import streamlit_shadcn_ui as ui

        ui.alert(title=variant.title(), description=message, key=f"alert_{hash(message) & 0xFFFF}")
        return
    fn = {"info": st.info, "warning": st.warning, "error": st.error, "success": st.success}.get(
        variant, st.info
    )
    fn(message)


def assert_ui_kit_smoke() -> None:
    """ponytail: import + API surface check (no Streamlit runtime)."""
    assert callable(metric_row)
    assert callable(section_tabs)
    assert callable(apply_theme)


if __name__ == "__main__":
    assert_ui_kit_smoke()
    print("ui_kit_smoke_ok")
