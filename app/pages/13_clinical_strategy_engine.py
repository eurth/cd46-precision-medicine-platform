"""Page 13 — Clinical Strategy Engine
End-to-end development narrative: Target → Drug → Patient → Trial → Outcome.
Gene-parameterized via get_active_symbol() / strategy_context().
"""
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from components.theme import apply_plotly_layout
from components.targets import get_active_symbol, get_target, render_stub_gate
from components.target_narratives import strategy_context, strategy_purpose, strategy_stage1_title
from components.gene_data import load_trials_summary
from components.ui_kit import page_header, research_table

# ── Streamlit Cloud secret injection ─────────────────────────────────────────
for _k in ("NEO4J_URI", "NEO4J_USERNAME", "NEO4J_PASSWORD"):
    try:
        if _k in st.secrets and not os.environ.get(_k):
            os.environ[_k] = st.secrets[_k]
    except Exception:
        pass

if render_stub_gate(module="Clinical Strategy Engine"):
    st.stop()

_GENE = get_active_symbol()
_PREFIX = _GENE.lower()
_TARGET = get_target(_GENE)
_GENE_NAME = str(_TARGET.get("name") or _GENE)
_strat = strategy_context(_GENE)

# ── Theme ─────────────────────────────────────────────────────────────────────
_BG     = "#FFFFFF"
_LINE   = "#E2E8F0"
_INDIGO = "#2563EB"
_TEAL   = "#2DD4BF"
_AMBER  = "#FBBF24"
_GREEN  = "#34D399"
_ROSE   = "#F472B6"
_ORANGE = "#FB923C"
_RED    = "#F87171"
_SLATE  = "#4E637A"
_TEXT   = "#64748B"
_LIGHT  = "#1E293B"

st.markdown("""
<style>
  .block-container { padding-top: 1.5rem; }
  .phase-pill {
      display: inline-block; padding: .22rem .65rem; border-radius: 99px;
      font-size: .78rem; font-weight: 700; margin-right: .3rem;
  }
  .pill-pre { background: #7c3aed22; color: #a78bfa; border: 1px solid #7c3aed; }
  .pill-p1  { background: #0369a122; color: #38bdf8; border: 1px solid #0369a1; }
  .pill-p2  { background: #05653222; color: #34d399; border: 1px solid #056532; }
  .pill-p3  { background: #92400e22; color: #fbbf24; border: 1px solid #92400e; }
  .pill-app { background: #14532d22; color: #4ade80; border: 1px solid #14532d; }
</style>
""", unsafe_allow_html=True)


# ── AuraDB driver ─────────────────────────────────────────────────────────────
@st.cache_resource(ttl=300)
def get_driver():
    from neo4j import GraphDatabase
    uri = os.environ.get("NEO4J_URI")
    user = os.environ.get("NEO4J_USERNAME", "neo4j")
    pw = os.environ.get("NEO4J_PASSWORD")
    if not uri or not pw:
        return None
    try:
        driver = GraphDatabase.driver(uri, auth=(user, pw))
        driver.verify_connectivity()
        return driver
    except Exception:
        return None


@st.cache_data(ttl=3600)
def load_kg_stats(symbol: str) -> dict:
    driver = get_driver()
    if not driver:
        return {}
    stats = {}
    try:
        with driver.session() as s:
            r = s.run(
                """
                MATCH (t:ClinicalTrial)
                WHERE t.target = $sym OR toLower(t.title) CONTAINS toLower($sym)
                RETURN t.nct_id AS nct, t.title AS title, t.phase AS phase,
                       t.status AS status, t.enrollment_count AS enrolled,
                       t.start_date AS start, t.primary_completion_date AS completion,
                       t.sponsor AS sponsor
                ORDER BY t.phase
                LIMIT 50
                """,
                sym=symbol,
            )
            stats["trials"] = [dict(rec) for rec in r]
            r3 = s.run("MATCH (d:Disease) RETURN COUNT(d) AS n")
            stats["disease_n"] = r3.single()["n"]
            r4 = s.run("MATCH (g:Gene)-[:INTERACTS_WITH]->() RETURN COUNT(DISTINCT g) AS n")
            stats["ppi_genes"] = r4.single()["n"]
    except Exception:
        pass
    return stats


