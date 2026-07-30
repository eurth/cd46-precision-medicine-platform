"""
LangGraph-based AI orchestrator for OncoBridge multi-target research assistant.

State machine:
  route_question → load_context → generate_answer → format_response
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

def _active_gene() -> str:
    """Prefer Streamlit session target; fall back to CD46."""
    try:
        from components.targets import get_active_symbol
        return get_active_symbol()
    except Exception:
        return "CD46"


def _append_kg_context(contexts: list[str], sources: list[str], intent: str, gene: str) -> None:
    """Additive KG retrieval — keeps CSV context; does not replace it."""
    from src.agent.kg_retrieval import queries_for_intent
    from src.agent.tools import query_kg

    for label, cypher in queries_for_intent(intent, gene):
        result = query_kg(cypher)
        contexts.append(f"KG — {label} ({gene}):\n{result}")
    sources.append("AuraDB Knowledge Graph")


def _load_context_for_intent(intent: str, question: str) -> tuple[str, list[str]]:
    """Load relevant data context based on intent. Returns (context_str, sources)."""
    from src.agent.tools import (
        get_eligibility,
        load_csv_data,
        run_analysis_summary,
        search_trials,
        search_pubmed,
    )

    gene = _active_gene()
    contexts = []
    sources = []

    if intent == "eligibility":
        result = get_eligibility("PRAD", "75th_pct")
        contexts.append(f"PRAD eligibility (75th pct, {gene}):\n{result}")
        result2 = run_analysis_summary("top_eligible")
        contexts.append(f"Top eligible cancers:\n{result2}")
        sources += [f"{gene.lower()}_patient_groups.csv", "TCGA"]

    elif intent == "survival":
        result = run_analysis_summary("survival_significant")
        contexts.append(f"Significant survival associations:\n{result}")
        result2 = load_csv_data("survival", top_n=10)
        contexts.append(f"Survival data sample:\n{result2}")
        sources += [f"{gene.lower()}_survival_results.csv", "TCGA KM/Cox"]

    elif intent == "expression":
        result = load_csv_data("by_cancer", top_n=33)
        contexts.append(f"Pan-cancer expression ({gene}):\n{result}")
        result2 = load_csv_data("hpa", top_n=30)
        contexts.append(f"HPA protein expression ({gene}):\n{result2}")
        sources += ["TCGA/Xena", "Human Protein Atlas"]

    elif intent == "drug":
        result = load_csv_data("combination", top_n=20)
        if "error" not in result:
            contexts.append(f"Combination biomarker correlations:\n{result}")
        result2 = run_analysis_summary("priority")
        contexts.append(f"Cancer priority / expression ranking:\n{result2}")
        result3 = load_csv_data("by_cancer", top_n=15)
        contexts.append(f"Pan-cancer expression ({gene}):\n{result3}")
        sources += ["ChEMBL", "cBioPortal", f"{gene.lower()}_by_cancer.csv"]

    elif intent == "trial":
        result = search_trials(gene)
        contexts.append(f"Relevant clinical trials ({gene}):\n{result}")
        sources += ["ClinicalTrials.gov"]

    elif intent == "knowledge_graph":
        pass  # KG-only intent — filled by _append_kg_context below

    elif intent == "biomarker":
        result = load_csv_data("combination", top_n=20)
        if "error" not in result:
            contexts.append(f"{gene} combination biomarker correlations:\n{result}")
        result2 = run_analysis_summary("priority")
        contexts.append(f"Cancer priority scores with biomarker context:\n{result2}")
        result3 = load_csv_data("by_cancer", top_n=15)
        contexts.append(f"{gene} expression by cancer type:\n{result3}")
        sources += [f"{gene.lower()}_combination_biomarkers.csv", "TCGA", "SU2C mCRPC"]

    elif intent == "protein":
        result = load_csv_data("hpa", top_n=30)
        contexts.append(f"{gene} protein expression (Human Protein Atlas):\n{result}")
        if "error" in result:
            result_alt = load_csv_data("hpa_intensity", top_n=30)
            contexts.append(f"{gene} HPA intensity:\n{result_alt}")
        result2 = load_csv_data("depmap", top_n=15)
        if "error" not in result2:
            contexts.append(f"DepMap essentiality ({gene}):\n{result2}")
        sources += ["Human Protein Atlas", "UniProt", "DepMap", "AlphaFold EBI"]

    elif intent == "literature":
        pubmed_result = search_pubmed(f"{gene} {question[:80]}")
        contexts.append(f"PubMed literature:\n{pubmed_result}")
        sources += ["PubMed / NCBI"]

    else:  # general
        result = run_analysis_summary("priority")
        contexts.append(f"{gene} priority / expression overview:\n{result}")
        result2 = load_csv_data("by_cancer", top_n=12)
        contexts.append(f"Pan-cancer expression ({gene}):\n{result2}")
        sources += ["TCGA/Xena", "All datasets"]

    # Additive KG context for every intent (gene-aware Cypher templates)
    _append_kg_context(contexts, sources, intent, gene)

    # Always append fresh PubMed context for non-literature intents
    if intent != "literature":
        try:
            pubmed_query = f"{gene} {intent} cancer theranostics"
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

class TargetResearchAgent:
    """
    Multi-target research agent. Uses LangGraph when available,
    sequential fallback otherwise.
    """

    def __init__(self, provider: str = "auto"):
        from src.agent.llm_factory import get_llm
        self.llm = get_llm(provider=provider)
        self._graph = self._build_graph()
        self.last_sources: list[str] = []
        self.last_intent: str = ""

    def retrieve(self, question: str) -> tuple[str, list[str], str]:
        """Load RAG context without calling the LLM (for source chips + streaming)."""
        state = route_question({"question": question, "intent": "", "context": "",
                                "kg_results": "", "answer": "", "sources": []})
        state = load_context(state)
        self.last_sources = list(state.get("sources") or [])
        self.last_intent = str(state.get("intent") or "")
        return state["context"], self.last_sources, self.last_intent

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
        context, sources, _intent = self.retrieve(question)
        yield from self.llm.stream(question, context=context)


# Back-compat alias — do not remove (pipeline + imports)
CD46Agent = TargetResearchAgent


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
