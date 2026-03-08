"""
Named Cypher queries for the CD46 knowledge graph.
All 8 queries from MEMORY_BANK/kg_schema.md implemented as Python functions.
Each returns a list of result dicts from Neo4j driver.
"""

import logging
from typing import Any

log = logging.getLogger(__name__)


def run_query(driver, cypher: str, params: dict | None = None) -> list[dict]:
    """Execute a Cypher query and return results as list of dicts."""
    with driver.session() as session:
        result = session.run(cypher, params or {})
        return [dict(record) for record in result]


# ─── Q1: Which cancers have CD46 overexpression AND poor survival? ─────────

Q1_CYPHER = """
MATCH (d:Disease)<-[:OVEREXPRESSED_IN]-(p:Protein {symbol:"CD46"})
WHERE d.cd46_expression_rank <= 15
  AND d.cd46_survival_hr > 1.2
  AND d.cd46_survival_pval < 0.05
RETURN d.name AS disease, d.tcga_code AS code,
       d.cd46_median_tpm_log2 AS median_expr,
       d.cd46_expression_rank AS rank,
       d.cd46_survival_hr AS hazard_ratio,
       d.cd46_survival_pval AS p_value,
       d.priority_score AS priority_score,
       d.priority_label AS priority_label
ORDER BY d.priority_score DESC
"""

def q1_priority_cancers(driver) -> list[dict]:
    """Q1: Cancers with CD46 overexpression AND poor survival."""
    return run_query(driver, Q1_CYPHER)


# ─── Q2: What % of prostate patients are 225Ac eligible? ─────────────────

Q2_CYPHER = """
MATCH (d:Disease {tcga_code:"PRAD"})-[:HAS_PATIENT_GROUP]->(pg:PatientGroup)
WHERE pg.expression_group = "CD46-High"
RETURN pg.name AS group_name,
       pg.n_patients AS n_eligible,
       pg.threshold_method AS threshold,
       d.tcga_sample_count AS n_total,
       toFloat(pg.n_patients) / d.tcga_sample_count * 100 AS pct_eligible
ORDER BY pct_eligible DESC
"""

def q2_prad_eligibility(driver) -> list[dict]:
    """Q2: % of PRAD patients eligible for 225Ac-CD46 therapy."""
    return run_query(driver, Q2_CYPHER)


# ─── Q3: CD46 + PSMA co-expression ───────────────────────────────────────

Q3_CYPHER = """
MATCH (g1:Gene {symbol:"CD46"})-[c:CORRELATED_WITH]-(g2:Gene)
WHERE g2.symbol IN ["FOLH1", "PSCA", "AR", "MYC"]
RETURN g1.symbol AS gene1, g2.symbol AS gene2,
       c.spearman_rho AS spearman_rho,
       c.p_value AS p_value,
       c.cancer_type AS cancer_type,
       c.n_samples AS n_samples
ORDER BY abs(c.spearman_rho) DESC
"""

def q3_coexpression(driver, cancer_type: str = "PRAD") -> list[dict]:
    """Q3: CD46 co-expression with therapeutic targets."""
    return run_query(driver, Q3_CYPHER)


# ─── Q4: Active clinical trials targeting CD46 ───────────────────────────

Q4_CYPHER = """
MATCH (d:Drug)-[:TARGETS]->(g:Gene {symbol:"CD46"})
MATCH (d)-[:TESTED_IN]->(t:ClinicalTrial)
WHERE t.status IN ["RECRUITING", "ACTIVE_NOT_RECRUITING"]
RETURN t.nct_id AS nct_id,
       t.title AS title,
       t.phase AS phase,
       t.status AS status,
       d.name AS drug_name,
       d.drug_type AS drug_type,
       t.sponsor AS sponsor,
       t.enrollment_target AS enrollment_target
ORDER BY t.phase DESC
"""

def q4_active_trials(driver) -> list[dict]:
    """Q4: All active clinical trials targeting CD46."""
    return run_query(driver, Q4_CYPHER)


# ─── Q5: CD46 protein therapeutic window ─────────────────────────────────

