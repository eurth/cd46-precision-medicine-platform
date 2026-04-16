"""Playwright audit script — oncobridge.eurthtech.com
Navigates to every known page, captures:
  - Full-page screenshot
  - Any visible red error boxes (Streamlit exception traceback divs)
  - Any blank/empty chart containers
  - Page load time
  - Console errors

Run: .venv/Scripts/python scripts/audit_site.py
Output: reports/audit/  (screenshots + audit_report.json)
"""
import json
import re
import time
from datetime import datetime
from pathlib import Path

from playwright.sync_api import sync_playwright

BASE_URL = "https://oncobridge.eurthtech.com"

# All known Streamlit pages (path suffix)
PAGES = [
    {"id": "overview",      "path": "/",                                "label": "Platform Overview"},
    {"id": "p1_atlas",      "path": "/cd46_expression_atlas",           "label": "Expression Atlas"},
    {"id": "p2_selection",  "path": "/patient_selection",               "label": "Patient Selection"},
    {"id": "p3_survival",   "path": "/survival_outcomes",               "label": "Survival Outcomes"},
    {"id": "p4_kg",         "path": "/biomedical_knowledge_graph",      "label": "Knowledge Graph"},
    {"id": "p5_assistant",  "path": "/research_assistant",              "label": "Research Assistant"},
    {"id": "p6_biomarker",  "path": "/biomarker_panel",                 "label": "Biomarker Panel"},
    {"id": "p7_kgquery",    "path": "/kg_query_explorer",               "label": "KG Query Explorer"},
    {"id": "p8_eligibility","path": "/patient_eligibility",             "label": "Patient Eligibility (old)"},
    {"id": "p9_competitive","path": "/competitive_landscape",           "label": "Competitive Landscape"},
    {"id": "p10_ppi",       "path": "/ppi_network",                     "label": "PPI Network"},
    {"id": "p11_drug",      "path": "/drug_pipeline",                   "label": "Drug Pipeline"},
    {"id": "p12_dosimetry", "path": "/dosimetry_safety",                "label": "Dosimetry & Safety"},
    {"id": "p13_clinical",  "path": "/clinical_strategy_engine",        "label": "Clinical Strategy Engine"},
    {"id": "p14_diagnostics","path": "/cd46_diagnostics",               "label": "CD46 Diagnostics"},
    # Clinical Tools
    {"id": "pt_eligibility","path": "/eligibility_scorer",              "label": "Eligibility Scorer"},
    {"id": "pt_competitive","path": "/competitive_landscape",           "label": "Competitive Landscape (clinical tools)"},
]

# Streamlit error selectors
ERROR_SELECTORS = [
    "div[data-testid='stException']",
    ".stException",
    "div.element-container div[class*='exception']",
    "pre.exception",
]

# Empty/blank chart indicators
EMPTY_CHART_SELECTORS = [
    "div[data-testid='stPlotlyChart']:empty",
    ".js-plotly-plot:not([data-full-initialized])",
]

OUTPUT_DIR = Path(__file__).parent.parent / "reports" / "audit"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def extract_error_text(page) -> list[dict]:
    """Extract all Streamlit exception/traceback blocks from the page."""
    errors = []
    for sel in ERROR_SELECTORS:
        try:
            elements = page.query_selector_all(sel)
            for el in elements:
                text = el.inner_text().strip()
                if text:
                    # Try to get the error type on the first line
                    first_line = text.split("\n")[0][:200]
                    errors.append({"selector": sel, "summary": first_line, "full": text[:1000]})
        except Exception:
            pass
    return errors


def check_empty_charts(page) -> list[str]:
    """Return list of chart containers that appear empty or have zero dimensions."""
    issues = []
    try:
        charts = page.query_selector_all("div[data-testid='stPlotlyChart']")
        for i, chart in enumerate(charts):
            bb = chart.bounding_box()
            if bb and (bb["width"] < 50 or bb["height"] < 50):
                issues.append(f"Chart #{i+1} appears too small: {bb['width']:.0f}×{bb['height']:.0f}px")
    except Exception as e:
        issues.append(f"Chart check failed: {e}")
    return issues


def check_blank_expanders_and_tabs(page) -> list[str]:
    """Detect blank/collapsed tab contents."""
    blanks = []
    try:
        # Look for tab panels
        tab_panels = page.query_selector_all("div[data-baseweb='tab-panel']")
        for i, panel in enumerate(tab_panels):
            text = panel.inner_text().strip()
            if len(text) < 20:
                blanks.append(f"Tab panel #{i+1} appears empty (text len={len(text)})")
    except Exception:
        pass
    return blanks


def check_dataframes(page) -> list[str]:
    """Check for completely empty dataframe containers."""
    empty = []
    try:
        dfs = page.query_selector_all("div[data-testid='stDataFrame']")
        for i, df in enumerate(dfs):
            bb = df.bounding_box()
            if bb and bb["height"] < 30:
                empty.append(f"DataFrame #{i+1} appears empty/zero height: {bb['height']:.0f}px")
    except Exception:
        pass
    return empty


