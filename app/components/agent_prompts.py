"""Target-aware Research Assistant preset questions."""
from __future__ import annotations

from components.targets import get_active_symbol, get_target

# CAB themes tuned per target class — not one mCRPC script for all genes
_CAB_BY_SYMBOL: dict[str, list[str]] = {
    "FOLH1": [
        "Which cancers have the strongest case for FOLH1-targeted RLT based on expression and survival?",
        "What is the optimal biomarker strategy for PSMA (FOLH1) patient selection in mCRPC?",
        "How does the FOLH1 trial landscape compare to emerging dual-target strategies?",
        "What clinical trial evidence exists for anti-FOLH1 / PSMA therapies and key readouts?",
        "What normal-tissue PSMA expression limits exist for radioligand dosing?",
    ],
    "FAP": [
        "Which cancers show the strongest FAP (stromal) expression and survival association?",
        "What is the optimal biomarker strategy for FAP-targeted radioligand trials?",
        "How does FAP compare to tumour-intrinsic targets for therapeutic index?",
        "What clinical trial evidence exists for FAP / FAPI radioligand programs?",
        "What DepMap and cell-line data support FAP as a dependency?",
    ],
    "SSTR2": [
        "Which cancers have the strongest SSTR2 expression for somatostatin-analog RLT?",
        "What is the optimal biomarker strategy for SSTR2 patient selection in NET?",
        "How does SSTR2 expression in tumour vs normal tissue inform dosimetry?",
        "What clinical trial evidence exists for SSTR2-targeted radioligand therapy?",
        "What drugs in the pipeline target SSTR2 (max phase and modality)?",
    ],
    "GRPR": [
        "Which solid tumours show the highest GRPR expression in TCGA?",
        "What is the optimal biomarker strategy for GRPR-targeted radioligand trials?",
        "How does GRPR compare to other GPCR radioligand targets?",
        "What clinical trial evidence exists for GRPR / bombesin-analog programs?",
        "What DepMap evidence supports GRPR as a cancer dependency?",
    ],
    "CD46": [
        "Which cancers have the strongest case for CD46-targeted RLT based on expression and survival?",
        "What is the optimal biomarker strategy for CD46 patient selection in a Phase I trial?",
        "How does CD46 compare to PSMA as a therapeutic target in mCRPC?",
        "Design a Phase I dose-escalation trial for CD46-targeted RLT in mCRPC — key elements?",
        "What clinical trial evidence exists for anti-CD46 therapies and emerging readouts?",
    ],
}

_MECHANISM_QUESTION: dict[str, str] = {
    "CD46": "How does CD46 regulate complement evasion in tumour cells?",
    "FOLH1": "What is the therapeutic rationale for targeting FOLH1 (PSMA) in prostate and solid tumours?",
    "FAP": "What is the therapeutic rationale for targeting FAP on cancer-associated fibroblasts?",
    "SSTR2": "What is the therapeutic rationale for targeting SSTR2 in neuroendocrine and solid tumours?",
    "GRPR": "What is the therapeutic rationale for targeting GRPR in lung and other solid tumours?",
}


def quick_start_questions(symbol: str | None = None) -> list[str]:
    g = symbol or get_active_symbol()
    mech = _MECHANISM_QUESTION.get(g, f"What is the therapeutic rationale for targeting {g} in solid tumours?")
    return [
        f"Which cancers have the strongest combination of {g} over-expression and survival impact?",
        f"What is the current {g}-targeted drug pipeline and which agents are in clinical trials?",
        mech,
        f"What DepMap evidence supports {g} as a cancer dependency?",
        f"Summarise {g} expression across TCGA cancer types with hazard ratios.",
        f"What are the {g} isoforms and which are most relevant for therapeutic targeting?",
    ]


def cab_questions(symbol: str | None = None) -> list[str]:
    g = symbol or get_active_symbol()
    return list(_CAB_BY_SYMBOL.get(g, _CAB_BY_SYMBOL["CD46"]))


def evidence_demo_rows(symbol: str | None = None) -> dict[str, list[str]]:
    """Sample Q&A table for Evidence Context tab — active target parameterized."""
    g = symbol or get_active_symbol()
    t = get_target(g)
    name = t.get("name", g)
    return {
        "Your Question": [
            f"Which cancers show the strongest {g} over-expression?",
            f"What is the clinical rationale for {g}-targeted radioligand therapy?",
            f"What DepMap evidence supports {g} as a dependency?",
            f"List active clinical trials targeting {g}.",
        ],
        "KG / Data Retrieved": [
            f"Gene→Disease EXPRESSED_IN_CANCER ranks for {g}",
            f"Drug→TARGETS→{g} and Trial→TARGETS_GENE→{g} nodes",
            f"CellLine→DEPENDS_ON→{g} (DepMap CRISPR)",
            f"ClinicalTrials.gov cache + Publication→SUPPORTS→{g}",
        ],
        "Evidence Source": [
            "TCGA / UCSC Xena + AuraDB KG",
            "ChEMBL + ClinicalTrials.gov + KG",
            "DepMap 25Q3 + KG",
            "ClinicalTrials.gov API + PubMed",
        ],
        "Target context": [name] * 4,
    }


if __name__ == "__main__":
    for s in ("FOLH1", "FAP", "SSTR2", "GRPR", "CD46"):
        assert s in quick_start_questions(s)[0]
    print("agent_prompts_ok")
