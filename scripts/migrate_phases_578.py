"""One-shot migration: theme_css extract, page_header codemod."""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STYLES = ROOT / "app" / "components" / "styles.py"
THEME_CSS = ROOT / "app" / "components" / "theme_css.py"
PAGES = ROOT / "app" / "pages"


def extract_theme_css() -> None:
    text = STYLES.read_text(encoding="utf-8")
    m = re.search(
        r"_GLOBAL_CSS = f\"\"\"(.*)\"\"\"\s*\n\n\ndef inject_global_css",
        text,
        re.DOTALL,
    )
    if not m:
        raise SystemExit("CSS block not found in styles.py")
    css_body = m.group(1)

    extra = """
.ob-crumb { font-size: 12px; color: {TEXT_MUTED}; margin: 0 0 10px 0; }
.ob-crumb-cur { color: {TEXT}; font-weight: 600; }
.ob-recent { font-size: 11px; color: {TEXT_MUTED}; margin-top: 8px; }
.ob-recent-title {
    font-size: 10px; font-weight: 700; text-transform: uppercase;
    letter-spacing: 0.08em; color: {TEXT_FAINT}; margin-bottom: 4px;
}
@media print {
    #ob-topbar, #ob-target-bar, .ob-dim-rail, .ob-crumb, .ob-recent,
    [data-testid="stSidebar"], header[data-testid="stHeader"] { display: none !important; }
    [data-testid="stApp"], .main .block-container { background: #fff !important; }
    .page-hero, .ob-kpi-card, [data-testid="stPlotlyChart"] { break-inside: avoid; }
}
"""
    if ".ob-crumb" not in css_body:
        css_body = css_body.replace("</style>", extra + "</style>")

    theme_css = f'''"""Clinical Slate global CSS (tokens from theme.py)."""
from __future__ import annotations

from components.theme import (
    AMBER,
    BG,
    BORDER,
    BORDER_STRONG,
    GREEN,
    PRIMARY,
    PRIMARY_SOFT,
    PRIMARY_TEXT,
    SIDEBAR_BG,
    SURFACE,
    SURFACE_2,
    TEXT,
    TEXT_FAINT,
    TEXT_MUTED,
    TEXT_SECONDARY,
    TOPBAR_BG,
)


def global_css() -> str:
    return f"""{css_body}"""
'''
    THEME_CSS.write_text(theme_css, encoding="utf-8")

    slim = '''"""
Shared presentation — inject CSS and page hero HTML.
"""
from __future__ import annotations

import streamlit as st

from components.theme import TEXT, TEXT_MUTED
from components.theme_css import global_css

_BADGE_COLORS = {
    "TCGA": "#2563EB", "HPA": "#7C3AED", "DepMap": "#059669", "ChEMBL": "#D97706",
    "GENIE": "#DB2777", "UniProt": "#4F46E5", "STRING": "#0891B2", "OpenTargets": "#16A34A",
    "ClinicalTrials": "#DC2626", "cBioPortal": "#EA580C", "mCRPC": "#64748B",
    "GTEx": "#9333EA", "ClinVar": "#E11D48",
}


def inject_global_css() -> None:
    """Inject platform CSS + top app bar."""
    st.markdown(global_css(), unsafe_allow_html=True)
    st.markdown(
        '<div id="ob-topbar">'
        '<span class="ob-tb-brand">OncoBridge Intelligence</span>'
        '<span class="ob-tb-ctx">Open theranostics research · multi-target workbench</span>'
        '<span class="ob-tb-spacer"></span>'
        '<span class="ob-tb-live"><span class="ob-tb-dot"></span>Research data live</span>'
        '</div>',
        unsafe_allow_html=True,
    )


def page_hero(
    icon: str,
    module_name: str,
    purpose: str,
    kpi_chips: list[tuple[str, str]],
    source_badges: list[str],
) -> str:
    """Return HTML for the module page hero."""
    chip_html = "".join(
        f'<div class="hero-chip"><span class="chip-val">{value}</span>'
        f'<span class="chip-lbl">{label}</span></div>'
        for label, value in kpi_chips
    )
    badge_html = "".join(
        f'<span class="src-badge">'
        f'<span style="display:inline-block;width:6px;height:6px;border-radius:50%;'
        f'background:{_BADGE_COLORS.get(src, TEXT_MUTED)};margin-right:5px;"></span>'
        f'{src}</span>'
        for src in source_badges
    )
    return (
        '<div class="page-hero">'
        f'<div class="hero-top"><span class="hero-icon">{icon}</span>'
        f'<h1 class="hero-title">{module_name}</h1></div>'
        f'<div class="hero-purpose">{purpose}</div>'
        f'<div class="hero-chips">{chip_html}</div>'
        f'<div class="hero-badges">{badge_html}</div>'
        '</div>'
    )
'''
    STYLES.write_text(slim, encoding="utf-8")
    print(f"theme_css.py + slim styles.py ({len(slim.splitlines())} lines)")


def migrate_page_headers() -> None:
    pat = re.compile(
        r"st\.markdown\(\s*page_hero\((.*?)\),\s*unsafe_allow_html=True,\s*\)",
        re.DOTALL,
    )
    for p in sorted(PAGES.glob("*.py")):
        src = p.read_text(encoding="utf-8")
        if "page_hero(" not in src:
            continue
        new_src, n = pat.subn(r"page_header(\1)", src)
        if n == 0:
            print("skip (no match):", p.name)
            continue
        new_src = re.sub(r"from components\.styles import page_hero\n", "", new_src)
        new_src = re.sub(r", page_hero", "", new_src)
        new_src = re.sub(r"page_hero, ", "", new_src)
        if "from components.ui_kit import" in new_src:
            if "page_header" not in new_src:
                new_src = re.sub(
                    r"(from components\.ui_kit import )([^\n]+)",
                    lambda m: f"{m.group(1)}{m.group(2).rstrip()}, page_header"
                    if m.group(2).strip()
                    else f"{m.group(1)}page_header",
                    new_src,
                    count=1,
                )
        else:
            new_src = new_src.replace(
                "import streamlit as st\n",
                "import streamlit as st\nfrom components.ui_kit import page_header\n",
                1,
            )
        p.write_text(new_src, encoding="utf-8")
        print("page_header:", p.name, n)


if __name__ == "__main__":
    extract_theme_css()
    migrate_page_headers()
