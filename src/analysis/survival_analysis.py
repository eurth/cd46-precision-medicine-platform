"""
Kaplan-Meier + Cox Proportional Hazards survival analysis for CD46.
Stratifies patients into CD46-High vs CD46-Low groups using median split.
Outputs: cd46_survival_results.csv + KM figures.
"""

import logging
from pathlib import Path

import numpy as np
import pandas as pd
from lifelines import KaplanMeierFitter, CoxPHFitter
from lifelines.statistics import logrank_test
from lifelines.utils import concordance_index
import yaml

log = logging.getLogger(__name__)

_CFG_PATH = Path(__file__).parents[2] / "config"
with open(_CFG_PATH / "config.yaml") as f:
    import yaml as _y; _CONFIG = _y.safe_load(f)

SURV_CFG = _CONFIG["survival"]
DATA_DIR = Path("data/processed")
FIGURES_DIR = Path("reports/figures")
OUT_RESULTS = DATA_DIR / "cd46_survival_results.csv"

OS_TIME = SURV_CFG["km_time_col"]
OS_EVENT = SURV_CFG["km_event_col"]
PFI_TIME = SURV_CFG["pfi_time_col"]
PFI_EVENT = SURV_CFG["pfi_event_col"]
MIN_SAMPLES = SURV_CFG["min_samples_per_group"]
SIG_THRESHOLD = SURV_CFG["significance_threshold"]


def stratify_patients(df: pd.DataFrame, expr_col: str = "cd46_log2_tpm") -> pd.DataFrame:
    """Add CD46-High/Low group column using median split."""
    median = df[expr_col].median()
    df = df.copy()
    df["cd46_group"] = np.where(df[expr_col] >= median, "CD46-High", "CD46-Low")
    df["cd46_threshold"] = median
    return df


def run_km_analysis(df: pd.DataFrame, cancer_type: str,
                    time_col: str, event_col: str,
                    group_col: str = "cd46_group") -> dict:
    """Run KM analysis + log-rank test for one cancer type."""
    sub = df[[time_col, event_col, group_col]].dropna()
    if len(sub) < MIN_SAMPLES * 2:
        return {}

    high = sub[sub[group_col] == "CD46-High"]
    low = sub[sub[group_col] == "CD46-Low"]

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


def run_cox_analysis(df: pd.DataFrame, cancer_type: str,
                     time_col: str, event_col: str) -> dict:
    """Run univariable Cox PH regression for CD46 expression."""
    sub = df[[time_col, event_col, "cd46_log2_tpm"]].dropna()
    if len(sub) < MIN_SAMPLES * 2:
        return {}

    cph = CoxPHFitter()
    try:
        cph.fit(sub, duration_col=time_col, event_col=event_col)
        summary = cph.summary
        cd46_row = summary.loc["cd46_log2_tpm"] if "cd46_log2_tpm" in summary.index else None
        if cd46_row is None:
            return {}
        return {
            "cancer_type": cancer_type,
            "endpoint": time_col.replace(".time", ""),
            "hazard_ratio": float(np.exp(cd46_row["coef"])),
            "hr_lower_95": float(np.exp(cd46_row["coef lower 95%"])),
            "hr_upper_95": float(np.exp(cd46_row["coef upper 95%"])),
            "p_value": float(cd46_row["p"]),
            "significant": cd46_row["p"] < SIG_THRESHOLD,
            "n_samples": len(sub),
        }
    except Exception as e:
        log.debug("Cox failed for %s: %s", cancer_type, e)
        return {}


def run_all_cancers(expr_df: pd.DataFrame) -> pd.DataFrame:
    """Run survival analysis for all TCGA cancer types."""
    if OS_TIME not in expr_df.columns:
        log.warning("Survival columns not found in expression data. Check merge.")
        return pd.DataFrame()

    expr_df = stratify_patients(expr_df)
    cancer_col = next((c for c in ["cancer type abbreviation", "cancer_type", "_cohort"]
                       if c in expr_df.columns), None)
    if cancer_col is None:
        log.error("No cancer type column found")
        return pd.DataFrame()

    results = []
    for cancer_type, group in expr_df.groupby(cancer_col):
        # OS KM
        km_os = run_km_analysis(group, cancer_type, OS_TIME, OS_EVENT)
        if km_os:
            results.append(km_os)

        # OS Cox
        cox_os = run_cox_analysis(group, cancer_type, OS_TIME, OS_EVENT)
        if cox_os:
            results.append(cox_os)

        # PFI KM (if available)
        if PFI_TIME in group.columns:
            km_pfi = run_km_analysis(group, cancer_type, PFI_TIME, PFI_EVENT)
            if km_pfi:
                results.append(km_pfi)

    if not results:
        log.warning("No survival results computed")
        return pd.DataFrame()

    result_df = pd.DataFrame(results)
    OUT_RESULTS.parent.mkdir(parents=True, exist_ok=True)
    result_df.to_csv(OUT_RESULTS, index=False)
    log.info("Survival analysis: %d results across %d cancer types → %s",
             len(result_df), result_df["cancer_type"].nunique(), OUT_RESULTS)
    return result_df


def get_km_data(expr_df: pd.DataFrame, cancer_type: str,
                time_col: str = OS_TIME, event_col: str = OS_EVENT) -> dict:
    """Return KM curve data dict for Plotly rendering."""
    sub = stratify_patients(expr_df[expr_df.get("cancer_type", expr_df.columns[0]) == cancer_type])
    kmf_high = KaplanMeierFitter()
    kmf_low = KaplanMeierFitter()
    high = sub[sub["cd46_group"] == "CD46-High"]
    low = sub[sub["cd46_group"] == "CD46-Low"]

    kmf_high.fit(high[time_col], high[event_col], label="CD46-High")
    kmf_low.fit(low[time_col], low[event_col], label="CD46-Low")

    return {"high": kmf_high, "low": kmf_low}


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    expr_path = DATA_DIR / "cd46_expression.csv"
    if not expr_path.exists():
        print("cd46_expression.csv not found. Run extract_cd46.py first.")
    else:
        expr_df = pd.read_csv(expr_path)
        results = run_all_cancers(expr_df)
        if not results.empty:
            sig = results[results.get("significant", False)]
            print(f"\nSignificant survival associations: {len(sig)}")
            print(results.head(10).to_string(index=False))
