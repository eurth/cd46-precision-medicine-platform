"""Load a thin theranostic target slice into Aura + write processed CSVs.

Usage (laptop, with .env Neo4j credentials):
    python scripts/load_target_slice.py --symbol FOLH1

Recipe for next gene: same command with --symbol FAP (etc).
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT))
load_dotenv(_ROOT / ".env")

from neo4j import GraphDatabase  # noqa: E402

from src.knowledge_graph.target_slice import (  # noqa: E402
    fetch_open_targets,
    get_target,
    load_ot_associations,
    merge_gene_protein,
    resolve_string_ensp,
)
from src.preprocessing.extract_gene import run_extract  # noqa: E402

log = logging.getLogger(__name__)


def _counts(session) -> tuple[int, int]:
    n = session.run("MATCH (n) RETURN count(n) AS c").single()["c"]
    r = session.run("MATCH ()-[r]->() RETURN count(r) AS c").single()["c"]
    return int(n), int(r)


def _string_load(
    session,
    symbol: str,
    string_id: str,
    *,
    edge_limit: int = 200,
    required_score: int = 700,
) -> int:
    """Fetch STRING neighborhood and MERGE INTERACTS_WITH (batched UNWIND)."""
    import urllib.parse
    import urllib.request

    params = urllib.parse.urlencode(
        {
            "identifiers": string_id,
            "species": 9606,
            "required_score": required_score,
            "limit": edge_limit,
            "caller_identity": "oncobridge",
        }
    )
    url = f"https://string-db.org/api/json/network?{params}"
    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=120) as resp:
        edges = json.loads(resp.read().decode("utf-8"))

    raw_out = _ROOT / "data" / "raw" / "apis" / f"string_{symbol.lower()}.json"
    raw_out.parent.mkdir(parents=True, exist_ok=True)
    raw_out.write_text(json.dumps({"seed": string_id, "edges": edges}, indent=2), encoding="utf-8")

    genes: dict[str, str] = {symbol: string_id}
    rel_rows: list[dict] = []
    for e in edges:
        a, b = e.get("preferredName_A"), e.get("preferredName_B")
        if not a or not b:
            continue
        genes[a] = e.get("stringId_A", "") or genes.get(a, "")
        genes[b] = e.get("stringId_B", "") or genes.get(b, "")
        rel_rows.append(
            {
                "sym_a": a,
                "sym_b": b,
                "score": round(e.get("score", 0), 4),
                "escore": round(e.get("escore", 0), 4),
                "tscore": round(e.get("tscore", 0), 4),
            }
        )
    gene_rows = [{"symbol": s, "string_id": sid} for s, sid in genes.items()]
    # ponytail: batch UNWIND — per-row Aura round-trips drop connections on large STRING nets
    for i in range(0, len(gene_rows), 200):
        session.run(
            """
            UNWIND $rows AS row
            MERGE (g:Gene {symbol: row.symbol})
            ON CREATE SET g.string_id = row.string_id, g.source = 'STRING DB', g.is_ppi_partner = true
            ON MATCH SET g.string_id = coalesce(g.string_id, row.string_id)
            """,
            rows=gene_rows[i : i + 200],
        )
    for i in range(0, len(rel_rows), 200):
        session.run(
            """
            UNWIND $rows AS row
            MATCH (a:Gene {symbol: row.sym_a})
            MATCH (b:Gene {symbol: row.sym_b})
            MERGE (a)-[r:INTERACTS_WITH {source: 'STRING DB'}]->(b)
            ON CREATE SET r.score = row.score, r.escore = row.escore, r.tscore = row.tscore
            ON MATCH SET r.score = row.score
            """,
            rows=rel_rows[i : i + 200],
        )
    return len(rel_rows)


def load_slice(
    symbol: str,
    *,
    skip_extract: bool = False,
    skip_string: bool = False,
    ot_size: int = 0,
    ot_top: int = 0,
    edge_limit: int = 500,
    required_score: int = 400,
    refresh_ot: bool = False,
) -> dict:
    t = get_target(symbol)
    uri = os.getenv("NEO4J_URI")
    user = os.getenv("NEO4J_USERNAME", "neo4j")
    pwd = os.getenv("NEO4J_PASSWORD")
    if not uri or not pwd:
        raise RuntimeError("NEO4J_URI / NEO4J_PASSWORD required in .env")

    report: dict = {
        "symbol": symbol,
        "ensembl_id": t["ensembl_id"],
        "started_utc": datetime.now(timezone.utc).isoformat(),
        "ot_size": ot_size,
        "ot_top": ot_top,
        "edge_limit": edge_limit,
        "skip_string": skip_string,
        "required_score": required_score,
    }

    # 1) Expression extract (laptop)
    if not skip_extract:
        out_expr, out_cancer = run_extract(symbol, t["ensembl_id"])
        report["expression_csv"] = str(out_expr.relative_to(_ROOT))
        report["by_cancer_csv"] = str(out_cancer.relative_to(_ROOT))

    # 2) STRING id (skip resolution when OT-only)
    string_id = ""
    if not skip_string:
        string_id = t.get("string_ensp")
        if not string_id:
            string_id = resolve_string_ensp(symbol)
            report["string_ensp_resolved"] = string_id
        else:
            report["string_ensp"] = string_id

    # 3) Open Targets fetch (prefer cache unless refresh / too small)
    ot_path = _ROOT / "data" / "raw" / "apis" / f"open_targets_{symbol.lower()}.json"
    use_cache = ot_path.exists() and not refresh_ot
    if use_cache:
        ot = json.loads(ot_path.read_text(encoding="utf-8"))
        cached_rows = (
            ot.get("data", {}).get("target", {}).get("associatedDiseases", {}).get("rows")
            or []
        )
        if len(cached_rows) < min(ot_size, 50):
            use_cache = False
    if use_cache:
        report["ot_json"] = str(ot_path.relative_to(_ROOT)) + " (cache)"
    else:
        ot = fetch_open_targets(t["ensembl_id"], size=ot_size)
        ot_path.parent.mkdir(parents=True, exist_ok=True)
        ot_path.write_text(json.dumps(ot, indent=2), encoding="utf-8")
        report["ot_json"] = str(ot_path.relative_to(_ROOT)) + " (refetch)"
    ot_count = (
        ot.get("data", {}).get("target", {}).get("associatedDiseases", {}).get("count", 0)
    )
    report["ot_assoc_count"] = ot_count

    driver = GraphDatabase.driver(uri, auth=(user, pwd))
    driver.verify_connectivity()
    try:
        with driver.session() as session:
            before = _counts(session)
            report["nodes_before"], report["rels_before"] = before

            merge_gene_protein(session, t)
            diseases, rels = load_ot_associations(session, symbol, ot, top_n=ot_top)
            report["ot_disease_nodes_top"], report["ot_assoc_rels"] = diseases, rels

            if skip_string:
                report["string_rels"] = 0
            else:
                time.sleep(0.5)
                string_rels = _string_load(
                    session,
                    symbol,
                    string_id,
                    edge_limit=edge_limit,
                    required_score=required_score,
                )
                report["string_rels"] = string_rels

            after = _counts(session)
            report["nodes_after"], report["rels_after"] = after
            report["nodes_delta"] = after[0] - before[0]
            report["rels_delta"] = after[1] - before[1]
    finally:
        driver.close()

    report["finished_utc"] = datetime.now(timezone.utc).isoformat()
    return report


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    ap = argparse.ArgumentParser()
    ap.add_argument("--symbol", required=True, help="Registry symbol e.g. FOLH1")
    ap.add_argument("--skip-extract", action="store_true")
    ap.add_argument("--skip-string", action="store_true", help="Skip STRING PPI (OT-only Wave 1)")
    ap.add_argument(
        "--ot-size",
        type=int,
        default=0,
        help="OT associations to fetch; 0=full API total (default, no research truncation)",
    )
    ap.add_argument(
        "--ot-top",
        type=int,
        default=0,
        help="Deprecated (all fetched associations are MERGED); kept for CLI compat",
    )
    ap.add_argument("--edge-limit", type=int, default=500, help="STRING API network limit (API param)")
    ap.add_argument(
        "--required-score",
        type=int,
        default=400,
        help="STRING confidence threshold 0-1000 (research filter, not a row truncate)",
    )
    ap.add_argument("--refresh-ot", action="store_true", help="Ignore OT JSON cache")
    args = ap.parse_args()
    symbol = args.symbol.upper()
    report = load_slice(
        symbol,
        skip_extract=args.skip_extract,
        skip_string=args.skip_string,
        ot_size=args.ot_size,
        ot_top=args.ot_top,
        edge_limit=args.edge_limit,
        required_score=args.required_score,
        refresh_ot=args.refresh_ot,
    )

    out = _ROOT / "reports" / f"phase4_{symbol.lower()}_load.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        f"# Target open-data slice — {symbol}",
        "",
        f"Generated: {report.get('finished_utc')}",
        "",
        "| Metric | Value |",
        "|--------|-------|",
    ]
    for k, v in report.items():
        lines.append(f"| `{k}` | {v} |")
    lines += ["", ""]
    out.write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps(report, indent=2))
    print(f"Wrote {out}")


if __name__ == "__main__":
    main()
