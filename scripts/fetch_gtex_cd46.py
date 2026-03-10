"""Fetch CD46 mRNA expression across 54 normal human tissues from GTEx v8.

Source: GTEx Portal public API (CC BY 4.0, no account required)
https://gtexportal.org/api/v2/expression/geneExpression

Output:
  data/processed/gtex_cd46_normal.csv
    Columns: tissue_site_detail, tissue_site, median_tpm, q1_tpm, q3_tpm,
             n_samples, unit

Run:
    python scripts/fetch_gtex_cd46.py
"""
import json
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

import pandas as pd

GTEX_API   = "https://gtexportal.org/api/v2"
GENCODE_ID = "ENSG00000117335.19"   # CD46 versioned gencodeId (v26/GRCh38, confirmed via reference API)
DATASET    = "gtex_v8"
OUT_CSV    = Path("data/processed/gtex_cd46_normal.csv")
RAW_OUT    = Path("data/raw/apis/gtex_cd46.json")

RAW_OUT.parent.mkdir(parents=True, exist_ok=True)
OUT_CSV.parent.mkdir(parents=True, exist_ok=True)


def gtex_get(endpoint: str, params: dict) -> dict:
    qs  = urllib.parse.urlencode(params)
    url = f"{GTEX_API}/{endpoint}?{qs}"
    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read())


def main():
    print("=== GTEx CD46 Normal-Tissue Expression Fetcher ===")
    print(f"Gene: CD46  ({GENCODE_ID})  |  Dataset: {DATASET}\n")

    # --- 1. Fetch tissue name mapping first ---------------------------------
    print("1. Fetching GTEx tissue catalogue...")
    tissue_data = gtex_get("dataset/tissueSiteDetail", {
        "datasetId": DATASET, "pageSize": 100
    })
    tissue_map = {
        t["tissueSiteDetailId"]: {
            "tissue_site_detail": t.get("tissueSiteDetail", t["tissueSiteDetailId"]),
            "tissue_site":        t.get("tissueSite", ""),
        }
        for t in tissue_data.get("data", [])
    }
    print(f"   Got {len(tissue_map)} tissue types")

    # --- 2. Fetch gene expression per tissue --------------------------------
    print("2. Fetching gene expression by tissue from GTEx API...")
    try:
        data = gtex_get("expression/geneExpression", {
            "datasetId":    DATASET,
            "gencodeId":    GENCODE_ID,
            "itemsPerPage": 300,
        })
    except Exception as e:
        print(f"   ERROR fetching gene expression: {e}")
        sys.exit(1)

    records = data.get("data", [])
    if not records:
        print("   No records returned — check API or gene ID.")
        sys.exit(1)

    print(f"   Retrieved {len(records)} tissue-level records")

    # Save raw JSON
    RAW_OUT.write_text(json.dumps(data, indent=2))
    print(f"   Raw JSON → {RAW_OUT}")

    # --- 3. Parse into tidy table ------------------------------------------
    rows = []
    for rec in records:
        tpm_values = rec.get("data", [])
        if not tpm_values:
            continue
        tpm_sorted = sorted(tpm_values)
        n          = len(tpm_sorted)
        q1         = tpm_sorted[n // 4]      if n >= 4 else tpm_sorted[0]
        median     = tpm_sorted[n // 2]
        q3         = tpm_sorted[3 * n // 4]  if n >= 4 else tpm_sorted[-1]
        mean_tpm   = sum(tpm_sorted) / n

        tissue_id   = rec.get("tissueSiteDetailId", "")
        tissue_info = tissue_map.get(tissue_id, {
            "tissue_site_detail": tissue_id,
            "tissue_site":        "",
        })

        rows.append({
            "tissue_site_detail": tissue_info["tissue_site_detail"],
            "tissue_site":        tissue_info["tissue_site"],
            "tissue_site_id":     tissue_id,
            "median_tpm":         round(median, 4),
            "mean_tpm":           round(mean_tpm, 4),
            "q1_tpm":             round(q1, 4),
            "q3_tpm":             round(q3, 4),
            "n_samples":          n,
            "unit":               rec.get("unit", "TPM"),
            "dataset":            DATASET,
        })

    df = pd.DataFrame(rows).sort_values("median_tpm", ascending=False).reset_index(drop=True)

    # --- 3. Save -----------------------------------------------------------
    df.to_csv(OUT_CSV, index=False)
    print(f"\n2. Saved → {OUT_CSV}  ({len(df)} tissues)")

    print("\nTop 10 tissues by median CD46 TPM:")
    print(df[["tissue_site_detail","median_tpm","n_samples"]].head(10).to_string(index=False))

    print("\nBottom 5 (lowest expression) = safer tissues for 225Ac delivery:")
    print(df[["tissue_site_detail","median_tpm","n_samples"]].tail(5).to_string(index=False))

    print("\nDone. Run scripts/load_kg_gtex.py to add to AuraDB.")


if __name__ == "__main__":
    main()
