"""Smoke-check C5 per-target strategy copy."""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "app"))

from components.target_narratives import (  # noqa: E402
    _STRATEGY,
    strategy_stage1_title,
)

for sym in ("CD46", "FOLH1", "SSTR2", "FAP", "GRPR"):
    assert _STRATEGY[sym]["modality"]
    assert strategy_stage1_title(sym).endswith(f"{sym}?")

print("OK: target narratives for 5 symbols")
