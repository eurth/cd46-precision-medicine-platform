# OncoBridge UI Migration Plan

**Status:** Phases 4–8 complete — bundled commit & deploy  
**Stack:** Streamlit (keep) + streamlit-shadcn-ui + streamlit-extras + streamlit-antd-components (nav only)

## Problem statement

- Triple navigation (sidebar + dimension billboard + target bar) wastes ~20% viewport on desktop.
- ~430 lines of global `!important` CSS in `app/components/styles.py` is brittle.
- Default Streamlit widgets (metrics, tabs) read as unfinished vs best-of-streamlit references.

## What we keep

- `st.navigation` (16 pages)
- Plotly (76 charts)
- pandas / polars / Neo4j data layer
- PyVis KG embed, chat assistant

## Recommended libraries

| Library | Role |
|---|---|
| [streamlit-shadcn-ui](https://github.com/ObservedObserver/streamlit-shadcn-ui) | **Phase 4: bypass iframes** — use native themed components instead |
| [streamlit-extras](https://github.com/arnaudmiribel/streamlit-extras) | Scoped CSS via `stylable_container` |
| [streamlit-antd-components](https://pypi.org/project/streamlit-antd-components/) | Nav only: `segmented`, optional `menu` |

**Not now:** Panel, Dash, Anvil, streamlit-elements (wrong shape or stale).

## Architecture

```
app/components/ui_kit.py     ← thin wrappers (pages import this, not raw shadcn)
app/components/styles.py     ← shrink to Plotly + sidebar overrides only
app/components/targets.py  ← SAC segmented target bar; dimension chrome removed
```

## Phases

### Phase 0 — Spike (current)

- [x] Save this plan
- [x] Add deps to `requirements.txt`
- [x] Create `ui_kit.py`
- [x] Remove `render_dimension_chrome()`
- [x] SAC compact target bar
- [x] Pilot: `1_cd46_expression_atlas.py` (shadcn metrics + tabs)
- [x] Smoke: app starts, Expression Atlas renders

**Acceptance:** content above fold on 28"; no dimension billboard; tabs/metrics use shadcn on pilot page.

### Phase 1 — Chrome surgery (3–5 days)

- [x] Sidebar cleanup (remove redundant target mirror caption)
- [x] Trim `styles.py` dead CSS (removed unused `.lp-stats` block)
- [ ] Mobile header toggle verified on live site

### Phase 2 — Shared UI kit (3–4 days)

- [x] `page_header()` replaces `page_hero()` on 3d pages (+ gradual rollout started)
- [x] `info_banner()`, `metric_row()`, `section_tabs()` stable APIs
- [x] `filter_bar()` on Survival Outcomes

### Phase 3 — Page rollout (2–3 weeks)

| Sprint | Pages | Status |
|---|---|---|
| 3a | Overview, Survival, Compare Targets | **Done** |
| 3b | Patient Selection, Eligibility, Biomarker Panel | **Done** |
| 3c | Drug Pipeline, PPI, Diagnostics, Dosimetry | **Done** |
| 3d | KG, Query Explorer, Assistant, Strategy | **Done** |

### Phase 4 — Theme pivot & shadcn fix (P0)

- [x] Clinical Slate light theme tokens (`theme.py`)
- [x] Remove white shadcn iframes
- [x] Global CSS rewritten for light clinical shell
- [x] Deduplicate hero chips + metric row on analytical pages
- [x] Shared Plotly light theme on all chart pages
- [ ] Deploy + visual QA (bundled with final push)

### Phase 5 — Chrome v2 & dimension rail

- [x] `dimension_rail()` — compact grouped nav under target bar
- [x] `page_header()` on all module pages
- [ ] Mobile header toggle verified on live site

### Phase 6 — Page rollout completion (3d + polish)

| Sprint | Pages | Status |
|---|---|---|
| 3d | KG, Query Explorer, Assistant, Strategy | **Done** |
| 6b | `filter_bar()` on Expression, Patient Selection, Survival | **Done** |

### Phase 7 — CSS debt paydown

- [x] `styles.py` ≤120 lines (61 lines); tokens in `theme.py`
- [x] Global CSS extracted to `theme_css.py`
- [x] Zero shadcn iframes

### Phase 8 — Research UX backlog

- [x] Breadcrumbs (`breadcrumb()`)
- [x] Recent modules sidebar (`track_recent_page`, `render_recent_modules`)
- [x] Export bundle helper (`export_research_pack`)
- [x] Print stylesheet in `theme_css.py`

### Phase 9 — Contingency (only if theme pivot fails)

Evaluate Panel → Dash → Next.js+FastAPI.

## Dependencies (new)

**Local dev:** `requirements.txt` (includes pytest)

**Docker / Coolify:** `requirements-docker.txt` (no pytest, no unused kaleido, pinned UI packages)

```
streamlit-shadcn-ui==0.1.19
streamlit-antd-components==0.3.2
networkx>=3.0
```

## Risks

| Risk | Mitigation |
|---|---|
| shadcn iframe white cards on dark shell | Phase 4: native themed metrics/tabs; Clinical Slate light theme |
| shadcn + SAC visual mismatch | SAC for nav only |
| Streamlit upgrade breaks CSS | Pin `streamlit>=1.32,<2.0` |

## References

- [best-of-streamlit](https://github.com/jrieke/best-of-streamlit)
- [Beautify Streamlit with shadcn-ui](https://medium.com/@ericdennis7/how-to-beautify-streamlit-using-shadcn-ui-c70a6e828b77)
- [Streamlit alternatives (Anvil)](https://anvil.works/articles/4-alternatives-streamlit)
