"""ponytail: Step-1 honesty — tiers, case_study gate logic, gene CSV map."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "app"))
sys.path.insert(0, str(ROOT))

from components.targets import (  # noqa: E402
    assert_phase2_targets,
    data_tier,
    is_case_study,
    load_registry,
)
from src.agent.tools import _gene_file_map  # noqa: E402


def main() -> None:
    load_registry.cache_clear()
    assert_phase2_targets()
    assert data_tier("CD46") == "full"
    assert is_case_study("CD46") and not is_case_study("FOLH1")
    m = _gene_file_map("FOLH1")
    assert m["by_cancer"] == "folh1_by_cancer.csv"
    assert m["survival"] == "folh1_survival_results.csv"
    assert (ROOT / "data/processed/folh1_survival_results.csv").exists()
    print("OK step1_honesty")


if __name__ == "__main__":
    main()
