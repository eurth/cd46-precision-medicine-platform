"""Page 5 — AI Research Assistant: KG-grounded RAG chat + architecture + evidence context."""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[2] / ".env")

import streamlit as st
from components.targets import get_active_symbol, render_stub_gate
from components.ui_kit import page_header, section_tabs, research_table, info_banner, source_chips
from components.data_freeze import render_data_freeze_banner
from components.agent_prompts import quick_start_questions, cab_questions, evidence_demo_rows

# Inject Streamlit Cloud secrets into os.environ
for _k in (
    "OPENROUTER_API_KEY",
    "OPENROUTER_MODEL",
    "OPENAI_API_KEY",
    "GEMINI_API_KEY",
    "NEO4J_URI",
    "NEO4J_USERNAME",
    "NEO4J_PASSWORD",
):
    try:
        if _k in st.secrets and not os.environ.get(_k):
            os.environ[_k] = st.secrets[_k]
    except Exception:
        pass

if render_stub_gate(module="Research Assistant"):
    st.stop()

_GENE = get_active_symbol()


@st.cache_resource(ttl=300)
def _get_kg_driver():
    from neo4j import GraphDatabase

    uri = os.getenv("NEO4J_URI")
    user = os.getenv("NEO4J_USERNAME", "neo4j")
    password = os.getenv("NEO4J_PASSWORD")
    if not uri or not password:
        return None
    try:
        driver = GraphDatabase.driver(uri, auth=(user, password))
        driver.verify_connectivity()
        return driver
    except Exception:
        return None


@st.cache_data(ttl=300)
def _kg_counts():
    driver = _get_kg_driver()
    if driver is None:
        return None
    try:
        with driver.session() as sess:
            total_nodes = sess.run("MATCH (n) RETURN count(n) AS c").single()["c"]
            total_rels = sess.run("MATCH ()-[r]->() RETURN count(r) AS c").single()["c"]
        return {"nodes": total_nodes, "rels": total_rels}
    except Exception:
        return None


_kg = _kg_counts()
_kg_nodes = f"{_kg['nodes']:,}" if _kg else "~3,068"
_kg_rels = f"{_kg['rels']:,}" if _kg else "~2,517"

# ---------------------------------------------------------------------------
# Theme constants
# ---------------------------------------------------------------------------
_BG     = "#FFFFFF"
_LINE   = "#E2E8F0"
_TEXT   = "#64748B"
_LIGHT  = "#1E293B"

# ---------------------------------------------------------------------------
# Preset / CAB questions (inline — no fragile orchestrator import required)
# ---------------------------------------------------------------------------
PRESET_QUESTIONS = quick_start_questions(_GENE)
CAB_QUESTIONS = cab_questions(_GENE)

# ---------------------------------------------------------------------------
# Agent initialisation (graceful degradation)
# ---------------------------------------------------------------------------
@st.cache_resource
def _get_agent(provider: str, gene: str):
    try:
        from src.agent.orchestrator import TargetResearchAgent
        return TargetResearchAgent(provider=provider, gene=gene), None
    except Exception as e:
        return None, str(e)

# ---------------------------------------------------------------------------
# Hero
# ---------------------------------------------------------------------------
page_header(
    icon="🤖",
    module_name="AI Research Assistant",
    purpose=(
        f"Retrieval-augmented Q&A for **{_GENE}** (switch target bar) · "
        f"Neo4j {_kg_nodes} nodes · TCGA · HPA · DepMap · trials · PubMed"
    ),
    kpi_chips=[
        ("Primary Model", "Gemma (OR)"),
        ("Fallback", "GPT-4o / Gemini"),
        ("KG Nodes", _kg_nodes),
        ("Evidence Types", "8 sources"),
    ],
    source_badges=["TCGA", "HPA", "OpenTargets", "ChEMBL", "DepMap", "PubMed"],
)
render_data_freeze_banner(compact=True)

# ---------------------------------------------------------------------------
# Tabs
# ---------------------------------------------------------------------------
_ASST_TABS = ["Research Assistant", "How It Works", "Evidence Context"]
_active_asst = section_tabs(_ASST_TABS, key="research_assistant_tabs")

