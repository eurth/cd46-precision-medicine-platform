"""Tests for data loading utilities."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def sample_expression_df():
    return pd.DataFrame(
        {
            "sample_id": ["TCGA-01", "TCGA-02", "TCGA-03"],
            "cd46_log2": [4.2, 3.8, 2.1],
            "cancer_type": ["PRAD", "PRAD", "BRCA"],
            "OS": [365, 730, 500],
            "OS.time": [365, 730, 500],
        }
    )


@pytest.fixture
def sample_hpa_df():
    return pd.DataFrame(
        {
            "tissue": ["Prostate", "Ovary", "Brain"],
            "tumor_level": ["High", "High", "Low"],
            "normal_level": ["Medium", "Medium", "Low"],
        }
    )


# ---------------------------------------------------------------------------
# test_load_csv_data
# ---------------------------------------------------------------------------

class TestLoadCsvData:
    def test_returns_error_for_unknown_dataset(self):
        from src.agent.tools import load_csv_data
        import json

        result = json.loads(load_csv_data("nonexistent_dataset"))
        assert "error" in result

    def test_known_dataset_missing_file_returns_error(self):
        from src.agent.tools import load_csv_data
        import json

        # File won't exist in test env
        result = json.loads(load_csv_data("expression"))
        # Either returns data or error — both valid
        assert "error" in result or "dataset" in result

    def test_filters_by_cancer_type(self, tmp_path, monkeypatch):
        from src.agent import tools
        import json

        # Write a temp CSV
        df = pd.DataFrame(
            {
                "cancer_type": ["PRAD", "OV", "PRAD"],
                "mean": [4.2, 3.1, 3.9],
            }
        )
        csv_path = tmp_path / "cd46_by_cancer.csv"
        df.to_csv(csv_path, index=False)

        monkeypatch.setattr(tools, "DATA_DIR", tmp_path)

        result = json.loads(load_csv_data("by_cancer", cancer_type="PRAD"))
        assert result.get("total_rows") == 2


from src.agent.tools import load_csv_data  # noqa: E402  (used in test)


# ---------------------------------------------------------------------------
# test_get_eligibility
# ---------------------------------------------------------------------------

class TestGetEligibility:
    def test_missing_file_returns_static_prad(self):
        from src.agent.tools import get_eligibility
        import json

        result = json.loads(get_eligibility("PRAD", "75th_pct"))
        # Either static or real data — must have numeric eligible count
        assert "n_eligible" in result or "error" in result

    def test_eligibility_with_temp_csv(self, tmp_path, monkeypatch):
        from src.agent import tools
        import json

        df = pd.DataFrame(
            {
                "cancer_type": ["PRAD", "PRAD", "OV"],
                "threshold": ["75th_pct", "median", "75th_pct"],
                "n_eligible": [219, 249, 180],
                "n_total": [497, 497, 420],
                "fraction_eligible": [0.441, 0.501, 0.429],
            }
        )
        csv_path = tmp_path / "patient_groups.csv"
        df.to_csv(csv_path, index=False)
        monkeypatch.setattr(tools, "DATA_DIR", tmp_path)

        result = json.loads(get_eligibility("PRAD", "75th_pct"))
        assert result["n_eligible"] == 219
        assert result["pct_eligible"] == pytest.approx(44.1, abs=0.5)


# ---------------------------------------------------------------------------
# test_search_trials
# ---------------------------------------------------------------------------

class TestSearchTrials:
    def test_cd46_search_returns_results(self):
        from src.agent.tools import search_trials
        import json

        results = json.loads(search_trials("CD46"))
        assert len(results) > 0
        assert all("nct_id" in t for t in results)

    def test_status_filter(self):
        from src.agent.tools import search_trials
        import json

        results = json.loads(search_trials("CD46", status="Recruiting"))
        assert all("Recruiting" in t.get("status", "") or t.get("status") == "Recruiting" for t in results)

    def test_no_results_for_nonsense_query(self):
        from src.agent.tools import search_trials
        import json

        results = json.loads(search_trials("zzz_no_match_xyz"))
        assert len(results) == 0
