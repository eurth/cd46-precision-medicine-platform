"""Smoke-check HTML dock right rail (main-document onclick, hover expand)."""
from __future__ import annotations

import inspect
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "app"))

from components.right_rail import _rail_html, render_floating_right_rail  # noqa: E402
from components.theme_css import global_css  # noqa: E402
from components.ui_kit import dimension_links, page_path_to_slug  # noqa: E402

html = _rail_html()
css = global_css()
src = inspect.getsource(render_floating_right_rail)

assert "ob-right-rail-dock" in html
assert "onclick=" in html
assert "Biomarkers" in html
assert "ob-rail-grip" in html
assert "st.columns" not in src
assert "components.html" not in src
assert "ob-right-rail-dock" in css
assert "ob-rail-collapsed-w" in css
assert "stColumn" not in css or "ob-rail-host" not in css
assert page_path_to_slug("pages/6_biomarker_panel.py") == "/biomarker_panel"
assert len(dimension_links()) == 9
print("OK: HTML dock right rail")
