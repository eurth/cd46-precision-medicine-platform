"""
Fetch mCRPC patient data from cBioPortal public REST API.
Uses SU2C mCRPC (su2c_mcrpc_2019) and MSK-IMPACT mCRPC (prad_msk_2019) studies.
No dbGaP access required — these are publicly available cohorts.
"""

import json
import logging
from pathlib import Path
from typing import Optional

import requests
import yaml

log = logging.getLogger(__name__)

_CONFIG_PATH = Path(__file__).parents[2] / "config" / "datasets.yaml"
with open(_CONFIG_PATH) as f:
    _DS = yaml.safe_load(f)["cbioportal"]

BASE_URL = _DS["base_url"]
STUDIES = _DS["studies"]
OUTPUT_RAW = Path(_DS["output"]["raw"])

HEADERS = {"Accept": "application/json", "Content-Type": "application/json"}


def get_study_info(study_id: str) -> Optional[dict]:
    """Fetch metadata for a cBioPortal study."""
    try:
        r = requests.get(f"{BASE_URL}/studies/{study_id}", headers=HEADERS, timeout=20)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        log.warning("Could not fetch study %s: %s", study_id, e)
        return None


def get_sample_ids(study_id: str) -> list[str]:
    """Get all sample IDs for a study."""
    try:
        r = requests.get(f"{BASE_URL}/studies/{study_id}/samples",
                         params={"projection": "ID"}, headers=HEADERS, timeout=30)
        r.raise_for_status()
        return [s["sampleId"] for s in r.json()]
    except Exception as e:
        log.warning("Could not fetch samples for %s: %s", study_id, e)
        return []


def get_clinical_data(study_id: str) -> list[dict]:
    """Get patient-level clinical data for a study."""
    try:
        r = requests.get(f"{BASE_URL}/studies/{study_id}/clinical-data",
                         params={"clinicalDataType": "PATIENT", "projection": "DETAILED"},
                         headers=HEADERS, timeout=60)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        log.warning("Could not fetch clinical data for %s: %s", study_id, e)
        return []


def get_molecular_profile_data(study_id: str, gene_id: int = 4179) -> list[dict]:
    """Get CD46 expression data from a study's RNA-seq molecular profile."""
    # First, find the RNA-seq profile
    try:
        r = requests.get(f"{BASE_URL}/studies/{study_id}/molecular-profiles",
                         headers=HEADERS, timeout=20)
        r.raise_for_status()
        profiles = r.json()
        rna_profile = next(
            (p for p in profiles if "mrna" in p.get("molecularProfileId", "").lower()
             or "rna_seq" in p.get("molecularProfileId", "").lower()),
            None
        )
        if not rna_profile:
            log.warning("No RNA-seq profile found for %s", study_id)
            return []

        profile_id = rna_profile["molecularProfileId"]
        # Get sample IDs
        sample_list_r = requests.get(
            f"{BASE_URL}/molecular-profiles/{profile_id}/molecular-data",
            params={"entrezGeneId": gene_id},
            headers=HEADERS, timeout=60
        )
        sample_list_r.raise_for_status()
        return sample_list_r.json()
    except Exception as e:
        log.warning("Could not fetch molecular data for %s: %s", study_id, e)
        return []


def fetch_mcrpc_data(force: bool = False) -> dict:
    """Fetch mCRPC data from cBioPortal for SU2C + MSK studies."""
    OUTPUT_RAW.parent.mkdir(parents=True, exist_ok=True)

    if OUTPUT_RAW.exists() and not force:
        log.info("Loading cached cBioPortal data from %s", OUTPUT_RAW)
        with open(OUTPUT_RAW) as f:
            return json.load(f)

    results = {}
    for key, study_id in STUDIES.items():
        log.info("Fetching cBioPortal study: %s (%s)", key, study_id)
        study_meta = get_study_info(study_id)
        samples = get_sample_ids(study_id)
        clinical = get_clinical_data(study_id)
        expression = get_molecular_profile_data(study_id)

        results[key] = {
            "study_id": study_id,
            "meta": study_meta,
            "n_samples": len(samples),
            "clinical_data": clinical[:100],  # cap for storage sanity
            "cd46_expression": expression[:100],
        }
        log.info("  %s: %d samples", study_id, len(samples))

    with open(OUTPUT_RAW, "w") as f:
        json.dump(results, f, indent=2)

    total_patients = sum(v["n_samples"] for v in results.values())
    log.info("Total mCRPC patients fetched: %d", total_patients)
    return results


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    data = fetch_mcrpc_data()
    for k, v in data.items():
        print(f"  {k}: {v['n_samples']} samples")
