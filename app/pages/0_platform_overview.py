"""
0_platform_overview.py — OncoBridge Intelligence landing page.

Covers all 15 research modules in 4 themed sections.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import streamlit as st
from components.styles import inject_global_css

inject_global_css()

# ---------------------------------------------------------------------------
# Hero
# ---------------------------------------------------------------------------
st.markdown(
    '<span class="lp-eyebrow">CD46 Precision Medicine · EurthTech Research</span>'
    '<h1 class="lp-headline">OncoBridge<br>Intelligence</h1>'
    '<p class="lp-sub">'
    'A multi-modal research platform integrating TCGA, HPA, STRING, ChEMBL, '
    'OpenTargets and Neo4j to accelerate CD46-targeted alpha-radioligand therapy '
    'from biomarker discovery to clinical strategy.'
    '</p>',
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="lp-stats">'
    '<div class="lp-stat"><span class="lp-stat-val">33</span><span class="lp-stat-lbl">Cancer Types</span></div>'
    '<div class="lp-stat"><span class="lp-stat-val">3,047</span><span class="lp-stat-lbl">KG Nodes</span></div>'
    '<div class="lp-stat"><span class="lp-stat-val">14</span><span class="lp-stat-lbl">Active Trials</span></div>'
    '<div class="lp-stat"><span class="lp-stat-val">15</span><span class="lp-stat-lbl">Modules</span></div>'
    '<div class="lp-stat"><span class="lp-stat-val">225Ac</span><span class="lp-stat-lbl">Alpha Emitter</span></div>'
    '</div>',
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _sec(label: str, variant: str) -> None:
    st.markdown(
        f'<div class="lp-sec lp-sec-{variant}">'
        f'<span class="lp-sec-txt">{label}</span>'
        '<span class="lp-sec-line"></span>'
        '</div>',
        unsafe_allow_html=True,
    )


def _card(icon, title, desc, chips, label_cls="mc-label-ind"):
    chip_html = "".join(f'<span class="mc-chip">{c}</span>' for c in chips)
    return (
        f'<div class="mc-wrap">'
        f'<span class="mc-ico">{icon}</span>'
        f'<span class="mc-label {label_cls}">Module</span>'
        f'<span class="mc-title">{title}</span>'
        f'<span class="mc-desc">{desc}</span>'
        f'<div class="mc-chips">{chip_html}</div>'
        '</div>'
    )


# ---------------------------------------------------------------------------
# Section 1 — Research Modules (7)
# ---------------------------------------------------------------------------
_sec("Research Modules", "ind")

col1, col2, col3 = st.columns(3)
with col1:
    with st.container(border=True):
        st.markdown(_card(
            "📊", "Expression Atlas",
            "Pan-cancer mRNA + protein expression across TCGA (33 cancers) and Human Protein Atlas (30 tissues).",
            ["33 Cancer Types", "Top: PRAD", "30 HPA Tissues"],
        ), unsafe_allow_html=True)
    st.page_link("pages/1_cd46_expression_atlas.py", label="Open module →")
with col2:
    with st.container(border=True):
        st.markdown(_card(
            "🎯", "Patient Selection",
            "225Ac-CD46 α-RLT eligibility — who qualifies? PSMA-low/CD46-high enrichment and AR-driven upregulation.",
            ["PSMA-low/CD46-high ~35%", "AR Effect ↑2–3×", "PRAD 75th pct 40"],
        ), unsafe_allow_html=True)
    st.page_link("pages/2_patient_selection.py", label="Open module →")
with col3:
    with st.container(border=True):
        st.markdown(_card(
            "📈", "Survival Outcomes",
            "CD46-High vs CD46-Low Kaplan-Meier curves and Cox hazard ratios across 33 TCGA cancers.",
            ["3 Significant Cancers", "PRAD HR 0.77", "OS + PFI Endpoints"],
        ), unsafe_allow_html=True)
    st.page_link("pages/3_survival_outcomes.py", label="Open module →")

col4, col5, col6 = st.columns(3)
with col4:
    with st.container(border=True):
        st.markdown(_card(
            "🕸️", "Biomedical Knowledge Graph",
            "Neo4j AuraDB integrating genes, proteins, diseases, drugs and clinical trials into a live interactive graph.",
            ["3,047 KG Nodes", "2,552 Edges", "10 Drug Nodes"],
        ), unsafe_allow_html=True)
    st.page_link("pages/4_biomedical_knowledge_graph.py", label="Open module →")
with col5:
    with st.container(border=True):
        st.markdown(_card(
            "🤖", "Research Assistant",
            "GPT-4o powered natural language interface with integrated knowledge-graph context and data-grounded answers.",
            ["GPT-4o Primary", "Gemini 2.5 Fallback", "3,047 Node Context"],
        ), unsafe_allow_html=True)
    st.page_link("pages/5_research_assistant.py", label="Open module →")
with col6:
    with st.container(border=True):
        st.markdown(_card(
            "🧬", "Biomarker Panel",
            "Clinical decision support for 225Ac-CD46 α-RLT with multi-biomarker scoring against the mCRPC cohort.",
            ["5 Biomarkers", "226 mCRPC Patients", "9,251 GENIE pts"],
        ), unsafe_allow_html=True)
    st.page_link("pages/6_biomarker_panel.py", label="Open module →")

col7, _, __ = st.columns(3)
with col7:
    with st.container(border=True):
        st.markdown(_card(
            "🔍", "KG Query Explorer",
            "Live Cypher interface to CD46 AuraDB with 10 pre-built query templates spanning 12 node labels.",
            ["10 Query Templates", "12 Node Labels", "15+ Rel Types"],
        ), unsafe_allow_html=True)
    st.page_link("pages/7_kg_query_explorer.py", label="Open module →")

# ---------------------------------------------------------------------------
# Section 2 — Clinical Tools (2)
# ---------------------------------------------------------------------------
_sec("Clinical Tools", "sky")

col8, col9, _ = st.columns(3)
with col8:
    with st.container(border=True):
        st.markdown(_card(
            "🎯", "Patient Eligibility Scorer",
            "Evidence-based candidate assessment for 225Ac-CD46 RLT across 25 TCGA cancer types and ~2,800 patients.",
            ["25 Cancer Types", "~2,800 Patients", "PRAD CD46-High 44%"],
            label_cls="mc-label-sky",
        ), unsafe_allow_html=True)
    st.page_link("pages/8_patient_eligibility.py", label="Open module →")
with col9:
    with st.container(border=True):
        st.markdown(_card(
            "🏆", "Competitive Landscape",
            "CD46 vs PSMA vs FAP — expression prevalence, clinical trial activity and differentiation analysis.",
            ["3 Targets Compared", "14 CD46 Trials", "Pluvicto Comparator"],
            label_cls="mc-label-sky",
        ), unsafe_allow_html=True)
    st.page_link("pages/9_competitive_landscape.py", label="Open module →")

# ---------------------------------------------------------------------------
# Section 3 — Biology & Pipeline (3)
# ---------------------------------------------------------------------------
_sec("Biology & Pipeline", "eme")

col10, col11, col12 = st.columns(3)
with col10:
    with st.container(border=True):
        st.markdown(_card(
            "🕸️", "PPI Network Explorer",
            "CD46 protein–protein interaction network from STRING DB v12 — 30 partners and 103 high-confidence interactions.",
            ["30 PPI Partners", "103 Interactions", "STRING High ≥0.7"],
            label_cls="mc-label-eme",
        ), unsafe_allow_html=True)
    st.page_link("pages/10_ppi_network.py", label="Open module →")
with col11:
    with st.container(border=True):
        st.markdown(_card(
            "💊", "Drug Pipeline Explorer",
            "CD46-targeting landscape — ADC, radioimmunotherapy and complement inhibitors across development stages.",
            ["10 Agents Tracked", "3 Drug Classes", "2 FDA Approved"],
            label_cls="mc-label-eme",
        ), unsafe_allow_html=True)
    st.page_link("pages/11_drug_pipeline.py", label="Open module →")
with col12:
    with st.container(border=True):
        st.markdown(_card(
            "⚗️", "Dosimetry & Safety Index",
            "Therapeutic index for 225Ac-CD46 α-RLT — normal vs tumour CD46 from 81 tissues supporting FOR46 Phase I.",
            ["81 HPA Tissues", "Tumour:Normal >3:1", "FOR46 n=56"],
            label_cls="mc-label-eme",
        ), unsafe_allow_html=True)
    st.page_link("pages/12_dosimetry_safety.py", label="Open module →")

# ---------------------------------------------------------------------------
# Section 4 — Clinical Strategy (2)
# ---------------------------------------------------------------------------
_sec("Clinical Strategy", "amb")

col13, col14, _ = st.columns(3)
with col13:
    with st.container(border=True):
        st.markdown(_card(
            "🔬", "Clinical Strategy Engine",
            "End-to-end development narrative: Target → Drug → Patient → Trial → Outcome. 5 stages, 14 trials.",
            ["5 Development Stages", "14 Trials", "Target 2030"],
            label_cls="mc-label-amb",
        ), unsafe_allow_html=True)
    st.page_link("pages/13_clinical_strategy_engine.py", label="Open module →")
with col14:
    with st.container(border=True):
        st.markdown(_card(
            "🔬", "Diagnostics & Early Detection",
            "CD46 from biomarker discovery to clinical companion diagnostic — GTEx, ClinVar, cBioPortal and PET imaging.",
            ["54 GTEx Tissues", "500 ClinVar Variants", "PET Imaging Active"],
            label_cls="mc-label-amb",
        ), unsafe_allow_html=True)
    st.page_link("pages/14_cd46_diagnostics.py", label="Open module →")

# ---------------------------------------------------------------------------
# Pipeline stepper
# ---------------------------------------------------------------------------
st.markdown("<br>", unsafe_allow_html=True)
st.markdown(
    """<div style="margin:40px 0 28px;border-top:1px solid #16243C;padding-top:36px;">
