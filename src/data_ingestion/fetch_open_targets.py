"""
Fetch CD46 target-disease associations and known drugs from Open Targets GraphQL API.
Returns disease association scores, known drugs, and clinical trial data.
"""

import json
import logging
from pathlib import Path

import requests
import yaml

log = logging.getLogger(__name__)

_CONFIG_PATH = Path(__file__).parents[2] / "config" / "datasets.yaml"
with open(_CONFIG_PATH) as f:
    _DS = yaml.safe_load(f)["open_targets"]

OT_ENDPOINT = _DS["endpoint"]
TARGET_ID = _DS["target_id"]
OUTPUT_RAW = Path(_DS["output"]["raw"])

QUERY = """
query CD46Target($ensemblId: String!) {
  target(ensemblId: $ensemblId) {
    id
    approvedSymbol
    biotype
    associatedDiseases(page: {index: 0, size: 25}) {
      count
      rows {
        disease {
          id
          name
          therapeuticAreas { id name }
        }
        score
        datasourceScores { id score }
      }
    }
    knownDrugs(size: 20) {
      count
      rows {
        drug {
          id
          name
          maximumClinicalTrialPhase
        }
        disease { name }
        phase
        status
      }
    }
  }
}
"""


def fetch_open_targets() -> dict:
    """Fetch CD46 data from Open Targets GraphQL API."""
    OUTPUT_RAW.parent.mkdir(parents=True, exist_ok=True)

    if OUTPUT_RAW.exists():
        log.info("Loading cached Open Targets data from %s", OUTPUT_RAW)
        with open(OUTPUT_RAW) as f:
            return json.load(f)

    log.info("Querying Open Targets GraphQL for ENSG00000117335")
    payload = {"query": QUERY, "variables": {"ensemblId": TARGET_ID}}
    r = requests.post(OT_ENDPOINT, json=payload, timeout=60,
                      headers={"Content-Type": "application/json"})
    r.raise_for_status()
    data = r.json()

    if "errors" in data:
        log.warning("Open Targets returned errors: %s", data["errors"])

    with open(OUTPUT_RAW, "w") as f:
        json.dump(data, f, indent=2)

    return data


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    data = fetch_open_targets()
    target = data.get("data", {}).get("target", {})
    if target:
        diseases = target.get("associatedDiseases", {}).get("count", 0)
        drugs = target.get("knownDrugs", {}).get("count", 0)
        print(f"Open Targets: {diseases} associated diseases, {drugs} known drugs")
