"""Build ENROLLS / USES_BIOMARKER edges for ClinicalTrial nodes."""
from __future__ import annotations

import logging
from pathlib import Path

from neo4j import Driver

logger = logging.getLogger(__name__)

# Trial → Disease+Gene relationships based on curated trial data
TRIAL_DISEASE_EDGES = [
    {"nct_id": "NCT04946370", "tcga_code": "PRAD", "role": "Primary cohort"},
    {"nct_id": "NCT05911295", "tcga_code": "PRAD", "role": "Expansion cohort"},
    {"nct_id": "NCT05911295", "tcga_code": "OV",   "role": "Expansion cohort"},
    {"nct_id": "NCT05911295", "tcga_code": "BLCA", "role": "Expansion cohort"},
    {"nct_id": "NCT04768608", "tcga_code": "PRAD", "role": "Primary cohort"},
    {"nct_id": "NCT04768608", "tcga_code": "BLCA", "role": "Expansion cohort"},
    {"nct_id": "NCT03544840", "tcga_code": "PRAD", "role": "Primary cohort — PSMA benchmark"},
    {"nct_id": "NCT04986683", "tcga_code": "PRAD", "role": "Primary cohort — 225Ac RIT"},
]

# Trial → Drug relationships
TRIAL_DRUG_EDGES = [
    {"nct_id": "NCT04946370", "chembl_id": "CHEMBL1991779", "role": "Investigational agent"},
    {"nct_id": "NCT05911295", "chembl_id": "NOVEL_JF5",     "role": "CD46-based CAR-T"},
    {"nct_id": "NCT04768608", "chembl_id": "CHEMBL2176",    "role": "Investigational agent"},
    {"nct_id": "NCT03544840", "chembl_id": "CHEMBL1991779", "role": "Comparator arm"},
    {"nct_id": "NCT04986683", "chembl_id": "NOVEL_225AC_CD46", "role": "Analogous 225Ac RIT"},
]

# Trial USES_BIOMARKER: which biomarker qualifies patients
TRIAL_BIOMARKER_EDGES = [
    {
        "nct_id": "NCT04768608",
        "biomarker": "CD46 protein expression (IHC ≥ 1+)",
        "cutoff": "IHC ≥ 1+",
        "assessment_method": "Immunohistochemistry",
        "mandatory": True,
    },
    {
        "nct_id": "NCT05911295",
        "biomarker": "CD46 surface expression (flow cytometry)",
        "cutoff": ">50% tumor cells positive",
        "assessment_method": "Flow cytometry",
        "mandatory": True,
    },
    {
        "nct_id": "NCT04946370",
        "biomarker": "PSMA PET-CT SUVmax",
        "cutoff": "SUVmax ≥ 10 in ≥ 2 lesions",
        "assessment_method": "68Ga-PSMA PET-CT",
        "mandatory": True,
    },
    {
        "nct_id": "NCT03544840",
        "biomarker": "PSMA PET-CT",
        "cutoff": "PSMA-positive disease",
        "assessment_method": "68Ga-PSMA PET-CT",
        "mandatory": True,
    },
]


def build_trial_edges(driver: Driver, processed_dir: Path) -> dict:
    """Create Trial→Disease, Trial→Drug, and Trial biomarker edges."""
    disease_edges = 0
    drug_edges = 0
    biomarker_edges = 0

    with driver.session() as session:
        # Trial → Disease (ENROLLS)
        for edge in TRIAL_DISEASE_EDGES:
            session.run(
                """
                MATCH (ct:ClinicalTrial {nct_id: $nct_id})
                MATCH (d:Disease {tcga_code: $tcga_code})
                MERGE (ct)-[r:ENROLLS]->(d)
                SET r.role = $role
                """,
                **edge,
            )
            disease_edges += 1

        # Trial → Drug (TESTS)
        for edge in TRIAL_DRUG_EDGES:
            session.run(
                """
                MATCH (ct:ClinicalTrial {nct_id: $nct_id})
                MATCH (dr:Drug {chembl_id: $chembl_id})
                MERGE (ct)-[r:TESTS_DRUG]->(dr)
                SET r.role = $role
                """,
                **edge,
            )
            drug_edges += 1

        # Trial → Gene (USES_BIOMARKER)
        for edge in TRIAL_BIOMARKER_EDGES:
            session.run(
                """
                MATCH (ct:ClinicalTrial {nct_id: $nct_id})
                MATCH (g:Gene {ensembl_id: 'ENSG00000117335'})
                MERGE (ct)-[r:USES_BIOMARKER]->(g)
                SET r.biomarker         = $biomarker,
                    r.cutoff            = $cutoff,
                    r.assessment_method = $assessment_method,
                    r.mandatory         = $mandatory
                """,
                **edge,
            )
            biomarker_edges += 1

    logger.info(
        "Created %d Trial→Disease + %d Trial→Drug + %d USES_BIOMARKER edges",
        disease_edges,
        drug_edges,
        biomarker_edges,
    )
    return {
        "trial_disease_edges": disease_edges,
        "trial_drug_edges": drug_edges,
        "trial_biomarker_edges": biomarker_edges,
    }