def count_metrics(page) -> int:
    try:
        return len(page.query_selector_all("div[data-testid='stMetric']"))
    except Exception:
        return -1


def count_charts(page) -> int:
    try:
        return len(page.query_selector_all("div[data-testid='stPlotlyChart']"))
    except Exception:
        return -1


def count_tabs(page) -> int:
    try:
        return len(page.query_selector_all("button[role='tab']"))
    except Exception:
        return -1


def audit_page(page, page_info: dict) -> dict:
    url = BASE_URL + page_info["path"]
    result = {
        "id": page_info["id"],
        "label": page_info["label"],
        "url": url,
        "load_time_s": None,
        "status": "unknown",
        "errors": [],
        "empty_charts": [],
        "blank_tab_panels": [],
        "empty_dataframes": [],
        "console_errors": [],
        "metrics_count": 0,
        "charts_count": 0,
        "tabs_count": 0,
        "screenshot": None,
    }

    console_errs = []

    def on_console(msg):
        if msg.type in ("error", "warning"):
            console_errs.append({"type": msg.type, "text": msg.text[:300]})

    page.on("console", on_console)

    t0 = time.time()
    try:
        page.goto(url, timeout=30000, wait_until="networkidle")
    except Exception as e:
        try:
            page.goto(url, timeout=30000, wait_until="domcontentloaded")
        except Exception as e2:
            result["status"] = f"LOAD_FAILED: {e2}"
            return result

    # Wait a bit for Streamlit to render
    try:
        page.wait_for_selector("div[data-testid='stApp']", timeout=15000)
    except Exception:
        pass
    time.sleep(3)  # extra render time for charts

    result["load_time_s"] = round(time.time() - t0, 2)

    # Screenshot
    screenshot_path = OUTPUT_DIR / f"{page_info['id']}.png"
    try:
        page.screenshot(path=str(screenshot_path), full_page=True)
        result["screenshot"] = str(screenshot_path)
    except Exception as e:
        result["screenshot"] = f"FAILED: {e}"

    # Checks
    result["errors"] = extract_error_text(page)
    result["empty_charts"] = check_empty_charts(page)
    result["blank_tab_panels"] = check_blank_expanders_and_tabs(page)
    result["empty_dataframes"] = check_dataframes(page)
    result["console_errors"] = console_errs[:20]
    result["metrics_count"] = count_metrics(page)
    result["charts_count"] = count_charts(page)
    result["tabs_count"] = count_tabs(page)

    if result["errors"]:
        result["status"] = "ERROR"
    elif result["empty_charts"] or result["empty_dataframes"]:
        result["status"] = "PARTIAL"
    else:
        result["status"] = "OK"

    page.remove_listener("console", on_console)
    return result


def run_audit():
    print(f"Starting audit — {datetime.now().isoformat()}")
    all_results = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1400, "height": 900})
        page = context.new_page()

        seen_paths = set()
        for pg in PAGES:
            if pg["path"] in seen_paths:
                continue
            seen_paths.add(pg["path"])

            print(f"  → Auditing: {pg['label']} ({pg['path']})")
            result = audit_page(page, pg)
            all_results.append(result)

            status_icon = "✅" if result["status"] == "OK" else "❌" if result["status"] == "ERROR" else "⚠️"
            print(f"    {status_icon} {result['status']} — {result['load_time_s']}s | "
                  f"charts={result['charts_count']} metrics={result['metrics_count']} "
                  f"tabs={result['tabs_count']} errors={len(result['errors'])}")
            if result["errors"]:
                for e in result["errors"]:
                    print(f"       ERROR: {e['summary']}")

        browser.close()

    # Save JSON
    report_path = OUTPUT_DIR / "audit_results.json"
    with open(report_path, "w") as f:
        json.dump(all_results, f, indent=2)
    print(f"\nAudit complete. Results saved to {report_path}")
    print(f"Screenshots in: {OUTPUT_DIR}")
    return all_results


if __name__ == "__main__":
    results = run_audit()

    # Quick summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    errors = [r for r in results if r["status"] == "ERROR"]
    partials = [r for r in results if r["status"] == "PARTIAL"]
    ok = [r for r in results if r["status"] == "OK"]
    print(f"  ✅ OK:      {len(ok)}")
    print(f"  ⚠️  PARTIAL: {len(partials)}")
    print(f"  ❌ ERROR:   {len(errors)}")
    for r in errors + partials:
        print(f"\n  [{r['status']}] {r['label']}")
        for e in r["errors"]:
            print(f"    • {e['summary']}")
        for c in r["empty_charts"]:
            print(f"    • EMPTY CHART: {c}")
        for d in r["empty_dataframes"]:
            print(f"    • EMPTY DF: {d}")
