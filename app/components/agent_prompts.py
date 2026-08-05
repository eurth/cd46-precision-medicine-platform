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
    "CEACAM5": [
        "Which cancers have the strongest CEACAM5 (CEA) expression for ADC / RLT strategies?",
        "What is the optimal biomarker strategy for CEACAM5 patient selection?",
        "How does CEACAM5 compare to other epithelial surface antigens in solid tumours?",
        "What clinical trial evidence exists for anti-CEACAM5 therapies?",
        "What normal-tissue CEA expression limits therapeutic index?",
    ],
    "DLL3": [
        "Which cancers show the strongest DLL3 expression for RLT / ADC strategies?",
        "What is the optimal biomarker strategy for DLL3 patient selection in SCLC / NE tumours?",
        "How does DLL3 compare to other Notch-pathway oncology targets?",
        "What clinical trial evidence exists for DLL3-targeted agents?",
        "What DepMap evidence supports DLL3 as a cancer dependency?",
    ],
    "NECTIN4": [
        "Which cancers have the strongest NECTIN4 expression for ADC strategies?",
        "What is the optimal biomarker / CDx strategy for NECTIN4 patient selection?",
        "How does NECTIN4 compare to other ADC surface antigens?",
        "What clinical trial evidence exists for anti-NECTIN4 therapies?",
        "What normal-tissue NECTIN4 expression informs safety?",
    ],
    "ERBB2": [
        "Which cancers have the strongest ERBB2 (HER2) case for targeted therapy?",
        "What is the optimal biomarker strategy for HER2 patient selection across solid tumours?",
        "How does ERBB2 compare to other RTK oncology targets in the panel?",
        "What clinical trial evidence exists for anti-HER2 ADCs and RLT programs?",
        "What DepMap evidence supports ERBB2 as a cancer dependency?",
    ],
    "TACSTD2": [
        "Which cancers have the strongest TACSTD2 (TROP2) expression for ADC strategies?",
        "What is the optimal biomarker strategy for TROP2 patient selection?",
        "How does TACSTD2 compare to other epithelial ADC antigens?",
        "What clinical trial evidence exists for anti-TROP2 therapies?",
        "What normal-tissue TROP2 expression limits dosing?",
    ],
    "EGFR": [
        "Which cancers have the strongest EGFR expression / alteration case for targeting?",
        "What is the optimal biomarker strategy for EGFR patient selection?",
        "How does EGFR compare to other RTK targets in the panel?",
        "What clinical trial evidence exists for EGFR-targeted ADCs and radioligands?",
        "What DepMap evidence supports EGFR as a cancer dependency?",
    ],
    "MSLN": [
        "Which cancers show the strongest MSLN (mesothelin) expression for ADC / CAR strategies?",
        "What is the optimal biomarker strategy for mesothelin patient selection?",
        "How does MSLN compare to other peritoneal / mesothelial targets?",
        "What clinical trial evidence exists for anti-mesothelin therapies?",
        "What normal-tissue mesothelin expression informs safety?",
    ],
    "CLDN18": [
        "Which cancers have the strongest CLDN18 (esp. CLDN18.2) case for targeting?",
        "What is the optimal biomarker strategy for CLDN18.2 patient selection in gastric cancer?",
        "How does CLDN18 compare to other tight-junction oncology antigens?",
        "What clinical trial evidence exists for CLDN18.2-targeted agents?",
        "What DepMap evidence supports CLDN18 as a cancer dependency?",
    ],
    "GPC3": [
        "Which cancers have the strongest GPC3 expression for ADC / CAR strategies?",
        "What is the optimal biomarker strategy for GPC3 patient selection in HCC?",
        "How does GPC3 compare to other HCC surface antigens?",
        "What clinical trial evidence exists for anti-GPC3 therapies?",
        "What DepMap evidence supports GPC3 as a cancer dependency?",
    ],
    "FOLR1": [
        "Which cancers have the strongest FOLR1 (FRα) expression for ADC strategies?",
        "What is the optimal biomarker strategy for FOLR1 patient selection in ovarian cancer?",
        "How does FOLR1 compare to other folate-pathway oncology targets?",
        "What clinical trial evidence exists for anti-FOLR1 therapies?",
        "What normal-tissue FOLR1 expression informs safety?",
    ],
    "CD19": [
        "Which haematologic cancers have the strongest CD19 case for CAR-T / ADC?",
        "What is the optimal biomarker strategy for CD19 patient selection?",
        "How does CD19 compare to other B-cell lineage antigens?",
        "What clinical trial evidence exists for anti-CD19 therapies?",
        "What DepMap / cell-line data support CD19 as a dependency?",
    ],
    "STEAP1": [
        "Which cancers show the strongest STEAP1 expression for RLT / ADC strategies?",
        "What is the optimal biomarker strategy for STEAP1 patient selection in prostate cancer?",
        "How does STEAP1 compare to PSMA and other prostate surface antigens?",
        "What clinical trial evidence exists for STEAP1-targeted agents?",
        "What DepMap evidence supports STEAP1 as a cancer dependency?",
    ],
    "CD276": [
        "Which cancers have the strongest CD276 (B7-H3) expression for ADC / RLT?",
        "What is the optimal biomarker strategy for B7-H3 patient selection?",
        "How does CD276 compare to other immune-checkpoint / surface antigens?",
        "What clinical trial evidence exists for anti-B7-H3 therapies?",
        "What DepMap evidence supports CD276 as a cancer dependency?",
    ],
    "CA9": [
        "Which cancers have the strongest CA9 (CAIX) expression under hypoxia?",
        "What is the optimal biomarker strategy for CA9 patient selection?",
        "How does CA9 compare to other hypoxia-associated oncology targets?",
        "What clinical trial evidence exists for CA9-targeted agents?",
        "What DepMap evidence supports CA9 as a cancer dependency?",
    ],
    "MET": [
        "Which cancers have the strongest MET expression / alteration case for targeting?",
        "What is the optimal biomarker strategy for MET patient selection?",
        "How does MET compare to other RTK oncology targets in the panel?",
        "What clinical trial evidence exists for MET-targeted therapies?",
        "What DepMap evidence supports MET as a cancer dependency?",
    ],
}

