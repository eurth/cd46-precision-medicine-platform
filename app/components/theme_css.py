"""Clinical Slate global CSS (tokens from theme.py)."""
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
    ROSE,
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
    return f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600;700&family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

[data-testid="stApp"],
[data-testid="stAppViewContainer"],
.main .block-container {{ background: {BG} !important; }}

body, p, li, label {{
    font-family: 'Inter', -apple-system, sans-serif;
    font-weight: 400; color: {TEXT_SECONDARY};
}}
h1, h2, h3, h4, h5, h6, [data-testid="stHeading"] {{
    font-family: 'IBM Plex Sans', 'Inter', sans-serif !important;
    color: {TEXT} !important; font-weight: 600 !important;
}}
[data-testid="stHeading"] h2 {{
    font-size: 18px !important; font-weight: 600 !important;
    color: {TEXT} !important; letter-spacing: -0.2px !important;
    margin: 24px 0 10px !important;
}}
[data-testid="stHeading"] h3 {{
    font-size: 12px !important; font-weight: 600 !important;
    color: {TEXT_MUTED} !important; text-transform: uppercase !important;
    letter-spacing: 0.1em !important;
}}

.block-container {{
    padding-top: 0 !important; padding-bottom: 3rem !important;
    max-width: 1320px !important;
}}
hr {{ border-color: {BORDER} !important; }}

header[data-testid="stHeader"], footer, #MainMenu,
[data-testid="stToolbar"], div[data-testid="stStatusWidget"],
[data-testid="stDecoration"], [data-testid="stSidebarCollapsedControl"],
button[data-testid="stBaseButton-headerNoPadding"] {{ display: none !important; }}

/* KPI cards */
.ob-kpi-card {{
    background: {SURFACE}; border: 1px solid {BORDER}; border-radius: 10px;
    padding: 14px 16px; height: 100%; box-shadow: 0 1px 2px rgba(15,23,42,0.04);
}}
.ob-kpi-title {{
    font-size: 10px; font-weight: 600; letter-spacing: 0.08em;
    text-transform: uppercase; color: {TEXT_MUTED}; margin-bottom: 6px;
}}
.ob-kpi-value {{
    font-family: 'IBM Plex Sans', sans-serif;
    font-size: 26px; font-weight: 700; color: {TEXT}; line-height: 1.1;
}}
.ob-kpi-desc {{ font-size: 12px; color: {TEXT_FAINT}; margin-top: 4px; line-height: 1.35; }}

.ob-banner {{
    border: 1px solid {BORDER}; border-radius: 8px; padding: 12px 16px;
    font-size: 14px; line-height: 1.55; margin: 12px 0;
}}

[data-testid="metric-container"] [data-testid="stMetricValue"] {{
    font-size: 26px !important; font-weight: 700 !important;
    color: {TEXT} !important; font-family: 'IBM Plex Sans', sans-serif !important;
}}
[data-testid="metric-container"] [data-testid="stMetricLabel"] {{
    font-size: 10px !important; font-weight: 600 !important;
    text-transform: uppercase !important; letter-spacing: 0.08em !important;
    color: {TEXT_MUTED} !important;
}}
[data-testid="metric-container"] [data-testid="stMetricDelta"] {{
    font-size: 12px !important; color: {TEXT_FAINT} !important;
}}

/* Section tabs (horizontal radio) */
[data-testid="stRadio"] > div[role="radiogroup"] {{
    gap: 4px !important; flex-wrap: wrap !important;
    border-bottom: 1px solid {BORDER}; padding-bottom: 2px; margin-bottom: 8px;
}}
[data-testid="stRadio"] label {{
    background: transparent !important; border: none !important;
    padding: 8px 14px !important; margin: 0 !important;
    font-size: 13px !important; font-weight: 500 !important;
    color: {TEXT_MUTED} !important;
    border-bottom: 2px solid transparent !important;
    border-radius: 0 !important;
}}
[data-testid="stRadio"] label:has(input:checked) {{
    color: {PRIMARY} !important; font-weight: 600 !important;
    border-bottom-color: {PRIMARY} !important;
    background: {PRIMARY_SOFT} !important;
    border-radius: 6px 6px 0 0 !important;
}}
[data-testid="stRadio"] label span[data-testid="stMarkdownContainer"] {{
    font-size: 13px !important;
}}

