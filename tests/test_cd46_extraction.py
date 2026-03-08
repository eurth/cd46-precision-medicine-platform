"""Tests for CD46 extraction from TCGA matrix (Polars lazy scan)."""
from __future__ import annotations

import gzip
from pathlib import Path

import pandas as pd
import pytest


ENSEMBL_CD46 = "ENSG00000117335"


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def fake_tcga_matrix(tmp_path) -> Path:
    """Create a tiny gzipped TCGA-like expression matrix for testing."""
    data = (
        "sample\tTCGA-01\tTCGA-02\tTCGA-03\n"
        f"{ENSEMBL_CD46}\t4.2\t3.8\t5.1\n"
        "ENSG00000000001\t1.0\t2.0\t3.0\n"
        "ENSG00000000002\t0.5\t0.8\t1.2\n"
    )
    gz_path = tmp_path / "tcga_expression.gz"
    with gzip.open(gz_path, "wt") as f:
        f.write(data)
    return gz_path


@pytest.fixture
def fake_phenotype(tmp_path) -> Path:
    data = "sample\t_primary_disease\nTCGA-01\tProstate Adenocarcinoma\nTCGA-02\tProstate Adenocarcinoma\nTCGA-03\tOvarian Serous Cystadenocarcinoma\n"
    p = tmp_path / "phenotype.gz"
    with gzip.open(p, "wt") as f:
        f.write(data)
    return p


@pytest.fixture
def fake_survival(tmp_path) -> Path:
    data = "sample\tOS\tOS.time\nTCGA-01\t1\t365\nTCGA-02\t0\t730\nTCGA-03\t1\t500\n"
    p = tmp_path / "survival.gz"
    with gzip.open(p, "wt") as f:
        f.write(data)
    return p


# ---------------------------------------------------------------------------
# Unit tests for extract_cd46.py helpers
# ---------------------------------------------------------------------------

class TestCD46Extraction:
    def test_cd46_ensembl_id_constant(self):
        """Verify the canonical CD46 Ensembl ID is correct."""
        assert ENSEMBL_CD46 == "ENSG00000117335"

    def test_extract_single_gene_row(self, fake_tcga_matrix, tmp_path):
        """Polars reads only the CD46 row from a gzipped tab-delimited file."""
        try:
            import polars as pl
        except ImportError:
            pytest.skip("polars not installed")

        # Read and check CD46 row exists
        lf = pl.scan_csv(fake_tcga_matrix, separator="\t", has_header=True)
        cd46_row = lf.filter(pl.col("sample") == ENSEMBL_CD46).collect()

        assert len(cd46_row) == 1
        assert float(cd46_row["TCGA-01"][0]) == pytest.approx(4.2)

    def test_harmonize_cancer_codes(self):
        """harmonize_datasets.py maps disease names to TCGA codes."""
        from src.preprocessing.harmonize_datasets import get_disease_meta

        meta = get_disease_meta("PRAD")
        assert meta["full_name"] == "Prostate Adenocarcinoma"
        assert meta["icd10"].startswith("C")
        assert "NCIT" in meta["ncit"]

    def test_harmonize_all_33_cancers(self):
        """All 33 TCGA cancer codes have metadata entries."""
        from src.preprocessing.harmonize_datasets import get_disease_meta

        TCGA_CODES = [
            "PRAD", "OV", "BLCA", "LUAD", "LUSC", "BRCA", "COAD", "READ", "STAD",
            "LIHC", "KIRC", "KIRP", "KICH", "THCA", "UCEC", "CESC", "HNSC", "SKCM",
            "GBM", "LGG", "PCPG", "ACC", "TGCT", "THYM", "MESO", "UVM", "UCS",
            "DLBC", "LAML", "SARC", "CHOL", "PAAD", "ESCA",
        ]
        missing = []
        for code in TCGA_CODES:
            try:
                meta = get_disease_meta(code)
                if not meta.get("full_name"):
                    missing.append(code)
            except (KeyError, AttributeError):
                missing.append(code)

        assert missing == [], f"Missing metadata for: {missing}"


# ---------------------------------------------------------------------------
# HPA processing
# ---------------------------------------------------------------------------

class TestHPAProcessing:
    def test_fallback_data_has_prostate(self):
        """HPA fallback returns prostate tumor expression."""
        from src.preprocessing.process_hpa import _hpa_fallback_data

        records = _hpa_fallback_data()
        df = pd.DataFrame(records)
        prostate_row = df[df["tissue"] == "Prostate"]
        assert len(prostate_row) > 0
        assert prostate_row.iloc[0]["tumor_level"] in ["High", "Medium"]

    def test_fallback_data_all_tissues_have_both_levels(self):
        """All fallback tissue rows have both tumor_level and normal_level."""
        from src.preprocessing.process_hpa import _hpa_fallback_data

        records = _hpa_fallback_data()
        for rec in records:
            assert "tumor_level" in rec, f"Missing tumor_level: {rec}"
            assert "normal_level" in rec, f"Missing normal_level: {rec}"
            assert rec["tumor_level"] in ["Not detected", "Low", "Medium", "High"]
