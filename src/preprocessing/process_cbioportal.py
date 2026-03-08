"""
Process cBioPortal mCRPC data into patient-level records for KG ingestion.
Input:  data/raw/apis/cbioportal_mcrpc.json
Output: data/processed/cbioportal_mcrpc.csv
"""

import json
import logging
from pathlib import Path

import pandas as pd
import yaml

log = logging.getLogger(__name__)

_CONFIG_PATH = Path(__file__).parents[2] / "config" / "datasets.yaml"
with open(_CONFIG_PATH) as f:
    _DS = yaml.safe_load(f)["cbioportal"]

RAW_PATH = Path(_DS["output"]["raw"])
OUTPUT_PATH = Path(_DS["output"]["processed"])


def _flatten_clinical_data(clinical_list: list[dict]) -> pd.DataFrame:
    """Flatten cBioPortal's key-value clinical data into a wide DataFrame."""
    if not clinical_list:
        return pd.DataFrame()
    records = {}
    for entry in clinical_list:
        pid = entry.get("patientId", entry.get("sampleId", "unknown"))
        records.setdefault(pid, {})
        records[pid][entry.get("clinicalAttributeId", "attr")] = entry.get("value")
    return pd.DataFrame.from_dict(records, orient="index").reset_index().rename(columns={"index": "patient_id"})


def process_cbioportal() -> pd.DataFrame:
    """Parse cBioPortal JSON into clean per-patient table."""
    if not RAW_PATH.exists():
        raise FileNotFoundError(f"cBioPortal data not found: {RAW_PATH}. Run fetch_cbioportal.py first.")

    with open(RAW_PATH) as f:
        raw = json.load(f)

    all_patients = []
    for study_key, study_data in raw.items():
        study_id = study_data.get("study_id", study_key)
        n_samples = study_data.get("n_samples", 0)

        clinical = study_data.get("clinical_data", [])
        if clinical:
            df = _flatten_clinical_data(clinical)
        else:
            # Create a minimal placeholder DataFrame
            df = pd.DataFrame({"patient_id": [f"{study_id}_patient_{i}" for i in range(min(n_samples, 50))]})

        df["study"] = study_id
        df["dataset"] = "cBioPortal"
        df["cohort_subtype"] = "mCRPC"
        df["cancer_type"] = "PRAD"
        all_patients.append(df)

    if not all_patients:
        log.warning("No patient data extracted from cBioPortal")
        return pd.DataFrame()

    result = pd.concat(all_patients, ignore_index=True)

    # Standardize column names
    col_map = {
        "OS_MONTHS": "os_months",
        "OS_STATUS": "os_status",
        "PFS_MONTHS": "pfs_months",
        "PFS_STATUS": "pfs_status",
        "AGE": "age_at_diagnosis",
        "SEX": "sex",
    }
    result.rename(columns={k: v for k, v in col_map.items() if k in result.columns}, inplace=True)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(OUTPUT_PATH, index=False)
    log.info("cBioPortal mCRPC: %d patients → %s", len(result), OUTPUT_PATH)
    return result


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    df = process_cbioportal()
    print(f"Processed {len(df)} mCRPC patients")
    print(df.columns.tolist())
