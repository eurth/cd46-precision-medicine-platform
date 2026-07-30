"""Verify internal module paths used in navigation + platform overview."""
from __future__ import annotations

import ast
import re
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "app"))

from components.ui_kit import _TITLE_PATHS  # noqa: E402

OVERVIEW = _ROOT / "app" / "pages" / "0_platform_overview.py"
APP = _ROOT / "app" / "streamlit_app.py"

errors: list[str] = []

# All registered navigation pages
nav_pages: set[str] = set()
for m in re.finditer(r'st\.Page\(\s*"([^"]+)"', APP.read_text(encoding="utf-8")):
    p = _ROOT / "app" / m.group(1)
    if not p.exists():
        errors.append(f"navigation missing file: {m.group(1)}")
    nav_pages.add(m.group(1))

# ui_kit title paths
for title, rel in _TITLE_PATHS.items():
    if not (_ROOT / "app" / rel).exists():
        errors.append(f"_TITLE_PATHS missing: {title} -> {rel}")

# overview page= fields
overview_text = OVERVIEW.read_text(encoding="utf-8")
for m in re.finditer(r'"page":\s*"(pages/[^"]+)"', overview_text):
    rel = m.group(1)
    if not (_ROOT / "app" / rel).exists():
        errors.append(f"overview missing: {rel}")
    if rel not in nav_pages:
        errors.append(f"overview not in navigation: {rel}")

# ponytail: no legacy /N_slug hrefs left on overview
if re.search(r'"/\d+_', overview_text):
    errors.append("overview still has legacy /N_slug href paths")

# global_css must be a single style block (link tags leak as visible text in Streamlit)
css = (_ROOT / "app" / "components" / "theme_css.py").read_text(encoding="utf-8")
if "<link rel=" in css and 'return f"""' in css:
    tree = ast.parse(css)
    # crude: forbid <link outside comment
    if "<link rel=" in css.split("<style>")[0].split('return f"""')[-1]:
        errors.append("theme_css: <link> before <style> will leak CSS on live site")

if errors:
    print("FAIL:")
    for e in errors:
        print(" ", e)
    raise SystemExit(1)

print(f"OK: {len(nav_pages)} nav pages, overview links verified")
raise SystemExit(0)
