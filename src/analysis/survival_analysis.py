"""
Kaplan-Meier + Cox Proportional Hazards survival analysis.
Stratifies patients into {GENE}-High vs {GENE}-Low using median split.
Outputs: {gene}_survival_results.csv
"""

from __future__ import annotations

import argparse
import logging
from pathlib import Path

import numpy as np
import pandas as pd
from lifelines import KaplanMeierFitter, CoxPHFitter
from lifelines.statistics import logrank_test
import yaml

log = logging.getLogger(__name__)

_CFG_PATH = Path(__file__).parents[2] / "config"
with open(_CFG_PATH / "config.yaml") as f:
    _CONFIG = yaml.safe_load(f)

SURV_CFG = _CONFIG["survival"]
DATA_DIR = Path("data/processed")
FIGURES_DIR = Path("reports/figures")

OS_TIME = SURV_CFG["km_time_col"]
OS_EVENT = SURV_CFG["km_event_col"]
PFI_TIME = SURV_CFG["pfi_time_col"]
PFI_EVENT = SURV_CFG["pfi_event_col"]
MIN_SAMPLES = SURV_CFG["min_samples_per_group"]
SIG_THRESHOLD = SURV_CFG["significance_threshold"]


def _cols(gene: str) -> tuple[str, str, str, str]:
    g = gene.upper()
    low = gene.lower()
    return (
        f"{low}_log2_tpm",
        f"{low}_group",
        f"{g}-High",
        f"{g}-Low",
    )


def stratify_patients(
    df: pd.DataFrame,
    expr_col: str = "cd46_log2_tpm",
    *,
    gene: str = "CD46",
) -> pd.DataFrame:
    """Add High/Low group column using median split."""
    expr_col, group_col, high_lbl, low_lbl = _cols(gene)
    if expr_col not in df.columns:
        raise KeyError(f"Missing expression column: {expr_col}")
    median = df[expr_col].median()
    df = df.copy()
    df[group_col] = np.where(df[expr_col] >= median, high_lbl, low_lbl)
    df[f"{gene.lower()}_threshold"] = median
    return df


def run_km_analysis(
    df: pd.DataFrame,
    cancer_type: str,
    time_col: str,
    event_col: str,
    *,
    gene: str = "CD46",
) -> dict:
    """Run KM analysis + log-rank test for one cancer type."""
    _, group_col, high_lbl, low_lbl = _cols(gene)
    sub = df[[time_col, event_col, group_col]].dropna()
    if len(sub) < MIN_SAMPLES * 2:
        return {}

    high = sub[sub[group_col] == high_lbl]
    low = sub[sub[group_col] == low_lbl]

    if len(high) < MIN_SAMPLES or len(low) < MIN_SAMPLES:
        return {}

    result = logrank_test(
        high[time_col], low[time_col],
        event_observed_A=high[event_col],
        event_observed_B=low[event_col],
    )

    return {
        "cancer_type": cancer_type,
        "endpoint": time_col.replace(".time", ""),
        "n_high": len(high),
        "n_low": len(low),
        "log_rank_p": float(result.p_value),
        "log_rank_stat": float(result.test_statistic),
        "significant": result.p_value < SIG_THRESHOLD,
    }


def run_cox_analysis(
    df: pd.DataFrame,
    cancer_type: str,
    time_col: str,
    event_col: str,
    *,
    gene: str = "CD46",
) -> dict:
    """Run univariable Cox PH regression for gene expression."""
    expr_col, _, _, _ = _cols(gene)
    sub = df[[time_col, event_col, expr_col]].dropna()
    if len(sub) < MIN_SAMPLES * 2:
        return {}

    cph = CoxPHFitter()
    try:
        cph.fit(sub, duration_col=time_col, event_col=event_col)
        summary = cph.summary
        if expr_col not in summary.index:
            return {}
        row = summary.loc[expr_col]
        return {
            "cancer_type": cancer_type,
            "endpoint": time_col.replace(".time", ""),
            "hazard_ratio": float(np.exp(row["coef"])),
            "hr_lower_95": float(np.exp(row["coef lower 95%"])),
            "hr_upper_95": float(np.exp(row["coef upper 95%"])),
            "p_value": float(row["p"]),
            "significant": row["p"] < SIG_THRESHOLD,
            "n_samples": len(sub),
        }
    except Exception as e:
        log.debug("Cox failed for %s: %s", cancer_type, e)
        return {}