<div style="font-family:'Space Grotesk',sans-serif;font-size:11px;font-weight:700;
letter-spacing:0.14em;text-transform:uppercase;color:#4E637A;margin-bottom:20px;">
Drug Development Pipeline</div>
<div style="display:flex;align-items:center;gap:0;overflow-x:auto;">
""" + "".join(
        f'<div style="flex:1;min-width:110px;">'
        f'<div style="background:#0D1829;border-radius:8px;padding:14px 16px;border:1px solid #16243C;">'
        f'<div style="font-family:\'Space Grotesk\',sans-serif;font-size:20px;margin-bottom:8px;">{icon}</div>'
        f'<div style="font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:0.1em;color:{color};margin-bottom:5px;">{stage}</div>'
        f'<div style="font-size:12px;color:#7A90AB;line-height:1.5;">{detail}</div>'
        f'</div>'
        f'{"<div style=\'color:#16243C;font-size:20px;padding:0 8px;\'>→</div>" if i < 4 else ""}'
        f'</div>'
        for i, (icon, stage, color, detail) in enumerate([
            ("🎯", "Target Identification", "#818CF8", "CD46 overexpression Pan-cancer validated"),
            ("⚛️", "Drug Design", "#38BDF8", "225Ac α-emitter FOR46 antibody scaffold"),
            ("🧪", "Preclinical", "#34D399", "Dosimetry modelling FOR46 in vitro / in vivo"),
            ("🏥", "Phase I", "#FBBF24", "FOR46 trial n=56 Safety & dosing"),
            ("📊", "Phase II/III", "#F87171", "Expansion trials Efficacy readouts"),
        ])
    ) + "</div></div>",
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Research summary expander
# ---------------------------------------------------------------------------
with st.expander("📋 Platform Research Summary"):
    st.markdown("""
**CD46 as a therapeutic target** — Membrane Cofactor Protein (CD46/MCP) is systemically overexpressed
in prostate cancer (PRAD), particularly in castration-resistant disease. Its expression is inversely
correlated with PSMA in a significant patient subset, positioning it as a complementary RLT target.

**225Ac-CD46 α-RLT rationale** — Alpha particles deliver ultra-short-range, high-LET cytotoxicity.
CD46's tumour:normal expression ratio (>3:1 in most solid tumours) supports a favourable therapeutic index.
FOR46 (anti-CD46 antibody conjugate) has demonstrated safety in 56 mCRPC patients in Phase I.

**Platform coverage** — 15 analytical modules spanning expression profiling, patient stratification,
survival analysis, knowledge-graph reasoning, drug pipeline tracking, dosimetry modelling and
clinical strategy synthesis. Data sources: TCGA · HPA · GENIE · STRING · ChEMBL · OpenTargets ·
ClinicalTrials.gov · cBioPortal · GTEx · ClinVar · UniProt.
""")