Q5_CYPHER = """
MATCH (p:Protein {symbol:"CD46"})-[e:EXPRESSED_IN]->(t:Tissue)
RETURN t.name AS tissue,
       t.type AS tissue_type,
       e.h_score_approx AS h_score,
       e.staining_intensity AS staining,
       e.intensity_score AS score,
       e.fraction_positive AS fraction_positive
ORDER BY e.intensity_score DESC
"""

def q5_protein_expression(driver) -> list[dict]:
    """Q5: CD46 protein expression therapeutic window (HPA data)."""
    return run_query(driver, Q5_CYPHER)


# ─── Q6: Resistance variants ────────────────────────────────────────────

Q6_CYPHER = """
MATCH (v:GenomicVariant)-[f:FOUND_IN]->(pg:PatientGroup {expression_group:"CD46-Low"})
WHERE f.frequency_ratio > 1.5
RETURN v.gene AS gene,
       v.consequence AS variant_type,
       f.frequency_pct AS frequency_pct,
       f.frequency_ratio AS enrichment_ratio,
       f.fdr AS fdr,
       pg.cancer_type AS cancer_type
ORDER BY f.frequency_ratio DESC LIMIT 15
"""

def q6_resistance_variants(driver) -> list[dict]:
    """Q6: Variants enriched in CD46-low tumors (potential resistance mechanisms)."""
    return run_query(driver, Q6_CYPHER)


# ─── Q7: Full CD46 graph neighborhood (2 hops) ───────────────────────────

Q7_CYPHER = """
MATCH path = (g:Gene {symbol:"CD46"})-[*1..2]-(neighbor)
WHERE NOT neighbor:DataSource
RETURN path LIMIT 100
"""

def q7_neighborhood(driver) -> list:
    """Q7: Full CD46 2-hop neighborhood for graph visualization."""
    with driver.session() as session:
        result = session.run(Q7_CYPHER)
        paths = []
        for record in result:
            path = record["path"]
            for node in path.nodes:
                paths.append({"type": "node", "id": node.id,
                               "labels": list(node.labels), "props": dict(node)})
            for rel in path.relationships:
                paths.append({"type": "rel", "start": rel.start_node.id,
                               "end": rel.end_node.id, "rel_type": rel.type})
        return paths


# ─── Q8: Priority ranking across all cancers ─────────────────────────────

Q8_CYPHER = """
MATCH (d:Disease)
WHERE d.priority_score IS NOT NULL
RETURN d.name AS disease,
       d.tcga_code AS code,
       d.cd46_expression_rank AS expression_rank,
       d.cd46_survival_hr AS hazard_ratio,
       d.cd46_cna_amplification_freq AS cna_freq,
       d.priority_score AS priority_score,
       d.priority_label AS priority_label
ORDER BY d.priority_score DESC
"""

def q8_priority_ranking(driver) -> list[dict]:
    """Q8: Full priority ranking of all cancer types for 225Ac-CD46 therapy."""
    return run_query(driver, Q8_CYPHER)


# ─── Bonus: DepMap essentiality ──────────────────────────────────────────

Q_DEPMAP_CYPHER = """
MATCH (cl:CellLine)
WHERE cl.cd46_is_dependency = true
RETURN cl.name AS cell_line,
       cl.cancer_type AS cancer_type,
       cl.cd46_crispr_score AS crispr_score,
       cl.cd46_expression_tpm AS cd46_expression
ORDER BY cl.cd46_crispr_score ASC LIMIT 20
"""

def q_depmap_dependencies(driver) -> list[dict]:
    """Bonus: Cell lines where CD46 is a fitness dependency."""
    return run_query(driver, Q_DEPMAP_CYPHER)


ALL_QUERIES = {
    "Q1: Priority Cancers (overexpression + poor survival)": q1_priority_cancers,
    "Q2: PRAD 225Ac Eligibility %": q2_prad_eligibility,
    "Q3: CD46 Co-expression Panel": q3_coexpression,
    "Q4: Active Clinical Trials": q4_active_trials,
    "Q5: CD46 Protein Therapeutic Window (HPA)": q5_protein_expression,
    "Q6: Resistance Variants (CD46-Low enriched)": q6_resistance_variants,
    "Q7: CD46 Graph Neighborhood (2 hops)": q7_neighborhood,
    "Q8: Full Priority Ranking": q8_priority_ranking,
    "DepMap: CD46 Fitness Dependencies": q_depmap_dependencies,
}
