"""One-shot: remap legacy dark-theme chart constants to Clinical Slate."""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAGES = ROOT / "app" / "pages"

REPLACEMENTS = [
    (r'_LIGHT\s*=\s*"#CBD5E1"', '_LIGHT  = "#1E293B"'),
    (r'_TEXT\s*=\s*"#94A3B8"', '_TEXT   = "#64748B"'),
    (r'_LINE\s*=\s*"#16243C"', '_LINE   = "#E2E8F0"'),
    (r'_BG\s*=\s*"#0D1829"', '_BG     = "#FFFFFF"'),
    (r'_INDIGO\s*=\s*"#818CF8"', '_INDIGO = "#2563EB"'),
    (r'_MID\s*=\s*"#4E637A"', '_MID    = "#94A3B8"'),
    (r'_SLATE\s*=\s*"#475569"', '_SLATE  = "#94A3B8"'),
    (r'gridcolor="#1e293b"', 'gridcolor="#E2E8F0"'),
    (r'gridcolor="#1E293B"', 'gridcolor="#E2E8F0"'),
    (r'paper_bgcolor="#0D1829"', 'paper_bgcolor="#FFFFFF"'),
    (r'plot_bgcolor="#0D1829"', 'plot_bgcolor="#EEF2F7"'),
    (r'bgcolor="#1e293b"', 'bgcolor="#FFFFFF"'),
    (r'"bgcolor": "#1e293b"', '"bgcolor": "#FFFFFF"'),
]

for p in sorted(PAGES.glob("*.py")):
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
        print("updated", p.name)
