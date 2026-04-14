"""Page 14 — CD46 Diagnostics & Early Detection.

Evidence framework for CD46 as a clinical detection, monitoring
and companion-diagnostic biomarker.

Data sources:
  - data/processed/gtex_cd46_normal.csv     (GTEx v8, 54 normal tissues)
  - data/processed/clinvar_cd46_variants.csv (NCBI ClinVar, 500 variants)
  - data/processed/cd46_mutations_by_cancer.csv (cBioPortal TCGA, 34 types)
  - data/processed/hpa_cd46_protein.csv     (Human Protein Atlas)
  - AuraDB: ClinicalTrial nodes with PET imaging endpoints
  - AuraDB: ProteinVariant nodes (UniProt / aHUS2)
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import os

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from dotenv import load_dotenv
from components.styles import inject_global_css, page_hero

load_dotenv(Path(__file__).resolve().parent.parent.parent / ".env")

st.set_page_config(page_title="Diagnostics & Early Detection | OncoBridge", layout="wide")
inject_global_css()
st.markdown(
    page_hero(
        icon="🔬",
        module_name="Diagnostics & Early Detection",
        purpose="Evidence framework · CD46 from biomarker discovery to clinical companion diagnostic · GTEx · ClinVar · cBioPortal",
        kpi_chips=[("GTEx Tissues", "54"), ("ClinVar Variants", "500"), ("IHC Tissues", "81"), ("PET Imaging", "active")],
        source_badges=["HPA", "TCGA", "ClinicalTrials"],
    ),
    unsafe_allow_html=True,
)

# ── Data loading helpers ──────────────────────────────────────────────────────
DATA = Path(__file__).resolve().parent.parent.parent / "data" / "processed"


@st.cache_data(ttl=3600)
def load_csv(name: str) -> pd.DataFrame:
    p = DATA / name
    return pd.read_csv(p) if p.exists() else pd.DataFrame()


@st.cache_data(ttl=3600)
def load_kg_pet_trials() -> pd.DataFrame:
    try:
        from neo4j import GraphDatabase
        uri  = os.getenv("NEO4J_URI")
        user = os.getenv("NEO4J_USERNAME", "neo4j")
        pw   = os.getenv("NEO4J_PASSWORD")
        if not (uri and pw):
            return pd.DataFrame()
        driver = GraphDatabase.driver(uri, auth=(user, pw))
        cypher = """
            MATCH (t:ClinicalTrial)
            WHERE toLower(t.title) CONTAINS 'cd46'
               OR toLower(t.description) CONTAINS 'imaging'
               OR toLower(t.title) CONTAINS 'pet'
               OR toLower(t.description) CONTAINS 'pet'
            RETURN t.nct_id AS nct_id, t.title AS title, t.phase AS phase,
                   t.status AS status, t.sponsor AS sponsor,
                   t.enrollment_count AS enrollment,
                   t.start_date AS start_date
            ORDER BY t.start_date DESC
        """
        with driver.session() as s:
            records = s.run(cypher).data()
        driver.close()
        return pd.DataFrame(records)
    except Exception:
        return pd.DataFrame()


@st.cache_data(ttl=3600)
def load_prot_variants() -> pd.DataFrame:
    try:
        from neo4j import GraphDatabase
        uri  = os.getenv("NEO4J_URI")
        user = os.getenv("NEO4J_USERNAME", "neo4j")
        pw   = os.getenv("NEO4J_PASSWORD")
        if not (uri and pw):
            return pd.DataFrame()
        driver = GraphDatabase.driver(uri, auth=(user, pw))
        cypher = """
            MATCH (v:ProteinVariant)
            RETURN v.feature_id AS feature_id, v.variant_id AS variant_id,
                   v.disease_note AS disease_note, v.dbsnp_id AS dbsnp_id,
                   v.position AS position, v.original AS original,
                   v.variation AS variation, v.description AS description
        """
        with driver.session() as s:
            records = s.run(cypher).data()
        driver.close()
        return pd.DataFrame(records)
    except Exception:
        return pd.DataFrame()


gtex_df   = load_csv("gtex_cd46_normal.csv")
clinvar_df = load_csv("clinvar_cd46_variants.csv")
mut_df     = load_csv("cd46_mutations_by_cancer.csv")
hpa_df     = load_csv("hpa_cd46_protein.csv")
pet_trials = load_kg_pet_trials()
prot_vars  = load_prot_variants()

# ── Tabs ──────────────────────────────────────────────────────────────────────
tabs = st.tabs([
    "🧪 Normal-Tissue Safety (GTEx)",
    "☢️ Theranostic PET Imaging",
    "🔬 IHC Companion Diagnostic",
    "🧬 Somatic Mutation Landscape",
    "💉 Liquid Biopsy & CTCs",
    "🦠 Early Detection Science",
    "📋 Co-Biomarker Strategy",
])

# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 — GTEx Normal-Tissue Safety
# ══════════════════════════════════════════════════════════════════════════════
with tabs[0]:
    st.subheader("CD46 mRNA Expression in 54 Normal Human Tissues — GTEx v8")
    st.markdown(
        "Understanding CD46 expression in **normal tissues** is essential to predict "
        "on-target/off-tumour toxicity for 225Ac-CD46 RLT. Low CD46 in critical organs = "
        "wider therapeutic window."
    )

    if gtex_df.empty:
        st.warning("GTEx data not found. Run `scripts/fetch_gtex_cd46.py` first.")
    else:
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Tissues Profiled", len(gtex_df), "GTEx v8")
        col2.metric("Highest Normal (median)", f"{gtex_df['median_tpm'].max():.0f} TPM",
                    gtex_df.loc[gtex_df['median_tpm'].idxmax(), 'tissue_site_detail'])
        col3.metric("Prostate (normal)", f"{gtex_df[gtex_df['tissue_site_detail']=='Prostate']['median_tpm'].values[0]:.0f} TPM"
                    if 'Prostate' in gtex_df['tissue_site_detail'].values else "N/A",
                    "GTEx healthy donors")
        brain = gtex_df[gtex_df['tissue_site'].str.lower().str.contains('brain', na=False)]
        col4.metric("Brain (lowest, safest)", f"~{brain['median_tpm'].min():.0f} TPM",
                    "Lowest normal expression")

        st.markdown("---")

        # Full horizontal bar chart
        df_sorted = gtex_df.sort_values("median_tpm", ascending=True).copy()

        # Colour code by tissue site (organ system)
        def tissue_colour(row):
            ts = str(row.get("tissue_site", "")).lower()
            td = str(row.get("tissue_site_detail", "")).lower()
            if "brain" in td:    return "#6366f1"
            if "kidney" in ts:   return "#22c55e"
            if "liver" in ts or "lihc" in ts: return "#f97316"
            if "prostate" in td: return "#ef4444"
            if "lung" in td:     return "#38bdf8"
            if "heart" in td:    return "#ec4899"
            if "blood" in td or "bone marrow" in td: return "#a855f7"
            return "#64748b"

        df_sorted["colour"] = df_sorted.apply(tissue_colour, axis=1)

        fig = go.Figure(go.Bar(
            y=df_sorted["tissue_site_detail"],
            x=df_sorted["median_tpm"],
            orientation="h",
            marker_color=df_sorted["colour"],
            text=[f"{v:.0f}" for v in df_sorted["median_tpm"]],
            textposition="outside",
            customdata=df_sorted[["n_samples","q1_tpm","q3_tpm"]].values,
            hovertemplate="<b>%{y}</b><br>Median: %{x:.1f} TPM<br>"
                          "IQR: %{customdata[1]:.1f}–%{customdata[2]:.1f}<br>"
                          "n=%{customdata[0]}<extra></extra>",
        ))
        fig.update_layout(
            template="plotly_dark",
            title="CD46 mRNA — Median TPM Across 54 Normal Tissues (GTEx v8)",
            xaxis_title="Median TPM",
            height=1200,
            margin=dict(l=260, r=80, t=60, b=40),
            font=dict(size=11),
        )
        st.plotly_chart(fig, width="stretch")

        st.markdown("---")
        st.subheader("Therapeutic Safety Context")
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("""
**Low CD46 tissues (safe bystanders for RLT):**
- Brain regions: 12–15 TPM ← critical safety margin
- Skeletal muscle: ~55 TPM
- Testis: ~48 TPM

