"""Smoke-check U3 hero band + rail tooltip helpers."""
from __future__ import annotations

import inspect
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "app"))

from components.landing_hero import _hero_visual, _slide_body, render_hero_zone, render_target_carousel  # noqa: E402
from components.targets import list_symbols  # noqa: E402

hero_src = inspect.getsource(render_hero_zone)
assert "lp-hero-zone" in hero_src
assert "alphafold" in hero_src.lower() or "pae" in hero_src.lower()

for sym in list_symbols():
    pae, caption = _hero_visual(sym)
    assert caption
    assert pae and "alphafold" in pae

carousel_src = inspect.getsource(render_target_carousel)
assert "st.radio" in carousel_src
assert "get_active_symbol" in carousel_src

for sym in list_symbols():
    body = _slide_body(sym)
    assert sym in body and "lp-spotlight" in body

print(f"OK: U3 hero + rail tooltips ({len(list_symbols())} targets)")
