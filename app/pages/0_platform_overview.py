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
from components.data_freeze import render_data_freeze_banner
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


_stats = _kg_stats()
_kg_nodes = f"{_stats['total_nodes']:,}" if _stats else "3,068"
_kg_rels = f"{_stats['total_rels']:,}" if _stats else "2,517"
_trial_count = str(_stats["active_trials"]) if _stats else "14"

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
        {"title": "Registry Targets", "content": "5", "description": "CD46, FOLH1, FAP, SSTR2, GRPR"},
        {"title": "KG Nodes", "content": _kg_nodes, "description": "Neo4j knowledge graph"},
        {"title": "KG Edges", "content": _kg_rels, "description": "Relationships"},
        {"title": "Trial Nodes", "content": _trial_count, "description": "Clinical trial records"},
        {"title": "Use", "content": "Research", "description": "Not for clinical decisions"},
    ],
    key_prefix="overview_kpi",
)

info_banner(
    "Open any module below, or use the **right rail** to switch target and data perspective. "
    "Five theranostic targets on one workbench — CD46 is the deepest reference case study."
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
# Section 2 — Evidence modules (currently CD46-loaded data)
# ---------------------------------------------------------------------------
_section_header("Evidence Modules", "sky")

# RCSB PDB CD46 structure (PDB 2QRM, public domain)
_PDB_CD46 = "https://cdn.rcsb.org/images/structures/qr/2qrm/2qrm_assembly-1.jpeg"
# STRING network image for CD46
_STRING_CD46 = "https://string-db.org/api/image/network?identifiers=CD46&species=9606&network_flavor=confidence&caller_identity=oncobridge"

_render_module_row([
    {
        "icon": "\U0001f4ca",
        "title": "Expression Atlas",
        "desc": "Pan-cancer mRNA + protein expression across TCGA (33 cancers) and Human Protein Atlas (30 tissues).",
        "chips": ["33 Cancer Types", "Top: PRAD", "log\u2082\u22652.5"],
        "variant": "sky",
        "page": "pages/1_cd46_expression_atlas.py",
    },
    {
        "icon": "\U0001f3af",
        "title": "Patient Selection",
        "desc": "Eligibility stratification patterns (currently CD46 case-study cohort views).",
        "chips": ["PSMA-low ~35%", "AR Effect \u21912\u20133\u00d7", "PRAD 75th: 40"],
        "variant": "sky",
        "page": "pages/2_patient_selection.py",
    },
    {
        "icon": "\U0001f4c8",
        "title": "Survival Outcomes",
        "desc": "High vs low expression Kaplan-Meier and Cox hazard ratios across TCGA cancers.",
        "chips": ["3 Significant", "PRAD HR: 0.77", "OS + PFI"],
        "variant": "sky",
        "page": "pages/3_survival_outcomes.py",
    },
])

_render_module_row([
    {
        "icon": "\U0001f9ec",
        "title": "Biomarker Panel",
        "desc": "Multi-biomarker clinical decision support views (CD46 case-study mCRPC cohort).",
        "chips": ["5 Biomarkers", "226 mCRPC Pts", "9,251 GENIE pts"],
        "variant": "sky",
        "page": "pages/6_biomarker_panel.py",
    },
    {
        "icon": "\U0001f578\ufe0f",
        "title": "PPI Network Explorer",
        "desc": "Protein–protein interaction network from STRING DB (seeded on case-study target).",
        "chips": ["STRING", "Partners", "CC BY 4.0"],
        "variant": "sky",
        "page": "pages/10_ppi_network.py",
        "bg_url": _STRING_CD46,
    },
])

# ---------------------------------------------------------------------------
# Section 3 — Case Study: CD46 α-RLT
# ---------------------------------------------------------------------------
_section_header("Case Study · CD46 α-RLT", "amb")

_render_module_row([
    {
        "icon": "\U0001f3af",
        "title": "Eligibility Scorer",
        "desc": "Evidence-based candidate assessment for 225Ac-CD46 RLT across TCGA cancer types.",
        "chips": ["25 Cancer Types", "~2,800 Patients", "PRAD: 44%"],
        "variant": "amb",
        "page": "pages/8_patient_eligibility.py",
    },
    {
        "icon": "\U0001f3c6",
        "title": "Competitive Landscape",
        "desc": "CD46 vs PSMA vs FAP — expression prevalence, trial activity and differentiation.",
        "chips": ["3 Targets", "14 CD46 Trials", "vs Pluvicto"],
        "variant": "amb",
        "page": "pages/9_competitive_landscape.py",
    },
    {
        "icon": "\U0001f48a",
        "title": "Drug Pipeline Explorer",
        "desc": "CD46-targeting landscape — ADC, radioimmunotherapy and complement inhibitors.",
        "chips": ["10 Agents", "3 Drug Classes", "2 FDA Approved"],
        "variant": "amb",
        "page": "pages/11_drug_pipeline.py",
        "bg_url": _PDB_CD46,
    },
])

_render_module_row([
    {
        "icon": "\u2697\ufe0f",
        "title": "Dosimetry & Safety Index",
        "desc": "Therapeutic index framing for 225Ac-CD46 α-RLT — normal vs tumour CD46 (HPA).",
        "chips": ["81 HPA Tissues", "Tumour:Normal", "FOR46 n=56"],
        "variant": "amb",
        "page": "pages/12_dosimetry_safety.py",
    },
    {
        "icon": "\U0001f52c",
        "title": "Clinical Strategy Engine",
        "desc": "End-to-end narrative: Target → Drug → Patient → Trial → Outcome (case study).",
        "chips": ["5 Stages", "14 Trials", "Target: 2030"],
        "variant": "amb",
        "page": "pages/13_clinical_strategy_engine.py",
    },
    {
        "icon": "\U0001f9ec",
        "title": "Diagnostics & Early Detection",
        "desc": "CD46 companion-diagnostic framing — GTEx, ClinVar, cBioPortal, PET imaging.",
        "chips": ["54 GTEx Tissues", "500 ClinVar Vars", "PET: Active"],
        "variant": "amb",
        "page": "pages/14_cd46_diagnostics.py",
    },
])

# ---------------------------------------------------------------------------
# Case-study pipeline stepper (CD46)
# ---------------------------------------------------------------------------
st.markdown("<br>", unsafe_allow_html=True)

_stages = [
    ("\U0001f3af", "Target ID",    "#2563EB", "CD46 overexpression \u00b7 Pan-cancer validated"),
    ("\u269b\ufe0f",  "Drug Design", "#0284C7", "225Ac \u03b1-emitter \u00b7 FOR46 antibody"),
    ("\U0001f9ea", "Preclinical",  "#059669", "Dosimetry \u00b7 FOR46 in vitro/in vivo"),
    ("\U0001f3e5", "Phase I",      "#D97706", "FOR46 trial \u00b7 n=56 \u00b7 Safety"),
    ("\U0001f4ca", "Phase II/III", "#E11D48", "Expansion trials \u00b7 Efficacy"),
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
    f'<div class="ob-pipeline-label">Case Study Pipeline \u00b7 CD46 \u03b1-RLT</div>'
    f'<div style="display:flex;align-items:stretch;gap:0;overflow-x:auto;">{_s}</div>'
    '</div>',
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Platform research summary
# ---------------------------------------------------------------------------
with st.expander("\U0001f4cb Platform Research Summary"):
    st.markdown("""
**CD46 as a therapeutic target** \u2014 Membrane Cofactor Protein (CD46/MCP) is systemically
overexpressed in prostate cancer (PRAD), particularly in castration-resistant disease. Its
expression is inversely correlated with PSMA in a significant patient subset, positioning
it as a complementary RLT target.

**225Ac-CD46 \u03b1-RLT rationale** \u2014 Alpha particles deliver ultra-short-range, high-LET
cytotoxicity. CD46\u2019s tumour:normal expression ratio (>3:1 in most solid tumours) supports a
favourable therapeutic index. FOR46 has demonstrated safety in 56 mCRPC patients in Phase\u00a0I.

**Platform coverage** \u2014 15 analytical modules spanning expression profiling, patient
stratification, survival analysis, knowledge-graph reasoning, drug pipeline tracking,
dosimetry modelling and clinical strategy synthesis.  
Data sources: TCGA \u00b7 HPA \u00b7 GENIE \u00b7 STRING \u00b7 ChEMBL \u00b7 OpenTargets \u00b7 ClinicalTrials.gov \u00b7
cBioPortal \u00b7 GTEx \u00b7 ClinVar \u00b7 UniProt.
""")
