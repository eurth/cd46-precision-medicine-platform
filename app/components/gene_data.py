"""Gene-parameterized processed CSV paths (P2 PARAM — additive, CD46 fallbacks kept)."""
from __future__ import annotations

from pathlib import Path

import pandas as pd

PROC = Path("data/processed")


def priority_path(symbol: str) -> Path:
    sym = symbol.upper()
    if sym == "CD46":
        return PROC / "priority_score.csv"
    return PROC / f"{symbol.lower()}_priority_score.csv"


def patient_groups_path(symbol: str) -> Path:
    sym = symbol.upper()
    if sym == "CD46":
        return PROC / "patient_groups.csv"
    return PROC / f"{symbol.lower()}_patient_groups.csv"


def load_priority_df(symbol: str) -> pd.DataFrame:
    p = priority_path(symbol)
    return pd.read_csv(p) if p.exists() else pd.DataFrame()


def load_patient_groups_df(symbol: str) -> pd.DataFrame:
    p = patient_groups_path(symbol)
    return pd.read_csv(p) if p.exists() else pd.DataFrame()


def prad_75th_eligibility(symbol: str) -> tuple[float | None, int | None]:
    """Return (pct_eligible, n_eligible) for PRAD 75th-pct high group."""
    df = load_patient_groups_df(symbol)
    if df.empty:
        return None, None
    sym = symbol.upper()
    high_labels = {f"{sym}-High", "CD46-High"} if sym == "CD46" else {f"{sym}-High"}
    sub = df[
        (df["cancer_type"] == "PRAD")
        & (df["threshold_method"].astype(str).str.contains("75th", case=False, na=False))
        & (df["expression_group"].isin(high_labels))
    ]
    if sub.empty:
        return None, None
    row = sub.iloc[0]
    return float(row.get("pct_eligible", 0)), int(row.get("n_eligible", 0))
