"""Smoke-check U1b HTML right rail."""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "app"))

from components.right_rail import _rail_html  # noqa: E402
from components.ui_kit import dimension_links, page_path_to_slug  # noqa: E402

html = _rail_html()
assert "ob-right-rail-dock" in html
assert 'data-ob-target="CD46"' in html
assert 'data-ob-dim="/biomarker_panel"' in html
assert 'target="_blank"' not in html
assert "<a " not in html
assert page_path_to_slug("pages/0_platform_overview.py") == "/"
assert page_path_to_slug("pages/3_survival_outcomes.py") == "/survival_outcomes"
assert len(dimension_links()) == 9
print("OK: HTML right rail overlay")
