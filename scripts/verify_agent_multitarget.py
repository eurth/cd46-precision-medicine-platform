#!/usr/bin/env python3
"""ponytail: smoke check multi-target agent wiring."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "app"))

from components.agent_prompts import cab_questions, quick_start_questions, evidence_demo_rows
from src.agent.kg_retrieval import cypher_drugs, queries_for_intent
from src.agent.orchestrator import CD46Agent, TargetResearchAgent
from src.agent.tools import _gene_file_map, _resolve_dataset_df


def main() -> None:
    for sym in ("FOLH1", "FAP", "SSTR2", "GRPR", "CD46"):
        qs = quick_start_questions(sym)
        assert len(qs) == 6, sym
        assert sym in qs[1], qs[1]
        assert len(cab_questions(sym)) == 5
        demo = evidence_demo_rows(sym)
        assert sym in demo["Your Question"][0]
    assert "FOLH1" in cypher_drugs("FOLH1")
    assert len(queries_for_intent("trial", "FAP")) >= 1
    assert TargetResearchAgent is CD46Agent
    m = _gene_file_map("FAP")
    assert m["survival"] == "fap_survival_results.csv"
    df, _ = _resolve_dataset_df("survival", "FOLH1")
    # file may be absent locally; function must not throw
    print("verify_agent_multitarget_ok")


if __name__ == "__main__":
    main()
