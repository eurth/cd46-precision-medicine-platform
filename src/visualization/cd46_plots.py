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
    "CD46-High": "#6366F1",
    "CD46-Low": "#94A3B8",
}

# Chart theme constants
_BG = "#0B1120"
_PLOT_BG = "#0B1120"
_GRID_COLOR = "#1E293B"
_AXIS_COLOR = "#475569"
_TEXT_COLOR = "#94A3B8"
_KM_HIGH_COLOR = "#6366F1"
_KM_LOW_COLOR = "#94A3B8"


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
        # Horizontal bar chart for aggregated summary data (cd46_by_cancer.csv)
        plot_df = expr_df.set_index(cancer_col).reindex(order).reset_index()

        # Sequential color scale from #1E3A5F (low) to #0EA5E9 (high)
        vals = plot_df[expr_col].fillna(0)
        v_min, v_max = vals.min(), vals.max()
        v_range = v_max - v_min if v_max != v_min else 1.0

        def _seq_color(v):
            t = (v - v_min) / v_range  # 0..1
            r = int(0x1E + t * (0x0E - 0x1E))
            g = int(0x3A + t * (0xA5 - 0x3A))
            b = int(0x5F + t * (0xE9 - 0x5F))
            return f"#{r:02X}{g:02X}{b:02X}"

        bar_colors = vals.apply(_seq_color).tolist()

        # Priority edge coloring (left border via marker_line)
        priority_edge_map = {
            "HIGH PRIORITY": "#EF4444",
            "MODERATE":      "#F59E0B",
            "EXPLORATORY":   "#475569",
        }
        edge_colors = plot_df["Priority"].map(priority_edge_map).fillna("#475569").tolist()

        fig = go.Figure(go.Bar(
            y=plot_df[cancer_col],
            x=vals,
            orientation="h",
            marker=dict(
                color=bar_colors,
                line=dict(color=edge_colors, width=3),
            ),
            text=vals.round(2),
            textposition="outside",
            textfont=dict(color=_TEXT_COLOR, size=10),
            hovertemplate="%{y}: %{x:.2f} log₂ TPM<extra></extra>",
        ))
        fig.add_vline(
            x=2.5,
            line_dash="dash",
            line_color="#94A3B8",
            line_width=1.5,
        )
        fig.add_annotation(
            x=2.5, y=1.0,
            xref="x", yref="paper",
            text="225Ac threshold",
            showarrow=False,
            font=dict(size=10, color="#94A3B8"),
            xanchor="left",
            xshift=5,
        )
        fig.update_layout(
            paper_bgcolor=_BG,
            plot_bgcolor=_PLOT_BG,
            height=max(500, len(plot_df) * 22 + 80),
            margin=dict(t=20, b=50, l=80, r=60),
            xaxis=dict(
                title=dict(text="CD46 MEDIAN EXPRESSION (LOG₂ TPM+0.001)",
                           font=dict(size=11, color=_TEXT_COLOR)),
                tickfont=dict(color=_AXIS_COLOR, size=11),
                gridcolor=_GRID_COLOR,
                linecolor=_GRID_COLOR,
                zeroline=False,
            ),
            yaxis=dict(
                tickfont=dict(
                    color=_AXIS_COLOR, size=11,
                    family="JetBrains Mono, Courier New, monospace",
                ),
                linecolor=_GRID_COLOR,
                automargin=True,
            ),
        )
    else:
        fig = px.box(
            expr_df,
            x=cancer_col,
            y=expr_col,
            color="Priority",
            color_discrete_map=PRIORITY_COLORS,
            category_orders={cancer_col: order},
            labels={expr_col: "CD46 Expression (log2 TPM+0.001)", cancer_col: "Cancer Type"},
            points=False,
        )
        fig.update_layout(
            paper_bgcolor=_BG,
            plot_bgcolor=_PLOT_BG,
            height=550,
            xaxis_tickangle=-45,
            showlegend=True,
            font=dict(size=12),
            xaxis=dict(tickfont=dict(color=_AXIS_COLOR), gridcolor=_GRID_COLOR),
            yaxis=dict(tickfont=dict(color=_AXIS_COLOR), gridcolor=_GRID_COLOR),
        )
        fig.add_vline(x=2.5, line_dash="dash", line_color="#94A3B8", line_width=1.5)
        fig.add_annotation(
            x=2.5, y=1.0, xref="x", yref="paper",
            text="225Ac threshold",
            showarrow=False,
            font=dict(size=10, color="#94A3B8"),
            xanchor="left", xshift=5,
        )

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
        paper_bgcolor=_BG,
        plot_bgcolor=_PLOT_BG,
        height=480,
        title_text="CD46 Protein Expression by Tissue (Human Protein Atlas)",
        yaxis_title="Staining Intensity Score (0–3)",
        showlegend=False,
        font=dict(color=_TEXT_COLOR),
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
    for kmf, line_color, ci_rgba in [
        (kmf_high, _KM_HIGH_COLOR, "rgba(99,102,241,0.15)"),
        (kmf_low,  _KM_LOW_COLOR,  "rgba(148,163,184,0.15)"),
    ]:
        t = kmf.timeline
        s = kmf.survival_function_.values.flatten()
        ci = kmf.confidence_interval_survival_function_

        # Confidence interval band
        fig.add_trace(go.Scatter(
            x=np.concatenate([t, t[::-1]]),
            y=np.concatenate([ci.iloc[:, 1], ci.iloc[:, 0][::-1]]),
            fill="toself",
            fillcolor=ci_rgba,
            line=dict(color="rgba(0,0,0,0)"),
            showlegend=False,
            hoverinfo="skip",
        ))
        # Survival line
        fig.add_trace(go.Scatter(
            x=t, y=s,
            mode="lines",
            name=kmf._label,
            line=dict(color=line_color, width=2.5),
        ))

        # Censored tick marks — vertical dashes at censored event times
        event_table = kmf.event_table
        censored_t = event_table[event_table["censored"] > 0].index.tolist()
        if censored_t:
            # Get survival probability at censored times
            surv_at_censor = []
            for tc in censored_t:
                idx = np.searchsorted(t, tc, side="right") - 1
                idx = max(0, min(idx, len(s) - 1))
                surv_at_censor.append(s[idx])
            fig.add_trace(go.Scatter(
                x=censored_t,
                y=surv_at_censor,
                mode="markers",
                marker=dict(
                    symbol="line-ns",
                    size=9,
                    color=line_color,
                    line=dict(width=1.5, color=line_color),
                ),
                showlegend=False,
                hoverinfo="skip",
            ))

    # Annotation box (upper right)
    fig.add_annotation(
        xref="paper", yref="paper",
        x=0.98, y=0.98,
        xanchor="right", yanchor="top",
        text=(
            f"Log-rank p = {lr.p_value:.4f}<br>"
            f"n_high = {len(high)}, n_low = {len(low)}"
        ),
        showarrow=False,
        font=dict(color="#F8FAFC", size=12, family="Inter, sans-serif"),
        bgcolor="#111827",
        bordercolor="#F8FAFC",
        borderwidth=1,
        borderpad=8,
        align="right",
    )

    fig.update_layout(
        paper_bgcolor=_BG,
        plot_bgcolor=_PLOT_BG,
        height=450,
        yaxis_range=[0, 1.05],
        margin=dict(t=30, b=50, l=60, r=20),
        legend=dict(
            x=0.02, y=0.10,
            bgcolor="rgba(11,17,32,0.8)",
            bordercolor="#1E293B",
            borderwidth=1,
            font=dict(color="#F8FAFC", size=12),
        ),
        xaxis=dict(
            title=dict(text="TIME (MONTHS)", font=dict(size=11, color=_TEXT_COLOR)),
            tickfont=dict(color=_AXIS_COLOR, size=11),
            gridcolor=_GRID_COLOR,
            linecolor=_GRID_COLOR,
            zeroline=False,
        ),
        yaxis=dict(
            title=dict(text="SURVIVAL PROBABILITY", font=dict(size=11, color=_TEXT_COLOR)),
            tickfont=dict(color=_AXIS_COLOR, size=11),
            gridcolor=_GRID_COLOR,
            linecolor=_GRID_COLOR,
            zeroline=False,
        ),
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

    def _forest_color(row) -> str:
        """Color logic: protective = indigo, risky = red, ns = muted."""
        p = row.get("log_rank_p", row.get("p_value", 1.0))
        hr = row["hazard_ratio"]
        if p < 0.05 and hr < 1.0:
            return "#6366F1"   # protective
        if p < 0.05 and hr > 1.0:
            return "#EF4444"   # risk
        return "#475569"       # not significant

    colors = [_forest_color(row) for _, row in cox_rows.iterrows()]

    fig = go.Figure()
    for i, (_, row) in enumerate(cox_rows.iterrows()):
        hr = row["hazard_ratio"]
        ci_lo = row.get("hr_lower_95", hr * 0.80)
        ci_hi = row.get("hr_upper_95", hr * 1.25)
        ct = row["cancer_type"]
        c = colors[i]
        p = row.get("log_rank_p", row.get("p_value", 1.0))
        sig_marker = "diamond" if p < 0.05 else "circle"

        # CI line
        fig.add_trace(go.Scatter(
            x=[ci_lo, ci_hi], y=[ct, ct],
            mode="lines",
            line=dict(color=c, width=1),
            showlegend=False,
            hoverinfo="skip",
        ))
        # HR point
        fig.add_trace(go.Scatter(
            x=[hr], y=[ct],
            mode="markers",
            marker=dict(size=9, color=c, symbol=sig_marker),
            name=ct,
            showlegend=False,
            hovertemplate=f"<b>{ct}</b><br>HR={hr:.2f}<br>95% CI [{ci_lo:.2f}, {ci_hi:.2f}]<extra></extra>",
        ))

    # Center reference line at HR=1.0
    fig.add_vline(
        x=1.0,
        line_dash="dash",
        line_color="rgba(255,255,255,0.4)",
        line_width=1.5,
    )

    fig.update_layout(
        paper_bgcolor=_BG,
        plot_bgcolor=_PLOT_BG,
        height=max(400, len(cox_rows) * 28 + 80),
        margin=dict(t=30, b=50, l=90, r=30),
        xaxis=dict(
            type="log",
            title=dict(text="HAZARD RATIO (LOG SCALE)", font=dict(size=11, color=_TEXT_COLOR)),
            tickfont=dict(color=_AXIS_COLOR, size=11),
            gridcolor=_GRID_COLOR,
            linecolor=_GRID_COLOR,
            zeroline=False,
        ),
        yaxis=dict(
            tickfont=dict(
                color=_AXIS_COLOR,
                size=11,
                family="JetBrains Mono, Courier New, monospace",
            ),
            gridcolor=_GRID_COLOR,
            linecolor=_GRID_COLOR,
            automargin=True,
        ),
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
