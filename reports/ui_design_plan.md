# OncoBridge UI Design Plan

**Status:** Phase 4 implemented (2026-07-29) — Clinical Slate light theme live in code  
**Audience:** Researchers, translational scientists, clinical strategists (not consumer / not “tech demo”)

---

## 1. Screenshot review (live deploy)

Reviewed **Platform Overview** and **Expression Atlas** after Phase 3c deploy.

### What works

| Element | Why it works |
|---|---|
| Sidebar grouped by dimension | Familiar lab-tool pattern (cBioPortal, OpenTargets nav) |
| SAC target segmented bar | Compact; 5 targets visible without billboard |
| Module image cards on Overview | Visual hierarchy; case-study vs open modules clear |
| Plotly charts on dark canvas | Readable; color encoding (top quartile blue) is clear |
| Page hero chips + purpose line | Good context before diving into data |

### What fails (must fix)

| Issue | Root cause | User impact |
|---|---|---|
| **White KPI cards** on dark page | `streamlit-shadcn-ui` `metric_card` renders light-theme iframes; no theme hook | Jarring “pasted from another app”; breaks trust |
| **White info alert** (“How to start…”) | Same — shadcn `alert` default theme | Reads as error/toast, not guidance |
| **Two visual languages** | Dark shell (`#07101F`) + light shadcn widgets + dark Plotly | Feels unfinished / AI-assembled |
| **Tech-startup dark aesthetic** | Space Grotesk + indigo-on-navy | Common in dev tools; uncommon in pharma/clinical analytics |
| **Duplicate KPIs** | Hero chips + metric row repeat same numbers | Wastes vertical space (visible on Expression Atlas) |

### Dimension navigation — clarified

| Version | Status | Notes |
|---|---|---|
| **Old “10-button billboard”** | **Removed (Phase 0)** — correct decision | Ate ~20% viewport; links were broken on deploy |
| **Sidebar dimension groups** | **Live today** | 9 groups, 16 pages — primary nav |
| **Compact dimension rail (planned)** | **Phase 5** | Slim second row under target bar — *not* a return of the billboard |

Users should **not** expect the old 10 large dimension buttons back. They should expect a **compact, grouped dimension strip** (icons + short labels, scrollable on mobile) that complements the sidebar.

---

## 2. Design direction: Clinical Research Light

### Principle

> Tools researchers reach for daily — cBioPortal, GTEx, Human Protein Atlas, ClinicalTrials.gov, OpenTargets — use **light backgrounds**, high text contrast, and restrained accent color. Dark mode is optional in those products, not the default.

OncoBridge should feel like a **precision-oncology evidence workbench**, not a SaaS landing page.

### Recommended theme: **Clinical Slate** (light default)

| Token | Value | Use |
|---|---|---|
| `--ob-bg` | `#F4F6F9` | Page background (soft cool gray) |
| `--ob-surface` | `#FFFFFF` | Cards, metrics, tables |
| `--ob-surface-2` | `#EEF2F7` | Secondary panels, chart backdrop |
| `--ob-border` | `#D5DEE8` | Dividers, card borders |
| `--ob-text` | `#1E293B` | Primary text |
| `--ob-text-muted` | `#64748B` | Labels, captions |
| `--ob-primary` | `#2563EB` | Links, active tab, primary actions (clinical blue) |
| `--ob-primary-soft` | `#DBEAFE` | Selected pill, hover |
| `--ob-accent-teal` | `#0D9488` | Biomarker / evidence highlights |
| `--ob-accent-amber` | `#D97706` | Warnings, unmet-need callouts |
| `--ob-case-study` | `#B45309` | CD46 α-RLT case-study stripe only |
| `--ob-success` | `#059669` | Positive survival / eligibility |
| `--ob-danger` | `#DC2626` | Risk tissues, significant HR>1 |

### Typography

| Role | Font | Rationale |
|---|---|---|
| Headings | **IBM Plex Sans** or **Source Sans 3** | Used in scientific publishing UIs; less “startup” than Space Grotesk |
| Body | **Inter** | Keep — excellent for data density |
| Mono / IDs | **JetBrains Mono** | Gene symbols, NCT IDs, Cypher |

### Plotly chart theme (paired with light shell)

- Paper/plot background: `#FFFFFF` or `#EEF2F7`
- Grid: `#E2E8F0`
- Text: `#475569`
- Series palette: blue-teal sequential (not neon on black)