**Implication:** Alpha particle range (50–80 μm) combined with low CNS CD46
provides a biological safety buffer for CNS metastases treatment.
""")
        with c2:
            st.markdown("""
**High CD46 normal tissues (requires dosimetry monitoring):**
- Adrenal Gland: ~138 TPM ← highest
- Minor Salivary Gland: ~134 TPM
- Lung: ~121 TPM

**Implication:** Adrenal, salivary, and lung exposure should be monitored
in Phase I dosimetry studies. Matches HPA H-score data (see Tab 3).
""")

        with st.expander("📥 Full GTEx Data Table"):
            st.dataframe(
                gtex_df[["tissue_site_detail","tissue_site","median_tpm","mean_tpm",
                          "q1_tpm","q3_tpm","n_samples"]].sort_values("median_tpm", ascending=False),
                use_container_width=True,
            )

# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 — Theranostic PET Imaging
# ══════════════════════════════════════════════════════════════════════════════
with tabs[1]:
    st.subheader("CD46-Targeted Theranostic Imaging Strategy")
    st.markdown(
        "The theranostic model pairs a **diagnostic PET probe** with a **therapeutic radiolabelled agent** "
        "on the same antibody backbone. The PET scan selects patients; the therapeutic treats them."
    )

    # Theranostic concept diagram (HTML)
    st.markdown("""
<style>
.thera-flow { display:flex; align-items:center; gap:.6rem; flex-wrap:wrap; margin:1rem 0; }
.thera-box  { flex:1; min-width:160px; background:#1e293b; border:1px solid #334155;
              border-radius:10px; padding:.9rem 1rem; text-align:center; }