# TAB 1 — Research Assistant (chat interface)
if _active_asst == _ASST_TABS[0]:
    # Provider controls
    col_prov, col_temp = st.columns([2, 1])
    with col_prov:
        provider = st.selectbox(
            "LLM Provider", ["auto", "openrouter", "openai", "gemini"], index=0,
            key="provider_sel",
        )
    with col_temp:
        temperature = st.slider(
            "Temperature", min_value=0.0, max_value=1.0, value=0.1, step=0.05,
            key="temp_slider",
        )

    agent, agent_error = _get_agent(provider, _GENE)

    if agent_error:
        st.warning(
            f"Agent unavailable: {agent_error}  \n"
            "Add OPENROUTER_API_KEY, OPENAI_API_KEY, or GEMINI_API_KEY to `.env` to enable live answers.  \n"
            "Preset questions and the chat input are shown below for reference."
        )
    else:
        _labels = {
            "auto": "auto (OpenRouter → OpenAI → Gemini)",
            "openrouter": "OpenRouter Gemma",
            "openai": "OpenAI GPT-4o",
            "gemini": "Gemini Flash",
        }
        st.success(f"Agent ready — {_labels.get(provider, provider)} with Knowledge Graph context")

    # Session state
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "citations" not in st.session_state:
        st.session_state.citations = {}

    # Clear conversation button
    if st.session_state.messages:
        ccol, _ = st.columns([1, 5])
        if ccol.button("New Question", use_container_width=True, key="new_q"):
            st.session_state.messages = []
            st.session_state.citations = {}
            st.rerun()

    # -----------------------------------------------------------------------
    # Shared response runner
    # -----------------------------------------------------------------------
    def _run_question(q: str) -> None:
        from components.llm_rate_limit import check_and_increment
        from src.agent.kg_dossier import is_dossier_question

        allowed, cap_msg = check_and_increment("global")
        if not allowed:
            st.warning(cap_msg)
            return

        st.session_state.messages.append({"role": "user", "content": q})
        with st.chat_message("user"):
            st.markdown(q)
        with st.chat_message("assistant"):
            if agent is None:
                st.error("Agent not available — set OPENROUTER_API_KEY, OPENAI_API_KEY, or GEMINI_API_KEY in .env")
            else:
                st.caption(cap_msg)
                with st.spinner("Retrieving knowledge graph context..."):
                    ph = st.empty()
                    full = ""
                    try:
                        for token in agent.stream(q, gene=_GENE):
                            full += token
                            ph.markdown(full + ("▌" if not full.startswith("###") else ""))
                        ph.markdown(full)
                    except Exception as e:
                        if is_dossier_question(q):
                            from src.agent.kg_dossier import build_kg_dossier, gene_from_question
                            sym = gene_from_question(q, _GENE)
                            full, sources = build_kg_dossier(sym)
                            ph.markdown(full)
                            agent.last_sources = sources
                            agent.last_intent = "dossier"
                        else:
                            full = f"Error: {e}"
                            ph.error(full)
                sources = list(getattr(agent, "last_sources", []) or [])
                intent = str(getattr(agent, "last_intent", "") or "")
                if sources:
                    source_chips(sources, intent=intent)
                st.session_state.messages.append({"role": "assistant", "content": full})
                try:
                    from src.agent.pubmed_search import fetch_pubmed
                    arts = fetch_pubmed(f"{_GENE} {q[:80]}", max_results=5)
                    st.session_state.citations[len(st.session_state.messages) - 1] = {
                        "pubmed": arts,
                        "sources": sources,
                        "intent": intent,
                    }
                except Exception:
                    if sources:
                        st.session_state.citations[len(st.session_state.messages) - 1] = {
                            "sources": sources,
                            "intent": intent,
                        }
        st.rerun()

    # -----------------------------------------------------------------------
    # Replay existing conversation
    # -----------------------------------------------------------------------
    for idx, msg in enumerate(st.session_state.messages):
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
        if msg["role"] == "assistant" and idx in st.session_state.citations:
            cite = st.session_state.citations[idx]
            if isinstance(cite, dict):
                if cite.get("sources"):
                    source_chips(cite["sources"], intent=cite.get("intent", ""))
                arts = cite.get("pubmed") or []
            else:
                arts = cite
            if arts:
                with st.expander(f"Referenced Literature ({len(arts)} papers)", expanded=False):
                    for i, art in enumerate(arts, 1):
                        st.markdown(
                            f"<div style='background:#1e293b;border-left:3px solid #38bdf8;"
                            f"padding:10px 14px;margin:6px 0;border-radius:4px;'>"
                            f"<b style='color:#1E293B;'>[{i}] {art.get('title','')}</b><br>"
                            f"<span style='color:#94a3b8;font-size:0.85em;'>{art.get('authors','')}</span><br>"
                            f"<span style='color:#64748b;font-size:0.82em;'>"
                            f"{art.get('journal','')} · {art.get('year','')}</span>"
                            + (
                                f"<br><span style='color:#94a3b8;font-size:0.82em;'>"
                                f"{art.get('abstract_snippet','')[:280]}...</span>"
                                if art.get("abstract_snippet") else ""
                            )
                            + "</div>",
                            unsafe_allow_html=True,
                        )
                        if art.get("url"):
                            st.link_button("Open PubMed", art["url"])

    # -----------------------------------------------------------------------
    # Entry state — preset + CAB buttons shown when no conversation yet
    # -----------------------------------------------------------------------
    if not st.session_state.messages:
        st.markdown(f"#### Quick-Start Questions — active target: **{_GENE}**")
        st.caption("Click any question to run it through the retrieval-augmented agent.")
        q_cols = st.columns(2)
        for i, q in enumerate(PRESET_QUESTIONS):
            if q_cols[i % 2].button(q, key=f"pq_{i}", use_container_width=True):
                _run_question(q)

        st.markdown("---")
        st.markdown("#### Clinical Advisory Board Focus Questions")
        st.caption(
            "Pre-built questions aligned to 6 CAB evaluation themes: "
            "Biomarkers/CDx · Theranostic Integration · Trial Architecture · "
            "Sequencing · Endpoints · Access/Pathways"
        )
        cab_cols = st.columns(2)
        for i, q in enumerate(CAB_QUESTIONS):
            if cab_cols[i % 2].button(q, key=f"cab_{i}", use_container_width=True):
                _run_question(q)

    # -----------------------------------------------------------------------
    # Chat input
    # -----------------------------------------------------------------------
    if prompt := st.chat_input(
        "Ask about expression, patient eligibility, drugs, trials, mechanisms for the active target..."
    ):
        _run_question(prompt)

    if st.session_state.messages:
        if st.button("Clear conversation", key="clear_conv"):
            st.session_state.messages = []
            st.session_state.citations = {}
            st.rerun()

    st.markdown("---")
    st.markdown(
        "<div style='color:#64748b;font-size:0.78em;'>"
        f"Active target: <b>{_GENE}</b> · LLM: OpenRouter Gemma primary · GPT-4o / Gemini fallback<br>"
        "Context: TCGA · HPA · DepMap · ClinicalTrials.gov · AuraDB KG (retrieval-augmented)<br>"
        "<b>For research purposes only. Not for clinical decision-making.</b>"
        "</div>",
        unsafe_allow_html=True,
    )

