"""Migrate **_PLOTLY_LAYOUT spread calls to apply_plotly_layout (safe merge)."""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAGES = ROOT / "app" / "pages"

IMPORT_RE = re.compile(r"^from components\.theme import (.+)$", re.M)
LAYOUT_LINE_RE = re.compile(r"^_PLOTLY_LAYOUT = plotly_layout\(\)\s*\n", re.M)
MULTI_RE = re.compile(
    r"(\b\w+)\.update_layout\(\s*\n\s*\*\*_PLOTLY_LAYOUT,\s*\n",
    re.M,
)
SINGLE_RE = re.compile(
    r"(\b\w+)\.update_layout\(\s*\*\*_PLOTLY_LAYOUT,\s*",
)


def _patch_import(src: str) -> str:
    def _repl(m: re.Match[str]) -> str:
        items = [x.strip() for x in m.group(1).split(",")]
        if "apply_plotly_layout" not in items:
            items.append("apply_plotly_layout")
        if "plotly_layout" in items and "_PLOTLY_LAYOUT" not in src:
            # keep plotly_layout only if still referenced
            pass
        return "from components.theme import " + ", ".join(items)

    return IMPORT_RE.sub(_repl, src, count=1)


def _drop_unused_plotly_layout_import(src: str) -> str:
    if "plotly_layout" not in src.replace("apply_plotly_layout", ""):
        return re.sub(r",?\s*plotly_layout", "", src, count=1)
    return src


for path in sorted(PAGES.glob("*.py")):
    src = path.read_text(encoding="utf-8-sig")
    if "_PLOTLY_LAYOUT" not in src:
        continue
    new = src
    new = _patch_import(new)
    new = LAYOUT_LINE_RE.sub("", new)
    new = MULTI_RE.sub(r"apply_plotly_layout(\1,\n", new)
    new = SINGLE_RE.sub(r"apply_plotly_layout(\1, ", new)
    new = _drop_unused_plotly_layout_import(new)
    if new != src:
        path.write_text(new, encoding="utf-8")
        print("updated", path.name)
