"""Smoke-check U2 landing spotlight."""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "app"))

from components.landing_hero import _slide_body  # noqa: E402
from components.targets import list_symbols  # noqa: E402

for sym in list_symbols():
    body = _slide_body(sym)
    assert sym in body and "lp-spotlight" in body

print(f"OK: landing spotlight ({len(list_symbols())} targets)")
