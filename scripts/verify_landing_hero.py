"""Smoke-check U2 landing carousel slides."""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "app"))

from components.landing_hero import _slide_html  # noqa: E402
from components.targets import list_symbols  # noqa: E402

for i, sym in enumerate(list_symbols()):
    html = _slide_html(sym, i)
    assert sym in html and "lp-carousel-slide" in html

print(f"OK: landing carousel ({len(list_symbols())} slides)")
