"""Fetch CD46 clinical variant records from NCBI ClinVar.

Source: NCBI E-utilities (public, free, no account for ≤3 req/s)
  https://www.ncbi.nlm.nih.gov/clinvar/

Output:
  data/processed/clinvar_cd46_variants.csv
    Columns: variation_id, name, clinical_significance, review_status,
             condition, variant_type, chromosome_change, rs_id, last_updated

Run:
    python scripts/fetch_clinvar_cd46.py
"""
import json
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

import pandas as pd

NCBI_BASE  = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
CLINVAR_JS = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"
GENE_SYMBOL = "CD46"
GENE_ID     = "4179"    # NCBI Gene ID for CD46
OUT_CSV     = Path("data/processed/clinvar_cd46_variants.csv")
RAW_OUT     = Path("data/raw/apis/clinvar_cd46.json")

OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
RAW_OUT.parent.mkdir(parents=True, exist_ok=True)


def ncbi_get(endpoint: str, params: dict) -> dict:
    params["retmode"] = "json"
    qs  = urllib.parse.urlencode(params)
    url = f"{NCBI_BASE}/{endpoint}?{qs}"
    req = urllib.request.Request(url, headers={"User-Agent": "cd46_platform/1.0 (research)"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read())


def clinvar_variant_api(variation_ids: list[str]) -> dict:
    """Use the ClinVar API (not E-utils) for richer variant data."""
    base = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"
    params = {
        "db":      "clinvar",
        "id":      ",".join(variation_ids),
        "retmode": "json",
    }
    qs  = urllib.parse.urlencode(params)
    url = f"{base}?{qs}"
    req = urllib.request.Request(url, headers={"User-Agent": "cd46_platform/1.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read())


def main():
    print("=== ClinVar CD46 Variant Fetcher ===")
    print(f"Gene: {GENE_SYMBOL}  (NCBI Gene ID: {GENE_ID})\n")

    # --- 1. Search ClinVar for CD46 variants --------------------------------
    print("1. Searching ClinVar for CD46[gene] variants...")
    search_result = ncbi_get("esearch.fcgi", {
        "db":     "clinvar",
        "term":   f"{GENE_SYMBOL}[gene]",
        "retmax": 500,
    })
    ids = search_result.get("esearchresult", {}).get("idlist", [])
    print(f"   Found {len(ids)} variant records in ClinVar")

    if not ids:
        print("   No variants found. Exiting.")
        sys.exit(0)

    # --- 2. Fetch summaries in batches of 100 -------------------------------
    print("2. Fetching variant summaries...")
    all_summaries = {}
    batch_size = 100
    for i in range(0, len(ids), batch_size):
        batch = ids[i:i+batch_size]
        time.sleep(0.4)  # NCBI rate limit: ≤3 req/s without API key
        summaries = clinvar_variant_api(batch)
        result    = summaries.get("result", {})
        for vid in result.get("uids", []):
            all_summaries[vid] = result[vid]
        print(f"   Fetched batch {i//batch_size + 1}: {len(batch)} records")

    # Save raw
    RAW_OUT.write_text(json.dumps(all_summaries, indent=2))
    print(f"   Raw JSON → {RAW_OUT}")

    # --- 3. Parse into tidy table -------------------------------------------
    print("3. Parsing variant summaries...")
    rows = []
    for vid, rec in all_summaries.items():
        if not isinstance(rec, dict):
            continue

        # Clinical significance
        germline = rec.get("germline_classification", {})
        sig      = germline.get("description", rec.get("clinical_significance", {}).get("description", "Unknown"))

        # Conditions
        trait_set = rec.get("trait_set", [])
        conditions = "; ".join(
            t.get("trait_name", "") for t in trait_set if t.get("trait_name")
        ) if isinstance(trait_set, list) else ""

        # Gene info
        genes = rec.get("genes", [])
        gene_sym = genes[0].get("symbol", GENE_SYMBOL) if genes else GENE_SYMBOL

        # Variant details
        variation_set = rec.get("variation_set", [])
        variant_type  = variation_set[0].get("variation_type", "") if variation_set else ""
        chrom_change  = variation_set[0].get("cdna_change", "") if variation_set else ""
        protein_change = variation_set[0].get("protein_change", "") if variation_set else ""

        # dbSNP
        xrefs = rec.get("supporting_submissions", {}).get("rcv", [])
        rs_id = ""
        for xref in rec.get("variation_set", []):
            for x in xref.get("variation_xrefs", []):
                if x.get("db_source") == "dbSNP":
                    rs_id = "rs" + str(x.get("db_id", ""))
                    break

        rows.append({
            "variation_id":        vid,
            "name":                rec.get("title", ""),
            "gene_symbol":         gene_sym,
            "clinical_significance": sig,
            "review_status":       germline.get("review_status", rec.get("review_status", "")),
            "condition":           conditions,
            "variant_type":        variant_type,
            "cdna_change":         chrom_change,
            "protein_change":      protein_change,
            "rs_id":               rs_id,
            "last_updated":        rec.get("date_last_updated", ""),
        })

    df = pd.DataFrame(rows)

    # Prioritise pathogenic/likely pathogenic
    sig_order = {
        "Pathogenic": 0, "Likely pathogenic": 1,
        "Pathogenic/Likely pathogenic": 2,
        "Uncertain significance": 3,
        "Benign": 4, "Likely benign": 5,
    }
    df["_sort"] = df["clinical_significance"].map(sig_order).fillna(9)
    df = df.sort_values("_sort").drop(columns="_sort").reset_index(drop=True)

    df.to_csv(OUT_CSV, index=False)
    print(f"\n4. Saved → {OUT_CSV}  ({len(df)} variants)")

    print("\nClinical significance breakdown:")
    print(df["clinical_significance"].value_counts().to_string())

    pathogenic = df[df["clinical_significance"].str.contains("Pathogenic|pathogenic", na=False, case=False)]
    print(f"\nPathogenic / Likely pathogenic variants: {len(pathogenic)}")
    if not pathogenic.empty:
        print(pathogenic[["variation_id","name","condition","cdna_change"]].head(10).to_string(index=False))

    print("\nDone.")


if __name__ == "__main__":
    main()
