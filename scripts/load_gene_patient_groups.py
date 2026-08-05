"""Path-to-50k: PatientGroup threshold slices from *_by_cancer.csv (not GENIE patients).

Creates one PatientGroup per gene × cancer × threshold label (top25/top50/above_median).
"""
from __future__ import annotations

import argparse
import logging
import os
import sys
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT))
load_dotenv(_ROOT / ".env")

from src.knowledge_graph.registry import all_symbols  # noqa: E402

log = logging.getLogger(__name__)
DATA = _ROOT / "data" / "processed"
THRESHOLDS = ("top25", "top50", "above_median")


def _driver():
    from neo4j import GraphDatabase

    uri = os.environ["NEO4J_URI"]
    user = os.environ.get("NEO4J_USERNAME", "neo4j")
    pwd = os.environ["NEO4J_PASSWORD"]
    d = GraphDatabase.driver(uri, auth=(user, pwd))
    d.verify_connectivity()
    return d


def load_symbol(session, symbol: str) -> int:
    path = DATA / f"{symbol.lower()}_by_cancer.csv"
    if not path.exists():
        log.warning("skip PatientGroup %s — missing %s", symbol, path.name)
        return 0
    df = pd.read_csv(path)
    # flexible column names
    cancer_col = next((c for c in df.columns if c.lower() in ("cancer", "tcga_code", "cancer_type")), None)
    med_col = next((c for c in df.columns if "median" in c.lower() or c.lower().endswith("tpm")), None)
    if not cancer_col:
        log.warning("skip %s — no cancer column in %s", symbol, path.name)
        return 0
    n = 0
    for _, row in df.iterrows():
        cancer = str(row[cancer_col]).strip().upper()
        if not cancer or cancer == "NAN":
            continue
        median = float(row[med_col]) if med_col and pd.notna(row.get(med_col)) else None
        for thr in THRESHOLDS:
            pg_id = f"{symbol}_{cancer}_{thr}"
            session.run(
                """
                MERGE (pg:PatientGroup {patient_id: $pg_id})
                SET pg.gene_symbol = $gene,
                    pg.cancer_type = $cancer,
                    pg.expression_group = $thr,
                    pg.threshold_value = $median,
                    pg.source = 'by_cancer_threshold',
                    pg.n_eligible = coalesce(pg.n_eligible, 0)
                WITH pg
                MATCH (g:Gene {symbol: $gene})
                MERGE (g)-[:HAS_PATIENT_GROUP]->(pg)
                WITH pg
                OPTIONAL MATCH (d:Disease {tcga_code: $cancer})
                FOREACH (_ IN CASE WHEN d IS NULL THEN [] ELSE [1] END |
                  MERGE (d)-[:HAS_PATIENT_GROUP]->(pg)
                )
                """,
                pg_id=pg_id,
                gene=symbol,
                cancer=cancer,
                thr=thr,
                median=median,
            )
            n += 1
    log.info("%s PatientGroup rows upserted: %d", symbol, n)
    return n


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    ap = argparse.ArgumentParser()
    ap.add_argument("--symbol")
    ap.add_argument("--all", action="store_true")
    args = ap.parse_args()
    symbols = all_symbols() if args.all else [args.symbol.upper()]
    if not symbols or not symbols[0]:
        ap.error("Need --symbol or --all")
    d = _driver()
    try:
        with d.session() as s:
            before = s.run("MATCH (n) RETURN count(n) AS c").single()["c"]
            total = 0
            for sym in symbols:
                s.run("MERGE (g:Gene {symbol: $s})", s=sym)
                total += load_symbol(s, sym)
            after = s.run("MATCH (n) RETURN count(n) AS c").single()["c"]
        print({"patient_groups_touched": total, "nodes_before": before, "nodes_after": after, "delta": after - before})
    finally:
        d.close()


if __name__ == "__main__":
    main()
