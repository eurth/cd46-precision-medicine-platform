"""Verify C2–C4 coverage CSVs exist for medium-tier targets."""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT))

from src.analysis.gene_coverage_slices import list_medium_targets  # noqa: E402

PROC = _ROOT / "data" / "processed"
errors: list[str] = []

for sym in list_medium_targets():
    pref = sym.lower()
    for name in (f"{pref}_gtex_dosimetry.csv", f"{pref}_trials_summary.csv"):
        if not (PROC / name).exists():
            errors.append(f"missing {name}")

if errors:
    print("FAIL:", *errors, sep="\n  ")
    raise SystemExit(1)
print(f"OK: coverage slices for {', '.join(list_medium_targets())}")
raise SystemExit(0)
