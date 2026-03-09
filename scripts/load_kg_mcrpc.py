"""Load MSK-IMPACT and SU2C mCRPC patient cohorts from cbioportal_mcrpc.json.

Input:  data/raw/apis/cbioportal_mcrpc.json
Loads:
  - SU2C mCRPC: 16 unique patients (prad_su2c_2019 study)
  - MSK mCRPC: 10 unique patients (prad_msk_2019 study)
  - Patient attributes: age_at_diagnosis, os_months, os_status, psa
  - Links patients to prostate cancer Disease node
Expected gain: ~+26 PatientGroup nodes, +26 TREATED_IN / linked rels

Note: cbioportal_mcrpc.json appears to have a sampled subset of the full cohort.
The full MSK-IMPACT mCRPC cohort has 1,033 patients; this file has 26 unique.
For full cohort: use cBioPortal API directly (see load_kg_pubmed.py for API pattern).

Run:
    python scripts/load_kg_mcrpc.py
Then verify:
    python scripts/audit_kg.py
"""
import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

from neo4j import GraphDatabase


def get_driver():
    uri = os.getenv("NEO4J_URI")
    user = os.getenv("NEO4J_USERNAME", "neo4j")
    password = os.getenv("NEO4J_PASSWORD")
    if not uri or not password:
        raise RuntimeError("NEO4J_URI and NEO4J_PASSWORD must be set in .env")
    driver = GraphDatabase.driver(uri, auth=(user, password))
    driver.verify_connectivity()
    return driver


def pivot_patient_data(clinical_rows: list) -> dict:
    """Convert long-format clinical rows (one per attribute) to wide dict per patient."""
    patients = {}
    for row in clinical_rows:
        pid = row.get("patientId", "")
        if not pid:
            continue
        if pid not in patients:
            patients[pid] = {"patient_id": pid}
        attr_id = row.get("clinicalAttributeId", "")
        value = row.get("value")
        if attr_id and value is not None:
            patients[pid][attr_id.lower()] = value
    return patients


def load_mcrpc_cohort(driver, data_path: Path):
    """Load mCRPC patient cohort nodes into AuraDB."""
    with open(data_path, encoding="utf-8") as f:
        raw = json.load(f)

    patient_cypher = """
        MERGE (pg:PatientGroup {patient_id: $patient_id})
        ON CREATE SET
            pg.study_id = $study_id,
            pg.cancer_type = 'Prostate Cancer',
            pg.expression_group = 'mCRPC',
            pg.age_at_diagnosis = $age,
            pg.os_months = $os_months,
            pg.os_status = $os_status,
            pg.psa = $psa,
            pg.cohort = $cohort,
            pg.threshold_method = 'mCRPC_cohort',
            pg.source = 'cBioPortal'
        ON MATCH SET
            pg.study_id = $study_id
        RETURN pg.patient_id AS id
    """

    link_disease_cypher = """
        MATCH (pg:PatientGroup {patient_id: $patient_id})
        MATCH (d:Disease)
        WHERE d.name CONTAINS 'prostate' OR d.tcga_code = 'PRAD'
        WITH pg, d LIMIT 1
        MERGE (d)-[r:HAS_PATIENT_GROUP]->(pg)
        ON CREATE SET r.source = 'cBioPortal'
        RETURN type(r)
    """

    total_loaded = 0

    with driver.session() as session:
        for cohort_key, cohort_data in raw.items():
            study_id = cohort_data.get("study_id", cohort_key)
            clinical_rows = cohort_data.get("clinical_data", [])
            patients = pivot_patient_data(clinical_rows)

            cohort_label = "SU2C mCRPC" if "su2c" in study_id else "MSK-IMPACT mCRPC"
            print(f"\n{cohort_label} cohort ({study_id}): {len(patients)} unique patients")

            for pid, attrs in patients.items():
                try:
                    age = float(attrs.get("age_at_diagnosis", 0)) or None
                except (ValueError, TypeError):
                    age = None

                try:
                    os_months = float(attrs.get("os_months", 0)) or None
                except (ValueError, TypeError):
                    os_months = None

                try:
                    psa = float(attrs.get("psa", 0)) or None
                except (ValueError, TypeError):
                    psa = None

                os_status = str(attrs.get("os_status", ""))

                session.run(
                    patient_cypher,
                    patient_id=f"{study_id}_{pid}",
                    study_id=study_id,
                    age=age,
                    os_months=os_months,
                    os_status=os_status,
                    psa=psa,
                    cohort=cohort_label,
                )
                session.run(link_disease_cypher, patient_id=f"{study_id}_{pid}")
                total_loaded += 1

            print(f"  ✅ {len(patients)} {cohort_label} patient nodes upserted.")

    print(f"\n✅ Total mCRPC patients loaded: {total_loaded}")
    print("Run scripts/audit_kg.py to confirm AuraDB counts.")
    return total_loaded


def main():
    data_path = Path(__file__).resolve().parents[1] / "data" / "raw" / "apis" / "cbioportal_mcrpc.json"
    if not data_path.exists():
        print(f"ERROR: {data_path} not found")
        sys.exit(1)

    driver = get_driver()
    try:
        load_mcrpc_cohort(driver, data_path)
    finally:
        driver.close()


if __name__ == "__main__":
    main()
