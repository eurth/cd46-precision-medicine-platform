"""Build PatientGroup nodes from 225Ac eligibility analysis output."""
from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd

from neo4j import Driver

logger = logging.getLogger(__name__)

# Threshold definitions mirroring ac225_analysis.py
THRESHOLDS = {
    "median": "Median CD46 expression (50th percentile split)",
    "75th_pct": "75th percentile — captures clearly high-expressing tumors",
    "log2_2.5": "log2(TPM+1) ≥ 2.5 absolute cutoff — biologically validated",
    "log2_3.0": "log2(TPM+1) ≥ 3.0 absolute cutoff — conservative / high-confidence",
}


def build_patient_group_nodes(driver: Driver, processed_dir: Path) -> dict:
    """Merge PatientGroup nodes from patient_groups.csv."""
    patient_file = processed_dir / "patient_groups.csv"

    if not patient_file.exists():
        logger.warning(
            "patient_groups.csv not found at %s — skipping PatientGroup nodes", patient_file
        )
        return {"patient_groups_merged": 0}

    df = pd.read_csv(patient_file)
    required_cols = {"cancer_type", "threshold", "n_eligible", "n_total", "fraction_eligible"}
    missing = required_cols - set(df.columns)
    if missing:
        logger.error("patient_groups.csv missing columns: %s", missing)
        return {"patient_groups_merged": 0}

    merged = 0
    with driver.session() as session:
        for _, row in df.iterrows():
            cancer_type = row["cancer_type"]
            threshold = row["threshold"]
            pg_id = f"{cancer_type}_{threshold}"

            params = {
                "group_id": pg_id,
                "cancer_type": cancer_type,
                "threshold_type": threshold,
                "threshold_description": THRESHOLDS.get(threshold, threshold),
                "n_eligible": int(row["n_eligible"]),
                "n_total": int(row["n_total"]),
                "fraction_eligible": float(row["fraction_eligible"]),
                "pct_eligible": round(float(row["fraction_eligible"]) * 100, 1),
                "threshold_value": float(row["threshold_value"]) if "threshold_value" in row else None,
                "mean_expression_eligible": float(row["mean_expression_eligible"]) if "mean_expression_eligible" in row else None,
            }

            session.run(
                """
                MERGE (pg:PatientGroup {group_id: $group_id})
                SET pg.cancer_type               = $cancer_type,
                    pg.threshold_type            = $threshold_type,
                    pg.threshold_description     = $threshold_description,
                    pg.n_eligible                = $n_eligible,
                    pg.n_total                   = $n_total,
                    pg.fraction_eligible         = $fraction_eligible,
                    pg.pct_eligible              = $pct_eligible,
                    pg.threshold_value           = $threshold_value,
                    pg.mean_expression_eligible  = $mean_expression_eligible,
                    pg.updated_at                = datetime()
                WITH pg
                MATCH (d:Disease {tcga_code: $cancer_type})
                MERGE (d)-[:HAS_PATIENT_GROUP]->(pg)
                """,
                **params,
            )
            merged += 1

    logger.info("Merged %d PatientGroup nodes from %s", merged, patient_file)
    return {"patient_groups_merged": merged}
