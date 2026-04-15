"""Page 5 — AI Research Assistant: KG-grounded RAG chat + architecture + evidence context."""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[2] / ".env")

import streamlit as st
from components.styles import page_hero

# Inject Streamlit Cloud secrets into os.environ
for _k in ("OPENAI_API_KEY", "GEMINI_API_KEY", "NEO4J_URI", "NEO4J_USERNAME", "NEO4J_PASSWORD"):
    try:
        if _k in st.secrets and not os.environ.get(_k):
            os.environ[_k] = st.secrets[_k]
    except Exception:
        pass

# ---------------------------------------------------------------------------
# Theme constants
# ---------------------------------------------------------------------------
_BG    = "#0D1829"
_LINE  = "#16243C"
_TEXT  = "#94A3B8"
_LIGHT = "#CBD5E1"

# ---------------------------------------------------------------------------
# Preset / CAB questions (inline — no fragile orchestrator import required)
# ---------------------------------------------------------------------------
PRESET_QUESTIONS = [
    "Which cancers have the strongest combination of CD46 over-expression and survival impact?",
    "What is the current CD46-targeted drug pipeline and which agents are in clinical trials?",
    "How does CD46 regulate complement evasion in tumour cells?",
    "What DepMap evidence supports CD46 as a cancer dependency?",
    "Summarise CD46 expression across TCGA cancer types with hazard ratios.",
    "What are the CD46 isoforms and which are most relevant for therapeutic targeting?",
]

CAB_QUESTIONS = [
    "Which cancers have the strongest case for 225Ac-CD46 RLT based on expression and survival?",
    "What is the optimal biomarker strategy for CD46 patient selection in a Phase I trial?",
    "How does CD46 compare to PSMA as a therapeutic target in mCRPC?",
    "Design a Phase I dose-escalation trial for 225Ac-CD46 RLT in mCRPC — key elements?",
    "What is the complement evasion mechanism of CD46 and how does it drive tumour immune escape?",
    "Which CD46 isoforms are most relevant for antibody targeting and why does isoform selection matter?",
    "How does PTEN loss affect CD46 expression and what does that mean for patient selection?",
    "What clinical trial evidence exists for anti-CD46 therapies and what are the emerging readouts?",
]

# ---------------------------------------------------------------------------
# Agent initialisation (graceful degradation)
# ---------------------------------------------------------------------------
@st.cache_resource
def _get_agent(provider: str):
    try:
        from src.agent.orchestrator import CD46Agent
        return CD46Agent(provider=provider), None
    except Exception as e:
        return None, str(e)

# ---------------------------------------------------------------------------
# Hero
# ---------------------------------------------------------------------------
st.markdown(
    page_hero(
        icon="🤖",
        module_name="AI Research Assistant",
        purpose=(
            "KG-grounded RAG · GPT-4o primary · Gemini 2.5 Flash fallback · "
            "retrieves structured evidence from 3,912-node Neo4j knowledge graph "
            "before every answer — not generic AI"
        ),
        kpi_chips=[
            ("Primary Model",  "GPT-4o"),
            ("Fallback",       "Gemini 2.5"),
            ("KG Nodes",       "~3,912"),
            ("Evidence Types", "8 sources"),
        ],
        source_badges=["TCGA", "HPA", "OpenTargets", "ChEMBL", "DepMap", "PubMed"],
    ),
    unsafe_allow_html=True,
)
st.markdown("---")

# ---------------------------------------------------------------------------
# Tabs
# ---------------------------------------------------------------------------
tab_chat, tab_arch, tab_evidence = st.tabs([
    "Research Assistant",
    "How It Works",
    "Evidence Context",
])

# ==========================================================================
# TAB 1 — Research Assistant (chat interface)
# ==========================================================================
with tab_chat:
    # Provider controls
    col_prov, col_temp = st.columns([2, 1])
    with col_prov:
        provider = st.selectbox(
            "LLM Provider", ["auto", "openai", "gemini"], index=0,
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
            "Add OPENAI_API_KEY or GEMINI_API_KEY to `.env` to enable live answers.  \n"
            "Preset questions and the chat input are shown below for reference."
        )
    else:
        st.success("Agent ready — GPT-4o connected with Knowledge Graph context")

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
        st.session_state.messages.append({"role": "user", "content": q})
        with st.chat_message("user"):
            st.markdown(q)
        with st.chat_message("assistant"):
            if agent is None:
                st.error("Agent not available — set OPENAI_API_KEY or GEMINI_API_KEY in .env")
            else:
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
                    arts = fetch_pubmed(f"CD46 {q[:80]}", max_results=5)
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
                            f"<b style='color:#e2e8f0;'>[{i}] {art.get('title','')}</b><br>"
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
        st.markdown("#### Quick-Start Questions")
        st.caption("Click any question to run it through the KG-grounded agent.")
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
        "Ask about CD46 expression, patient eligibility, drugs, trials, mechanisms..."
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
        "LLM: GPT-4o (OpenAI) primary · Gemini 2.5 Flash (Google) fallback · "
        "Orchestrated via LangGraph + LiteLLM<br>"
        "Context sources: TCGA · HPA · cBioPortal · DepMap · ClinicalTrials.gov · AuraDB KG<br>"
        "<b>For research purposes only. Not for clinical decision-making.</b>"
        "</div>",
        unsafe_allow_html=True,
    )

