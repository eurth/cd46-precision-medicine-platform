"""
Fetch CD46-related clinical trials from ClinicalTrials.gov API v2.
Returns active + recruiting trials, study details, phases, sponsors.
"""

import json
import logging
from pathlib import Path

import requests
import yaml

log = logging.getLogger(__name__)

_CONFIG_PATH = Path(__file__).parents[2] / "config" / "datasets.yaml"
with open(_CONFIG_PATH) as f:
    _DS = yaml.safe_load(f)["clinicaltrials"]

BASE_URL = _DS["base_url"]
OUTPUT_RAW = Path(_DS["output"]["raw"])


def fetch_cd46_trials(query: str = "CD46 cancer", page_size: int = 100) -> list[dict]:
    """Fetch all CD46 clinical trials from ClinicalTrials.gov v2 API."""
    OUTPUT_RAW.parent.mkdir(parents=True, exist_ok=True)

    if OUTPUT_RAW.exists():
        log.info("Loading cached trials from %s", OUTPUT_RAW)
        with open(OUTPUT_RAW) as f:
            return json.load(f)

    params = {
        "query.term": query,
        "pageSize": page_size,
        "format": "json",
    }

    log.info("Fetching CD46 trials from ClinicalTrials.gov v2")
    r = requests.get(BASE_URL, params=params, timeout=30)
    r.raise_for_status()
    data = r.json()

    studies = data.get("studies", [])
    log.info("Retrieved %d trials", len(studies))

    with open(OUTPUT_RAW, "w") as f:
        json.dump(studies, f, indent=2)

    return studies


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    trials = fetch_cd46_trials()
    print(f"Found {len(trials)} trials")
    for t in trials[:3]:
        proto = t.get("protocolSection", {})
        print(f"  {proto.get('identificationModule', {}).get('nctId')} — {proto.get('identificationModule', {}).get('briefTitle', '')[:60]}")
