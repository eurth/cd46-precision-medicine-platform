#!/usr/bin/env python3
"""One-pass TCGA extract + survival + Aura load for registry genes missing slices.

Usage:
  python scripts/load_tcga_panel.py --pending
  python scripts/load_tcga_panel.py --symbols EGFR,ERBB2,TACSTD2
"""
from __future__ import annotations

import argparse
import json
import logging
import subprocess
import sys
import time
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT))

from dotenv import load_dotenv

load_dotenv(_ROOT / ".env")

log = logging.getLogger(__name__)
PY = sys.executable
PROC = _ROOT / "data" / "processed"


def _pending_symbols() -> list[str]:
    from src.knowledge_graph.registry import all_symbols, get_target

    out = []
    for s in all_symbols():
        if not (PROC / f"{s.lower()}_by_cancer.csv").exists():
            get_target(s)
            out.append(s)
    return out


def _run(cmd: list[str]) -> int:
    log.info("RUN %s", " ".join(cmd))
    return subprocess.call(cmd, cwd=str(_ROOT))


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    ap = argparse.ArgumentParser()
    ap.add_argument("--pending", action="store_true")
    ap.add_argument("--symbols", default="")
    ap.add_argument("--skip-kg", action="store_true")
    args = ap.parse_args()

    from src.knowledge_graph.registry import get_target
    from src.preprocessing.extract_gene import run_extract_batch
    import pandas as pd
    from src.analysis.survival_analysis import run_all_cancers

    if args.pending:
        symbols = _pending_symbols()
    elif args.symbols:
        symbols = [s.strip().upper() for s in args.symbols.split(",") if s.strip()]
    else:
        ap.error("Need --pending or --symbols")

    pairs = [(s, get_target(s)["ensembl_id"]) for s in symbols]
    log.info("batch extract %d genes: %s", len(pairs), [s for s, _ in pairs])
    t0 = time.time()
    extracted = run_extract_batch(pairs)
    log.info("extract done in %.1fs (%d genes)", time.time() - t0, len(extracted))

    reports = []
    for symbol, _expr, _cancer in extracted:
        t1 = time.time()
        try:
            df = pd.read_csv(PROC / f"{symbol.lower()}_expression.csv")
            run_all_cancers(df, gene=symbol)
            if not args.skip_kg:
                for script in (
                    ["scripts/load_gene_open_data.py", "--symbol", symbol],
                    ["scripts/load_gene_patient_groups.py", "--symbol", symbol],
                ):
                    rc = _run([PY, *script])
                    if rc != 0:
                        raise RuntimeError(f"{script} exit={rc}")
            reports.append({"symbol": symbol, "ok": True, "sec": round(time.time() - t1, 1)})
        except Exception as e:
            log.exception("%s post-extract failed", symbol)
            reports.append({"symbol": symbol, "ok": False, "error": str(e)})

    missed = [s for s, _ in pairs if s not in {r["symbol"] for r in reports}]
    for s in missed:
        reports.append({"symbol": s, "ok": False, "error": "not found in TCGA matrix"})

    print(json.dumps(reports, indent=2))
    raise SystemExit(0 if all(r.get("ok") for r in reports) else 1)


if __name__ == "__main__":
    main()
