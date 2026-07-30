"""OncoBridge Clinical Slate design tokens + shared chart theme."""
from __future__ import annotations

# Surfaces
BG = "#F4F6F9"
SURFACE = "#FFFFFF"
SURFACE_2 = "#EEF2F7"
BORDER = "#D5DEE8"
BORDER_STRONG = "#CBD5E1"

# Text
TEXT = "#1E293B"
TEXT_SECONDARY = "#475569"
TEXT_MUTED = "#64748B"
TEXT_FAINT = "#94A3B8"

# Brand
PRIMARY = "#2563EB"
PRIMARY_HOVER = "#1D4ED8"
PRIMARY_SOFT = "#DBEAFE"
PRIMARY_TEXT = "#1E40AF"

TEAL = "#0D9488"
AMBER = "#D97706"
GREEN = "#059669"
ROSE = "#E11D48"
SLATE = "#94A3B8"

# Sidebar / chrome
SIDEBAR_BG = "#FFFFFF"
TOPBAR_BG = "#FFFFFF"

# Chart series (readable on light canvas)
CHART_HIGHLIGHT = "#2563EB"
CHART_MID = "#64748B"
CHART_MUTED = "#94A3B8"  # secondary bars/lines — not grid-line gray
CHART_GRID = "#E2E8F0"
CHART_BAR_SECONDARY = CHART_MUTED

# Legacy page aliases — maps old dark-theme vars to Clinical Slate (keep during migration)
C_BG = SURFACE
C_LINE = CHART_GRID
C_TEXT = TEXT_MUTED
C_LIGHT = TEXT
C_MID = TEXT_FAINT
C_INDIGO = CHART_HIGHLIGHT


def _deep_merge(base: dict, overrides: dict) -> dict:
    """Merge Plotly layout dicts (nested xaxis/yaxis/font/legend/margin)."""
    out = dict(base)
    for key, val in overrides.items():
        if key in out and isinstance(out[key], dict) and isinstance(val, dict):
            out[key] = _deep_merge(out[key], val)
        else:
            out[key] = val
    return out


_AXIS = {
    "color": TEXT_MUTED,
    "gridcolor": CHART_GRID,
    "zerolinecolor": CHART_GRID,
    "linecolor": BORDER,
    "tickfont": {"color": TEXT_SECONDARY, "size": 11},
    "title": {"font": {"color": TEXT_MUTED, "size": 12}},
}
CHART_AXIS = _AXIS  # optional: merge into per-page xaxis/yaxis dicts


def plotly_layout(**overrides) -> dict:
    """Default Plotly layout for Clinical Slate; pass page overrides as kwargs.

    Base omits xaxis/yaxis/legend/hoverlabel — pages spread ``**_PLOTLY_LAYOUT``
    then pass those keys; including them here causes duplicate-kwarg TypeErrors.
  Use ``plotly_layout(xaxis=..., yaxis=...)`` or ``apply_plotly_layout(fig, ...)``
    when you need merged axis defaults from CHART_AXIS.
    """
    base = {
        "paper_bgcolor": SURFACE,
        "plot_bgcolor": SURFACE_2,
        "font": {"family": "Inter, sans-serif", "color": TEXT_MUTED},
    }
    return _deep_merge(base, overrides)


def chart_layout(**overrides) -> dict:
    """Build one layout dict — merges CHART_AXIS into xaxis/yaxis (safe for update_layout)."""
    kw = dict(overrides)
    for ax in ("xaxis", "yaxis"):
        if ax in kw and isinstance(kw[ax], dict):
            merged = _deep_merge(dict(_AXIS), kw[ax])
            tf = merged.get("tickfont")
            if not isinstance(tf, dict):
                tf = {}
            if "color" not in tf:
                merged["tickfont"] = _deep_merge({"color": TEXT_SECONDARY, "size": 11}, tf)
            kw[ax] = merged
    if "legend" in kw and isinstance(kw["legend"], dict):
        kw["legend"] = _deep_merge(
            {
                "bgcolor": "rgba(255,255,255,0.92)",
                "bordercolor": BORDER,
                "font": {"color": TEXT, "size": 11},
            },
            kw["legend"],
        )
    if "hoverlabel" in kw and isinstance(kw["hoverlabel"], dict):
        kw["hoverlabel"] = _deep_merge(
            {
                "bgcolor": SURFACE,
                "bordercolor": BORDER,
                "font": {"color": TEXT, "size": 12},
            },
            kw["hoverlabel"],
        )
    return plotly_layout(**kw)


def apply_plotly_layout(fig, **overrides):
    """ponytail: one safe entry — merges axis defaults, no duplicate-kwarg spread."""
    fig.update_layout(**chart_layout(**overrides))
    return fig


def assert_theme_smoke() -> None:
    layout = plotly_layout()
    assert layout["paper_bgcolor"] == SURFACE
    assert PRIMARY.startswith("#")
    # Page pattern: **_PLOTLY_LAYOUT then explicit xaxis/yaxis must not duplicate keys.
    assert "xaxis" not in layout and "yaxis" not in layout
    import plotly.graph_objects as go

    fig = go.Figure()
    base = plotly_layout()
    fig.update_layout(
        **base,
        xaxis=dict(title="Test", color=TEXT_MUTED, gridcolor=CHART_GRID),
        yaxis=dict(color=TEXT, tickfont=dict(size=11)),
        legend=dict(font=dict(color=TEXT)),
    )
    merged = chart_layout(
        xaxis=_deep_merge(dict(_AXIS), {"title": "Merged"}),
        yaxis=dict(color=TEXT),
    )
    assert merged["xaxis"]["title"] == "Merged"
    assert merged["yaxis"]["tickfont"]["color"] == TEXT_SECONDARY


if __name__ == "__main__":
    assert_theme_smoke()
    print("theme_smoke_ok")
