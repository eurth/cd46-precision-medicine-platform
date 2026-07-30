"""Per-gene PARAM slices: priority scores + eligibility patient groups (additive ETL)."""
from __future__ import annotations

import logging
from pathlib import Path

import numpy as np
import pandas as pd
import yaml
from sklearn.preprocessing import MinMaxScaler

log = logging.getLogger(__name__)

_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = _ROOT / "data" / "processed"
TARGETS_YAML = _ROOT / "config" / "targets.yaml"

with (_ROOT / "config" / "config.yaml").open(encoding="utf-8") as f:
    _CONFIG = yaml.safe_load(f) or {}

WEIGHTS = (_CONFIG.get("priority_score") or {})
HIGH_THRESHOLD = WEIGHTS.get("high_priority_threshold", 0.65)
MOD_THRESHOLD = WEIGHTS.get("moderate_threshold", 0.35)

PRIORITY_CANCERS = ["PRAD", "OV", "BLCA", "MESO", "LUAD", "KIRC", "BRCA"]
TISSUE_MAP = {
    "PRAD": "Prostate",
    "BRCA": "Breast",
    "LUAD": "Lung",
    "LUSC": "Lung",
    "OV": "Ovary",
    "COAD": "Colon",
    "BLCA": "Bladder",
    "PAAD": "Pancreas",
    "KIRC": "Kidney",
    "LIHC": "Liver",
}


def list_param_targets() -> list[str]:
    with TARGETS_YAML.open(encoding="utf-8") as f:
        reg = yaml.safe_load(f) or {}
    return [
        sym
        for sym, meta in (reg.get("targets") or {}).items()
        if (meta or {}).get("data_tier") in ("medium", "full")
    ]


def _median_col(df: pd.DataFrame, symbol: str) -> str | None:
    pref = symbol.lower()
    for c in (f"{pref}_median", "gene_median", "cd46_median", f"{pref}_mean", "gene_mean"):
        if c in df.columns:
            return c
    return None


def _expr_col(df: pd.DataFrame, symbol: str) -> str | None:
    pref = symbol.lower()
    for c in (f"{pref}_log2_tpm", "gene_log2_tpm", "cd46_log2_tpm"):
        if c in df.columns:
            return c
    return None


def _survival_os_map(survival_df: pd.DataFrame) -> pd.DataFrame:
    if survival_df.empty or "cancer_type" not in survival_df.columns:
        return pd.DataFrame()
    df = survival_df.copy()
    if "endpoint" in df.columns:
        df = df[df["endpoint"].fillna("OS").eq("OS")]
    df = df[df["hazard_ratio"].notna()]
    if df.empty:
        return pd.DataFrame()
    return df.drop_duplicates("cancer_type", keep="first").set_index("cancer_type")


