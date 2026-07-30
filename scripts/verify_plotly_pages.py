"""Smoke-test Plotly layout patterns used across page modules."""
from __future__ import annotations

import ast
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "app"))

import plotly.graph_objects as go
from components.theme import CHART_GRID, TEXT, TEXT_MUTED, apply_plotly_layout, chart_layout


def _simulate_page_call() -> None:
    fig = go.Figure(go.Bar(x=[1], y=[2]))
    apply_plotly_layout(
        fig,
        height=400,
        margin=dict(l=10, r=10, t=10, b=10),
        xaxis=dict(title="X", gridcolor=CHART_GRID, color=TEXT_MUTED),
        yaxis=dict(color=TEXT, tickfont=dict(size=11)),
        legend=dict(font=dict(color=TEXT)),
        hoverlabel=dict(bgcolor="#FFFFFF", font=dict(color=TEXT)),
    )
    merged = chart_layout(yaxis=dict(title="Y"))
    assert merged["yaxis"]["tickfont"]["color"] == "#475569"


def _scan_pages() -> list[str]:
    issues: list[str] = []
    pages = ROOT / "app" / "pages"
    for path in sorted(pages.glob("*.py")):
        src = path.read_text(encoding="utf-8-sig")
        if "**_PLOTLY_LAYOUT" in src:
            issues.append(f"{path.name}: still uses **_PLOTLY_LAYOUT spread")
        tree = ast.parse(src)
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            func = node.func
            if not (isinstance(func, ast.Attribute) and func.attr == "update_layout"):
                continue
            has_spread = any(
                isinstance(kw, ast.keyword) and isinstance(kw.value, ast.Starred)
                for kw in node.keywords
            )
            if has_spread:
                issues.append(f"{path.name}:{node.lineno} update_layout still uses **spread")
    return issues


def main() -> None:
    _simulate_page_call()
    issues = _scan_pages()
    if issues:
        print("FAIL:")
        for i in issues:
            print(" ", i)
        sys.exit(1)
    print("verify_plotly_pages_ok")


if __name__ == "__main__":
    main()
