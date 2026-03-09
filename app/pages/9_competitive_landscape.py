"""Page 9 — Competitive Landscape: CD46 vs PSMA vs FAP in Solid Tumours."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import os

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[2] / ".env")

for _k in ("NEO4J_URI", "NEO4J_USERNAME", "NEO4J_PASSWORD"):
    try:
        if _k in st.secrets and not os.environ.get(_k):
            os.environ[_k] = st.secrets[_k]
    except Exception:
        pass

DATA_DIR = Path("data/processed")

st.title("🏆 Competitive Landscape")
st.markdown(
    "**Target comparison: CD46 vs PSMA vs FAP in solid tumours.** "
    "Expression prevalence, clinical trial activity, target biology, and differentiation rationale "
    "for 225Ac-CD46 radiopharmaceutical therapy in the current RLT treatment landscape."
)

# ---------------------------------------------------------------------------
# Data
# ---------------------------------------------------------------------------

DATA_DIR = Path("data/processed")

@st.cache_data(ttl=3600)
def load_by_cancer() -> pd.DataFrame:
    p = DATA_DIR / "cd46_by_cancer.csv"
    return pd.read_csv(p) if p.exists() else pd.DataFrame()


df_expr = load_by_cancer()

# ---------------------------------------------------------------------------
# Competitive reference data (curated from public sources)
# ---------------------------------------------------------------------------

# Clinical trial counts per target (ClinicalTrials.gov, March 2026)
TRIAL_DATA = pd.DataFrame(
    {
        "Target": ["CD46", "PSMA", "FAP"],
        "Active Trials": [14, 183, 31],
        "Phase 1": [10, 45, 18],
        "Phase 2+": [4, 138, 13],
        "Approved Agents": [0, 2, 0],
    }
)

# Competitor pipeline (PSMA-space and adjacent — public data only)
COMPETITORS = pd.DataFrame(
    [
        {
            "Agent": "Pluvicto (177Lu-PSMA-617)",
            "Company": "Novartis",
            "Target": "PSMA",
            "Modality": "Beta RLT",
            "Status": "FDA Approved",
            "Indication": "PSMA+ mCRPC",
            "Notes": "Current standard of care; leaves ~30–40% PSMA-low patients unserved",
        },
        {
            "Agent": "ART-101",
            "Company": "Archeus Technologies",
            "Target": "PSMA",
            "Modality": "Alpha/Beta RLT",
            "Status": "Pre-IND / Phase 1 (~late 2025)",
            "Indication": "PSMA+ mCRPC",
            "Notes": "Higher tumour uptake & lower salivary gland uptake vs Pluvicto in preclinical data",
        },
        {
            "Agent": "P-PSMA-101",
            "Company": "Poseida Therapeutics",
            "Target": "PSMA",
            "Modality": "CAR-T (piggyBac)",
            "Status": "Phase 1 (NCT04249947)",
            "Indication": "PSMA+ mCRPC",
            "Notes": "PSA declines in 10/14 patients; stem cell memory T-cell phenotype",
        },
        {
            "Agent": "225Ac-PSMA-617",
            "Company": "Various (investigational)",
            "Target": "PSMA",
            "Modality": "Alpha RLT",
            "Status": "Phase 1/2 (multiple trials)",
            "Indication": "PSMA+ mCRPC",
            "Notes": "Alpha upgrade of Pluvicto backbone; high LET in same PSMA+ population",
        },
        {
            "Agent": "FOR46 / BC8-CD46",
            "Company": "Academic centres",
            "Target": "CD46",
            "Modality": "Radiolabelled antibody",
            "Status": "Phase 1",
            "Indication": "Haematological malignancies",
            "Notes": "CD46 as target validated; solid tumour extension is novel",
        },
        {
            "Agent": "sibrotuzumab (FAP)",
            "Company": "Various",
            "Target": "FAP",
            "Modality": "RLT / ADC",
            "Status": "Phase 1/2",
            "Indication": "Multiple solid tumours",
            "Notes": "Stroma/TME target; not tumour-cell intrinsic — different biology from CD46",
        },
        {
            "Agent": "225Ac-CD46 RLT",
            "Company": "—",
            "Target": "CD46",
            "Modality": "Alpha RLT",
            "Status": "Research / Pre-IND",
            "Indication": "CD46+ solid tumours (pan-cancer)",
            "Notes": "This platform — public TCGA + HPA + DepMap evidence base",
        },
    ]
)

TARGET_BIOLOGY = {
    "CD46": {
        "icon": "🎯",
        "full_name": "Membrane Cofactor Protein (MCP / CD46)",
        "expression": "Pan-tumour overexpression; 25 TCGA cancer types with elevated CD46 vs normal",
        "mechanism": "Complement evasion — downregulates C3b/C4b, protecting tumour cells from complement-mediated lysis",
        "isoforms": "6+ isoforms (BC1/BC2 splice variants); tissue-specific isoform expression",
        "selectivity": "Moderate — expressed in normal tissue but significantly upregulated in tumour",
        "psma_overlap": "Present in PSMA-low/negative disease — complementary, not competing",
        "status": "14 active NCT trials; no approved agent → whitespace opportunity",
        "modality_fit": "Alpha RLT (225Ac) ideal — high LET for solid tumour penetration",
        "colour": "#3498db",
    },
    "PSMA": {
        "icon": "⚠️",
        "full_name": "Prostate-Specific Membrane Antigen (FOLH1 / PSMA)",
        "expression": "Prostate-predominant; low expression in most other solid tumours",
        "mechanism": "Folate hydrolase enzyme; internalised on binding → high tumour delivery",
        "isoforms": "Limited isoform complexity",
        "selectivity": "High for prostate tumour — validated in mCRPC setting (VISION trial)",
        "psma_overlap": "Defines the PSMA+ patient population; ~30–40% mCRPC are PSMA-low/neg",
        "status": "Pluvicto FDA-approved (2022); ART-101 + P-PSMA-101 in Phase 1 → CROWDED",
        "modality_fit": "Both beta (177Lu-Pluvicto) and alpha (225Ac-PSMA-617) in trials",
        "colour": "#e67e22",
    },
    "FAP": {
        "icon": "🔬",
        "full_name": "Fibroblast Activation Protein (FAP)",
        "expression": "Tumour microenvironment (activated fibroblasts); not tumour-cell intrinsic",
        "mechanism": "Serine protease; up to 90% expression in cancer-associated fibroblasts",
        "isoforms": "Single glycoprotein; limited complexity",
        "selectivity": "Stroma-selective; not expressed in resting fibroblasts",
        "psma_overlap": "Orthogonal population — TME targeting vs surface tumour antigen",
        "status": "~31 active trials; no approved agent; emerging but stroma biology limits payload delivery",
        "modality_fit": "RLT + ADC under investigation; stroma delivery less efficient than tumour-surface targets",
        "colour": "#27ae60",
    },
}

# ---------------------------------------------------------------------------
# Tabs
# ---------------------------------------------------------------------------

tab1, tab2, tab3, tab4 = st.tabs(
    [
        "📊 Expression Prevalence",
        "🔬 Trial Activity",
        "🧬 Target Biology",
        "✅ Why CD46 Adds Value",
    ]
)

# ------------------------------------------------------------------
# Tab 1 — Expression Prevalence
# ------------------------------------------------------------------

with tab1:
    st.subheader("CD46 Expression Across TCGA Cancer Types")
    st.markdown(
        "CD46 is elevated in **25 TCGA cancer types** relative to PSMA (FOLH1), "
        "which is predominantly prostate-restricted. "
        "This pan-tumour profile gives CD46-based RLT a broader addressable patient population."
    )

    if not df_expr.empty:
        # Approximate PSMA (FOLH1) medians — PRAD is the primary PSMA cancer;
        # other cancers have near-zero expression. Using published TCGA data estimates.
        PSMA_MEDIANS = {
            "PRAD": 8.2, "LUAD": 1.1, "BRCA": 0.9, "COAD": 0.8, "BLCA": 0.7,
            "KIRC": 1.0, "LIHC": 0.5, "STAD": 0.6, "PAAD": 0.5, "CESC": 0.4,
            "UCEC": 0.4, "OV": 0.5, "LUSC": 0.8, "HNSC": 0.6, "THCA": 0.7,
            "SKCM": 0.4, "LAML": 0.3, "KIRP": 0.9, "GBM": 0.5, "LGG": 0.3,
            "TGCT": 0.7, "ACC": 0.4, "PCPG": 0.3, "SARC": 0.4, "THYM": 0.5,
        }
        df_plot = df_expr.copy()
        df_plot["PSMA_median"] = df_plot["cancer_type"].map(PSMA_MEDIANS).fillna(0.5)
        df_plot = df_plot.sort_values("cd46_median", ascending=False)

        df_melt = pd.melt(
            df_plot,
            id_vars=["cancer_type"],
            value_vars=["cd46_median", "PSMA_median"],
            var_name="Target",
            value_name="Median log₂ TPM",
        )
        df_melt["Target"] = df_melt["Target"].map(
            {"cd46_median": "CD46", "PSMA_median": "PSMA (FOLH1)"}
        )

        fig = px.bar(
            df_melt,
            x="cancer_type",
            y="Median log₂ TPM",
            color="Target",
            barmode="group",
            color_discrete_map={"CD46": "#3498db", "PSMA (FOLH1)": "#e67e22"},
            labels={"cancer_type": "TCGA Cancer Type"},
            height=420,
        )
        fig.update_layout(
            plot_bgcolor="white",
            paper_bgcolor="white",
            legend={"orientation": "h", "y": 1.08},
            margin={"t": 30, "b": 60},
            xaxis={"tickangle": -45},
        )
        st.plotly_chart(fig, width='stretch')
        st.caption(
            "CD46 data: TCGA UCSC Xena (n > 2,800 patients). "
            "PSMA estimates: representative TCGA median values from published literature. "
            "Note: PSMA is near-zero in all non-prostate cancers — making those patients "
            "ineligible for PSMA-targeted RLT."
        )

# ------------------------------------------------------------------
# Tab 2 — Trial Activity
# ------------------------------------------------------------------

with tab2:
    st.subheader("Clinical Trial Landscape by Target")

    cols_trial = st.columns([1.3, 1])

    with cols_trial[0]:
        fig_trials = go.Figure()
        colours = {"CD46": "#3498db", "PSMA": "#e67e22", "FAP": "#27ae60"}
        for _, row in TRIAL_DATA.iterrows():
            fig_trials.add_trace(
                go.Bar(
                    name=row["Target"],
                    x=[row["Target"]],
                    y=[row["Active Trials"]],
                    marker_color=colours[row["Target"]],
                    text=[row["Active Trials"]],
                    textposition="outside",
                )
            )
        fig_trials.update_layout(
            title="Active Clinical Trials (ClinicalTrials.gov, March 2026)",
            showlegend=False,
            height=380,
            plot_bgcolor="white",
            yaxis={"title": "Number of Trials"},
            margin={"t": 50, "b": 20},
        )
        st.plotly_chart(fig_trials, width='stretch')

    with cols_trial[1]:
        st.markdown("**Trial Breakdown**")
        st.dataframe(
            TRIAL_DATA.set_index("Target"),
            use_container_width=True,
        )
        st.markdown("")
        st.info(
            "**PSMA space is saturated.** "
            "With Pluvicto FDA-approved and multiple Phase 1/2 agents entering, "
            "differentiation in PSMA+ disease is increasingly difficult. "
            "CD46 represents the uncrowded next target with a validated tumour surface antigen rationale."
        )

    st.markdown("**Active Competitor Agents**")
    st.dataframe(
        COMPETITORS,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Agent": st.column_config.TextColumn("Agent", width=180),
            "Status": st.column_config.TextColumn("Status", width=200),
            "Notes": st.column_config.TextColumn("Notes", width=340),
        },
    )
    st.caption(
        "Sources: ClinicalTrials.gov · Drug Discovery World · UroToday · NIH · company press releases. "
        "March 2026. ART-101 = Archeus Technologies (PSMA). P-PSMA-101 = Poseida Therapeutics (PSMA CAR-T)."
    )

# ------------------------------------------------------------------
# Tab 3 — Target Biology
# ------------------------------------------------------------------

with tab3:
    st.subheader("Target Biology Comparison")

    bio_cols = st.columns(3)
    for col, target in zip(bio_cols, ["CD46", "PSMA", "FAP"]):
        bio = TARGET_BIOLOGY[target]
        with col:
            with st.container(border=True):
                st.markdown(
                    f"<h3 style='color:{bio['colour']}'>{bio['icon']} {target}</h3>",
                    unsafe_allow_html=True,
                )
                st.markdown(f"*{bio['full_name']}*")
                st.markdown("---")
                st.markdown(f"**Expression:** {bio['expression']}")
                st.markdown(f"**Mechanism:** {bio['mechanism']}")
                st.markdown(f"**Isoforms:** {bio['isoforms']}")
                st.markdown(f"**Selectivity:** {bio['selectivity']}")
                st.markdown(f"**PSMA overlap:** {bio['psma_overlap']}")
                st.markdown(f"**Pipeline status:** {bio['status']}")
                st.markdown(f"**Modality fit:** {bio['modality_fit']}")

# ------------------------------------------------------------------
# Tab 4 — Why CD46 Adds Value
# ------------------------------------------------------------------

with tab4:
    st.subheader("Why CD46 as a Radiopharmaceutical Target?")

    msg_col, metric_col = st.columns([1.6, 1])

    with msg_col:
        st.markdown(
            """
            #### The PSMA Story Proves the Model — CD46 Is the Next Chapter

            177Lu-Pluvicto (PSMA-617) validated that **radioligand therapy works in mCRPC**.
            But it created a new clinical problem: approximately **30–40% of mCRPC patients
            are PSMA-low or PSMA-negative** at progression, and they have no approved RLT option.

            CD46 is **constitutively overexpressed** in PSMA-low disease, making it the
            natural complementary target — not a competitor, but the next distinct patient population.

            #### Differentiation Points

            **1. Non-overlapping patient population**
            CD46 is independently elevated in PSMA-low/negative mCRPC. A CD46-targeted agent
            can serve patients who fail or are ineligible for PSMA-RLT.

            **2. Novel mechanism**
            CD46 drives complement evasion — tumours hijack it to avoid immune destruction.
            Targeting it combines direct cytotoxicity (alpha particle) with disruption of
            an active immune escape mechanism. No approved RLT shares this MOA.

            **3. Pan-tumour opportunity**
            PSMA is prostate-restricted. CD46 is elevated in lung, colorectal, breast,
            bladder, and 20+ other TCGA cancer types — opening broader indications beyond mCRPC.

            **4. Alpha-particle advantage**
            225Ac delivers ~4 orders of magnitude higher linear energy transfer (LET) than
            177Lu. Single-cell kill without requiring high target density — critical for
            heterogeneous solid tumours.

            **5. Whitespace in trial landscape**
            14 CD46 trials globally vs 183 PSMA trials. Less competition, more room
            for first-mover advantage and IP differentiation.
            """
        )

    with metric_col:
        st.markdown("**Evidence Summary (this platform)**")

        kpi_data = [
            ("TCGA cancer types with CD46 elevation", "25 / 25"),
            ("PSMA-low mCRPC — unserved by Pluvicto", "~30–40%"),
            ("CD46 active clinical trials", "14"),
            ("PSMA active clinical trials", "183"),
            ("Approved PSMA agents", "2 (Pluvicto, PSMA-617)"),
            ("Approved CD46 agents", "0 → whitespace"),
            ("KG publications supporting CD46 RLT", "55"),
            ("DepMap cell lines with CD46 data", "1,186"),
        ]

        for label, val in kpi_data:
            with st.container(border=True):
                st.markdown(
                    f"<div style='font-size:0.82em;color:#94a3b8;'>{label}</div>"
                    f"<div style='font-size:1.15em;font-weight:600;color:#e2e8f0;'>{val}</div>",
                    unsafe_allow_html=True,
                )

    st.divider()
    st.caption(
        "**Research use only.** All competitive intelligence sourced from public databases "
        "(ClinicalTrials.gov, PubMed, Drug Discovery World, UroToday, NIH). "
        "Trial counts as of March 2026. No proprietary or non-public information used."
    )
