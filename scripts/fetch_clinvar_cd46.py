"""Fetch clinical variant records from NCBI ClinVar (per gene).

Source: NCBI E-utilities (public, free, no account for ≤3 req/s)
  https://www.ncbi.nlm.nih.gov/clinvar/

Output (per gene):
  data/processed/clinvar_{symbol}_variants.csv
  data/raw/apis/clinvar_{symbol}.json

Run:
    python scripts/fetch_clinvar_cd46.py                         # CD46 (backward compat)
    python scripts/fetch_clinvar_cd46.py --symbol FOLH1
    python scripts/fetch_clinvar_cd46.py --all-non-cd46 --max-variants 50
"""
from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

import pandas as pd
import yaml

_ROOT = Path(__file__).resolve().parents[1]
TARGETS_YAML = _ROOT / "config" / "targets.yaml"
PROC = _ROOT / "data" / "processed"
RAW = _ROOT / "data" / "raw" / "apis"

NCBI_BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
DEFAULT_MAX = 0  # 0 = load all ClinVar hits returned for the gene search
SIG_ORDER = {
    "Pathogenic": 0,
    "Likely pathogenic": 1,
    "Pathogenic/Likely pathogenic": 2,
    "Uncertain significance": 3,
    "Benign": 4,
    "Likely benign": 5,
}


def get_target(symbol: str) -> dict[str, Any]:
    with TARGETS_YAML.open(encoding="utf-8") as f:
        reg = yaml.safe_load(f) or {}
    t = (reg.get("targets") or {}).get(symbol.upper())
    if not t:
        raise KeyError(symbol)
    return {"symbol": symbol.upper(), **t}


def paths_for(symbol: str) -> tuple[Path, Path]:
    sym = symbol.lower()
    return PROC / f"clinvar_{sym}_variants.csv", RAW / f"clinvar_{sym}.json"


