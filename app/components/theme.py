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


def plotly_layout(**overrides) -> dict:
    """Default Plotly layout for Clinical Slate; pass page overrides as kwargs."""
    base = {
        "paper_bgcolor": SURFACE,
        "plot_bgcolor": SURFACE_2,
        "font": {"family": "Inter, sans-serif", "color": TEXT_MUTED},
        "xaxis": dict(_AXIS),
        "yaxis": dict(_AXIS),
        "hoverlabel": {
            "bgcolor": SURFACE,
            "bordercolor": BORDER,
            "font": {"color": TEXT, "size": 12},
        },
        "legend": {
            "bgcolor": "rgba(255,255,255,0.92)",
            "bordercolor": BORDER,
            "font": {"color": TEXT, "size": 11},
        },
    }
    return _deep_merge(base, overrides)


def apply_plotly_layout(fig, **overrides):
    """ponytail: one safe entry — avoids **base + duplicate margin/xaxis kwargs."""
    fig.update_layout(**plotly_layout(**overrides))
    return fig


def assert_theme_smoke() -> None:
    layout = plotly_layout()
    assert layout["paper_bgcolor"] == SURFACE
    assert PRIMARY.startswith("#")


if __name__ == "__main__":
    assert_theme_smoke()
    print("theme_smoke_ok")