def run_all_cancers(expr_df: pd.DataFrame, gene: str = "CD46") -> pd.DataFrame:
    """Run survival analysis for all TCGA cancer types."""
    gene = gene.upper()
    out_path = DATA_DIR / f"{gene.lower()}_survival_results.csv"

    if OS_TIME not in expr_df.columns:
        log.warning("Survival columns not found in expression data. Check merge.")
        return pd.DataFrame()

    expr_df = stratify_patients(expr_df, gene=gene)
    cancer_col = next(
        (c for c in ["cancer type abbreviation", "cancer_type", "_cohort"]
         if c in expr_df.columns),
        None,
    )
    if cancer_col is None:
        log.error("No cancer type column found")
        return pd.DataFrame()

    results = []
    for cancer_type, group in expr_df.groupby(cancer_col):
        km_os = run_km_analysis(group, cancer_type, OS_TIME, OS_EVENT, gene=gene)
        if km_os:
            results.append(km_os)

        cox_os = run_cox_analysis(group, cancer_type, OS_TIME, OS_EVENT, gene=gene)
        if cox_os:
            results.append(cox_os)

        if PFI_TIME in group.columns:
            km_pfi = run_km_analysis(group, cancer_type, PFI_TIME, PFI_EVENT, gene=gene)
            if km_pfi:
                results.append(km_pfi)

    if not results:
        log.warning("No survival results computed")
        return pd.DataFrame()

    result_df = pd.DataFrame(results)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    result_df.to_csv(out_path, index=False)
    log.info(
        "Survival analysis (%s): %d results across %d cancer types → %s",
        gene,
        len(result_df),
        result_df["cancer_type"].nunique(),
        out_path,
    )
    return result_df


def get_km_data(
    expr_df: pd.DataFrame,
    cancer_type: str,
    time_col: str = OS_TIME,
    event_col: str = OS_EVENT,
    *,
    gene: str = "CD46",
) -> dict:
    """Return KM curve data dict for Plotly rendering."""
    _, group_col, high_lbl, low_lbl = _cols(gene)
    cancer_col = next(
        (c for c in ["cancer_type", "cancer type abbreviation", "_cohort"]
         if c in expr_df.columns),
        None,
    )
    sub = expr_df[expr_df[cancer_col] == cancer_type] if cancer_col else expr_df
    sub = stratify_patients(sub, gene=gene)
    kmf_high = KaplanMeierFitter()
    kmf_low = KaplanMeierFitter()
    high = sub[sub[group_col] == high_lbl]
    low = sub[sub[group_col] == low_lbl]

    kmf_high.fit(high[time_col], high[event_col], label=high_lbl)
    kmf_low.fit(low[time_col], low[event_col], label=low_lbl)

    return {"high": kmf_high, "low": kmf_low}


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    ap = argparse.ArgumentParser(description="Gene survival analysis (TCGA)")
    ap.add_argument("--gene", default="CD46", help="HGNC symbol, e.g. FOLH1")
    args = ap.parse_args()
    gene = args.gene.upper()
    expr_path = DATA_DIR / f"{gene.lower()}_expression.csv"
    if not expr_path.exists():
        print(f"{expr_path} not found. Run extract for {gene} first.")
    else:
        expr_df = pd.read_csv(expr_path)
        results = run_all_cancers(expr_df, gene=gene)
        if not results.empty:
            sig = results[results["significant"] == True]  # noqa: E712
            print(f"\nSignificant survival associations ({gene}): {len(sig)}")
            print(results.head(10).to_string(index=False))
