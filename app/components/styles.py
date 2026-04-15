"""
Shared presentation layer — global CSS injection and reusable HTML components.

Usage in any page:
    from components.styles import inject_global_css, page_hero
    inject_global_css()
    st.markdown(page_hero(...), unsafe_allow_html=True)
"""

import streamlit as st


# ---------------------------------------------------------------------------
# Global CSS
# ---------------------------------------------------------------------------

_GLOBAL_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700;800&family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

[data-testid="stApp"],
[data-testid="stAppViewContainer"],
.main .block-container { background: #07101F !important; }

body, p, li, label {
    font-family: 'Inter', -apple-system, sans-serif;
    font-weight: 400; color: #94A3B8;
}
h1, h2, h3, h4, h5, h6, [data-testid="stHeading"] {
    font-family: 'Space Grotesk', -apple-system, sans-serif !important;
    color: #F1F5F9 !important; font-weight: 700 !important;
}
[data-testid="stHeading"] h2 {
    font-size: 18px !important; font-weight: 700 !important;
    color: #CBD5E1 !important; letter-spacing: -0.3px !important;
    margin: 24px 0 10px !important;
}
[data-testid="stHeading"] h3 {
    font-size: 12px !important; font-weight: 700 !important;
    color: #4E637A !important; text-transform: uppercase !important;
    letter-spacing: 0.12em !important;
}

.block-container {
    padding-top: 0 !important; padding-bottom: 3rem !important;
    max-width: 1320px !important;
}
hr { border-color: #16243C !important; }

header[data-testid="stHeader"], footer, #MainMenu,
[data-testid="stToolbar"], div[data-testid="stStatusWidget"],
[data-testid="stDecoration"], [data-testid="stSidebarCollapsedControl"],
button[data-testid="stBaseButton-headerNoPadding"] { display: none !important; }

[data-testid="metric-container"] [data-testid="stMetricValue"] {
    font-size: 28px !important; font-weight: 700 !important;
    color: #F1F5F9 !important; font-family: 'Space Grotesk', sans-serif !important;
}
[data-testid="metric-container"] [data-testid="stMetricLabel"] {
    font-size: 10px !important; font-weight: 600 !important;
    text-transform: uppercase !important; letter-spacing: 0.1em !important;
    color: #4E637A !important;
}
[data-testid="metric-container"] [data-testid="stMetricDelta"] {
    font-size: 12px !important; color: #7A90AB !important;
}

[data-testid="stTabs"] [data-baseweb="tab-list"] {
    background: transparent !important; border-bottom: 1px solid #16243C !important; gap: 0 !important;
}
[data-testid="stTabs"] [data-baseweb="tab"] {
    background: transparent !important; color: #4E637A !important;
    font-size: 13px !important; font-weight: 500 !important;
    border-bottom: 2px solid transparent !important;
    padding: 9px 20px !important; transition: color 0.15s, border-color 0.15s;
}
[data-testid="stTabs"] [aria-selected="true"] {
    color: #F1F5F9 !important; border-bottom: 2px solid #818CF8 !important;
}
[data-testid="stTabs"] [data-baseweb="tab"]:hover { color: #94A3B8 !important; }
[data-testid="stTabsContent"] {
    background: transparent !important; padding-top: 1.25rem !important;
}

[data-testid="stDataFrame"] iframe,
[data-testid="stDataFrame"] > div {
    background: #0D1829 !important; border: 1px solid #16243C !important; border-radius: 8px !important;
}
.dvn-scroller { background: #0D1829 !important; }

[data-testid="stVerticalBlockBorderWrapper"],
div[data-testid="stVerticalBlockBorderWrapper"] {
    border: none !important; border-radius: 10px !important;
    background: #0D1829 !important; box-shadow: none !important;
    transition: background 0.15s !important;
}
[data-testid="stVerticalBlockBorderWrapper"]:hover { background: transparent !important; }
[data-testid="stVerticalBlockBorderWrapper"] > div {
    background: transparent !important; border-radius: 10px !important;
}

/* Equal-height columns */
[data-testid="stHorizontalBlock"] { align-items: stretch !important; }
[data-testid="stColumn"] { display: flex !important; flex-direction: column !important; }
[data-testid="stColumn"] > div { display: flex !important; flex-direction: column !important; flex: 1 !important; }
[data-testid="stColumn"] [data-testid="stVerticalBlockBorderWrapper"] { flex: 1 !important; }

[data-testid="stExpander"] {
    border: 1px solid #16243C !important; border-radius: 8px !important; background: #07101F !important;
}
details[data-testid="stExpander"] > summary { padding: 12px 18px !important; }
details[data-testid="stExpander"] > summary span {
    color: #7A90AB !important; font-size: 13px !important; font-weight: 500 !important;
}

[data-testid="stCaptionContainer"] p { color: #4E637A !important; font-size: 11px !important; }
[data-testid="stAlert"] { background: #0D1829 !important; border-color: #16243C !important; }

[data-testid="stPageLink"] a {
    display: inline-flex !important; align-items: center !important;
    color: #818CF8 !important; font-size: 12px !important; font-weight: 600 !important;
    text-decoration: none !important; border: 1px solid rgba(129,140,248,0.3) !important;
    border-radius: 6px !important; padding: 6px 14px !important;
    margin-top: 8px !important; background: transparent !important;
    transition: all 0.15s !important;
}
[data-testid="stPageLink"] a:hover {
    background: rgba(129,140,248,0.1) !important;
    border-color: rgba(129,140,248,0.65) !important; color: #A5B4FC !important;
}

[data-testid="stSidebar"] {
    background: #040913 !important; border-right: 1px solid #16243C !important;
    min-width: 270px !important; max-width: 270px !important;
}
[data-testid="stSidebar"] .block-container,
[data-testid="stSidebar"] > div:first-child > div { padding: 0 !important; }
[data-testid="stSidebarNav"] { padding-top: 0 !important; padding-bottom: 32px !important; }

[data-testid="stSidebarNavSeparator"] { padding: 22px 0 6px 18px !important; margin: 0 !important; }
[data-testid="stSidebarNavSeparator"] span,
[data-testid="stSidebarNavSeparator"] p {
    font-family: 'Inter', sans-serif !important;
    font-size: 10px !important; font-weight: 700 !important;
    text-transform: uppercase !important; letter-spacing: 0.14em !important;
    color: #4E637A !important;
}

[data-testid="stSidebarNavLink"] {
    border-radius: 0 !important; margin: 0 !important;
    padding: 9px 18px !important; border-left: 3px solid transparent !important;
    width: 100% !important; transition: background 0.12s, border-color 0.12s !important;
}
[data-testid="stSidebarNavLink"] span,
[data-testid="stSidebarNavLink"] p {
    font-family: 'Inter', sans-serif !important;
    font-size: 12.5px !important; font-weight: 500 !important;
    color: #7A90AB !important; line-height: 1.3 !important;
}
[data-testid="stSidebarNavLink"]:hover { background: rgba(129,140,248,0.07) !important; }
[data-testid="stSidebarNavLink"]:hover span,
[data-testid="stSidebarNavLink"]:hover p { color: #CBD5E1 !important; }
[data-testid="stSidebarNavLink"][aria-current="page"] {
    background: rgba(129,140,248,0.12) !important; border-left-color: #818CF8 !important;
}
[data-testid="stSidebarNavLink"][aria-current="page"] span,
[data-testid="stSidebarNavLink"][aria-current="page"] p {
    color: #A5B4FC !important; font-weight: 600 !important;
}

::-webkit-scrollbar { width: 4px; height: 4px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: #16243C; border-radius: 2px; }
::-webkit-scrollbar-thumb:hover { background: #1E3A5F; }

.gene-id {
    font-family: 'JetBrains Mono', 'Courier New', monospace !important;
    color: #818CF8 !important; font-size: 0.88em;
}
.muted { color: #4E637A !important; }
.accent { color: #818CF8 !important; }

#ob-topbar {
    display: flex; align-items: center; gap: 0;
    height: 46px; padding: 0;
    border-bottom: 1px solid #16243C; background: #07101F;
    position: sticky; top: 0; z-index: 999; margin-bottom: 8px;
}
.ob-tb-brand {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 14px; font-weight: 700; color: #F1F5F9;
    letter-spacing: -0.3px; padding: 0 16px;
    border-right: 1px solid #16243C; height: 100%;
    display: flex; align-items: center;
}
.ob-tb-ctx {
    font-family: 'Inter', sans-serif;
    font-size: 12px; color: #4E637A; padding: 0 16px;
}
.ob-tb-spacer { flex: 1; }
.ob-tb-live {
    font-size: 10px; color: #7A90AB;
    display: flex; align-items: center;
    gap: 7px; padding: 0 16px;
    border-left: 1px solid #16243C; height: 100%;
    letter-spacing: 0.08em; text-transform: uppercase; font-weight: 600;
}
.ob-tb-dot {
    width: 7px; height: 7px; border-radius: 50%;
    background: #34D399; display: inline-block; flex-shrink: 0;
}

.lp-eyebrow {
    font-size: 11px; font-weight: 700; letter-spacing: 0.18em;
    text-transform: uppercase; color: #818CF8; display: block; margin-bottom: 14px;
}
.lp-headline {
    font-family: 'Space Grotesk', sans-serif !important;
    font-size: clamp(36px, 4.5vw, 58px) !important;
    font-weight: 800 !important; color: #F1F5F9 !important;
    line-height: 1.04 !important; letter-spacing: -2px !important;
    margin: 0 0 18px !important;
}
.lp-sub {
    font-size: 16px; color: #7A90AB;
    max-width: 640px; line-height: 1.75; margin-bottom: 36px; font-weight: 400;
}
.lp-stats {
    display: flex; flex-wrap: wrap; gap: 0;
    padding: 22px 0; margin-bottom: 48px;
    border-top: 1px solid #16243C; border-bottom: 1px solid #16243C;
}
.lp-stat { flex: 1; min-width: 110px; padding: 0 32px; }
.lp-stat:first-child { padding-left: 0; }
.lp-stat + .lp-stat { border-left: 1px solid #16243C; }
.lp-stat-val {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 30px; font-weight: 800; color: #F1F5F9; line-height: 1;
}
.lp-stat-lbl {
    font-size: 10px; text-transform: uppercase;
    letter-spacing: 0.1em; color: #4E637A; margin-top: 7px; display: block;
}

.lp-sec {
    display: flex; align-items: center; gap: 14px; margin: 48px 0 22px;
}
.lp-sec-txt {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 11px; font-weight: 700;
    text-transform: uppercase; letter-spacing: 0.18em; white-space: nowrap;
}
.lp-sec-line { flex: 1; height: 1px; background: #16243C; }
.lp-sec-ind .lp-sec-txt { color: #818CF8; }
.lp-sec-sky .lp-sec-txt { color: #38BDF8; }
.lp-sec-eme .lp-sec-txt { color: #34D399; }
.lp-sec-amb .lp-sec-txt { color: #FBBF24; }

.mc-wrap { padding: 18px 20px 14px; height: 100%; display: flex; flex-direction: column; }
.mc-ico { font-size: 22px; margin-bottom: 12px; line-height: 1; }
.mc-label {
    font-size: 9px; font-weight: 700; letter-spacing: 0.16em;
    text-transform: uppercase; display: block; margin-bottom: 7px;
}
.mc-label-ind { color: #818CF8; }
.mc-label-sky { color: #38BDF8; }
.mc-label-eme { color: #34D399; }
.mc-label-amb { color: #FBBF24; }
.mc-title {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 15px; font-weight: 700; color: #E2E8F0;
    margin-bottom: 9px; display: block; line-height: 1.3;
}
.mc-desc {
    font-size: 12.5px; color: #7A90AB; line-height: 1.65;
    display: block; flex: 1;
}
.mc-chips {
    display: flex; gap: 8px; flex-wrap: wrap;
    margin-top: 14px; padding-top: 12px; border-top: 1px solid #16243C;
}
.mc-chip {
    font-size: 11px; font-weight: 600; color: #4E637A;
    background: #07101F; padding: 3px 9px; border-radius: 4px;
}

.kf-item {
    font-size: 13px; color: #7A90AB; padding: 7px 0;
    border-bottom: 1px solid #16243C; display: block;
}
.kf-item:last-child { border-bottom: none; }
.kf-item strong { color: #E2E8F0; font-weight: 600; }

/* Image module cards (landing page) */
.mc-img-card {
    border-radius: 12px; overflow: hidden;
    background: #0D1829;
    display: flex; flex-direction: column;
    height: 100%; transition: transform 0.15s, box-shadow 0.15s;
}
.mc-img-card:hover { transform: translateY(-2px); box-shadow: 0 8px 32px rgba(0,0,0,0.4); }
.mc-img-top {
    height: 110px; display: flex; align-items: center; justify-content: center;
    font-size: 42px; position: relative; overflow: hidden; flex-shrink: 0;
}
.mc-img-top-ind { background: linear-gradient(135deg, #1e1e54 0%, #141438 100%); }
.mc-img-top-sky { background: linear-gradient(135deg, #0c2d45 0%, #071c2c 100%); }
.mc-img-top-eme { background: linear-gradient(135deg, #0a2e22 0%, #061c15 100%); }
.mc-img-top-amb { background: linear-gradient(135deg, #2e1f08 0%, #1a1105 100%); }
.mc-img-body { padding: 16px 18px 14px; display: flex; flex-direction: column; flex: 1; }
.mc-img-label {
    font-size: 9px; font-weight: 700; letter-spacing: 0.16em;
    text-transform: uppercase; display: block; margin-bottom: 6px;
}
.mc-img-label-ind { color: #818CF8; }
.mc-img-label-sky { color: #38BDF8; }
.mc-img-label-eme { color: #34D399; }
.mc-img-label-amb { color: #FBBF24; }
.mc-img-title {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 15px; font-weight: 700; color: #E2E8F0;
    margin-bottom: 8px; display: block; line-height: 1.3;
}
.mc-img-desc {
    font-size: 12px; color: #7A90AB; line-height: 1.6;
    display: block; flex: 1; margin-bottom: 12px;
}
.mc-img-chips {
    display: flex; gap: 6px; flex-wrap: wrap;
    padding-top: 10px; border-top: 1px solid #16243C; margin-bottom: 12px;
}
.mc-img-chip {
    font-size: 10px; font-weight: 600; color: #4E637A;
    background: #07101F; padding: 2px 8px; border-radius: 4px;
}
.mc-img-link {
    font-size: 11px; font-weight: 600; color: #818CF8;
    text-decoration: none; letter-spacing: 0.04em;
}
.mc-img-link:hover { color: #A5B4FC; }

.page-hero { padding: 26px 0 20px 0; margin-bottom: 32px; border-bottom: 1px solid #16243C; }
.hero-top { display: flex; align-items: center; gap: 14px; margin-bottom: 5px; }
.hero-icon { font-size: 22px; line-height: 1; flex-shrink: 0; }
.hero-title {
    font-family: 'Space Grotesk', sans-serif !important;
    font-size: 30px !important; font-weight: 800 !important;
    color: #F1F5F9 !important; margin: 0 !important;
    line-height: 1.05 !important; letter-spacing: -0.8px;
}
.hero-purpose { color: #7A90AB; font-size: 14px; margin: 6px 0 18px 36px; line-height: 1.55; }
.hero-chips {
    display: flex; flex-wrap: wrap; margin-left: 36px; gap: 0; margin-bottom: 14px;
}
.hero-chip { background: transparent; border: none; padding: 0; display: flex; align-items: baseline; gap: 6px; }
.hero-chip + .hero-chip { margin-left: 20px; padding-left: 20px; border-left: 1px solid #16243C; }
.chip-val {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 18px; font-weight: 700; color: #E2E8F0; line-height: 1;
}
.chip-lbl { font-size: 11px; color: #4E637A; font-weight: 400; }
.hero-badges { display: flex; flex-wrap: wrap; gap: 0; margin-left: 36px; align-items: center; }
.src-badge {
    display: inline-flex; align-items: center;
    padding: 0 12px 0 0; font-size: 11px;
    color: #4E637A; background: transparent; border: none; font-weight: 500;
}
</style>
"""


def inject_global_css() -> None:
    """Inject platform CSS + top app bar. Call once after set_page_config."""
    st.markdown(_GLOBAL_CSS, unsafe_allow_html=True)
    st.markdown(
        '<div id="ob-topbar">'
        '<span class="ob-tb-brand">🔬 OncoBridge Intelligence</span>'
        '<span class="ob-tb-ctx">CD46 Precision Medicine · EurthTech Research</span>'
        '<span class="ob-tb-spacer"></span>'
        '<span class="ob-tb-live"><span class="ob-tb-dot"></span>Research Data Live</span>'
        '</div>',
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# Page Hero HTML helper
# ---------------------------------------------------------------------------

_BADGE_COLORS = {
    "TCGA":           "#3B82F6",
    "HPA":            "#8B5CF6",
    "DepMap":         "#10B981",
    "ChEMBL":         "#F59E0B",
    "GENIE":          "#EC4899",
    "UniProt":        "#818CF8",
    "STRING":         "#0EA5E9",
    "OpenTargets":    "#22C55E",
    "ClinicalTrials": "#EF4444",
    "cBioPortal":     "#F97316",
    "mCRPC":          "#94A3B8",
    "GTEx":           "#A78BFA",
    "ClinVar":        "#FB7185",
}


def page_hero(
    icon: str,
    module_name: str,
    purpose: str,
    kpi_chips: list[tuple[str, str]],
    source_badges: list[str],
) -> str:
    """Return HTML for the module page hero. All CSS lives in _GLOBAL_CSS."""
    chip_html = ""
    for label, value in kpi_chips:
        chip_html += (
            f'<div class="hero-chip">'
            f'<span class="chip-val">{value}</span>'
            f'<span class="chip-lbl">{label}</span>'
            f'</div>'
        )

    badge_html = ""
    for src in source_badges:
        dot_color = _BADGE_COLORS.get(src, "#4E637A")
        badge_html += (
            f'<span class="src-badge">'
            f'<span style="display:inline-block;width:6px;height:6px;border-radius:50%;'
            f'background:{dot_color};margin-right:5px;flex-shrink:0;"></span>'
            f'{src}</span>'
        )

    return (
        '<div class="page-hero">'
        f'<div class="hero-top">'
        f'<span class="hero-icon">{icon}</span>'
        f'<h1 class="hero-title">{module_name}</h1>'
        f'</div>'
        f'<div class="hero-purpose">{purpose}</div>'
        f'<div class="hero-chips">{chip_html}</div>'
        f'<div class="hero-badges">{badge_html}</div>'
        '</div>'
    )
