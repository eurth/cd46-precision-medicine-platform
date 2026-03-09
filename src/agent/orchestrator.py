"""
LangGraph-based AI orchestrator for CD46 Precision Medicine Platform.

State machine:
  route_question → load_context → generate_answer → format_response
                              ↘ query_kg ↗
"""
from __future__ import annotations

import json
import logging
import re
from typing import Any, TypedDict

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Agent State
# ---------------------------------------------------------------------------

class AgentState(TypedDict):
    question: str
    intent: str          # classified intent
    context: str         # retrieved data context
    kg_results: str      # raw KG query results
    answer: str          # final LLM answer
    sources: list[str]   # data sources used


# ---------------------------------------------------------------------------
# Intent classification
# ---------------------------------------------------------------------------

INTENTS = {
    "eligibility": [
        "eligib", "how many patient", "225Ac", "candidate", "threshold",
        "treatment candidate", "fraction", "percent eligible",
    ],
    "survival": [
        "survival", "hazard ratio", "kaplan", "km curve", "prognosis",
        "overall survival", "progression", "cox", "log rank",
    ],
    "expression": [
        "express", "mrna", "log2", "tpm", "tumor vs normal", "tissue",
        "protein level", "hpa", "overexpress",
    ],
    "drug": [
        "drug", "therapy", "treatment", "225ac", "abbv", "losatux",
        "docetaxel", "enzalutamide", "psma", "adt", "chemotherapy",
    ],
    "trial": [
        "trial", "nct", "clinical", "phase i", "phase ii", "recruit",
        "enrolling", "sponsor",
    ],
    "knowledge_graph": [
        "knowledge graph", "kg", "node", "edge", "relationship",
        "cypher", "neo4j", "graph",
    ],
    "biomarker": [
        "biomarker", "marker", "predictive", "complement", "cd55", "cd59", "ar-v7",
        "tp53", "rb1", "resistance", "precision medicine", "patient selection",
        "combination", "co-target", "scoring",
    ],
    "protein": [
        "protein", "structure", "alphafold", "uniprot", "isoform", "domain",
        "string", "interaction", "network", "complement pathway", "p15529",
    ],
    "literature": [
        "pubmed", "paper", "publication", "study", "journal", "research",
        "article", "cited", "reference", "evidence", "published",
    ],
    "general": [],  # fallback
}


def _classify_intent(question: str) -> str:
    q_lower = question.lower()
    for intent, keywords in INTENTS.items():
        if intent == "general":
            continue
        if any(kw in q_lower for kw in keywords):
            return intent
    return "general"


# ---------------------------------------------------------------------------
# Context loaders (call tools.py functions)
# ---------------------------------------------------------------------------

def _load_context_for_intent(intent: str, question: str) -> tuple[str, list[str]]:
    """Load relevant data context based on intent. Returns (context_str, sources)."""
    from src.agent.tools import (
        get_eligibility,
        load_csv_data,
        run_analysis_summary,
        search_trials,
        search_pubmed,
    )

    contexts = []
    sources = []

    if intent == "eligibility":
        result = get_eligibility("PRAD", "75th_pct")
        contexts.append(f"PRAD eligibility (75th pct):\n{result}")
        result2 = run_analysis_summary("top_eligible")
        contexts.append(f"Top eligible cancers:\n{result2}")
        sources += ["patient_groups.csv", "TCGA"]

    elif intent == "survival":
        result = run_analysis_summary("survival_significant")
        contexts.append(f"Significant survival associations:\n{result}")
        result2 = load_csv_data("survival", top_n=10)
        contexts.append(f"Survival data sample:\n{result2}")
        sources += ["cd46_survival_results.csv", "TCGA KM/Cox"]

    elif intent == "expression":
        result = load_csv_data("by_cancer", top_n=33)
        contexts.append(f"Pan-cancer expression:\n{result}")
        result2 = load_csv_data("hpa", top_n=30)
        contexts.append(f"HPA protein expression:\n{result2}")
        sources += ["TCGA/Xena", "Human Protein Atlas"]

    elif intent == "drug":
        result = load_csv_data("combination", top_n=20)
        contexts.append(f"Combination biomarker correlations:\n{result}")
        result2 = run_analysis_summary("priority")
        contexts.append(f"Cancer priority scores:\n{result2}")
        sources += ["ChEMBL", "cBioPortal", "cd46_combination_biomarkers.csv"]

    elif intent == "trial":
        result = search_trials("CD46")
        contexts.append(f"Relevant clinical trials:\n{result}")
        sources += ["ClinicalTrials.gov"]

    elif intent == "knowledge_graph":
        from src.agent.tools import query_kg
        result = query_kg(
            "MATCH (g:Gene)-[:EXPRESSED_IN]->(d:Disease) "
            "RETURN d.tcga_code AS cancer, d.cd46_priority_score AS priority "
            "ORDER BY priority DESC LIMIT 10"
        )
        contexts.append(f"KG priority scores:\n{result}")
        sources += ["AuraDB Knowledge Graph"]

    elif intent == "biomarker":
        result = load_csv_data("combination", top_n=20)
        contexts.append(f"CD46 combination biomarker correlations:\n{result}")
        result2 = run_analysis_summary("priority")
        contexts.append(f"Cancer priority scores with biomarker context:\n{result2}")
        result3 = load_csv_data("by_cancer", top_n=15)
        contexts.append(f"CD46 expression by cancer type:\n{result3}")
        sources += ["cd46_combination_biomarkers.csv", "TCGA", "SU2C mCRPC"]

    elif intent == "protein":
        result = load_csv_data("hpa", top_n=30)
        contexts.append(f"CD46 protein expression (Human Protein Atlas):\n{result}")
        result2 = load_csv_data("combination", top_n=15)
        contexts.append(f"Protein interaction biomarkers:\n{result2}")
        sources += ["Human Protein Atlas", "UniProt P15529", "AlphaFold EBI"]

    elif intent == "literature":
        pubmed_result = search_pubmed(f"CD46 {question[:80]}")
        contexts.append(f"PubMed literature:\n{pubmed_result}")
        sources += ["PubMed / NCBI"]

    else:  # general
        result = run_analysis_summary("priority")
        contexts.append(f"CD46 priority overview:\n{result}")
        sources += ["All datasets"]

    # Always append fresh PubMed context for non-literature intents
    if intent != "literature":
        try:
            pubmed_query = f"CD46 {intent} prostate cancer 225Ac therapy"
            pub_raw = search_pubmed(pubmed_query, max_results=4)
            import json as _json
            pub_data = _json.loads(pub_raw)
            if pub_data.get("formatted_context"):
                contexts.append(pub_data["formatted_context"])
                sources.append("PubMed / NCBI")
        except Exception as _e:
            logger.debug("PubMed context append skipped: %s", _e)

    return "\n\n".join(contexts), sources


