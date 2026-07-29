"""Page 1 — CD46 Expression Atlas: pan-cancer mRNA, protein, safety, and CRISPR evidence."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from components.targets import get_active_symbol, render_stub_gate
from components.theme import CHART_HIGHLIGHT, CHART_MUTED, plotly_layout
from components.ui_kit import export_research_pack, filter_bar, page_header, section_tabs

if render_stub_gate(module="Expression Atlas"):
    st.stop()

_GENE = get_active_symbol()
_PREFIX = _GENE.lower()

# Chart colors (Clinical Slate)
_INDIGO = CHART_HIGHLIGHT
_SLATE = CHART_MUTED
_TEAL = "#0D9488"
_AMBER = "#D97706"
_GREEN = "#059669"
_ROSE = "#E11D48"
_TEXT = "#64748B"
_LINE = "#E2E8F0"

_PLOTLY_LAYOUT = plotly_layout()

# ---------------------------------------------------------------------------
# Data loaders
# ---------------------------------------------------------------------------
@st.cache_data
def load_by_cancer(symbol: str):
    p = Path(f"data/processed/{symbol.lower()}_by_cancer.csv")
    if not p.exists():
        return None
    df = pd.read_csv(p)
    # Normalize median column for charts
    if "gene_median" in df.columns:
        df["median_expr"] = df["gene_median"]
    elif f"{symbol.lower()}_median" in df.columns:
        df["median_expr"] = df[f"{symbol.lower()}_median"]
    elif "cd46_median" in df.columns:
        df["median_expr"] = df["cd46_median"]
    return df

@st.cache_data
def load_hpa(symbol: str):
    for name in (
        f"hpa_{symbol.lower()}_protein.csv",
        f"hpa_{symbol.lower()}_protein_intensity.csv",
        f"hpa_{symbol.lower()}_rna_tissue.csv",
    ):
        p = Path("data/processed") / name
        if p.exists():
            return pd.read_csv(p)
    return None

@st.cache_data
def load_priority():
    p = Path("data/processed/priority_score.csv")
    return pd.read_csv(p) if p.exists() else None

@st.cache_data
def load_gtex(symbol: str):
    p = Path(f"data/processed/gtex_{symbol.lower()}_normal.csv")
    return pd.read_csv(p) if p.exists() else None

@st.cache_data
def load_depmap(symbol: str):
    p = Path(f"data/processed/depmap_{symbol.lower()}_essentiality.csv")
    if not p.exists():
        return None
    df = pd.read_csv(p)
    # Normalize legacy CD46 column names ↔ gene-generic Step 3c names
    if "crispr_score" in df.columns and "cd46_crispr_score" not in df.columns:
        df["cd46_crispr_score"] = df["crispr_score"]
    if "is_dependency" in df.columns and "cd46_is_dependency" not in df.columns:
        df["cd46_is_dependency"] = df["is_dependency"]
    if "cd46_crispr_score" in df.columns and "crispr_score" not in df.columns:
        df["crispr_score"] = df["cd46_crispr_score"]
    if "cd46_is_dependency" in df.columns and "is_dependency" not in df.columns:
        df["is_dependency"] = df["cd46_is_dependency"]
    return df

expr_df    = load_by_cancer(_GENE)
hpa_df     = load_hpa(_GENE)
priority_df = load_priority() if _GENE == "CD46" else None
gtex_df    = load_gtex(_GENE)
depmap_df  = load_depmap(_GENE)

# ---------------------------------------------------------------------------
# Derived KPI values
# ---------------------------------------------------------------------------
n_cancers  = len(expr_df) if expr_df is not None else 25
top_cancer = (
    expr_df.sort_values("median_expr", ascending=False).iloc[0]["cancer_type"]
    if expr_df is not None and "median_expr" in expr_df.columns else "—"
)
n_lines  = len(depmap_df) if depmap_df is not None else 0
_dep_col = "cd46_is_dependency" if depmap_df is not None and "cd46_is_dependency" in depmap_df.columns else "is_dependency"
pct_safe = (
    (1 - depmap_df[_dep_col].mean()) * 100
    if depmap_df is not None and _dep_col in depmap_df.columns else None
)

# ---------------------------------------------------------------------------
# Page hero
# ---------------------------------------------------------------------------
page_header(
        icon="📊",
        module_name="Expression Atlas",
        purpose=(
            f"Pan-cancer **{_GENE}** mRNA (TCGA/Xena)"
            + (" · protein · GTEx · DepMap" if (hpa_df is not None or gtex_df is not None or depmap_df is not None) else "")
        ),
        kpi_chips=[
            ("Active Target", _GENE),
            ("Cancers Profiled", str(n_cancers)),
            ("Top by mRNA", str(top_cancer)),
            ("Not a Dependency", f"{pct_safe:.1f}%" if pct_safe is not None else "n/a"),
        ],
        source_badges=["TCGA", "HPA", "GTEx", "DepMap"],
    )

# Entity card (Sprint 7) — click for AlphaFold / UniProt
try:
    from components.tooltip_generator import render_entity_popover
    tc1, tc2 = st.columns([1, 3])
    with tc1:
        render_entity_popover(_GENE, label=f"🧬 {_GENE} structure")
    with tc2:
        st.caption("Click the gene chip for UniProt / AlphaFold / HPA links (tooltip mapping file).")
except Exception:
    pass

# ---------------------------------------------------------------------------
# Tabs (shadcn pilot)
# ---------------------------------------------------------------------------
_TAB_LABELS = [
    "Pan-Cancer mRNA",
    "Protein & Safety",
    "Functional Screen",
    "Priority & Data",
]
_active_tab = section_tabs(_TAB_LABELS, key="expr_atlas_tabs")

# ── Tab 1 : Pan-Cancer mRNA ─────────────────────────────────────────────────
if _active_tab == _TAB_LABELS[0]:
    st.markdown(f"#### {_GENE} mRNA Expression — TCGA Pan-Cancer Survey")
    st.caption(
        "TCGA RNA-seq via UCSC Xena · sorted by median expression · "
        f"{expr_df['n_samples'].sum():,} patients across {n_cancers} cancer types"
        if expr_df is not None else "TCGA RNA-seq via UCSC Xena"
    )

    if expr_df is None or "median_expr" not in expr_df.columns:
        st.warning(f"⚠️ No by-cancer CSV for {_GENE} — run `python scripts/load_target_slice.py --symbol {_GENE}`")
    else:
        with filter_bar("Chart options"):
            ctrl_col, info_col = st.columns([3, 1])
            with ctrl_col:
                sort_by = st.radio(
                    "Sort by",
                    ["Median expression ↓", "Cancer type A–Z"],
                    horizontal=True,
                    key="t1_sort",
                )
            with info_col:
                st.caption(
                    f"Showing **{n_cancers} cancers**  \n"
                    f"Highest: **{top_cancer}**  \n"
                    f"Top quartile = indigo"
                )

        df_plot = (
            expr_df.sort_values("median_expr", ascending=True)
            if sort_by == "Median expression ↓"
            else expr_df.sort_values("cancer_type", ascending=False)
        )
        q75 = df_plot["median_expr"].quantile(0.75)
        bar_colors = [_INDIGO if v >= q75 else _SLATE for v in df_plot["median_expr"]]

        fig1 = go.Figure()
        fig1.add_trace(go.Bar(
            x=df_plot["median_expr"],
            y=df_plot["cancer_type"],
            orientation="h",
            marker_color=bar_colors,
            hovertemplate=(
                "<b>%{y}</b><br>"
                "Median: %{x:.3f}<br>"
                "N = %{customdata[0]:,} samples<extra></extra>"
            ),
            customdata=df_plot[["n_samples"]].values,
        ))
        fig1.update_layout(
            **_PLOTLY_LAYOUT,
            height=520,
            margin=dict(l=10, r=20, t=20, b=40),
            xaxis=dict(title=f"{_GENE} Median Expression", gridcolor=_LINE, color=_TEXT, zeroline=False),
            yaxis=dict(color=_LIGHT, tickfont=dict(size=11)),
        )
        st.plotly_chart(fig1, use_container_width=True)

        top3 = df_plot.nlargest(3, "median_expr")["cancer_type"].tolist()
        st.info(
            f"**Top 3 by median expression:** {', '.join(top3)}  \n"
            f"log₂(TPM+1) for **{_GENE}**. Indigo bars = top quartile."
        )

# ── Tab 2 : Protein & Safety ────────────────────────────────────────────────
elif _active_tab == _TAB_LABELS[1]:
    if hpa_df is None and gtex_df is None:
        st.info(
            f"No HPA/GTEx processed slice for **{_GENE}** yet. "
            f"Pan-Cancer mRNA tab and KG Query Explorer remain available."
        )
    st.caption(
        "Human Protein Atlas protein/RNA intensity · "
        "GTEx v8 normal-tissue mRNA (when gene slice exists)"
    )

    col_hpa, col_gtex = st.columns(2)

    with col_hpa:
        st.markdown("##### 🔬 HPA IHC — Tumour vs Normal")
        if hpa_df is None:
            st.warning("HPA data not available.")
            st.markdown(
                "**Known from literature:**\n"
                "- Prostate tumour → H-score 300/300\n"
                "- Prostate normal → ~200/300\n"
                "- Kidney normal → 300/300 ⚠️\n"
                "- Liver normal → ~200/300\n"
                "- Breast normal → ~100/300"
            )
        else:
            if "h_score_approx" in hpa_df.columns and "type" in hpa_df.columns:
                tumor_d  = hpa_df[hpa_df["type"] == "tumor"]
                normal_d = hpa_df[hpa_df["type"] == "normal"]
                fig_hpa = go.Figure()
                if not tumor_d.empty:
                    fig_hpa.add_trace(go.Bar(
                        name="Tumour",
                        x=tumor_d["tissue"],
                        y=tumor_d["h_score_approx"],
                        marker_color=_INDIGO,
                        hovertemplate="<b>%{x}</b> (tumour)<br>H-score: %{y}<extra></extra>",
                    ))
                if not normal_d.empty:
                    fig_hpa.add_trace(go.Bar(
                        name="Normal",
                        x=normal_d["tissue"],
                        y=normal_d["h_score_approx"],
                        marker_color=_SLATE,
                        hovertemplate="<b>%{x}</b> (normal)<br>H-score: %{y}<extra></extra>",
                    ))
                fig_hpa.update_layout(
                    **_PLOTLY_LAYOUT,
                    barmode="group",
                    height=320,
                    margin=dict(l=0, r=0, t=20, b=50),
                    xaxis=dict(color=_LIGHT, tickangle=-30),
                    yaxis=dict(title="H-score (0–300)", gridcolor=_LINE, color=_TEXT),
                    legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color=_TEXT)),
                )
                st.plotly_chart(fig_hpa, use_container_width=True)
                st.caption("H-score = staining intensity × % positive cells (max 300).")
            elif "intensity_score" in hpa_df.columns:
                plot_df = hpa_df.sort_values("intensity_score", ascending=True)
                fig_hpa = go.Figure(go.Bar(
                    x=plot_df["intensity_score"],
                    y=plot_df["tissue"],
                    orientation="h",
                    marker_color=_INDIGO,
                    hovertemplate="<b>%{y}</b><br>Intensity: %{x:.0f}<extra></extra>",
                ))
                fig_hpa.update_layout(
                    **_PLOTLY_LAYOUT,
                    height=max(280, 28 * len(plot_df)),
                    margin=dict(l=0, r=10, t=20, b=40),
                    xaxis=dict(title=f"{_GENE} HPA protein intensity", gridcolor=_LINE, color=_TEXT),
                    yaxis=dict(color=_LIGHT, tickfont=dict(size=10)),
                )
                st.plotly_chart(fig_hpa, use_container_width=True)
                st.caption(f"HPA protein tissue/cell-type intensity for **{_GENE}** (Step 3c).")
            elif "ntpm" in hpa_df.columns:
                plot_df = hpa_df.dropna(subset=["ntpm"]).sort_values("ntpm", ascending=True)
                fig_hpa = go.Figure(go.Bar(
                    x=plot_df["ntpm"],
                    y=plot_df["tissue"],
                    orientation="h",
                    marker_color=_INDIGO,
                ))
                fig_hpa.update_layout(
                    **_PLOTLY_LAYOUT,
                    height=max(280, 28 * max(len(plot_df), 1)),
                    margin=dict(l=0, r=10, t=20, b=40),
                    xaxis=dict(title=f"{_GENE} HPA RNA nTPM", gridcolor=_LINE, color=_TEXT),
                    yaxis=dict(color=_LIGHT, tickfont=dict(size=10)),
                )
                st.plotly_chart(fig_hpa, use_container_width=True)
            else:
                st.dataframe(hpa_df, use_container_width=True)

    with col_gtex:
        st.markdown("##### 🏥 GTEx — Normal Tissue mRNA (54 sites)")
        if gtex_df is None:
            st.warning("GTEx data not available.")
        else:
            gtex_key = "tissue_site" if "tissue_site" in gtex_df.columns else "tissue_site_detail"
            gtex_agg = (
                gtex_df.groupby(gtex_key)["median_tpm"]
                .mean()
                .reset_index()
                .sort_values("median_tpm", ascending=True)
            )

            def _gtex_color(v):
                if v >= 80:
                    return _AMBER
                elif v >= 40:
                    return _SLATE
                return _GREEN

            fig_gtex = go.Figure()
            fig_gtex.add_trace(go.Bar(
                x=gtex_agg["median_tpm"],
                y=gtex_agg[gtex_key],
                orientation="h",
                marker_color=[_gtex_color(v) for v in gtex_agg["median_tpm"]],
                hovertemplate="<b>%{y}</b><br>Median TPM: %{x:.1f}<extra></extra>",
            ))
            fig_gtex.update_layout(
                **_PLOTLY_LAYOUT,
                height=480,
                margin=dict(l=0, r=10, t=10, b=40),
                xaxis=dict(title="Median TPM (normal tissue)", gridcolor=_LINE, color=_TEXT),
                yaxis=dict(color=_LIGHT, tickfont=dict(size=10)),
            )
            st.plotly_chart(fig_gtex, use_container_width=True)
            st.caption(
                "🟡 **Amber** ≥ 80 TPM — organs at risk (monitor in dosimetry).  \n"
                "🔵 **Slate** 40–80 TPM — moderate expression.  \n"
                "🟢 **Green** < 40 TPM — low expression, favourable safety."
            )

    st.markdown("---")
    st.markdown("**Therapeutic Window Summary**")
    w1, w2, w3 = st.columns(3)
    w1.warning(
        "**Adrenal gland, salivary glands, lung** show highest normal-tissue CD46 "
        "(≥120 TPM GTEx). Monitor closely in dosimetry modelling."
    )
    w2.success(
        "**Brain, skeletal muscle, heart** are low-CD46 normal tissues (<25 TPM). "
        "Minimal CNS and cardiac risk expected from a CD46-targeted radioligand."
    )
    w3.error(
        "**Kidney** is the primary at-risk organ: GTEx ~80 TPM AND HPA H-score 300/300. "
        "Renal dosimetry constraint will drive maximum tolerated dose."
    )

# ── Tab 3 : Functional Screen (DepMap) ──────────────────────────────────────
elif _active_tab == _TAB_LABELS[2]:
    st.markdown(f"#### {_GENE} CRISPR Essentiality — DepMap Screen")
    st.caption(
        f"Cancer Dependency Map (DepMap) CRISPR-Cas9 screen · "
        f"Score ≈ 0 → non-essential · Score < –0.5 → cell-essential dependency"
    )

    if depmap_df is None:
        st.warning(f"DepMap data not available for {_GENE}.")
        st.info(
            f"Run `python scripts/load_gene_uniprot_gtex_depmap.py --symbol {_GENE}` "
            f"to extract CRISPR scores for this gene."
        )
    else:
        n_dep   = int(depmap_df["cd46_is_dependency"].sum())
        pct_dep = depmap_df["cd46_is_dependency"].mean() * 100
        med_score = depmap_df["cd46_crispr_score"].median()

        dm1, dm2, dm3 = st.columns(3)
        dm1.metric("Cell lines screened", f"{len(depmap_df):,}")
        dm2.metric(f"{_GENE} dependencies", str(n_dep), f"{pct_dep:.1f}% of total")
        dm3.metric("Median CRISPR score", f"{med_score:.3f}", "near 0 → not essential")

        lin_agg = (
            depmap_df.groupby("lineage")
            .agg(
                mean_score=("cd46_crispr_score", "mean"),
                n_lines=("depmap_id", "count"),
                n_dep=("cd46_is_dependency", "sum"),
            )
            .reset_index()
            .sort_values("mean_score")
        )
        lin_agg["pct_dep"] = (lin_agg["n_dep"] / lin_agg["n_lines"] * 100).round(1)

        chart_col, table_col = st.columns([3, 2])

        with chart_col:
            st.markdown("##### Mean CRISPR Score by Cancer Lineage")
            lin_colors = [
                _ROSE if v < -0.3 else (_AMBER if v < -0.15 else _SLATE)
                for v in lin_agg["mean_score"]
            ]
            fig_dep = go.Figure()
            fig_dep.add_trace(go.Bar(
                x=lin_agg["mean_score"],
                y=lin_agg["lineage"],
                orientation="h",
                marker_color=lin_colors,
                hovertemplate=(
                    "<b>%{y}</b><br>"
                    "Mean score: %{x:.3f}<br>"
                    "Cell lines: %{customdata[0]:,}<extra></extra>"
                ),
                customdata=lin_agg[["n_lines"]].values,
            ))
            fig_dep.add_vline(
                x=-0.5,
                line_dash="dash",
                line_color=_ROSE,
                line_width=1.5,
                annotation_text="Dependency threshold (–0.5)",
                annotation_font_color=_ROSE,
                annotation_font_size=10,
                annotation_position="top right",
            )
            fig_dep.add_vline(x=0, line_color=_LINE, line_width=1)
            fig_dep.update_layout(
                **_PLOTLY_LAYOUT,
                height=580,
                margin=dict(l=10, r=20, t=20, b=40),
                xaxis=dict(title="Mean CRISPR score", gridcolor=_LINE, color=_TEXT),
                yaxis=dict(color=_LIGHT, tickfont=dict(size=10)),
            )
            st.plotly_chart(fig_dep, use_container_width=True)

        with table_col:
            st.markdown("##### Lineage Summary Table")
            disp = lin_agg[["lineage", "mean_score", "n_lines", "pct_dep"]].rename(columns={
                "lineage":    "Cancer Lineage",
                "mean_score": "Avg Score",
                "n_lines":    "Cell Lines",
                "pct_dep":    "% Deps",
            })
            disp["Avg Score"] = disp["Avg Score"].round(3)
            st.dataframe(disp, use_container_width=True, height=480, hide_index=True)

        st.info(
            "**Key insight:** CD46 CRISPR scores cluster near 0 across all 30 lineages — "
            "well above the –0.5 dependency threshold. This confirms CD46 is a **surface "
            "presentation target**, not an oncogenic driver. Radioligand strategies exploit "
            "overexpression for selective delivery; CD46 loss does not impair tumour cell "
            "survival, ensuring the therapeutic effect is driven entirely by the radioisotope payload."
        )

# ── Tab 4 : Priority Ranking & Downloads ────────────────────────────────────
elif _active_tab == _TAB_LABELS[3]:
    st.markdown("#### CD46 Cancer Priority Ranking")
    st.caption(
        "Priority score (0–1) combines: mRNA expression rank · protein evidence (HPA) · "
        "CNA frequency (TCGA somatic) · survival impact (Kaplan–Meier) · "
        "clinical trial activity (ClinicalTrials.gov)"
    )

    if expr_df is not None:
        # Build full priority ranking for all cancers from expression rank
        _n_ct = len(expr_df)
        _full_pri = expr_df.copy().sort_values("expression_rank")
        _full_pri["priority_score"] = (
            1.0 - (_full_pri["expression_rank"] - 1) / max(_n_ct - 1, 1)
        )
        # Override with multi-dimensional scores where available
        if priority_df is not None and len(priority_df) > 0:
            _md = priority_df.set_index("cancer_type")["priority_score"].to_dict()
            _full_pri["priority_score"] = _full_pri.apply(
                lambda r: _md.get(r["cancer_type"], r["priority_score"]), axis=1
            )

        def _tier(s):
            if s >= 0.70:
                return "HIGH"
            if s >= 0.50:
                return "MODERATE"
            if s >= 0.30:
                return "EXPLORATORY"
            return "LOW"

        _full_pri["tier"] = _full_pri["priority_score"].map(_tier)
        _full_pri = _full_pri.sort_values("priority_score", ascending=False).reset_index(drop=True)
        _full_pri["rank"] = _full_pri.index + 1

        _TIER_COL = {"HIGH": _GREEN, "MODERATE": _INDIGO, "EXPLORATORY": _AMBER, "LOW": _SLATE}
        _chart_h = max(500, _n_ct * 20)

        pri_col, exp_col = st.columns(2)

        with pri_col:
            st.markdown("##### 🏆 Priority Ranking — All Cancers")
            _fig_pri = go.Figure(go.Bar(
                x=_full_pri["priority_score"],
                y=_full_pri["cancer_type"],
                orientation="h",
                marker_color=[_TIER_COL[t] for t in _full_pri["tier"]],
                text=[f"{s:.2f}" for s in _full_pri["priority_score"]],
                textposition="outside",
                textfont=dict(color=_LIGHT, size=10),
                customdata=_full_pri[["tier", "median_expr", "rank"]].values,
                hovertemplate=(
                    "<b>%{y}</b><br>"
                    "Rank: %{customdata[2]}<br>"
                    "Score: %{x:.3f}<br>"
                    "Tier: %{customdata[0]}<br>"
                    "CD46 mRNA: %{customdata[1]:.2f}"
                    "<extra></extra>"
                ),
            ))
            _fig_pri.update_layout(
                **_PLOTLY_LAYOUT,
                height=_chart_h,
                margin=dict(l=10, r=70, t=10, b=40),
                xaxis=dict(
                    title="Priority Score (0–1)",
                    gridcolor=_LINE, color=_TEXT,
                    range=[0, 1.2],
                ),
                yaxis=dict(
                    color=_LIGHT, tickfont=dict(size=10),
                    autorange="reversed",
                ),
            )
            st.plotly_chart(_fig_pri, use_container_width=True)

            st.markdown("**Priority Score Dimensions**")
            st.markdown(
                """
