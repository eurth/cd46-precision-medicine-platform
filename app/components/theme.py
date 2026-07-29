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
CHART_MUTED = "#CBD5E1"
CHART_GRID = "#E2E8F0"


def plotly_layout(**overrides) -> dict:
    """Default Plotly layout for Clinical Slate."""
    base = {
        "paper_bgcolor": SURFACE,
        "plot_bgcolor": SURFACE_2,
        "font": {"family": "Inter, sans-serif", "color": TEXT_MUTED},
        "margin": {"l": 48, "r": 24, "t": 48, "b": 48},
        "xaxis": {
            "gridcolor": CHART_GRID,
            "linecolor": BORDER,
            "color": TEXT_MUTED,
            "zerolinecolor": BORDER,
        },
        "yaxis": {
            "gridcolor": CHART_GRID,
            "linecolor": BORDER,
            "color": TEXT_MUTED,
            "zerolinecolor": BORDER,
        },
    }
    base.update(overrides)
    return base


def assert_theme_smoke() -> None:
    layout = plotly_layout()
    assert layout["paper_bgcolor"] == SURFACE
    assert PRIMARY.startswith("#")


if __name__ == "__main__":
    assert_theme_smoke()
    print("theme_smoke_ok")
