"""Light-surface sweep: chart bg + tab-intro callouts (safe string replaces)."""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAGES = ROOT / "app" / "pages"

CHART = [
    ('paper_bgcolor="#0f172a"', 'paper_bgcolor="#FFFFFF"'),
    ("paper_bgcolor='#0f172a'", "paper_bgcolor='#FFFFFF'"),
    ('plot_bgcolor="#0f172a"', 'plot_bgcolor="#EEF2F7"'),
    ('paper_bgcolor="#0D1829"', 'paper_bgcolor="#FFFFFF"'),
    ('plot_bgcolor="#0D1829"', 'plot_bgcolor="#EEF2F7"'),
    ('"bgcolor": "#0f172a"', '"bgcolor": "#FFFFFF"'),
    ('bgcolor="#0f172a"', 'bgcolor="#FFFFFF"'),
    ('font=dict(color="#e2e8f0")', 'font=dict(color="#64748B")'),
]

CALLOUTS = [
    (
        "<div style='background:#1e293b;border-left:3px solid #38bdf8;padding:12px 16px;border-radius:6px;margin-bottom:14px;'>",
        '<div class="ob-tab-intro ob-tab-intro-info">',
    ),
    (
        '<div style="background:#1e293b;border-left:3px solid #38bdf8;padding:12px 16px;border-radius:6px;margin-bottom:14px;">',
        '<div class="ob-tab-intro ob-tab-intro-info">',
    ),
    (
        "<div style='background:#1e293b;border-left:3px solid #4ade80;padding:12px 16px;border-radius:6px;margin-bottom:14px;'>",
        '<div class="ob-tab-intro ob-tab-intro-success">',
    ),
    (
        "<div style='background:#1e293b;border-left:3px solid #fbbf24;padding:12px 16px;border-radius:6px;margin-bottom:14px;'>",
        '<div class="ob-tab-intro ob-tab-intro-warning">',
    ),
    (
        "<div style='background:#1e293b;border-left:3px solid #818cf8;padding:12px 16px;border-radius:6px;margin-bottom:14px;'>",
        '<div class="ob-tab-intro ob-tab-intro-violet">',
    ),
    (
        "<div style='background:#1e293b;border-left:3px solid #fb923c;padding:12px 16px;border-radius:6px;margin-bottom:14px;'>",
        '<div class="ob-tab-intro ob-tab-intro-warning">',
    ),
    (
        "<div style='background:#1e293b;border-left:3px solid #a78bfa;padding:12px 16px;border-radius:6px;margin-bottom:14px;'>",
        '<div class="ob-tab-intro ob-tab-intro-violet">',
    ),
    (
        "<div style='background:#1e293b;border-left:4px solid #f87171;",
        '<div class="ob-tab-intro ob-tab-intro-error">',
    ),
    (
        "<div style='background:#1e293b;border-left:4px solid #4ade80;",
        '<div class="ob-tab-intro ob-tab-intro-success">',
    ),
    (
        "<div style='background:#1e293b;border:1px solid #334155;",
        '<div class="ob-tab-intro ob-tab-intro-neutral">',
    ),
    (
        "<div style='background:#0f172a;border:1px solid #334155;",
        '<div class="ob-tab-intro ob-tab-intro-neutral">',
    ),
]

MISC = [
    ('bgcolor="#0B1120"', 'bgcolor="#F4F6F9"'),
    ('font_color="#F8FAFC"', 'font_color="#1E293B"'),
    ('"color":"#F8FAFC"', '"color":"#1E293B"'),
    (
        "<div style='background:#0D1829;border:1px solid #16243C;border-radius:10px;",
        '<div class="ob-pipeline-step" style="border-radius:10px;',
    ),
]


def main() -> None:
    for p in sorted(PAGES.glob("*.py")):
        text = p.read_text(encoding="utf-8")
        orig = text
        for old, new in CHART + CALLOUTS + MISC:
            text = text.replace(old, new)
        # Lighten inline span colors in callouts
        text = text.replace("color:#38bdf8;", "color:#2563EB;")
        text = text.replace("color:#94a3b8;", "color:#64748B;")
        text = text.replace("color:#94A3B8;", "color:#64748B;")
        if text != orig:
            p.write_text(text, encoding="utf-8")
            print("updated", p.name)


if __name__ == "__main__":
    main()