@st.cache_data
def load_survival(symbol: str):
    for fp in [
        Path(f"data/processed/{symbol.lower()}_survival_results.csv"),
        Path(__file__).resolve().parents[2] / f"data/processed/{symbol.lower()}_survival_results.csv",
    ]:
        if fp.exists():
            return pd.read_csv(fp)
    return pd.DataFrame()


@st.cache_data
def load_expression(symbol: str):
    for fp in [
        Path(f"data/processed/{symbol.lower()}_by_cancer.csv"),
        Path(__file__).resolve().parents[2] / f"data/processed/{symbol.lower()}_by_cancer.csv",
    ]:
        if fp.exists():
            return pd.read_csv(fp)
    return pd.DataFrame()


def _median_col(df: pd.DataFrame, symbol: str) -> str | None:
    pref = symbol.lower()
    for c in ("gene_median", f"{pref}_median", f"{pref}_mean", "median_tpm", "mean_tpm"):
        if c in df.columns:
            return c
    return None


@st.cache_data
def load_chembl_summary(symbol: str) -> pd.DataFrame:
    raw = Path(__file__).resolve().parents[2] / "data" / "raw" / "apis" / f"chembl_{symbol.lower()}.json"
    if not raw.exists():
        return pd.DataFrame()
    try:
        payload = json.loads(raw.read_text(encoding="utf-8"))
    except Exception:
        return pd.DataFrame()
    drugs = payload.get("drugs") or []
    rows = []
    for d in drugs[:20]:
        phase = int(d.get("max_phase") or 0)
        rows.append({
            "name": d.get("name") or d.get("chembl_id") or "—",
            "type": d.get("molecule_type") or d.get("drug_type") or "—",
            "phase": phase,
            "mechanism": (d.get("mechanism") or "—")[:120],
            "chembl_id": d.get("chembl_id") or "—",
        })
    return pd.DataFrame(rows)


def _trials_from_summary(symbol: str) -> list[dict]:
    df = load_trials_summary(symbol)
    if df.empty:
        return []
    rows = []
    for _, r in df.iterrows():
        rows.append({
            "nct": r.get("nct_id") or r.get("nct") or "—",
            "title": r.get("title") or "",
            "phase": str(r.get("phase") or "NA").upper().replace(" ", ""),
            "status": str(r.get("status") or "—").upper(),
            "enrolled": r.get("enrollment") or r.get("enrolled") or None,
            "start": r.get("start_date") or r.get("start") or "—",
            "completion": r.get("completion_date") or r.get("completion") or "—",
            "sponsor": r.get("sponsor") or "—",
        })
    return rows


surv_df  = load_survival(_GENE)
expr_df  = load_expression(_GENE)
kg_stats = load_kg_stats(_GENE)
chembl_df = load_chembl_summary(_GENE)

# Prefer processed trial CSV, then KG, never a foreign-gene fallback
_trials = kg_stats.get("trials") or []
if not _trials:
    _trials = _trials_from_summary(_GENE)

n_disease = kg_stats.get("disease_n")
n_ppi     = kg_stats.get("ppi_genes")

# ── Page hero ──────────────────────────────────────────────────────────────────
page_header(
    icon="🔬",
    module_name="Clinical Strategy Engine",
    purpose=strategy_purpose(_GENE),
    kpi_chips=[
        ("Stages", "5"),
        (f"{_GENE} Trials", str(len(_trials)) if _trials else "—"),
        ("Focus", _strat["indication"][:28]),
        ("Horizon", _strat["approval_target"][:20]),
    ],
    source_badges=["TCGA", "ClinicalTrials", "HPA", "ChEMBL"],
)

