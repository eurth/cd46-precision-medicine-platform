"""Smoke: Neo4j counts + LLM chat (OpenRouter if key set, else Gemini/OpenAI)."""
from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv

load_dotenv(ROOT / ".env")


def main() -> int:
    from neo4j import GraphDatabase
    from src.agent.llm_factory import get_llm
    from src.agent.tools import query_kg

    uri = os.getenv("NEO4J_URI")
    user = os.getenv("NEO4J_USERNAME", "neo4j")
    pw = os.getenv("NEO4J_PASSWORD")
    if not uri or not pw:
        print("FAIL: NEO4J_URI / NEO4J_PASSWORD missing")
        return 1

    driver = GraphDatabase.driver(uri, auth=(user, pw))
    driver.verify_connectivity()
    with driver.session() as s:
        nodes = s.run("MATCH (n) RETURN count(n) AS c").single()["c"]
        rels = s.run("MATCH ()-[r]->() RETURN count(r) AS c").single()["c"]
    driver.close()
    print(f"neo4j_ok nodes={nodes} rels={rels}")

    kg = query_kg("MATCH (d:Disease) RETURN count(d) AS n LIMIT 1")
    assert '"n": 797' in kg or '"n":' in kg, kg
    print("query_kg_ok", kg[:120].replace("\n", " "))

    if (os.getenv("OPENROUTER_API_KEY") or "").strip():
        llm = get_llm("openrouter")
        tag = "openrouter"
    elif os.getenv("GEMINI_API_KEY"):
        llm = get_llm("gemini")
        tag = "gemini_fallback"
    elif os.getenv("OPENAI_API_KEY"):
        llm = get_llm("openai")
        tag = "openai_fallback"
    else:
        print("FAIL: no LLM key")
        return 1

    ans = llm.chat("Reply with exactly: OK", context="")
    print(f"llm_ok provider={tag} model={llm.model} ans={ans[:80]!r}")
    if tag != "openrouter":
        print("NOTE: set OPENROUTER_API_KEY in .env to smoke Gemma via OpenRouter")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