[data-testid="stTabs"] [data-baseweb="tab-list"] {{
    background: transparent !important; border-bottom: 1px solid {BORDER} !important;
}}
[data-testid="stTabs"] [data-baseweb="tab"] {{
    background: transparent !important; color: {TEXT_MUTED} !important;
    font-size: 13px !important; font-weight: 500 !important;
    border-bottom: 2px solid transparent !important;
    padding: 9px 18px !important;
}}
[data-testid="stTabs"] [aria-selected="true"] {{
    color: {PRIMARY} !important; border-bottom: 2px solid {PRIMARY} !important;
}}

[data-testid="stDataFrame"] iframe,
[data-testid="stDataFrame"] > div {{
    background: {SURFACE} !important; border: 1px solid {BORDER} !important;
    border-radius: 8px !important;
}}
.dvn-scroller {{ background: {SURFACE} !important; }}

[data-testid="stVerticalBlockBorderWrapper"] {{
    border: 1px solid {BORDER} !important; border-radius: 10px !important;
    background: {SURFACE} !important; box-shadow: 0 1px 2px rgba(15,23,42,0.04) !important;
}}

[data-testid="stExpander"] {{
    border: 1px solid {BORDER} !important; border-radius: 8px !important;
    background: {SURFACE} !important;
}}
details[data-testid="stExpander"] > summary span {{
    color: {TEXT_SECONDARY} !important; font-size: 13px !important;
}}

[data-testid="stCaptionContainer"] p {{ color: {TEXT_MUTED} !important; font-size: 12px !important; }}
[data-testid="stAlert"] {{
    background: {SURFACE} !important; border-color: {BORDER} !important; color: {TEXT_SECONDARY} !important;
}}

[data-testid="stSidebar"] {{
    background: {SIDEBAR_BG} !important; border-right: 1px solid {BORDER} !important;
    min-width: 270px !important; max-width: 270px !important;
    box-shadow: 1px 0 0 rgba(15,23,42,0.04);
}}
[data-testid="stSidebarNavSeparator"] span,
[data-testid="stSidebarNavSeparator"] p {{
    font-size: 10px !important; font-weight: 700 !important;
    text-transform: uppercase !important; letter-spacing: 0.12em !important;
    color: {TEXT_FAINT} !important;
}}
[data-testid="stSidebarNavLink"] {{
    border-radius: 6px !important; margin: 1px 8px !important;
    padding: 8px 12px !important; border-left: none !important;
}}
[data-testid="stSidebarNavLink"] span,
[data-testid="stSidebarNavLink"] p {{
    font-size: 13px !important; color: {TEXT_SECONDARY} !important;
}}
[data-testid="stSidebarNavLink"]:hover {{ background: {SURFACE_2} !important; }}
[data-testid="stSidebarNavLink"][aria-current="page"] {{
    background: {PRIMARY_SOFT} !important;
}}
[data-testid="stSidebarNavLink"][aria-current="page"] span,
[data-testid="stSidebarNavLink"][aria-current="page"] p {{
    color: {PRIMARY_TEXT} !important; font-weight: 600 !important;
}}

::-webkit-scrollbar {{ width: 6px; height: 6px; }}
::-webkit-scrollbar-thumb {{ background: {BORDER_STRONG}; border-radius: 3px; }}

.gene-id {{
    font-family: 'JetBrains Mono', monospace !important;
    color: {PRIMARY} !important; font-size: 0.88em;
}}

#ob-topbar {{
    display: flex; align-items: center; height: 46px;
    border-bottom: 1px solid {BORDER}; background: {TOPBAR_BG};
    position: sticky; top: 0; z-index: 999; margin-bottom: 8px;
    box-shadow: 0 1px 0 rgba(15,23,42,0.04);
}}
.ob-tb-brand {{
    font-family: 'IBM Plex Sans', sans-serif;
    font-size: 14px; font-weight: 700; color: {TEXT};
    padding: 0 16px; border-right: 1px solid {BORDER}; height: 100%;
    display: flex; align-items: center;
}}
.ob-tb-ctx {{ font-size: 12px; color: {TEXT_MUTED}; padding: 0 16px; }}
.ob-tb-spacer {{ flex: 1; }}
.ob-tb-live {{
    font-size: 10px; color: {TEXT_MUTED}; display: flex; align-items: center;
    gap: 7px; padding: 0 16px; border-left: 1px solid {BORDER}; height: 100%;
    letter-spacing: 0.06em; text-transform: uppercase; font-weight: 600;
}}
.ob-tb-dot {{
    width: 7px; height: 7px; border-radius: 50%;
    background: {GREEN}; display: inline-block;
}}