def compute_gene_priority(
    symbol: str,
    *,
    cancer_df: pd.DataFrame | None = None,
    survival_df: pd.DataFrame | None = None,
    hpa_df: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """Composite priority score for one gene; writes {gene}_priority_score.csv."""
    pref = symbol.lower()
    by_cancer_path = DATA_DIR / f"{pref}_by_cancer.csv"
    if cancer_df is None:
        if not by_cancer_path.exists():
            raise FileNotFoundError(by_cancer_path)
        cancer_df = pd.read_csv(by_cancer_path)

    if survival_df is None:
        surv_path = DATA_DIR / f"{pref}_survival_results.csv"
        survival_df = pd.read_csv(surv_path) if surv_path.exists() else pd.DataFrame()

    if hpa_df is None:
        for name in (f"hpa_{pref}_protein.csv", f"hpa_{pref}_protein_intensity.csv"):
            p = DATA_DIR / name
            if p.exists():
                hpa_df = pd.read_csv(p)
                break
        else:
            hpa_df = pd.DataFrame()

    df = cancer_df.copy()
    med_col = _median_col(df, symbol)
    scaler = MinMaxScaler()

    if "expression_rank" in df.columns and df["expression_rank"].notna().any():
        max_rank = df["expression_rank"].max()
        df["expr_rank_score"] = 1.0 - (df["expression_rank"] - 1) / max(max_rank - 1, 1)
    elif med_col:
        df["expr_rank_score"] = scaler.fit_transform(df[[med_col]].fillna(0)).flatten()
    else:
        df["expr_rank_score"] = 0.5

    surv_map = _survival_os_map(survival_df)
    if not surv_map.empty:
        df["hr"] = df["cancer_type"].map(surv_map["hazard_ratio"])
        df["surv_pval"] = df["cancer_type"].map(surv_map.get("p_value", pd.Series(dtype=float)))
        df["survival_impact"] = np.where(
            df["surv_pval"].fillna(1.0) < 0.05,
            (df["hr"].fillna(1.0) - 1.0).clip(0, 2.0) / 2.0,
            0.0,
        )
    else:
        df["hr"] = 1.0
        df["surv_pval"] = 1.0
        df["survival_impact"] = 0.3

    df["cna_score"] = 0.15

    tumor_hpa = pd.DataFrame()
    if not hpa_df.empty and "type" in hpa_df.columns:
        tumor_hpa = hpa_df[hpa_df["type"] == "tumor"]
    score_col = next(
        (c for c in ("intensity_score", "h_score_approx") if c in hpa_df.columns),
        None,
    )
    if not tumor_hpa.empty and score_col:
        hpa_lookup = tumor_hpa.set_index("tissue")[score_col].to_dict()
        df["tissue"] = df["cancer_type"].map(TISSUE_MAP)
        max_val = max(hpa_lookup.values()) if hpa_lookup else 3.0
        df["protein_score"] = df["tissue"].map(hpa_lookup).fillna(max_val * 0.5) / max(max_val, 1.0)
    elif score_col and "tissue" in hpa_df.columns:
        # ponytail: intensity-only HPA — rank-normalize across tissues
        vals = hpa_df.groupby("tissue")[score_col].max()
        df["tissue"] = df["cancer_type"].map(TISSUE_MAP)
        vmax = vals.max() or 1.0
        df["protein_score"] = df["tissue"].map((vals / vmax).to_dict()).fillna(0.5)
    else:
        df["protein_score"] = 0.5

    w_expr = WEIGHTS.get("expression_rank_weight", 0.35)
    w_surv = WEIGHTS.get("survival_impact_weight", 0.35)
    w_cna = WEIGHTS.get("cna_amplification_weight", 0.15)
    w_prot = WEIGHTS.get("protein_expression_weight", 0.15)

    df["priority_score"] = (
        w_expr * df["expr_rank_score"]
        + w_surv * df["survival_impact"]
        + w_cna * df["cna_score"]
        + w_prot * df["protein_score"]
    ).clip(0, 1)

    df["priority_label"] = pd.cut(
        df["priority_score"],
        bins=[-0.001, MOD_THRESHOLD, HIGH_THRESHOLD, 1.001],
        labels=["EXPLORATORY", "MODERATE", "HIGH PRIORITY"],
    )
    df = df.sort_values("priority_score", ascending=False).reset_index(drop=True)
    df["priority_rank"] = df.index + 1

    if med_col and med_col != "gene_median":
        df["gene_median"] = df[med_col]
    elif med_col:
        df["gene_median"] = df[med_col]
    else:
        df["gene_median"] = np.nan

    out = DATA_DIR / (
        "priority_score.csv" if symbol.upper() == "CD46" else f"{pref}_priority_score.csv"
    )
    out.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out, index=False)
    log.info("Wrote %s (%d cancers)", out.name, len(df))
    return df