### Optional later: `Clinical Slate Dark`

A toggled dark theme for long evening sessions — **not** the first deliverable. Light-first matches user expectation for medical/pharma tools.

---

## 3. Component standards

All pages import **`components/ui_kit` only** — never raw shadcn.

| Component | Phase 4 target | Rule |
|---|---|---|
| `metric_row()` | Native HTML cards OR themed `st.metric` | **No shadcn iframes** until library supports custom theme |
| `section_tabs()` | Streamlit tabs + CSS in `apply_theme()` | Underline tabs, not pill iframes |
| `info_banner()` | `st.info` / custom `.ob-banner` | Same surface color as page — no white flash |
| `page_header()` | Replaces `page_hero()` | Title + purpose + optional inline KPIs (no duplicate row) |
| `dimension_rail()` | **New — Phase 5** | Compact grouped links |
| `filter_bar()` | **New — Phase 6** | Standard layout for gene/cancer/endpoint filters |

### KPI layout rule

**One KPI surface per page** — choose hero chips *or* metric row, not both.

Expression Atlas example (target state):

```
[ Page header: title + purpose + 4 inline stats in hero band ]
[ Section tabs ]
[ Filters row ]
[ Chart ]
```

---

## 4. Information architecture

### Navigation layers (final)

```
┌─────────────────────────────────────────────────────────────┐
│ Top bar: OncoBridge · Research live badge                    │
├─────────────────────────────────────────────────────────────┤
│ Target bar: [CD46][FOLH1][FAP][SSTR2][GRPR]  + context chip │
├─────────────────────────────────────────────────────────────┤
│ Dimension rail (Phase 5): Target │ Biomarkers │ Patients │ …  │  ← compact, optional on Overview only OR all pages
├──────────┬──────────────────────────────────────────────────┤
│ Sidebar  │ Main: page_header → tabs → filters → content      │
│ (groups) │                                                   │
└──────────┴──────────────────────────────────────────────────┘
```

### Dimension groups (sidebar — unchanged)

| Group | Pages |
|---|---|
| Home | Platform Overview |
| Target / Cancer | Expression Atlas, Compare Targets |
| Biomarkers | Biomarker Panel |
| Proteins | PPI Network, Diagnostics |
| Patients | Patient Selection, Eligibility Scorer |
| Drugs / Safety | Drug Pipeline, Dosimetry |
| Survival | Survival Outcomes |
| Graph / Ask | Knowledge Graph, Query Explorer, Research Assistant |
| Strategy | Clinical Strategy Engine |

### Dimension rail (Phase 5 — new, compact)

Single horizontal row, **max 36px height**, grouped labels:

`Target · Biomarkers · Patients · Drugs · Survival · Graph · Strategy`

- Click opens first page in group OR dropdown of pages in group (SAC `menu` or `segmented` with overflow).
- Hidden on mobile (sidebar only).
- **Not** 10 equal-width billboards.

---

## 5. Page-level patterns

### A. Overview (landing)

- Keep image module cards (they work).
- KPI row: light surface cards matching theme.
- Remove duplicate stats between hero and cards.
- Case-study gold accent only on CD46 pipeline section.

### B. Analytical pages (Expression, Survival, Compare, …)

- `page_header()` with 3–4 inline stats.
- Tabs directly under header.
- Filters in a **single collapsible bar** (`filter_bar`) — default expanded on desktop, collapsed on mobile.
- Chart full width; interpretation callout below chart (`.ob-insight` — soft blue left border).

### C. Form pages (Eligibility Scorer)

- Left: inputs · Right: live score gauge.
- Evidence tabs below fold — keep current structure.

### D. Graph / AI pages (KG, Assistant)

- Phase 3d rollout last; may keep slightly denser layout.

---

## 6. Phased roadmap (inputs & action items)

### Phase 4 — Theme pivot & shadcn fix (P0, ~1 week)

**Goal:** Eliminate white-on-dark clash; establish Clinical Slate tokens.

