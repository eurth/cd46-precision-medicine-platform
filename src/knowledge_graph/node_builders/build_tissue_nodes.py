"""Build Tissue nodes from HPA protein expression data."""
from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd

from neo4j import Driver

logger = logging.getLogger(__name__)

# Curated tissue metadata with tissue type classification
TISSUE_CLASSIFICATION = {
    "Prostate": {"tissue_type": "Glandular", "normal_cd46_level": "Medium", "is_cancer_relevant": True},
    "Kidney": {"tissue_type": "Glandular", "normal_cd46_level": "High", "is_cancer_relevant": True},
    "Liver": {"tissue_type": "Glandular", "normal_cd46_level": "Medium", "is_cancer_relevant": True},
    "Lung": {"tissue_type": "Respiratory", "normal_cd46_level": "Low", "is_cancer_relevant": True},
    "Breast": {"tissue_type": "Glandular", "normal_cd46_level": "Low", "is_cancer_relevant": True},
    "Ovary": {"tissue_type": "Reproductive", "normal_cd46_level": "Medium", "is_cancer_relevant": True},
    "Bladder": {"tissue_type": "Epithelial", "normal_cd46_level": "Low", "is_cancer_relevant": True},
    "Colon": {"tissue_type": "Epithelial", "normal_cd46_level": "Low", "is_cancer_relevant": True},
    "Rectum": {"tissue_type": "Epithelial", "normal_cd46_level": "Low", "is_cancer_relevant": True},
    "Stomach": {"tissue_type": "Epithelial", "normal_cd46_level": "Low", "is_cancer_relevant": True},
    "Uterus": {"tissue_type": "Reproductive", "normal_cd46_level": "Medium", "is_cancer_relevant": True},
    "Cervix": {"tissue_type": "Reproductive", "normal_cd46_level": "Medium", "is_cancer_relevant": True},
    "Thyroid": {"tissue_type": "Glandular", "normal_cd46_level": "Low", "is_cancer_relevant": False},
    "Brain": {"tissue_type": "Neural", "normal_cd46_level": "Low", "is_cancer_relevant": False},
    "Skin": {"tissue_type": "Integumentary", "normal_cd46_level": "Medium", "is_cancer_relevant": True},
    "Lymph node": {"tissue_type": "Lymphoid", "normal_cd46_level": "High", "is_cancer_relevant": True},
    "Bone marrow": {"tissue_type": "Hematopoietic", "normal_cd46_level": "High", "is_cancer_relevant": True},
    "Testis": {"tissue_type": "Reproductive", "normal_cd46_level": "High", "is_cancer_relevant": True},
    "Placenta": {"tissue_type": "Reproductive", "normal_cd46_level": "High", "is_cancer_relevant": False},
    "Adrenal gland": {"tissue_type": "Endocrine", "normal_cd46_level": "Medium", "is_cancer_relevant": True},
    "Pancreas": {"tissue_type": "Glandular", "normal_cd46_level": "Low", "is_cancer_relevant": True},
    "Small intestine": {"tissue_type": "Epithelial", "normal_cd46_level": "Medium", "is_cancer_relevant": False},
    "Gallbladder": {"tissue_type": "Epithelial", "normal_cd46_level": "Medium", "is_cancer_relevant": False},
    "Heart muscle": {"tissue_type": "Muscle", "normal_cd46_level": "Low", "is_cancer_relevant": False},
    "Skeletal muscle": {"tissue_type": "Muscle", "normal_cd46_level": "Low", "is_cancer_relevant": False},
    "Spleen": {"tissue_type": "Lymphoid", "normal_cd46_level": "High", "is_cancer_relevant": False},
    "Appendix": {"tissue_type": "Epithelial", "normal_cd46_level": "Low", "is_cancer_relevant": False},
    "Epididymis": {"tissue_type": "Reproductive", "normal_cd46_level": "Medium", "is_cancer_relevant": False},
    "Fallopian tube": {"tissue_type": "Reproductive", "normal_cd46_level": "Medium", "is_cancer_relevant": False},
    "Endometrium": {"tissue_type": "Reproductive", "normal_cd46_level": "Medium", "is_cancer_relevant": True},
}

LEVEL_SCORE = {"Not detected": 0, "Low": 1, "Medium": 2, "High": 3}


def build_tissue_nodes(driver: Driver, processed_dir: Path) -> dict:
    """Merge Tissue nodes from hpa_cd46_protein.csv + tissue classification."""
    hpa_file = processed_dir / "hpa_cd46_protein.csv"

    if hpa_file.exists():
        hpa_df = pd.read_csv(hpa_file)
        # Expected columns: tissue, tumor_level, normal_level, tissue_type (optional)
        hpa_map = hpa_df.set_index("tissue").to_dict("index") if "tissue" in hpa_df.columns else {}
    else:
        logger.warning("hpa_cd46_protein.csv not found — using classification defaults only")
        hpa_map = {}

    # Ensure every classified tissue exists in hpa_map (fallback to defaults)
    all_tissues = set(TISSUE_CLASSIFICATION.keys()) | set(hpa_map.keys())

    merged = 0
    with driver.session() as session:
        for tissue_name in all_tissues:
            hpa_row = hpa_map.get(tissue_name, {})
            meta = TISSUE_CLASSIFICATION.get(tissue_name, {})

            tumor_level = hpa_row.get("tumor_level", "Not detected")
            normal_level = hpa_row.get("normal_level") or meta.get("normal_cd46_level", "Not detected")

            params = {
                "tissue_name": tissue_name,
                "tissue_type": hpa_row.get("tissue_type") or meta.get("tissue_type", "Unknown"),
                "cd46_tumor_expression": tumor_level,
                "cd46_normal_expression": normal_level,
                "tumor_score": LEVEL_SCORE.get(tumor_level, 0),
                "normal_score": LEVEL_SCORE.get(normal_level, 0),
                "tumor_normal_ratio": (
                    round(LEVEL_SCORE.get(tumor_level, 0) / max(LEVEL_SCORE.get(normal_level, 1), 1), 2)
                    if normal_level != "Not detected"
                    else None
                ),
                "is_cancer_relevant": meta.get("is_cancer_relevant", False),
                "data_source": "HPA" if tissue_name in hpa_map else "Curated",
            }

            session.run(
                """
                MERGE (t:Tissue {tissue_name: $tissue_name})
                SET t.tissue_type               = $tissue_type,
                    t.cd46_tumor_expression     = $cd46_tumor_expression,
                    t.cd46_normal_expression    = $cd46_normal_expression,
                    t.tumor_score               = $tumor_score,
                    t.normal_score              = $normal_score,
                    t.tumor_normal_ratio        = $tumor_normal_ratio,
                    t.is_cancer_relevant        = $is_cancer_relevant,
                    t.data_source               = $data_source,
                    t.updated_at                = datetime()
                WITH t
                MATCH (p:Protein {uniprot_id: 'P15529'})
                MERGE (p)-[:EXPRESSED_IN_TISSUE]->(t)
                """,
                **params,
            )
            merged += 1

    logger.info("Merged %d Tissue nodes", merged)
    return {"tissues_merged": merged}
