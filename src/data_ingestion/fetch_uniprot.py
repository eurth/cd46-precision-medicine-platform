"""
Fetch CD46 protein annotation from UniProt REST API.
Returns protein properties, isoforms, function, and post-translational modifications.
"""

import json
import logging
from pathlib import Path

import requests
import yaml

log = logging.getLogger(__name__)

_CONFIG_PATH = Path(__file__).parents[2] / "config" / "datasets.yaml"
with open(_CONFIG_PATH) as f:
    _DS = yaml.safe_load(f)["uniprot"]

BASE_URL = _DS["base_url"]
ACCESSION = _DS["accession"]
OUTPUT_RAW = Path(_DS["output"]["raw"])


def fetch_cd46_uniprot() -> dict:
    """Fetch CD46 (P15529) annotation from UniProt REST API."""
    OUTPUT_RAW.parent.mkdir(parents=True, exist_ok=True)

    if OUTPUT_RAW.exists():
        log.info("Loading cached UniProt data from %s", OUTPUT_RAW)
        with open(OUTPUT_RAW) as f:
            return json.load(f)

    url = f"{BASE_URL}/{ACCESSION}.json"
    log.info("Fetching CD46 from UniProt: %s", url)
    r = requests.get(url, timeout=30, headers={"Accept": "application/json"})
    r.raise_for_status()
    data = r.json()

    with open(OUTPUT_RAW, "w") as f:
        json.dump(data, f, indent=2)

    log.info("Saved UniProt data for CD46 (P15529)")
    return data


def extract_key_fields(data: dict) -> dict:
    """Pull out the fields relevant for KG node creation."""
    genes = data.get("genes", [{}])
    gene_name = genes[0].get("geneName", {}).get("value", "CD46") if genes else "CD46"

    functions = data.get("comments", [])
    func_text = next((c.get("texts", [{}])[0].get("value", "") for c in functions
                      if c.get("commentType") == "FUNCTION"), "")

    keywords = [kw.get("name", "") for kw in data.get("keywords", [])]

    return {
        "uniprot_id": data.get("primaryAccession", "P15529"),
        "gene_symbol": gene_name,
        "protein_name": data.get("uniProtkbId", "CD46_HUMAN"),
        "function": func_text[:500],
        "molecular_weight": data.get("sequence", {}).get("molWeight", None),
        "length": data.get("sequence", {}).get("length", None),
        "keywords": keywords,
    }


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    raw = fetch_cd46_uniprot()
    fields = extract_key_fields(raw)
    for k, v in fields.items():
        print(f"  {k}: {v}")