#ob-target-bar {{
    position: sticky; top: 46px; z-index: 998;
    background: {SURFACE}; border: 1px solid {BORDER}; border-radius: 10px;
    padding: 10px 14px 6px; margin-bottom: 14px;
    box-shadow: 0 1px 3px rgba(15,23,42,0.06);
}}
.ob-tb-label {{
    font-size: 10px; letter-spacing: 0.08em; text-transform: uppercase;
    color: {TEXT_MUTED}; font-weight: 600; margin-bottom: 4px;
}}
.ob-tb-meta {{ font-size: 12px; color: {TEXT_SECONDARY}; line-height: 1.45; padding-top: 4px; }}
.ob-tb-meta strong {{ color: {TEXT}; font-size: 13px; }}
.ob-tb-tier {{
    display: inline-block; margin-top: 2px; padding: 1px 8px; border-radius: 4px;
    background: {PRIMARY_SOFT}; color: {PRIMARY_TEXT}; font-size: 11px; font-weight: 600;
}}
.ob-tb-ens {{ font-family: 'JetBrains Mono', monospace; font-size: 11px; color: {TEXT_MUTED}; }}

.ob-side-target {{
    padding: 10px 14px; margin: 8px 8px 4px;
    border: 1px solid {BORDER}; border-radius: 8px; background: {SURFACE_2};
}}
.ob-side-target-kicker {{
    font-size: 9px; letter-spacing: 0.1em; text-transform: uppercase;
    color: {TEXT_MUTED}; font-weight: 600;
}}
.ob-side-target-sym {{
    font-family: 'IBM Plex Sans', sans-serif;
    font-size: 18px; font-weight: 700; color: {TEXT}; margin: 2px 0;
}}
.ob-side-target-sub {{ font-size: 11px; color: {TEXT_MUTED}; }}

.ob-dim-rail {{
    margin: 0 0 10px 0; padding-bottom: 6px; border-bottom: 1px solid {BORDER};
}}
.ob-dim-rail-label {{
    font-size: 10px; font-weight: 600; letter-spacing: 0.08em;
    text-transform: uppercase; color: {TEXT_FAINT}; display: block; margin-bottom: 6px;
}}
[data-testid="stPageLink-NavLink"] {{
    font-size: 12px !important; font-weight: 500 !important;
    padding: 4px 8px !important; border-radius: 6px !important;
    border: 1px solid {BORDER} !important; background: {SURFACE} !important;
    color: {TEXT_SECONDARY} !important; text-align: center !important;
}}
[data-testid="stPageLink-NavLink"]:hover {{
    border-color: {PRIMARY} !important; color: {PRIMARY} !important;
    background: {PRIMARY_SOFT} !important;
}}
@media (max-width: 768px) {{
    .ob-dim-rail {{ display: none !important; }}
}}

.lp-headline {{
    font-family: 'IBM Plex Sans', sans-serif !important;
    font-size: clamp(32px, 4vw, 52px) !important;
    font-weight: 700 !important; color: {TEXT} !important;
    line-height: 1.08 !important; letter-spacing: -1px !important;
    margin: 0 0 16px !important;
}}
.lp-sub {{
    font-size: 16px; color: {TEXT_SECONDARY};
    max-width: 640px; line-height: 1.7; margin-bottom: 28px;
}}

