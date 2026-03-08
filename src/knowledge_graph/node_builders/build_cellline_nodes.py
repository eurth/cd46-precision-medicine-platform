"""Build CellLine nodes from DepMap CCLE + CRISPR essentiality data."""
from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd

from neo4j import Driver

logger = logging.getLogger(__name__)

# Curated cell lines with known CD46 biology — always included
CURATED_CELL_LINES = [
    {
        "cell_line_id": "LNCaP",
        "name": "LNCaP",
        "cancer_type": "PRAD",
        "primary_site": "Prostate",
        "cd46_expression_log2": 4.2,
        "cd46_is_dependency": False,
        "crispr_score": -0.1,
        "ar_positive": True,
        "psma_positive": True,
        "notes": "Classic androgen-sensitive PRAD model; high CD46",
    },
    {
        "cell_line_id": "PC3",
        "name": "PC3",
        "cancer_type": "PRAD",
        "primary_site": "Prostate",
        "cd46_expression_log2": 3.8,
        "cd46_is_dependency": False,
        "crispr_score": -0.2,
        "ar_positive": False,
        "psma_positive": False,
        "notes": "Androgen-independent, PSMA-negative — CD46 targeting alone applies",
    },
    {
        "cell_line_id": "DU145",
        "name": "DU145",
        "cancer_type": "PRAD",
        "primary_site": "Prostate",
        "cd46_expression_log2": 3.6,
        "cd46_is_dependency": False,
        "crispr_score": -0.15,
        "ar_positive": False,
        "psma_positive": False,
        "notes": "Brain-metastasis derived; AR-negative CRPC model",
    },
    {
        "cell_line_id": "22Rv1",
        "name": "22Rv1",
        "cancer_type": "PRAD",
        "primary_site": "Prostate",
        "cd46_expression_log2": 4.5,
        "cd46_is_dependency": False,
        "crispr_score": -0.08,
        "ar_positive": True,
        "psma_positive": False,
        "notes": "CRPC model with AR-V7 splice variant; high CD46 maintained",
    },
    {
        "cell_line_id": "SKOV3",
        "name": "SKOV3",
        "cancer_type": "OV",
        "primary_site": "Ovary",
        "cd46_expression_log2": 4.1,
        "cd46_is_dependency": False,
        "crispr_score": -0.05,
        "ar_positive": False,
        "psma_positive": False,
        "notes": "Ovarian cancer model with high CD46; candidate for 225Ac-CD46",
    },
    {
        "cell_line_id": "T24",
        "name": "T24",
        "cancer_type": "BLCA",
        "primary_site": "Bladder",
        "cd46_expression_log2": 3.9,
        "cd46_is_dependency": False,
        "crispr_score": -0.12,
        "ar_positive": False,
        "psma_positive": False,
        "notes": "Bladder cancer — elevated CD46 correlates with MIBC subtype",
    },
    {
        "cell_line_id": "MCF7",
        "name": "MCF7",
        "cancer_type": "BRCA",
        "primary_site": "Breast",
        "cd46_expression_log2": 2.9,
        "cd46_is_dependency": False,
        "crispr_score": -0.13,
        "ar_positive": False,
        "psma_positive": False,
        "notes": "ER+ breast cancer — moderate CD46; TNBC models show higher expression",
    },
]


def _parse_depmap_csv(depmap_file: Path) -> list[dict]:
    """Parse DepMap CCLE essentiality CSV to extract CD46 data."""
    if not depmap_file.exists():
        logger.warning("DepMap CSV not found: %s", depmap_file)
        return []

    df = pd.read_csv(depmap_file)
    records = []

    for _, row in df.iterrows():
        cell_line_id = str(row.get("DepMap_ID", row.get("cell_line_id", "")))
        name = str(row.get("cell_line_name", cell_line_id))

        if not cell_line_id or cell_line_id in {c["cell_line_id"] for c in CURATED_CELL_LINES}:
            continue

        records.append(
            {
                "cell_line_id": cell_line_id,
                "name": name,
                "cancer_type": str(row.get("primary_disease", "Unknown")),
                "primary_site": str(row.get("primary_site", "Unknown")),
                "cd46_expression_log2": float(row["cd46_expression_log2"]) if "cd46_expression_log2" in row else None,
                "cd46_is_dependency": bool(row["cd46_is_dependency"]) if "cd46_is_dependency" in row else False,
                "crispr_score": float(row["crispr_score"]) if "crispr_score" in row else None,
                "ar_positive": None,
                "psma_positive": None,
                "notes": "From DepMap CCLE dataset",
            }
        )

    logger.info("Parsed %d cell lines from DepMap CSV", len(records))
    return records


def build_cellline_nodes(driver: Driver, processed_dir: Path) -> dict:
    """Merge CellLine nodes from curated list + DepMap CCLE output."""
    depmap_file = processed_dir / "depmap_cd46_essentiality.csv"
    depmap_records = _parse_depmap_csv(depmap_file)

    # Curated cell lines take precedence
    all_lines = CURATED_CELL_LINES + depmap_records[:100]  # cap at 100 extra

    merged = 0
    with driver.session() as session:
        for cl in all_lines:
            session.run(
                """
                MERGE (cl:CellLine {cell_line_id: $cell_line_id})
                SET cl.name                    = $name,
                    cl.cancer_type             = $cancer_type,
                    cl.primary_site            = $primary_site,
                    cl.cd46_expression_log2    = $cd46_expression_log2,
                    cl.cd46_is_dependency      = $cd46_is_dependency,
                    cl.crispr_score            = $crispr_score,
                    cl.ar_positive             = $ar_positive,
                    cl.psma_positive           = $psma_positive,
                    cl.notes                   = $notes,
                    cl.updated_at              = datetime()
                WITH cl
                MATCH (g:Gene {ensembl_id: 'ENSG00000117335'})
                MERGE (g)-[:EXPRESSED_IN_CELL_LINE]->(cl)
                """,
                **cl,
            )
            # Link essentiality as analysis result
            if cl.get("cd46_is_dependency"):
                session.run(
                    """
                    MATCH (cl:CellLine {cell_line_id: $cell_line_id})
                    MATCH (g:Gene {ensembl_id: 'ENSG00000117335'})
                    MERGE (g)-[:IS_DEPENDENCY_IN]->(cl)
                    """,
                    cell_line_id=cl["cell_line_id"],
                )
            merged += 1

    logger.info("Merged %d CellLine nodes", merged)
    return {"cell_lines_merged": merged}