# ---------------------------------------------------------------------------
# Graph nodes
# ---------------------------------------------------------------------------

def route_question(state: AgentState) -> AgentState:
    intent = _classify_intent(state["question"])
    logger.info("Intent classified: %s", intent)
    return {**state, "intent": intent}


def load_context(state: AgentState) -> AgentState:
    context, sources = _load_context_for_intent(state["intent"], state["question"])
    return {**state, "context": context, "sources": sources}


def generate_answer(state: AgentState, llm=None) -> AgentState:
    if llm is None:
        from src.agent.llm_factory import get_llm
        llm = get_llm()

    answer = llm.chat(state["question"], context=state["context"])
    return {**state, "answer": answer}


def format_response(state: AgentState) -> AgentState:
    sources_str = ", ".join(state.get("sources", []))
    formatted = state["answer"]
    if sources_str:
        formatted += f"\n\n---\n*Sources: {sources_str}*"
    return {**state, "answer": formatted}


# ---------------------------------------------------------------------------
# Orchestrator — runs without LangGraph dependency if unavailable
# ---------------------------------------------------------------------------

class CD46Agent:
    """
    CD46 AI agent. Uses LangGraph StateGraph when available,
    falls back to sequential execution otherwise.
    """

    def __init__(self, provider: str = "auto"):
        from src.agent.llm_factory import get_llm
        self.llm = get_llm(provider=provider)
        self._graph = self._build_graph()

    def _build_graph(self):
        try:
            from langgraph.graph import StateGraph, END

            graph = StateGraph(AgentState)
            graph.add_node("route_question", route_question)
            graph.add_node("load_context", load_context)
            graph.add_node("generate_answer", lambda s: generate_answer(s, self.llm))
            graph.add_node("format_response", format_response)

            graph.set_entry_point("route_question")
            graph.add_edge("route_question", "load_context")
            graph.add_edge("load_context", "generate_answer")
            graph.add_edge("generate_answer", "format_response")
            graph.add_edge("format_response", END)

            return graph.compile()
        except ImportError:
            logger.warning("LangGraph not available — using sequential fallback")
            return None

    def ask(self, question: str) -> str:
        """Ask a question and get an answer with context."""
        initial_state: AgentState = {
            "question": question,
            "intent": "",
            "context": "",
            "kg_results": "",
            "answer": "",
            "sources": [],
        }

        if self._graph is not None:
            result = self._graph.invoke(initial_state)
        else:
            # Sequential fallback
            state = route_question(initial_state)
            state = load_context(state)
            state = generate_answer(state, self.llm)
            state = format_response(state)
            result = state

        return result["answer"]

    def stream(self, question: str):
        """Stream the answer token by token (for Streamlit)."""
        # Load context first, then stream LLM response
        initial_state: AgentState = {
            "question": question,
            "intent": "",
            "context": "",
            "kg_results": "",
            "answer": "",
            "sources": [],
        }
        state = route_question(initial_state)
        state = load_context(state)

        yield from self.llm.stream(state["question"], context=state["context"])


# ---------------------------------------------------------------------------
# Preset Q&A for demo
# ---------------------------------------------------------------------------

PRESET_QUESTIONS = [
    "How many mCRPC patients are eligible for 225Ac-CD46 therapy at the 75th percentile threshold?",
    "Which cancer types show the strongest survival impact from high CD46 expression?",
    "Is CD46 expression correlated with PSMA in prostate cancer, and what does that mean therapeutically?",
    "What is the CD46 priority score for ovarian cancer and why?",
    "List the active clinical trials targeting CD46 in prostate cancer.",
    "How does CD46 expression in prostate tumor tissue compare to normal prostate in the HPA?",
]
