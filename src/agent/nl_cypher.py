"""NL → Cypher helpers for agent KG retrieval (template fallback + optional LLM)."""
from __future__ import annotations

import hashlib
import logging
import os
import re

logger = logging.getLogger(__name__)

_SCHEMA_HINT = """
Neo4j schema (read-only MATCH): Gene(symbol), Disease(tcga_code, mondo_id, name), Drug(name, chembl_id),
ClinicalTrial(nct_id), SurvivalResult(gene_symbol, hazard_ratio, p_value), CellLine(name),
Publication(pubmed_id, title, year).
Relationships: EXPRESSED_IN_CANCER, ASSOCIATED_WITH (Gene→Disease, Open Targets),
TARGETS (Drug→Gene), TARGETS_GENE (Trial→Gene), DEPENDS_ON, HAS_SURVIVAL_RESULT,
SUPPORTS (Publication→Gene), INTERACTS_WITH (Gene↔Gene, STRING).
""".strip()


def _clean_cypher(raw: str) -> str:
    text = raw.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        text = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])
    return text.replace("```cypher", "").replace("```", "").strip()


def _llm_nl_cypher(question: str, gene: str) -> str | None:
    """Optional LLM translation — skipped when no API key."""
    if not any(os.getenv(k) for k in ("OPENROUTER_API_KEY", "OPENAI_API_KEY", "GEMINI_API_KEY")):
        return None
    try:
        from src.agent.llm_factory import get_llm

        llm = get_llm()
        prompt = f"""{_SCHEMA_HINT}

Active gene symbol: {gene}
Research question: {question}

Return ONLY one read-only Cypher query (MATCH/WITH/RETURN). LIMIT 25.
Use gene symbol '{gene}' where relevant. No markdown fences."""
        out = llm.chat(prompt, context="")
        cypher = _clean_cypher(out)
        if not cypher.upper().startswith(("MATCH", "WITH", "CALL")):
            return None
        forbidden = ("CREATE", "MERGE", "DELETE", "SET ", "DROP")
        up = cypher.upper()
        if any(k in up for k in forbidden):
            return None
        return cypher
    except Exception as exc:
        logger.debug("NL→Cypher LLM skipped: %s", exc)
        return None


def nl_cypher_for_question(question: str, gene: str, *, intent: str = "general") -> tuple[str, str] | None:
    """
    Best-effort NL→Cypher for agent context.
    ponytail: LLM only for graph-heavy intents/questions; templates handle the rest via kg_retrieval.
    """
    q = question.lower()
    graphy = intent == "knowledge_graph" or any(
        k in q for k in ("cypher", "neo4j", "knowledge graph", " graph ", "node", "relationship")
    )
    if not graphy:
        return None
    # Cache key in session-less module — hash question+gene
    cache_key = hashlib.md5(f"{gene}:{question[:200]}".encode()).hexdigest()
    if not hasattr(nl_cypher_for_question, "_cache"):
        nl_cypher_for_question._cache = {}  # type: ignore[attr-defined]
    cached = nl_cypher_for_question._cache.get(cache_key)  # type: ignore[attr-defined]
    if cached is not None:
        return cached
    cypher = _llm_nl_cypher(question, gene)
    result = ("NL→Cypher", cypher) if cypher else None
    nl_cypher_for_question._cache[cache_key] = result  # type: ignore[attr-defined]
    return result
