"""Page 11 — Drug Pipeline: CD46-targeting and RLT therapeutic landscape.

Static curated dataset — no KG dependency required.
Data: ClinicalTrials.gov · PubMed · FDA · ChEMBL (CC BY-SA 4.0)
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from components.styles import page_hero

# ── Theme ──────────────────────────────────────────────────────────────────────
_BG      = "#0D1829"
_LINE    = "#16243C"
_ORANGE  = "#FB923C"   # CD46-targeted
_INDIGO  = "#818CF8"   # PSMA-targeted
_GREEN   = "#34D399"   # Complement inhibitor
_AMBER   = "#FBBF24"
_TEAL    = "#2DD4BF"
_SLATE   = "#4E637A"
_TEXT    = "#94A3B8"
_LIGHT   = "#CBD5E1"

_PLOTLY_LAYOUT = dict(
    paper_bgcolor=_BG,
    plot_bgcolor=_BG,
    font=dict(family="Inter", color=_TEXT),
    margin=dict(l=10, r=20, t=20, b=40),
)

# ── Pipeline data (curated, public sources) ────────────────────────────────────
PIPELINE = pd.DataFrame([
    # ── CD46-targeting ──────────────────────────────────────────────────────
    {
        "Name":        "FOR46 (SAR-CD46)",
        "Target":      "CD46",
        "Modality":    "ADC",
        "Drug Class":  "CD46-Targeted",
        "Developer":   "Fortis Therapeutics / AstraZeneca",
        "Phase":       1,
        "Phase Label": "Phase 1",
        "Indication":  "mCRPC, Multiple Myeloma",
        "Isotope / Payload": "PBD (pyrrolobenzodiazepine)",
        "Mechanism":   "Anti-CD46 humanised IgG1 conjugated to topoisomerase-I inhibitor PBD warhead. "
                       "Receptor-mediated internalisation → lysosomal linker cleavage → intracellular cytotoxin. "
                       "Phase 1 expansion cohort: PSMA-low / CD46-positive mCRPC.",
        "NCT":         "NCT04407754",
        "Notes":       "AstraZeneca-backed. Phase 1 dose-escalation in mCRPC. Partial response in heavily "
                       "pre-treated PSMA-low/CD46-high patients (ASCO 2023 data). Independently validates "
                       "PSMA-low + CD46-high as the clinical selection criterion used in this platform.",
        "ChEMBL":      "—",
    },
    {
        "Name":        "BC8-CD46 (131I-BC8)",
        "Target":      "CD46",
        "Modality":    "RLT (β⁻)",
        "Drug Class":  "CD46-Targeted",
        "Developer":   "Fred Hutchinson / Academic",
        "Phase":       1,
        "Phase Label": "Phase 1",
        "Indication":  "AML, Multiple Myeloma",
        "Isotope / Payload": "131I (beta-emitter)",
        "Mechanism":   "Pretargeted radioimmunotherapy. Anti-CD46 bispecific antibody pre-positions at tumour; "
                       "131I-radiolabelled small molecule locks on after blood clearance (~24 h). "
                       "Reduces normal-tissue radiation vs direct-labelled full antibody.",
        "NCT":         "NCT (multiple Fred Hutch)",
        "Notes":       "Clinical proof-of-concept for CD46-targeted radioimmunotherapy. Good tolerability in "
                       "haematological malignancies. Provides human PK/dosimetry data directly applicable to "
                       "a solid-tumour 225Ac-CD46 programme.",
        "ChEMBL":      "—",
    },
    {
        "Name":        "225Ac-CD46-RLT",
        "Target":      "CD46",
        "Modality":    "RLT (α)",
        "Drug Class":  "CD46-Targeted",
        "Developer":   "Academic / Preclinical",
        "Phase":       0,
        "Phase Label": "Preclinical",
        "Indication":  "Pan-cancer (CD46+)",
        "Isotope / Payload": "225Ac (alpha-emitter)",
        "Mechanism":   "Anti-CD46 antibody conjugated to 225Ac via DOTA chelator. Alpha particles (5.8 MeV) "
                       "cause double-strand DNA breaks within 2–3 cell diameters (40–100 µm path length). "
                       "20× more DSBs per unit dose vs beta emitters.",
        "NCT":         "—",
        "Notes":       "Scientific rationale of this platform. Ideal for micrometastatic / bone-dominant mCRPC. "
                       "Short path length minimises bystander normal-tissue toxicity. No existing Phase 1.",
        "ChEMBL":      "—",
    },
    # ── PSMA-targeting (competitive reference) ──────────────────────────────
    {
        "Name":        "177Lu-PSMA-617 (Pluvicto)",
        "Target":      "PSMA (FOLH1)",
        "Modality":    "RLT (β⁻)",
        "Drug Class":  "PSMA-Targeted",
        "Developer":   "Novartis",
        "Phase":       4,
        "Phase Label": "FDA Approved",
        "Indication":  "PSMA+ mCRPC (post-ARPI + taxane)",
        "Isotope / Payload": "177Lu (beta-emitter)",
        "Mechanism":   "PSMA-617 targeting ligand conjugated to 177Lu. Beta particles irradiate PSMA-expressing "
                       "prostate cancer. Internalised for sustained intracellular irradiation. VISION trial: "
                       "rPFS HR 0.40, OS HR 0.62 vs best supportive care.",
        "NCT":         "NCT03511664 (VISION trial)",
        "Notes":       "FDA Approved 2022. Current SoC for PSMA+ mCRPC. Leaves ~35% PSMA-low/heterogeneous "
                       "patients unserved — the CD46 clinical whitespace.",
        "ChEMBL":      "CHEMBL4523781",
    },
    {
        "Name":        "225Ac-PSMA-617",
        "Target":      "PSMA (FOLH1)",
        "Modality":    "RLT (α)",
        "Drug Class":  "PSMA-Targeted",
        "Developer":   "Multiple / Academic",
        "Phase":       2,
        "Phase Label": "Phase 2",
        "Indication":  "PSMA+ mCRPC",
        "Isotope / Payload": "225Ac (alpha-emitter)",
        "Mechanism":   "Same PSMA-617 ligand as Pluvicto conjugated to 225Ac alpha-emitter. "
                       "Direct parallel to 225Ac-CD46 — same isotope, different target. "
                       "Under investigation in Pluvicto-refractory patients.",
        "NCT":         "Multiple",
        "Notes":       "Key parallel: shows 225Ac alpha-emitter delivery is clinically feasible at the PSMA target. "
                       "CD46 would use the same isotope chemistry — just a different targeting antibody. "
                       "Does NOT address PSMA-low patients.",
        "ChEMBL":      "—",
    },
    # ── Complement pathway inhibitors (mechanistic context) ─────────────────
    {
        "Name":        "Eculizumab (Soliris)",
        "Target":      "C5 (Complement)",
        "Modality":    "Monoclonal Antibody",
        "Drug Class":  "Complement Inhibitor",
        "Developer":   "Alexion / AstraZeneca",
        "Phase":       4,
        "Phase Label": "FDA Approved",
        "Indication":  "PNH, aHUS, gMG, NMOSD",
        "Isotope / Payload": "—",
        "Mechanism":   "Anti-C5 mAb. Blocks terminal complement — prevents C5a + C5b-9 (MAC) formation. "
                       "Relevance: validates complement as clinically druggable. CD46 regulates upstream "
                       "(C3b/C4b inactivation) — orthogonal target vs eculizumab's C5 block.",
        "NCT":         "Multiple",
        "Notes":       "Combination hypothesis: eculizumab protects normal liver (high CD46) during 225Ac-CD46 "
                       "dosing by blocking downstream complement activation. Reduces hepatotoxicity risk.",
        "ChEMBL":      "CHEMBL1201823",
    },
    {
        "Name":        "Ravulizumab (Ultomiris)",
        "Target":      "C5 (Complement)",
        "Modality":    "Monoclonal Antibody",
        "Drug Class":  "Complement Inhibitor",
        "Developer":   "Alexion / AstraZeneca",
        "Phase":       4,
        "Phase Label": "FDA Approved",
        "Indication":  "PNH, aHUS, NMOSD",
        "Isotope / Payload": "—",
        "Mechanism":   "Long-acting anti-C5 (engineered Fc for pH-dependent recycling). 8-week dosing vs "
                       "eculizumab's 2-week. Same downstream C5 block with improved PK.",
        "NCT":         "Multiple",
        "Notes":       "Next-gen eculizumab. 8-week dosing more compatible with RLT cycle intervals "
                       "than eculizumab's 2-week schedule — preferable co-administration partner.",
        "ChEMBL":      "CHEMBL4296393",
    },
])

PHASE_ORDER = {
    "Preclinical": 0, "Phase 1": 1, "Phase 2": 2, "Phase 3": 3, "FDA Approved": 4,
}
PIPELINE["Phase_num"] = PIPELINE["Phase Label"].map(PHASE_ORDER).fillna(0)

CLASS_COLORS = {
    "CD46-Targeted":      _ORANGE,
    "PSMA-Targeted":      _INDIGO,
    "Complement Inhibitor": _GREEN,
}
MODALITY_SHAPES = {
    "ADC":                 "diamond",
    "RLT (α)":             "star",
    "RLT (β⁻)":            "circle",
    "Monoclonal Antibody": "square",
}

# ── Page hero ─────────────────────────────────────────────────────────────────
st.markdown(
    page_hero(
        icon="💊",
        module_name="Drug Pipeline Explorer",
        purpose="CD46-targeting and RLT therapeutic landscape · ADC · radioimmunotherapy · "
                "complement inhibitors · clinical trial status",
        kpi_chips=[
            ("Agents Tracked", str(len(PIPELINE))),
            ("Drug Classes", "3"),
            ("FDA Approved", str(len(PIPELINE[PIPELINE["Phase Label"] == "FDA Approved"]))),
            ("225Ac Programmes", str(len(PIPELINE[PIPELINE["Isotope / Payload"].str.contains("225Ac", na=False)]))),
        ],
        source_badges=["ClinicalTrials", "ChEMBL", "FDA"],
    ),
    unsafe_allow_html=True,
)

# ── KPI metric strip ──────────────────────────────────────────────────────────
m1, m2, m3, m4, m5 = st.columns(5)
m1.metric("Agents Tracked", len(PIPELINE), "across 3 drug classes")
m2.metric("CD46-Targeting", len(PIPELINE[PIPELINE["Drug Class"] == "CD46-Targeted"]),
          "ADC + β-RLT + α-RLT")
m3.metric("FDA Approved", len(PIPELINE[PIPELINE["Phase Label"] == "FDA Approved"]),
          "PSMA + complement")
m4.metric("Modalities", PIPELINE["Modality"].nunique(), "ADC · RLT · mAb")
m5.metric("225Ac Programmes", len(PIPELINE[PIPELINE["Isotope / Payload"].str.contains("225Ac", na=False)]),
          "alpha-emitter frontier")
st.markdown("---")

# ── Tabs ──────────────────────────────────────────────────────────────────────
tab_overview, tab_cd46, tab_psma, tab_complement, tab_rationale = st.tabs([
    "📊 Pipeline Overview",
    "🎯 CD46 Agents",
    "☢️ PSMA Competitive",
    "🧬 Complement Context",
    "🔬 Combination Rationale",
])

# ─────────────────────────────────────────────────────────────────────────────
# TAB 1 — Pipeline Overview (swim-lane chart)
# ─────────────────────────────────────────────────────────────────────────────
with tab_overview:
    st.markdown("#### Clinical Development Landscape — Swim-Lane View")
    st.caption("Each marker = one agent · hover for mechanism detail · colour = drug class · shape = modality")

    df_sorted = PIPELINE.sort_values(["Drug Class", "Phase_num"], ascending=[True, False])
    phase_labels = {0: "Preclinical", 1: "Phase 1", 2: "Phase 2", 3: "Phase 3", 4: "Approved"}

    fig_swim = go.Figure()

    for phase_num in phase_labels:
        fig_swim.add_vline(x=phase_num, line=dict(color=_LINE, width=1, dash="dot"))

    for drug_class, color in CLASS_COLORS.items():
        df_cls = df_sorted[df_sorted["Drug Class"] == drug_class]
        for _, row in df_cls.iterrows():
            symb = MODALITY_SHAPES.get(row["Modality"], "circle")
            fig_swim.add_trace(go.Scatter(
                x=[row["Phase_num"]],
                y=[row["Name"]],
                mode="markers+text",
                marker=dict(
                    symbol=symb,
                    size=32 if row["Phase Label"] == "FDA Approved" else 22,
                    color=color,
                    opacity=0.92,
                    line=dict(width=2, color=_BG),
                ),
                text=[f"  {row['Phase Label']}"],
                textposition="middle right",
                textfont=dict(size=10, color=_LIGHT),
                hovertemplate=(
                    f"<b>{row['Name']}</b><br>"
                    f"Class: {row['Drug Class']}<br>"
                    f"Modality: {row['Modality']}<br>"
                    f"Phase: {row['Phase Label']}<br>"
                    f"Target: {row['Target']}<br>"
                    f"Developer: {row['Developer']}<br>"
                    f"Indication: {row['Indication']}<br>"
                    f"NCT: {row['NCT']}<br>"
                    f"<i>{row['Notes'][:120]}...</i><extra></extra>"
                ),
                name=drug_class,
                showlegend=False,
            ))

    for drug_class, color in CLASS_COLORS.items():
        fig_swim.add_trace(go.Scatter(
            x=[None], y=[None], mode="markers",
            marker=dict(size=12, color=color, symbol="circle"),
            name=drug_class, showlegend=True,
        ))
    for mod, shape in MODALITY_SHAPES.items():
        fig_swim.add_trace(go.Scatter(
            x=[None], y=[None], mode="markers",
            marker=dict(size=12, color=_SLATE, symbol=shape),
            name=f"Shape: {mod}", showlegend=True,
        ))

    fig_swim.update_layout(
        **_PLOTLY_LAYOUT,
        xaxis=dict(
            tickvals=list(phase_labels.keys()),
            ticktext=list(phase_labels.values()),
            showgrid=False, range=[-0.5, 4.9],
            title=None, color=_LIGHT,
        ),
        yaxis=dict(
            showgrid=True, gridcolor=_LINE,
            title=None, color=_LIGHT,
            autorange="reversed",
        ),
        legend=dict(
            bgcolor="rgba(13,24,41,0.90)", bordercolor=_LINE,
            borderwidth=1, font=dict(size=10, color=_LIGHT),
            x=1.01, y=1,
        ),
        height=500,
        margin=dict(l=10, r=270, t=20, b=40),
        hoverlabel=dict(bgcolor=_LINE, bordercolor="#475569", font=dict(color=_LIGHT, size=12)),
    )
    st.plotly_chart(fig_swim, use_container_width=True)
    st.caption(
        "◆ Diamond = ADC  ·  ★ Star = RLT (α)  ·  ● Circle = RLT (β⁻)  ·  ■ Square = Monoclonal Antibody  ·  "
        "Hover each marker for mechanism details and trial context."
    )

    st.markdown("---")
    st.markdown("**Complete Agent Summary**")
    summary_cols = ["Name", "Drug Class", "Modality", "Target", "Phase Label",
                    "Developer", "Indication", "Isotope / Payload"]
    st.dataframe(
        PIPELINE.sort_values(["Drug Class", "Phase_num"], ascending=[True, False])[summary_cols],
        use_container_width=True,
        height=340,
        hide_index=True,
    )

# ─────────────────────────────────────────────────────────────────────────────
# TAB 2 — CD46 Agents Detail
# ─────────────────────────────────────────────────────────────────────────────
with tab_cd46:
    st.markdown("#### CD46-Targeting Therapeutic Agents")

    df_cd46 = PIPELINE[PIPELINE["Drug Class"] == "CD46-Targeted"].sort_values(
        "Phase_num", ascending=False
    )

    # Phase timeline bar for CD46 agents
    phase_emoji = {"Preclinical": "🔬", "Phase 1": "🧪", "Phase 2": "⚗️", "FDA Approved": "✅"}
    for _, row in df_cd46.iterrows():
        emoji = phase_emoji.get(row["Phase Label"], "🔬")
        with st.expander(
            f"{emoji} **{row['Name']}** — {row['Phase Label']} · {row['Developer']}"
        ):
            col_left, col_right = st.columns([2, 1])
            with col_left:
                st.markdown(f"**Target:** {row['Target']}  |  **Modality:** {row['Modality']}  "
                            f"|  **Payload / Isotope:** `{row['Isotope / Payload']}`")
                st.markdown(f"**Indication:** {row['Indication']}")
                st.markdown("**Mechanism:**")
                st.markdown(f"> {row['Mechanism']}")
                if row["Notes"]:
                    st.success(f"**Clinical significance:** {row['Notes']}")
            with col_right:
                st.markdown(f"**Developer:** {row['Developer']}")
                if row["NCT"] != "—":
                    st.markdown(f"**NCT:** `{row['NCT']}`")
                if row["ChEMBL"] != "—":
                    st.markdown(f"**ChEMBL:** `{row['ChEMBL']}`")

    # 225Ac vs 177Lu vs 131I mechanism comparison
    st.markdown("---")
    st.markdown("#### Alpha vs Beta Emitter Comparison — 225Ac vs 177Lu vs 131I")
    iso_df = pd.DataFrame([
        {"Property": "Particle type",           "225Ac (alpha)": "Alpha particle",    "177Lu (beta)": "Beta particle",     "131I (beta)": "Beta particle"},
        {"Property": "Path length in tissue",   "225Ac (alpha)": "40–100 µm",         "177Lu (beta)": "2–3 mm",            "131I (beta)": "0.8 mm"},
        {"Property": "Cell diameters reached",  "225Ac (alpha)": "2–3 cells",         "177Lu (beta)": "100–200 cells",     "131I (beta)": "40–60 cells"},
        {"Property": "Linear energy transfer",  "225Ac (alpha)": "~80 keV/µm",        "177Lu (beta)": "~0.2 keV/µm",      "131I (beta)": "~0.2 keV/µm"},
        {"Property": "DNA double-strand breaks","225Ac (alpha)": "20× vs 177Lu",      "177Lu (beta)": "Baseline",          "131I (beta)": "Comparable"},
        {"Property": "Best tumour context",     "225Ac (alpha)": "Micromet / bone",   "177Lu (beta)": "Macrometastasis",   "131I (beta)": "Haematological"},
        {"Property": "CD46 programme",          "225Ac (alpha)": "225Ac-CD46-RLT",    "177Lu (beta)": "None (PSMA: Pluvicto)", "131I (beta)": "BC8-CD46"},
        {"Property": "Clinical status (CD46)",  "225Ac (alpha)": "Preclinical",       "177Lu (beta)": "Not applicable",    "131I (beta)": "Phase 1"},
    ])
    st.dataframe(iso_df, use_container_width=True, hide_index=True)

    st.info(
        "**Why 225Ac for mCRPC?** Micrometastatic osseous disease in mCRPC consists of small clusters "
        "of cells where a 2–3 mm beta-particle path overshoots the target. Actinium-225's 40–100 µm range "
        "matches the tumour cell cluster size — maximising on-target kill and minimising "
        "bystander toxicity in adjacent normal bone marrow."
    )

    st.markdown("---")
    st.markdown("**CD46 Programme Comparison**")
    cmp = ["Name", "Modality", "Phase Label", "Isotope / Payload", "Indication", "Developer"]
    st.dataframe(df_cd46[cmp].reset_index(drop=True), use_container_width=True, hide_index=True)
    st.success(
        "**Three independent programmes (FOR46, BC8-CD46, 225Ac-CD46) across three distinct "
        "delivery mechanisms** — all validating CD46 as a tractable surface target for "
        "antibody-mediated cancer therapy."
    )

# ─────────────────────────────────────────────────────────────────────────────
# TAB 3 — PSMA Competitive Reference
# ─────────────────────────────────────────────────────────────────────────────
with tab_psma:
    st.markdown("#### PSMA-Targeted RLT — Competitive Reference & Whitespace Map")

    df_psma = PIPELINE[PIPELINE["Drug Class"] == "PSMA-Targeted"]

    col1, col2 = st.columns([1.2, 1])

    with col1:
        st.markdown("**PSMA vs CD46: Head-to-Head**")
        comparison_data = {
            "Attribute": [
                "mCRPC expression prevalence",
                "PSMA-low / heterogeneous patients",
                "Pan-tumour utility",
                "Active clinical trials",
                "Approved agents",
                "225Ac programme",
                "ADC programme",
                "Immune evasion function",
                "Patient exclusion risk",
            ],
            "PSMA (FOLH1)": [
                "~85% at initial diagnosis",
                "~35% unserved by Pluvicto",
                "Prostate-restricted",
                "183",
                "2 (Pluvicto, PSMA-1007)",
                "225Ac-PSMA-617 (Phase 2)",
                "None",
                "No direct immune role",
                "High — PSMA-negative excluded",
            ],
            "CD46 (MCP)": [
                ">95% mCRPC (incl. PSMA-low)",
                "Maintained in PSMA-neg tumours",
                "25 TCGA cancer types",
                "14",
                "None — whitespace open",
                "This programme (Preclinical)",
                "FOR46 (Phase 1)",
                "Complement evasion hub",
                "Very low — ubiquitous expression",
            ],
        }
        st.dataframe(
            pd.DataFrame(comparison_data),
            use_container_width=True,
            hide_index=True,
        )

    with col2:
        st.markdown("**Active RLT Trial Volume**")
        fig_trials = go.Figure(go.Bar(
            x=["CD46", "PSMA", "FAP"],
            y=[14, 183, 31],
            marker=dict(
                color=[_ORANGE, _INDIGO, _GREEN],
                line=dict(color=_BG, width=1),
            ),
            text=[14, 183, 31],
            textposition="outside",
            textfont=dict(color=_LIGHT, size=14),
        ))
        fig_trials.update_layout(
            **_PLOTLY_LAYOUT,
            yaxis=dict(title="Active clinical trials", gridcolor=_LINE, color=_TEXT),
            xaxis=dict(showgrid=False, color=_LIGHT),
            height=280,
            margin=dict(l=10, r=20, t=10, b=40),
        )
        st.plotly_chart(fig_trials, use_container_width=True)

        m_c1, m_c2 = st.columns(2)
        m_c1.metric("PSMA trials", "183", "Saturated space")
        m_c2.metric("CD46 trials", "14", "First-mover open")

    st.warning(
        "**Strategic context:** PSMA matured from ~14 trials to 183 in ~8 years. "
        "CD46 is at the 14-trial inflection point today — the same stage PSMA was "
        "at in ~2014, 8 years before the VISION trial approval."
    )

    st.markdown("---")
    for _, row in df_psma.iterrows():
        with st.expander(f"**{row['Name']}** — {row['Phase Label']} · {row['Developer']}"):
            st.markdown(f"**Target:** {row['Target']} | **Modality:** {row['Modality']} "
                        f"| **Isotope:** `{row['Isotope / Payload']}`")
            st.markdown(f"**Indication:** {row['Indication']}")
            st.markdown(f"> {row['Mechanism']}")
            if row["Notes"]:
                st.info(f"💡 {row['Notes']}")

# ─────────────────────────────────────────────────────────────────────────────
# TAB 4 — Complement Inhibitors
# ─────────────────────────────────────────────────────────────────────────────
with tab_complement:
    st.markdown("#### Complement Pathway Inhibitors — Mechanistic Context")
    st.markdown(
        "Complement inhibitors are not CD46-targeting agents — they validate the **complement pathway as "
        "clinically druggable** and provide combination and safety context for a CD46 programme."
    )

    col_ec, col_ra = st.columns(2)
    df_comp = PIPELINE[PIPELINE["Drug Class"] == "Complement Inhibitor"]
    for col, (_, row) in zip([col_ec, col_ra], df_comp.iterrows()):
        with col:
            with st.container(border=True):
                st.markdown(f"### {row['Name']}")
                st.markdown(f"**Target:** {row['Target']}  |  **Developer:** {row['Developer']}")
                st.markdown(f"**Approved Indications:** {row['Indication']}")
                st.markdown(f"**Mechanism:** {row['Mechanism']}")
                if row["ChEMBL"] != "—":
                    st.markdown(f"**ChEMBL:** `{row['ChEMBL']}`")
                if row["Notes"]:
                    st.info(f"💡 **KG context:** {row['Notes']}")

    st.markdown("---")
    st.markdown("**Complement Cascade — Where Each Agent Acts**")

    ca, cb = st.columns(2)
    with ca:
        st.markdown("""
