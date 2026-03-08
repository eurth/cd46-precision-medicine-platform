"""LiteLLM-based LLM factory — GPT-4o primary, Gemini Flash fallback."""
from __future__ import annotations

import logging
import os

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = """You are an expert AI assistant for the CD46 Precision Medicine Platform,
supporting Prof. Bobba Naidu's 225Ac-CD46 cancer therapy research program.

You have access to:
- Pan-cancer TCGA CD46 expression data (33 cancer types, ~11,000 patients)
- HPA protein expression across 30+ tissues (tumor vs normal)
- Patient eligibility estimates for 225Ac-CD46 therapy at multiple thresholds
- Kaplan-Meier and Cox PH survival analysis results for all 33 TCGA cancers
- cBioPortal mCRPC cohort data (SU2C + MSK, n=1,183 patients)
- DepMap CRISPR essentiality data for CD46 across cancer cell lines
- Knowledge graph with ~3,912 nodes covering genes, proteins, diseases, drugs, trials, pathways
- ClinicalTrials.gov data for CD46-targeting and 225Ac programs
- ChEMBL bioactivity data and Open Targets disease associations

CD46 key facts:
- Gene: ENSG00000117335, chromosome 1q32.2, Entrez 4179
- Protein: UniProt P15529 (Membrane cofactor protein / CD46)
- Function: Complement regulator; overexpressed in multiple cancers (60-85% of PRAD specimens)
- Primary target: Metastatic castration-resistant prostate cancer (mCRPC)
- Mechanism: 225Ac alpha-particle emitter tethered to anti-CD46 mAb → DNA double-strand breaks
- PSMA-CD46 relationship: Complementary biomarkers — ~35% of mCRPC are PSMA-low but CD46-high

Priority cancers (by CD46 priority score): PRAD, OV, BLCA, BRCA, COAD

Always cite specific data points when available. Be precise about statistical significance.
For clinical claims, always clarify if data is from preclinical, early clinical, or approved sources.
GENIE dataset analysis is deferred to Phase 2 (requires Synapse DUA + AuraDB Pro tier).
"""


def get_llm(provider: str = "auto", temperature: float = 0.1) -> "LiteLLMWrapper":
    """
    Get a configured LLM instance.

    Args:
        provider: "openai" | "gemini" | "ollama" | "auto"
                  "auto" tries OpenAI first, falls back to Gemini.
        temperature: Sampling temperature (default 0.1 for factual precision).

    Returns:
        LiteLLMWrapper instance ready for chat completion.
    """
    from litellm import completion  # deferred import so module loads without litellm

    if provider == "auto":
        if os.getenv("OPENAI_API_KEY"):
            provider = "openai"
            logger.info("LLM factory: using OpenAI GPT-4o (primary)")
        elif os.getenv("GEMINI_API_KEY"):
            provider = "gemini"
            logger.info("LLM factory: using Gemini Flash (fallback — OpenAI key not set)")
        else:
            raise RuntimeError(
                "No LLM API key found. Set OPENAI_API_KEY or GEMINI_API_KEY in .env"
            )

    model_map = {
        "openai": "gpt-4o",
        "gemini": "gemini/gemini-2.5-flash",
        "ollama": "ollama/llama3",
    }

    model = model_map.get(provider)
    if model is None:
        raise ValueError(f"Unknown provider '{provider}'. Choose: openai, gemini, ollama, auto")

    return LiteLLMWrapper(
        model=model,
        temperature=temperature,
        system_prompt=_SYSTEM_PROMPT,
        completion_fn=completion,
    )


class LiteLLMWrapper:
    """Thin wrapper around LiteLLM completion for integration with LangGraph."""

    def __init__(self, model: str, temperature: float, system_prompt: str, completion_fn):
        self.model = model
        self.temperature = temperature
        self.system_prompt = system_prompt
        self._completion = completion_fn

    def chat(self, user_message: str, context: str = "") -> str:
        """
        Generate a response to a user message.

        Args:
            user_message: The user's question.
            context: Optional pre-fetched context (KG results, CSV data, etc.) to inject.

        Returns:
            Model response string.
        """
        messages = [{"role": "system", "content": self.system_prompt}]

        if context:
            messages.append(
                {
                    "role": "system",
                    "content": f"RETRIEVED CONTEXT:\n{context}\n\nUse this context to answer accurately.",
                }
            )

        messages.append({"role": "user", "content": user_message})

        try:
            response = self._completion(
                model=self.model,
                messages=messages,
                temperature=self.temperature,
                max_tokens=2000,
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error("LLM completion error (%s): %s", self.model, e)
            raise

    def stream(self, user_message: str, context: str = ""):
        """Stream response tokens — used by Streamlit app."""
        messages = [{"role": "system", "content": self.system_prompt}]
        if context:
            messages.append(
                {
                    "role": "system",
                    "content": f"RETRIEVED CONTEXT:\n{context}\n\nUse this context to answer accurately.",
                }
            )
        messages.append({"role": "user", "content": user_message})

        response = self._completion(
            model=self.model,
            messages=messages,
            temperature=self.temperature,
            max_tokens=2000,
            stream=True,
        )
        for chunk in response:
            delta = chunk.choices[0].delta
            if hasattr(delta, "content") and delta.content:
                yield delta.content