| # | Action | Owner | Input needed |
|---|---|---|---|
| 4.1 | Add `theme.py` with design tokens | Dev | Approve palette above |
| 4.2 | Rewrite `apply_theme()` — light shell CSS | Dev | — |
| 4.3 | Replace `metric_row()` shadcn path with themed native cards | Dev | — |
| 4.4 | Replace `info_banner()` shadcn path with `.ob-banner` | Dev | — |
| 4.5 | Replace `section_tabs()` shadcn path with styled `st.tabs` | Dev | — |
| 4.6 | Update Plotly `_PLOTLY_LAYOUT` constant → shared `chart_theme()` | Dev | — |
| 4.7 | Remove duplicate KPI row on pages that keep `page_hero` chips | Dev | — |
| 4.8 | Deploy + visual QA on Overview + Expression Atlas | You | Screenshots OK? |

**Acceptance:** No white iframes; WCAG AA contrast on body text; charts match page background.

---

### Phase 5 — Chrome v2 & dimension rail (~3–4 days)

| # | Action | Input needed |
|---|---|---|
| 5.1 | Implement `dimension_rail()` in `ui_kit.py` | Confirm: show on all pages or Overview only? |
| 5.2 | Implement `page_header()` — merge hero + KPIs | — |
| 5.3 | Gradually replace `page_hero()` on 11 migrated pages | — |
| 5.4 | Mobile header toggle QA on live | You |
| 5.5 | Sidebar: active group highlight | — |

**Acceptance:** Dimension wayfinding without billboard; ≤120px chrome above content on 28" display.

---

### Phase 6 — Page rollout completion (3d + polish, ~1 week)

| # | Action | Pages |
|---|---|---|
| 6.1 | Migrate remaining pages to `ui_kit` | KG, Query Explorer, Assistant, Strategy |
| 6.2 | Add `filter_bar()` helper | Survival, Expression, Patient Selection |
| 6.3 | Standardize download buttons (`st.download_button` row) | All data tables |
| 6.4 | Tooltip / popover consistency | Gene symbols site-wide |

---

### Phase 7 — CSS debt & performance (~3 days)

| # | Action |
|---|---|
| 7.1 | Collapse `styles.py` to ≤120 lines; move tokens to `theme.py` |
| 7.2 | Audit iframe count per page (target: 0 shadcn iframes) |
| 7.3 | Lazy-load heavy charts (KG PyVis) below fold |
| 7.4 | Add `prefers-color-scheme` hook for optional dark (stretch) |

---

### Phase 8 — Research UX enhancements (backlog)

| Item | Description |
|---|---|
| Breadcrumb | `Home › Target / Cancer › Expression Atlas` |
| Recent modules | Session memory of last 3 pages |
| Compare mode | Side-by-side target overlay on Expression Atlas |
| Export bundle | One-click CSV+PNG per tab |
| Print stylesheet | PDF-friendly evidence summary |

---

## 7. Decisions needed from you

| # | Question | Default if no answer |
|---|---|---|
| D1 | **Light theme as default?** | Yes — Clinical Slate |
| D2 | **Dimension rail on all pages or Overview only?** | Overview + analytical pages; hidden on KG full-screen |
| D3 | **Keep Space Grotesk for logo only?** | Yes — wordmark only; body headings → IBM Plex Sans |
| D4 | **Remove shadcn dependency entirely?** | Keep package but bypass iframes; remove from Docker if unused |
| D5 | **Hero chips vs metric row?** | `page_header` inline stats only; drop duplicate row |

---

## 8. What we are explicitly not doing

- ❌ Restoring the old 10-button dimension billboard
- ❌ Pure black `#000` backgrounds
- ❌ White shadcn cards on dark pages (interim bug, fixed in Phase 4)
- ❌ Framework migration (Dash/Panel/Next.js) unless Phase 6 fails
- ❌ Rounding corners / glassmorphism for its own sake

---

## 9. Success metrics

| Metric | Target |
|---|---|
| Chrome height above first chart | ≤ 220px desktop |
| White iframe widgets | 0 |
| Pages on unified theme | 16/16 |
| Mobile sidebar usable | Toggle visible; rail hidden |
| Researcher feedback | “Feels like a lab tool, not a demo” |

---

## 10. References (design benchmarks)

- [cBioPortal](https://www.cbioportal.org/) — light analytical shell
- [GTEx Portal](https://gtexportal.org/) — tissue expression UX
- [Human Protein Atlas](https://www.proteinatlas.org/) — clinical readability
- [OpenTargets](https://www.opentargets.org/) — evidence cards
- [ClinicalTrials.gov](https://clinicaltrials.gov/) — trustworthy neutral UI
