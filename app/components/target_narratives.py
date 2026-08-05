"""Per-target module copy — P5 site balance + C5 strategy templates (additive)."""
from __future__ import annotations

from components.targets import get_active_symbol, get_target

_STRATEGY: dict[str, dict[str, str]] = {
    "CD46": {
        "indication": "mCRPC · haematologic malignancies",
        "modality": "225Ac-CD46 α-RLT / ADC",
        "trial_focus": "FOR46 · complement-evasion niche",
        "approval_target": "2030",
    },
    "FOLH1": {
        "indication": "mCRPC · PSMA-positive solid tumours",
        "modality": "177Lu/225Ac PSMA radioligand",
        "trial_focus": "Pluvicto-class RLT · PSMA PET selection",
        "approval_target": "Approved (RLT) · next-gen agents in Ph I–III",
    },
    "FAP": {
        "indication": "pancreatic · sarcoma · CAF-rich solid tumours",
        "modality": "FAPI radioligand · stromal targeting",
        "trial_focus": "FAPI-04/46 programmes · stromal TI",
        "approval_target": "2028+ (investigational)",
    },
    "SSTR2": {
        "indication": "neuroendocrine tumours · SSTR2+ solid tumours",
        "modality": "somatostatin analog RLT (177Lu-DOTATATE class)",
        "trial_focus": "PRRT expansion · NET selection",
        "approval_target": "Approved (NET) · expansion trials",
    },
    "GRPR": {
        "indication": "GRPR+ lung · breast · GI solid tumours",
        "modality": "bombesin-analog radioligand",
        "trial_focus": "GRPR PET selection · early-phase RLT",
        "approval_target": "2029+ (investigational)",
    },
}


def strategy_context(symbol: str | None = None) -> dict[str, str]:
    sym = symbol or get_active_symbol()
    base = _STRATEGY.get(
        sym,
        {
            "indication": f"{sym}-associated malignancies",
            "modality": f"{sym}-targeted therapy",
            "trial_focus": f"{sym} ClinicalTrials.gov / ChEMBL",
            "approval_target": "horizon TBD",
        },
    ).copy()
    base["symbol"] = sym
    base["name"] = get_target(sym).get("name", sym)
    return base


def dosimetry_purpose(symbol: str | None = None) -> str:
    g = symbol or get_active_symbol()
    ctx = strategy_context(g)
    return (
        f"Therapeutic index for **{g}**-targeted radioligand therapy · "
        f"HPA normal vs tumour proxy · {ctx['modality']}"
    )


def diagnostics_purpose(symbol: str | None = None) -> str:
    g = symbol or get_active_symbol()
    return (
        f"Companion diagnostic framing for **{g}** — GTEx normal tissue, "
        "mutation burden, and imaging selection context"
    )


def strategy_purpose(symbol: str | None = None) -> str:
    g = symbol or get_active_symbol()
    ctx = strategy_context(g)
    return (
        f"End-to-end narrative for **{g}** ({ctx['name']}): "
        f"Target → Drug → Patient → Trial → Outcome · "
        f"{ctx['indication']} · {ctx['modality']}"
    )


def strategy_stage1_title(symbol: str | None = None) -> str:
    g = symbol or get_active_symbol()
    return f"Stage 1 — Target Biology: Why {g}?"
