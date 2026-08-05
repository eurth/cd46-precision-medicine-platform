"""
0_platform_overview.py — OncoBridge Intelligence landing page.

Image-card grid layout. inject_global_css() is NOT called here;
streamlit_app.py calls it once per render.
"""
import os
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import streamlit as st
from dotenv import load_dotenv
from components.data_freeze import load_data_freeze, render_data_freeze_banner
from components.targets import get_active_symbol, list_symbols
from components.ui_kit import info_banner, metric_row

load_dotenv(Path(__file__).resolve().parents[2] / ".env")

for _k in ("NEO4J_URI", "NEO4J_USERNAME", "NEO4J_PASSWORD"):
    try:
        if _k in st.secrets and not os.environ.get(_k):
            os.environ[_k] = st.secrets[_k]
    except Exception:
        pass


@st.cache_resource(ttl=1800)
def _get_driver():
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


@st.cache_data(ttl=1800)
def _kg_stats():
    driver = _get_driver()
    if driver is None:
        return None
    try:
        with driver.session() as sess:
            total_nodes = sess.run("MATCH (n) RETURN count(n) AS c").single()["c"]
            total_rels = sess.run("MATCH ()-[r]->() RETURN count(r) AS c").single()["c"]
            active_trials = sess.run("MATCH (t:ClinicalTrial) RETURN count(t) AS c").single()["c"]
        return {
            "total_nodes": total_nodes,
            "total_rels": total_rels,
            "active_trials": active_trials,
        }
    except Exception:
        return None


_REGISTRY = list_symbols()
_N_TARGETS = len(_REGISTRY)
_ACTIVE = get_active_symbol()
_freeze = load_data_freeze()
# ponytail: offline fallback mirrors config/data_freeze.yaml Aura notes (~100k / ~289k)
_stats = _kg_stats()
_kg_nodes = f"{_stats['total_nodes']:,}" if _stats else "100,250"
_kg_rels = f"{_stats['total_rels']:,}" if _stats else "288,572"
_trial_count = f"{_stats['active_trials']:,}" if _stats else "~26.8k"
_freeze_label = _freeze.get("freeze_label") or _freeze.get("freeze_id") or "current"

# ---------------------------------------------------------------------------
# U2 landing — carousel + quick start (no duplicate OncoBridge hero title)
# ---------------------------------------------------------------------------
from components.landing_hero import render_hero_zone, render_start_here, render_target_carousel

render_hero_zone()
render_target_carousel()
render_start_here()
render_data_freeze_banner(compact=True)

metric_row(
    [
        {
            "title": "Registry Targets",
            "content": str(_N_TARGETS),
            "description": "Theranostic panel from config/targets.yaml",
        },
        {"title": "KG Nodes", "content": _kg_nodes, "description": "Neo4j knowledge graph"},
        {"title": "KG Edges", "content": _kg_rels, "description": "Relationships"},
        {"title": "Trial Nodes", "content": _trial_count, "description": "Clinical trial records"},
        {"title": "Use", "content": "Research", "description": "Not for clinical decisions"},
    ],
    key_prefix="overview_kpi",
)

