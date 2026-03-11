"""Page 8 — Patient Eligibility Scorer: 225Ac-CD46 Therapy Candidate Assessment."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import math
import os

import pandas as pd
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

st.title("🎯 Patient Eligibility Scorer")
st.markdown(
    "**Evidence-based candidate assessment for 225Ac-CD46 radiopharmaceutical therapy. "
    "Integrates CD46 expression rank, clinical survival impact, co-biomarker context, and "
    "treatment history across 25 TCGA cancer types (n > 2,800 patients).**"
)

# ---------------------------------------------------------------------------
# Data loaders
# ---------------------------------------------------------------------------


@st.cache_data(ttl=3600)
def load_by_cancer() -> pd.DataFrame:
    p = DATA_DIR / "cd46_by_cancer.csv"
    return pd.read_csv(p) if p.exists() else pd.DataFrame()


@st.cache_data(ttl=3600)
def load_survival() -> pd.DataFrame:
    p = DATA_DIR / "cd46_survival_results.csv"
    return pd.read_csv(p) if p.exists() else pd.DataFrame()


@st.cache_data(ttl=3600)
def load_priority() -> pd.DataFrame:
    p = DATA_DIR / "priority_score.csv"
    return pd.read_csv(p) if p.exists() else pd.DataFrame()

@st.cache_data(ttl=3600)
def load_genie() -> pd.DataFrame:
    p = DATA_DIR / "genie_full_cohort.parquet"
    return pd.read_parquet(p) if p.exists() else pd.DataFrame()

# ---------------------------------------------------------------------------
# Scoring logic
# ---------------------------------------------------------------------------

CANCER_LABELS: dict[str, str] = {
    "LUAD": "Lung Adenocarcinoma",
    "PRAD": "Prostate Adenocarcinoma",
    "COAD": "Colorectal Adenocarcinoma",
    "BRCA": "Breast Carcinoma",
    "BLCA": "Bladder Urothelial Carcinoma",
    "ACC": "Adrenocortical Carcinoma",
    "PAAD": "Pancreatic Adenocarcinoma",
    "LUSC": "Lung Squamous Cell Carcinoma",
    "KIRC": "Kidney Clear Cell Carcinoma",
    "STAD": "Gastric Adenocarcinoma",
    "PCPG": "Pheochromocytoma / Paraganglioma",
    "OV": "Ovarian Serous Cystadenocarcinoma",
    "CESC": "Cervical Squamous Cell Carcinoma",
    "LIHC": "Liver Hepatocellular Carcinoma",
    "KIRP": "Kidney Papillary Cell Carcinoma",
    "UCEC": "Uterine Corpus Endometrial Carcinoma",
    "THCA": "Thyroid Carcinoma",
    "LAML": "Acute Myeloid Leukemia",
    "HNSC": "Head & Neck Squamous Cell Carcinoma",
    "THYM": "Thymoma",
    "SKCM": "Skin Cutaneous Melanoma",
    "SARC": "Sarcoma",
    "TGCT": "Testicular Germ Cell Tumors",
    "GBM": "Glioblastoma Multiforme",
    "LGG": "Brain Lower Grade Glioma",
}

TCGA_TO_GENIE_MAP = {
    "LUAD": "Non-Small Cell Lung Cancer",
    "LUSC": "Non-Small Cell Lung Cancer",
    "PRAD": "Prostate Cancer",
    "COAD": "Colorectal Cancer",
    "BRCA": "Breast Cancer",
    "BLCA": "Bladder Cancer",
    "PAAD": "Pancreatic Cancer",
    "KIRC": "Renal Cell Carcinoma",
    "KIRP": "Renal Cell Carcinoma",
    "STAD": "Esophagogastric Cancer",
    "OV": "Ovarian Cancer",
    "LIHC": "Hepatobiliary Cancer",
    "UCEC": "Endometrial Cancer",
    "LAML": "Leukemia",
    "SKCM": "Melanoma",
    "SARC": "Soft Tissue Sarcoma",
    "GBM": "Glioma",
    "LGG": "Glioma"
}


def compute_expression_score(
    rank: int,
    cd46_level: float,
    cancer_median: float,
    cancer_std: float,
) -> float:
    """
    0–35 pts based on cancer-type expression rank (1 = highest CD46 across TCGA),
    adjusted ±5 pts by the individual patient's CD46 level relative to the cancer median.
    """
    base = max(0.0, (26 - rank) / 25.0) * 35.0
    if cancer_std > 0:
        z = (cd46_level - cancer_median) / cancer_std
        modifier = 5.0 * math.tanh(z)   # smooth ±5 adjustment
    else:
        modifier = 0.0
    return max(0.0, min(35.0, base + modifier))


def compute_survival_score(
    df_surv: pd.DataFrame, cancer_type: str
) -> tuple[float, str]:
    """0–35 pts from OS hazard ratio significance."""
    os_rows = df_surv[
        (df_surv["cancer_type"] == cancer_type) & (df_surv["endpoint"] == "OS")
    ]
    if os_rows.empty:
        return 0.0, "No OS survival data available for this indication."
    row = os_rows.iloc[0]
    hr = float(row.get("hazard_ratio", 1.0))
    sig = bool(row.get("significant", False))
    pval = float(row.get("p_value", 1.0))
    if hr > 1.0 and sig:
        return (
            35.0,
            f"CD46-high patients have significantly **worse** OS (HR = {hr:.2f}, p = {pval:.4f}) "
            "— strongest therapy rationale.",
        )
    if hr > 1.0 and not sig:
        return (
            20.0,
            f"CD46-high associated with worse OS trend (HR = {hr:.2f}, p = {pval:.4f}) "
            "— supportive but non-significant signal.",
        )
    if hr <= 1.0 and sig:
        return (
            5.0,
            f"CD46-high associated with **better** OS in this indication (HR = {hr:.2f}, p = {pval:.4f}) "
            "— weaker therapy rationale; selection biomarker needed.",
        )
    return (
        10.0,
        f"No significant survival impact detected (HR = {hr:.2f}, p = {pval:.4f}).",
    )


def compute_biomarker_score(psma: str, complement: str) -> tuple[float, str]:
    """
    0–15 pts. PSMA co-expression dominates (0/5/12); complement activity adds up to +3.
    """
    psma_pts = {"Positive": 12, "Unknown": 5, "Negative": 0}[psma]
    comp_pts = {"High": 3, "Unknown": 1, "Low": 0}[complement]
    score = min(15.0, float(psma_pts + comp_pts))
    parts: list[str] = []
    if psma == "Positive":
        parts.append("PSMA co-expression supports dual-target approach")
    elif psma == "Negative":
        parts.append("PSMA-negative profile — CD46 single-target strategy applies")
    if complement == "High":
        parts.append("elevated complement activity potentiates CD46 targeting")
    explanation = "; ".join(parts) if parts else "Limited co-biomarker context — exploratory assessment."
    return score, explanation


def compute_clinical_score(therapy: str) -> tuple[float, str]:
    """0–15 pts based on treatment history and positioning."""
    mapping = {
        "Taxane-Refractory": (
            15.0,
            "Post-taxane setting — highest unmet need; alpha-particle RLT well-positioned as salvage.",
        ),
        "Post-ARSI": (
            10.0,
            "Post-ARSI setting — established unmet need for novel mechanism.",
        ),
        "Treatment Naive": (
            5.0,
            "Treatment-naive — CD46-RLT may suit combination or biomarker-selected first-line strategy.",
        ),
    }
    return mapping[therapy]


def classify(score: float) -> tuple[str, str, str, str]:
    """Return (category, colour, icon, description)."""
    if score >= 70:
        return (
            "HIGH",
            "#27ae60",
            "🟢",
            "Strong candidate. Evidence supports prioritised clinical evaluation.",
        )
    if score >= 45:
        return (
            "MODERATE",
            "#e67e22",
            "🟡",
            "Moderate candidate. Biomarker enrichment or combination strategy recommended.",
        )
    return (
        "EXPLORATORY",
        "#e74c3c",
        "🔴",
        "Exploratory context. Limited current evidence; consider biomarker-selected sub-cohort design.",
    )


# ---------------------------------------------------------------------------
# Load data
# ---------------------------------------------------------------------------

df_expr = load_by_cancer()
df_surv = load_survival()
df_priority = load_priority()
df_genie = load_genie()

if df_expr.empty:
    st.error("Expression data unavailable — check data/processed/cd46_by_cancer.csv")
    st.stop()

cancer_types = df_expr["cancer_type"].tolist()
default_idx = cancer_types.index("PRAD") if "PRAD" in cancer_types else 0

# ---------------------------------------------------------------------------
# Input / Output layout
# ---------------------------------------------------------------------------

col_input, col_output = st.columns([1, 1.4], gap="large")

with col_input:
    st.subheader("Patient & Tumour Profile")
    with st.form("eligibility_form"):
        cancer_sel = st.selectbox(
            "Cancer type (TCGA)",
            options=cancer_types,
            format_func=lambda c: f"{c} — {CANCER_LABELS.get(c, c)}",
            index=default_idx,
        )

        st.caption(
            "Patient CD46 expression level (log₂ TPM) — adjust to match biopsy result "
            "or leave at 12.0 to use TCGA population average."
        )
        cd46_level = st.slider(
            "CD46 expression level (log₂ TPM)",
            min_value=0.0,
            max_value=16.0,
            value=12.0,
            step=0.1,
        )

        psma_status = st.radio(
            "PSMA co-expression",
            options=["Unknown", "Positive", "Negative"],
            horizontal=True,
        )

        prior_therapy = st.radio(
            "Prior systemic therapy",
            options=["Treatment Naive", "Post-ARSI", "Taxane-Refractory"],
        )

        complement_activity = st.radio(
            "Complement pathway activity",
            options=["Unknown", "High", "Low"],
            horizontal=True,
        )

        st.form_submit_button(
            "Calculate Eligibility Score",
            use_container_width=True,
            type="primary",
        )

# ---------------------------------------------------------------------------
# Compute scores (always runs — form_submit just re-renders with new values)
# ---------------------------------------------------------------------------

expr_row = df_expr[df_expr["cancer_type"] == cancer_sel]
if not expr_row.empty:
    expression_rank = int(expr_row["expression_rank"].iloc[0])
    cancer_median = float(expr_row["cd46_median"].iloc[0])
    cancer_std = float(expr_row["cd46_std"].iloc[0])
    n_samples = int(expr_row["n_samples"].iloc[0])
else:
    expression_rank, cancer_median, cancer_std, n_samples = 13, 12.0, 0.6, 0

expr_score = compute_expression_score(expression_rank, cd46_level, cancer_median, cancer_std)
surv_score, surv_expl = compute_survival_score(df_surv, cancer_sel)
bio_score, bio_expl = compute_biomarker_score(psma_status, complement_activity)
clin_score, clin_expl = compute_clinical_score(prior_therapy)

total_score = expr_score + surv_score + bio_score + clin_score
category, cat_colour, cat_icon, cat_desc = classify(total_score)

# ---------------------------------------------------------------------------
# Score output panel
# ---------------------------------------------------------------------------

with col_output:
    st.subheader("Eligibility Assessment")

    # Gauge chart
    fig_gauge = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=round(total_score, 1),
            gauge={
                "axis": {"range": [0, 100], "tickwidth": 1, "tickcolor": "#555"},
                "bar": {"color": cat_colour, "thickness": 0.25},
                "bgcolor": "white",
                "steps": [
                    {"range": [0, 45], "color": "#fde8e8"},
                    {"range": [45, 70], "color": "#fef3cd"},
                    {"range": [70, 100], "color": "#d4edda"},
                ],
                "threshold": {
                    "line": {"color": "#333", "width": 3},
                    "thickness": 0.85,
                    "value": 70,
                },
            },
            title={"text": "Eligibility Score (0 – 100)", "font": {"size": 14}},
            number={"font": {"size": 56, "color": cat_colour}},
        )
    )
    fig_gauge.update_layout(height=270, margin={"t": 40, "b": 10, "l": 20, "r": 20})
    st.plotly_chart(fig_gauge, width='stretch')

    m1, m2 = st.columns(2)
    m1.metric("Overall Score", f"{total_score:.1f} / 100")
    m2.metric("Candidate Category", f"{cat_icon} {category}")
    st.caption(f"*{cat_desc}*")

    # Score breakdown bar chart
    components = [
        "Expression (0–35)",
        "Survival Impact (0–35)",
        "Biomarker Context (0–15)",
        "Clinical Profile (0–15)",
    ]
    values = [expr_score, surv_score, bio_score, clin_score]
    colours = ["#3498db", "#9b59b6", "#e67e22", "#27ae60"]

    fig_bar = go.Figure(
        go.Bar(
            x=values,
            y=components,
            orientation="h",
            marker_color=colours,
            text=[f"{v:.1f}" for v in values],
            textposition="outside",
            cliponaxis=False,
        )
    )
    fig_bar.update_layout(
        height=220,
        margin={"t": 10, "b": 10, "l": 10, "r": 50},
        xaxis={"range": [0, 42], "title": "Points"},
        yaxis={"title": ""},
        plot_bgcolor="white",
        showlegend=False,
    )
    st.plotly_chart(fig_bar, width='stretch')

# ---------------------------------------------------------------------------
# Evidence detail tabs
# ---------------------------------------------------------------------------

st.divider()
st.subheader("Evidence & Context")

tab_ev, tab_genie, tab_sim = st.tabs(["Evidence Summary", "🌍 GENIE Real-World Context", "Similar Indications"])

with tab_ev:
    ev1, ev2 = st.columns(2)

    with ev1:
        cancer_label = CANCER_LABELS.get(cancer_sel, cancer_sel)
        st.markdown("**Expression Evidence (TCGA)**")
        st.markdown(f"- Cancer type: **{cancer_sel}** — {cancer_label}")
        st.markdown(f"- CD46 expression rank: **#{expression_rank} of 25** TCGA cancer types")
        st.markdown(f"- TCGA cohort median log₂ TPM: **{cancer_median:.3f}**")
        st.markdown(f"- Patient input level: **{cd46_level:.1f}** log₂ TPM")
        st.markdown(f"- Samples in TCGA cohort: **{n_samples:,}**")

        st.markdown("**Survival Evidence (TCGA OS)**")
        st.markdown(f"- {surv_expl}")

    with ev2:
        st.markdown("**Co-Biomarker Context**")
        st.markdown(f"- PSMA status: **{psma_status}**")
        st.markdown(f"- Complement activity: **{complement_activity}**")
        st.markdown(f"- {bio_expl}")

        st.markdown("**Clinical Profile**")
        st.markdown(f"- Prior therapy: **{prior_therapy}**")
        st.markdown(f"- {clin_expl}")

    # Survival data table
    if not df_surv.empty:
        surv_cancer = df_surv[df_surv["cancer_type"] == cancer_sel][
            [
                "endpoint",
                "n_high",
                "n_low",
                "hazard_ratio",
                "hr_lower_95",
                "hr_upper_95",
                "p_value",
                "significant",
            ]
        ].copy()
        if not surv_cancer.empty:
            st.markdown("**Full Survival Data**")
            surv_cancer.columns = [
                "Endpoint",
                "N (CD46-high)",
                "N (CD46-low)",
                "Hazard Ratio",
                "HR 95% CI Lower",
                "HR 95% CI Upper",
                "p-value",
                "Significant",
            ]
            st.dataframe(
                surv_cancer.reset_index(drop=True),
                use_container_width=True,
                hide_index=True,
            )

with tab_genie:
    st.markdown("#### AACR Project GENIE 19.0 — Cohort Context")
    if df_genie.empty:
        st.warning("GENIE data not found. Run the extraction pipeline.")
    else:
        genie_name = TCGA_TO_GENIE_MAP.get(cancer_sel)
        if genie_name:
            st.info(f"Mapping TCGA **{cancer_sel}** to GENIE **{genie_name}**.")
            g_cohort = df_genie[df_genie["CANCER_TYPE"] == genie_name]
            total_g = len(g_cohort)
            
            if total_g > 0:
                # Calculate real-world frequencies
                g = g_cohort.copy()
                g["AR"] = g["AR_Mutated"] | g["AR_Amplified"]
                g["PTEN"] = g["PTEN_Mutated"] | g["PTEN_Deleted"]
                g["TP53"] = g["TP53_Mutated"]
                ar_alt = g["AR"].sum()
                pten_alt = g["PTEN"].sum()
                tp53_alt = g["TP53"].sum()
                any_alt = (g["AR"] | g["PTEN"] | g["TP53"]).sum()
                triple_hit = (g["AR"] & g["PTEN"] & g["TP53"]).sum()
                ar_pten = (g["AR"] & g["PTEN"]).sum()

                c1, c2, c3, c4, c5 = st.columns(5)
                c1.metric("Real-World Patients", f"{total_g:,}")
                c2.metric("AR Altered", f"{(ar_alt/total_g)*100:.1f}%")
                c3.metric("PTEN Altered", f"{(pten_alt/total_g)*100:.1f}%")
                c4.metric("TP53 Mutated", f"{(tp53_alt/total_g)*100:.1f}%")
                c5.metric("Any Driver", f"{(any_alt/total_g)*100:.1f}%", "at least 1")

                st.caption(
                    "\U0001F9EC CD46 is targeted by **protein overexpression** (IHC/RNA-seq), "
                    "not genomic alteration. AR and PTEN alterations identify patients where CD46 is most upregulated."
                )

                # Full 8-segment molecular landscape chart
                st.markdown("**Molecular Landscape \u2014 Driver Alteration Subtypes:**")

                def _classify_p8(row):
                    ar, pt, t = row["AR"], row["PTEN"], row["TP53"]
                    if ar and pt and t:  return "AR + PTEN + TP53 (Triple-Hit)"
                    if ar and pt:        return "AR + PTEN \u2192 CD46 Priority"
                    if ar and t:         return "AR + TP53"
                    if pt and t:         return "PTEN + TP53"
                    if ar:               return "AR Only"
                    if pt:               return "PTEN Only"
                    if t:                return "TP53 Only"
                    return "No Detected Driver Alteration"

                g["Segment"] = g.apply(_classify_p8, axis=1)
                seg_df = g["Segment"].value_counts().reset_index()
                seg_df.columns = ["Segment", "Patients"]
                seg_df["%"] = (seg_df["Patients"] / total_g * 100).round(1)

                _seg_order = [
                    "AR + PTEN + TP53 (Triple-Hit)", "AR + PTEN \u2192 CD46 Priority",
                    "AR + TP53", "PTEN + TP53", "AR Only", "PTEN Only",
                    "TP53 Only", "No Detected Driver Alteration"
                ]
                _seg_colors = [
                    "#7c3aed", "#8b5cf6", "#3b82f6", "#f97316",
                    "#38bdf8", "#f59e0b", "#f87171", "#334155"
                ]
                color_map = dict(zip(_seg_order, _seg_colors))
                seg_df["Color"] = seg_df["Segment"].map(color_map).fillna("#6b7280")
                seg_df["Segment"] = pd.Categorical(seg_df["Segment"], categories=_seg_order, ordered=True)
                seg_df = seg_df.sort_values("Segment")

                import plotly.graph_objects as _go_p8
                bar_p8 = _go_p8.Figure(_go_p8.Bar(
                    x=seg_df["Segment"], y=seg_df["%"],
                    marker_color=seg_df["Color"].tolist(),
                    text=seg_df["%"].astype(str) + "%",
                    textposition="outside"
                ))
                bar_p8.update_layout(
                    height=320, xaxis_tickangle=-35,
                    yaxis_title="% of Patients",
                    margin=dict(t=10, b=80, l=10, r=10),
                    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)"
                )
                st.plotly_chart(bar_p8, use_container_width=True)

                st.markdown(f"**Clinical Translation for {cancer_sel}:**")
                if ar_alt/total_g > 0.05:
                    st.markdown(
                        f"- **AR alterations** ({ar_alt/total_g:.1%}) drive castrate-resistant disease; "
                        "androgen deprivation upregulates CD46 expression 2\u20133\u00d7."
                    )
                if pten_alt/total_g > 0.05:
                    st.markdown(
                        f"- **PTEN loss** ({pten_alt/total_g:.1%}) activates PI3K/AKT and elevates CD46 surface expression."
                    )
                if ar_pten > 0:
                    st.markdown(
                        f"- **{ar_pten/total_g*100:.1f}% AR+PTEN co-altered** (double-hit) \u2014 "
                        "highest-priority 225Ac-CD46 subgroup."
                    )
                if triple_hit > 0:
                    st.markdown(
                        f"- **{triple_hit/total_g*100:.1f}% triple-hit** (AR+PTEN+TP53) \u2014 most aggressive phenotype, "
                        "most likely to have failed prior therapies."
                    )
                if tp53_alt/total_g > 0.2:
                    st.markdown(
                        f"- **TP53 mutations** ({tp53_alt/total_g:.1%}) reflect aggressive biology "
                        "where conventional therapies frequently fail."
                    )
            else:
                st.write(f"No patients found for {genie_name} in the targeted GENIE cohort.")
        else:
            st.write(f"No direct GENIE broad cancer type mapping available for TCGA {cancer_sel}.")

with tab_sim:
    st.markdown(
        "**Top 5 similar indications by CD46 evidence profile** "
        "(ranked by composite priority score across expression + survival dimensions)"
    )
    if not df_priority.empty:
        df_sim = (
            df_priority[df_priority["cancer_type"] != cancer_sel]
            .sort_values("priority_score", ascending=False)
            .head(5)
        )
        display_cols = {
            "cancer_type": "Cancer Type",
            "expression_rank": "CD46 Rank",
            "cd46_median": "Median log₂ TPM",
            "priority_score": "Priority Score",
            "priority_label": "Category",
        }
        df_display = df_sim[list(display_cols.keys())].rename(columns=display_cols).copy()
        df_display["Cancer Type"] = df_display["Cancer Type"].apply(
            lambda c: f"{c} — {CANCER_LABELS.get(c, c)}"
        )
        df_display["Priority Score"] = df_display["Priority Score"].round(3)
        df_display["Median log₂ TPM"] = df_display["Median log₂ TPM"].round(3)
        st.dataframe(
            df_display.reset_index(drop=True),
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info("Priority score data unavailable.")

# ---------------------------------------------------------------------------
# Disclaimer
# ---------------------------------------------------------------------------

st.divider()
st.caption(
    "**Research use only.** All scores derive from publicly available TCGA genomic data. "
    "This tool does not constitute medical advice. "
    "Clinical patient selection for radiopharmaceutical therapy trials requires "
    "prospective biomarker validation and regulatory approval."
)
