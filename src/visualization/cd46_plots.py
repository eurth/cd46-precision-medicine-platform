"""
All Plotly interactive charts for CD46 platform.
Produces: pan-cancer boxplot, violin, KM curves, forest plot, heatmap, HPA bar chart.
Charts are returned as Plotly Figure objects for use in Streamlit or export to HTML/PNG.
"""

import logging
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

log = logging.getLogger(__name__)

FIGURES_DIR = Path("reports/figures")

# Color palette
PRIORITY_COLORS = {
    "HIGH PRIORITY": "#d62728",
    "MODERATE": "#ff7f0e",
    "EXPLORATORY": "#2ca02c",
    "CD46-High": "#d62728",
    "CD46-Low": "#1f77b4",
}


def plot_pan_cancer_boxplot(expr_df: pd.DataFrame,
                             priority_df: Optional[pd.DataFrame] = None,
                             cancer_col: str = "cancer_type",
                             expr_col: str = "cd46_log2_tpm",
                             sort_by: Optional[str] = None,
                             return_fig: bool = False) -> go.Figure:
    """
    Pan-cancer CD46 expression boxplot, sorted by median, colored by priority label.
    """
    if cancer_col not in expr_df.columns:
        cancer_col = next((c for c in ["cancer type abbreviation", "_cohort"]
                           if c in expr_df.columns), expr_df.columns[0])

    # Handle aggregated (cd46_by_cancer.csv) vs per-sample data
    is_aggregated = expr_col not in expr_df.columns and "cd46_median" in expr_df.columns
    if is_aggregated:
        expr_col = "cd46_median"  # use the precomputed median column

    # Sort cancers by median CD46 expression
    if sort_by and "priority" in sort_by.lower() and priority_df is not None and "priority_score" in priority_df.columns:
        order = priority_df.sort_values("priority_score", ascending=False)["cancer_type"].tolist()
    elif sort_by and "a-z" in sort_by.lower():
        order = sorted(expr_df[cancer_col].unique().tolist())
    elif is_aggregated:
        order = (expr_df.sort_values("cd46_median", ascending=False)[cancer_col].tolist())
    else:
        order = (expr_df.groupby(cancer_col)[expr_col].median()
                 .sort_values(ascending=False).index.tolist())

    # Map priority labels
    color_map = {}
    if priority_df is not None and "priority_label" in priority_df.columns:
        color_map = priority_df.set_index("cancer_type")["priority_label"].to_dict()

    expr_df = expr_df.copy()
    expr_df["Priority"] = expr_df[cancer_col].map(color_map).fillna("EXPLORATORY")

    if is_aggregated:
        # Use bar chart for aggregated summary data (cd46_by_cancer.csv)
        plot_df = expr_df.set_index(cancer_col).reindex(order).reset_index()
        colors = plot_df["Priority"].map(PRIORITY_COLORS).fillna("#2ca02c")
        fig = go.Figure(go.Bar(
            x=plot_df[cancer_col],
            y=plot_df[expr_col],
            marker_color=colors,
            text=plot_df[expr_col].round(2),
            textposition="outside",
        ))
        fig.update_layout(
            title="CD46 Median Expression Across TCGA Cancer Types",
            xaxis_title="Cancer Type",
            yaxis_title="CD46 Median Expression (log2 TPM+0.001)",
            height=550,
            xaxis_tickangle=-45,
            font=dict(size=12),
            title_font_size=16,
        )
    else:
        fig = px.box(
            expr_df,
            x=cancer_col,
            y=expr_col,
            color="Priority",
            color_discrete_map=PRIORITY_COLORS,
            category_orders={cancer_col: order},
            title="CD46 Expression Across 33 TCGA Cancer Types",
            labels={expr_col: "CD46 Expression (log2 TPM+0.001)", cancer_col: "Cancer Type"},
            points=False,
        )
        fig.update_layout(
            height=550,
            xaxis_tickangle=-45,
            showlegend=True,
            font=dict(size=12),
            title_font_size=16,
        )
    fig.add_hline(y=2.5, line_dash="dash", line_color="gray",
                  annotation_text="225Ac threshold (log2=2.5)")

    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    fig.write_html(str(FIGURES_DIR / "pan_cancer_boxplot.html"))
    return fig



def plot_hpa_protein(hpa_df: pd.DataFrame, return_fig: bool = False) -> go.Figure:
    """CD46 protein expression bar chart by tissue type (HPA data)."""
    tumor = hpa_df[hpa_df["type"] == "tumor"].sort_values("intensity_score", ascending=False)
    normal = hpa_df[hpa_df["type"] == "normal"].sort_values("intensity_score", ascending=False)

    fig = make_subplots(rows=1, cols=2,
                        subplot_titles=["CD46 Protein — Tumor Tissues", "CD46 Protein — Normal Tissues"])

    fig.add_trace(go.Bar(
        x=tumor["tissue"], y=tumor["intensity_score"],
        marker_color=tumor["intensity_score"].map({0: "#2ca02c", 1: "#ff7f0e", 2: "#ff7f0e", 3: "#d62728"}),
        name="Tumor",
    ), row=1, col=1)

    fig.add_trace(go.Bar(
        x=normal["tissue"], y=normal["intensity_score"],
        marker_color="#1f77b4", name="Normal",
    ), row=1, col=2)

    fig.update_layout(
        height=480,
        title_text="CD46 Protein Expression by Tissue (Human Protein Atlas)",
        yaxis_title="Staining Intensity Score (0–3)",
        showlegend=False,
    )
    fig.write_html(str(FIGURES_DIR / "hpa_protein.html"))
    return fig


