"""Smoke-test Plotly update_layout patterns used across page modules."""
from __future__ import annotations

import ast
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "app"))

import plotly.graph_objects as go
from components.theme import CHART_GRID, TEXT, TEXT_MUTED, plotly_layout

_PLOTLY_LAYOUT = plotly_layout()
_CONFLICT_KEYS = frozenset({"xaxis", "yaxis", "legend", "hoverlabel", "font", "margin", "title"})


def _simulate_page_call(extra_keys: set[str]) -> None:
    kwargs = dict(
        height=400,
        margin=dict(l=10, r=10, t=10, b=10),
        xaxis=dict(title="X", gridcolor=CHART_GRID, color=TEXT_MUTED),
        yaxis=dict(color=TEXT, tickfont=dict(size=11)),
    )
    if "legend" in extra_keys:
        kwargs["legend"] = dict(font=dict(color=TEXT))
    if "hoverlabel" in extra_keys:
        kwargs["hoverlabel"] = dict(bgcolor="#FFFFFF", font=dict(color=TEXT))
    fig = go.Figure(go.Bar(x=[1], y=[2]))
    fig.update_layout(**_PLOTLY_LAYOUT, **kwargs)


def _scan_pages() -> list[str]:
    issues: list[str] = []
    pages = ROOT / "app" / "pages"
    for path in sorted(pages.glob("*.py")):
        src = path.read_text(encoding="utf-8-sig")
        if "**_PLOTLY_LAYOUT" not in src:
            continue
        tree = ast.parse(src)
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            func = node.func
            if not (isinstance(func, ast.Attribute) and func.attr == "update_layout"):
                continue
            has_spread = any(
                isinstance(kw, ast.keyword) and isinstance(kw.value, ast.Starred)
                and isinstance(kw.value.value, ast.Name)
                and kw.value.value.id == "_PLOTLY_LAYOUT"
                for kw in node.keywords
            )
            if not has_spread:
                continue
            overlap = {
                kw.arg for kw in node.keywords
                if kw.arg and kw.arg in _CONFLICT_KEYS and kw.arg in plotly_layout()
            }
            if overlap:
                issues.append(f"{path.name}:{node.lineno} **_PLOTLY_LAYOUT + {sorted(overlap)}")
    return issues


def main() -> None:
    _simulate_page_call({"legend", "hoverlabel"})
    issues = _scan_pages()
    if issues:
        print("FAIL — layout key overlaps still possible:")
        for i in issues:
            print(" ", i)
        sys.exit(1)
    print("verify_plotly_pages_ok")


if __name__ == "__main__":
    main()
