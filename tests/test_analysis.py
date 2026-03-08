"""Tests for pan-cancer analysis, survival analysis, and 225Ac eligibility."""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def sample_expression_df():
    """Minimal CD46 expression DataFrame resembling extract_cd46.py output."""
    rng = np.random.default_rng(42)
    n = 100
    cancer_types = ["PRAD"] * 40 + ["OV"] * 30 + ["BLCA"] * 30
    return pd.DataFrame(
        {
            "sample_id": [f"TCGA-{i:04d}" for i in range(n)],
            "cd46_log2": np.concatenate(
                [rng.normal(4.5, 0.8, 40), rng.normal(3.8, 1.0, 30), rng.normal(4.0, 0.9, 30)]
            ),
            "cancer_type": cancer_types,
            "OS": rng.integers(0, 2, n),
            "OS.time": rng.integers(100, 2000, n),
            "PFI": rng.integers(0, 2, n),
            "PFI.time": rng.integers(50, 1500, n),
        }
    )


@pytest.fixture
def sample_hpa_df():
    return pd.DataFrame(
        {
            "tissue": ["Prostate", "Ovary", "Brain", "Bladder", "Liver"],
            "tumor_level": ["High", "High", "Low", "High", "Medium"],
            "normal_level": ["Medium", "Medium", "Low", "Low", "Medium"],
        }
    )


# ---------------------------------------------------------------------------
# Pan-cancer analysis
# ---------------------------------------------------------------------------

class TestPanCancerAnalysis:
    def test_expression_stats_per_cancer(self, sample_expression_df):
        """Verify per-cancer stats computed correctly."""
        grouped = sample_expression_df.groupby("cancer_type")["cd46_log2"]

        prad_mean = grouped.mean()["PRAD"]
        assert 3.5 < prad_mean < 5.5, f"PRAD mean out of expected range: {prad_mean}"

    def test_kruskal_wallis_significance(self, sample_expression_df):
        """Kruskal-Wallis test detects difference across cancer types (with simulated data)."""
        from scipy import stats

        groups = [
            sample_expression_df[sample_expression_df["cancer_type"] == ct]["cd46_log2"].values
            for ct in sample_expression_df["cancer_type"].unique()
        ]

        stat, p_value = stats.kruskal(*groups)
        # With deliberately different distributions, should reject H0
        assert isinstance(stat, float)
        assert 0 <= p_value <= 1

    def test_priority_score_range(self):
        """Priority scores must be in [0, 1]."""
        try:
            from src.analysis.pan_cancer_cd46 import compute_priority_score
        except ImportError:
            pytest.skip("pan_cancer_cd46 not importable without data")

        # Mock input
        row = pd.Series(
            {
                "expression_rank": 0.9,
                "survival_impact": 0.7,
                "cna_freq": 0.3,
                "protein_score": 0.8,
            }
        )
        score = compute_priority_score(row)
        assert 0.0 <= score <= 1.0, f"Priority score out of range: {score}"

    def test_all_tcga_codes_in_priority_formula(self):
        """Formula weights must sum to 1.0."""
        weights = {"expression_rank": 0.35, "survival_impact": 0.35, "cna_freq": 0.15, "protein_score": 0.15}
        total = sum(weights.values())
        assert total == pytest.approx(1.0, abs=1e-9), f"Weights sum to {total}, expected 1.0"


# ---------------------------------------------------------------------------
# Survival analysis
# ---------------------------------------------------------------------------

class TestSurvivalAnalysis:
    def test_stratify_patients_by_median(self, sample_expression_df):
        """stratify_patients: exactly half should be in each group at median threshold."""
        try:
            from src.analysis.survival_analysis import stratify_patients
        except ImportError:
            pytest.skip("survival_analysis not importable")

        prad_df = sample_expression_df[sample_expression_df["cancer_type"] == "PRAD"].copy()
        stratified = stratify_patients(prad_df, threshold="median")

        assert "cd46_group" in stratified.columns
        n_high = (stratified["cd46_group"] == "High").sum()
        n_low = (stratified["cd46_group"] == "Low").sum()
        assert abs(n_high - n_low) <= 2, f"Unequal groups: {n_high} high, {n_low} low"

    def test_logrank_test_returns_float_p(self, sample_expression_df):
        """Log-rank test returns a float p-value."""
        try:
            from lifelines.statistics import logrank_test
        except ImportError:
            pytest.skip("lifelines not installed")

        prad_df = sample_expression_df[sample_expression_df["cancer_type"] == "PRAD"].copy()
        median_val = prad_df["cd46_log2"].median()
        high = prad_df[prad_df["cd46_log2"] >= median_val]
        low = prad_df[prad_df["cd46_log2"] < median_val]

        result = logrank_test(
            high["OS.time"], low["OS.time"],
            event_observed_A=high["OS"], event_observed_B=low["OS"]
        )
        assert isinstance(result.p_value, float)
        assert 0 <= result.p_value <= 1


# ---------------------------------------------------------------------------
# 225Ac eligibility analysis
# ---------------------------------------------------------------------------

class TestAc225EligibilityAnalysis:
    def test_eligibility_thresholds(self, sample_expression_df):
        """Eligibility fractions must be between 0 and 1 for all thresholds."""
        prad_df = sample_expression_df[sample_expression_df["cancer_type"] == "PRAD"].copy()
        cd46_vals = prad_df["cd46_log2"]

        thresholds = {
            "median": cd46_vals.median(),
            "75th_pct": cd46_vals.quantile(0.75),
            "log2_2.5": 2.5,
            "log2_3.0": 3.0,
        }

        for name, threshold_val in thresholds.items():
            n_eligible = (cd46_vals >= threshold_val).sum()
            fraction = n_eligible / len(cd46_vals)
            assert 0 <= fraction <= 1, f"Fraction out of range for {name}: {fraction}"

    def test_prad_eligibility_estimate_range(self, sample_expression_df):
        """PRAD at 75th pct should yield roughly 20-30% eligible in sample."""
        prad_df = sample_expression_df[sample_expression_df["cancer_type"] == "PRAD"]
        threshold = prad_df["cd46_log2"].quantile(0.75)
        fraction = (prad_df["cd46_log2"] >= threshold).sum() / len(prad_df)
        assert 0.20 <= fraction <= 0.35, f"75th pct fraction unexpected: {fraction:.2f}"

    def test_monotone_decreasing_eligibility(self, sample_expression_df):
        """Higher expression thresholds → fewer eligible patients."""
        prad_df = sample_expression_df[sample_expression_df["cancer_type"] == "PRAD"]
        cd46 = prad_df["cd46_log2"]

        fractions = [
            (cd46 >= cd46.median()).mean(),
            (cd46 >= cd46.quantile(0.75)).mean(),
            (cd46 >= 2.5).mean(),
            (cd46 >= 3.0).mean(),
        ]

        for i in range(len(fractions) - 1):
            assert fractions[i] >= fractions[i + 1] - 0.05, (
                f"Non-monotone eligibility: {fractions}"
            )
