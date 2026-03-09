"""Fetch full mCRPC patient cohorts from cBioPortal REST API and load into AuraDB.

Studies fetched:
  - prad_su2c_2019 : SU2C/PCF Dream Team mCRPC, PNAS 2019 (Abida et al.) — 429 patients
  - prad_su2c_2015 : SU2C/PCF Dream Team mCRPC, Cell 2015 (Robinson et al.) — 150 patients

Loads:
  - PatientGroup nodes (MERGE on patient_id — safe to re-run)
  - HAS_PATIENT_GROUP relationship to prostate cancer Disease node

Run:
    python scripts/load_kg_cbioportal_full.py

Then verify:
    python scripts/audit_kg.py
"""

import os
import sys
import time
import json
import urllib.request
import urllib.error
from pathlib import Path

from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parents[1] / ".env")

from neo4j import GraphDatabase

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

STUDIES = [
    {"study_id": "prad_su2c_2019", "cohort_label": "SU2C mCRPC 2019"},
    {"study_id": "prad_su2c_2015", "cohort_label": "SU2C mCRPC 2015"},
]

CBIOPORTAL_BASE = "https://www.cbioportal.org/api"
PAGE_SIZE = 500
REQUEST_DELAY = 0.5  # seconds between API calls (be polite)


# ---------------------------------------------------------------------------
# Neo4j driver
# ---------------------------------------------------------------------------

def get_driver():
    uri = os.getenv("NEO4J_URI")
    user = os.getenv("NEO4J_USERNAME", "neo4j")
    password = os.getenv("NEO4J_PASSWORD")
    if not uri or not password:
        raise RuntimeError("NEO4J_URI and NEO4J_PASSWORD must be set in .env")
    driver = GraphDatabase.driver(uri, auth=(user, password))
    driver.verify_connectivity()
    return driver


# ---------------------------------------------------------------------------
# cBioPortal API helpers
# ---------------------------------------------------------------------------

def api_get(path: str, params: dict = None) -> list | dict:
    """GET from cBioPortal API, return parsed JSON."""
    url = f"{CBIOPORTAL_BASE}{path}"
    if params:
        query = "&".join(f"{k}={v}" for k, v in params.items())
        url = f"{url}?{query}"
    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.loads(r.read())
        except urllib.error.HTTPError as e:
            if e.code == 404:
                print(f"  [WARN] 404 Not Found: {url}")
                return []
            if attempt < 2:
                print(f"  [WARN] HTTP {e.code}, retrying ({attempt+1}/3)…")
                time.sleep(2)
            else:
                raise
        except Exception as e:
            if attempt < 2:
                print(f"  [WARN] {e}, retrying ({attempt+1}/3)…")
                time.sleep(2)
            else:
                raise
    return []


def fetch_all_clinical_data(study_id: str) -> dict:
    """Fetch all patient-level clinical attributes, return dict keyed by patientId."""
    patients: dict[str, dict] = {}
    page = 0
    total_rows = 0
    while True:
        rows = api_get(
            f"/studies/{study_id}/clinical-data",
            {"clinicalDataType": "PATIENT", "pageSize": PAGE_SIZE, "pageNumber": page},
        )
        if not rows:
            break
        for row in rows:
            pid = row.get("patientId", "")
            if not pid:
                continue
            if pid not in patients:
                patients[pid] = {"patient_id": pid, "study_id": study_id}
            attr = row.get("clinicalAttributeId", "").lower()
            value = row.get("value")
            if attr and value is not None:
                patients[pid][attr] = value
        total_rows += len(rows)
        print(f"    Fetched page {page}: {len(rows)} rows ({total_rows} total rows so far)")
        if len(rows) < PAGE_SIZE:
            break
        page += 1
        time.sleep(REQUEST_DELAY)
    return patients


# ---------------------------------------------------------------------------
# AuraDB load helpers
# ---------------------------------------------------------------------------

