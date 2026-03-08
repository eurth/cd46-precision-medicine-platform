"""
Process DepMap 25Q3 cell line data to extract CD46 CRISPR essentiality scores.
Input:  data/raw/depmap/CRISPRGeneEffect.csv + Model.csv
Output: data/processed/depmap_cd46_essentiality.csv
"""

import logging
from pathlib import Path

import pandas as pd
import yaml

log = logging.getLogger(__name__)

_CONFIG_PATH = Path(__file__).parents[2] / "config" / "datasets.yaml"
with open(_CONFIG_PATH) as f:
    _DS = yaml.safe_load(f)["depmap"]

CRISPR_PATH = Path(_DS["files"]["crispr"]["local_path"])
META_PATH = Path(_DS["files"]["metadata"]["local_path"])
CD46_COL = _DS["files"]["crispr"]["cd46_column"]
OUTPUT_PATH = Path(_DS["output"]["processed"])

DEPENDENCY_THRESHOLD = -0.5  # CRISPR score below this = CD46 is essential


def extract_cd46_depmap() -> pd.DataFrame:
    """
    Extract CD46 CRISPR essentiality scores from DepMap 25Q3.
    Returns DataFrame: depmap_id, cell_line_name, cancer_type, lineage,
                       cd46_crispr_score, cd46_is_dependency
    """
    if not CRISPR_PATH.exists():
        raise FileNotFoundError(
            f"DepMap CRISPR file not found: {CRISPR_PATH}\n"
            "Please download CRISPRGeneEffect.csv from https://depmap.org/portal/data_page/"
        )

    log.info("Reading DepMap CRISPR data (CD46 column only)...")
    crispr = pd.read_csv(CRISPR_PATH, index_col=0,
                         usecols=lambda c: "Unnamed" in c or "CD46" in c)
    cd46_cols = [c for c in crispr.columns if "CD46" in c]
    if not cd46_cols:
        raise KeyError(f"CD46 column not found. Available cols sample: {list(crispr.columns[:5])}")

    crispr = crispr[[cd46_cols[0]]].rename(columns={cd46_cols[0]: "cd46_crispr_score"})
    crispr.index.name = "depmap_id"
    crispr = crispr.reset_index()
    log.info("CRISPR: %d cell lines loaded", len(crispr))

    # Load Model.csv metadata for cancer type and lineage
    if META_PATH.exists():
        log.info("Reading Model.csv metadata...")
        meta = pd.read_csv(META_PATH)
        # Standardise the ID column name
        id_col = next((c for c in meta.columns if c in ("ModelID", "DepMapID", "depmap_id")), None)
        if id_col:
            meta = meta.rename(columns={id_col: "depmap_id"})
        # Select useful columns
        keep = ["depmap_id"]
        col_map = {
            "CellLineName": "cell_line_name",
            "OncotreePrimaryDisease": "cancer_type",
            "OncotreeLineage": "lineage",
            "OncotreeSubtype": "subtype",
            "DepmapModelType": "model_type",
        }
        for src, dst in col_map.items():
            if src in meta.columns:
                meta = meta.rename(columns={src: dst})
                keep.append(dst)
        meta = meta[keep].drop_duplicates("depmap_id")
        result = crispr.merge(meta, on="depmap_id", how="left")
    else:
        log.warning("Model.csv not found — cancer type info will be missing")
        result = crispr.copy()
        result["cell_line_name"] = result["depmap_id"]
        result["cancer_type"] = "Unknown"
        result["lineage"] = "Unknown"

    result["cd46_is_dependency"] = result["cd46_crispr_score"].fillna(0) < DEPENDENCY_THRESHOLD

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(OUTPUT_PATH, index=False)
    log.info("DepMap: %d cell lines → %s", len(result), OUTPUT_PATH)

    n_dep = result["cd46_is_dependency"].sum()
    log.info("CD46 is a fitness dependency in %d / %d cell lines (%.1f%%)",
             n_dep, len(result), 100 * n_dep / len(result))

    return result


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    df = extract_cd46_depmap()
    print(f"\nDepMap CD46 summary:")
    print(f"  Total cell lines: {len(df)}")
    print(f"  CD46 dependencies: {df['cd46_is_dependency'].sum()}")
    print(f"  Median CRISPR score: {df['cd46_crispr_score'].median():.3f}")
