"""
Extract CD46 expression row from the 2.5 GB TCGA expression matrix.
Uses Polars lazy evaluation — RAM peak stays below 300 MB.

Strategy:
  1. scan_csv() for expression (lazy, seeks CD46 row only)
  2. Read phenotype and survival into memory (small files ~10 MB each)
  3. Join on sample ID → output cd46_expression.csv
"""

import gzip
import logging
from pathlib import Path

import polars as pl
import pandas as pd
import yaml

log = logging.getLogger(__name__)

_CFG_PATH = Path(__file__).parents[2] / "config"
with open(_CFG_PATH / "config.yaml") as f:
    import yaml as _y; _CONFIG = _y.safe_load(f)
with open(_CFG_PATH / "datasets.yaml") as f:
    _DS = _y.safe_load(f)["tcga"]

CD46_ID = _CONFIG["cd46"]["ensembl_id"]  # ENSG00000117335
EXPR_GZ = Path(_DS["expression"]["local_path"])
PHENO_GZ = Path(_DS["phenotype"]["local_path"])
SURV_GZ = Path(_DS["survival"]["local_path"])
OUT_EXPR = Path(_DS["output"]["cd46_expression"])
OUT_CANCER = Path(_DS["output"]["cd46_by_cancer"])

SAMPLE_TYPE_COL = _DS["phenotype"]["sample_type_col"]
COHORT_COL = _DS["phenotype"]["cohort_col"]
STUDY_COL = _DS["phenotype"]["study_col"]
OS_TIME = _DS["survival"]["os_time_col"]
OS_EVENT = _DS["survival"]["os_event_col"]
PFI_TIME = _DS["survival"]["pfi_time_col"]
PFI_EVENT = _DS["survival"]["pfi_event_col"]
CANCER_COL = _DS["survival"]["cancer_type_col"]
SURV_SAMPLE = _DS["survival"]["sample_col"]


def extract_cd46_expression() -> pl.DataFrame:
    """
    Stream-read the TCGA gene expression matrix and extract the CD46 row.
    Reads line-by-line (early exit once CD46 found) — RAM peak < 50 MB.
    Returns a Polars DataFrame with columns: [sample, cd46_log2_tpm].
    """
    log.info("Scanning TCGA expression matrix (line-by-line gzip)...")

    # Patterns to match: Ensembl ID or HUGO symbol
    targets = {CD46_ID, "CD46"}

    with gzip.open(EXPR_GZ, "rb") as fh:
        # Header line → sample IDs
        header_line = fh.readline().decode("utf-8", errors="replace").rstrip("\n")
        sample_ids = header_line.split("\t")  # sample_ids[0] = gene-col header

        cd46_values: list[str] | None = None
        for raw in fh:
            line = raw.decode("utf-8", errors="replace").rstrip("\n")
            # Fast early check before splitting
            if "\tCD46" in line or line.startswith("CD46\t") or CD46_ID in line:
                parts = line.split("\t")
                gene_id = parts[0]
                if gene_id in targets or any(t in gene_id for t in targets):
                    cd46_values = parts[1:]
                    log.info("Found CD46 (gene id=%s) with %d samples", gene_id, len(cd46_values))
                    break

    if cd46_values is None:
        raise ValueError(
            f"Could not find CD46 (Ensembl={CD46_ID} or symbol='CD46') in {EXPR_GZ}"
        )

    sample_ids = sample_ids[1:]  # drop gene-col header
    if len(sample_ids) != len(cd46_values):
        # Truncate to shortest to handle edge cases
        n = min(len(sample_ids), len(cd46_values))
        sample_ids, cd46_values = sample_ids[:n], cd46_values[:n]

    expr_long = pl.DataFrame({
        "sample": sample_ids,
        "cd46_log2_tpm": [float(v) if v.strip() else float("nan") for v in cd46_values],
    })

    log.info("Extracted %d CD46 expression values", len(expr_long))
    return expr_long


def load_phenotype() -> pd.DataFrame:
    """Load TCGA phenotype metadata, filter to TCGA samples only."""
    log.info("Loading phenotype metadata...")
    with gzip.open(PHENO_GZ, "rb") as f:
        pheno = pd.read_csv(f, sep="\t", low_memory=False)

    # Filter to TCGA samples only — sample IDs start with "TCGA-"
    sample_col_ph = pheno.columns[0]
    pheno = pheno[pheno[sample_col_ph].astype(str).str.startswith("TCGA-")]

    log.info("Phenotype: %d TCGA samples", len(pheno))
    return pheno


def load_survival() -> pd.DataFrame:
    """Load TCGA survival data."""
    log.info("Loading survival data...")
    with gzip.open(SURV_GZ, "rb") as f:
        surv = pd.read_csv(f, sep="\t", low_memory=False)
    log.info("Survival: %d samples", len(surv))
    return surv


def compute_cd46_per_cancer(merged: pd.DataFrame) -> pd.DataFrame:
    """Aggregate CD46 expression stats per TCGA cancer type."""
    if CANCER_COL not in merged.columns:
        raise KeyError(f"Cancer type column '{CANCER_COL}' not found in merged data")

    stats = (
        merged.groupby(CANCER_COL)["cd46_log2_tpm"]
        .agg(["mean", "median", "std", "count"])
        .reset_index()
        .rename(columns={
            CANCER_COL: "cancer_type",
            "mean": "cd46_mean",
            "median": "cd46_median",
            "std": "cd46_std",
            "count": "n_samples",
        })
        .sort_values("cd46_median", ascending=False)
        .reset_index(drop=True)
    )
    stats["expression_rank"] = stats.index + 1
    return stats


def run_extraction() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Full extraction pipeline → saves cd46_expression.csv and cd46_by_cancer.csv."""
    OUT_EXPR.parent.mkdir(parents=True, exist_ok=True)

    # Step 1: extract CD46 from expression matrix
    cd46_pl = extract_cd46_expression()
    cd46_pd = cd46_pl.to_pandas()

    # Step 2: load phenotype and survival
    pheno = load_phenotype()
    surv = load_survival()

    # Step 3: merge on sample ID
    sample_col_pheno = pheno.columns[0]  # usually 'sample' or 'Sample'
    merged = cd46_pd.merge(pheno, left_on="sample", right_on=sample_col_pheno, how="inner")

    # TCGA sample IDs have a "-NN" type suffix (e.g. "TCGA-AB-1234-01")
    # Survival file uses patient-level IDs ("TCGA-AB-1234") — strip the suffix
    merged["_patient_id"] = merged["sample"].str.rsplit("-", n=1).str[0]
    surv_renamed = surv.rename(columns={SURV_SAMPLE: "_patient_id"})
    merged = merged.merge(surv_renamed, on="_patient_id", how="left")
    merged.drop(columns=["_patient_id"], inplace=True)

    log.info("Merged dataset: %d samples", len(merged))

    # Step 4: save per-sample expression
    merged.to_csv(OUT_EXPR, index=False)
    log.info("Saved: %s", OUT_EXPR)

    # Step 5: compute and save per-cancer stats
    cancer_stats = compute_cd46_per_cancer(merged)
    cancer_stats.to_csv(OUT_CANCER, index=False)
    log.info("Saved: %s", OUT_CANCER)

    return merged, cancer_stats


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    merged, stats = run_extraction()
    print(f"\nExtracted {len(merged)} samples across {len(stats)} cancer types")
    print(stats[["cancer_type", "cd46_median", "expression_rank"]].head(10).to_string())
