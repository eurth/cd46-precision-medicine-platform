"""KG-only target dossier — no LLM (demo-safe when OpenRouter times out)."""
from __future__ import annotations

import json

from src.agent.kg_retrieval import (
    cypher_depmap,
    cypher_drugs,
    cypher_expression,
    cypher_trials,
)
from src.agent.tools import query_kg


_SYMBOLS = ("CD46", "FOLH1", "FAP", "SSTR2", "GRPR")


def gene_from_question(question: str, default: str) -> str:
    """Prefer explicit symbol/alias in question over session target."""
    q = question.upper()
    if "PSMA" in q or "FOLH1" in q:
        return "FOLH1"
    for sym in _SYMBOLS:
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


def build_kg_dossier(gene: str) -> tuple[str, list[str]]:
    """Return markdown dossier + source labels (instant, no LLM)."""
    expr = _rows(cypher_expression(gene))
    drugs = _rows(cypher_drugs(gene))
    trials = _rows(cypher_trials(gene))
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
        "#### 2. Drugs targeting gene (ChEMBL / curated)",
        _md_table(
            drugs,
            ["drug", "type", "max_phase"],
            limit=12,
        ),
        "#### 3. Clinical trials (NCT-linked)",
        _md_table(
            trials,
            ["nct_id", "phase", "status", "title"],
            limit=10,
        ),
        "#### 4. DepMap cell-line dependency (CRISPR)",
        _md_table(
            depmap,
            ["cell_line", "cancer_type", "crispr_score"],
            limit=10,
        ),
    ]
    sources = [
        "AuraDB Knowledge Graph",
        "TCGA (graph)",
        "ChEMBL (graph)",
        "ClinicalTrials.gov (graph)",
        "DepMap (graph)",
    ]
    return "\n".join(parts), sources


if __name__ == "__main__":
    md, src = build_kg_dossier("FOLH1")
    assert "FOLH1" in md and "AuraDB" in str(src)
    print("kg_dossier_ok")
