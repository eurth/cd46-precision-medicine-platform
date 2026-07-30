"""Build C2–C4 coverage CSVs (trials, GTEx dosimetry, GENIE co-occurrence).

Usage:
  python scripts/build_gene_coverage_slices.py --fetch-trials --all-non-cd46
  python scripts/build_gene_coverage_slices.py --symbol FOLH1
"""
from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT))

from src.analysis.gene_coverage_slices import (  # noqa: E402
    build_coverage,
    list_medium_targets,
)

log = logging.getLogger(__name__)


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    p = argparse.ArgumentParser()
    p.add_argument("--symbol")
    p.add_argument("--all-non-cd46", action="store_true")
    p.add_argument("--all", action="store_true")
    p.add_argument("--fetch-trials", action="store_true", help="Hit ClinicalTrials.gov API first")
    args = p.parse_args()

    if args.symbol:
        symbols = [args.symbol.upper()]
    elif args.all:
        symbols = list_medium_targets()
    else:
        symbols = [s for s in list_medium_targets() if s != "CD46"]

    if args.fetch_trials:
        import importlib.util

        mod_path = _ROOT / "scripts" / "load_gene_trials_hpa.py"
        spec = importlib.util.spec_from_file_location("load_gene_trials_hpa", mod_path)
        mod = importlib.util.module_from_spec(spec)
        assert spec.loader is not None
        spec.loader.exec_module(mod)
        for sym in symbols:
            try:
                mod.fetch_trials(sym, refresh=False)
            except Exception as exc:
                log.warning("Trial fetch %s: %s", sym, exc)

    failed: list[str] = []
    for sym in symbols:
        try:
            stats = build_coverage(sym)
            log.info("%s → %s", sym, stats)
        except Exception as exc:
            log.error("%s failed: %s", sym, exc)
            failed.append(sym)

    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
