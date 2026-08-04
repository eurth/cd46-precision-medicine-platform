"""Wave 7 — per-gene ClinVar variants into Aura (open-data recipe).

Usage (laptop, .env Neo4j):
  python scripts/load_gene_clinvar.py --symbol FOLH1
  python scripts/load_gene_clinvar.py --all-non-cd46 --max-variants 75
  python scripts/load_gene_clinvar.py --all-non-cd46 --dry-run   # no Neo4j / no fetch

Schema:
  (:Protein)-[:HAS_VARIANT]->(:ProteinVariant {source:'ClinVar', clinvar_id, ...})

Caps (Aura Free): default 100 variants/gene (pathogenic-first ordering from fetch).
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import sys
import time
from pathlib import Path
from typing import Any

import pandas as pd
from dotenv import load_dotenv

_ROOT = Path(__file__).resolve().parents[1]
_SCRIPTS = _ROOT / "scripts"
sys.path.insert(0, str(_SCRIPTS))
sys.path.insert(0, str(_ROOT))
load_dotenv(_ROOT / ".env")

import fetch_clinvar_cd46 as clinvar_fetch  # noqa: E402

log = logging.getLogger(__name__)
PROC = _ROOT / "data" / "processed"
DEFAULT_MAX = clinvar_fetch.DEFAULT_MAX


def clinvar_variant_id(variation_id: str | int) -> str:
    return f"CLINVAR_{variation_id}"


def _driver():
    from neo4j import GraphDatabase

    uri = os.environ.get("NEO4J_URI")
    user = os.environ.get("NEO4J_USERNAME", "neo4j")
    pwd = os.environ.get("NEO4J_PASSWORD")
    if not uri or not pwd:
        raise RuntimeError("NEO4J_URI / NEO4J_PASSWORD required")
    d = GraphDatabase.driver(uri, auth=(user, pwd))
    d.verify_connectivity()
    return d


CLINVAR_CYPHER = """
MATCH (p:Protein)
WHERE p.symbol = $gene OR p.gene_symbol = $gene
WITH p LIMIT 1
MERGE (v:ProteinVariant {variant_id: $variant_id})
ON CREATE SET
    v.clinvar_id = $clinvar_id,
    v.name = $name,
    v.clinical_significance = $clinical_significance,
    v.review_status = $review_status,
    v.condition = $condition,
    v.variant_type = $variant_type,
    v.cdna_change = $cdna_change,
    v.protein_change = $protein_change,
    v.dbsnp_id = $dbsnp_id,
    v.last_updated = $last_updated,
    v.gene_symbol = $gene,
    v.source = 'ClinVar'
ON MATCH SET
    v.clinical_significance = $clinical_significance,
    v.review_status = $review_status,
    v.last_updated = $last_updated
