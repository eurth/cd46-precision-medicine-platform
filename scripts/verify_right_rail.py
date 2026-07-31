"""Smoke-check right rail uses native widgets (no sandboxed iframe nav)."""
from __future__ import annotations

import inspect
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "app"))

from components.right_rail import render_floating_right_rail  # noqa: E402
from components.ui_kit import dimension_links, page_path_to_slug  # noqa: E402

src = inspect.getsource(render_floating_right_rail)
assert "st.button" in src
assert "st.page_link" in src
assert "components.html" not in src
assert page_path_to_slug("pages/3_survival_outcomes.py") == "/survival_outcomes"
assert len(dimension_links()) == 9
print("OK: native right rail widgets")
