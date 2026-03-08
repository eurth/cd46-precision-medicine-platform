"""Build TARGETS / TESTED_IN drug-related edges."""
from __future__ import annotations

import logging
from pathlib import Path

from neo4j import Driver

logger = logging.getLogger(__name__)

# Drug→Disease relationships derived from known clinical data
DRUG_INDICATION_EDGES = [
    {
        "chembl_id": "NOVEL_225AC_CD46",
        "tcga_code": "PRAD",
        "relationship_type": "PRIMARY_INDICATION",
        "clinical_stage": "Preclinical / Phase I design",
        "evidence": "Prof. Bobba Naidu program — direct target population",
    },
    {
        "chembl_id": "CHEMBL2176",
        "tcga_code": "PRAD",
        "relationship_type": "TESTED_IN",
        "clinical_stage": "Phase I/II",
        "evidence": "ABBV-CLS-484 NCT04768608 primary cohort",
    },
    {
        "chembl_id": "CHEMBL2176",
        "tcga_code": "BLCA",
        "relationship_type": "TESTED_IN",
        "clinical_stage": "Phase I/II",
        "evidence": "ABBV-CLS-484 expansion cohort",
    },
    {
        "chembl_id": "CHEMBL1201583",
        "tcga_code": "PRAD",
        "relationship_type": "COMBINATION_CANDIDATE",
        "clinical_stage": "Approved",
        "evidence": "Standard first-line mCRPC; used before 225Ac-CD46 in tx sequence",
    },
    {
        "chembl_id": "CHEMBL1201587",
        "tcga_code": "PRAD",
        "relationship_type": "COMBINATION_CANDIDATE",
        "clinical_stage": "Approved",
        "evidence": "AR blockade upregulates CD46 — combination rationale",
    },
    {
        "chembl_id": "CHEMBL1991779",
        "tcga_code": "PRAD",
        "relationship_type": "PARALLEL_TARGET",
        "clinical_stage": "Approved",
        "evidence": "PSMA-low patients (~35%) are CD46-high — complementary targeting",
    },
    {
        "chembl_id": "NOVEL_JF5",
        "tcga_code": "PRAD",
        "relationship_type": "RESEARCH_TOOL",
        "clinical_stage": "Preclinical",
        "evidence": "scFv used in CAR-T and ADC development pipelines",
    },
]

# Drug→CellLine TESTED_IN relationships
DRUG_CELLLINE_EDGES = [
    {"chembl_id": "NOVEL_225AC_CD46", "cell_line_id": "LNCaP", "efficacy": "High tumor regression", "model": "Xenograft"},
    {"chembl_id": "NOVEL_225AC_CD46", "cell_line_id": "22Rv1", "efficacy": "Moderate — AR-V7 reduces PSMA but CD46 retained", "model": "Xenograft"},
    {"chembl_id": "CHEMBL2176", "cell_line_id": "LNCaP", "efficacy": "High — MMAE ADC active", "model": "In vitro + xenograft"},
    {"chembl_id": "CHEMBL2176", "cell_line_id": "PC3", "efficacy": "Moderate — AR-independent lines respond", "model": "In vitro"},
    {"chembl_id": "CHEMBL1201587", "cell_line_id": "LNCaP", "efficacy": "High initial, resistance develops", "model": "In vitro"},
    {"chembl_id": "NOVEL_JF5", "cell_line_id": "LNCaP", "efficacy": "Complement lysis induced", "model": "In vitro"},
    {"chembl_id": "NOVEL_JF5", "cell_line_id": "PC3", "efficacy": "Moderate complement lysis", "model": "In vitro"},
]


def build_drug_edges(driver: Driver, processed_dir: Path) -> dict:
    """Create Drug→Disease and Drug→CellLine edges."""
    indication_edges = 0
    cellline_edges = 0

    with driver.session() as session:
        # Drug → Disease indication edges
        for edge in DRUG_INDICATION_EDGES:
            session.run(
                """
                MATCH (dr:Drug {chembl_id: $chembl_id})
                MATCH (d:Disease {tcga_code: $tcga_code})
                MERGE (dr)-[r:TESTED_IN]->(d)
                SET r.relationship_type = $relationship_type,
                    r.clinical_stage    = $clinical_stage,
                    r.evidence          = $evidence
                """,
                **edge,
            )
            indication_edges += 1

        # Drug → CellLine edges
        for edge in DRUG_CELLLINE_EDGES:
            session.run(
                """
                MATCH (dr:Drug {chembl_id: $chembl_id})
                MATCH (cl:CellLine {cell_line_id: $cell_line_id})
                MERGE (dr)-[r:TESTED_IN_CELL_LINE]->(cl)
                SET r.efficacy = $efficacy,
                    r.model    = $model
                """,
                **edge,
            )
            cellline_edges += 1

    logger.info(
        "Created %d Drug→Disease edges + %d Drug→CellLine edges",
        indication_edges,
        cellline_edges,
    )
    return {"drug_indication_edges": indication_edges, "drug_cellline_edges": cellline_edges}