.lp-sec {{ display: flex; align-items: center; gap: 14px; margin: 40px 0 18px; }}
.lp-sec-txt {{
    font-size: 11px; font-weight: 700; text-transform: uppercase;
    letter-spacing: 0.14em; white-space: nowrap;
}}
.lp-sec-line {{ flex: 1; height: 1px; background: {BORDER}; }}
.lp-sec-ind .lp-sec-txt {{ color: {PRIMARY}; }}
.lp-sec-sky .lp-sec-txt {{ color: #0284C7; }}
.lp-sec-eme .lp-sec-txt {{ color: {GREEN}; }}
.lp-sec-amb .lp-sec-txt {{ color: {AMBER}; }}

.mc-img-card {{
    border-radius: 12px; overflow: hidden; background: {SURFACE};
    border: 1px solid {BORDER}; display: flex; flex-direction: column; height: 100%;
    box-shadow: 0 1px 3px rgba(15,23,42,0.06);
    transition: box-shadow 0.15s, transform 0.15s;
}}
.mc-img-card:hover {{
    transform: translateY(-1px); box-shadow: 0 4px 12px rgba(15,23,42,0.08);
}}
.mc-img-top {{
    height: 100px; display: flex; align-items: center; justify-content: center;
    font-size: 38px; flex-shrink: 0;
}}
.mc-img-top-ind {{ background: linear-gradient(135deg, #DBEAFE 0%, #EFF6FF 100%); }}
.mc-img-top-sky {{ background: linear-gradient(135deg, #E0F2FE 0%, #F0F9FF 100%); }}
.mc-img-top-eme {{ background: linear-gradient(135deg, #D1FAE5 0%, #ECFDF5 100%); }}
.mc-img-top-amb {{ background: linear-gradient(135deg, #FEF3C7 0%, #FFFBEB 100%); }}
.mc-img-body {{ padding: 16px 18px 14px; display: flex; flex-direction: column; flex: 1; }}
.mc-img-label {{
    font-size: 9px; font-weight: 700; letter-spacing: 0.14em;
    text-transform: uppercase; margin-bottom: 6px;
}}
.mc-img-label-ind {{ color: {PRIMARY}; }}
.mc-img-label-sky {{ color: #0284C7; }}
.mc-img-label-eme {{ color: {GREEN}; }}
.mc-img-label-amb {{ color: {AMBER}; }}
.mc-img-title {{
    font-family: 'IBM Plex Sans', sans-serif;
    font-size: 15px; font-weight: 600; color: {TEXT};
    margin-bottom: 8px; line-height: 1.3;
}}
.mc-img-desc {{ font-size: 12px; color: {TEXT_SECONDARY}; line-height: 1.55; flex: 1; margin-bottom: 12px; }}
.mc-img-chips {{
    display: flex; gap: 6px; flex-wrap: wrap;
    padding-top: 10px; border-top: 1px solid {BORDER}; margin-bottom: 12px;
}}
.mc-img-chip {{
    font-size: 10px; font-weight: 600; color: {TEXT_MUTED};
    background: {SURFACE_2}; padding: 2px 8px; border-radius: 4px;
}}
.mc-img-link {{ font-size: 12px; font-weight: 600; color: {PRIMARY}; text-decoration: none; }}
.mc-img-link:hover {{ color: {PRIMARY_TEXT}; }}

.page-hero {{
    padding: 20px 0 16px; margin-bottom: 20px;
    border-bottom: 1px solid {BORDER}; background: transparent;
}}
.hero-top {{ display: flex; align-items: center; gap: 12px; margin-bottom: 4px; }}
.hero-icon {{ font-size: 22px; line-height: 1; }}
.hero-title {{
    font-family: 'IBM Plex Sans', sans-serif !important;
    font-size: 28px !important; font-weight: 700 !important;
    color: {TEXT} !important; margin: 0 !important; letter-spacing: -0.5px;
}}
.hero-purpose {{ color: {TEXT_SECONDARY}; font-size: 14px; margin: 4px 0 14px 34px; line-height: 1.55; }}
.hero-chips {{
    display: flex; flex-wrap: wrap; margin-left: 34px; gap: 0; margin-bottom: 10px;
}}
.hero-chip {{ display: flex; align-items: baseline; gap: 6px; padding: 0; }}
.hero-chip + .hero-chip {{ margin-left: 18px; padding-left: 18px; border-left: 1px solid {BORDER}; }}
.chip-val {{
    font-family: 'IBM Plex Sans', sans-serif;
    font-size: 17px; font-weight: 700; color: {TEXT};
}}
.chip-lbl {{ font-size: 11px; color: {TEXT_MUTED}; }}
.hero-badges {{ display: flex; flex-wrap: wrap; margin-left: 34px; align-items: center; }}
.src-badge {{
    display: inline-flex; align-items: center; padding: 0 12px 0 0;
    font-size: 11px; color: {TEXT_MUTED}; font-weight: 500;
}}

@media (max-width: 768px) {{
    header[data-testid="stHeader"] {{
        display: flex !important; background: {TOPBAR_BG} !important;
    }}
    [data-testid="stSidebarCollapsedControl"],
    button[data-testid="stBaseButton-headerNoPadding"] {{ display: flex !important; }}
    .block-container {{ padding-left: 1rem !important; padding-right: 1rem !important; }}
    .ob-tb-ctx, .ob-tb-live {{ display: none !important; }}
    .ob-tb-brand {{ border-right: 0; padding-left: 3rem; }}
}}

.ob-crumb {{ font-size: 12px; color: {TEXT_MUTED}; margin: 0 0 10px 0; }}
.ob-crumb-cur {{ color: {TEXT}; font-weight: 600; }}
.ob-recent {{ font-size: 11px; color: {TEXT_MUTED}; margin-top: 8px; }}
.ob-recent-title {{
    font-size: 10px; font-weight: 700; text-transform: uppercase;
    letter-spacing: 0.08em; color: {TEXT_FAINT}; margin-bottom: 4px;
}}

/* Tab / section intros (replaces dark #1e293b callouts) */
.ob-tab-intro {{
    padding: 12px 16px; border-radius: 6px; margin-bottom: 14px;
    font-size: 14px; line-height: 1.55;
}}
.ob-tab-intro-info {{ background: #EFF6FF; border-left: 3px solid {PRIMARY}; color: {PRIMARY_TEXT}; }}
.ob-tab-intro-success {{ background: #ECFDF5; border-left: 3px solid {GREEN}; color: #065F46; }}
.ob-tab-intro-warning {{ background: #FFFBEB; border-left: 3px solid {AMBER}; color: #92400E; }}
.ob-tab-intro-violet {{ background: #F5F3FF; border-left: 3px solid #7C3AED; color: #5B21B6; }}
.ob-tab-intro-error {{ background: #FEF2F2; border-left: 4px solid {ROSE}; color: #991B1B; padding: 12px 16px; border-radius: 6px; margin-bottom: 14px; }}
.ob-tab-intro-neutral {{ background: {SURFACE}; border: 1px solid {BORDER}; color: {TEXT_SECONDARY}; padding: 12px 16px; border-radius: 6px; }}

/* Research target segmented bar — uniform light chips */
#ob-target-bar .ant-segmented {{
    background: {SURFACE_2} !important; padding: 3px !important;
    border-radius: 8px !important; border: 1px solid {BORDER} !important;
}}
#ob-target-bar .ant-segmented-item {{
    color: {TEXT_SECONDARY} !important; background: transparent !important;
    font-weight: 500 !important;
}}
#ob-target-bar .ant-segmented-item-selected {{
    background: {SURFACE} !important; color: {PRIMARY} !important;
    font-weight: 600 !important;
    box-shadow: 0 1px 2px rgba(15,23,42,0.08) !important;
}}
#ob-target-bar [data-baseweb="button-group"] button {{
    background: transparent !important; color: {TEXT_SECONDARY} !important;
    border-color: {BORDER} !important;
}}
#ob-target-bar [data-baseweb="button-group"] button[aria-pressed="true"] {{
    background: {PRIMARY_SOFT} !important; color: {PRIMARY} !important;
    border-color: {PRIMARY} !important;
}}

/* Filter expander header — light, not dark */
details[data-testid="stExpander"] > summary {{
    background: {SURFACE_2} !important; border-radius: 6px !important;
}}
details[data-testid="stExpander"] > summary span {{
    color: {TEXT_SECONDARY} !important;
}}

/* Case-study pipeline stepper (overview) */
.ob-pipeline-wrap {{ margin: 40px 0 28px; border-top: 1px solid {BORDER}; padding-top: 36px; }}
.ob-pipeline-label {{
    font-family: 'IBM Plex Sans', sans-serif; font-size: 11px; font-weight: 700;
    letter-spacing: 0.14em; text-transform: uppercase; color: {TEXT_MUTED}; margin-bottom: 20px;
}}
.ob-pipeline-step {{
    background: {SURFACE}; border-radius: 8px; padding: 16px 14px;
    border: 1px solid {BORDER}; height: 100%; box-sizing: border-box;
    box-shadow: 0 1px 2px rgba(15,23,42,0.04);
}}
.ob-pipeline-step-title {{ font-size: 10px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.1em; margin-bottom: 6px; }}
.ob-pipeline-step-detail {{ font-size: 11.5px; color: {TEXT_MUTED}; line-height: 1.5; }}
.ob-pipeline-arrow {{ color: {TEXT_FAINT}; font-size: 18px; padding: 0 6px; align-self: center; flex-shrink: 0; }}

@media print {{
    #ob-topbar, #ob-target-bar, .ob-dim-rail, .ob-crumb, .ob-recent,
    [data-testid="stSidebar"], header[data-testid="stHeader"] {{ display: none !important; }}
    [data-testid="stApp"], .main .block-container {{ background: #fff !important; }}
    .page-hero, .ob-kpi-card, [data-testid="stPlotlyChart"] {{ break-inside: avoid; }}
}}
</style>
"""
