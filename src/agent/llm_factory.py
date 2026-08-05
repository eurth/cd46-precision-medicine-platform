"""LiteLLM-based LLM factory — OpenRouter Gemma primary, GPT-4o / Gemini fallback."""
from __future__ import annotations

import logging
import os

logger = logging.getLogger(__name__)

# Default free Gemma on OpenRouter (override with OPENROUTER_MODEL)
_DEFAULT_OPENROUTER_MODEL = "openrouter/google/gemma-4-31b-it:free"


def _target_meta(gene: str) -> dict:
    """Best-effort registry lookup — works outside Streamlit too."""
    sym = (gene or "").upper().strip() or "CD46"
    try:
        from components.targets import get_target

        return get_target(sym)
    except Exception:
        pass
    try:
        from pathlib import Path
        import yaml

        root = Path(__file__).resolve().parents[2]
        data = yaml.safe_load((root / "config" / "targets.yaml").read_text(encoding="utf-8")) or {}
        t = (data.get("targets") or {}).get(sym) or {}
        return {"symbol": sym, **t}
    except Exception:
        return {"symbol": sym}


def system_prompt_for(gene: str) -> str:
    """Gene-aware system prompt from registry metadata (any active target)."""
    g = (gene or "").upper().strip() or "CD46"
    t = _target_meta(g)
    name = t.get("name") or g
    ensembl = t.get("ensembl_id") or "n/a"
    uniprot = t.get("uniprot_id") or "n/a"
    entrez = t.get("entrez_id") or "n/a"
    aliases = ", ".join(t.get("aliases") or []) or "n/a"
    modalities = ", ".join(t.get("modality_tags") or []) or "oncology surface / pathway target"
    tier = t.get("data_tier") or t.get("kg_status") or "unknown"
    case_study = bool(t.get("case_study"))

    lines = [
        "You are an expert AI research assistant for OncoBridge Intelligence,",
        "an EurthTech pan-cancer target intelligence platform demonstrating Knowledge Graph + AI-driven",
        f"cancer research. Active research target: {g} ({name}).",
        "",
        "You have access to (depth varies by target data_tier):",
        f"- Pan-cancer TCGA {g} expression data (33 cancer types where sliced)",
        "- HPA / GTEx normal and tumour tissue expression",
        f"- Patient eligibility / expression-group estimates for {g}-High cohorts when CSVs exist",
        "- Kaplan-Meier and Cox PH survival analysis results for TCGA cancers",
        "- DepMap CRISPR essentiality data across cancer cell lines",
        "- Knowledge graph covering genes, proteins, diseases, drugs, trials, pathways",
        f"- ClinicalTrials.gov cache and ChEMBL / Open Targets associations for {g}",
        "",
        f"Target metadata ({g}):",
        f"- Gene: {ensembl}, Entrez {entrez}",
        f"- Protein: UniProt {uniprot}",
        f"- Aliases: {aliases}",
        f"- Modality tags: {modalities}",
        f"- Data tier: {tier}",
    ]

    # Target-specific biology notes only when that gene is active (not a platform privilege)
    if g == "CD46":
        lines += [
            "",
            f"{g} biology notes (active target):",
            "- Protein: Membrane cofactor protein / CD46 (complement regulator)",
            "- Often overexpressed in solid tumours; studied in prostate and other cancers",
            "- Therapeutic context includes radioligand / antibody strategies when supported by evidence",
            "- Complementary to PSMA (FOLH1) in some prostate cohorts — verify from retrieved data",
        ]
    else:
        lines += [
            "",
            f"Focus answers on {g} using retrieved context. Do not substitute another gene's narrative.",
            f"Prefer {g}-specific expression, survival, trials, drugs, and DepMap evidence from context.",
        ]

    lines += [
        "",
        "Always cite specific data points when available. Be precise about statistical significance.",
        "For clinical claims, always clarify if data is from preclinical, early clinical, or approved sources.",
        "GENIE dataset analysis is deferred to Phase 2 (requires Synapse DUA + AuraDB Pro tier).",
    ]
    return "\n".join(lines)


