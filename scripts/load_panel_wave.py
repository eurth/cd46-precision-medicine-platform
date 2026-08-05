"""Path-to-50k panel orchestrator — full research loads per gene (no mid-dataset truncation).

Philosophy:
  - Complete each source for a gene (OT full API, CT.gov full pagination, etc.).
  - Soft goal ≥50k is aspirational; never stop mid-dataset to hit a round number.
  - Between genes only: bail if Aura Free hard ceiling (~180k) approached.
  - Step failures retry then continue remaining sources (don't abort whole panel).

Usage:
  python scripts/load_panel_wave.py --all-loaded-caps --skip-extract
  python scripts/load_panel_wave.py --pending --skip-extract
  python scripts/load_panel_wave.py --symbols CEACAM5,STEAP1 --skip-extract
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import subprocess
import sys
import time
from pathlib import Path

from dotenv import load_dotenv

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT))
load_dotenv(_ROOT / ".env")

from src.knowledge_graph.registry import load_registry  # noqa: E402

log = logging.getLogger(__name__)
PY = sys.executable
AURA_SOFT_CEILING = 180_000


def _count_nodes() -> int:
    from neo4j import GraphDatabase

    d = GraphDatabase.driver(
        os.environ["NEO4J_URI"],
        auth=(os.environ.get("NEO4J_USERNAME", "neo4j"), os.environ["NEO4J_PASSWORD"]),
    )
    try:
        with d.session() as s:
            return int(s.run("MATCH (n) RETURN count(n) AS c").single()["c"])
    finally:
        d.close()


def _run(cmd: list[str], *, retries: int = 3) -> int:
    log.info("RUN %s", " ".join(cmd))
    last = 1
    for attempt in range(1, retries + 1):
        last = subprocess.run(cmd, cwd=str(_ROOT)).returncode
        if last == 0:
            return 0
        log.warning("cmd failed exit=%d attempt=%d/%d — backoff", last, attempt, retries)
        time.sleep(5 * attempt)
    return last


def _mark_loaded(symbol: str) -> None:
    import yaml

    path = _ROOT / "config" / "targets.yaml"
    with path.open(encoding="utf-8") as f:
        data = yaml.safe_load(f)
    t = data["targets"][symbol]
    t["kg_status"] = "loaded"
    if t.get("data_tier") in (None, "thin", "stub", "pending"):
        t["data_tier"] = "medium"
    with path.open("w", encoding="utf-8") as f:
        yaml.safe_dump(data, f, default_flow_style=False, sort_keys=False)


def load_symbol(symbol: str, *, skip_extract: bool = False) -> dict:
    report: dict = {"symbol": symbol, "nodes_before": _count_nodes()}
    # ponytail: no --refresh* — resume uses on-disk API caches; missing files still fetch
    steps = [
        [
            PY, "scripts/load_target_slice.py", "--symbol", symbol,
            "--ot-size", "0",
            "--edge-limit", "500", "--required-score", "400",
        ] + (["--skip-extract"] if skip_extract else []),
        [PY, "scripts/load_gene_open_data.py", "--symbol", symbol],
        [PY, "scripts/load_gene_trials_hpa.py", "--symbol", symbol, "--max-trials", "0"],
        [
            PY, "scripts/load_gene_pubmed_chembl.py", "--symbol", symbol,
            "--pubmed-max", "0", "--chembl-cap", "0",
        ],
        [PY, "scripts/load_gene_uniprot_gtex_depmap.py", "--symbol", symbol],
        [
            PY, "scripts/load_gene_clinvar.py", "--symbol", symbol,
            "--max-variants", "0",
        ],
        [PY, "scripts/load_gene_patient_groups.py", "--symbol", symbol],
    ]
    failed = []
    for cmd in steps:
        rc = _run(cmd)
        if rc != 0:
            failed.append({"cmd": cmd, "exit": rc})
            log.error("step failed for %s — continuing remaining steps", symbol)
            time.sleep(2)
            continue
        time.sleep(0.3)
    if not failed or len(failed) < len(steps) // 2:
        _mark_loaded(symbol)
        report["exit"] = 0 if not failed else 1
        report["partial"] = bool(failed)
    else:
        report["exit"] = 1
    if failed:
        report["failed"] = failed
    report["nodes_after"] = _count_nodes()
    report["delta"] = report["nodes_after"] - report["nodes_before"]
    return report


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    ap = argparse.ArgumentParser()
    ap.add_argument("--symbols")
    ap.add_argument("--pending", action="store_true")
    ap.add_argument("--all-loaded-caps", action="store_true")
    ap.add_argument("--skip-extract", action="store_true")
    args = ap.parse_args()

    reg = load_registry()["targets"]
    if args.symbols:
        symbols = [s.strip().upper() for s in args.symbols.split(",") if s.strip()]
    elif args.pending:
        symbols = [s for s, m in reg.items() if (m.get("kg_status") or "").lower() == "pending"]
    elif args.all_loaded_caps:
        symbols = [s for s, m in reg.items() if (m.get("kg_status") or "").lower() == "loaded"]
    else:
        ap.error("Need --symbols, --pending, or --all-loaded-caps")

    start = _count_nodes()
    log.info("nodes_before=%d symbols=%s (full-source loads; soft goal 50k)", start, symbols)
    reports = []
    for sym in symbols:
        if _count_nodes() >= AURA_SOFT_CEILING:
            log.warning("Aura soft ceiling %d — stop before next gene", AURA_SOFT_CEILING)
            break
        reports.append(load_symbol(sym, skip_extract=args.skip_extract))
        print(json.dumps(reports[-1], indent=2))

    end = _count_nodes()
    summary = {"nodes_before": start, "nodes_after": end, "delta": end - start, "reports": reports}
    (_ROOT / "reports" / "path_to_50k_panel_wave.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps({"nodes_before": start, "nodes_after": end, "delta": end - start}, indent=2))


if __name__ == "__main__":
    main()
