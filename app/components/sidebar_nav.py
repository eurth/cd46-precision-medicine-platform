"""Sidebar nav — expand active section once; avoid click-thrash layout flicker."""
from __future__ import annotations

import json

import streamlit.components.v1 as components

# Must match st.navigation dict keys (excludes hidden admin group)
NAV_SECTIONS: tuple[str, ...] = (
    "Home",
    "Target / Cancer",
    "Biomarkers",
    "Proteins",
    "Patients",
    "Drugs / Safety",
    "Survival",
    "Graph / Ask",
    "Strategy",
)

PAGE_TO_SECTION: dict[str, str] = {
    "Platform Overview": "Home",
    "Expression Atlas": "Target / Cancer",
    "Compare Targets": "Target / Cancer",
    "Biomarker Panel": "Biomarkers",
    "PPI Network Explorer": "Proteins",
    "Diagnostics & Early Detection": "Proteins",
    "Patient Selection": "Patients",
    "Eligibility Scorer": "Patients",
    "Drug Pipeline": "Drugs / Safety",
    "Dosimetry & Safety Index": "Drugs / Safety",
    "Survival Outcomes": "Survival",
    "Knowledge Graph": "Graph / Ask",
    "KG Query Explorer": "Graph / Ask",
    "Research Assistant": "Graph / Ask",
    "Clinical Strategy Engine": "Strategy",
}


def inject_sidebar_nav_defaults(current_page: str | None) -> None:
    """Expand the section for the current page; collapse others once.

    Previous interval clicked every open section header for ~4.5s after paint,
    which thrashed layout on deep-link refresh (formatting flicker / 'Streamlit'
    chrome flash). One-shot apply after nav mounts.
    """
    active = PAGE_TO_SECTION.get(current_page or "", "Home")
    active_js = json.dumps(active)
    # ponytail: st.components.v1.html → migrate to st.iframe when Streamlit drops html()
    components.html(
        f"""
<script>
(function () {{
  const win = window.parent;
  const doc = win.document;
  const activeSection = {active_js};
  const FLAG = "__ob_nav_applied__";

  function headerLabel(header) {{
    return (header.textContent || "").replace(/\\s+/g, " ").trim();
  }}

  function sectionExpanded(section) {{
    if (!section) return false;
    if (section.getAttribute("aria-expanded") === "true") return true;
    if (section.getAttribute("aria-expanded") === "false") return false;
    // Fallback: visible nav links under this section
    const link = section.querySelector('[data-testid="stSidebarNavLink"]');
    if (!link) return false;
    const style = win.getComputedStyle(link);
    return style && style.display !== "none" && style.visibility !== "hidden";
  }}

  function applyOnce() {{
    if (win[FLAG]) return true;
    const nav = doc.querySelector('[data-testid="stSidebarNav"]');
    if (!nav) return false;
    const headers = nav.querySelectorAll('[data-testid="stNavSectionHeader"]');
    if (!headers.length) return false;

    headers.forEach((header) => {{
      const name = headerLabel(header);
      const section = header.parentElement;
      const wantOpen = name === activeSection;
      const isOpen = sectionExpanded(section);
      if (wantOpen !== isOpen) {{
        try {{ header.click(); }} catch (e) {{}}
      }}
    }});
    win[FLAG] = true;
    return true;
  }}

  let tries = 0;
  const timer = win.setInterval(() => {{
    if (applyOnce() || ++tries > 20) win.clearInterval(timer);
  }}, 100);
}})();
</script>
        """,
        height=0,
        scrolling=False,
    )


if __name__ == "__main__":
    assert PAGE_TO_SECTION["Platform Overview"] == "Home"
    assert PAGE_TO_SECTION["Research Assistant"] == "Graph / Ask"
    print("sidebar_nav_ok")
