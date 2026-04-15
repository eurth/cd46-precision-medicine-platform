"""
0_platform_overview.py — OncoBridge Intelligence landing page.

Image-card grid layout. inject_global_css() is NOT called here;
streamlit_app.py calls it once per render.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import streamlit as st

# ---------------------------------------------------------------------------
# Hero — no eyebrow (duplicates topbar), just headline + sub + stats bar
# ---------------------------------------------------------------------------
st.markdown(
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
    '<div class="lp-stat"><span class="lp-stat-val">33</span>'
    '<span class="lp-stat-lbl">Cancer Types</span></div>'
    '<div class="lp-stat"><span class="lp-stat-val">3,047</span>'
    '<span class="lp-stat-lbl">KG Nodes</span></div>'
    '<div class="lp-stat"><span class="lp-stat-val">14</span>'
    '<span class="lp-stat-lbl">Active Trials</span></div>'
    '<div class="lp-stat"><span class="lp-stat-val">15</span>'
    '<span class="lp-stat-lbl">Modules</span></div>'
    '<div class="lp-stat"><span class="lp-stat-val">225Ac</span>'
    '<span class="lp-stat-lbl">Alpha Emitter</span></div>'
    '</div>',
    unsafe_allow_html=True,
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
    page_path: str,
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
    # Overlay so emoji is always readable
    overlay = (
        '<div style="position:absolute;inset:0;'
        f'background:rgba(7,16,31,0.55);"></div>'
    )
    return (
        f'<div class="mc-img-card">'
        # --- Image / gradient top ---
        f'<div class="mc-img-top mc-img-top-{variant}" '
        f'style="position:relative;{img_style}">'
        f'{overlay if bg_url else ""}'
        f'<span style="position:relative;z-index:1;">{icon}</span>'
        f'</div>'
        # --- Body ---
        f'<div class="mc-img-body">'
        f'<span class="mc-img-label mc-img-label-{variant}">Module</span>'
        f'<span class="mc-img-title">{title}</span>'
        f'<span class="mc-img-desc">{desc}</span>'
        f'<div class="mc-img-chips">{chips_html}</div>'
        f'<a class="mc-img-link" href="{page_path}">Open module \u2192</a>'
        f'</div>'
        f'</div>'
    )


def _grid(*cards: str) -> str:
    """Wrap cards in equal-height CSS grid (3 columns)."""
    items = "".join(cards)
    return (
        '<div style="display:grid;grid-template-columns:repeat(3,1fr);'
        'grid-auto-rows:1fr;gap:16px;margin-bottom:8px;">'
        f'{items}'
        '</div>'
    )


# ---------------------------------------------------------------------------
# Section 1 — Research Modules (pages 1–7)
# ---------------------------------------------------------------------------
_section_header("Research Modules", "ind")

# HPA CD46 IHC image (public, CC-BY Human Protein Atlas)
_HPA_CD46 = "https://www.proteinatlas.org/images/2702/ihc_hpa007568_prostate.jpg"
# RCSB PDB CD46 structure (PDB 2QRM, public domain)
_PDB_CD46 = "https://cdn.rcsb.org/images/structures/qr/2qrm/2qrm_assembly-1.jpeg"
# STRING network image for CD46
_STRING_CD46 = "https://string-db.org/api/image/network?identifiers=CD46&species=9606&network_flavor=confidence&caller_identity=oncobridge"

st.markdown(_grid(
    _image_card(
        "\U0001f4ca", "Expression Atlas",
        "Pan-cancer mRNA + protein expression across TCGA (33 cancers) and Human Protein Atlas (30 tissues).",
        ["33 Cancer Types", "Top: PRAD", "log\u2082\u22652.5"],
        "ind", "/1_cd46_expression_atlas",
        bg_url=_HPA_CD46,
    ),
    _image_card(
        "\U0001f3af", "Patient Selection",
        "225Ac-CD46 \u03b1-RLT eligibility \u2014 PSMA-low/CD46-high enrichment and AR-driven upregulation.",
        ["PSMA-low ~35%", "AR Effect \u21912\u20133\u00d7", "PRAD 75th: 40"],
        "ind", "/2_patient_selection",
    ),
    _image_card(
        "\U0001f4c8", "Survival Outcomes",
        "CD46-High vs CD46-Low Kaplan-Meier curves and Cox hazard ratios across 33 TCGA cancers.",
        ["3 Significant", "PRAD HR: 0.77", "OS + PFI"],
        "ind", "/3_survival_outcomes",
    ),
), unsafe_allow_html=True)

st.markdown(_grid(
    _image_card(
        "\U0001f578\ufe0f", "Knowledge Graph",
        "Neo4j AuraDB integrating genes, proteins, diseases, drugs and clinical trials into a live graph.",
        ["3,047 Nodes", "2,552 Edges", "10 Drug Nodes"],
        "ind", "/4_biomedical_knowledge_graph",
    ),
    _image_card(
        "\U0001f916", "Research Assistant",
        "GPT-4o natural language interface with integrated knowledge-graph context and data-grounded answers.",
        ["GPT-4o Primary", "Gemini 2.5 Fallback", "3,047 Nodes"],
        "ind", "/5_research_assistant",
    ),
    _image_card(
        "\U0001f9ec", "Biomarker Panel",
        "Clinical decision support for 225Ac-CD46 \u03b1-RLT with multi-biomarker scoring — mCRPC cohort.",
        ["5 Biomarkers", "226 mCRPC Pts", "9,251 GENIE pts"],
        "ind", "/6_biomarker_panel",
    ),
), unsafe_allow_html=True)

# Row 3: only 1 card — spans 1/3 width; use single-column grid
st.markdown(
    '<div style="display:grid;grid-template-columns:repeat(3,1fr);gap:16px;margin-bottom:8px;">'
    + _image_card(
        "\U0001f50d", "KG Query Explorer",
        "Live Cypher interface to CD46 AuraDB with 10 pre-built query templates spanning 12 node labels.",
        ["10 Templates", "12 Node Labels", "15+ Rel Types"],
        "ind", "/7_kg_query_explorer",
    )
    + '</div>',
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Section 2 — Clinical Tools (pages 8–9)
# ---------------------------------------------------------------------------
_section_header("Clinical Tools", "sky")

st.markdown(
    '<div style="display:grid;grid-template-columns:repeat(3,1fr);gap:16px;margin-bottom:8px;">'
    + _image_card(
        "\U0001f3af", "Eligibility Scorer",
        "Evidence-based candidate assessment for 225Ac-CD46 RLT across 25 TCGA cancer types (~2,800 patients).",
        ["25 Cancer Types", "~2,800 Patients", "PRAD: 44%"],
        "sky", "/8_patient_eligibility",
    )
    + _image_card(
        "\U0001f3c6", "Competitive Landscape",
        "CD46 vs PSMA vs FAP \u2014 expression prevalence, clinical trial activity and differentiation.",
        ["3 Targets", "14 CD46 Trials", "vs Pluvicto"],
        "sky", "/9_competitive_landscape",
    )
    + '</div>',
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Section 3 — Biology & Pipeline (pages 10–12)
# ---------------------------------------------------------------------------
_section_header("Biology & Pipeline", "eme")

st.markdown(_grid(
    _image_card(
        "\U0001f578\ufe0f", "PPI Network Explorer",
        "CD46 protein\u2013protein interaction network from STRING DB v12 \u2014 30 partners, 103 interactions.",
        ["30 Partners", "103 Interactions", "STRING \u22650.7"],
        "eme", "/10_ppi_network",
        bg_url=_STRING_CD46,
    ),
    _image_card(
        "\U0001f48a", "Drug Pipeline Explorer",
        "CD46-targeting landscape \u2014 ADC, radioimmunotherapy and complement inhibitors across all stages.",
        ["10 Agents", "3 Drug Classes", "2 FDA Approved"],
        "eme", "/11_drug_pipeline",
        bg_url=_PDB_CD46,
    ),
    _image_card(
        "\u2697\ufe0f", "Dosimetry & Safety Index",
        "Therapeutic index for 225Ac-CD46 \u03b1-RLT \u2014 normal vs tumour CD46 from 81 HPA tissues.",
        ["81 HPA Tissues", "Tumour:Normal >3:1", "FOR46 n=56"],
        "eme", "/12_dosimetry_safety",
    ),
), unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Section 4 — Clinical Strategy (pages 13–14)
# ---------------------------------------------------------------------------
_section_header("Clinical Strategy", "amb")

st.markdown(
    '<div style="display:grid;grid-template-columns:repeat(3,1fr);gap:16px;margin-bottom:8px;">'
    + _image_card(
        "\U0001f52c", "Clinical Strategy Engine",
        "End-to-end narrative: Target \u2192 Drug \u2192 Patient \u2192 Trial \u2192 Outcome. 5 stages, 14 trials.",
        ["5 Stages", "14 Trials", "Target: 2030"],
        "amb", "/13_clinical_strategy_engine",
    )
    + _image_card(
        "\U0001f9ec", "Diagnostics & Early Detection",
        "CD46 from biomarker discovery to companion diagnostic \u2014 GTEx, ClinVar, cBioPortal, PET imaging.",
        ["54 GTEx Tissues", "500 ClinVar Vars", "PET: Active"],
        "amb", "/14_cd46_diagnostics",
    )
    + '</div>',
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Drug development pipeline stepper
# ---------------------------------------------------------------------------
st.markdown("<br>", unsafe_allow_html=True)

_stages = [
    ("\U0001f3af", "Target ID",    "#818CF8", "CD46 overexpression \u00b7 Pan-cancer validated"),
    ("\u269b\ufe0f",  "Drug Design", "#38BDF8", "225Ac \u03b1-emitter \u00b7 FOR46 antibody"),
    ("\U0001f9ea", "Preclinical",  "#34D399", "Dosimetry \u00b7 FOR46 in vitro/in vivo"),
    ("\U0001f3e5", "Phase I",      "#FBBF24", "FOR46 trial \u00b7 n=56 \u00b7 Safety"),
    ("\U0001f4ca", "Phase II/III", "#F87171", "Expansion trials \u00b7 Efficacy"),
]

_s = ""
for i, (ico, stage, col, detail) in enumerate(_stages):
    _s += (
        f'<div style="flex:1;min-width:110px;">'
        f'<div style="background:#0D1829;border-radius:8px;padding:16px 14px;'
        f'border:1px solid #16243C;height:100%;box-sizing:border-box;">'
        f'<div style="font-size:22px;margin-bottom:10px;">{ico}</div>'
        f'<div style="font-size:10px;font-weight:700;text-transform:uppercase;'
        f'letter-spacing:0.1em;color:{col};margin-bottom:6px;">{stage}</div>'
        f'<div style="font-size:11.5px;color:#7A90AB;line-height:1.5;">{detail}</div>'
        f'</div></div>'
    )
    if i < len(_stages) - 1:
        # Visible arrow
        _s += (
            '<div style="color:#4E637A;font-size:18px;padding:0 6px;'
            'align-self:center;flex-shrink:0;">\u2192</div>'
        )

st.markdown(
    '<div style="margin:40px 0 28px;border-top:1px solid #16243C;padding-top:36px;">'
    '<div style="font-family:\'Space Grotesk\',sans-serif;font-size:11px;font-weight:700;'
    'letter-spacing:0.14em;text-transform:uppercase;color:#4E637A;margin-bottom:20px;">'
    'Drug Development Pipeline</div>'
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
