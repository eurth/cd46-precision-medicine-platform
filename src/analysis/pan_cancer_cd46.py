"""
Pan-cancer CD46 expression analysis.
Computes:
  - Per-cancer mean/median/std/rank
  - Kruskal-Wallis significance test
  - Composite clinical priority score for 225Ac-CD46 therapy selection

Priority score formula:
  0.35 × expression_rank_normalized
  + 0.35 × survival_impact_score
  + 0.15 × cna_amplification_freq (from DepMap / GENIE)
  + 0.15 × protein_expression_score (from HPA)
"""

import logging
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats
from sklearn.preprocessing import MinMaxScaler
import yaml

log = logging.getLogger(__name__)

_CFG_PATH = Path(__file__).parents[2] / "config"
with open(_CFG_PATH / "config.yaml") as f:
    import yaml as _y; _CONFIG = _y.safe_load(f)

WEIGHTS = _CONFIG["priority_score"]
HIGH_THRESHOLD = WEIGHTS["high_priority_threshold"]
MOD_THRESHOLD = WEIGHTS["moderate_threshold"]

DATA_DIR = Path("data/processed")
OUT_PRIORITY = DATA_DIR / "priority_score.csv"
OUT_BY_CANCER = DATA_DIR / "cd46_by_cancer.csv"

# HPA protein level → numeric score
HPA_SCORE_MAP = {"Not detected": 0.0, "Low": 0.33, "Medium": 0.66, "High": 1.0}