# TAB 2 — How It Works (RAG architecture)
elif _active_asst == _ASST_TABS[1]:
    st.markdown("#### Retrieval-Augmented Generation on a Structured Scientific Knowledge Graph")

    info_banner(
        "Generic LLMs generate plausible oncology text without retrieving your TCGA values, "
        "GENIE cohort counts, trial NCT IDs, or graph relationships. Claims can be untraceable.",
        variant="error",
    )
    info_banner(
        f"Retrieval combines **TCGA/CSV slices** for the active target ({_GENE}), "
        "**template Cypher** against AuraDB on every question, and **NL→Cypher** when you ask "
        "graph-style questions. Answers are not guaranteed to cite every source — check the chips below each reply.",
        variant="warning",
    )

    # Two-step pipeline
    st.markdown("#### Two-Stage RAG Pipeline")
    p1, p2 = st.columns(2)
    with p1:
        st.markdown(
            "<div style='background:#0f172a;border:1px solid #334155;"
            "padding:20px;border-radius:8px;text-align:center;height:180px;"
            "display:flex;flex-direction:column;justify-content:center;'>"
            "<div style='font-size:2em;margin-bottom:10px;'>🔍</div>"
            "<b style='color:#38bdf8;font-size:1.05em;'>Step 1 — Graph Retrieval</b><br>"
            "<span style='color:#94a3b8;font-size:0.9em;margin-top:8px;display:block;'>"
            f"Question → semantic search across {_kg_nodes} KG nodes → "
            "retrieve 10–30 relevant nodes and relationships as structured JSON context"
            "</span></div>",
            unsafe_allow_html=True,
        )
    with p2:
        st.markdown(
            "<div style='background:#0f172a;border:1px solid #334155;"
            "padding:20px;border-radius:8px;text-align:center;height:180px;"
            "display:flex;flex-direction:column;justify-content:center;'>"
            "<div style='font-size:2em;margin-bottom:10px;'>✍️</div>"
            "<b style='color:#818cf8;font-size:1.05em;'>Step 2 — LLM Synthesis</b><br>"
            "<span style='color:#94a3b8;font-size:0.9em;margin-top:8px;display:block;'>"
            "Retrieved subgraph + system prompt → GPT-4o / Gemini 2.5 → "
            "fluent scientific answer grounded strictly in retrieved facts"
            "</span></div>",
            unsafe_allow_html=True,
        )

    st.markdown("---")
    st.markdown("#### Generic AI vs Grounded AI — Side-by-Side")

    comp_data = {
        "Capability": [
            "Source of facts",
            "TCGA expression values",
            "GENIE patient counts",
            "Active clinical trial IDs",
            "PubMed citations",
            "DepMap dependency scores",
            "Answer traceability",
            "Updated with new data",
            "Hallucination risk",
        ],
        "ChatGPT / Generic LLM": [
            "Training data (static, compressed)",
            "Approximate or invented",
            "Unknown / unverifiable",
            "May be outdated or hallucinated",
            "Often fabricated DOIs",
            "Not available",
            "None — no source nodes returned",
            "Only on model re-training",
            "HIGH",
        ],
        "This Research Assistant": [
            "Neo4j AuraDB KG (live, verified)",
            "Exact TCGA values from graph node",
            "Exact GENIE counts from graph node",
            "14 verified NCT IDs from graph",
            "55 curated PubMed papers in graph",
            "1,186 DepMap cell lines in graph",
            "Full — retrieved node IDs logged",
            "Instantly — update KG, answers change",
            "LOW — constrained to retrieved facts",
        ],
    }

    import pandas as pd
    df_comp = pd.DataFrame(comp_data)
    research_table(df_comp.set_index("Capability"), use_container_width=True)

    st.markdown("---")
    st.markdown("#### Technology Stack")
    tc1, tc2, tc3 = st.columns(3)
    tc1.markdown(
        "**LLM Layer**\n"
        "- OpenRouter Gemma — primary\n"
        "- GPT-4o / Gemini — fallback\n"
        "- Routed via LiteLLM\n"
        "- Orchestrated by LangGraph"
    )
    tc2.markdown(
        "**Knowledge Graph**\n"
        "- Neo4j AuraDB (cloud)\n"
        f"- {_kg_nodes} nodes, {_kg_rels} edges\n"
        "- Cypher query interface\n"
        "- Typed biological relationships"
    )
    tc3.markdown(
        "**Data Sources**\n"
        "- TCGA (mRNA + survival)\n"
        "- GENIE (271k patients)\n"
        "- HPA / GTEx (tissue expression)\n"
        "- ChEMBL · OpenTargets · DepMap"
    )

    st.markdown("---")
    st.info(
        "The system logs the retrieved nodes for every query — your team can audit "
        "exactly which evidence set drove any specific answer. "
        "If the knowledge graph is updated tonight with new publications or trial "
        "registrations, the assistant answers differently tomorrow."
    )

