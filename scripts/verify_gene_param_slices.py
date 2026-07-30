"""Smoke-check PARAM slice CSVs exist for medium-tier targets."""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT))

from app.components.gene_data import load_patient_groups_df, load_priority_df, priority_path  # noqa: E402
from src.analysis.gene_param_slices import list_param_targets  # noqa: E402

NON_CD46 = [s for s in list_param_targets() if s != "CD46"]
errors: list[str] = []

for sym in NON_CD46:
    if not priority_path(sym).exists():
        errors.append(f"missing {priority_path(sym)}")
    else:
        pri = load_priority_df(sym)
        if pri.empty or "priority_score" not in pri.columns:
            errors.append(f"{sym} priority empty or missing priority_score")
    pg = load_patient_groups_df(sym)
    if pg.empty:
        errors.append(f"missing/empty patient groups for {sym}")
    elif not pg["cancer_type"].nunique() >= 5:
        errors.append(f"{sym} patient_groups too few cancers")

if errors:
    print("FAIL:", *errors, sep="\n  ")
    raise SystemExit(1)

print(f"OK: PARAM slices for {', '.join(NON_CD46)}")
raise SystemExit(0)