PATIENT_CYPHER = """
    MERGE (pg:PatientGroup {patient_id: $patient_id})
    ON CREATE SET
        pg.study_id    = $study_id,
        pg.cohort      = $cohort,
        pg.cancer_type = 'Prostate Cancer',
        pg.expression_group = 'mCRPC',
        pg.source      = 'cBioPortal'
    SET
        pg.age_at_diagnosis = CASE WHEN $age IS NOT NULL THEN $age ELSE pg.age_at_diagnosis END,
        pg.os_months        = CASE WHEN $os_months IS NOT NULL THEN $os_months ELSE pg.os_months END,
        pg.os_status        = CASE WHEN $os_status <> '' THEN $os_status ELSE pg.os_status END,
        pg.psa              = CASE WHEN $psa IS NOT NULL THEN $psa ELSE pg.psa END,
        pg.chemo_regimen    = CASE WHEN $chemo IS NOT NULL THEN $chemo ELSE pg.chemo_regimen END,
        pg.race             = CASE WHEN $race IS NOT NULL THEN $race ELSE pg.race END
    RETURN pg.patient_id AS id
"""

LINK_DISEASE_CYPHER = """
    MATCH (pg:PatientGroup {patient_id: $patient_id})
    MATCH (d:Disease)
    WHERE d.name CONTAINS 'prostate' OR d.tcga_code = 'PRAD'
    WITH pg, d LIMIT 1
    MERGE (d)-[r:HAS_PATIENT_GROUP]->(pg)
    ON CREATE SET r.source = 'cBioPortal'
"""


def safe_float(val) -> float | None:
    try:
        f = float(val)
        return f if f != 0.0 else None
    except (TypeError, ValueError):
        return None


def load_patients(driver, patients: dict, cohort_label: str) -> int:
    """MERGE PatientGroup nodes into AuraDB. Returns count of processed patients."""
    loaded = 0
    failed = 0
    with driver.session() as session:
        for pid, attrs in patients.items():
            try:
                session.run(
                    PATIENT_CYPHER,
                    patient_id=f"{attrs['study_id']}_{pid}",
                    study_id=attrs["study_id"],
                    cohort=cohort_label,
                    age=safe_float(attrs.get("age_at_diagnosis")),
                    os_months=safe_float(attrs.get("os_months")),
                    os_status=str(attrs.get("os_status", "")),
                    psa=safe_float(attrs.get("psa")),
                    chemo=attrs.get("chemo_regimen_category"),
                    race=attrs.get("race"),
                )
                session.run(
                    LINK_DISEASE_CYPHER,
                    patient_id=f"{attrs['study_id']}_{pid}",
                )
                loaded += 1
            except Exception as e:
                failed += 1
                if failed <= 5:
                    print(f"  [ERROR] Patient {pid}: {e}")
    return loaded


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print("=" * 60)
    print("cBioPortal Full mCRPC Load — AuraDB")
    print("=" * 60)

    driver = get_driver()
    print("Connected to AuraDB.\n")

    total_loaded = 0
    for study in STUDIES:
        study_id = study["study_id"]
        cohort_label = study["cohort_label"]
        print(f"\n{'─'*50}")
        print(f"Study: {study_id}  ({cohort_label})")
        print(f"{'─'*50}")

        print("  Fetching clinical data from cBioPortal API…")
        patients = fetch_all_clinical_data(study_id)
        print(f"  Found {len(patients)} unique patients")

        if not patients:
            print("  No patients found — skipping.")
            continue

        # Sample first patient attrs
        first = next(iter(patients.values()))
        print(f"  Sample attributes for first patient: {list(first.keys())}")

        print(f"  Loading {len(patients)} patients into AuraDB…")
        n = load_patients(driver, patients, cohort_label)
        print(f"  ✓ Loaded {n} patients")
        total_loaded += n

    driver.close()

    print(f"\n{'='*60}")
    print(f"DONE — Total patients processed: {total_loaded}")
    print("Run  python scripts/audit_kg.py  to verify node counts.")
    print("=" * 60)


if __name__ == "__main__":
    main()