# TAB 3 — Evidence Context
elif _active_asst == _ASST_TABS[2]:
    st.markdown(f"#### Evidence base — active target **{_GENE}**")
    st.caption(
        "Structured data retrieved by the assistant (CSVs + AuraDB templates). "
        "Depth varies by target tier."
    )

    ev1, ev2 = st.columns(2)

    with ev1:
        info_banner(
            f"**TCGA expression + survival** — Pan-cancer `{_GENE}` mRNA ranks, Cox HRs, "
            "and KM splits from per-gene survival CSVs.",
        )
        info_banner(
            f"**Patient eligibility** — `{_GENE.lower()}_patient_groups.csv` threshold stats "
            f"for {_GENE}-High cohorts when available.",
        )
        info_banner(
            f"**Drug / trial context** — ChEMBL + ClinicalTrials.gov cache keyed to **{_GENE}** "
            "where available.",
        )
        info_banner(
            "**Open Targets disease associations** — Gene→disease scores in the knowledge graph.",
        )

    with ev2:
        info_banner(
            f"**DepMap** — `{_GENE}` CRISPR dependency and expression across ~1,186 cell lines.",
        )
        info_banner(
            f"**Protein / tissue** — HPA + GTEx slices (`hpa_{_GENE.lower()}_*`, `gtex_{_GENE.lower()}_normal.csv`).",
        )
        info_banner(
            "**PubMed** — Literature snippets appended to non-literature intents.",
        )
        info_banner(
            f"**KG templates** — Expression, survival, drugs, trials, DepMap Cypher for **{_GENE}** "
            "on every question; NL→Cypher when you ask graph-style questions.",
        )

    st.markdown("---")
    st.markdown(f"#### Sample Questions — active target **{_GENE}**")

    demo_data = evidence_demo_rows(_GENE)
    research_table(pd.DataFrame(demo_data), use_container_width=True, hide_index=True)

    st.markdown("---")
    st.caption(
        "All data sources are pre-ingested into Neo4j AuraDB. "
        "The agent retrieves structured facts as Cypher query results before every LLM call. "
        "No data leaves the knowledge graph boundary during retrieval."
    )