| Dimension | Weight | Data Source |
|-----------|-------:|-------------|
| mRNA expression rank | 25% | TCGA via UCSC Xena |
| Protein evidence | 20% | Human Protein Atlas IHC |
| CNA frequency | 20% | TCGA somatic CNV |
| Survival impact | 20% | Kaplan–Meier (page 3) |
| Clinical trial activity | 15% | ClinicalTrials.gov |
"""
            )

        with exp_col:
            st.markdown("##### 📊 Expression Ranking — All Cancers")
            _ranked_expr = expr_df.sort_values("median_expr", ascending=False).reset_index(drop=True)
            # Gene-parameterized mean/std columns (cd46_* or {gene}_* or gene_*)
            _mean_col = next(
                (c for c in (f"{_PREFIX}_mean", "gene_mean", "cd46_mean") if c in _ranked_expr.columns),
                None,
            )
            _std_col = next(
                (c for c in (f"{_PREFIX}_std", "gene_std", "cd46_std") if c in _ranked_expr.columns),
                None,
            )
            if _mean_col is None:
                _ranked_expr = _ranked_expr.assign(_mean=_ranked_expr["median_expr"])
                _mean_col = "_mean"
            if _std_col is None:
                _ranked_expr = _ranked_expr.assign(_std=0.0)
                _std_col = "_std"
            _fig_expr = go.Figure(go.Bar(
                x=_ranked_expr["median_expr"],
                y=_ranked_expr["cancer_type"],
                orientation="h",
                marker_color=_TEAL,
                text=[f"{v:.2f}" for v in _ranked_expr["median_expr"]],
                textposition="outside",
                textfont=dict(color=_LIGHT, size=10),
                customdata=_ranked_expr[["n_samples", _mean_col, _std_col]].values,
                hovertemplate=(
                    "<b>%{y}</b><br>"
                    "Median log₂(TPM+1): %{x:.3f}<br>"
                    "Mean: %{customdata[1]:.3f}<br>"
                    "Std Dev: %{customdata[2]:.3f}<br>"
                    "Samples: %{customdata[0]}"
                    "<extra></extra>"
                ),
            ))
            _fig_expr.update_layout(
                **_PLOTLY_LAYOUT,
                height=_chart_h,
                margin=dict(l=10, r=70, t=10, b=40),
                xaxis=dict(
                    title=f"{_GENE} Median log₂(TPM+1)",
                    gridcolor=_LINE, color=_TEXT,
                ),
                yaxis=dict(
                    color=_LIGHT, tickfont=dict(size=10),
                    autorange="reversed",
                ),
            )
            st.plotly_chart(_fig_expr, use_container_width=True)

            st.download_button(
                "⬇ Download expression CSV",
                data=expr_df.to_csv(index=False),
                file_name=f"{_GENE.lower()}_expression_by_cancer.csv",
                mime="text/csv",
            )
            export_research_pack(
                expr_df,
                key="expr_export_pack",
                result_name=f"{_GENE.lower()}_expression_by_cancer.csv",
            )
            if depmap_df is not None:
                st.download_button(
                    "⬇ Download DepMap CSV",
                    data=depmap_df.to_csv(index=False),
                    file_name=f"depmap_{_GENE.lower()}_essentiality.csv",
                    mime="text/csv",
                    key="dl_depmap",
                )
    else:
        st.info(
            "Priority scoring pending. Run `python scripts/run_pipeline.py --mode analyze` "
            "to compute scores for all 25 cancer types."
        )

st.markdown("---")
st.caption(
    "Sources: TCGA RNA-seq via UCSC Xena (RNAseqv2, log₂(TPM+1), 7,500+ patients) · "
    "Human Protein Atlas IHC (H-score 0–300) · "
    "GTEx v8 normal tissue mRNA (54 sites) · "
    "DepMap 24Q2 CRISPR screen (1,186 cancer cell lines)"
)
