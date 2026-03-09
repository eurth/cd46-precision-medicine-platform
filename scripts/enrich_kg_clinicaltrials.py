"""Enrich existing ClinicalTrial nodes in AuraDB with live data from ClinicalTrials.gov v2 API.

Fetches: enrollment count, actual start date, primary completion date,
         last update date, results URL, and current status.

Run:
    python scripts/enrich_kg_clinicaltrials.py

Then verify:
    python scripts/audit_kg.py
"""

import os
import time
import json
import urllib.request
import urllib.error
from pathlib import Path

from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parents[1] / ".env")

from neo4j import GraphDatabase

CTGOV_BASE = "https://clinicaltrials.gov/api/v2/studies"
REQUEST_DELAY = 0.8


def get_driver():
    uri = os.getenv("NEO4J_URI")
    user = os.getenv("NEO4J_USERNAME", "neo4j")
    password = os.getenv("NEO4J_PASSWORD")
    if not uri or not password:
        raise RuntimeError("NEO4J_URI and NEO4J_PASSWORD must be set in .env")
    driver = GraphDatabase.driver(uri, auth=(user, password))
    driver.verify_connectivity()
    return driver


def fetch_trial(nct_id: str) -> dict | None:
    url = f"{CTGOV_BASE}/{nct_id}?format=json"
    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=20) as r:
                return json.loads(r.read())
        except urllib.error.HTTPError as e:
            if e.code == 404:
                print(f"  [WARN] {nct_id} not found (404)")
                return None
            if attempt < 2:
                time.sleep(2)
            else:
                print(f"  [ERROR] {nct_id}: HTTP {e.code}")
                return None
        except Exception as e:
            if attempt < 2:
                time.sleep(2)
            else:
                print(f"  [ERROR] {nct_id}: {e}")
                return None


def parse_trial(data: dict) -> dict:
    proto = data.get("protocolSection", {})
    status_mod = proto.get("statusModule", {})
    design_mod = proto.get("designModule", {})
    id_mod = proto.get("identificationModule", {})

    def get_date(struct):
        return struct.get("date") if struct else None

    phases = design_mod.get("phases", [])
    enroll = design_mod.get("enrollmentInfo", {})

    return {
        "nct_id": id_mod.get("nctId"),
        "status": status_mod.get("overallStatus"),
        "phase": "/".join(phases) if phases else None,
        "enrollment_count": enroll.get("count"),
        "enrollment_type": enroll.get("type"),
        "start_date": get_date(status_mod.get("startDateStruct")),
        "primary_completion_date": get_date(status_mod.get("primaryCompletionDateStruct")),
        "last_update_date": get_date(status_mod.get("lastUpdatePostDateStruct")),
        "results_posted": get_date(status_mod.get("resultsFirstPostedDateStruct")),
    }


ENRICH_CYPHER = """
    MATCH (t:ClinicalTrial {nct_id: $nct_id})
    SET
        t.status                  = COALESCE($status, t.status),
        t.phase                   = COALESCE($phase, t.phase),
        t.enrollment_count        = COALESCE($enrollment_count, t.enrollment_count),
        t.enrollment_type         = COALESCE($enrollment_type, t.enrollment_type),
        t.start_date              = COALESCE($start_date, t.start_date),
        t.primary_completion_date = COALESCE($primary_completion_date, t.primary_completion_date),
        t.last_update_date        = COALESCE($last_update_date, t.last_update_date),
        t.results_posted          = COALESCE($results_posted, t.results_posted),
        t.enriched_at             = '2026-03-09',
        t.data_source             = 'ClinicalTrials.gov v2 API'
    RETURN t.nct_id AS id
"""


def main():
    driver = get_driver()
    print("Connected to AuraDB.\n")

    # Fetch all NCT IDs from KG
    with driver.session() as session:
        result = session.run("MATCH (t:ClinicalTrial) RETURN t.nct_id AS nct ORDER BY t.nct_id")
        nct_ids = [r["nct"] for r in result if r["nct"]]

    print(f"Found {len(nct_ids)} ClinicalTrial nodes in KG: {nct_ids}\n")

    enriched = 0
    skipped = 0

    for nct_id in nct_ids:
        print(f"  Fetching {nct_id}…", end=" ")
        raw = fetch_trial(nct_id)
        if not raw:
            skipped += 1
            continue

        parsed = parse_trial(raw)
        print(f"status={parsed['status']} phase={parsed['phase']} enrollment={parsed['enrollment_count']}")

        with driver.session() as session:
            session.run(ENRICH_CYPHER, **parsed)

        enriched += 1
        time.sleep(REQUEST_DELAY)

    driver.close()
    print(f"\nDone — enriched {enriched} trials, skipped {skipped}.")


if __name__ == "__main__":
    main()