MERGE (p)-[:HAS_VARIANT]->(v)
"""


def load_clinvar_variants(session, symbol: str, df: pd.DataFrame) -> int:
    n = 0
    for _, row in df.iterrows():
        vid = str(row.get("variation_id", "")).strip()
        if not vid:
            continue
        session.run(
            CLINVAR_CYPHER,
            gene=symbol,
            variant_id=clinvar_variant_id(vid),
            clinvar_id=vid,
            name=str(row.get("name") or ""),
            clinical_significance=str(row.get("clinical_significance") or ""),
            review_status=str(row.get("review_status") or ""),
            condition=str(row.get("condition") or ""),
            variant_type=str(row.get("variant_type") or ""),
            cdna_change=str(row.get("cdna_change") or ""),
            protein_change=str(row.get("protein_change") or ""),
            dbsnp_id=str(row.get("rs_id") or ""),
            last_updated=str(row.get("last_updated") or ""),
        )
        n += 1
    log.info("%s ClinVar variants loaded: %d", symbol, n)
    return n


def run_symbol(
    symbol: str,
    *,
    refresh: bool = False,
    max_variants: int = DEFAULT_MAX,
    dry_run: bool = False,
) -> dict[str, Any]:
    symbol = symbol.upper()
    clinvar_fetch.get_target(symbol)
    report: dict[str, Any] = {"symbol": symbol, "dry_run": dry_run}

    out_csv, _ = clinvar_fetch.paths_for(symbol)
    if dry_run:
        if not out_csv.exists():
            report["error"] = f"no cached CSV at {out_csv}; run fetch first"
            return report
        df = pd.read_csv(out_csv).head(max_variants)
        report["variants_ready"] = len(df)
        report["csv"] = str(out_csv)
        pathogenic = df[
            df["clinical_significance"].astype(str).str.contains(
                "Pathogenic|pathogenic", case=False, na=False
            )
        ]
        report["pathogenic_count"] = len(pathogenic)
        return report

    df = clinvar_fetch.fetch_clinvar(symbol, max_variants=max_variants, refresh=refresh)
    report["variants_fetched"] = len(df)

    PROC.mkdir(parents=True, exist_ok=True)
    summary = {
        "symbol": symbol,
        "variant_count": len(df),
        "pathogenic_count": int(
            df["clinical_significance"]
            .astype(str)
            .str.contains("Pathogenic|pathogenic", case=False, na=False)
            .sum()
        )
        if not df.empty
        else 0,
    }
    (PROC / f"step7_clinvar_{symbol.lower()}_summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )

    driver = _driver()
    try:
        with driver.session() as session:
            before = session.run("MATCH (n) RETURN count(n) AS c").single()["c"]
            session.run("MERGE (g:Gene {symbol: $s})", s=symbol)
            report["variants_loaded"] = load_clinvar_variants(session, symbol, df)
            after = session.run("MATCH (n) RETURN count(n) AS c").single()["c"]
            report["nodes_before"] = before
            report["nodes_after"] = after
            report["nodes_delta"] = after - before
            report["has_variant_rels"] = session.run(
                """
                MATCH (p:Protein)-[:HAS_VARIANT]->(v:ProteinVariant)
                WHERE v.source = 'ClinVar' AND v.gene_symbol = $s
                RETURN count(*) AS c
                """,
                s=symbol,
            ).single()["c"]
    finally:
        driver.close()
    return report


def _self_check() -> None:
    assert clinvar_variant_id("123") == "CLINVAR_123"
    assert clinvar_fetch.paths_for("FAP")[0].name == "clinvar_fap_variants.csv"


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    ap = argparse.ArgumentParser()
    ap.add_argument("--symbol")
    ap.add_argument("--all-non-cd46", action="store_true")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--refresh", action="store_true", help="Re-fetch from NCBI even if CSV exists")
    ap.add_argument("--max-variants", type=int, default=DEFAULT_MAX)
    ap.add_argument("--dry-run", action="store_true", help="Parse cached CSV only; no fetch/Neo4j")
    ap.add_argument("--self-check", action="store_true")
    args = ap.parse_args()

    if args.self_check:
        clinvar_fetch._self_check()
        _self_check()
        print("self-check OK")
        return

    if args.all:
        symbols = ["CD46", "FOLH1", "FAP", "SSTR2", "GRPR"]
    elif args.all_non_cd46:
        symbols = ["FOLH1", "FAP", "SSTR2", "GRPR"]
    elif args.symbol:
        symbols = [args.symbol.upper()]
    else:
        ap.error("Need --symbol, --all-non-cd46, or --all")

    reports = []
    for i, sym in enumerate(symbols):
        if i:
            time.sleep(1.0)
        reports.append(
            run_symbol(
                sym,
                refresh=args.refresh,
                max_variants=args.max_variants,
                dry_run=args.dry_run,
            )
        )
        print(json.dumps(reports[-1], indent=2))

    out = _ROOT / "reports" / "step7_clinvar.md"
    lines = [
        "# Step 7 — ClinVar per target",
        "",
        "| Gene | Variants | Pathogenic | Nodes Δ |",
        "|------|----------|------------|---------|",
    ]
    for r in reports:
        lines.append(
            f"| {r['symbol']} | {r.get('variants_loaded', r.get('variants_ready', '?'))} | "
            f"{r.get('pathogenic_count', '—')} | {r.get('nodes_delta', '—')} |"
        )
    lines += [
        "",
        "Schema: `Protein-[:HAS_VARIANT]->ProteinVariant` (`source='ClinVar'`).",
        "",
        "```bash",
        "# Wave 7 — fetch then load (non-CD46)",
        "python scripts/fetch_clinvar_cd46.py --all-non-cd46 --max-variants 75 --refresh",
        "python scripts/load_gene_clinvar.py --all-non-cd46 --max-variants 75",
        "```",
        "",
    ]
    if not args.dry_run:
        out.write_text("\n".join(lines), encoding="utf-8")
        print(f"Wrote {out}")


if __name__ == "__main__":
    main()