_GENERIC_CAB = [
    "Which cancers have the strongest case for {g}-targeted therapy based on expression and survival?",
    "What is the optimal biomarker / CDx strategy for {g} patient selection in early trials?",
    "How does {g} compare to related panel targets on expression, survival, and trial maturity?",
    "What clinical trial evidence exists for anti-{g} / {g}-directed therapies and key readouts?",
    "What normal-tissue {g} expression and DepMap data inform therapeutic index and dependency?",
]

_MECHANISM_QUESTION: dict[str, str] = {
    "CD46": "How does CD46 regulate complement evasion in tumour cells?",
    "FOLH1": "What is the therapeutic rationale for targeting FOLH1 (PSMA) in prostate and solid tumours?",
    "FAP": "What is the therapeutic rationale for targeting FAP on cancer-associated fibroblasts?",
    "SSTR2": "What is the therapeutic rationale for targeting SSTR2 in neuroendocrine and solid tumours?",
    "GRPR": "What is the therapeutic rationale for targeting GRPR in lung and other solid tumours?",
    "CEACAM5": "What is the therapeutic rationale for targeting CEACAM5 (CEA) in solid tumours?",
    "DLL3": "What is the therapeutic rationale for targeting DLL3 in SCLC and neuroendocrine tumours?",
    "NECTIN4": "What is the therapeutic rationale for targeting NECTIN4 with ADCs?",
    "ERBB2": "What is the therapeutic rationale for targeting ERBB2 (HER2) across solid tumours?",
    "TACSTD2": "What is the therapeutic rationale for targeting TACSTD2 (TROP2) with ADCs?",
    "EGFR": "What is the therapeutic rationale for targeting EGFR in solid tumours?",
    "MSLN": "What is the therapeutic rationale for targeting mesothelin (MSLN) in solid tumours?",
    "CLDN18": "What is the therapeutic rationale for targeting CLDN18.2 in gastric and solid tumours?",
    "GPC3": "What is the therapeutic rationale for targeting GPC3 in hepatocellular carcinoma?",
    "FOLR1": "What is the therapeutic rationale for targeting FOLR1 (folate receptor alpha)?",
    "CD19": "What is the therapeutic rationale for targeting CD19 in B-cell malignancies?",
    "STEAP1": "What is the therapeutic rationale for targeting STEAP1 in prostate cancer?",
    "CD276": "What is the therapeutic rationale for targeting CD276 (B7-H3) in solid tumours?",
    "CA9": "What is the therapeutic rationale for targeting CA9 (CAIX) in hypoxic tumours?",
    "MET": "What is the therapeutic rationale for targeting MET in solid tumours?",
}


def _generic_cab(g: str) -> list[str]:
    return [q.format(g=g) for q in _GENERIC_CAB]


def quick_start_questions(symbol: str | None = None) -> list[str]:
    g = symbol or get_active_symbol()
    mech = _MECHANISM_QUESTION.get(
        g, f"What is the therapeutic rationale for targeting {g} in solid tumours?"
    )
    return [
        f"Which cancers have the strongest combination of {g} over-expression and survival impact?",
        f"What is the current {g}-targeted drug pipeline and which agents are in clinical trials?",
        mech,
        f"What DepMap evidence supports {g} as a cancer dependency?",
        f"Summarise {g} expression across TCGA cancer types with hazard ratios.",
        f"What are the {g} isoforms and which are most relevant for therapeutic targeting?",
    ]


def cab_questions(symbol: str | None = None) -> list[str]:
    """CAB prompts for the active gene — never falls back to CD46 for unknown symbols."""
    g = symbol or get_active_symbol()
    if g in _CAB_BY_SYMBOL:
        return list(_CAB_BY_SYMBOL[g])
    return _generic_cab(g)


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
    for s in ("FOLH1", "FAP", "SSTR2", "GRPR", "CD46", "EGFR", "XYZ"):
        qs = cab_questions(s)
        assert all(s in q or "{g}" not in q for q in qs)
        assert "CD46" not in qs[0] or s == "CD46"
        assert s in quick_start_questions(s)[0]
    print("agent_prompts_ok")
