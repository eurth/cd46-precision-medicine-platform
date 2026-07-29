"""Fix broken quote nesting from callout migration."""
from __future__ import annotations

import re
from pathlib import Path

PAGES = Path(__file__).resolve().parents[1] / "app" / "pages"

for p in PAGES.glob("*.py"):
    text = p.read_text(encoding="utf-8")
    orig = text
    text = text.replace('f"<div class="ob-tab-intro', 'f\'<div class="ob-tab-intro')
    text = text.replace('"<div class="ob-tab-intro', '\'<div class="ob-tab-intro')
  # drop orphan padding lines after callout open
    text = re.sub(
        r'(\'<div class="ob-tab-intro[^>]+>")\s*\n\s*"padding:[^"]*">',
        r"\1",
        text,
    )
    text = re.sub(
        r"(f'<div class=\"ob-tab-intro[^>]+>')\s*\n\s*f\"padding:[^\"]*\">",
        r"\1",
        text,
    )
    # biomarker evidence card
    text = text.replace(
        '<div class="ob-tab-intro ob-tab-intro-neutral">border-left:4px solid {ev_c};\n'
        "            padding:14px 18px;margin:8px 0;border-radius:6px;'>",
        '<div class="ob-tab-intro ob-tab-intro-neutral" style="border-left:4px solid {ev_c};'
        'padding:14px 18px;margin:8px 0;border-radius:6px;">',
    )
    if text != orig:
        p.write_text(text, encoding="utf-8")
        print("fixed", p.name)
