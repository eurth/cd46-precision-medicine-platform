"""
Fetch CD46-related compounds from ChEMBL REST API.
Returns drug targets, mechanisms, and bioactivities for CD46.
"""

import json
import logging
from pathlib import Path

import requests
import yaml

log = logging.getLogger(__name__)

_CONFIG_PATH = Path(__file__).parents[2] / "config" / "datasets.yaml"
with open(_CONFIG_PATH) as f:
    _DS = yaml.safe_load(f)["chembl"]

BASE_URL = _DS["base_url"]
TARGET_ID = _DS["target_id"]
OUTPUT_RAW = Path(_DS["output"]["raw"])


def search_cd46_target() -> list[dict]:
    """Search ChEMBL for CD46 target entries."""
    url = f"{BASE_URL}/target/search"
    params = {"q": "CD46", "format": "json"}
    r = requests.get(url, params=params, timeout=30)
    r.raise_for_status()
    return r.json().get("targets", {}).get("target", [])


def fetch_cd46_drugs() -> dict:
    """Fetch CD46 target info and known drugs from ChEMBL."""
    OUTPUT_RAW.parent.mkdir(parents=True, exist_ok=True)

    if OUTPUT_RAW.exists():
        log.info("Loading cached ChEMBL data from %s", OUTPUT_RAW)
        with open(OUTPUT_RAW) as f:
            return json.load(f)

    log.info("Fetching CD46 data from ChEMBL REST API")
    results = {"targets": [], "activities": []}

    # Search for CD46 target
    try:
        targets = search_cd46_target()
        results["targets"] = targets
        log.info("Found %d ChEMBL targets for CD46", len(targets))
    except Exception as e:
        log.warning("ChEMBL target search failed: %s", e)

    # Fetch bioactivities for CHEMBL2176 (CD46)
    try:
        act_url = f"{BASE_URL}/activity"
        params = {"target_chembl_id": TARGET_ID, "limit": 100, "format": "json"}
        r = requests.get(act_url, params=params, timeout=30)
        r.raise_for_status()
        results["activities"] = r.json().get("activities", [])
        log.info("Found %d ChEMBL bioactivities", len(results["activities"]))
    except Exception as e:
        log.warning("ChEMBL activity fetch failed: %s", e)

    with open(OUTPUT_RAW, "w") as f:
        json.dump(results, f, indent=2)

    return results


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    data = fetch_cd46_drugs()
    print(f"ChEMBL targets: {len(data['targets'])}, activities: {len(data['activities'])}")