def get_llm(
    provider: str = "auto",
    temperature: float = 0.1,
    gene: str | None = None,
) -> "LiteLLMWrapper":
    """
    Get a configured LLM instance.

    Args:
        provider: "openrouter" | "openai" | "gemini" | "ollama" | "auto"
                  "auto" prefers OpenRouter → OpenAI → Gemini.
        temperature: Sampling temperature (default 0.1 for factual precision).
        gene: Active gene symbol for the system prompt (defaults to registry active / CD46).

    Returns:
        LiteLLMWrapper instance ready for chat completion.
    """
    from litellm import completion  # deferred import so module loads without litellm

    if provider == "auto":
        if os.getenv("OPENROUTER_API_KEY"):
            provider = "openrouter"
            logger.info("LLM factory: using OpenRouter Gemma (primary)")
        elif os.getenv("OPENAI_API_KEY"):
            provider = "openai"
            logger.info("LLM factory: using OpenAI GPT-4o")
        elif os.getenv("GEMINI_API_KEY"):
            provider = "gemini"
            logger.info("LLM factory: using Gemini Flash (fallback)")
        else:
            raise RuntimeError(
                "No LLM API key found. Set OPENROUTER_API_KEY, OPENAI_API_KEY, or GEMINI_API_KEY in .env"
            )

    openrouter_model = os.getenv("OPENROUTER_MODEL", _DEFAULT_OPENROUTER_MODEL)
    if openrouter_model and not openrouter_model.startswith("openrouter/"):
        openrouter_model = f"openrouter/{openrouter_model}"

    model_map = {
        "openrouter": openrouter_model,
        "openai": "gpt-4o",
        "gemini": "gemini/gemini-2.5-flash",
        "ollama": "ollama/llama3",
    }

    model = model_map.get(provider)
    if model is None:
        raise ValueError(
            f"Unknown provider '{provider}'. Choose: openrouter, openai, gemini, ollama, auto"
        )

    active = gene
    if not active:
        try:
            from components.targets import get_active_symbol

            active = get_active_symbol()
        except Exception:
            active = "CD46"

    return LiteLLMWrapper(
        model=model,
        temperature=temperature,
        system_prompt=system_prompt_for(active),
        completion_fn=completion,
        default_gene=active,
    )


class LiteLLMWrapper:
    """Thin wrapper around LiteLLM completion for integration with LangGraph."""

    def __init__(
        self,
        model: str,
        temperature: float,
        system_prompt: str,
        completion_fn,
        default_gene: str = "CD46",
    ):
        self.model = model
        self.temperature = temperature
        self.system_prompt = system_prompt
        self._completion = completion_fn
        self.default_gene = default_gene

    def _resolve_prompt(self, gene: str | None) -> str:
        if gene:
            return system_prompt_for(gene)
        return self.system_prompt or system_prompt_for(self.default_gene)

    def chat(self, user_message: str, context: str = "", gene: str | None = None) -> str:
        """
        Generate a response to a user message.

        Args:
            user_message: The user's question.
            context: Optional pre-fetched context (KG results, CSV data, etc.) to inject.
            gene: Active gene — selects the dynamic system prompt.

        Returns:
            Model response string.
        """
        messages = [{"role": "system", "content": self._resolve_prompt(gene)}]

        if context:
            messages.append(
                {
                    "role": "system",
                    "content": f"RETRIEVED CONTEXT:\n{context}\n\nUse this context to answer accurately.",
                }
            )

        messages.append({"role": "user", "content": user_message})

        # ponytail: cap context size — huge dossier payloads timeout free OpenRouter tiers
        ctx_cap = 14_000
        for msg in messages:
            if len(msg.get("content", "")) > ctx_cap:
                msg["content"] = msg["content"][:ctx_cap] + "\n\n[…context truncated…]"

        try:
            response = self._completion(
                model=self.model,
                messages=messages,
                temperature=self.temperature,
                max_tokens=2000,
                timeout=90,
                request_timeout=90,
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error("LLM completion error (%s): %s", self.model, e)
            raise

    def stream(self, user_message: str, context: str = "", gene: str | None = None):
        """Stream response tokens — used by Streamlit app."""
        messages = [{"role": "system", "content": self._resolve_prompt(gene)}]
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
            timeout=90,
            request_timeout=90,
        )
        for chunk in response:
            delta = chunk.choices[0].delta
            if hasattr(delta, "content") and delta.content:
                yield delta.content
