"""Build per-gene PARAM CSV slices (priority, eligibility, HPA protein proxy).

Usage:
  python scripts/build_gene_param_slices.py --symbol FOLH1
  python scripts/build_gene_param_slices.py --all-non-cd46
  python scripts/build_gene_param_slices.py --all
"""
from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT))

from src.analysis.gene_param_slices import build_gene_slices, list_param_targets  # noqa: E402

log = logging.getLogger(__name__)


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    p = argparse.ArgumentParser(description="Build PARAM slices per gene")
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--symbol", help="Single gene symbol")
    g.add_argument("--all-non-cd46", action="store_true")
    g.add_argument("--all", action="store_true")
    args = p.parse_args()

    if args.symbol:
        symbols = [args.symbol.upper()]
    elif args.all:
        symbols = list_param_targets()
    else:
        symbols = [s for s in list_param_targets() if s != "CD46"]

    failed: list[str] = []
    for sym in symbols:
        try:
            stats = build_gene_slices(sym)
            log.info("%s → %s", sym, stats)
        except Exception as exc:
            log.error("%s failed: %s", sym, exc)
            failed.append(sym)

    if failed:
        log.error("Failed: %s", ", ".join(failed))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