def load_data() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Load cd46_by_cancer, survival_results, and HPA protein data."""
    cancer_df = pd.read_csv(DATA_DIR / "cd46_by_cancer.csv")
    
    surv_path = DATA_DIR / "cd46_survival_results.csv"
    survival_df = pd.read_csv(surv_path) if surv_path.exists() else pd.DataFrame()

    hpa_path = DATA_DIR / "hpa_cd46_protein.csv"
    hpa_df = pd.read_csv(hpa_path) if hpa_path.exists() else pd.DataFrame()

    return cancer_df, survival_df, hpa_df


def kruskal_wallis_across_cancers(expr_df: pd.DataFrame,
                                   cancer_col: str = "cancer_type",
                                   expr_col: str = "cd46_log2_tpm") -> dict:
    """Kruskal-Wallis test: is CD46 expression significantly different across cancer types?"""
    groups = [grp[expr_col].dropna().values for _, grp in expr_df.groupby(cancer_col)]
    groups = [g for g in groups if len(g) >= 5]
    if len(groups) < 2:
        return {"statistic": None, "p_value": None}
    stat, pval = stats.kruskal(*groups)
    return {"statistic": float(stat), "p_value": float(pval)}


def compute_priority_score(cancer_df: pd.DataFrame,
                            survival_df: pd.DataFrame,
                            hpa_df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute composite clinical priority score for each cancer type.
    Output: cancer_type, priority_score, priority_label + all component scores.
    """
    df = cancer_df.copy()
    scaler = MinMaxScaler()

    # Component 1: expression rank (higher rank = lower number = more expressed)
    if "expression_rank" in df.columns:
        # Invert rank so rank=1 (highest expression) → score=1.0
        max_rank = df["expression_rank"].max()
        df["expr_rank_score"] = 1.0 - (df["expression_rank"] - 1) / (max_rank - 1)
    elif "cd46_median" in df.columns:
        vals = df[["cd46_median"]].fillna(0)
        df["expr_rank_score"] = scaler.fit_transform(vals).flatten()
    else:
        df["expr_rank_score"] = 0.5

    # Component 2: survival impact (HR > 1 + low p-value = high score)
    if not survival_df.empty and "cancer_type" in survival_df.columns:
        surv_map = survival_df.set_index("cancer_type")
        df["hr"] = df["cancer_type"].map(surv_map.get("hazard_ratio", pd.Series(dtype=float)))
        df["surv_pval"] = df["cancer_type"].map(surv_map.get("p_value", pd.Series(dtype=float)))
        df["survival_impact"] = np.where(
            df["surv_pval"].fillna(1.0) < 0.05,
            (df["hr"].fillna(1.0) - 1.0).clip(0, 2.0) / 2.0,
            0.0
        )
    else:
        df["hr"] = 1.0
        df["surv_pval"] = 1.0
        df["survival_impact"] = 0.3  # moderate default

    # Component 3: CNA amplification freq (from DepMap or placeholder)
    if "cd46_cna_amplification_freq" in df.columns:
        df["cna_score"] = df["cd46_cna_amplification_freq"].fillna(0).clip(0, 1)
    else:
        df["cna_score"] = 0.15  # placeholder

    # Component 4: HPA protein score
    if not hpa_df.empty:
        tumor_hpa = hpa_df[hpa_df["type"] == "tumor"][["tissue", "intensity_score"]].copy()
        # Map TCGA cancer types to HPA tissues — approximate
        tissue_map = {
            "PRAD": "Prostate", "BRCA": "Breast", "LUAD": "Lung", "LUSC": "Lung",
            "OV": "Ovary", "COAD": "Colon", "BLCA": "Bladder", "PAAD": "Pancreas",
            "KIRC": "Kidney", "LIHC": "Liver",
        }
        df["tissue"] = df["cancer_type"].map(tissue_map)
        hpa_lookup = tumor_hpa.set_index("tissue")["intensity_score"].to_dict()
        df["protein_score"] = df["tissue"].map(hpa_lookup).fillna(1.5) / 3.0  # normalize to 0-1
    else:
        df["protein_score"] = 0.5  # placeholder

    # Compute final priority score
    df["priority_score"] = (
        WEIGHTS["expression_rank_weight"] * df["expr_rank_score"]
        + WEIGHTS["survival_impact_weight"] * df["survival_impact"]
        + WEIGHTS["cna_amplification_weight"] * df["cna_score"]
        + WEIGHTS["protein_expression_weight"] * df["protein_score"]
    ).clip(0, 1)

    # Assign labels
    df["priority_label"] = pd.cut(
        df["priority_score"],
        bins=[-0.001, MOD_THRESHOLD, HIGH_THRESHOLD, 1.001],
        labels=["EXPLORATORY", "MODERATE", "HIGH PRIORITY"],
    )

    df = df.sort_values("priority_score", ascending=False).reset_index(drop=True)
    df["priority_rank"] = df.index + 1

    OUT_PRIORITY.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT_PRIORITY, index=False)
    log.info("Priority scores computed for %d cancer types → %s", len(df), OUT_PRIORITY)

    return df


def run_pan_cancer_analysis(expr_df: pd.DataFrame | None = None) -> pd.DataFrame:
    """Main entry point: load data, run KW test, compute priority scores."""
    cancer_df, survival_df, hpa_df = load_data()

    if expr_df is not None:
        # Run KW test on full per-sample data
        kw = kruskal_wallis_across_cancers(expr_df)
        log.info("Kruskal-Wallis test: stat=%.2f, p=%.2e", kw["statistic"] or 0, kw["p_value"] or 1)

    priority_df = compute_priority_score(cancer_df, survival_df, hpa_df)

    n_high = (priority_df["priority_label"] == "HIGH PRIORITY").sum()
    n_mod = (priority_df["priority_label"] == "MODERATE").sum()
    log.info("Priority: %d HIGH PRIORITY, %d MODERATE, %d EXPLORATORY",
             n_high, n_mod, len(priority_df) - n_high - n_mod)

    return priority_df


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    df = run_pan_cancer_analysis()
    print("\nTop 10 priority cancers for 225Ac-CD46 therapy:")
    cols = ["cancer_type", "priority_score", "priority_label", "expr_rank_score", "survival_impact"]
    avail = [c for c in cols if c in df.columns]
    print(df[avail].head(10).to_string(index=False))
