"""Page 5 — AI Assistant (GPT-4o + Gemini fallback via LiteLLM)."""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parents[2] / ".env")

import streamlit as st

# Inject Streamlit Cloud secrets into os.environ (no-op when running locally with .env)
for _k in ("OPENAI_API_KEY", "GEMINI_API_KEY", "NEO4J_URI", "NEO4J_USERNAME", "NEO4J_PASSWORD"):
    try:
        if _k in st.secrets and not os.environ.get(_k):
            os.environ[_k] = st.secrets[_k]
    except Exception:
        pass


st.title("🤖 CD46 AI Research Assistant")
st.markdown(
    "**Ask questions about CD46 biology, patient eligibility, survival outcomes, drug targets, and clinical trials. "
    "Powered by GPT-4o (primary) or Gemini 2.5 Flash (fallback) with integrated research data context.**"
)

# ---------------------------------------------------------------------------
# LLM provider selector
# ---------------------------------------------------------------------------

from src.agent.orchestrator import PRESET_QUESTIONS

col_provider, col_temp = st.columns([2, 1])
with col_provider:
    provider = st.selectbox("LLM Provider", ["auto", "openai", "gemini"], index=0)
with col_temp:
    temperature = st.slider("Temperature", min_value=0.0, max_value=1.0, value=0.1, step=0.05)

# ---------------------------------------------------------------------------
# Initialize agent
# ---------------------------------------------------------------------------

@st.cache_resource
def get_agent(provider: str, temperature: float):
    try:
        from src.agent.orchestrator import CD46Agent
        return CD46Agent(provider=provider), None
    except Exception as e:
        return None, str(e)


agent, agent_error = get_agent(provider, temperature)

if agent_error:
    st.error(
        f"⚠️ Agent initialization failed: {agent_error}\n\n"
        "Set OPENAI_API_KEY or GEMINI_API_KEY in your .env file."
    )

# ---------------------------------------------------------------------------
# Chat history
# ---------------------------------------------------------------------------

if "messages" not in st.session_state:
    st.session_state.messages = []

# New Question / Clear button — always visible when conversation exists
if st.session_state.messages:
    col_clear, _ = st.columns([1, 4])
    with col_clear:
        if st.button("✚ New Question", use_container_width=True):
            st.session_state.messages = []
            st.rerun()

# Display prior messages
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ---------------------------------------------------------------------------
# Preset questions (quick-start buttons)
# ---------------------------------------------------------------------------

if not st.session_state.messages:
    st.subheader("Quick-start Questions")
    cols = st.columns(2)
    for i, q in enumerate(PRESET_QUESTIONS):
        col = cols[i % 2]
        if col.button(q, key=f"preset_{i}", use_container_width=True):
            st.session_state.messages.append({"role": "user", "content": q})
            if agent is not None:
                with st.chat_message("user"):
                    st.markdown(q)
                with st.chat_message("assistant"):
                    with st.spinner("Thinking..."):
                        response_placeholder = st.empty()
                        full_response = ""
                        try:
                            for token in agent.stream(q):
                                full_response += token
                                response_placeholder.markdown(full_response + "▌")
                            response_placeholder.markdown(full_response)
                        except Exception as e:
                            full_response = f"Error: {e}"
                            response_placeholder.error(full_response)
                st.session_state.messages.append({"role": "assistant", "content": full_response})
                st.rerun()

# ---------------------------------------------------------------------------
# Chat input
# ---------------------------------------------------------------------------

if prompt := st.chat_input("Ask about CD46 expression, eligibility, survival, drugs, trials..."):
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        if agent is None:
            st.error(
                "Agent not available — set OPENAI_API_KEY or GEMINI_API_KEY in .env "
                "and restart the app."
            )
        else:
            with st.spinner("Retrieving context + generating answer..."):
                response_placeholder = st.empty()
                full_response = ""
                try:
                    for token in agent.stream(prompt):
                        full_response += token
                        response_placeholder.markdown(full_response + "▌")
                    response_placeholder.markdown(full_response)
                except Exception as e:
                    full_response = f"Error generating response: {str(e)}"
                    response_placeholder.error(full_response)

            st.session_state.messages.append({"role": "assistant", "content": full_response})

# ---------------------------------------------------------------------------
# Clear chat
# ---------------------------------------------------------------------------

if st.session_state.messages:
    if st.button("🗑️ Clear conversation"):
        st.session_state.messages = []
        st.rerun()

# ---------------------------------------------------------------------------
# Footer
# ---------------------------------------------------------------------------

st.markdown("---")
st.markdown(
    "<div style='color:#64748b; font-size:0.8em;'>"
    "LLM: GPT-4o (OpenAI) primary · Gemini 2.5 Flash (Google) fallback · Orchestrated via LangGraph + LiteLLM<br>"
    "Context sources: TCGA · HPA · cBioPortal · DepMap · ClinicalTrials.gov · AuraDB KG<br>"
    "⚠️ This tool is for research purposes only. Not for clinical decision-making."
    "</div>",
    unsafe_allow_html=True,
)