def compute_gene_patient_groups(
    symbol: str,
    expr_df: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """Eligibility thresholds per cancer; writes {gene}_patient_groups.csv."""
    pref = symbol.lower()
    expr_path = DATA_DIR / f"{pref}_expression.csv"
    if expr_df is None:
        if not expr_path.exists():
            raise FileNotFoundError(expr_path)
        expr_df = pd.read_csv(expr_path)

    expr_col = _expr_col(expr_df, symbol)
    if not expr_col:
        raise ValueError(f"No expression column in {expr_path}")

    high_label = f"{symbol.upper()}-High"
    low_label = f"{symbol.upper()}-Low"
    records: list[dict] = []

    for cancer, group in expr_df.groupby("cancer_type"):
        expr = group[expr_col].dropna()
        if len(expr) < 10:
            continue
        median_val = float(expr.median())
        pct75_val = float(expr.quantile(0.75))
        for method, threshold in (
            ("median", median_val),
            ("75th_pct", pct75_val),
            ("log2tpm_2.5", 2.5),
            ("log2tpm_3.0", 3.0),
        ):
            n_high = int((expr >= threshold).sum())
            n_total = int(len(expr))
            pct_eligible = round(100 * n_high / n_total, 1) if n_total else 0.0
            for group_label, n_elig, pct in (
                (high_label, n_high, pct_eligible),
                (low_label, n_total - n_high, round(100 - pct_eligible, 1)),
            ):
                records.append(
                    {
                        "cancer_type": cancer,
                        "threshold_method": method,
                        "threshold_value": threshold,
                        "n_eligible": n_elig,
                        "n_total": n_total,
                        "pct_eligible": pct,
                        "expression_group": group_label,
                        "dataset": "TCGA",
                        "is_priority_cancer": cancer in PRIORITY_CANCERS,
                        "gene_symbol": symbol.upper(),
                    }
                )

    result = pd.DataFrame(records)
    out = DATA_DIR / (
        "patient_groups.csv" if symbol.upper() == "CD46" else f"{pref}_patient_groups.csv"
    )
    out.parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(out, index=False)
    log.info("Wrote %s (%d rows)", out.name, len(result))
    return result


def build_hpa_protein_from_intensity(symbol: str) -> pd.DataFrame | None:
    """Approximate hpa_{gene}_protein.csv from intensity slice (dosimetry-friendly)."""
    pref = symbol.lower()
    src = DATA_DIR / f"hpa_{pref}_protein_intensity.csv"
    dst = DATA_DIR / f"hpa_{pref}_protein.csv"
    if not src.exists() or dst.exists():
        return pd.read_csv(dst) if dst.exists() else None

    raw = pd.read_csv(src)
    if "intensity_score" not in raw.columns or "tissue" not in raw.columns:
        return None

    scores = raw["intensity_score"].astype(float)
    lo, hi = scores.min(), scores.max()
    span = hi - lo if hi > lo else 1.0
    raw["h_score_approx"] = ((scores - lo) / span * 250 + 50).round(0).astype(int)
    raw["staining_intensity"] = pd.cut(
        raw["h_score_approx"],
        bins=[-1, 150, 250, 400],
        labels=["Weak", "Moderate", "Strong"],
    ).astype(str)
    raw["fraction_positive"] = (raw["h_score_approx"] / 300).clip(0.25, 1.0).round(2)
    raw["intensity_score"] = (raw["h_score_approx"] / 100).round(1)
    raw["data_source"] = "HPA_intensity_proxy"
    if "type" not in raw.columns:
        raw["type"] = "normal"
    raw.to_csv(dst, index=False)
    log.info("Wrote proxy %s from intensity", dst.name)
    return raw


def build_gene_slices(symbol: str) -> dict[str, int]:
    """Build all PARAM slices for one symbol."""
    sym = symbol.upper()
    stats: dict[str, int] = {}
    stats["priority_rows"] = len(compute_gene_priority(sym))
    stats["patient_group_rows"] = len(compute_gene_patient_groups(sym))
    hpa = build_hpa_protein_from_intensity(sym)
    stats["hpa_protein_rows"] = len(hpa) if hpa is not None else 0
    return stats