def ncbi_get(endpoint: str, params: dict) -> dict:
    params = dict(params)
    params["retmode"] = "json"
    qs = urllib.parse.urlencode(params)
    url = f"{NCBI_BASE}/{endpoint}?{qs}"
    req = urllib.request.Request(url, headers={"User-Agent": "cd46_platform/1.0 (research)"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read())


def clinvar_variant_api(variation_ids: list[str]) -> dict:
    base = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"
    params = {"db": "clinvar", "id": ",".join(variation_ids), "retmode": "json"}
    qs = urllib.parse.urlencode(params)
    url = f"{base}?{qs}"
    req = urllib.request.Request(url, headers={"User-Agent": "cd46_platform/1.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read())


def parse_summaries(all_summaries: dict, default_gene: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for vid, rec in all_summaries.items():
        if not isinstance(rec, dict):
            continue

        germline = rec.get("germline_classification", {})
        sig = germline.get(
            "description",
            rec.get("clinical_significance", {}).get("description", "Unknown"),
        )

        trait_set = rec.get("trait_set", [])
        conditions = (
            "; ".join(t.get("trait_name", "") for t in trait_set if t.get("trait_name"))
            if isinstance(trait_set, list)
            else ""
        )

        genes = rec.get("genes", [])
        gene_sym = genes[0].get("symbol", default_gene) if genes else default_gene

        variation_set = rec.get("variation_set", [])
        variant_type = variation_set[0].get("variation_type", "") if variation_set else ""
        chrom_change = variation_set[0].get("cdna_change", "") if variation_set else ""
        protein_change = variation_set[0].get("protein_change", "") if variation_set else ""

        rs_id = ""
        for xref in rec.get("variation_set", []):
            for x in xref.get("variation_xrefs", []):
                if x.get("db_source") == "dbSNP":
                    rs_id = "rs" + str(x.get("db_id", ""))
                    break
            if rs_id:
                break

        rows.append(
            {
                "variation_id": vid,
                "name": rec.get("title", ""),
                "gene_symbol": gene_sym,
                "clinical_significance": sig,
                "review_status": germline.get(
                    "review_status", rec.get("review_status", "")
                ),
                "condition": conditions,
                "variant_type": variant_type,
                "cdna_change": chrom_change,
                "protein_change": protein_change,
                "rs_id": rs_id,
                "last_updated": rec.get("date_last_updated", ""),
            }
        )
    return rows


def sort_variants(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["_sort"] = out["clinical_significance"].map(SIG_ORDER).fillna(9)
    return out.sort_values("_sort").drop(columns="_sort").reset_index(drop=True)


def fetch_clinvar(
    symbol: str,
    *,
    max_variants: int = DEFAULT_MAX,
    refresh: bool = True,
) -> pd.DataFrame:
    """Fetch ClinVar variants for *symbol*; return capped DataFrame and write CSV/JSON."""
    symbol = symbol.upper()
    t = get_target(symbol)
    out_csv, raw_out = paths_for(symbol)
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    raw_out.parent.mkdir(parents=True, exist_ok=True)

    if out_csv.exists() and not refresh:
        df = sort_variants(pd.read_csv(out_csv))
        return df if max_variants <= 0 else df.head(max_variants)

    # retmax: full gene search (NCBI allows large retmax; paginate if needed later)
    retmax = 10_000 if max_variants <= 0 else max(max_variants, 100)
    search_result = ncbi_get(
        "esearch.fcgi",
        {
            "db": "clinvar",
            "term": f"{symbol}[gene]",
            "retmax": retmax,
        },
    )
    ids = search_result.get("esearchresult", {}).get("idlist", [])
    if not ids:
        df = pd.DataFrame(
            columns=[
                "variation_id",
                "name",
                "gene_symbol",
                "clinical_significance",
                "review_status",
                "condition",
                "variant_type",
                "cdna_change",
                "protein_change",
                "rs_id",
                "last_updated",
            ]
        )
        df.to_csv(out_csv, index=False)
        raw_out.write_text("{}", encoding="utf-8")
        return df

    all_summaries: dict[str, Any] = {}
    batch_size = 100
    for i in range(0, len(ids), batch_size):
        batch = ids[i : i + batch_size]
        time.sleep(0.4)
        summaries = clinvar_variant_api(batch)
        result = summaries.get("result", {})
        for vid in result.get("uids", []):
            all_summaries[vid] = result[vid]

    raw_out.write_text(json.dumps(all_summaries, indent=2), encoding="utf-8")
    df = sort_variants(pd.DataFrame(parse_summaries(all_summaries, symbol)))
    if max_variants > 0:
        df = df.head(max_variants)
    df.to_csv(out_csv, index=False)
    _ = t  # entrez_id reserved for future gene-id search fallback
    return df


def _self_check() -> None:
    assert paths_for("CD46")[0].name == "clinvar_cd46_variants.csv"
    rows = parse_summaries(
        {
            "42": {
                "title": "NM_test",
                "genes": [{"symbol": "FOLH1"}],
                "germline_classification": {"description": "Pathogenic"},
                "variation_set": [{"variation_type": "single nucleotide variant"}],
            }
        },
        "FOLH1",
    )
    assert rows[0]["gene_symbol"] == "FOLH1"
    assert rows[0]["clinical_significance"] == "Pathogenic"


def main() -> None:
    ap = argparse.ArgumentParser(description="Fetch ClinVar variants per gene")
    ap.add_argument("--symbol")
    ap.add_argument("--all-non-cd46", action="store_true")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--max-variants", type=int, default=DEFAULT_MAX)
    ap.add_argument("--refresh", action="store_true")
    ap.add_argument("--self-check", action="store_true")
    args = ap.parse_args()

    if args.self_check:
        _self_check()
        print("self-check OK")
        return

    if args.all:
        from src.knowledge_graph.registry import all_symbols

        symbols = all_symbols()
    elif args.all_non_cd46:
        from src.knowledge_graph.registry import non_cd46_symbols

        symbols = non_cd46_symbols()
    elif args.symbol:
        symbols = [args.symbol.upper()]
    else:
        symbols = ["CD46"]

    for i, sym in enumerate(symbols):
        if i:
            time.sleep(1.0)
        print(f"=== ClinVar {sym} ===")
        df = fetch_clinvar(sym, max_variants=args.max_variants, refresh=args.refresh)
        out_csv, _ = paths_for(sym)
        print(f"Saved → {out_csv}  ({len(df)} variants)")
        if not df.empty and "clinical_significance" in df.columns:
            print(df["clinical_significance"].value_counts().to_string())
    print("Done.")


if __name__ == "__main__":
    main()