info_banner(
    f"**{_N_TARGETS} registry targets** on one workbench — switch gene in the right rail. "
    f"Open any module below. Freeze: {_freeze_label}."
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _section_header(label: str, variant: str) -> None:
    st.markdown(
        f'<div class="lp-sec lp-sec-{variant}">'
        f'<span class="lp-sec-txt">{label}</span>'
        '<span class="lp-sec-line"></span>'
        '</div>',
        unsafe_allow_html=True,
    )


def _image_card(
    icon: str,
    title: str,
    desc: str,
    chips: list,
    variant: str,          # ind | sky | eme | amb
    bg_url: str = "",      # optional CSS background-image url(...)
) -> str:
    chips_html = "".join(f'<span class="mc-img-chip">{c}</span>' for c in chips)
    if bg_url:
        img_style = (
            f'background-image: url({bg_url}); background-size: cover; '
            f'background-position: center; '
        )
    else:
        img_style = ""
    overlay = (
        '<div style="position:absolute;inset:0;'
        'background:rgba(255,255,255,0.35);"></div>'
    )
    return (
        f'<div class="mc-img-card">'
        f'<div class="mc-img-top mc-img-top-{variant}" '
        f'style="position:relative;{img_style}">'
        f'{overlay if bg_url else ""}'
        f'<span style="position:relative;z-index:1;">{icon}</span>'
        f'</div>'
        f'<div class="mc-img-body">'
        f'<span class="mc-img-label mc-img-label-{variant}">Module</span>'
        f'<span class="mc-img-title">{title}</span>'
        f'<span class="mc-img-desc">{desc}</span>'
        f'<div class="mc-img-chips">{chips_html}</div>'
        f'</div>'
        f'</div>'
    )


def _render_module_row(cards: list[dict]) -> None:
    """Render up to 3 module cards per row with native st.page_link navigation."""
    cols = st.columns(3)
    for col, card in zip(cols, cards):
        with col:
            st.markdown(
                _image_card(
                    card["icon"],
                    card["title"],
                    card["desc"],
                    card["chips"],
                    card["variant"],
                    bg_url=card.get("bg_url", ""),
                ),
                unsafe_allow_html=True,
            )
            try:
                st.page_link(card["page"], label="Open module \u2192", use_container_width=True)
            except TypeError:
                st.page_link(card["page"], label="Open module \u2192")


# ---------------------------------------------------------------------------
# Section 1 — Research Hub (primary scientific surface)
# ---------------------------------------------------------------------------
_section_header("Research Hub", "ind")

_render_module_row([
    {
        "icon": "\U0001f578\ufe0f",
        "title": "Knowledge Graph",
        "desc": "Neo4j AuraDB integrating genes, proteins, diseases, drugs and clinical trials into a live graph.",
        "chips": [f"{_kg_nodes} Nodes", f"{_kg_rels} Edges", "Aura Free"],
        "variant": "ind",
        "page": "pages/4_biomedical_knowledge_graph.py",
    },
    {
        "icon": "\U0001f50d",
        "title": "KG Query Explorer",
        "desc": "Live Cypher interface with templates spanning the graph schema — primary research query surface.",
        "chips": ["Templates", "Cypher", "NL\u2192Cypher"],
        "variant": "ind",
        "page": "pages/7_kg_query_explorer.py",
    },
    {
        "icon": "\U0001f916",
        "title": "Research Assistant",
        "desc": "LLM assistant with knowledge-graph and literature context for research Q&A.",
        "chips": ["OpenRouter / Gemma", "KG Context", "PubMed"],
        "variant": "ind",
        "page": "pages/5_research_assistant.py",
    },
])

# ---------------------------------------------------------------------------
# Section 2 — Evidence modules (active-target slices)
# ---------------------------------------------------------------------------
_section_header("Evidence Modules", "sky")

_STRING_ACTIVE = (
    "https://string-db.org/api/image/network?identifiers="
    f"{_ACTIVE}"
    "&species=9606&network_flavor=confidence&caller_identity=oncobridge"
)

_render_module_row([
    {
        "icon": "\U0001f4ca",
        "title": "Expression Atlas",
        "desc": "Pan-cancer mRNA + protein expression across TCGA and Human Protein Atlas for the active target.",
        "chips": ["TCGA", "HPA", "Active gene"],
        "variant": "sky",
        "page": "pages/1_cd46_expression_atlas.py",
    },
    {
        "icon": "\U0001f3af",
        "title": "Patient Selection",
        "desc": "Eligibility stratification patterns from processed cohort slices for the active target.",
        "chips": ["Cohorts", "Thresholds", "Active gene"],
        "variant": "sky",
        "page": "pages/2_patient_selection.py",
    },
    {
        "icon": "\U0001f4c8",
        "title": "Survival Outcomes",
        "desc": "High vs low expression Kaplan-Meier and Cox hazard ratios across TCGA cancers.",
        "chips": ["OS + PFI", "Cox HR", "Active gene"],
        "variant": "sky",
        "page": "pages/3_survival_outcomes.py",
    },
])

_render_module_row([
    {
        "icon": "\U0001f9ec",
        "title": "Biomarker Panel",
        "desc": "Multi-biomarker clinical decision-support views keyed to the active registry target.",
        "chips": ["GENIE", "Co-occurrence", "Active gene"],
        "variant": "sky",
        "page": "pages/6_biomarker_panel.py",
    },
    {
        "icon": "\U0001f578\ufe0f",
        "title": "PPI Network Explorer",
        "desc": "Protein–protein interaction network from STRING DB centred on the active gene.",
        "chips": ["STRING", "Partners", "CC BY 4.0"],
        "variant": "sky",
        "page": "pages/10_ppi_network.py",
        "bg_url": _STRING_ACTIVE,
    },
])

# ---------------------------------------------------------------------------
# Section 3 — Pipeline & strategy (gene-parameterized modules)
# ---------------------------------------------------------------------------
_section_header("Pipeline & Strategy", "amb")

_render_module_row([
    {
        "icon": "\U0001f3af",
        "title": "Eligibility Scorer",
        "desc": "Evidence-based candidate assessment across TCGA cancer types for the active target.",
        "chips": ["TCGA", "Eligibility", "Active gene"],
        "variant": "amb",
        "page": "pages/8_patient_eligibility.py",
    },
    {
        "icon": "\U0001f3c6",
        "title": "Competitive Landscape",
        "desc": f"Side-by-side expression and trial context across {_N_TARGETS} registry targets.",
        "chips": [f"{_N_TARGETS} Targets", "Live compare", "Trials"],
        "variant": "amb",
        "page": "pages/9_competitive_landscape.py",
    },
    {
        "icon": "\U0001f48a",
        "title": "Drug Pipeline Explorer",
        "desc": "ADC / RLT / inhibitor landscape from ClinicalTrials.gov and ChEMBL slices.",
        "chips": ["ChEMBL", "CT.gov", "Active gene"],
        "variant": "amb",
        "page": "pages/11_drug_pipeline.py",
    },
])

_render_module_row([
    {
        "icon": "\u2697\ufe0f",
        "title": "Dosimetry & Safety Index",
        "desc": "Therapeutic-index framing — normal vs tumour expression (HPA / GTEx) for the active gene.",
        "chips": ["HPA", "GTEx", "Tumour:Normal"],
        "variant": "amb",
        "page": "pages/12_dosimetry_safety.py",
    },
    {
        "icon": "\U0001f52c",
        "title": "Clinical Strategy Engine",
        "desc": "End-to-end narrative: Target \u2192 Drug \u2192 Patient \u2192 Trial \u2192 Outcome.",
        "chips": ["5 Stages", "Active gene", "Trials"],
        "variant": "amb",
        "page": "pages/13_clinical_strategy_engine.py",
    },
    {
        "icon": "\U0001f9ec",
        "title": "Diagnostics & Early Detection",
        "desc": "Companion-diagnostic framing — GTEx, ClinVar, cBioPortal, imaging context.",
        "chips": ["GTEx", "ClinVar", "Active gene"],
        "variant": "amb",
        "page": "pages/14_cd46_diagnostics.py",
    },
])

# ---------------------------------------------------------------------------
# Module pathway (registry-agnostic)
# ---------------------------------------------------------------------------
st.markdown("<br>", unsafe_allow_html=True)

_stages = [
    ("\U0001f3af", "Target ID",    "#2563EB", "Expression \u00b7 Essentiality \u00b7 Selectivity"),
    ("\u269b\ufe0f",  "Drug Design", "#0284C7", "Modality fit \u00b7 Payload \u00b7 Linker"),
    ("\U0001f9ea", "Preclinical",  "#059669", "Dosimetry \u00b7 Safety index \u00b7 PPI"),
    ("\U0001f3e5", "Phase I",      "#D97706", "First-in-human \u00b7 Safety \u00b7 Imaging"),
    ("\U0001f4ca", "Phase II/III", "#E11D48", "Expansion \u00b7 Efficacy \u00b7 Strategy"),
]

_s = ""
for i, (ico, stage, col, detail) in enumerate(_stages):
    _s += (
        f'<div style="flex:1;min-width:110px;">'
        f'<div class="ob-pipeline-step">'
        f'<div style="font-size:22px;margin-bottom:10px;">{ico}</div>'
        f'<div class="ob-pipeline-step-title" style="color:{col};">{stage}</div>'
        f'<div class="ob-pipeline-step-detail">{detail}</div>'
        f'</div></div>'
    )
    if i < len(_stages) - 1:
        _s += '<div class="ob-pipeline-arrow">\u2192</div>'

st.markdown(
    f'<div class="ob-pipeline-wrap">'
    f'<div class="ob-pipeline-label">Research pathway \u00b7 {_N_TARGETS} registry targets</div>'
    f'<div style="display:flex;align-items:stretch;gap:0;overflow-x:auto;">{_s}</div>'
    '</div>',
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Platform research summary
# ---------------------------------------------------------------------------
with st.expander("\U0001f4cb Platform Research Summary"):
    st.markdown(f"""
**Registry-first workbench** \u2014 OncoBridge covers **{_N_TARGETS} theranostic targets**
({", ".join(_REGISTRY[:8])}{", \u2026" if _N_TARGETS > 8 else ""}) from `config/targets.yaml`.
Switch the active gene in the right rail; every module reads that selection.

**Example depth** \u2014 CD46 is one deep reference slice among many (α-RLT / complement biology);
FOLH1, FAP, EGFR, ERBB2 and the ADC/RLT panel share the same module surfaces at varying data tiers.

**Coverage** \u2014 Analytical modules spanning expression, stratification, survival, knowledge-graph
reasoning, drug pipeline, dosimetry and clinical strategy.  
Data freeze: {_freeze_label}.  
Sources: TCGA \u00b7 HPA \u00b7 GENIE \u00b7 STRING \u00b7 ChEMBL \u00b7 OpenTargets \u00b7 ClinicalTrials.gov \u00b7
cBioPortal \u00b7 GTEx \u00b7 ClinVar \u00b7 UniProt.
""")
