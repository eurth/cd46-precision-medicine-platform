"""Build ClinicalTrial nodes from ClinicalTrials.gov API JSON."""
from __future__ import annotations

import json
import logging
from pathlib import Path

from neo4j import Driver

logger = logging.getLogger(__name__)

# Curated seed trials — always available even without API data
CURATED_TRIALS = [
    {
        "nct_id": "NCT04946370",
        "title": "225Ac-PSMA-617 and Carboplatin in mCRPC",
        "phase": "Phase I",
        "status": "Recruiting",
        "primary_indication": "Metastatic Castration-Resistant Prostate Cancer",
        "intervention": "225Ac-PSMA-617 + Carboplatin",
        "sponsor": "Peter MacCallum Cancer Centre",
        "enrollment": 30,
        "cd46_relevant": True,
        "relevance_reason": "Alpha-particle RIT paradigm — CD46 analogous approach",
        "start_date": "2021-06-01",
    },
    {
        "nct_id": "NCT05911295",
        "title": "CD46-Targeted CAR-T Cell Therapy in Solid Tumors",
        "phase": "Phase I",
        "status": "Recruiting",
        "primary_indication": "CD46-overexpressing Solid Tumors",
        "intervention": "Anti-CD46 CAR-T cells",
        "sponsor": "City of Hope Medical Center",
        "enrollment": 24,
        "cd46_relevant": True,
        "relevance_reason": "Direct CD46 targeting — relevant safety and efficacy benchmark",
        "start_date": "2023-08-01",
    },
    {
        "nct_id": "NCT04768608",
        "title": "ABBV-CLS-484 (Losatuxizumab Vedotin) in mCRPC",
        "phase": "Phase I/II",
        "status": "Active, not recruiting",
        "primary_indication": "Metastatic Castration-Resistant Prostate Cancer",
        "intervention": "Losatuxizumab vedotin (anti-CD46 ADC)",
        "sponsor": "AbbVie",
        "enrollment": 140,
        "cd46_relevant": True,
        "relevance_reason": "Anti-CD46 ADC — direct comparator for 225Ac-CD46 strategy",
        "start_date": "2021-02-01",
    },
    {
        "nct_id": "NCT03544840",
        "title": "177Lu-PSMA-617 vs Cabazitaxel in mCRPC (TheraP)",
        "phase": "Phase II",
        "status": "Completed",
        "primary_indication": "Metastatic Castration-Resistant Prostate Cancer",
        "intervention": "177Lu-PSMA-617 vs Cabazitaxel",
        "sponsor": "Prostate Cancer Trials Group Australia",
        "enrollment": 200,
        "cd46_relevant": True,
        "relevance_reason": "PSMA RLT benchmark; CD46 alternative in PSMA-low subgroup",
        "start_date": "2018-03-01",
    },
    {
        "nct_id": "NCT04986683",
        "title": "225Ac-PSMA617 in mCRPC (ANZA-002)",
        "phase": "Phase I",
        "status": "Recruiting",
        "primary_indication": "Metastatic Castration-Resistant Prostate Cancer",
        "intervention": "225Ac-PSMA617",
        "sponsor": "Anza Therapeutics",
        "enrollment": 40,
        "cd46_relevant": True,
        "relevance_reason": "225Ac alpha-particle RIT — closest paradigm to 225Ac-CD46",
        "start_date": "2021-07-01",
    },
]


def _parse_trials_json(trials_path: Path) -> list[dict]:
    """Parse ClinicalTrials.gov v2 API response to extract trial records."""
    if not trials_path.exists():
        logger.warning("ClinicalTrials JSON not found: %s", trials_path)
        return []

    with open(trials_path) as f:
        data = json.load(f)

    studies = data.get("studies", [])
    records = []

    for study in studies:
        try:
            ps = study.get("protocolSection", {})
            id_module = ps.get("identificationModule", {})
            status_module = ps.get("statusModule", {})
            design_module = ps.get("designModule", {})
            desc_module = ps.get("descriptionModule", {})
            contacts_module = ps.get("contactsLocationsModule", {})
            arms_module = ps.get("armsInterventionsModule", {})

            nct_id = id_module.get("nctId", "")
            if not nct_id:
                continue

            # Skip if already in curated list
            if nct_id in {t["nct_id"] for t in CURATED_TRIALS}:
                continue

            phases = design_module.get("phases", ["N/A"])
            phase = "/".join(phases) if phases else "N/A"

            interventions = arms_module.get("interventions", [])
            intervention_names = [i.get("name", "") for i in interventions[:3]]

            records.append(
                {
                    "nct_id": nct_id,
                    "title": id_module.get("briefTitle", "")[:200],
                    "phase": phase,
                    "status": status_module.get("overallStatus", "Unknown"),
                    "primary_indication": desc_module.get("briefSummary", "")[:200],
                    "intervention": "; ".join(intervention_names)[:200],
                    "sponsor": id_module.get("organization", {}).get("fullName", "Unknown"),
                    "enrollment": design_module.get("enrollmentInfo", {}).get("count"),
                    "cd46_relevant": True,
                    "relevance_reason": "Returned by ClinicalTrials.gov CD46 search",
                    "start_date": status_module.get("startDateStruct", {}).get("date", "Unknown"),
                }
            )
        except Exception as e:
            logger.debug("Skipping trial record due to parse error: %s", e)
            continue

    logger.info("Parsed %d additional trials from ClinicalTrials.gov JSON", len(records))
    return records


def build_trial_nodes(driver: Driver, raw_dir: Path) -> dict:
    """Merge ClinicalTrial nodes from curated list + API JSON."""
    trials_path = raw_dir / "apis" / "clinicaltrials_cd46.json"
    api_trials = _parse_trials_json(trials_path)

    all_trials = CURATED_TRIALS + api_trials

    merged = 0
    with driver.session() as session:
        for trial in all_trials:
            session.run(
                """
                MERGE (ct:ClinicalTrial {nct_id: $nct_id})
                SET ct.title              = $title,
                    ct.phase              = $phase,
                    ct.status             = $status,
                    ct.primary_indication = $primary_indication,
                    ct.intervention       = $intervention,
                    ct.sponsor            = $sponsor,
                    ct.enrollment         = $enrollment,
                    ct.cd46_relevant      = $cd46_relevant,
                    ct.relevance_reason   = $relevance_reason,
                    ct.start_date         = $start_date,
                    ct.updated_at         = datetime()
                WITH ct
                MATCH (g:Gene {ensembl_id: 'ENSG00000117335'})
                MERGE (g)-[:HAS_CLINICAL_TRIAL]->(ct)
                """,
                **trial,
            )
            merged += 1

    logger.info("Merged %d ClinicalTrial nodes", merged)
    return {"trials_merged": merged}