```
Classical / Lectin pathway        Alternative pathway
        ↓                                ↓
C1 → C4 → C2                     C3 → CFB → CFD
        ↓                                ↓
    C3 convertase ─────── C3 ──── C3 convertase
          ↓            cleavage         ↓
        C3b ←── CD46 + CFI ────→ iC3b (INACTIVE)
          ↓         ▲
    C5 convertase   └── This programme's target
          ↓
       C5a + C5b ←── Eculizumab / Ravulizumab
                         (Soliris / Ultomiris)
          ↓
    C5b-9 (MAC) — eliminated
```
""")
    with cb:
        cascade_df = pd.DataFrame([
            {"Level":       "C3b/C4b cleavage",
             "Regulator":   "CD46 + CFI",
             "Action":      "Upstream — prevents C3 amplification",
             "Drugged?":    "This programme"},
            {"Level":       "Convertase decay",
             "Regulator":   "CD55",
             "Action":      "Co-expressed with CD46 on tumour surface",
             "Drugged?":    "No approved agent"},
            {"Level":       "MAC inhibition",
             "Regulator":   "CD59",
             "Action":      "Third layer of tumour evasion",
             "Drugged?":    "No approved agent"},
            {"Level":       "Terminal C5",
             "Regulator":   "Eculizumab / Ravulizumab",
             "Action":      "Downstream C5 block — FDA approved",
             "Drugged?":    "Approved (Soliris / Ultomiris)"},
        ])
        st.dataframe(cascade_df, use_container_width=True, hide_index=True)

    st.success(
        "**Key distinction:** 225Ac-CD46 therapy targets the *tumour surface expression* of CD46 — "
        "the alpha particle kills the cancer cell regardless of CD46's downstream complement biology. "
        "Complement regulation is a passenger function, not the primary mechanism of cell kill."
    )

# ─────────────────────────────────────────────────────────────────────────────
# TAB 5 — Combination Rationale
# ─────────────────────────────────────────────────────────────────────────────
with tab_rationale:
    st.markdown("#### Combination Strategy Rationale")
    st.markdown(
        "KG traversal (Drug → Gene → Pathway → Disease) surfaces biologically motivated "
        "combination hypotheses. Each is graded by current evidence strength."
    )

    COMBOS = [
        {
            "title":    "225Ac-CD46 + ARPI (Enzalutamide / Abiraterone)",
            "priority": "High",
            "stage":    "Preclinical hypothesis",
            "rationale": "Androgen-receptor pathway inhibitors upregulate CD46 expression in mCRPC — "
                         "castration-resistant cells increase CD46 as part of immune evasion adaptation. "
                         "ARPI pre-treatment enriches the CD46-high population, improving tumour-to-normal "
                         "target density before 225Ac-CD46 dosing.",
            "evidence":  "Preclinical xenograft data; CD46 mRNA upregulation inversely correlated with AR "
                         "activity in TCGA PRAD cohort.",
        },
        {
            "title":    "225Ac-CD46 + Pluvicto (177Lu-PSMA-617)",
            "priority": "High",
            "stage":    "Clinical design hypothesis",
            "rationale": "PSMA and CD46 are largely non-overlapping antigens in heterogeneous tumours. "
                         "Sequential dosing — PSMA-RLT first, then CD46-RLT — could address both antigen-high "
                         "populations in series and prevent antigen-negative escape.",
            "evidence":  "Antigen co-expression data from DepMap; PSMA/CD46 inverse correlation in TCGA PRAD. "
                         "Clinical trial sequential design under consideration at academic centres.",
        },
        {
            "title":    "225Ac-CD46 + anti-PD-1 (checkpoint blockade)",
            "priority": "Medium",
            "stage":    "Preclinical hypothesis",
            "rationale": "Alpha particles cause immunogenic cell death (ICD) — releasing DAMPs and tumour "
                         "neoantigens. CD46 normally suppresses T-cell activation via Tr1 conversion; "
                         "destroying CD46-high cells may simultaneously restore anti-tumour immune surveillance. "
                         "Checkpoint blockade sustains and amplifies this effect.",
            "evidence":  "ICD from alpha emitters (published); CD46 → Tr1 conversion mechanism (STRING network).",
        },
        {
            "title":    "225Ac-CD46 + Eculizumab (liver protection strategy)",
            "priority": "Medium",
            "stage":    "Safety hypothesis",
            "rationale": "CD46 is highly expressed in normal liver. Eculizumab inhibits C5 (downstream of CD46) "
                         "and may reduce hepatotoxicity from inadvertent complement activation during "
                         "225Ac-CD46 RLT dosing in hepatic vasculature.",
            "evidence":  "Mechanistic basis only — complement biology in liver IHC; no clinical data.",
        },
        {
            "title":    "225Ac-CD46 + FOR46 (dual-payload approach)",
            "priority": "Exploratory",
            "stage":    "Future hypothesis",
            "rationale": "FOR46 (ADC / PBD cytotoxin) + 225Ac-CD46 (alpha RLT) — orthogonal kill mechanisms "
                         "at the same antigen. Non-overlapping toxicity profiles: DM4/PBD = GI/hepatic; "
                         "225Ac = haematological. Potential for dose-schedule interleaving.",
            "evidence":  "Mechanistic only — parallel CD46 programmes; no clinical co-dosing data.",
        },
    ]

    priority_color = {
        "High": _GREEN, "Medium": _AMBER, "Exploratory": _SLATE, "Safety hypothesis": _INDIGO,
    }

    for combo in COMBOS:
        pcolor = priority_color.get(combo["priority"], _SLATE)
        with st.expander(f"**{combo['title']}** — Priority: {combo['priority']}"):
            c_left, c_right = st.columns([3, 1])
            with c_left:
                st.markdown("**Biological Rationale:**")
                st.markdown(f"> {combo['rationale']}")
                st.markdown(f"**Supporting Evidence:** {combo['evidence']}")
            with c_right:
                st.markdown(f"**Stage:** `{combo['stage']}`")
                st.markdown(
                    f"<div style='background:{pcolor};color:{'#0D1829' if pcolor == _GREEN else 'white'};"
                    f"padding:6px 12px;border-radius:8px;text-align:center;font-weight:700;margin-top:8px;'>"
                    f"{combo['priority']}</div>",
                    unsafe_allow_html=True,
                )

    st.markdown("---")
    st.info(
        "**KG-derived insight:** These combinations are surfaced by traversing the "
        "Drug → Gene → Pathway → Disease path in the AuraDB knowledge graph. "
        "The STRING PPI network (page 10) provides the molecular mechanism "
        "connecting each combination partner to CD46's signalling neighbourhood. "
        "The GENIE 271,837-patient cohort (page 8) provides the real-world screening populations."
    )

st.markdown("---")
st.caption(
    "Sources: ClinicalTrials.gov · ChEMBL (CC BY-SA 4.0) · FDA drug approvals database · "
    "Published Phase 1 data (ASCO 2023: FOR46) · Fred Hutchinson Cancer Center publications. "
    "March 2026. Research use only."
)
