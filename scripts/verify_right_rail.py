"""Smoke-check U1 right rail dimension abbreviations."""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "app"))

from components.right_rail import _DIM_SHORT  # noqa: E402
from components.ui_kit import dimension_links  # noqa: E402

assert len(_DIM_SHORT) == len(dimension_links()) == 9
print("OK: right rail (9 targets dims)")
