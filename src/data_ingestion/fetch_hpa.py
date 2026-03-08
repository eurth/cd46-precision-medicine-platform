"""
Fetch CD46 protein expression data from Human Protein Atlas (HPA) REST API.
Returns per-tissue protein levels: H-score, staining intensity, fraction positive.
"""

import json
import logging
from pathlib import Path

import requests
import yaml

log = logging.getLogger(__name__)

_CONFIG_PATH = Path(__file__).parents[2] / "config" / "datasets.yaml"
with open(_CONFIG_PATH) as f:
    _DS = yaml.safe_load(f)["hpa"]

HPA_URL = _DS["endpoints"]["gene"]
OUTPUT_RAW = Path(_DS["output"]["raw"])


def fetch_hpa_cd46() -> dict:
    """Fetch CD46 protein data from HPA API. Returns raw JSON."""
    OUTPUT_RAW.parent.mkdir(parents=True, exist_ok=True)

    if OUTPUT_RAW.exists():
        log.info("Loading cached HPA data from %s", OUTPUT_RAW)
        with open(OUTPUT_RAW) as f:
            return json.load(f)

    # HPA v24: direct gene page JSON endpoint
    url = "https://www.proteinatlas.org/ENSG00000117335.json"
    log.info("Fetching CD46 protein expression from HPA: %s", url)
    r = requests.get(url, timeout=30, headers={"Accept": "application/json"})
    r.raise_for_status()
    data = r.json()

    with open(OUTPUT_RAW, "w") as f:
        json.dump(data, f, indent=2)

    log.info("Saved HPA data to %s", OUTPUT_RAW)
    return data


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    data = fetch_hpa_cd46()
    print(f"HPA response keys: {list(data.keys()) if isinstance(data, dict) else type(data)}")
