"""Remap invisible light-on-light chart colors left from dark-theme migration."""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGETS = [ROOT / "app" / "pages", ROOT / "app" / "components"]

REPLACEMENTS = [
    # invisible axis / title / legend text (grid gray used as ink)
    (r'color="#e2e8f0"', 'color="#64748B"'),
    (r"color='#e2e8f0'", "color='#64748B'"),
    (r'font_color="#e2e8f0"', 'font_color="#64748B"'),
    (r'"color": "#e2e8f0"', '"color": "#1E293B"'),
    (r'"color": "#E2E8F0"', '"color": "#1E293B"'),
    (r'font=dict\(color="#e2e8f0"', 'font=dict(color="#1E293B"'),
    (r"font=dict\(color='#e2e8f0'", "font=dict(color='#1E293B'"),
    (r'title_font=dict\(color="#e2e8f0"', 'title_font=dict(color="#1E293B"'),
    (r'color:#e2e8f0', 'color:#1E293B'),
    (r"color:'#e2e8f0'", "color:'#1E293B'"),
    # bar fills too pale on white
    (r'_SLATE\s*=\s*"#CBD5E1"', '_SLATE  = "#94A3B8"'),
    (r'yaxis=dict\(color="#CBD5E1"', 'yaxis=dict(color="#64748B"'),
    (r'textfont=dict\(color="#CBD5E1"', 'textfont=dict(color="#1E293B"'),
    # white bar labels on white bars
    (r'textfont=dict\(color=_BG', 'textfont=dict(color="#FFFFFF"'),
    # dark-theme legend boxes
    (r'bgcolor="rgba\(13,24,41,0\.9\)"', 'bgcolor="rgba(255,255,255,0.95)"'),
    (r"bgcolor='rgba\(13,24,41,0\.9\)'", "bgcolor='rgba(255,255,255,0.95)'"),
    # fix_chart_palette regression: slate mapped to grid gray
    (r'line=dict\(color=_BG, width=0\.5\)', 'line=dict(color="#D5DEE8", width=0.5)'),
    (r'line=dict\(color=_BG, width=1\)', 'line=dict(color="#D5DEE8", width=1)'),
]

for folder in TARGETS:
    for p in sorted(folder.glob("*.py")):
        src = p.read_text(encoding="utf-8")
        new = src
        changed = False
        for pat, repl in REPLACEMENTS:
            nsrc, n = re.subn(pat, repl, new)
            if n:
                changed = True
                new = nsrc
        if changed:
            p.write_text(new, encoding="utf-8")
            print("updated", p.relative_to(ROOT))
