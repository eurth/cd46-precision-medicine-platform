"""Smoke-check U1b HTML right rail."""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "app"))

from components.right_rail import _DIM_HREF, _rail_html  # noqa: E402
from components.ui_kit import dimension_links  # noqa: E402

html = _rail_html()
assert "ob-right-rail-dock" in html
assert "?target=CD46" in html
assert "Biomarkers" in html
assert len(_DIM_HREF) == len(dimension_links())
print("OK: HTML right rail overlay")
