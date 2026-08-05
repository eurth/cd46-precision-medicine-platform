"""KG-only target dossier — no LLM (demo-safe when OpenRouter times out)."""
from __future__ import annotations

import json

from src.agent.kg_retrieval import (
    cypher_depmap,
    cypher_drugs,
    cypher_drugs_count,
    cypher_expression,
    cypher_interacts,
    cypher_interacts_count,
    cypher_ot_associations,
    cypher_ot_count,
    cypher_publications,
    cypher_publications_count,
    cypher_trials,
    cypher_trials_count,
)
from src.agent.tools import query_kg
from src.knowledge_graph.registry import all_symbols, load_registry


def _registry_symbols() -> tuple[str, ...]:
    try:
        return tuple(all_symbols())
    except Exception:
        return ("CD46", "FOLH1", "FAP", "SSTR2", "GRPR")


def gene_from_question(question: str, default: str) -> str:
    """Prefer explicit symbol/alias in question over session target."""
    q = question.upper()
    if "PSMA" in q or "FOLH1" in q:
        return "FOLH1"
    if "TROP2" in q or "TACSTD2" in q:
        return "TACSTD2"
    if "HER2" in q or "ERBB2" in q:
        return "ERBB2"
    if "B7-H3" in q or "B7H3" in q or "CD276" in q:
        return "CD276"
    # aliases from registry
    try:
        for sym, meta in load_registry()["targets"].items():
            if sym.upper() in q:
                return sym
            for a in meta.get("aliases") or []:
                if str(a).upper() in q:
                    return sym
    except Exception:
        pass
    for sym in _registry_symbols():
        if sym in q:
            return sym
    return default


def is_dossier_question(question: str) -> bool:
    q = question.lower()
    if "dossier" in q or "landscape" in q:
        return True
    hits = sum(
        1
        for k in (
            "expression",
            "tcga",
            "drug",
            "trial",
            "nct",
            "depmap",
            "crispr",
            "cell line",
            "chembl",
            "pubmed",
            "string",
            "ppi",
            "open target",
        )
        if k in q
    )
    return hits >= 3


def _rows(cypher: str) -> list[dict]:
    raw = query_kg(cypher)
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return []
    if isinstance(data, dict) and "error" in data:
        return []
    return data if isinstance(data, list) else []


def _md_table(rows: list[dict], cols: list[str], *, limit: int = 12) -> str:
    if not rows:
        return "_No rows in knowledge graph._\n"
    lines = ["| " + " | ".join(cols) + " |", "| " + " | ".join(["---"] * len(cols)) + " |"]
    for row in rows[:limit]:
        lines.append("| " + " | ".join(str(row.get(c, "—")) for c in cols) + " |")
    if len(rows) > limit:
        lines.append(f"\n_Showing {limit} of {len(rows)} graph rows._")
    return "\n".join(lines) + "\n"


def _scalar(cypher: str, key: str, default: str = "0") -> str:
    rows = _rows(cypher)
    if rows and rows[0].get(key) is not None:
        return str(rows[0][key])
    return default


def build_kg_dossier(gene: str) -> tuple[str, list[str]]:
    """Return markdown dossier + source labels (instant, no LLM)."""
    expr = _rows(cypher_expression(gene))
    ot = _rows(cypher_ot_associations(gene))
    ot_n = _scalar(cypher_ot_count(gene), "ot_count")
    drugs = _rows(cypher_drugs(gene))
    drug_n = _scalar(cypher_drugs_count(gene), "drug_count")
    trials = _rows(cypher_trials(gene))
    trial_n = _scalar(cypher_trials_count(gene), "trial_count")
    pubs = _rows(cypher_publications(gene))
    pub_n = _scalar(cypher_publications_count(gene), "publication_count")
    ppi = _rows(cypher_interacts(gene))
    ppi_n = _scalar(cypher_interacts_count(gene), "interact_count")
    depmap = _rows(cypher_depmap(gene))

    parts = [
        f"### {gene} — Knowledge Graph dossier",
        "_Retrieved live from Neo4j (read-only Cypher). No LLM synthesis._\n",
        "#### 1. TCGA expression (top cancers)",
        _md_table(
            expr,
            ["cancer", "median", "rank"],
            limit=10,
        ),
        f"#### 2. Open Targets disease associations ({ot_n} in graph; top by score)",
        _md_table(
            ot,
            ["disease", "mondo_id", "score", "genetics", "literature"],
            limit=12,
        ),
        f"#### 3. Drugs targeting gene (ChEMBL / curated) — {drug_n} TARGETS edges",
        _md_table(
            drugs,
            ["drug", "type", "max_phase", "chembl_id"],
            limit=12,
        ),
        f"#### 4. Clinical trials (TARGETS_GENE) — {trial_n} trials; sample below",
        _md_table(
            trials,
            ["nct_id", "phase", "status", "title"],
            limit=10,
        ),
        f"#### 5. PubMed evidence (SUPPORTS) — {pub_n} publications",
        _md_table(
            pubs,
            ["title", "journal", "year", "pmid"],
            limit=10,
        ),
        f"#### 6. STRING protein partners (INTERACTS_WITH) — {ppi_n} edges; top neighbors",
        _md_table(
            ppi,
            ["partner", "score", "escore", "tscore"],
            limit=12,
        ),
        "#### 7. DepMap cell-line dependency (CRISPR)",
        _md_table(
            depmap,
            ["cell_line", "cancer_type", "crispr_score"],
            limit=10,
        ),
    ]
    sources = [
        "AuraDB Knowledge Graph",
        "TCGA (graph)",
        "Open Targets (graph)",
        "ChEMBL (graph)",
        "ClinicalTrials.gov (graph)",
        "PubMed (graph)",
        "STRING DB (graph)",
        "DepMap (graph)",
    ]
    return "\n".join(parts), sources


if __name__ == "__main__":
    md, src = build_kg_dossier("FOLH1")
    assert "FOLH1" in md and "AuraDB" in str(src)
    print("kg_dossier_ok")