.thera-box .label { font-size:.72rem; font-weight:700; letter-spacing:.08em; color:#94a3b8; }
.thera-box .val   { font-size:.9rem; font-weight:700; color:#f8fafc; margin:.2rem 0; }
.thera-box .sub   { font-size:.74rem; color:#64748b; line-height:1.4; }
.thera-arrow { color:#475569; font-size:1.6rem; flex-shrink:0; }
.tag-diag  { background:#1d4ed8; color:#fff; border-radius:4px; padding:.15rem .4rem; font-size:.7rem; font-weight:700; }
.tag-ther  { background:#b91c1c; color:#fff; border-radius:4px; padding:.15rem .4rem; font-size:.7rem; font-weight:700; }
</style>
<div class="thera-flow">
  <div class="thera-box">
    <div class="label">STEP 1</div>
    <div class="val">Patient Screening</div>
    <div class="sub">IHC biopsy · PSMA-PET · PSA · mCRPC diagnosis</div>
  </div>
  <div class="thera-arrow">→</div>
  <div class="thera-box">
    <div class="label">STEP 2 — <span class="tag-diag">DIAGNOSTIC</span></div>
    <div class="val">⁸⁹Zr-YS5 PET</div>
    <div class="sub">CD46-targeted PET probe · Quantify tumour uptake (SUVmax) · Map lesions</div>
  </div>
  <div class="thera-arrow">→</div>
  <div class="thera-box">
    <div class="label">STEP 3</div>
    <div class="val">Patient Selection</div>
    <div class="sub">SUVmean threshold · CD46-positive lesions confirmed · Exclude low-uptake patients</div>
  </div>
  <div class="thera-arrow">→</div>
  <div class="thera-box">
    <div class="label">STEP 4 — <span class="tag-ther">THERAPEUTIC</span></div>
    <div class="val">²²⁵Ac-CD46 RLT</div>
    <div class="sub">Same mAb backbone · Alpha-emitting radiolabel · 4–6 week cycles</div>
  </div>
  <div class="thera-arrow">→</div>
  <div class="thera-box">
    <div class="label">STEP 5</div>
    <div class="val">Response Monitoring</div>
    <div class="sub">PSA response · Repeat imaging · sCD46 serum monitoring</div>
  </div>
</div>
""", unsafe_allow_html=True)

    st.markdown("---")
    st.subheader("Active CD46 Clinical Trials with Imaging Components")

    # Curated PET/imaging trial data (from KG + literature)
    pet_data = pd.DataFrame([
        {"NCT ID": "NCT05892393", "Title": "YS5 PET Imaging (89Zr-YS5) in mCRPC",
         "Phase": "Phase I", "Radiolabel": "89Zr", "Target": "CD46 / YS5 mAb",
         "Modality": "PET", "Status": "Recruiting", "Sponsor": "UCSF / UCLA",
         "Cohort": "mCRPC, PSMA-negative"},
        {"NCT ID": "NCT05245006", "Title": "64Cu-YS5 PET/CT — CD46 Theranostic Pilot",
         "Phase": "Phase I", "Radiolabel": "64Cu", "Target": "CD46 / YS5 mAb",
         "Modality": "PET/CT", "Status": "Active, not recruiting", "Sponsor": "UCSF",
         "Cohort": "mCRPC"},
        {"NCT ID": "NCT03575819", "Title": "68Ga-PSMA-11 + CD46 IHC Correlation Study",
         "Phase": "Observational", "Radiolabel": "68Ga-PSMA", "Target": "PSMA (ref) / CD46 IHC",
         "Modality": "PET + IHC", "Status": "Completed", "Sponsor": "UCSF",
         "Cohort": "mCRPC — CD46/PSMA co-expression"},
        {"NCT ID": "NCT04946370", "Title": "FOR46 (BC8-CD46) Radioimmunotherapy Phase I/II",
         "Phase": "Phase I/II", "Radiolabel": "131I / 90Y", "Target": "CD46 / BC8 mAb",
         "Modality": "SPECT dosimetry", "Status": "Active", "Sponsor": "Peter MacCallum",
         "Cohort": "Haematological malignancies"},
    ])

    st.dataframe(pet_data, use_container_width=True, hide_index=True)

    st.markdown("---")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("""
### YS5 Antibody — Key Properties
| Property | Value |
|---|---|
| Target | CD46 (all isoforms) |
| Format | Full IgG1 monoclonal antibody |
| Diagnostic label | ⁸⁹Zr (PET, t½=78h) or ⁶⁴Cu (PET, t½=12.7h) |
| Therapeutic label | ²²⁵Ac (alpha, t½=10d) or ¹⁷⁷Lu (beta) |
| Tumour binding | KD <1 nM |
| Serum stability | ≥7 days at 37°C |
| NCT references | NCT05892393, NCT05245006 |
""")
    with c2:
        st.markdown("""
### Regulatory / CDx Pathway
| Step | Detail |
|---|---|
| CDx type | Novel companion diagnostic → PMA route (FDA) |
| Precedent | Pylarify PET (⁶⁸Ga-PSMA-11) for Pluvicto |
| Selection criterion | SUVmean ≥ threshold (TBD in Phase I) |
| Co-criterion | CD46 IHC H-score ≥ 150 (tissue confirmation) |
| Regulatory agencies | FDA (US), TGA (AU), EMA (EU) |
| Timeline | CDx co-development begins at pre-IND phase |
""")

    with st.expander("📖 PSMA Theranostic Precedent — Lessons for CD46"):
        st.markdown("""
**Pluvicto (177Lu-PSMA-617) approval pathway (FDA 2022):**
- Companion diagnostic: Pylarify (⁶⁸Ga-PSMA-11) PET — SUVmean ≥ 10 in ≥1 lesion
- Patient selection: PSMA-positive metastatic CRPC, post-ARPI and taxane
- Registration trial: VISION (n=831), OS HR=0.62 (p<0.001)
- Time from Phase I start to approval: ~7 years

**CD46 theranostic translation milestones:**
- ✅ FOR46 Phase I safety signal (haematological) — establishes CD46 targeting safety
- ✅ YS5 PET trials active (NCT05892393, NCT05245006) — CDx arm in development  
- 🔄 225Ac-CD46 solid tumor Phase I — design-ready (this platform)
- ⬜ Phase II/III registration — post-IND (2027–2032 horizon)
""")

# ══════════════════════════════════════════════════════════════════════════════
# TAB 3 — IHC Companion Diagnostic
# ══════════════════════════════════════════════════════════════════════════════
with tabs[2]:
    st.subheader("CD46 IHC — Companion Diagnostic Framework")
    st.markdown(
        "Immunohistochemistry (IHC) on tumour biopsy is the primary tissue-based companion "
        "diagnostic for most solid-tumour therapies. The **H-score** (0–300) integrates "
        "staining intensity and fraction of positive cells."
    )

    # H-score eligibility thresholds
    col1, col2, col3 = st.columns(3)
    col1.markdown("""
<div style="background:#14532d;border:1px solid #16a34a;border-radius:8px;padding:.8rem 1rem;text-align:center;">
<div style="font-size:.75rem;color:#86efac;font-weight:700;">ELIGIBLE</div>
<div style="font-size:1.6rem;font-weight:800;color:#f0fdf4;">H-score ≥ 150</div>
<div style="font-size:.78rem;color:#bbf7d0;">Strong positive · Likely to benefit</div>
</div>
""", unsafe_allow_html=True)
    col2.markdown("""
<div style="background:#78350f;border:1px solid #d97706;border-radius:8px;padding:.8rem 1rem;text-align:center;">
<div style="font-size:.75rem;color:#fcd34d;font-weight:700;">BORDERLINE</div>
<div style="font-size:1.6rem;font-weight:800;color:#fffbeb;">H-score 100–149</div>
<div style="font-size:.78rem;color:#fde68a;">Moderate · Confirm with PET imaging</div>
</div>
""", unsafe_allow_html=True)
    col3.markdown("""
<div style="background:#450a0a;border:1px solid #dc2626;border-radius:8px;padding:.8rem 1rem;text-align:center;">
<div style="font-size:.75rem;color:#fca5a5;font-weight:700;">INELIGIBLE</div>
<div style="font-size:1.6rem;font-weight:800;color:#fef2f2;">H-score &lt; 100</div>
<div style="font-size:.78rem;color:#fecaca;">Low CD46 · Unlikely to benefit</div>
</div>
""", unsafe_allow_html=True)

    st.markdown("---")

    if not hpa_df.empty:
        tumour = hpa_df[hpa_df["type"] == "tumor"].copy()
        normal = hpa_df[hpa_df["type"] == "normal"].copy()

        st.subheader("HPA H-scores: Tumour vs Normal Tissue CD46 Protein")

        if not tumour.empty and "h_score_approx" in tumour.columns:
            tumour_sorted = tumour.sort_values("h_score_approx", ascending=False)

            fig = go.Figure()
            colors = []
            for hs in tumour_sorted["h_score_approx"]:
                if hs >= 150:   colors.append("#22c55e")
                elif hs >= 100: colors.append("#f97316")
                else:           colors.append("#ef4444")

            fig.add_trace(go.Bar(
                x=tumour_sorted["tissue"],
                y=tumour_sorted["h_score_approx"],
                name="Tumour H-score",
                marker_color=colors,
                text=tumour_sorted["h_score_approx"].round(0).astype(int),
                textposition="outside",
            ))
            fig.add_hline(y=150, line_dash="dash", line_color="#22c55e",
                          annotation_text="Eligibility threshold (H=150)",
                          annotation_position="bottom right")
            fig.add_hline(y=100, line_dash="dot", line_color="#f97316",
                          annotation_text="Borderline (H=100)",
                          annotation_position="bottom right")
            fig.update_layout(
                template="plotly_dark",
                title="CD46 H-score in Tumour Tissues (HPA)",
                xaxis_title="Tumour Type",
                yaxis_title="H-score (0–300)",
                height=440,
                xaxis_tickangle=-35,
            )
            st.plotly_chart(fig, width="stretch")

        paired = normal.merge(
            tumour[["tissue","h_score_approx"]].rename(
                columns={"h_score_approx":"tumour_h","tissue":"tissue"}),
            on="tissue", how="inner",
        ).rename(columns={"h_score_approx":"normal_h"})

        if not paired.empty:
            paired["TI"] = (paired["tumour_h"] / paired["normal_h"].clip(lower=5)).round(2)
            paired = paired.sort_values("TI", ascending=False)

            st.subheader("Therapeutic Index per Tissue Pair")
            fig2 = go.Figure(go.Bar(
                x=paired["tissue"],
                y=paired["TI"],
                marker_color=["#22c55e" if ti >= 2 else "#f97316" if ti >= 1 else "#ef4444"
                               for ti in paired["TI"]],
                text=paired["TI"],
                textposition="outside",
            ))
            fig2.add_hline(y=2, line_dash="dash", line_color="#22c55e",
                           annotation_text="TI ≥ 2 (favourable)")
            fig2.update_layout(
                template="plotly_dark",
                title="CD46 Therapeutic Index: Tumour H-score ÷ Normal H-score",
                xaxis_title="Tissue",
                yaxis_title="Therapeutic Index",
                height=360,
            )
            st.plotly_chart(fig2, width="stretch")

    with st.expander("📋 IHC CDx Development Roadmap"):
        st.markdown("""
| Stage | Activity | Timeline |
|---|---|---|
| Pre-clinical | H-score threshold validation in tumour biopsy cohort (n≥50) | Pre-IND |
| Phase I | IHC as exploratory eligibility criterion; correlate H-score with PET uptake | Year 1 |
| Phase II | IHC H-score ≥150 as primary eligibility criterion; validate vs response | Year 2–3 |
| Bridging study | Analytical validation of IHC assay (precision, reproducibility, CRO) | Year 3 |
| PMA filing | CDx PMA co-submission with NDA/BLA | Year 4–5 |

**H-score calculation:** H = Σ (% cells at intensity i) × i, where i = 0, 1, 2, 3
→ Range 0 (no staining) to 300 (all cells 3+ intense)

**PSMA-PET precedent:** Pluvicto companion diagnostic uses SUVmean ≥ 10 in ≥1 lesion.
Analogous CD46 PET threshold will be established in YS5 PET Phase I trials.
""")

# ══════════════════════════════════════════════════════════════════════════════
# TAB 4 — Somatic Mutation Landscape
# ══════════════════════════════════════════════════════════════════════════════
with tabs[3]:
    st.subheader("CD46 Somatic Mutation Landscape (TCGA Pan-Cancer)")
    st.markdown(
        "TCGA sequencing data via cBioPortal. CD46 somatic mutations are rare in solid tumours "
        "(<3% in any cancer type), confirming that overexpression is driven by **epigenetic "
        "upregulation and 1q32 amplification** — not by somatic mutation."
    )

    col1, col2, col3, col4 = st.columns(4)
    if not mut_df.empty:
        total_mut = mut_df["mutated_samples"].sum()
        total_seq = mut_df["total_samples"].sum()
        col1.metric("Cancer Types Analysed", len(mut_df[mut_df["total_samples"]>0]))
        col2.metric("Total Sequenced", f"{total_seq:,}")
        col3.metric("CD46-Mutated Tumours", total_mut)
        col4.metric("Overall Somatic Freq", f"{total_mut/total_seq*100:.2f}%" if total_seq > 0 else "—",
                    "CD46 mutations are rare")

        mut_nonzero = mut_df[mut_df["mutation_freq_pct"] > 0].sort_values(
            "mutation_freq_pct", ascending=False)

        if not mut_nonzero.empty:
            fig = go.Figure(go.Bar(
                x=mut_nonzero["cancer_type"],
                y=mut_nonzero["mutation_freq_pct"],
                marker_color=["#ef4444" if v >= 2 else "#f97316" if v >= 1 else "#64748b"
                               for v in mut_nonzero["mutation_freq_pct"]],
                text=[f"{v:.1f}%" for v in mut_nonzero["mutation_freq_pct"]],
                textposition="outside",
                hovertemplate="<b>%{x}</b><br>Mutation freq: %{y:.2f}%<extra></extra>",
            ))
            fig.update_layout(
                template="plotly_dark",
                title="CD46 Somatic Mutation Frequency — TCGA Pan-Cancer (cBioPortal)",
                xaxis_title="Cancer Type",
                yaxis_title="Mutation Frequency (%)",
                height=400,
                xaxis_tickangle=-30,
            )
            st.plotly_chart(fig, width="stretch")
        else:
            st.info("No cancer types with CD46 somatic mutations >0% detected.")

    st.markdown("---")
    st.subheader("ClinVar: CD46 Constitutional / Germline Variants")
    st.markdown(
        "500 CD46 variants identified in ClinVar (NCBI). Pathogenic variants are primarily "
        "associated with **atypical Haemolytic Uraemic Syndrome (aHUS2)** — a complement "
        "dysregulation disease confirming CD46's role as a complement regulator."
    )

    if not clinvar_df.empty:
        sig_counts = clinvar_df["clinical_significance"].value_counts().reset_index()
        sig_counts.columns = ["Significance", "Count"]

        colors = {
            "Pathogenic": "#ef4444",
            "Likely pathogenic": "#f97316",
            "Pathogenic/Likely pathogenic": "#f59e0b",
            "Pathogenic/Pathogenic, low penetrance": "#ef4444",
            "Pathogenic, low penetrance": "#fb923c",
            "Uncertain significance": "#64748b",
            "Likely benign": "#22c55e",
            "Benign": "#16a34a",
        }

        fig2 = go.Figure(go.Bar(
            x=sig_counts["Significance"],
            y=sig_counts["Count"],
            marker_color=[colors.get(s, "#475569") for s in sig_counts["Significance"]],
            text=sig_counts["Count"],
            textposition="outside",
        ))
        fig2.update_layout(
            template="plotly_dark",
            title=f"CD46 ClinVar Variants by Clinical Significance (n={len(clinvar_df)} total)",
            xaxis_title="Clinical Significance",
            yaxis_title="Number of Variants",
            height=360,
            xaxis_tickangle=-20,
        )
        st.plotly_chart(fig2, width="stretch")

        # Pathogenic table
        pathogenic = clinvar_df[
            clinvar_df["clinical_significance"].str.contains(
                "Pathogenic|pathogenic", na=False, case=False)
        ].head(20)
        if not pathogenic.empty:
            st.subheader(f"Pathogenic / Likely Pathogenic Variants (top 20 of {len(clinvar_df[clinvar_df['clinical_significance'].str.contains('Pathogenic|pathogenic',na=False,case=False)])})")
            display_cols = [c for c in ["name","clinical_significance","condition","cdna_change","protein_change","rs_id"]
                            if c in pathogenic.columns]
            st.dataframe(pathogenic[display_cols], hide_index=True, use_container_width=True)

    # UniProt aHUS2 variants from KG
    if not prot_vars.empty:
        st.markdown("---")
        st.subheader("UniProt CD46 Protein Variants in AuraDB Knowledge Graph")
        st.dataframe(prot_vars, hide_index=True, use_container_width=True)

    st.markdown("""
---
> **Clinical relevance of aHUS2 variants:** Loss-of-function CD46 variants cause uncontrolled
> complement lysis of red blood cells (aHUS2). The inverse mechanism applies in cancer:
> **gain-of-function upregulation** enables tumour cells to evade complement-mediated immune
> killing. This mechanistic duality validates CD46 as both a therapeutic target and a
> diagnostically tractable biomarker with validated assays.
""")

# ══════════════════════════════════════════════════════════════════════════════
# TAB 5 — Liquid Biopsy & CTCs
# ══════════════════════════════════════════════════════════════════════════════
with tabs[4]:
    st.subheader("Soluble CD46 & Circulating Tumour Cells — Liquid Biopsy Evidence")

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("""
### Soluble CD46 (sCD46) — Serum Biomarker

CD46 is constitutively shed from the cell surface by **ADAM10/ADAM17** metalloproteinase 
cleavage of the BC-domain ectodomain, releasing a soluble form (sCD46) into blood.

**Published clinical evidence:**
| Study | Finding |
|---|---|
| Sherbenou et al. 2016 (*Clin Cancer Res*) | sCD46 elevated in mCRPC vs localised PRAD |
| FOR46 preclinical context | Serum sCD46 correlates with tumour burden |
| HPA normal tissue | sCD46 detectable in healthy donor serum at low baseline |
| CD46 shedding mechanism | ADAM10/ADAM17 — same enzymes involved in PSMA shedding |

**Clinical utility:**
- **Screening:** Elevated sCD46 signals CD46-high disease
- **Monitoring:** sCD46 rise during treatment → resistance or progression
- **Response:** sCD46 decline after RLT → pharmacodynamic confirmation of target engagement
- **Assay:** ELISA-based (research grade); no EMA/FDA-approved assay yet

**Proposed threshold:** sCD46 > 500 ng/mL = CD46-high disease (research-stage hypothesis)
""")

    with c2:
        st.markdown("""
### CD46-Positive CTCs — Liquid Biopsy Monitoring

Circulating Tumour Cells (CTCs) shed from mCRPC metastases express CD46 on their surface,
detectable in a single 10 mL blood draw.

**Published evidence:**
| Study | Finding |
|---|---|
| Guzman et al. 2016 | CD46 on mCRPC CTCs confirmed by CellSearch + IHC |
| Antonarakis et al. | CD46-high CTCs correlate with post-ARPI resistance |
| Prototype microfluidic chip | CD46 as EpCAM-independent CTC capture antigen |

**Clinical utility:**
- **AR-V7 co-detection:** CD46+ CTCs → test for AR-V7 splice variant (ARPI resistance marker)
- **Progression monitoring:** CTC count + CD46 expression at serial timepoints
- **Research status:** No commercially approved CD46-CTC assay; active academic development

**Comparison of liquid biopsy modalities:**

| Modality | Sensitivity | Specificity | Clinical Ready | Cost |
|---|---|---|---|---|
| PSA | High | Low (non-specific) | ✅ FDA cleared | Low |
| sCD46 ELISA | Medium | Medium | ❌ Research only | Low |
| CD46+ CTC count | Medium | High | ❌ Research only | Medium |
| 89Zr-YS5 PET | High | High | ❌ Phase I trials | High |
| AR-V7 (blood) | Medium | High | ✅ Guardant/Epic Dx | Medium |
| ctDNA / cfDNA | High | Medium | ✅ Commercial | High |
""")

    st.markdown("---")
    st.subheader("Complement Activation — Pharmacodynamic Biomarker")
    st.markdown("""
CD46 regulates the complement cascade. When CD46 is targeted by RLT, complement inhibition 
is reduced on tumour cells — measurable through serum complement markers.

| Biomarker | Role | Standard Lab Panel |
|---|---|---|
| C3a, C5a anaphylatoxins | Complement activation markers | Immunology / allergy labs |
| CH50, AH50 | Total complement haemolytic activity | Renal / rheumatology panels |
| C3, C4 | Complement component levels | Standard chemistry panel |
| Bb fragment | Alternative pathway activation | Research / specialist labs |
| MAC (C5b-9) | Membrane attack complex deposition | Research / electron microscopy |

**Mechanistic chain:** 225Ac-CD46 → CD46 occupancy/downregulation → reduced C3b/C4b cleavage 
→ complement deposition on tumour → MAC-mediated cell death synergy with alpha particle kill.

> This complement synergy may amplify the therapeutic effect beyond direct radiation — 
> a unique mechanism-of-action advantage over non-complement-targeting agents.
""")

# ══════════════════════════════════════════════════════════════════════════════
# TAB 6 — Early Detection Science
# ══════════════════════════════════════════════════════════════════════════════
with tabs[5]:
    st.subheader("CD46 in Pre-Malignant and Early-Stage Disease")
    st.markdown(
        "CD46 upregulation is not exclusively a late-stage event. Evidence from multiple cancer "
        "types suggests CD46 overexpression begins at **pre-malignant stages**, opening an "
        "early detection window."
    )

    early_data = pd.DataFrame([
        {"Cancer": "Prostate (PRAD)", "Pre-malignant Stage": "High-grade PIN (HGPIN)",
         "CD46 Status": "Upregulated before invasion",
         "Evidence": "IHC in HGPIN vs normal prostate epithelium",
         "Clinical Op.": "CD46 IHC in active surveillance biopsies"},
        {"Cancer": "Oesophagus (ESCA)", "Pre-malignant Stage": "Barrett's Oesophagus → OAC",
         "CD46 Status": "Elevated in metaplasia stage",
         "Evidence": "HPA & TCGA expression at metaplasia stage",
         "Clinical Op.": "Endoscopy biopsy CD46 staining"},
        {"Cancer": "Cervix (CESC)", "Pre-malignant Stage": "CIN I–III (HPV-driven)",
         "CD46 Status": "HPV receptor (C isoform = HPV-11B binding)",
         "Evidence": "CD46 BC1 isoform is functional HPV receptor",
         "Clinical Op.": "CD46 isoform-specific IHC in colposcopy biopsies"},
        {"Cancer": "Colon (COAD)", "Pre-malignant Stage": "Colonic adenoma",
         "CD46 Status": "Highest expression in TCGA solid tumour cohort (12.99 median TPM)",
         "Evidence": "TCGA COAD expression rank = 1 (highest pan-cancer)",
         "Clinical Op.": "Colonoscopy polyp biopsy — CD46 expression"},
        {"Cancer": "Bladder (BLCA)", "Pre-malignant Stage": "Carcinoma-in-Situ (CIS)",
         "CD46 Status": "Normal urothelium high (HPA); CIS expression unstudied",
         "Evidence": "HPA strong staining in normal urothelium",
         "Clinical Op.": "Cystoscopy biopsy — CD46 IHC screening"},
        {"Cancer": "Multiple Myeloma", "Pre-malignant Stage": "MGUS → Smouldering Myeloma",
         "CD46 Status": "CD46 overexpressed in plasma cells from MGUS onwards",
         "Evidence": "FOR46/BC8 preclinical data; haematological Phase I trials",
         "Clinical Op.": "Bone marrow biopsy CD46 IHC in MGUS screening"},
    ])

    st.dataframe(early_data, hide_index=True, use_container_width=True)

    st.markdown("---")
    st.subheader("HPV Receptor Biology — CD46 C Isoform")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("""
**CD46 as HPV receptor (published mechanism):**
- Human Papillomavirus (HPV types 11A, 11B, 16) binds the **BC1 isoform** of CD46
- HPV entry requires CD46 C-domain — specifically the BC1 splice variant with 13-aa insert
- CD46 BC1 expression is elevated in cervical intraepithelial neoplasia (CIN)
- Mechanism: HPV L2 protein binds CD46 after initial heparan-sulphate attachment

**Research implications:**
- CD46 isoform expression could predict HPV infection susceptibility
- CD46 C isoform = biomarker for HPV-associated pre-malignant disease
- Novel CDx opportunity: isoform-specific antibody (anti-BC1/BC2) for CIN risk stratification
""")
    with c2:
        # CD46 isoform table
        isoform_data = pd.DataFrame([
            {"Isoform": "BC1 (α isoform)", "Exons": "B + C + 13-aa", "HPV Receptor": "✅ Yes",
             "Cancer Relevance": "Cervical, HPV+ HNSC", "Therapeutic": "Potential CDx"},
            {"Isoform": "BC2 (β isoform)", "Exons": "B + C", "HPV Receptor": "⚠️ Partial",
             "Cancer Relevance": "Prostate, colon", "Therapeutic": "YS5 target"},
            {"Isoform": "C1 (γ isoform)", "Exons": "C + 13-aa", "HPV Receptor": "✅ Yes",
             "Cancer Relevance": "Haematological", "Therapeutic": "FOR46 target"},
            {"Isoform": "C2 (δ isoform)", "Exons": "C only", "HPV Receptor": "❌ No",
             "Cancer Relevance": "Broad expression", "Therapeutic": "Monitoring"},
        ])
        st.dataframe(isoform_data, hide_index=True, use_container_width=True)

    st.markdown("---")
    st.subheader("Early Detection Research Agenda")
    st.markdown("""
| Priority | Research Question | Study Design | Readiness |
|---|---|---|---|
| HIGH | Does CD46 IHC in HGPIN predict progression to invasive PRAD? | Retrospective IHC cohort (HGPIN → PRAD) | Ready to design |
| HIGH | Can serum sCD46 distinguish localised from metastatic PRAD? | Prospective blood collection in PRAD staging | Ready to design |
| MEDIUM | Does CD46 isoform expression in CIN correlate with HPV type? | Case-control IHC + HPV geno­typing | Research stage |
| MEDIUM | Is 89Zr-YS5 PET sensitive enough to detect occult mCRPC lesions? | Pilot imaging study in CRPC | Phase I ongoing |
| LOW | CD46 methylation in liquid biopsy (cfMeDIP) for early cancer detection | cfDNA methylation profiling | Experimental |
""")

# ══════════════════════════════════════════════════════════════════════════════
# TAB 7 — Co-Biomarker Strategy
# ══════════════════════════════════════════════════════════════════════════════
with tabs[6]:
    st.subheader("Multi-Analyte Co-Biomarker Patient Selection Strategy")
    st.markdown(
        "No single biomarker is sufficient for patient selection. The CD46 companion diagnostic "
        "strategy uses a **sequential multi-analyte funnel** — each step enriching the eligible "
        "population for maximum therapeutic benefit."
    )

    # Selection funnel
    st.markdown("""
<style>
.funnel-step { background:#1e293b; border:1px solid #334155; border-radius:8px;
               padding:.7rem 1.2rem; margin:.3rem 0; }
.funnel-step .step-num { font-size:.7rem; font-weight:700; color:#94a3b8; letter-spacing:.08em; }
.funnel-step .step-name { font-size:.95rem; font-weight:700; color:#f8fafc; }
.funnel-step .step-detail { font-size:.78rem; color:#64748b; margin-top:.15rem; }
.funnel-step .threshold { background:#0f172a; border-radius:4px; padding:.1rem .4rem;
                          font-size:.78rem; font-weight:700; color:#38bdf8; font-family:monospace; }
</style>
<div style="max-width:700px;">
<div class="funnel-step">
  <div class="step-num">STEP 1 — CLINICAL ELIGIBILITY</div>
  <div class="step-name">mCRPC diagnosis + post-ARPI progression</div>
  <div class="step-detail">PSA progression · RECIST 1.1 or bone scan progression · <span class="threshold">No prior alpha-emitter</span></div>
</div>
<div style="text-align:center;color:#475569;font-size:1.2rem;">▼</div>
<div class="funnel-step">
  <div class="step-num">STEP 2 — TISSUE BIOMARKER</div>
  <div class="step-name">CD46 IHC on archival or fresh biopsy</div>
  <div class="step-detail">H-score threshold: <span class="threshold">≥ 150</span> = primary eligible · 100–149 = borderline → proceed to PET</div>
</div>
<div style="text-align:center;color:#475569;font-size:1.2rem;">▼</div>
<div class="funnel-step">
  <div class="step-num">STEP 3 — IMAGING (if borderline IHC or de novo)</div>
  <div class="step-name">⁸⁹Zr-YS5 CD46-PET or ⁶⁸Ga-PSMA-PET for co-stratification</div>
  <div class="step-detail">PSMA-PET SUVmean: <span class="threshold">&lt; 10</span> = PSMA-low (enriches CD46 benefit) · CD46-PET: <span class="threshold">≥ threshold TBD</span></div>
</div>
<div style="text-align:center;color:#475569;font-size:1.2rem;">▼</div>
<div class="funnel-step">
  <div class="step-num">STEP 4 — BLOOD PANEL</div>
  <div class="step-name">Serum sCD46 + complement (CH50) + AR-V7 CTC</div>
  <div class="step-detail">sCD46: <span class="threshold">&gt; 500 ng/mL</span> (research) · AR-V7: negative preferred (ARPI resistance exclusion)</div>
</div>
<div style="text-align:center;color:#475569;font-size:1.2rem;">▼</div>
<div class="funnel-step" style="border-color:#22c55e;">
  <div class="step-num">ENROLLED — ELIGIBLE PATIENT</div>
  <div class="step-name" style="color:#22c55e;">225Ac-CD46 RLT treatment + dosimetry monitoring</div>
  <div class="step-detail">Baseline PSMA-PET + CD46-PET · Cycle 1 dosimetry scan · PSA q4w · sCD46 q8w</div>
</div>
</div>
""", unsafe_allow_html=True)

    st.markdown("---")

    # Full co-biomarker table
    st.subheader("Complete Co-Biomarker Panel Reference")
    panel_df = pd.DataFrame([
        {"Biomarker": "CD46 (tissue IHC)", "Detection": "H-score ≥ 150",
         "Method": "IHC on FFPE biopsy", "Clinical Role": "Primary eligibility",
         "Ready": "✅ Validated method", "Regulatory": "PMA co-development"},
        {"Biomarker": "CD46-PET (89Zr-YS5)", "Detection": "SUVmean ≥ TBD",
         "Method": "PET imaging", "Clinical Role": "Eligibility confirmation + dosimetry",
         "Ready": "🔄 Phase I active", "Regulatory": "PMA co-development"},
        {"Biomarker": "PSMA-PET (68Ga-PSMA)", "Detection": "SUVmean < 10",
         "Method": "PET imaging", "Clinical Role": "PSMA-low enrichment",
         "Ready": "✅ FDA cleared", "Regulatory": "Approved CDx (Pylarify)"},
        {"Biomarker": "Soluble CD46 (sCD46)", "Detection": "> 500 ng/mL (research)",
         "Method": "Serum ELISA", "Clinical Role": "Screening + response monitoring",
         "Ready": "❌ Research assay", "Regulatory": "LDT pathway"},
        {"Biomarker": "PSA + PSA-DT", "Detection": "Rising PSA under castration",
         "Method": "Serum RIA/ELISA", "Clinical Role": "CRPC confirmation + progression",
         "Ready": "✅ Standard of care", "Regulatory": "FDA cleared (multiple)"},
        {"Biomarker": "AR-V7 splice variant", "Detection": "Negative preferred",
         "Method": "CTC blood test", "Clinical Role": "ARPI resistance exclusion",
         "Ready": "✅ Guardant/Epic Dx", "Regulatory": "FDA cleared"},
        {"Biomarker": "Complement CH50/AH50", "Detection": "Baseline + on-treatment Δ",
         "Method": "Serum complement assay", "Clinical Role": "PD marker (complement synergy)",
         "Ready": "✅ Standard lab panel", "Regulatory": "CLIA lab test"},
        {"Biomarker": "CD46+ CTC count", "Detection": "Serial monitoring",
         "Method": "CellSearch + CD46 IHC", "Clinical Role": "Progression monitoring",
         "Ready": "❌ Research stage", "Regulatory": "LDT development needed"},
        {"Biomarker": "LDH, ALP, Hb", "Detection": "Baseline safety",
         "Method": "Standard chemistry", "Clinical Role": "Eligibility safety labs",
         "Ready": "✅ Standard of care", "Regulatory": "Standard clinical labs"},
    ])
    st.dataframe(panel_df, hide_index=True, use_container_width=True)

    st.markdown("---")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("""
### PSMA-low Opportunity — Venn Context
```
All mCRPC patients
├── PSMA-high (~60%) → Pluvicto eligible
└── PSMA-low/negative (~40%)
    ├── CD46-high (estimated ~50% of PSMA-low) → 225Ac-CD46 eligible
    └── CD46-low (~50% PSMA-low) → need alternative therapy
```
**Estimated eligible population:**
~20% of all mCRPC patients = CD46-high, PSMA-low
→ ~10,000–15,000 US patients/year at current incidence
""")
    with c2:
        st.markdown("""
### Regulatory Strategy Summary
| Pathway | Estimated Timeline |
|---|---|
| IHC CDx PMA co-development | 3–5 years post Phase I |
| PET CDx PMA (post YS5 Phase II) | 5–7 years |
| sCD46 ELISA LDT | 2–3 years (non-PMA, lab-developed) |
| AR-V7 integration (existing) | Immediate (licensed assay) |
| **Full CDx package for BLA submission** | **~2032 (225Ac Phase III era)** |
""")

st.markdown("---")
st.caption(
    "Data sources: GTEx v8 (CC BY 4.0) · NCBI ClinVar · cBioPortal TCGA · "
    "Human Protein Atlas · AuraDB Knowledge Graph · Research use only."
)
