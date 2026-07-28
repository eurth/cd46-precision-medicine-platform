"""Extract one gene row from TCGA/Xena matrix → data/processed/{gene}_*.csv."""
from __future__ import annotations

import argparse
import gzip
import logging
from pathlib import Path

import pandas as pd
import yaml

log = logging.getLogger(__name__)
_ROOT = Path(__file__).resolve().parents[2]


def _load_ds() -> dict:
    with (_ROOT / "config" / "datasets.yaml").open(encoding="utf-8") as f:
        return yaml.safe_load(f)["tcga"]


def extract_gene_expression(symbol: str, ensembl_id: str) -> pd.DataFrame:
    ds = _load_ds()
    expr_gz = Path(ds["expression"]["local_path"])
    if not expr_gz.is_absolute():
        expr_gz = _ROOT / expr_gz
    if not expr_gz.exists():
        raise FileNotFoundError(f"Missing Xena matrix: {expr_gz}")

    targets = {ensembl_id, symbol, f"{ensembl_id}.{symbol}"}
    log.info("Scanning %s for %s / %s ...", expr_gz, symbol, ensembl_id)
    with gzip.open(expr_gz, "rb") as fh:
        header_line = fh.readline().decode("utf-8", errors="replace").rstrip("\n")
        sample_ids = header_line.split("\t")
        values = None
        for raw in fh:
            line = raw.decode("utf-8", errors="replace").rstrip("\n")
            if symbol not in line and ensembl_id not in line:
                continue
            parts = line.split("\t")
            gene_id = parts[0]
            if gene_id in targets or gene_id.startswith(ensembl_id) or gene_id.endswith(symbol):
                values = parts[1:]
                log.info("Found gene_id=%s samples=%d", gene_id, len(values))
                break
    if values is None:
        raise ValueError(f"{symbol} / {ensembl_id} not found in {expr_gz}")

    sample_ids = sample_ids[1:]
    n = min(len(sample_ids), len(values))
    col = f"{symbol.lower()}_log2_tpm"

    def _to_float(v: str) -> float:
        s = str(v).strip()
        if not s or s.upper() in {"NA", "NAN", "NULL", "."}:
            return float("nan")
        return float(s)

    return pd.DataFrame(
        {
            "sample": sample_ids[:n],
            col: [_to_float(v) for v in values[:n]],
        }
    )


def by_cancer_stats(expr: pd.DataFrame, symbol: str) -> pd.DataFrame:
    ds = _load_ds()
    pheno_gz = Path(ds["phenotype"]["local_path"])
    surv_gz = Path(ds["survival"]["local_path"])
    if not pheno_gz.is_absolute():
        pheno_gz = _ROOT / pheno_gz
        surv_gz = _ROOT / surv_gz
    cancer_col = ds["survival"]["cancer_type_col"]
    surv_sample = ds["survival"]["sample_col"]
    expr_col = f"{symbol.lower()}_log2_tpm"

    with gzip.open(pheno_gz, "rb") as f:
        pheno = pd.read_csv(f, sep="\t", low_memory=False)
    sample_col_ph = pheno.columns[0]
    pheno = pheno[pheno[sample_col_ph].astype(str).str.startswith("TCGA-")]

    with gzip.open(surv_gz, "rb") as f:
        surv = pd.read_csv(f, sep="\t", low_memory=False)

    merged = expr.merge(pheno, left_on="sample", right_on=sample_col_ph, how="inner")
    merged["_patient_id"] = merged["sample"].str.rsplit("-", n=1).str[0]
    surv_renamed = surv.rename(columns={surv_sample: "_patient_id"})
    merged = merged.merge(surv_renamed, on="_patient_id", how="left")

    if cancer_col not in merged.columns:
        raise KeyError(cancer_col)

    prefix = symbol.lower()
    stats = (
        merged.groupby(cancer_col)[expr_col]
        .agg(["mean", "median", "std", "count"])
        .reset_index()
        .rename(
            columns={
                cancer_col: "cancer_type",
                "mean": f"{prefix}_mean",
                "median": f"{prefix}_median",
                "std": f"{prefix}_std",
                "count": "n_samples",
            }
        )
        .sort_values(f"{prefix}_median", ascending=False)
        .reset_index(drop=True)
    )
    stats["expression_rank"] = stats.index + 1
    # Gene-neutral aliases for UI
    stats["gene_median"] = stats[f"{prefix}_median"]
    stats["gene_mean"] = stats[f"{prefix}_mean"]
    return stats, merged


def run_extract(symbol: str, ensembl_id: str) -> tuple[Path, Path]:
    out_dir = _ROOT / "data" / "processed"
    out_dir.mkdir(parents=True, exist_ok=True)
    prefix = symbol.lower()
    out_expr = out_dir / f"{prefix}_expression.csv"
    out_cancer = out_dir / f"{prefix}_by_cancer.csv"

    expr = extract_gene_expression(symbol, ensembl_id)
    stats, merged = by_cancer_stats(expr, symbol)
    merged.to_csv(out_expr, index=False)
    stats.to_csv(out_cancer, index=False)
    log.info("Wrote %s (%d rows)", out_cancer, len(stats))
    log.info("Wrote %s (%d rows)", out_expr, len(merged))
    return out_expr, out_cancer


def main() -> None:
    import sys

    sys.path.insert(0, str(_ROOT))
    from src.knowledge_graph.target_slice import get_target

    logging.basicConfig(level=logging.INFO)
    ap = argparse.ArgumentParser(description="Extract gene from TCGA/Xena")
    ap.add_argument("--symbol", required=True)
    args = ap.parse_args()
    t = get_target(args.symbol.upper())
    run_extract(t["symbol"], t["ensembl_id"])
    print(f"extract_ok {t['symbol']}")


if __name__ == "__main__":
    main()
