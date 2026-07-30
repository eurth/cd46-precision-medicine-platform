"""Smoke-check kg_retrieval + nl_cypher wiring."""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT))

from src.agent.kg_retrieval import queries_for_intent, supplemental_queries  # noqa: E402
from src.agent.nl_cypher import nl_cypher_for_question  # noqa: E402

q_elig = "How many PRAD patients are eligible at the 75th percentile?"
qs = queries_for_intent("eligibility", "FOLH1", q_elig)
labels = [l for l, _ in qs]
assert "KG patient groups" in labels, labels
assert supplemental_queries(q_elig, "eligibility", "FOLH1")

# NL path returns None without API keys (expected in CI)
assert nl_cypher_for_question("show neo4j graph for FOLH1 trials", "FOLH1", intent="knowledge_graph") is None

print("verify_kg_rag_ok")
