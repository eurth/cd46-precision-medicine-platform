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
from components.ui_kit import page_header, section_tabs, research_table, info_banner
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
def _get_agent(provider: str):
    try:
        from src.agent.orchestrator import TargetResearchAgent
        return TargetResearchAgent(provider=provider), None
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

    agent, agent_error = _get_agent(provider)

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
                with st.spinner("Retrieving KG context + generating answer..."):
                    ph = st.empty()
                    full = ""
                    try:
                        for token in agent.stream(q):
                            full += token
                            ph.markdown(full + "▌")
                        ph.markdown(full)
                    except Exception as e:
                        full = f"Error: {e}"
                        ph.error(full)
                st.session_state.messages.append({"role": "assistant", "content": full})
                try:
                    from src.agent.pubmed_search import fetch_pubmed
                    arts = fetch_pubmed(f"{_GENE} {q[:80]}", max_results=5)
                    st.session_state.citations[len(st.session_state.messages) - 1] = arts
                except Exception:
                    pass
        st.rerun()

    # -----------------------------------------------------------------------
    # Replay existing conversation
    # -----------------------------------------------------------------------
    for idx, msg in enumerate(st.session_state.messages):
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
        if msg["role"] == "assistant" and idx in st.session_state.citations:
            arts = st.session_state.citations[idx]
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
        f"OncoBridge retrieves structured facts for the **active target** ({_GENE}) from CSVs and "
        f"Neo4j ({_kg_nodes} nodes) before the model writes an answer. Every claim should map to a source.",
        variant="success",
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
    st.markdown("#### Knowledge Graph Evidence Base — What the Agent Knows")
    st.caption(
        "The following evidence is pre-loaded into the Neo4j knowledge graph "
        "and is retrievable by the research assistant for every query."
    )

    ev1, ev2 = st.columns(2)

    with ev1:
        st.markdown(
            "<div style='background:#1e293b;border:1px solid #334155;"
            "padding:16px;border-radius:8px;margin-bottom:12px;'>"
            "<b style='color:#38bdf8;'>TCGA Expression + Survival</b><br>"
            "<span style='color:#94a3b8;font-size:0.88em;'>"
            "25 cancer types · CD46 mRNA log2 expression · "
            "Cox proportional hazard ratios · p-values · "
            "Expression tertile classification<br>"
            "<b style='color:#cbd5e1;'>Top signals:</b> CESC HR=3.42, LGG HR=1.94, "
            "SKCM HR=0.59 (protective), KIRC HR=0.44"
            "</span></div>",
            unsafe_allow_html=True,
        )
        st.markdown(
            "<div style='background:#1e293b;border:1px solid #334155;"
            "padding:16px;border-radius:8px;margin-bottom:12px;'>"
            "<b style='color:#4ade80;'>GENIE Patient Cohorts</b><br>"
            "<span style='color:#94a3b8;font-size:0.88em;'>"
            "271,176 real-world patients · 23 cancer types · "
            "CD46-High/Low cohorts at median, 75th, 90th percentile · "
            "Somatic mutation context · PTEN/TP53/AR co-alteration data"
            "</span></div>",
            unsafe_allow_html=True,
        )
        st.markdown(
            "<div style='background:#1e293b;border:1px solid #334155;"
            "padding:16px;border-radius:8px;margin-bottom:12px;'>"
            "<b style='color:#fbbf24;'>Drug Pipeline</b><br>"
            "<span style='color:#94a3b8;font-size:0.88em;'>"
            "10 CD46-targeting agents · Modalities: 225Ac-RLT, ADC, BiTE, mAb · "
            "14 active clinical trials (ClinicalTrials.gov) · "
            "NCT IDs, phase, sponsor, primary endpoint"
            "</span></div>",
            unsafe_allow_html=True,
        )
        st.markdown(
            "<div style='background:#1e293b;border:1px solid #334155;"
            "padding:16px;border-radius:8px;'>"
            "<b style='color:#f87171;'>Disease Associations</b><br>"
            "<span style='color:#94a3b8;font-size:0.88em;'>"
            "797 Open Targets disease associations · "
            "Hematologic, immune, oncology, infectious, genetic linkages · "
            "Scored 0–1 (OT data-driven association score)"
            "</span></div>",
            unsafe_allow_html=True,
        )

    with ev2:
        st.markdown(
            "<div style='background:#1e293b;border:1px solid #334155;"
            "padding:16px;border-radius:8px;margin-bottom:12px;'>"
            "<b style='color:#a78bfa;'>DepMap Cell Lines (1,186)</b><br>"
            "<span style='color:#94a3b8;font-size:0.88em;'>"
            "CRISPR knockout fitness scores · mRNA expression · "
            "25 cancer lineages · "
            "CD46 essentiality flags for pan-cancer dependency analysis"
            "</span></div>",
            unsafe_allow_html=True,
        )
        st.markdown(
            "<div style='background:#1e293b;border:1px solid #334155;"
            "padding:16px;border-radius:8px;margin-bottom:12px;'>"
            "<b style='color:#1E293B;'>Protein Structural Biology</b><br>"
            "<span style='color:#94a3b8;font-size:0.88em;'>"
            "UniProt P15529 · 4 isoforms (STA-1/2, LCA-1/2) · "
            "392 aa canonical sequence · 4 SCR/Sushi complement-binding domains · "
            "STRING protein interaction network (25 partners)"
            "</span></div>",
            unsafe_allow_html=True,
        )
        st.markdown(
            "<div style='background:#1e293b;border:1px solid #334155;"
            "padding:16px;border-radius:8px;margin-bottom:12px;'>"
            "<b style='color:#34d399;'>PubMed Publications (55)</b><br>"
            "<span style='color:#94a3b8;font-size:0.88em;'>"
            "Curated evidence base · "
            "Evidence types: Experimental, Clinical trial, Biomarker, Preclinical, Review · "
            "Full metadata: title, authors, journal, year, key finding"
            "</span></div>",
            unsafe_allow_html=True,
        )
        st.markdown(
            "<div style='background:#1e293b;border:1px solid #334155;"
            "padding:16px;border-radius:8px;'>"
            "<b style='color:#38bdf8;'>HPA / GTEx Tissue Expression</b><br>"
            "<span style='color:#94a3b8;font-size:0.88em;'>"
            "54 GTEx tissue sites · HPA tumour vs normal classification · "
            "CD46 protein localisation data · "
            "Therapeutic window analysis nodes"
            "</span></div>",
            unsafe_allow_html=True,
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
