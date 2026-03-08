"""Build SUPPORTS evidence edges from Publications + Open Targets."""
from __future__ import annotations

import json
import logging
from pathlib import Path

from neo4j import Driver

logger = logging.getLogger(__name__)

# Curated Publication → Disease SUPPORTS edges with evidence strength
PUB_DISEASE_EVIDENCE = [
    {
        "pubmed_id": "33740951",
        "tcga_code": "PRAD",
        "evidence_category": "Radiotherapy",
        "evidence_strength": 0.95,
        "notes": "Direct 225Ac-CD46 preclinical study in mCRPC",
    },
    {
        "pubmed_id": "PMC7398579",
        "tcga_code": "PRAD",
        "evidence_category": "ADC therapy",
        "evidence_strength": 0.90,
        "notes": "CD46 ADC efficacy in PRAD xenograft",
    },
    {
        "pubmed_id": "PMC7398579",
        "tcga_code": "BLCA",
        "evidence_category": "ADC therapy",
        "evidence_strength": 0.85,
        "notes": "CD46 ADC efficacy in bladder cancer xenograft",
    },
    {
        "pubmed_id": "32461245",
        "tcga_code": "PRAD",
        "evidence_category": "Biomarker — resistance",
        "evidence_strength": 0.88,
        "notes": "AR signaling regulates CD46 in CRPC",
    },
    {
        "pubmed_id": "28898243",
        "tcga_code": "PRAD",
        "evidence_category": "Biomarker — expression",
        "evidence_strength": 0.92,
        "notes": "IHC validation: CD46 in 72% PCa specimens",
    },
    {
        "pubmed_id": "36754843",
        "tcga_code": "PRAD",
        "evidence_category": "RLT benchmark",
        "evidence_strength": 0.93,
        "notes": "177Lu-PSMA TheraP — PSMA-low gap filled by CD46",
    },
    {
        "pubmed_id": "31375513",
        "tcga_code": "OV",
        "evidence_category": "Bioinformatics",
        "evidence_strength": 0.72,
        "notes": "Pan-TCGA complement gene analysis",
    },
    {
        "pubmed_id": "31375513",
        "tcga_code": "BLCA",
        "evidence_category": "Bioinformatics",
        "evidence_strength": 0.70,
        "notes": "Pan-TCGA complement gene analysis",
    },
]

# Open Targets association evidence → Disease nodes
def _parse_open_targets_json(ot_path: Path) -> list[dict]:
    """Parse Open Targets GraphQL response for disease associations."""
    if not ot_path.exists():
        logger.warning("Open Targets JSON not found: %s", ot_path)
        return []

    with open(ot_path) as f:
        data = json.load(f)

    try:
        diseases = (
            data.get("data", {})
            .get("target", {})
            .get("associatedDiseases", {})
            .get("rows", [])
        )
    except AttributeError:
        logger.warning("Could not parse Open Targets disease associations")
        return []

    records = []
    for row in diseases:
        try:
            disease_id = row.get("disease", {}).get("id", "")
            disease_name = row.get("disease", {}).get("name", "")
            score = float(row.get("score", 0))
            records.append(
                {
                    "disease_id": disease_id,
                    "disease_name": disease_name,
                    "score": score,
                }
            )
        except Exception:
            continue

    logger.info("Parsed %d disease associations from Open Targets", len(records))
    return records


def build_evidence_edges(driver: Driver, raw_dir: Path) -> dict:
    """Create SUPPORTS edges from Publications→Disease and Open Targets→Disease."""
    pub_edges = 0
    ot_edges = 0

    with driver.session() as session:
        # Publication → Disease SUPPORTS edges
        for edge in PUB_DISEASE_EVIDENCE:
            session.run(
                """
                MATCH (pub:Publication {pubmed_id: $pubmed_id})
                MATCH (d:Disease {tcga_code: $tcga_code})
                MERGE (pub)-[r:SUPPORTS_DISEASE]->(d)
                SET r.evidence_category  = $evidence_category,
                    r.evidence_strength  = $evidence_strength,
                    r.notes              = $notes
                """,
                **edge,
            )
            pub_edges += 1

        # Open Targets → Disease DataSource evidence nodes
        ot_path = raw_dir / "apis" / "open_targets_cd46.json"
        ot_diseases = _parse_open_targets_json(ot_path)

        for ot in ot_diseases:
            # Create OpenTargets DataSource node if needed
            session.run(
                """
                MERGE (ds:DataSource {source_id: 'OpenTargets_CD46'})
                SET ds.name        = 'Open Targets Platform',
                    ds.url         = 'https://www.opentargets.org',
                    ds.data_type   = 'Multi-evidence target-disease association',
                    ds.version     = '24.03'
                WITH ds
                MATCH (g:Gene {ensembl_id: 'ENSG00000117335'})
                MERGE (ds)-[:SCORES]->(g)
                """
            )

            # Link Open Targets disease to DataSource via score
            session.run(
                """
                MATCH (ds:DataSource {source_id: 'OpenTargets_CD46'})
                MERGE (otd:OTDisease {disease_id: $disease_id})
                SET otd.disease_name = $disease_name,
                    otd.score        = $score
                MERGE (ds)-[r:ASSOCIATES]->(otd)
                SET r.score = $score
                """,
                disease_id=ot["disease_id"],
                disease_name=ot["disease_name"],
                score=ot["score"],
            )
            ot_edges += 1

    logger.info(
        "Created %d Publication→Disease SUPPORTS + %d Open Targets edges",
        pub_edges,
        ot_edges,
    )
    return {"publication_evidence_edges": pub_edges, "open_targets_edges": ot_edges}