# ── Pipeline progress banner ──────────────────────────────────────────────────
st.markdown(f"""
<div class="ob-pipeline-step" style="border-radius:10px;
            padding:1rem 1.5rem;margin:.5rem 0 1rem 0;'>
  <div style='display:flex;align-items:center;gap:1.2rem;flex-wrap:wrap;'>
    <span style='color:#64748B;font-size:.82rem;font-weight:600;'>DEVELOPMENT STAGE →</span>
    <span class='phase-pill pill-pre'>PRECLINICAL</span>
    <span style='color:#4E637A'>──</span>
    <span class='phase-pill pill-p1'>PHASE I</span>
    <span style='color:#4E637A'>──</span>
    <span class='phase-pill pill-p2'>PHASE II</span>
    <span style='color:#4E637A'>──</span>
    <span class='phase-pill pill-p3'>PHASE III</span>
    <span style='color:#4E637A'>──</span>
    <span class='phase-pill pill-app'>APPROVAL · {_strat['approval_target'][:24]}</span>
  </div>
</div>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
# STAGE 1 — TARGET BIOLOGY
# ═══════════════════════════════════════════════════════════════════════════════
with st.container(border=True):
    st.markdown(f"### 🧬 {strategy_stage1_title(_GENE)}")
    st.caption(
        f"Molecular rationale for **{_GENE}** ({_GENE_NAME}) — "
        f"pan-cancer expression, survival, and tissue atlas evidence · "
        f"focus: {_strat['indication']}"
    )

    col_t1, col_t2 = st.columns([3, 2])
    _med = _median_col(expr_df, _GENE) if not expr_df.empty else None

    with col_t1:
        if _med and "cancer_type" in expr_df.columns:
            top_expr = expr_df.nlargest(12, _med).copy()
            fig_expr = go.Figure(go.Bar(
                x=top_expr["cancer_type"],
                y=top_expr[_med],
                marker=dict(color=_INDIGO, line=dict(color="#D5DEE8", width=0.5)),
                text=[f"{v:.1f}" for v in top_expr[_med]],
                textposition="outside",
                textfont=dict(size=10, color=_LIGHT),
                hovertemplate=f"<b>%{{x}}</b><br>{_GENE} median: %{{y:.1f}} log₂ TPM<extra></extra>",
            ))
            apply_plotly_layout(fig_expr,
                title=dict(
                    text=f"Top 12 Cancers by Median {_GENE} mRNA (log₂ TPM)",
                    font=dict(color=_LIGHT, size=13),
                ),
                xaxis=dict(title=None, color=_LIGHT, showgrid=False),
                yaxis=dict(title="log₂ TPM", gridcolor=_LINE, color=_TEXT),
                height=300,
                margin=dict(l=10, r=10, t=40, b=40),
            )
            st.plotly_chart(fig_expr, use_container_width=True)
        else:
            st.warning(
                f"No expression slice for **{_GENE}** "
                f"(`data/processed/{_PREFIX}_by_cancer.csv`)."
            )
            st.page_link(
                "pages/7_kg_query_explorer.py",
                label="Open KG Query Explorer →",
            )

    with col_t2:
        st.markdown("**Target Validation Evidence**")
        v1, v2 = st.columns(2)
        v1.metric(
            "Disease Associations",
            f"{n_disease:,}" if n_disease is not None else "—",
            "Open Targets / KG",
        )
        v2.metric("PPI Partners", n_ppi if n_ppi is not None else "—", "STRING / KG")
        v3, v4 = st.columns(2)
        v3.metric("Active Target", _GENE, _GENE_NAME[:18])
        v4.metric("Modality", _strat["modality"][:18], "strategy context")

        st.markdown("**Molecular Rationale**")
        st.markdown(f"""
- **{_GENE}** ({_GENE_NAME}) — active research target in this platform
- Indication focus: **{_strat['indication']}**
- Preferred modality frame: **{_strat['modality']}**
- Trial watchlist: **{_strat['trial_focus']}**
- Horizon: **{_strat['approval_target']}**
        """)

    if _med:
        st.success(
            f"**Stage 1 verdict:** {_GENE} expression ranks are available across TCGA cancers. "
            f"Use the Survival Outcomes module for Cox HRs and the Drug Pipeline for "
            f"{_strat['modality']} competitive context. Stage 1 closed for {_GENE}."
        )
    else:
        st.info(
            f"**Stage 1:** Expression CSV missing for {_GENE} — biology narrative is incomplete "
            "until the atlas slice is generated."
        )

st.markdown(
    "<div style='text-align:center;color:#FB923C;font-size:1.5rem;padding:.3rem 0;'>▼</div>",
    unsafe_allow_html=True,
)

# ═══════════════════════════════════════════════════════════════════════════════
# STAGE 2 — DRUG DESIGN
# ═══════════════════════════════════════════════════════════════════════════════
with st.container(border=True):
    st.markdown(f"### ⚛️ Stage 2 — Drug Design: {_strat['modality']}")
    st.caption(
        f"Modality framing for **{_GENE}** — open-data agents from ChEMBL when available"
    )

    col_d1, col_d2 = st.columns([2, 3])

    with col_d1:
        with st.container(border=True):
            st.markdown("**Strategy context**")
            st.markdown(f"""
| | |
|---|---|
| **Gene** | {_GENE} ({_GENE_NAME}) |
| **Indication** | {_strat['indication']} |
| **Modality** | {_strat['modality']} |
| **Trial focus** | {_strat['trial_focus']} |
| **Horizon** | {_strat['approval_target']} |
            """)

    with col_d2:
        with st.container(border=True):
            st.markdown(f"**{_GENE} agents (ChEMBL cache)**")
            if chembl_df.empty:
                st.info(
                    f"No ChEMBL cache at `data/raw/apis/chembl_{_PREFIX}.json`. "
                    "See Drug Pipeline Explorer for curated landscape when available."
                )
                st.page_link(
                    "pages/11_drug_pipeline.py",
                    label="Open Drug Pipeline Explorer →",
                )
            else:
                show = chembl_df.rename(columns={
                    "name": "Name", "type": "Type", "phase": "Max phase",
                    "mechanism": "Mechanism", "chembl_id": "ChEMBL",
                })
                research_table(show, use_container_width=True, hide_index=True, height=260)
                st.caption(f"{len(chembl_df)} agents from ChEMBL open-data cache for {_GENE}.")

    st.info(
        f"**Stage 2 verdict:** Programme framing for {_GENE} centres on "
        f"**{_strat['modality']}** in {_strat['indication']}. "
        "Competitive agents come from ChEMBL / ClinicalTrials slices — not a hardcoded "
        "foreign-gene pipeline. Stage 2 closed."
    )

st.markdown(
    "<div style='text-align:center;color:#FB923C;font-size:1.5rem;padding:.3rem 0;'>▼</div>",
    unsafe_allow_html=True,
)

# ═══════════════════════════════════════════════════════════════════════════════
# STAGE 3 — PATIENT SELECTION
# ═══════════════════════════════════════════════════════════════════════════════
with st.container(border=True):
    st.markdown(f"### 👥 Stage 3 — Patient Selection: Who Qualifies for {_GENE}?")
    st.caption(
        f"Biomarker-driven eligibility framing — {_GENE}-High vs Low · "
        f"{_strat['indication']}"
    )

    col_p1, col_p2 = st.columns([2, 3])

    with col_p1:
        st.markdown("**Proposed Eligibility Criteria (template)**")
        with st.container(border=True):
            st.markdown(f"""
**Inclusion:**
- Histologically confirmed disease in {_strat['indication']}
- {_GENE} IHC / mRNA above programme threshold (e.g. median or 75th pct)
- Adequate organ function; ECOG 0–2
- Prior standard-of-care per indication

**Exclusion:**
- Active CNS disease (unless indication-specific)
- Organ function below modality-specific dosimetry floor
- Active uncontrolled autoimmune disease
            """)

        m_a, m_b = st.columns(2)
        m_a.metric("Target", _GENE, "active symbol")
        m_b.metric("Selection", f"{_GENE}-High", "biomarker gate")

    with col_p2:
        st.markdown(f"**Patient Selection Funnel — schematic per 1,000 screened ({_GENE})**")
        # ponytail: illustrative funnel ratios; replace with patient_groups.csv when sliced
        funnel_labels = [
            "All screened",
            f"{_GENE}-High (post-assay)",
            "Indication-fit",
            "Prior therapy eligible",
            "Organ function eligible",
            "Trial eligible (est.)",
        ]
        funnel_values = [1000, 400, 220, 180, 150, 120]

        fig_funnel = go.Figure(go.Funnel(
            y=funnel_labels,
            x=funnel_values,
            textinfo="value+percent initial",
            marker=dict(
                color=[_ORANGE, "#FB923C", "#FCA5A5", _INDIGO, _TEAL, _GREEN],
                line=dict(color="#D5DEE8", width=1),
            ),
            connector=dict(line=dict(color=_LINE, width=2)),
            textfont=dict(color=_LIGHT, size=11),
        ))
        apply_plotly_layout(fig_funnel,
            height=340,
            margin=dict(l=10, r=10, t=10, b=20),
            yaxis=dict(color=_LIGHT),
        )
        st.plotly_chart(fig_funnel, use_container_width=True)
        st.caption(
            f"Schematic only — calibrate with `{_PREFIX}_patient_groups.csv` / eligibility module "
            f"when available for {_GENE}."
        )

    st.success(
        f"**Stage 3 verdict:** Enrolment for a {_GENE}-targeted programme hinges on a "
        f"{_GENE}-High biomarker gate within {_strat['indication']}. "
        "Refine thresholds in Patient Eligibility. Stage 3 closed."
    )

st.markdown(
    "<div style='text-align:center;color:#FB923C;font-size:1.5rem;padding:.3rem 0;'>▼</div>",
    unsafe_allow_html=True,
)

# ═══════════════════════════════════════════════════════════════════════════════
# STAGE 4 — CLINICAL EVIDENCE
# ═══════════════════════════════════════════════════════════════════════════════
with st.container(border=True):
    st.markdown(f"### 🧪 Stage 4 — Clinical Evidence: {_GENE} Trial Landscape")
    st.caption(
        f"{_strat['trial_focus']} — ClinicalTrials.gov / KG slice for **{_GENE}**"
    )

    PHASE_LABEL = {
        "PHASE1": "Phase I", "PHASE1/PHASE2": "Phase I/II", "PHASE1PHASE2": "Phase I/II",
        "PHASE2": "Phase II", "PHASE3": "Phase III", "NA": "Observational",
        "EARLY_PHASE1": "Early Phase I",
    }
    STATUS_ICON = {
        "RECRUITING": "🟢 Recruiting",
        "ACTIVE_NOT_RECRUITING": "🔵 Active",
        "COMPLETED": "✅ Completed",
        "TERMINATED": "🔴 Terminated",
        "UNKNOWN": "⚪ Unknown",
    }
    PHASE_ORDER = {
        "PHASE1": 1, "EARLY_PHASE1": 1, "PHASE1/PHASE2": 2, "PHASE1PHASE2": 2,
        "PHASE2": 3, "PHASE3": 4, "NA": 0,
    }

    if not _trials:
        st.warning(
            f"No trial slice for **{_GENE}**. "
            f"Expected KG hits or `data/processed/{_PREFIX}_trials_summary.csv`."
        )
        st.page_link(
            "pages/7_kg_query_explorer.py",
            label="Open KG Query Explorer →",
        )
        st.page_link(
            "pages/11_drug_pipeline.py",
            label="Open Drug Pipeline Explorer →",
        )
    else:
        trial_df = pd.DataFrame(_trials)
        if "phase" not in trial_df.columns:
            trial_df["phase"] = "NA"
        trial_df["phase_sort"] = trial_df["phase"].map(
            lambda x: PHASE_ORDER.get(str(x or "NA").upper().replace(" ", ""), 0)
        )
        trial_df = trial_df.sort_values("phase_sort")

        col_tri1, col_tri2 = st.columns([3, 2])

        with col_tri1:
            cols_keep = [c for c in ["nct", "phase", "status", "enrolled", "start", "completion"]
                         if c in trial_df.columns]
            display_trial = trial_df[cols_keep].copy()
            rename = {
                "nct": "NCT ID", "phase": "Phase", "status": "Status",
                "enrolled": "Enrolled", "start": "Start", "completion": "Completion",
            }
            display_trial = display_trial.rename(columns=rename)
            if "Phase" in display_trial.columns:
                display_trial["Phase"] = display_trial["Phase"].map(
                    lambda x: PHASE_LABEL.get(str(x or "NA").upper().replace(" ", ""), x)
                )
            if "Status" in display_trial.columns:
                display_trial["Status"] = display_trial["Status"].map(
                    lambda s: STATUS_ICON.get(str(s or "").upper(), s or "—")
                )
            research_table(display_trial, hide_index=True, use_container_width=True)

            if "enrolled" in trial_df.columns:
                total_enrolled = pd.to_numeric(trial_df["enrolled"], errors="coerce").dropna().sum()
                if total_enrolled:
                    st.metric("Total Patients Enrolled Across Trials", f"{int(total_enrolled):,}")

        with col_tri2:
            phase_counts = trial_df["phase"].fillna("NA").astype(str).value_counts().reset_index()
            phase_counts.columns = ["phase", "count"]
            phase_counts["label"] = phase_counts["phase"].map(
                lambda x: PHASE_LABEL.get(str(x).upper().replace(" ", ""), x)
            )

            fig_phase = go.Figure(go.Pie(
                labels=phase_counts["label"],
                values=phase_counts["count"],
                hole=0.55,
                marker=dict(
                    colors=[_INDIGO, _TEAL, _GREEN, _AMBER, _SLATE],
                    line=dict(color="#D5DEE8", width=2),
                ),
                textinfo="label+value",
                textfont=dict(color=_LIGHT, size=11),
            ))
            apply_plotly_layout(fig_phase,
                height=290,
                margin=dict(l=10, r=10, t=10, b=10),
                showlegend=False,
            )
            st.plotly_chart(fig_phase, use_container_width=True)

        # Highlight first completed / recruiting row if present — gene-agnostic
        done = trial_df[trial_df["status"].astype(str).str.upper() == "COMPLETED"]
        if not done.empty:
            row0 = done.iloc[0]
            st.markdown(
                f"**Milestone:** `{row0.get('nct', '—')}` completed "
                f"({row0.get('phase', '—')}) — {_GENE}-linked programme precedent."
            )

    st.info(
        f"**Stage 4 verdict:** {len(_trials)} indexed trial(s) for {_GENE}. "
        f"Watchlist: {_strat['trial_focus']}. Stage 4 closed."
    )

st.markdown(
    "<div style='text-align:center;color:#FB923C;font-size:1.5rem;padding:.3rem 0;'>▼</div>",
    unsafe_allow_html=True,
)

# ═══════════════════════════════════════════════════════════════════════════════
# STAGE 5 — EXPECTED OUTCOME
# ═══════════════════════════════════════════════════════════════════════════════
with st.container(border=True):
    st.markdown(f"### 📈 Stage 5 — Expected Outcome: {_GENE} Efficacy Projection")
    st.caption(
        f"Survival analysis + mechanistic rationale for {_GENE}-High patient benefit"
    )

    col_o1, col_o2 = st.columns([3, 2])

    with col_o1:
        if surv_df.empty or "hazard_ratio" not in surv_df.columns:
            st.warning(
                f"TCGA survival slice is missing for **{_GENE}**. "
                f"Expected `data/processed/{_PREFIX}_survival_results.csv`."
            )
            st.page_link(
                "pages/3_survival_outcomes.py",
                label="Open Survival Outcomes →",
            )
            st.page_link(
                "pages/7_kg_query_explorer.py",
                label="Open KG Query Explorer →",
            )
        else:
            use_surv = surv_df.copy()
            if "endpoint" in use_surv.columns:
                use_surv = use_surv[use_surv["endpoint"] == "OS"]

            forest_df = use_surv[
                use_surv["hazard_ratio"].notna() & (use_surv["hazard_ratio"] > 0)
            ].copy()
            forest_df = forest_df.nlargest(10, "hazard_ratio").sort_values("hazard_ratio")

            p_col = "log_rank_p" if "log_rank_p" in forest_df.columns else "p_value"

            fig_forest = go.Figure()
            for _, row in forest_df.iterrows():
                hr  = row["hazard_ratio"]
                ci_lo = row.get("hr_lower_95", hr * 0.75)
                ci_hi = row.get("hr_upper_95", hr * 1.30)
                ct    = row["cancer_type"]
                p_val = float(row.get(p_col, 0.05) or 0.05)
                color = _RED if (p_val < 0.05 and hr >= 1.0) else (
                    _GREEN if (p_val < 0.05 and hr < 1.0) else _SLATE
                )

                fig_forest.add_trace(go.Scatter(
                    x=[ci_lo, hr, ci_hi],
                    y=[ct, ct, ct],
                    mode="lines+markers",
                    line=dict(color=color, width=2),
                    marker=dict(
                        symbol=["line-ew", "diamond", "line-ew"],
                        size=[8, 10, 8],
                        color=color,
                    ),
                    showlegend=False,
                    hovertemplate=(
                        f"<b>{ct}</b><br>HR={hr:.2f} "
                        f"(95% CI {ci_lo:.2f}–{ci_hi:.2f})<extra></extra>"
                    ),
                ))

            fig_forest.add_vline(
                x=1.0,
                line=dict(color=_SLATE, dash="dash", width=1.5),
                annotation_text="HR=1.0 (no effect)",
                annotation_position="top right",
                annotation_font=dict(color=_TEXT, size=10),
            )
            apply_plotly_layout(fig_forest,
                title=dict(
                    text=f"OS Hazard Ratio — {_GENE}-High vs {_GENE}-Low (top 10)",
                    font=dict(color=_LIGHT, size=13),
                ),
                xaxis=dict(
                    title=f"Hazard Ratio (>1 = worse OS for {_GENE}-High)",
                    gridcolor=_LINE, color=_TEXT,
                ),
                yaxis=dict(title=None, color=_LIGHT),
                height=380,
                margin=dict(l=10, r=30, t=40, b=40),
            )
            st.plotly_chart(fig_forest, use_container_width=True)
            st.caption(
                f"{_GENE}-High associations with worse OS support a therapeutic hypothesis "
                f"in those cancers; inverse HRs argue against {_GENE} as a primary target there."
            )

    with col_o2:
        st.markdown("**Efficacy Projection**")
        with st.container(border=True):
            if not surv_df.empty and "hazard_ratio" in surv_df.columns:
                os_rows = surv_df.copy()
                if "endpoint" in os_rows.columns:
                    os_rows = os_rows[os_rows["endpoint"] == "OS"]
                top = (
                    os_rows.nsmallest(1, "p_value")
                    if "p_value" in os_rows.columns and os_rows["p_value"].notna().any()
                    else os_rows.head(1)
                )
                if not top.empty and pd.notna(top.iloc[0].get("hazard_ratio")):
                    r = top.iloc[0]
                    hr = float(r["hazard_ratio"])
                    pv = r.get("p_value")
                    pv_txt = f"{pv:.4f}" if pd.notna(pv) else "—"
                    direction = "worse OS for High" if hr >= 1 else "better OS for High"
                    st.markdown(
                        f"**Strongest TCGA OS signal ({_GENE}):**\n"
                        f"- **{r['cancer_type']}** — HR **{hr:.2f}**\n"
                        f"- p = {pv_txt}\n"
                        f"- Direction: {direction}"
                    )
                else:
                    st.info(f"No OS Cox rows for {_GENE}.")
            else:
                st.info(f"Survival CSV missing for {_GENE} — no HR projection.")

        st.markdown("**Phase II Endpoints (proposed template)**")
        ep_df = pd.DataFrame([
            {"Endpoint": "ORR / biomarker response", "Timepoint": "12 weeks", "Target": "≥ programme bar"},
            {"Endpoint": "PFS / rPFS", "Timepoint": "Continuous", "Target": "> SoC"},
            {"Endpoint": "OS", "Timepoint": "Secondary", "Target": "HR < 0.80"},
            {"Endpoint": "Safety (DLT)", "Timepoint": "Cycle 1", "Target": "Modality-specific"},
        ])
        research_table(ep_df, use_container_width=True, hide_index=True)

    if not surv_df.empty:
        st.success(
            f"**Stage 5 verdict:** {_GENE} Cox HRs from TCGA define where {_GENE}-High "
            f"carries a measurable survival penalty (or protective signal). "
            f"Anchor Phase II design to {_strat['indication']}. Stage 5 closed."
        )
    else:
        st.info(
            f"**Stage 5:** Survival slice missing for {_GENE} — outcome projection deferred."
        )

# ═══════════════════════════════════════════════════════════════════════════════
# STRATEGY SUMMARY TABLE
# ═══════════════════════════════════════════════════════════════════════════════
st.markdown("---")
st.markdown(f"### 🗺️ End-to-End Development Engine Summary — {_GENE}")

n_trial_txt = str(len(_trials)) if _trials else "—"
strategy_df = pd.DataFrame([
    {
        "Stage": "🧬 Preclinical",
        "Key Evidence": (
            f"{_GENE} expression atlas + PPI/disease KG context · modality {_strat['modality']}"
        ),
        "Platform Pages": "1, 4, 6, 10",
        "Status": "Data-driven" if _med else "Slice pending",
        "Confidence": "High" if _med else "Low",
    },
    {
        "Stage": "⚗️ Phase I Safety",
        "Key Evidence": f"HPA / dosimetry for {_GENE}-targeted {_strat['modality']}",
        "Platform Pages": "12",
        "Status": "Module-ready",
        "Confidence": "Medium",
    },
    {
        "Stage": "📊 Phase II PoC",
        "Key Evidence": (
            f"TCGA Cox for {_GENE} · eligibility funnel · {_strat['indication']}"
        ),
        "Platform Pages": "2, 3, 8",
        "Status": "Evidence-strong" if not surv_df.empty else "Survival pending",
        "Confidence": "Medium-High" if not surv_df.empty else "Low",
    },
    {
        "Stage": "🌍 Phase III",
        "Key Evidence": f"{n_trial_txt} indexed trials · {_strat['trial_focus']}",
        "Platform Pages": "9, 11",
        "Status": "Monitoring pipeline",
        "Confidence": "Medium" if _trials else "Low",
    },
    {
        "Stage": "✅ Approval",
        "Key Evidence": (
            f"{_GENE} companion diagnostic + label scope: {_strat['indication']} · "
            f"horizon {_strat['approval_target']}"
        ),
        "Platform Pages": "5, 7, 13",
        "Status": _strat["approval_target"][:24],
        "Confidence": "Contingent on Ph II",
    },
])
research_table(strategy_df, hide_index=True, use_container_width=True)

st.info(
    f"**Platform synthesis:** The Clinical Strategy Engine assembles analytical modules into a "
    f"**{_GENE}**-centric programme roadmap. Numbers trace to gene-keyed processed files "
    "(TCGA, ClinicalTrials, ChEMBL) — not a privileged default target."
)

st.markdown("---")
st.caption(
    f"Active target: {_GENE} ({_GENE_NAME}). "
    "Data sources: TCGA, HPA, ClinicalTrials.gov, ChEMBL, Open Targets / STRING via KG. "
    "Research use only. Not for clinical decision-making."
)
