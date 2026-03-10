"""Fetch CD46 somatic mutation and copy-number alteration (CNA) frequencies
from cBioPortal across all TCGA cancer types.

Source: cBioPortal public REST API (CC BY 4.0, no account required)
  https://www.cbioportal.org/api

Output:
  data/processed/cd46_mutations_by_cancer.csv
    Columns: cancer_type, study_id, total_samples, mutated_samples,
             mutation_freq_pct, cna_amp_samples, cna_del_samples,
             cna_amp_freq_pct, cna_del_freq_pct, gene_symbol

Run:
    python scripts/fetch_cbioportal_mutations.py
"""
import json
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

import pandas as pd

CBIOPORTAL  = "https://www.cbioportal.org/api"
GENE_SYMBOL = "CD46"
ENTREZ_ID   = 4179       # NCBI Gene ID for CD46
OUT_CSV     = Path("data/processed/cd46_mutations_by_cancer.csv")
RAW_MUT     = Path("data/raw/apis/cbioportal_cd46_mutations.json")
RAW_CNA     = Path("data/raw/apis/cbioportal_cd46_cna.json")

OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
RAW_MUT.parent.mkdir(parents=True, exist_ok=True)


def api_get(path: str, params: dict = None) -> list | dict:
    url = f"{CBIOPORTAL}{path}"
    if params:
        url += "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={
        "Accept":     "application/json",
        "User-Agent": "cd46_platform/1.0",
    })
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read())


def api_post(path: str, body: dict) -> list | dict:
    url  = f"{CBIOPORTAL}{path}"
    data = json.dumps(body).encode()
    req  = urllib.request.Request(url, data=data, headers={
        "Accept":       "application/json",
        "Content-Type": "application/json",
        "User-Agent":   "cd46_platform/1.0",
    })
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read())


# TCGA pan-cancer study IDs (provisional — contain mutation + CNA data)
TCGA_STUDIES = [
    "acc_tcga", "blca_tcga", "brca_tcga", "cesc_tcga", "chol_tcga",
    "coad_tcga", "dlbc_tcga", "esca_tcga", "gbm_tcga", "hnsc_tcga",
    "kich_tcga", "kirc_tcga", "kirp_tcga", "laml_tcga", "lgg_tcga",
    "lihc_tcga", "luad_tcga", "lusc_tcga", "meso_tcga", "ov_tcga",
    "paad_tcga", "pcpg_tcga", "prad_tcga", "read_tcga", "sarc_tcga",
    "skcm_tcga", "stad_tcga", "stes_tcga", "tgct_tcga", "thca_tcga",
    "thym_tcga", "ucec_tcga", "ucs_tcga", "uvm_tcga",
]


def get_study_info(study_id: str) -> dict:
    """Return study dict with totalSampleCount, or {}."""
    try:
        return api_get(f"/studies/{study_id}")
    except Exception:
        return {}


def get_mutation_counts(study_id: str, total_samples: int) -> int:
    """Return number of samples with a CD46 mutation in this study."""
    try:
        # Standard cBioPortal mutation profile ID convention
        profile_id = f"{study_id}_mutations"
        mutations = api_post("/mutations/fetch", {
            "entrezGeneIds":      [ENTREZ_ID],
            "molecularProfileIds": [profile_id],
        })
        if not isinstance(mutations, list):
            return 0
        return len(set(m.get("sampleId", "") for m in mutations if isinstance(m, dict)))
    except Exception:
        return 0


def get_cna_counts(study_id: str, total_samples: int) -> tuple[int, int]:
    """Return (amp_samples, homdel_samples) for CD46 in this study."""
    try:
        profile_id = f"{study_id}_gistic"   # standard GISTIC CNA profile
        cnas = api_post("/discrete-copy-number/fetch", {
            "entrezGeneIds":      [ENTREZ_ID],
            "molecularProfileIds": [profile_id],
            "alterationTypes":    ["AMP", "HOMDEL"],
        })
        if not isinstance(cnas, list):
            return (0, 0)
        amp    = sum(1 for c in cnas if isinstance(c, dict) and c.get("alteration") == 2)
        homdel = sum(1 for c in cnas if isinstance(c, dict) and c.get("alteration") == -2)
        return (amp, homdel)
    except Exception:
        return (0, 0)


def study_id_to_cancer_type(study_id: str) -> str:
    return study_id.split("_")[0].upper()


def main():
    print("=== cBioPortal CD46 Mutation & CNA Fetcher ===")
    print(f"Gene: {GENE_SYMBOL}  (Entrez: {ENTREZ_ID})")
    print(f"Studies: {len(TCGA_STUDIES)} TCGA pan-cancer\n")

    rows = []
    for study_id in TCGA_STUDIES:
        cancer_type = study_id_to_cancer_type(study_id)
        print(f"  {cancer_type:8s} ({study_id}) ...", end="", flush=True)

        study_info = get_study_info(study_id)
        total      = study_info.get("sequencedSampleCount", 0)

        mutated        = get_mutation_counts(study_id, total)
        amp, homdel    = get_cna_counts(study_id, total)

        mut_pct  = round(mutated / total * 100, 2) if total > 0 else 0.0
        amp_pct  = round(amp / total * 100, 2)     if total > 0 else 0.0
        del_pct  = round(homdel / total * 100, 2)  if total > 0 else 0.0

        rows.append({
            "cancer_type":       cancer_type,
            "study_id":          study_id,
            "total_samples":     total,
            "mutated_samples":   mutated,
            "mutation_freq_pct": mut_pct,
            "cna_amp_samples":   amp,
            "cna_del_samples":   homdel,
            "cna_amp_freq_pct":  amp_pct,
            "cna_del_freq_pct":  del_pct,
            "gene_symbol":       GENE_SYMBOL,
        })
        print(f" n={total}, mut={mutated} ({mut_pct}%), AMP={amp} ({amp_pct}%), DEL={homdel}")
        time.sleep(0.3)

    df = pd.DataFrame(rows).sort_values("mutation_freq_pct", ascending=False).reset_index(drop=True)
    df.to_csv(OUT_CSV, index=False)
    print(f"\nSaved → {OUT_CSV}  ({len(df)} cancer types)")

    print("\nTop 10 by mutation frequency:")
    print(df[["cancer_type","total_samples","mutated_samples","mutation_freq_pct",
              "cna_amp_freq_pct","cna_del_freq_pct"]].head(10).to_string(index=False))

    print("\nDone.")


if __name__ == "__main__":
    main()
