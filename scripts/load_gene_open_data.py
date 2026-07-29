"""Load per-gene TCGA open data into Aura (survival + by_cancer expression).

Copies the CD46 recipe shape for other targets without overwriting CD46 Disease props.

  MERGE (g:Gene)-[:EXPRESSED_IN_CANCER]->(d:Disease)
  MERGE (g)-[:HAS_SURVIVAL]->(sr:SurvivalResult {gene_symbol, cancer, endpoint, kind})

Usage (laptop, .env Neo4j):
  python scripts/load_gene_open_data.py --symbol FOLH1
  python scripts/load_gene_open_data.py --all
"""
from __future__ import annotations

import argparse
import logging
import math
import os
import sys
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from neo4j import GraphDatabase

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT))
load_dotenv(_ROOT / ".env")

log = logging.getLogger(__name__)
DATA = _ROOT / "data" / "processed"


def _num(v, default=None):
    if v is None or (isinstance(v, float) and math.isnan(v)) or pd.isna(v):
        return default
    try:
        return float(v)
    except (TypeError, ValueError):
        return default


def _int(v, default=0):
    n = _num(v, None)
    return int(n) if n is not None else default


def load_by_cancer(session, symbol: str) -> int:
    path = DATA / f"{symbol.lower()}_by_cancer.csv"
    if not path.exists():
        log.warning("%s missing — skip by_cancer", path.name)
        return 0
    df = pd.read_csv(path)
    med_col = f"{symbol.lower()}_median"
    mean_col = f"{symbol.lower()}_mean"
    if med_col not in df.columns:
        med_col = "gene_median" if "gene_median" in df.columns else None
    if mean_col not in df.columns:
        mean_col = "gene_mean" if "gene_mean" in df.columns else None
    if not med_col:
        raise KeyError(f"No median column in {path.name}")

    cypher = """
    MERGE (g:Gene {symbol: $symbol})
    MERGE (d:Disease {tcga_code: $cancer})
    ON CREATE SET d.name = $cancer, d.source = 'TCGA'
    MERGE (g)-[r:EXPRESSED_IN_CANCER]->(d)
    SET r.median_tpm_log2 = $median,
        r.mean_tpm_log2 = $mean,
        r.n_samples = $n_samples,
        r.expression_rank = $rank,
        r.source = 'TCGA/Xena'
    """
    n = 0
    for _, row in df.iterrows():
        cancer = str(row["cancer_type"]).strip()
        if not cancer or cancer == "nan":
            continue
        session.run(
            cypher,
            symbol=symbol,
            cancer=cancer,
            median=_num(row.get(med_col)),
            mean=_num(row.get(mean_col)) if mean_col else None,
            n_samples=_int(row.get("n_samples")),
            rank=_int(row.get("expression_rank")),
        )
        n += 1
    log.info("%s EXPRESSED_IN_CANCER: %d", symbol, n)
    return n


def load_survival(session, symbol: str) -> int:
    path = DATA / f"{symbol.lower()}_survival_results.csv"
    if not path.exists():
        log.warning("%s missing — skip survival", path.name)
        return 0
    df = pd.read_csv(path)
    cypher = """
    MERGE (sr:SurvivalResult {
        gene_symbol: $gene,
        cancer_type: $cancer,
        endpoint: $endpoint,
        kind: $kind
    })
    SET sr.n_high = $n_high,
        sr.n_low = $n_low,
        sr.log_rank_p = $log_rank_p,
        sr.hazard_ratio = $hazard_ratio,
        sr.hr_lower_95 = $hr_lower_95,
        sr.hr_upper_95 = $hr_upper_95,
        sr.p_value = $p_value,
        sr.n_samples = $n_samples,
        sr.significant = $significant,
        sr.label = $gene + '_' + $cancer + '_' + $endpoint + '_' + $kind
    WITH sr
    MATCH (g:Gene {symbol: $gene})
    MERGE (g)-[:HAS_SURVIVAL]->(sr)
    WITH sr
    MERGE (d:Disease {tcga_code: $cancer})
    ON CREATE SET d.name = $cancer, d.source = 'TCGA'
    MERGE (d)-[:HAS_SURVIVAL_RESULT]->(sr)
    """
    n = 0
    for _, row in df.iterrows():
        cancer = str(row.get("cancer_type", "")).strip()
        endpoint = str(row.get("endpoint", "OS")).strip() or "OS"
        if not cancer or cancer == "nan":
            continue
        has_cox = pd.notna(row.get("hazard_ratio"))
        has_km = pd.notna(row.get("log_rank_p"))
        # One CSV row can be KM-only, Cox-only, or (rarely) mixed — pick primary kind
        if has_cox and not has_km:
            kind = "cox"
        elif has_km and not has_cox:
            kind = "km"
        elif has_cox:
            kind = "cox"
        elif has_km:
            kind = "km"
        else:
            continue
        p_val = _num(row.get("p_value"), _num(row.get("log_rank_p"), 1.0))
        session.run(
            cypher,
            gene=symbol,
            cancer=cancer,
            endpoint=endpoint,
            kind=kind,
            n_high=_int(row.get("n_high")),
            n_low=_int(row.get("n_low")),
            log_rank_p=_num(row.get("log_rank_p")),
            hazard_ratio=_num(row.get("hazard_ratio")),
            hr_lower_95=_num(row.get("hr_lower_95")),
            hr_upper_95=_num(row.get("hr_upper_95")),
            p_value=p_val,
            n_samples=_int(row.get("n_samples")),
            significant=bool(row.get("significant")) if pd.notna(row.get("significant")) else (p_val is not None and p_val < 0.05),
        )
        n += 1
    log.info("%s SurvivalResult: %d", symbol, n)
    return n


def load_gene(symbol: str) -> dict:
    uri = os.environ.get("NEO4J_URI")
    user = os.environ.get("NEO4J_USERNAME", "neo4j")
    pwd = os.environ.get("NEO4J_PASSWORD")
    if not uri or not pwd:
        raise RuntimeError("NEO4J_URI / NEO4J_PASSWORD required")

    symbol = symbol.upper()
    driver = GraphDatabase.driver(uri, auth=(user, pwd))
    driver.verify_connectivity()
    out = {"symbol": symbol}
    try:
        with driver.session() as session:
            before = session.run("MATCH (n) RETURN count(n) AS c").single()["c"]
            out["by_cancer_rels"] = load_by_cancer(session, symbol)
            out["survival_nodes"] = load_survival(session, symbol)
            after = session.run("MATCH (n) RETURN count(n) AS c").single()["c"]
            out["nodes_before"] = before
            out["nodes_after"] = after
            out["nodes_delta"] = after - before
    finally:
        driver.close()
    return out


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    ap = argparse.ArgumentParser()
    ap.add_argument("--symbol", help="e.g. FOLH1")
    ap.add_argument("--all", action="store_true", help="CD46 + FOLH1 + FAP + SSTR2 + GRPR")
    args = ap.parse_args()
    symbols = ["CD46", "FOLH1", "FAP", "SSTR2", "GRPR"] if args.all else [args.symbol]
    if not symbols[0]:
        ap.error("Need --symbol or --all")
    for sym in symbols:
        report = load_gene(sym)
        print(report)


if __name__ == "__main__":
    main()
