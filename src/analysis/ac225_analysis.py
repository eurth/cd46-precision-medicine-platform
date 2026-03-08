"""
225Ac-CD46 therapy eligibility analysis.
Computes patient eligibility at three CD46 expression thresholds.
Outputs: patient_groups.csv with eligibility stats per cancer type.
"""

import logging
from pathlib import Path

import numpy as np
import pandas as pd

log = logging.getLogger(__name__)

DATA_DIR = Path("data/processed")
OUT_GROUPS = DATA_DIR / "patient_groups.csv"

# Threshold levels for 225Ac eligibility
THRESHOLDS = {
    "median": None,           # computed per cancer type
    "75th_pct": None,         # computed per cancer type
    "log2tpm_2.5": 2.5,       # absolute threshold (frequently cited in CD46 literature)
    "log2tpm_3.0": 3.0,
}

# Key cancers for 225Ac focus
PRIORITY_CANCERS = ["PRAD", "OV", "BLCA", "MESO", "LUAD", "KIRC", "BRCA"]


def compute_eligibility(df: pd.DataFrame,
                        cancer_type_col: str = "cancer_type",
                        expr_col: str = "cd46_log2_tpm") -> pd.DataFrame:
    """
    For each cancer type, compute CD46-high patient count at each threshold.
    Returns patient_groups DataFrame ready for KG ingestion.
    """
    records = []
    
    for cancer, group in df.groupby(cancer_type_col):
        expr = group[expr_col].dropna()
        if len(expr) < 10:
            continue
        
        median_val = expr.median()
        pct75_val = expr.quantile(0.75)

        for method, threshold in [
            ("median", median_val),
            ("75th_pct", pct75_val),
            ("log2tpm_2.5", 2.5),
            ("log2tpm_3.0", 3.0),
        ]:
            n_high = (expr >= threshold).sum()
            n_total = len(expr)
            pct_eligible = 100 * n_high / n_total if n_total > 0 else 0

            records.append({
                "cancer_type": cancer,
                "threshold_method": method,
                "threshold_value": threshold,
                "n_eligible": int(n_high),
                "n_total": int(n_total),
                "pct_eligible": round(pct_eligible, 1),
                "expression_group": "CD46-High",
                "dataset": "TCGA",
                "is_priority_cancer": cancer in PRIORITY_CANCERS,
            })

            # Also add the CD46-Low group
            n_low = n_total - n_high
            records.append({
                "cancer_type": cancer,
                "threshold_method": method,
                "threshold_value": threshold,
                "n_eligible": int(n_low),
                "n_total": int(n_total),
                "pct_eligible": round(100 - pct_eligible, 1),
                "expression_group": "CD46-Low",
                "dataset": "TCGA",
                "is_priority_cancer": cancer in PRIORITY_CANCERS,
            })

    result = pd.DataFrame(records)
    OUT_GROUPS.parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(OUT_GROUPS, index=False)
    log.info("Patient groups: %d records → %s", len(result), OUT_GROUPS)
    return result


def get_prad_eligibility_summary(groups_df: pd.DataFrame) -> dict:
    """Return a concise PRAD eligibility summary for the Streamlit hero stat."""
    prad = groups_df[
        (groups_df["cancer_type"] == "PRAD") &
        (groups_df["expression_group"] == "CD46-High")
    ]
    if prad.empty:
        return {}

    median_row = prad[prad["threshold_method"] == "median"]
    pct75_row = prad[prad["threshold_method"] == "75th_pct"]
    abs_row = prad[prad["threshold_method"] == "log2tpm_2.5"]

    return {
        "cancer_type": "PRAD",
        "n_total_prad": int(prad["n_total"].iloc[0]) if not prad.empty else 0,
        "n_median_eligible": int(median_row["n_eligible"].iloc[0]) if not median_row.empty else 0,
        "pct_median_eligible": float(median_row["pct_eligible"].iloc[0]) if not median_row.empty else 0,
        "n_75pct_eligible": int(pct75_row["n_eligible"].iloc[0]) if not pct75_row.empty else 0,
        "pct_75pct_eligible": float(pct75_row["pct_eligible"].iloc[0]) if not pct75_row.empty else 0,
        "n_abs_eligible": int(abs_row["n_eligible"].iloc[0]) if not abs_row.empty else 0,
        "pct_abs_eligible": float(abs_row["pct_eligible"].iloc[0]) if not abs_row.empty else 0,
    }


def run_ac225_analysis() -> pd.DataFrame:
    """Main entry: load expression data and compute all eligibility groups."""
    expr_path = DATA_DIR / "cd46_expression.csv"
    if not expr_path.exists():
        raise FileNotFoundError(f"Run extract_cd46.py first. Missing: {expr_path}")

    df = pd.read_csv(expr_path)
    cancer_col = next((c for c in ["cancer type abbreviation", "cancer_type"]
                       if c in df.columns), None)
    if cancer_col is None:
        log.warning("Could not identify cancer type column. Using first string column.")
        cancer_col = df.select_dtypes("object").columns[0]

    df = df.rename(columns={cancer_col: "cancer_type"}) if cancer_col != "cancer_type" else df
    return compute_eligibility(df)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    groups = run_ac225_analysis()
    summary = get_prad_eligibility_summary(groups)
    print("\n225Ac-CD46 PRAD Eligibility Summary:")
    for k, v in summary.items():
        print(f"  {k}: {v}")
