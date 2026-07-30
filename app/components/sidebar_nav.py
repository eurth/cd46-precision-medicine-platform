"""Sidebar nav — collapsed sections by default + top spacing."""
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


def _collapsed_state(active_section: str) -> dict[str, bool]:
    return {name: name == active_section for name in NAV_SECTIONS}


def inject_sidebar_nav_defaults(current_page: str | None) -> None:
    """Persist collapsed section state; click-collapse after nav paints."""
    active = PAGE_TO_SECTION.get(current_page or "", "Home")
    state_json = json.dumps(_collapsed_state(active))
    sections_js = json.dumps(list(NAV_SECTIONS))
    components.html(
        f"""
<script>
(function () {{
  const win = window.parent;
  const doc = win.document;
  const state = {state_json};
  const sectionNames = {sections_js};

  function storageKey() {{
    return Object.keys(win.localStorage).find((k) => k.startsWith("stSidebarSectionsState-"));
  }}

  function persistState() {{
    const key = storageKey();
    if (key) win.localStorage.setItem(key, JSON.stringify(state));
  }}

  function collapseExpanded() {{
    const nav = doc.querySelector('[data-testid="stSidebarNav"]');
    if (!nav) return false;
    nav.querySelectorAll('[data-testid="stNavSectionHeader"]').forEach((header) => {{
      const section = header.parentElement;
      if (!section) return;
      const hasActive = section.querySelector('[aria-current="page"]');
      const hasLinks = section.querySelector('[data-testid="stSidebarNavLink"]');
      if (hasLinks && !hasActive) header.click();
    }});
    return true;
  }}

  persistState();
  let tries = 0;
  const timer = win.setInterval(() => {{
    if (collapseExpanded() || ++tries > 24) win.clearInterval(timer);
  }}, 120);
}})();
</script>
        """,
        height=0,
        scrolling=False,
    )


if __name__ == "__main__":
    assert PAGE_TO_SECTION["Platform Overview"] == "Home"
    assert _collapsed_state("Home")["Target / Cancer"] is False
    print("sidebar_nav_ok")
