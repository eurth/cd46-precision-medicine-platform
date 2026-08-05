#!/usr/bin/env python3
"""Re-extract CA9 (fix ABCA9 mis-match), then survival+KG for all panel expression CSVs."""
from __future__ import annotations

import json
import logging
import subprocess
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT))
from dotenv import load_dotenv

load_dotenv(_ROOT / ".env")

log = logging.getLogger(__name__)
PROC = _ROOT / "data" / "processed"
PY = sys.executable
CORE = {"CD46", "FOLH1", "FAP", "SSTR2", "GRPR"}


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    from src.knowledge_graph.registry import all_symbols, get_target
    from src.preprocessing.extract_gene import run_extract_batch
    from src.analysis.survival_analysis import run_all_cancers
    import pandas as pd

    # Fix CA9 row identity
    log.info("re-extract CA9 with exact matcher")
    run_extract_batch([("CA9", get_target("CA9")["ensembl_id"])])

    panel = [s for s in all_symbols() if s not in CORE]
    reports = []
    for s in panel:
        try:
            expr = PROC / f"{s.lower()}_expression.csv"
            if not expr.exists():
                reports.append({"symbol": s, "ok": False, "error": "missing expression"})
                continue
            run_all_cancers(pd.read_csv(expr), gene=s)
            for script in (
                ["scripts/load_gene_open_data.py", "--symbol", s],
                ["scripts/load_gene_patient_groups.py", "--symbol", s],
            ):
                rc = subprocess.call([PY, *script], cwd=str(_ROOT))
                if rc != 0:
                    raise RuntimeError(f"{script} rc={rc}")
            reports.append({"symbol": s, "ok": True})
            log.info("done %s", s)
        except Exception as e:
            log.exception("%s failed", s)
            reports.append({"symbol": s, "ok": False, "error": str(e)})

    print(json.dumps(reports, indent=2))
    raise SystemExit(0 if all(r.get("ok") for r in reports) else 1)


if __name__ == "__main__":
    main()
