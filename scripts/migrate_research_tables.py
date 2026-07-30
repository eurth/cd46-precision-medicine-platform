"""Replace read-only st.dataframe with research_table (st.table)."""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAGES = ROOT / "app" / "pages"

SKIP_FILES = {"9_competitive_landscape.py"}  # column_config width control


def _ensure_import(src: str) -> str:
    if re.search(r"from components\.ui_kit import[^\n]*research_table", src):
        return src
    if "from components.ui_kit import" in src:
        return re.sub(
            r"(from components\.ui_kit import [^\n]+)",
            lambda m: m.group(1) + ", research_table"
            if "research_table" not in m.group(1)
            else m.group(1),
            src,
            count=1,
        )
    return "from components.ui_kit import research_table\n" + src


for path in sorted(PAGES.glob("*.py")):
    if path.name in SKIP_FILES:
        continue
    src = path.read_text(encoding="utf-8-sig")
    if "st.dataframe(" not in src:
        continue
    if "column_config" in src:
        # keep st.dataframe only where column_config is used
        new = src
        new = _ensure_import(new)
        if new != src:
            path.write_text(new, encoding="utf-8")
            print("import only", path.name)
        continue
    new = src.replace("st.dataframe(", "research_table(")
    new = _ensure_import(new)
    if new != src:
        path.write_text(new, encoding="utf-8")
        print("updated", path.name)
