"""Gene-parameterized Cypher snippets for agent context (read-only)."""
from __future__ import annotations


def cypher_expression(gene: str) -> str:
    return f"""
MATCH (g:Gene {{symbol: '{gene}'}})-[r:EXPRESSED_IN_CANCER]->(d:Disease)
RETURN d.tcga_code AS cancer, r.median_tpm_log2 AS median, r.expression_rank AS rank
ORDER BY r.expression_rank ASC
LIMIT 15
""".strip()


def cypher_survival(gene: str) -> str:
    return f"""
MATCH (d:Disease)-[:HAS_SURVIVAL_RESULT]->(sr:SurvivalResult)
WHERE sr.gene_symbol = '{gene}'
  AND sr.hazard_ratio > 1.0
  AND sr.p_value < 0.05
RETURN d.tcga_code AS cancer, sr.hazard_ratio AS hr, sr.p_value AS p, sr.endpoint AS endpoint
ORDER BY sr.hazard_ratio DESC
LIMIT 15
""".strip()


def cypher_drugs(gene: str) -> str:
    # ponytail: alias `drug` must not shadow the node in ORDER BY (Neo4j TypeError)
    return f"""
MATCH (d:Drug)-[:TARGETS]->(g:Gene {{symbol: '{gene}'}})
WITH d
ORDER BY coalesce(d.max_phase, -1) DESC, coalesce(d.name, '')
RETURN d.name AS drug, d.drug_type AS type, d.max_phase AS max_phase,
       d.chembl_id AS chembl_id, d.source AS source
LIMIT 30
""".strip()


def cypher_trials(gene: str) -> str:
    return f"""
MATCH (t:ClinicalTrial)-[:TARGETS_GENE]->(g:Gene {{symbol: '{gene}'}})
RETURN t.nct_id AS nct_id, t.phase AS phase, t.status AS status, t.title AS title
ORDER BY t.phase, t.nct_id
LIMIT 30
""".strip()


def cypher_trials_count(gene: str) -> str:
    return f"""
MATCH (:ClinicalTrial)-[:TARGETS_GENE]->(g:Gene {{symbol: '{gene}'}})
RETURN count(*) AS trial_count
""".strip()


def cypher_ot_associations(gene: str) -> str:
    return f"""
MATCH (g:Gene {{symbol: '{gene}'}})-[r:ASSOCIATED_WITH]->(d:Disease)
RETURN d.name AS disease, d.mondo_id AS mondo_id,
       round(r.score, 4) AS score,
       round(coalesce(r.genetics_score, 0), 4) AS genetics,
       round(coalesce(r.literature_score, 0), 4) AS literature
ORDER BY r.score DESC
LIMIT 40
""".strip()


def cypher_ot_count(gene: str) -> str:
    return f"""
MATCH (g:Gene {{symbol: '{gene}'}})-[:ASSOCIATED_WITH]->(:Disease)
RETURN count(*) AS ot_count
""".strip()


def cypher_interacts(gene: str) -> str:
    return f"""
MATCH (g:Gene {{symbol: '{gene}'}})-[r:INTERACTS_WITH]-(b:Gene)
WHERE b.symbol <> '{gene}'
RETURN b.symbol AS partner,
       round(coalesce(r.score, 0), 4) AS score,
       round(coalesce(r.escore, 0), 4) AS escore,
       round(coalesce(r.tscore, 0), 4) AS tscore
ORDER BY r.score DESC
LIMIT 30
""".strip()


def cypher_depmap(gene: str) -> str:
    return f"""
MATCH (cl:CellLine)-[r:DEPENDS_ON]->(g:Gene {{symbol: '{gene}'}})
RETURN cl.name AS cell_line, cl.cancer_type AS cancer_type, r.crispr_score AS crispr_score
ORDER BY r.crispr_score ASC
LIMIT 12
""".strip()


def cypher_publications(gene: str) -> str:
    return f"""
MATCH (pub:Publication)-[:SUPPORTS]->(g:Gene {{symbol: '{gene}'}})
RETURN pub.title AS title, pub.journal AS journal, pub.year AS year, pub.pubmed_id AS pmid
ORDER BY pub.year DESC
LIMIT 25
""".strip()


def cypher_publications_count(gene: str) -> str:
    return f"""
MATCH (:Publication)-[:SUPPORTS]->(g:Gene {{symbol: '{gene}'}})
RETURN count(*) AS publication_count
""".strip()


def cypher_drugs_count(gene: str) -> str:
    return f"""
MATCH (:Drug)-[:TARGETS]->(g:Gene {{symbol: '{gene}'}})
RETURN count(*) AS drug_count
""".strip()