# ==========================================================================
# TAB 2 — How It Works (RAG architecture)
# ==========================================================================
with tab_arch:
    st.markdown("#### Retrieval-Augmented Generation on a Structured Scientific Knowledge Graph")

    # Grounded AI vs Generic AI comparison
    st.markdown(
        "<div style='background:#1e293b;border-left:4px solid #f87171;"
        "padding:16px 20px;border-radius:8px;margin-bottom:20px;'>"
        "<b style='color:#f87171;font-size:1.05em;'>The Problem with Generic AI</b><br><br>"
        "<span style='color:#cbd5e1;'>Large language models like ChatGPT generate "
        "<i>plausible</i> text about CD46 biology. They do not retrieve your TCGA expression values, "
        "your GENIE patient counts, your active clinical trial IDs, or your PubMed corpus. "
        "They invent or misrepresent statistics. Every claim is untraceable.</span>"
        "</div>",
        unsafe_allow_html=True,
    )
    st.markdown(
        "<div style='background:#1e293b;border-left:4px solid #4ade80;"
        "padding:16px 20px;border-radius:8px;margin-bottom:24px;'>"
        "<b style='color:#4ade80;font-size:1.05em;'>This System: Grounded AI</b><br><br>"
        "<span style='color:#cbd5e1;'>Before the LLM writes a single word, "
        "the system queries the Neo4j knowledge graph — 3,912 biology-specific nodes — "
        "and retrieves structured, verified facts relevant to the question. "
        "The LLM then writes <i>around those facts</i>. "
        "Every claim is traceable to a node: TCGA, HPA, ClinicalTrials.gov, PubMed, DepMap.</span>"
        "</div>",
        unsafe_allow_html=True,
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
            "Question → semantic search across 3,912 KG nodes → "
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
    st.dataframe(df_comp.set_index("Capability"), use_container_width=True)

    st.markdown("---")
    st.markdown("#### Technology Stack")
    tc1, tc2, tc3 = st.columns(3)
    tc1.markdown(
        "**LLM Layer**\n"
        "- GPT-4o (OpenAI) — primary\n"
        "- Gemini 2.5 Flash — fallback\n"
        "- Routed via LiteLLM\n"
        "- Orchestrated by LangGraph"
    )
    tc2.markdown(
        "**Knowledge Graph**\n"
        "- Neo4j AuraDB (cloud)\n"
        "- ~3,912 nodes, ~14,880 edges\n"
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

# ==========================================================================
# TAB 3 — Evidence Context (what data the agent has access to)
# ==========================================================================
with tab_evidence:
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
            "<b style='color:#e2e8f0;'>Protein Structural Biology</b><br>"
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
    st.markdown("#### Sample Questions Demonstrating Evidence Retrieval")

    demo_data = {
        "Your Question": [
            "Which cancers show the strongest CD46 over-expression?",
            "What is the clinical rationale for 225Ac-CD46 in mCRPC?",
            "How does PTEN loss affect CD46 expression?",
            "Design a biomarker strategy for Phase I patient selection.",
            "What STRING interactions are most relevant for toxicity profiling?",
        ],
        "KG Nodes Retrieved": [
            "25 Disease nodes with cd46_mean_tpm_log2 and expression_rank",
            "PRAD Disease node + SU2C cohort + 14 Drug/Trial nodes",
            "PRAD PatientGroup nodes (PTEN_deleted subtype) + AnalysisResult",
            "PatientGroup nodes at 75th/median threshold + ClinicalTrial endpoints",
            "Protein–Protein interaction nodes + Tissue nodes (normal expression)",
        ],
        "Evidence Source": [
            "TCGA (25 cancer types), HPA (protein atlas)",
            "TCGA, SU2C mCRPC, ClinicalTrials.gov, ChEMBL",
            "GENIE molecular subtypes, cBioPortal",
            "GENIE, TCGA, ClinicalTrials.gov registry",
            "STRING DB (taxid 9606), HPA tissue distribution",
        ],
    }
    st.dataframe(pd.DataFrame(demo_data), use_container_width=True, hide_index=True)

    st.markdown("---")
    st.caption(
        "All data sources are pre-ingested into Neo4j AuraDB. "
        "The agent retrieves structured facts as Cypher query results before every LLM call. "
        "No data leaves the knowledge graph boundary during retrieval."
    )
