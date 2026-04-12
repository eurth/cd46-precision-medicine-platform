"""Build Drug nodes from ChEMBL data + curated 225Ac therapeutics."""
from __future__ import annotations

import json
import logging
from pathlib import Path

from neo4j import Driver

logger = logging.getLogger(__name__)

# Curated drugs with known CD46 relevance — always loaded regardless of ChEMBL API
CURATED_DRUGS = [
    {
        "chembl_id": "NOVEL_225AC_CD46",
        "name": "225Ac-DOTA-anti-CD46 mAb",
        "drug_type": "Radioimmunoconjugate",
        "mechanism_of_action": "Alpha-particle emitter tethered to anti-CD46 monoclonal antibody; delivers cytotoxic 225Ac decay chain to CD46+ tumor cells",
        "phase": "Preclinical / Phase I design",
        "target": "CD46 (ENSG00000117335)",
        "indication": "mCRPC, CD46-overexpressing solid tumors",
        "notes": "Primary therapeutic agent in the 225Ac-CD46 radiopharmaceutical programme",
    },
    {
        "chembl_id": "CHEMBL2176",
        "name": "Losatuxizumab vedotin (ABBV-CLS-484)",
        "drug_type": "Antibody-drug conjugate",
        "mechanism_of_action": "Anti-CD46 antibody conjugated to MMAE; disrupts microtubules in CD46+ cells",
        "phase": "Phase I/II",
        "target": "CD46",
        "indication": "mCRPC",
        "notes": "Abbvie / Calimmune — benchmark comparator",
    },
    {
        "chembl_id": "CHEMBL1201583",
        "name": "Docetaxel",
        "drug_type": "Small molecule — taxane",
        "mechanism_of_action": "Microtubule stabilization; standard first-line mCRPC chemotherapy",
        "phase": "Approved",
        "target": "Tubulin",
        "indication": "mCRPC",
        "notes": "Combination partner — CD46 expression modulated by taxane exposure",
    },
    {
        "chembl_id": "CHEMBL1201587",
        "name": "Enzalutamide",
        "drug_type": "Small molecule — androgen receptor antagonist",
        "mechanism_of_action": "Blocks androgen receptor nuclear translocation; downstream AR signaling suppresses CD46",
        "phase": "Approved",
        "target": "Androgen Receptor (AR)",
        "indication": "mCRPC",
        "notes": "AR blockade may upregulate CD46 — resistance mechanism hypothesis",
    },
    {
        "chembl_id": "CHEMBL1991779",
        "name": "PSMA-617 (177Lu-PSMA-617 / Pluvicto)",
        "drug_type": "Radioligand therapy",
        "mechanism_of_action": "177Lu beta-emitter targeted to PSMA; complementary to CD46 targeting in PSMA-low tumors",
        "phase": "Approved",
        "target": "PSMA (FOLH1)",
        "indication": "mCRPC",
        "notes": "CD46 is alternative target when PSMA is low — combination strategy",
    },
    {
        "chembl_id": "NOVEL_JF5",
        "name": "JF5 (anti-CD46 scFv)",
        "drug_type": "Single-chain antibody fragment",
        "mechanism_of_action": "Binds SCR1-2 domains of CD46; blocks complement evasion",
        "phase": "Preclinical",
        "target": "CD46 SCR1-2 domains",
        "indication": "Prostate cancer",
        "notes": "Research tool — basis for CAR-T and ADC development",
    },
]


def _parse_chembl_json(chembl_path: Path) -> list[dict]:
    """Parse ChEMBL API JSON to extract bioactivity records."""
    if not chembl_path.exists():
        logger.warning("ChEMBL JSON not found: %s", chembl_path)
        return []

    with open(chembl_path) as f:
        data = json.load(f)

    records = []
    activities = data.get("activities", [])
    for act in activities:
        try:
            records.append(
                {
                    "chembl_id": act.get("molecule_chembl_id", "UNKNOWN"),
                    "name": act.get("molecule_pref_name") or act.get("molecule_chembl_id", "Unknown"),
                    "drug_type": "Small molecule",
                    "mechanism_of_action": f"Activity type: {act.get('standard_type')} = {act.get('standard_value')} {act.get('standard_units')}",
                    "phase": act.get("src_description", "Research"),
                    "target": "CD46",
                    "indication": "Cancer research",
                    "notes": f"ChEMBL assay: {act.get('assay_description', 'N/A')[:120]}",
                }
            )
        except Exception:
            continue

    logger.info("Parsed %d activity records from ChEMBL JSON", len(records))
    return records


def build_drug_nodes(driver: Driver, raw_dir: Path) -> dict:
    """Merge Drug nodes from curated list + ChEMBL JSON."""
    chembl_path = raw_dir / "apis" / "chembl_cd46.json"
    chembl_records = _parse_chembl_json(chembl_path)

    # Deduplicate by chembl_id — curated takes precedence
    curated_ids = {d["chembl_id"] for d in CURATED_DRUGS}
    extra_from_api = [r for r in chembl_records if r["chembl_id"] not in curated_ids]

    all_drugs = CURATED_DRUGS + extra_from_api[:20]  # cap API drugs at 20 extra

    merged = 0
    with driver.session() as session:
        for drug in all_drugs:
            session.run(
                """
                MERGE (dr:Drug {chembl_id: $chembl_id})
                SET dr.name                  = $name,
                    dr.drug_type             = $drug_type,
                    dr.mechanism_of_action   = $mechanism_of_action,
                    dr.phase                 = $phase,
                    dr.target                = $target,
                    dr.indication            = $indication,
                    dr.notes                 = $notes,
                    dr.updated_at            = datetime()
                WITH dr
                MATCH (p:Protein {uniprot_id: 'P15529'})
                MERGE (dr)-[:TARGETS]->(p)
                """,
                **drug,
            )
            merged += 1

    logger.info("Merged %d Drug nodes", merged)
    return {"drugs_merged": merged}
