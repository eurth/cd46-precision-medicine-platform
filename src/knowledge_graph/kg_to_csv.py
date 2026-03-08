"""Export all KG nodes and edges to CSV files for bulk-load / offline analysis."""
from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd

from neo4j import Driver

logger = logging.getLogger(__name__)

NODE_QUERIES = {
    "genes": "MATCH (n:Gene) RETURN n",
    "proteins": "MATCH (n:Protein) RETURN n",
    "diseases": "MATCH (n:Disease) RETURN n",
    "tissues": "MATCH (n:Tissue) RETURN n",
    "drugs": "MATCH (n:Drug) RETURN n",
    "trials": "MATCH (n:ClinicalTrial) RETURN n",
    "patient_groups": "MATCH (n:PatientGroup) RETURN n",
    "cell_lines": "MATCH (n:CellLine) RETURN n",
    "publications": "MATCH (n:Publication) RETURN n",
    "pathways": "MATCH (n:Pathway) RETURN n",
    "analysis_results": "MATCH (n:AnalysisResult) RETURN n",
    "data_sources": "MATCH (n:DataSource) RETURN n",
}

EDGE_QUERIES = {
    "expressed_in_tissue": (
        "MATCH (p:Protein)-[r:EXPRESSED_IN_TISSUE]->(t:Tissue) "
        "RETURN p.uniprot_id AS source, t.tissue_name AS target, "
        "r.tumor_level AS tumor_level, r.normal_level AS normal_level, "
        "r.data_source AS data_source"
    ),
    "expressed_in_disease": (
        "MATCH (g:Gene)-[r:EXPRESSED_IN]->(d:Disease) "
        "RETURN g.ensembl_id AS source, d.tcga_code AS target, "
        "d.mean_log2_expression AS mean_expression"
    ),
    "has_analysis": (
        "MATCH (d:Disease)-[r:HAS_ANALYSIS]->(ar:AnalysisResult) "
        "RETURN d.tcga_code AS source, ar.analysis_id AS target, "
        "ar.hazard_ratio AS hazard_ratio, ar.log_rank_p AS log_rank_p, "
        "ar.is_significant AS is_significant, ar.endpoint AS endpoint"
    ),
    "drug_targets": (
        "MATCH (dr:Drug)-[r:TARGETS]->(p:Protein) "
        "RETURN dr.chembl_id AS source, p.uniprot_id AS target, dr.mechanism_of_action AS mechanism"
    ),
    "drug_indication": (
        "MATCH (dr:Drug)-[r:TESTED_IN]->(d:Disease) "
        "RETURN dr.chembl_id AS source, d.tcga_code AS target, "
        "r.relationship_type AS rel_type, r.clinical_stage AS stage"
    ),
    "trial_enrolls": (
        "MATCH (ct:ClinicalTrial)-[r:ENROLLS]->(d:Disease) "
        "RETURN ct.nct_id AS source, d.tcga_code AS target, r.role AS role"
    ),
    "trial_biomarker": (
        "MATCH (ct:ClinicalTrial)-[r:USES_BIOMARKER]->(g:Gene) "
        "RETURN ct.nct_id AS source, g.ensembl_id AS target, "
        "r.biomarker AS biomarker, r.cutoff AS cutoff"
    ),
    "pub_supports": (
        "MATCH (pub:Publication)-[r:SUPPORTS]->(g:Gene) "
        "RETURN pub.pubmed_id AS source, g.ensembl_id AS target"
    ),
    "pub_supports_disease": (
        "MATCH (pub:Publication)-[r:SUPPORTS_DISEASE]->(d:Disease) "
        "RETURN pub.pubmed_id AS source, d.tcga_code AS target, "
        "r.evidence_strength AS strength, r.evidence_category AS category"
    ),
    "has_patient_group": (
        "MATCH (d:Disease)-[:HAS_PATIENT_GROUP]->(pg:PatientGroup) "
        "RETURN d.tcga_code AS source, pg.group_id AS target, "
        "pg.n_eligible AS n_eligible, pg.fraction_eligible AS fraction"
    ),
    "cellline_expression": (
        "MATCH (g:Gene)-[:EXPRESSED_IN_CELL_LINE]->(cl:CellLine) "
        "RETURN g.ensembl_id AS source, cl.cell_line_id AS target, "
        "cl.cd46_expression_log2 AS expression_log2, cl.cd46_is_dependency AS is_dependency"
    ),
    "gene_encodes": (
        "MATCH (g:Gene)-[:ENCODES]->(p:Protein) "
        "RETURN g.ensembl_id AS source, p.uniprot_id AS target"
    ),
    "pathway_participation": (
        "MATCH (g:Gene)-[:PARTICIPATES_IN]->(pw:Pathway) "
        "RETURN g.ensembl_id AS source, pw.pathway_id AS target, pw.name AS pathway_name"
    ),
}


def _records_to_df(records: list) -> pd.DataFrame:
    """Convert Neo4j record list to a flat DataFrame."""
    if not records:
        return pd.DataFrame()
    rows = []
    for rec in records:
        row = {}
        for key in rec.keys():
            val = rec[key]
            # Node records — flatten properties
            if hasattr(val, "_properties"):
                row.update({f"{key}_{k}": v for k, v in val._properties.items()})
            else:
                row[key] = val
        rows.append(row)
    return pd.DataFrame(rows)


def export_kg_to_csv(driver: Driver, output_dir: Path) -> dict:
    """
    Export all Knowledge Graph nodes and edges to CSV files.

    Args:
        driver: Active Neo4j driver.
        output_dir: Path to write CSV files (e.g., data/processed/kg_ready/).

    Returns:
        Dict with file paths and row counts.
    """
    nodes_dir = output_dir / "nodes"
    edges_dir = output_dir / "edges"
    nodes_dir.mkdir(parents=True, exist_ok=True)
    edges_dir.mkdir(parents=True, exist_ok=True)

    results = {"nodes": {}, "edges": {}}

    with driver.session() as session:
        # Export node CSVs
        for label, query in NODE_QUERIES.items():
            records = session.run(query).data()
            if not records:
                logger.warning("No records for node type: %s", label)
                continue

            # Flatten nested node dict
            rows = []
            for rec in records:
                node = rec.get("n", {})
                if hasattr(node, "_properties"):
                    rows.append(dict(node._properties))
                elif isinstance(node, dict):
                    rows.append(node)

            if not rows:
                continue

            df = pd.DataFrame(rows)
            out_path = nodes_dir / f"{label}.csv"
            df.to_csv(out_path, index=False)
            results["nodes"][label] = {"path": str(out_path), "rows": len(df)}
            logger.info("Exported %d %s nodes → %s", len(df), label, out_path)

        # Export edge CSVs
        for edge_type, query in EDGE_QUERIES.items():
            records = session.run(query).data()
            if not records:
                logger.info("No edges for type: %s (may be expected)", edge_type)
                continue

            df = pd.DataFrame(records)
            out_path = edges_dir / f"{edge_type}.csv"
            df.to_csv(out_path, index=False)
            results["edges"][edge_type] = {"path": str(out_path), "rows": len(df)}
            logger.info("Exported %d %s edges → %s", len(df), edge_type, out_path)

    # Summary stats
    total_nodes = sum(v["rows"] for v in results["nodes"].values())
    total_edges = sum(v["rows"] for v in results["edges"].values())
    logger.info(
        "KG export complete: %d total node rows, %d total edge rows across %d + %d files",
        total_nodes,
        total_edges,
        len(results["nodes"]),
        len(results["edges"]),
    )

    return results
