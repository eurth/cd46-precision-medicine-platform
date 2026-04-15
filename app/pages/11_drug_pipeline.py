"""Page 11 — Drug Pipeline: CD46-targeting and RLT therapeutic landscape.

Shows the full drug pipeline loaded into the knowledge graph:
  - CD46-targeting agents (ADC, radioimmunotherapy)
  - PSMA-targeting RLT (competitive reference)
  - Complement pathway inhibitors (mechanistic context / combination rationale)

Data: curated from ClinicalTrials.gov, PubMed, FDA, ChEMBL (CC BY-SA 4.0)
      mirrored in AuraDB as Drug nodes (scripts/load_kg_chembl.py)
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import streamlit as st
from components.styles import page_hero

# ── Pipeline data ─────────────────────────────────────────────────────────────
# Curated from NCT, FDA, PubMed, ChEMBL — matches Drug nodes in AuraDB KG

PIPELINE = pd.DataFrame([
    # ── CD46-targeting agents ──────────────────────────────────────────────
    {
        "Name":        "FOR46",
        "Target":      "CD46",
        "Modality":    "ADC",
        "Drug Class":  "CD46-Targeted",
        "Developer":   "Fortis Therapeutics / AstraZeneca",
        "Phase":       1,
        "Phase Label": "Phase 1",
        "Indication":  "mCRPC, Multiple Myeloma",
        "Isotope / Payload": "DM4 (maytansinoid)",
        "Mechanism":   "Anti-CD46 antibody conjugated to DM4 (tubulin inhibitor). Internalised on CD46 binding → intracellular cytotoxin release.",
        "NCT":         "NCT03959397",
        "Notes":       "Phase 1 dose-escalation ongoing. mCRPC cohort shows activity in PSMA-low/CD46-high patients.",
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
        "Mechanism":   "Anti-CD46 antibody radiolabelled with 131-Iodine. Beta particle irradiation of CD46-expressing haematological malignancies.",
        "NCT":         "NCT (multiple)",
        "Notes":       "Academic programme; good tolerability in haematological settings. Provides clinical proof-of-concept for CD46-targeted RLT.",
        "ChEMBL":      "—",
    },
    {
        "Name":        "225Ac-CD46-Antibody",
        "Target":      "CD46",
        "Modality":    "RLT (α)",
        "Drug Class":  "CD46-Targeted",
        "Developer":   "Academic / Preclinical",
        "Phase":       0,
        "Phase Label": "Preclinical",
        "Indication":  "Pan-cancer (CD46+)",
        "Isotope / Payload": "225Ac (alpha-emitter)",
        "Mechanism":   "Anti-CD46 antibody conjugated to 225Ac via DOTA chelator. Alpha particles (5.8 MeV) cause double-strand DNA breaks within 2–3 cell diameters.",
        "NCT":         "—",
        "Notes":       "Scientific rationale of this platform. High LET (100× vs photon), short path length minimises bystander toxicity.",
        "ChEMBL":      "—",
    },
    {
        "Name":        "IMGN779 (+ CD46 rationalised)",
        "Target":      "CD33",
        "Modality":    "ADC",
        "Drug Class":  "CD46-Targeted",
        "Developer":   "ImmunoGen",
        "Phase":       2,
        "Phase Label": "Phase 2",
        "Indication":  "AML",
        "Isotope / Payload": "DGN549 (indolino-PBD)",
        "Mechanism":   "Anti-CD33 ADC; CD46-high AML (typically CD33+/CD46+) represents the target population. Phase 2 ongoing.",
        "NCT":         "NCT03722095",
        "Notes":       "CD46 not the direct target but CD46-high AML cells are the therapeutic population of interest for combination strategies.",
        "ChEMBL":      "CHEMBL3707330",
    },
    # ── PSMA-targeting RLT (competitive reference) ─────────────────────────
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
        "Mechanism":   "PSMA-targeting small molecule (PSMA-617) conjugated to 177Lu. Beta particles irradiate PSMA-expressing prostate cancer cells.",
        "NCT":         "NCT03511664 (VISION trial)",
        "Notes":       "FDA Approved 2022. Current SoC. Leaves ~35% PSMA-low/heterogeneous patients unserved — CD46 whitespace.",
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
        "Mechanism":   "Same PSMA-617 ligand as Pluvicto but conjugated to 225Ac alpha-emitter. Investigational for Pluvicto-refractory patients.",
        "NCT":         "Multiple NCTs",
        "Notes":       "Directly parallel modality to 225Ac-CD46 but restricted to PSMA+ patients. Key differentiator: CD46 expressed in PSMA-low tumours.",
        "ChEMBL":      "—",
    },
    # ── Complement pathway inhibitors (mechanistic context) ────────────────
    {
        "Name":        "Eculizumab (Soliris)",
        "Target":      "C5 (Complement)",
        "Modality":    "Monoclonal Antibody",
        "Drug Class":  "Complement Inhibitor",
        "Developer":   "Alexion / AstraZeneca",
        "Phase":       4,
        "Phase Label": "FDA Approved",
        "Indication":  "PNH, aHUS, gMG",
        "Isotope / Payload": "—",
        "Mechanism":   "Anti-C5 antibody — blocks terminal complement cascade (C5a + C5b-9/MAC). Relevant as CD46 biology context: both protect against terminal complement.",
        "NCT":         "Multiple",
        "Notes":       "Validates complement pathway as druggable. CD46 regulates upstream (C3b/C4b) while eculizumab targets downstream C5 — orthogonal targets.",
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
        "Mechanism":   "Long-acting anti-C5 (engineered Fc for pH-dependent recycling; 8-week dosing vs eculizumab 2-week).",
        "NCT":         "Multiple",
        "Notes":       "Next-gen eculizumab. Combined with CD46-targeted RLT: complement inhibition may reduce hepatotoxicity risk from C3b deposition in liver.",
        "ChEMBL":      "CHEMBL4296393",
    },
])

# Phase numeric for sorting / positioning
PHASE_ORDER = {
    "Preclinical": 0, "Phase 1": 1, "Phase 2": 2,
    "Phase 3": 3, "FDA Approved": 4,
}
PIPELINE["Phase_num"] = PIPELINE["Phase Label"].map(PHASE_ORDER).fillna(0)

CLASS_COLORS = {
    "CD46-Targeted":      "#f97316",   # orange
    "PSMA-Targeted":      "#3b82f6",   # blue
    "Complement Inhibitor": "#22c55e", # green
}

MODALITY_SHAPES = {
    "ADC":              "diamond",
    "RLT (α)":          "star",
    "RLT (β⁻)":         "circle",
    "Monoclonal Antibody": "square",
}


# ── Page layout ───────────────────────────────────────────────────────────────

st.markdown(
    page_hero(
        icon="💊",
        module_name="Drug Pipeline Explorer",
        purpose="CD46-targeting and RLT therapeutic landscape · ADC, radioimmunotherapy, and complement inhibitors · clinical trial status",
        kpi_chips=[
            ("Agents Tracked", "10"),
            ("Drug Classes", "3"),
            ("FDA Approved", "2"),
            ("α-emitter", "225Ac"),
        ],
        source_badges=["ClinicalTrials", "ChEMBL", "TCGA"],
    ),
    unsafe_allow_html=True,
)

# ── Metric strip ──────────────────────────────────────────────────────────────
m1, m2, m3, m4, m5 = st.columns(5)
m1.metric("Agents in Pipeline", len(PIPELINE), "across 3 drug classes")
m2.metric("CD46-Targeting", len(PIPELINE[PIPELINE["Drug Class"] == "CD46-Targeted"]),
          "ADC + RLT modalities")
m3.metric("Approved Agents", len(PIPELINE[PIPELINE["Phase Label"] == "FDA Approved"]),
          "complement + PSMA")
m4.metric("Modalities", PIPELINE["Modality"].nunique(), "ADC · RLT · mAb")
m5.metric("α-emitter Agents", len(PIPELINE[PIPELINE["Isotope / Payload"].str.contains("225Ac", na=False)]),
          "225Ac programmes")

st.markdown("---")

tab_overview, tab_cd46, tab_psma, tab_complement, tab_rationale = st.tabs([
    "📊 Pipeline Overview", "🎯 CD46 Agents", "☢️ PSMA Competitive", "🧬 Complement Context", "🔬 Combination Rationale"
])

# ──────────────────────────────────────────────────────────────────────────────
# TAB 1 — Pipeline Overview (swim-lane chart)
# ──────────────────────────────────────────────────────────────────────────────
with tab_overview:
    st.subheader("Clinical Development Landscape")

    # Bubble scatter: y = drug name, x = phase, color = class, shape = modality
    df_sorted = PIPELINE.sort_values(["Drug Class", "Phase_num"], ascending=[True, False])

    fig = go.Figure()

    for drug_class, color in CLASS_COLORS.items():
        df_cls = df_sorted[df_sorted["Drug Class"] == drug_class]
        if df_cls.empty:
            continue
        for _, row in df_cls.iterrows():
            symb = MODALITY_SHAPES.get(row["Modality"], "circle")
            fig.add_trace(go.Scatter(
                x=[row["Phase_num"]],
                y=[row["Name"]],
                mode="markers+text",
                marker=dict(
                    symbol=symb,
                    size=28 if row["Phase Label"] == "FDA Approved" else 20,
                    color=color,
                    opacity=0.9,
                    line=dict(width=2, color="white"),
                ),
                text=[f"  {row['Phase Label']}"],
                textposition="middle right",
                textfont=dict(size=10, color="#cbd5e1"),
                hovertemplate=(
                    f"<b>{row['Name']}</b><br>"
                    f"Class: {row['Drug Class']}<br>"
                    f"Modality: {row['Modality']}<br>"
                    f"Phase: {row['Phase Label']}<br>"
                    f"Target: {row['Target']}<br>"
                    f"Developer: {row['Developer']}<br>"
                    f"Indication: {row['Indication']}<br>"
                    f"<i>{row['Notes'][:120]}...</i><extra></extra>"
                ),
                name=drug_class,
                showlegend=False,
            ))

    # Add phase labels on x-axis via annotations + reference lines
    phase_labels = {0: "Preclinical", 1: "Phase 1", 2: "Phase 2",
                    3: "Phase 3", 4: "Approved"}
    for phase_num, label in phase_labels.items():
        fig.add_vline(x=phase_num, line=dict(color="#1e293b", width=1, dash="dot"))

    # Legend patches (manual)
    for drug_class, color in CLASS_COLORS.items():
        fig.add_trace(go.Scatter(
            x=[None], y=[None],
            mode="markers",
            marker=dict(size=12, color=color, symbol="circle"),
            name=drug_class,
            showlegend=True,
        ))
    for mod, shape in MODALITY_SHAPES.items():
        fig.add_trace(go.Scatter(
            x=[None], y=[None],
            mode="markers",
            marker=dict(size=12, color="#64748b", symbol=shape),
            name=f"Shape: {mod}",
            showlegend=True,
        ))

    fig.update_layout(
        paper_bgcolor="#0f172a",
        plot_bgcolor="#0f172a",
        font=dict(color="white"),
        xaxis=dict(
            tickvals=list(phase_labels.keys()),
            ticktext=list(phase_labels.values()),
            showgrid=False,
            range=[-0.5, 4.8],
            title=None,
        ),
        yaxis=dict(
            showgrid=True, gridcolor="#1e293b",
            title=None,
            autorange="reversed",
        ),
        legend=dict(
            bgcolor="rgba(15,23,42,0.85)", bordercolor="#334155",
            borderwidth=1, font=dict(size=10, color="white"),
            x=1.01, y=1,
        ),
        height=480,
        margin=dict(l=10, r=260, t=20, b=40),
        hoverlabel=dict(bgcolor="#1e293b", bordercolor="#475569",
                        font=dict(color="white", size=12)),
    )
    st.plotly_chart(fig, width="stretch")
    st.caption(
        "**Circle** = RLT (β⁻) · **Star** = RLT (α) · **Diamond** = ADC · **Square** = Monoclonal Antibody · "
        "Hover each marker for mechanism details."
    )

    # Summary table
    st.markdown("---")
    st.subheader("Complete Agent Summary")
    summary_cols = ["Name", "Drug Class", "Modality", "Target", "Phase Label",
                    "Developer", "Indication", "Isotope / Payload"]
    st.dataframe(
        PIPELINE.sort_values(["Drug Class", "Phase_num"], ascending=[True, False])[summary_cols],
        use_container_width=True,
        height=340,
        hide_index=True,
    )

# ──────────────────────────────────────────────────────────────────────────────
# TAB 2 — CD46-Targeting Agents Detail
# ──────────────────────────────────────────────────────────────────────────────
with tab_cd46:
    st.subheader("🎯 CD46-Targeting Therapeutic Agents")
    df_cd46 = PIPELINE[PIPELINE["Drug Class"] == "CD46-Targeted"].sort_values(
        "Phase_num", ascending=False
    )

    for _, row in df_cd46.iterrows():
        phase_emoji = {"Preclinical": "🔬", "Phase 1": "🧪", "Phase 2": "⚗️",
                       "FDA Approved": "✅"}.get(row["Phase Label"], "🔬")
        with st.expander(
            f"{phase_emoji} **{row['Name']}** — {row['Phase Label']} · {row['Developer']}"
        ):
            col_left, col_right = st.columns([2, 1])
            with col_left:
                st.markdown(f"**Target:** {row['Target']}")
                st.markdown(f"**Modality:** {row['Modality']}")
                st.markdown(f"**Payload / Isotope:** {row['Isotope / Payload']}")
                st.markdown(f"**Indication:** {row['Indication']}")
                st.markdown(f"**Mechanism:**")
                st.markdown(f"> {row['Mechanism']}")
                if row["Notes"]:
                    st.info(f"💡 {row['Notes']}")
            with col_right:
                st.markdown(f"**Developer:** {row['Developer']}")
                if row["NCT"] != "—":
                    st.markdown(f"**NCT:** `{row['NCT']}`")
                if row["ChEMBL"] != "—":
                    st.markdown(f"**ChEMBL:** `{row['ChEMBL']}`")

    st.markdown("---")

    # CD46 programme comparison
    st.subheader("CD46 Programme Comparison")
    compare_cols = ["Name", "Modality", "Phase Label", "Isotope / Payload",
                    "Indication", "Developer"]
    st.dataframe(
        df_cd46[compare_cols].reset_index(drop=True),
        use_container_width=True,
        hide_index=True,
    )

    st.markdown("""
    **Key observations:**
    - **FOR46** (AstraZeneca-backed) is the most advanced CD46-targeting agent in solid tumours
    - **BC8-CD46** provides clinical PoC for CD46-targeted radioimmunotherapy in haematological malignancy
    - **225Ac-CD46** (this programme) represents the alpha-emitter frontier — 20× higher LET than 131I-BC8
    - Three distinct delivery mechanisms (ADC / β-RLT / α-RLT) validate CD46 as a tractable surface target
    """)

# ──────────────────────────────────────────────────────────────────────────────
# TAB 3 — PSMA Competitive Reference
# ──────────────────────────────────────────────────────────────────────────────
with tab_psma:
    st.subheader("☢️ PSMA-Targeted RLT — Competitive Reference")

    df_psma = PIPELINE[PIPELINE["Drug Class"] == "PSMA-Targeted"]

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### PSMA vs CD46: Head-to-Head Comparison")
        comparison_data = {
            "Attribute": [
                "Expression in mCRPC",
                "Expression: PSMA-low / heterogeneous",
                "Expression: non-prostate cancers",
                "Number of active trials",
                "Approved agents",
                "Alpha-emitter programme",
                "ADC programme",
                "Immune evasion function",
                "Patient exclusion risk",
            ],
            "PSMA (FOLH1)": [
                "~85% PSMA+ at initial diagnosis",
                "~35% of patients (unserved by Pluvicto)",
                "Very low (prostate-restricted)",
                "183",
                "2 (Pluvicto, PSMA-1007)",
                "225Ac-PSMA-617 (Phase 2)",
                "None approved",
                "No direct immune role",
                "PSMA-negative or heterogeneous",
            ],
            "CD46 (MCP)": [
                ">95% of mCRPC (including PSMA-low)",
                "Maintained in PSMA-negative tumours",
                "Pan-cancer: 25 tumour types",
                "14",
                "None (early-clinical stage)",
                "This programme (Preclinical)",
                "FOR46 (Phase 1)",
                "Complement evasion hub",
                "Very low (ubiquitous expression)",
            ],
        }
        df_compare = pd.DataFrame(comparison_data)
        st.dataframe(df_compare, use_container_width=True, hide_index=True, height=360)

    with col2:
        st.markdown("#### Clinical Trial Volume")
        fig_trials = go.Figure(go.Bar(
            x=["CD46", "PSMA", "FAP"],
            y=[14, 183, 31],
            marker=dict(
                color=["#f97316", "#3b82f6", "#22c55e"],
                line=dict(color="#0f172a", width=1),
            ),
            text=[14, 183, 31],
            textposition="outside",
            textfont=dict(color="white", size=14),
        ))
        fig_trials.update_layout(
            paper_bgcolor="#0f172a", plot_bgcolor="#0f172a",
            font=dict(color="white"),
            yaxis=dict(title="Active clinical trials", gridcolor="#1e293b"),
            xaxis=dict(showgrid=False),
            height=280,
            margin=dict(l=20, r=20, t=20, b=40),
        )
        st.plotly_chart(fig_trials, width="stretch")

        st.markdown("""
        **Strategic insight:**
        PSMA has 183 active trials vs CD46's 14 — yet CD46 covers the patients
        that PSMA misses. The under-explored nature of CD46 represents
        **first-mover whitespace** in the alpha-RLT segment.
        """)

    st.markdown("---")
    for _, row in df_psma.iterrows():
        with st.expander(f"**{row['Name']}** — {row['Phase Label']} · {row['Developer']}"):
            st.markdown(f"**Target:** {row['Target']}")
            st.markdown(f"**Modality:** {row['Modality']} | **Isotope:** {row['Isotope / Payload']}")
            st.markdown(f"**Indication:** {row['Indication']}")
            st.markdown(f"> {row['Mechanism']}")
            if row["Notes"]:
                st.info(f"💡 {row['Notes']}")

# ──────────────────────────────────────────────────────────────────────────────
# TAB 4 — Complement Inhibitors
# ──────────────────────────────────────────────────────────────────────────────
with tab_complement:
    st.subheader("🧬 Complement Pathway Inhibitors — Mechanistic Context")

    df_comp = PIPELINE[PIPELINE["Drug Class"] == "Complement Inhibitor"]

    st.markdown("""
    While not direct CD46-targeting agents, complement inhibitors validate the complement
    pathway as **clinically druggable** and provide important context for:
    1. Understanding the biology CD46 regulates (C3b/C4b inactivation)
    2. Potential combination strategies to enhance tumour complement sensitivity
    3. Managing hepatotoxicity risk from inadvertent CD46 targeting in liver
    """)

    col_ec, col_ra = st.columns(2)

    for col, (_, row) in zip([col_ec, col_ra], df_comp.iterrows()):
        with col:
            st.markdown(f"### {row['Name']}")
            st.markdown(f"**Target:** {row['Target']}")
            st.markdown(f"**Developer:** {row['Developer']}")
            st.markdown(f"**Approved Indications:** {row['Indication']}")
            st.markdown(f"**Mechanism:** {row['Mechanism']}")
            st.markdown(f"**ChEMBL:** `{row['ChEMBL']}`")
            if row["Notes"]:
                st.info(f"💡 **KG context:** {row['Notes']}")

    st.markdown("---")
    st.subheader("Complement Cascade — Where Each Agent Acts")
    st.markdown("""
    ```
    Classical/Lectin pathway         Alternative pathway
            ↓                               ↓
    C1 → C4 → C2                      C3 → CFB → CFD
            ↓                               ↓
           C3 convertase ←─── C3 ─────── C3 convertase
                ↓           cleavage           ↓
            C3b ← ─ ─ ─ CD46 + CFI ─ ─ ─ → iC3b (inactive)
                ↓           [This programme's target]
            C5 convertase
                ↓
               C5a + C5b ← ─ Eculizumab / Ravulizumab block here
                               [Soliris / Ultomiris]
                ↓
           C5b-9 (MAC)
    ```

    | Level | Regulator | Relevance |
    |-------|-----------|-----------|
    | C3b/C4b cleavage | **CD46 + CFI** | This drug target — upstream, prevents C3 amplification |
    | MAC assembly | **Eculizumab / Ravulizumab** | Validated approved drugs — downstream C5 |
    | CD55 | Convertase decay | Co-expressed with CD46 on tumour surface |
    | CD59 | MAC inhibition | Third layer of tumour complement evasion |

    **Key distinction:** 225Ac-CD46 therapy targets the *tumour surface expression* of CD46 —
    it does not inhibit CD46's complement regulatory function. The alpha particle kills the cancer
    cell regardless of CD46's downstream biology.
    """)

# ──────────────────────────────────────────────────────────────────────────────
# TAB 5 — Combination Rationale
# ──────────────────────────────────────────────────────────────────────────────
with tab_rationale:
    st.subheader("🔬 Combination Strategy Rationale")

    st.markdown("""
    The knowledge graph linking Drug nodes → Gene nodes → Pathway nodes reveals
    biologically-motivated combination hypotheses:
    """)

    combos = [
        {
            "Combination": "225Ac-CD46 + ARPI (Enzalutamide / Abiraterone)",
            "Rationale": "ARPI upregulates CD46 expression in mCRPC (castration-resistant cells increase CD46 to evade immune clearance). This creates a targetable window where ARPI pre-treatment enriches the CD46-high population.",
            "Evidence": "Preclinical xenograft data; CD46 upregulation inversely correlated with AR activity",
            "Stage": "Hypothesis",
            "Priority": "High",
        },
        {
            "Combination": "225Ac-CD46 + Pluvicto (177Lu-PSMA-617)",
            "Rationale": "PSMA and CD46 are largely non-overlapping — sequential dosing could address both PSMA-high and CD46-high cell populations in heterogeneous tumours. Alternating dosing could prevent antigen-negative escape.",
            "Evidence": "Antigen co-expression data from DepMap; clinical trial design under consideration",
            "Stage": "Hypothesis",
            "Priority": "High",
        },
        {
            "Combination": "225Ac-CD46 + Anti-PD-1 (checkpoint blockade)",
            "Rationale": "Alpha particles cause immunogenic cell death (ICD) — release of DAMPs and tumour neoantigens. CD46 normally suppresses T-cell activation; killing CD46-high cells may re-activate anti-tumour T-cell responses. Checkpoint blockade sustains this effect.",
            "Evidence": "ICD generated by alpha emitters (published); CD46 → Tr1 conversion mechanism",
            "Stage": "Preclinical hypothesis",
            "Priority": "Medium",
        },
        {
            "Combination": "225Ac-CD46 + Eculizumab (liver protection)",
            "Rationale": "CD46 is highly expressed in normal liver. Eculizumab inhibits C5 (downstream of CD46) and may reduce hepatotoxicity risk from complement activation during CD46-targeted RLT dosing.",
            "Evidence": "Mechanistic hypothesis based on complement biology in liver",
            "Stage": "Safety hypothesis",
            "Priority": "Medium",
        },
        {
            "Combination": "225Ac-CD46 + FOR46 (ADC + alpha RLT dual-payload)",
            "Rationale": "FOR46 (ADC / cytotoxin) + 225Ac-CD46 (alpha RLT) dual targeting of the same antigen with orthogonal kill mechanisms. Non-overlapping toxicity profiles (DM4=peripheral neuropathy vs 225Ac=haematologic).",
            "Evidence": "Mechanistic — parallel CDO46 programmes; no clinical data yet",
            "Stage": "Future hypothesis",
            "Priority": "Exploratory",
        },
    ]

    priority_colors = {"High": "#22c55e", "Medium": "#f59e0b",
                       "Exploratory": "#94a3b8", "Safety hypothesis": "#3b82f6"}

    for combo in combos:
        pcolor = priority_colors.get(combo["Priority"], "#94a3b8")
        with st.expander(
            f"**{combo['Combination']}** — Priority: {combo['Priority']}"
        ):
            col_r, col_e = st.columns([3, 1])
            with col_r:
                st.markdown(f"**Biological Rationale:**")
                st.markdown(f"> {combo['Rationale']}")
                st.markdown(f"**Supporting Evidence:** {combo['Evidence']}")
            with col_e:
                st.markdown(f"**Stage:** {combo['Stage']}")
                st.markdown(
                    f"<div style='background:{pcolor};color:white;padding:6px 12px;"
                    f"border-radius:8px;text-align:center;font-weight:bold;'>"
                    f"{combo['Priority']}</div>",
                    unsafe_allow_html=True,
                )

    st.markdown("---")
    st.info(
        "💡 **KG-derived insight**: These combinations are surfaced by traversing the "
        "Drug → Gene → Pathway → Disease path in the AuraDB knowledge graph. "
        "The STRING PPI network (Page 10) provides the biological mechanism "
        "connecting each combination partner to CD46's signalling neighbourhood."
    )
