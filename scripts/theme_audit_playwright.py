"""Playwright theme audit — scans live OncoBridge pages for legacy dark colors."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

# ponytail: optional dep — run `pip install playwright && playwright install chromium`
try:
    from playwright.sync_api import sync_playwright
except ImportError:
    print("Install: pip install playwright && playwright install chromium")
    sys.exit(1)

BASE = sys.argv[1] if len(sys.argv) > 1 else "https://oncobridge.eurthtech.com"
OUT = Path(__file__).resolve().parents[1] / "reports" / "theme_audit.json"

PAGES = [
    "/",
    "/expression_atlas",
    "/compare_targets",
    "/biomarker_panel",
    "/ppi_network",
    "/patient_selection",
    "/drug_pipeline",
    "/survival_outcomes",
    "/biomedical_knowledge_graph",
    "/kg_query_explorer",
]

DARK_PATTERNS = [
    (r"#0[fF]172[aA]", "slate-900 chart/bg"),
    (r"#0[Dd]1829", "legacy navy bg"),
    (r"#1[eE]293[bB]", "slate-800 callout/chart"),
    (r"#07101[fF]", "legacy shell bg"),
    (r"background:\s*#0", "inline dark background"),
]


def audit_page(page, url: str) -> dict:
    page.goto(url, wait_until="networkidle", timeout=90000)
    page.wait_for_timeout(2000)
    html = page.content()
    errors = []
    for el in page.locator('[data-testid="stException"]').all():
        errors.append(el.inner_text()[:500])
    hits = []
    for pat, label in DARK_PATTERNS:
        if re.search(pat, html):
            hits.append(label)
    return {
        "url": url,
        "dark_hits": sorted(set(hits)),
        "errors": errors,
        "title": page.title(),
    }


def main() -> None:
    results = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(viewport={"width": 1440, "height": 900})
        page = ctx.new_page()
        for path in PAGES:
            url = BASE.rstrip("/") + path
            try:
                results.append(audit_page(page, url))
                print("ok", path, "errors=", len(results[-1]["errors"]))
            except Exception as exc:
                results.append({"url": url, "error": str(exc)})
                print("fail", path, exc)
        browser.close()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print("wrote", OUT)


if __name__ == "__main__":
    main()