def plot_km_curves(expr_df: pd.DataFrame,
                   cancer_type: str = "PRAD",
                   time_col: str = "OS.time",
                   event_col: str = "OS",
                   return_fig: bool = False) -> go.Figure:
    """Plotly Kaplan-Meier curves for CD46-High vs CD46-Low."""
    from lifelines import KaplanMeierFitter
    from lifelines.statistics import logrank_test

    sub = expr_df.copy()
    cancer_col = next((c for c in ["cancer type abbreviation", "cancer_type"]
                       if c in sub.columns), sub.columns[0])
    sub = sub[sub[cancer_col] == cancer_type][[time_col, event_col, "cd46_log2_tpm"]].dropna()

    if len(sub) < 40:
        fig = go.Figure()
        fig.add_annotation(text=f"Insufficient data for {cancer_type} KM analysis",
                           xref="paper", yref="paper", x=0.5, y=0.5)
        return fig

    median = sub["cd46_log2_tpm"].median()
    sub["group"] = (sub["cd46_log2_tpm"] >= median).map({True: "CD46-High", False: "CD46-Low"})

    high = sub[sub["group"] == "CD46-High"]
    low = sub[sub["group"] == "CD46-Low"]

    kmf_high = KaplanMeierFitter()
    kmf_low = KaplanMeierFitter()
    kmf_high.fit(high[time_col] / 30, high[event_col], label="CD46-High")
    kmf_low.fit(low[time_col] / 30, low[event_col], label="CD46-Low")

    lr = logrank_test(high[time_col], low[time_col],
                      event_observed_A=high[event_col], event_observed_B=low[event_col])

    fig = go.Figure()
    for kmf, color in [(kmf_high, "#d62728"), (kmf_low, "#1f77b4")]:
        t = kmf.timeline
        s = kmf.survival_function_.values.flatten()
        ci = kmf.confidence_interval_survival_function_
        fig.add_trace(go.Scatter(x=t, y=s, mode="lines", name=kmf._label,
                                  line=dict(color=color, width=2)))
        fig.add_trace(go.Scatter(
            x=np.concatenate([t, t[::-1]]),
            y=np.concatenate([ci.iloc[:, 1], ci.iloc[:, 0][::-1]]),
            fill="toself", fillcolor=color, opacity=0.1,
            line=dict(color="rgba(0,0,0,0)"), showlegend=False,
        ))

    fig.update_layout(
        title=f"{cancer_type} Overall Survival by CD46 Expression<br>"
              f"<sup>Log-rank p={lr.p_value:.4f} | n_high={len(high)}, n_low={len(low)}</sup>",
        xaxis_title="Time (months)", yaxis_title="Survival Probability",
        height=450, yaxis_range=[0, 1.05],
    )
    fig.write_html(str(FIGURES_DIR / f"km_{cancer_type}.html"))
    return fig


def plot_forest_plot(survival_df: pd.DataFrame,
                     endpoint: str = "OS",
                     return_fig: bool = False) -> go.Figure:
    """Forest plot: CD46 hazard ratios across cancer types."""
    cox_rows = survival_df[survival_df["endpoint"] == endpoint].dropna(subset=["hazard_ratio"])
    cox_rows = cox_rows.sort_values("hazard_ratio", ascending=True).reset_index(drop=True)

    if cox_rows.empty:
        fig = go.Figure()
        fig.add_annotation(text="No Cox survival data available", xref="paper", yref="paper",
                           x=0.5, y=0.5)
        return fig

    colors = cox_rows["hazard_ratio"].map(
        lambda hr: "#d62728" if hr > 1 else "#1f77b4"
    )

    fig = go.Figure()
    for i, row in cox_rows.iterrows():
        fig.add_trace(go.Scatter(
            x=[row.get("hr_lower_95", row["hazard_ratio"] * 0.8),
               row.get("hr_upper_95", row["hazard_ratio"] * 1.2)],
            y=[row["cancer_type"], row["cancer_type"]],
            mode="lines", line=dict(color=colors[i], width=2),
            showlegend=False,
        ))
        fig.add_trace(go.Scatter(
            x=[row["hazard_ratio"]], y=[row["cancer_type"]],
            mode="markers",
            marker=dict(size=10, color=colors[i],
                        symbol="diamond" if row.get("significant", False) else "circle"),
            name=row["cancer_type"], showlegend=False,
        ))

    fig.add_vline(x=1.0, line_dash="dash", line_color="black",
                  annotation_text="HR=1 (no effect)")
    fig.update_layout(
        title="CD46 Expression — Hazard Ratio for Overall Survival",
        xaxis_title="Hazard Ratio (log scale)",
        xaxis_type="log", height=max(400, len(cox_rows) * 25 + 100),
    )
    fig.write_html(str(FIGURES_DIR / "forest_plot.html"))
    return fig


def plot_priority_heatmap(priority_df: pd.DataFrame, return_fig: bool = False) -> go.Figure:
    """Heatmap of priority score components across cancer types."""
    score_cols = ["expr_rank_score", "survival_impact", "cna_score", "protein_score", "priority_score"]
    avail = [c for c in score_cols if c in priority_df.columns]
    if not avail:
        return go.Figure()

    df = priority_df.sort_values("priority_score", ascending=False).head(20)
    z = df[avail].fillna(0).values
    labels = ["Expression Rank", "Survival Impact", "CNA Freq", "Protein Score", "TOTAL"][:len(avail)]

    fig = go.Figure(data=go.Heatmap(
        z=z.T, x=df["cancer_type"].tolist(), y=labels,
        colorscale="RdYlGn", zmid=0.5,
        text=np.round(z.T, 2), texttemplate="%{text}",
    ))
    fig.update_layout(
        title="CD46 Priority Score Components — Top 20 Cancer Types",
        height=380, xaxis_tickangle=-45,
    )
    fig.write_html(str(FIGURES_DIR / "priority_heatmap.html"))
    return fig
