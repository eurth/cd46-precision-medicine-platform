"""Tests for Knowledge Graph node and relationship builders."""
from __future__ import annotations

from unittest.mock import MagicMock, call, patch

import pandas as pd
import pytest


# ---------------------------------------------------------------------------
# Fixtures — mock Neo4j driver
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_driver():
    """Mock Neo4j driver that captures Cypher queries."""
    driver = MagicMock()
    session = MagicMock()
    driver.session.return_value.__enter__ = MagicMock(return_value=session)
    driver.session.return_value.__exit__ = MagicMock(return_value=False)
    session.run = MagicMock(return_value=MagicMock())
    return driver, session


# ---------------------------------------------------------------------------
# Gene node builder
# ---------------------------------------------------------------------------

class TestBuildGeneNodes:
    def test_merges_gene_node(self, mock_driver):
        from src.knowledge_graph.node_builders.build_gene_nodes import build_gene_nodes

        driver, session = mock_driver
        result = build_gene_nodes(driver)

        assert result["genes_merged"] == 1
        assert result["proteins_merged"] == 1
        assert result["pathways_merged"] == 5
        assert session.run.called

    def test_gene_cypher_uses_ensembl_id(self, mock_driver):
        from src.knowledge_graph.node_builders.build_gene_nodes import build_gene_nodes

        driver, session = mock_driver
        build_gene_nodes(driver)

        # Check that at least one call contains the CD46 Ensembl ID
        all_calls = [str(c) for c in session.run.call_args_list]
        assert any("ENSG00000117335" in c for c in all_calls), (
            "No Cypher call found referencing ENSG00000117335"
        )


# ---------------------------------------------------------------------------
# Disease node builder
# ---------------------------------------------------------------------------

class TestBuildDiseaseNodes:
    def test_uses_static_metadata_when_no_csv(self, mock_driver, tmp_path):
        from src.knowledge_graph.node_builders.build_disease_nodes import build_disease_nodes

        driver, session = mock_driver
        result = build_disease_nodes(driver, tmp_path)

        # Should merge all 33 cancers from DISEASE_META
        assert result["diseases_merged"] == 33

    def test_merges_expression_stats_from_csv(self, mock_driver, tmp_path):
        from src.knowledge_graph.node_builders.build_disease_nodes import build_disease_nodes

        driver, session = mock_driver

        # Create minimal CSV
        df = pd.DataFrame(
            {
                "cancer_type": ["PRAD", "OV"],
                "mean": [4.5, 3.8],
                "median": [4.4, 3.7],
                "std": [0.8, 0.9],
                "count": [497, 420],
            }
        )
        (tmp_path / "cd46_by_cancer.csv").unlink(missing_ok=True)
        df.to_csv(tmp_path / "cd46_by_cancer.csv", index=False)

        result = build_disease_nodes(driver, tmp_path)
        assert result["diseases_merged"] == 33  # all 33 from DISEASE_META


# ---------------------------------------------------------------------------
# Drug node builder
# ---------------------------------------------------------------------------

class TestBuildDrugNodes:
    def test_merges_curated_drugs(self, mock_driver, tmp_path):
        from src.knowledge_graph.node_builders.build_drug_nodes import (
            CURATED_DRUGS,
            build_drug_nodes,
        )

        driver, session = mock_driver
        result = build_drug_nodes(driver, tmp_path)

        assert result["drugs_merged"] >= len(CURATED_DRUGS)

    def test_225ac_drug_in_curated(self):
        from src.knowledge_graph.node_builders.build_drug_nodes import CURATED_DRUGS

        ids = [d["chembl_id"] for d in CURATED_DRUGS]
        assert "NOVEL_225AC_CD46" in ids


# ---------------------------------------------------------------------------
# Schema tests
# ---------------------------------------------------------------------------

class TestKGSchema:
    def test_gene_node_to_dict(self):
        from src.knowledge_graph.schema import GeneNode

        node = GeneNode(
            ensembl_id="ENSG00000117335",
            symbol="CD46",
            entrez_id="4179",
            chromosome="1q32.2",
            full_name="CD46 molecule",
        )
        d = node.to_dict()
        assert d["ensembl_id"] == "ENSG00000117335"
        assert d["symbol"] == "CD46"

    def test_disease_node_to_dict(self):
        from src.knowledge_graph.schema import DiseaseNode

        node = DiseaseNode(tcga_code="PRAD", full_name="Prostate Adenocarcinoma", icd10="C61")
        d = node.to_dict()
        assert d["tcga_code"] == "PRAD"

    def test_all_node_types_have_to_dict(self):
        """All node dataclasses must implement to_dict() without error."""
        from src.knowledge_graph import schema

        node_classes = [
            (schema.GeneNode, {"ensembl_id": "X", "symbol": "X", "entrez_id": "1", "chromosome": "1", "full_name": "X"}),
            (schema.ProteinNode, {"uniprot_id": "P1", "name": "N", "symbol": "S"}),
            (schema.DiseaseNode, {"tcga_code": "X", "full_name": "N", "icd10": "C1"}),
            (schema.TissueNode, {"tissue_name": "T", "tissue_type": "Epithelial"}),
            (schema.DrugNode, {"chembl_id": "C1", "name": "D1", "drug_type": "ADC"}),
        ]
        for cls, kwargs in node_classes:
            node = cls(**kwargs)
            d = node.to_dict()
            assert isinstance(d, dict)
            assert len(d) > 0


# ---------------------------------------------------------------------------
# Curated data consistency
# ---------------------------------------------------------------------------

class TestCuratedDataConsistency:
    def test_trial_nct_ids_format(self):
        from src.knowledge_graph.node_builders.build_trial_nodes import CURATED_TRIALS

        for trial in CURATED_TRIALS:
            assert trial["nct_id"].startswith("NCT"), f"Invalid NCT ID: {trial['nct_id']}"
            assert len(trial["nct_id"]) == 11, f"NCT ID wrong length: {trial['nct_id']}"

    def test_publications_have_required_fields(self):
        from src.knowledge_graph.node_builders.build_publication_nodes import CURATED_PUBLICATIONS

        required = {"pubmed_id", "title", "journal", "year", "evidence_type"}
        for pub in CURATED_PUBLICATIONS:
            missing = required - set(pub.keys())
            assert not missing, f"Publication {pub.get('pubmed_id')} missing: {missing}"

    def test_curated_cell_lines_have_cancer_type(self):
        from src.knowledge_graph.node_builders.build_cellline_nodes import CURATED_CELL_LINES

        for cl in CURATED_CELL_LINES:
            assert cl.get("cancer_type"), f"Cell line {cl['cell_line_id']} missing cancer_type"
