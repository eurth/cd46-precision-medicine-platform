"""Smoke-check U1 right rail architecture (native widgets + fixed-column CSS)."""
from __future__ import annotations

import inspect
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "app"))

from components.right_rail import render_floating_right_rail  # noqa: E402
from components.theme_css import global_css  # noqa: E402
from components.ui_kit import dimension_links  # noqa: E402

src = inspect.getsource(render_floating_right_rail)
css = global_css()

assert "st.button" in src
assert "st.page_link" in src
assert "st.columns" in src
assert "ob-right-rail-host" in src
assert "ob-rail-flow-anchor" in src
assert "components.html" not in src
assert 'stColumn"]:has(.ob-right-rail-host)' in css
assert 'column"]:has(.ob-right-rail-host)' in css  # legacy Streamlit
assert "#ob-rail-flow-anchor" in css
assert "position: fixed" in css
assert "ob-right-rail-dock" not in css  # dead HTML dock must stay gone
assert len(dimension_links()) == 9
print("OK: U1 right rail (stColumn + column selectors)")
