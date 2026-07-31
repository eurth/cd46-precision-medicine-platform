"""Smoke-check native-widget right rail."""
from __future__ import annotations

import inspect
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "app"))

from components.right_rail import render_floating_right_rail  # noqa: E402
from components.theme_css import global_css  # noqa: E402

src = inspect.getsource(render_floating_right_rail)
css = global_css()

assert "st.button" in src
assert "help=" not in src
assert "st.page_link" in src
assert "st.columns" in src
assert 'onclick="' not in src
assert "ob-right-rail-host" in src
assert "stColumn" in css and "ob-right-rail-host" in css
rail_css = css.split("ob-right-rail-host")[1].split(".ob-tb-label")[0]
assert "max-height: 0" not in rail_css
print("OK: native widget right rail")
