"""Smoke-check sidebar nav section mapping."""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "app"))

from components.sidebar_nav import NAV_SECTIONS, PAGE_TO_SECTION, _collapsed_state  # noqa: E402

assert len(NAV_SECTIONS) == 9
assert PAGE_TO_SECTION["Expression Atlas"] == "Target / Cancer"
st = _collapsed_state("Home")
assert st["Home"] and not st["Biomarkers"]
print("OK: sidebar nav defaults")