def cypher_interacts_count(gene: str) -> str:
    return f"""
MATCH (g:Gene {{symbol: '{gene}'}})-[:INTERACTS_WITH]-(:Gene)
RETURN count(*) AS interact_count
""".strip()


# ponytail: keyword → query; extend for richer NL routing later
INTENT_KG_QUERIES: dict[str, str] = {
    "expression": "expression",
    "survival": "survival",
    "drug": "drugs",
    "trial": "trials",
    "protein": "depmap",
    "literature": "publications",
    "knowledge_graph": "expression",
    "biomarker": "expression",
    "general": "expression",
}


def cypher_eligibility(gene: str) -> str:
    return f"""
MATCH (pg:PatientGroup)
WHERE pg.gene_symbol = '{gene}' OR pg.expression_group CONTAINS '{gene}'
RETURN pg.cancer_type AS cancer, pg.threshold_method AS threshold,
       pg.n_eligible AS n_eligible, pg.n_total AS n_total, pg.pct_eligible AS pct
ORDER BY pg.pct_eligible DESC
LIMIT 12
""".strip()


def supplemental_queries(question: str, intent: str, gene: str) -> list[tuple[str, str]]:
    """Keyword boosts on top of intent templates — no LLM."""
    q = question.lower()
    extra: list[tuple[str, str]] = []
    if any(k in q for k in ("eligib", "threshold", "75th", "percent", "fraction")):
        extra.append(("KG patient groups", cypher_eligibility(gene)))
    if any(k in q for k in ("depmap", "crispr", "dependency", "cell line")):
        extra.append(("KG DepMap", cypher_depmap(gene)))
    if any(k in q for k in ("pubmed", "publication", "paper", "literature")):
        extra.append(("KG publications", cypher_publications(gene)))
    if any(k in q for k in ("open target", "associated disease", "mondo", "ot ")):
        extra.append(("KG Open Targets", cypher_ot_associations(gene)))
    if any(k in q for k in ("string", "ppi", "interact", "protein-protein")):
        extra.append(("KG STRING PPI", cypher_interacts(gene)))
    if intent == "eligibility":
        extra.append(("KG patient groups", cypher_eligibility(gene)))
    # dedupe labels
    seen: set[str] = set()
    out: list[tuple[str, str]] = []
    for label, cypher in extra:
        if label in seen:
            continue
        seen.add(label)
        out.append((label, cypher))
    return out


def queries_for_intent(intent: str, gene: str, question: str = "") -> list[tuple[str, str]]:
    """Return (label, cypher) pairs — additive retrieval per intent + question keywords."""
    builders = {
        "expression": [("KG expression ranks", cypher_expression(gene))],
        "survival": [
            ("KG survival (HR>1)", cypher_survival(gene)),
            ("KG expression ranks", cypher_expression(gene)),
        ],
        "drug": [
            ("KG drugs", cypher_drugs(gene)),
            ("KG trials", cypher_trials(gene)),
        ],
        "trial": [("KG trials", cypher_trials(gene))],
        "protein": [
            ("KG DepMap dependency", cypher_depmap(gene)),
            ("KG drugs", cypher_drugs(gene)),
        ],
        "literature": [("KG publications", cypher_publications(gene))],
        "biomarker": [
            ("KG expression", cypher_expression(gene)),
            ("KG co-expression context", cypher_survival(gene)),
        ],
        "knowledge_graph": [
            ("KG expression", cypher_expression(gene)),
            ("KG drugs", cypher_drugs(gene)),
            ("KG trials", cypher_trials(gene)),
        ],
        "dossier": [
            ("KG expression ranks", cypher_expression(gene)),
            ("KG Open Targets", cypher_ot_associations(gene)),
            ("KG drugs", cypher_drugs(gene)),
            ("KG trials", cypher_trials(gene)),
            ("KG publications", cypher_publications(gene)),
            ("KG STRING PPI", cypher_interacts(gene)),
            ("KG DepMap dependency", cypher_depmap(gene)),
        ],
        "general": [
            ("KG expression", cypher_expression(gene)),
            ("KG drugs", cypher_drugs(gene)),
        ],
        "eligibility": [
            ("KG expression", cypher_expression(gene)),
            ("KG patient groups", cypher_eligibility(gene)),
        ],
    }
    base = builders.get(intent, builders["general"])
    merged = list(base)
    for item in supplemental_queries(question, intent, gene):
        if item not in merged:
            merged.append(item)
    return merged
