# OncoBridge UI Migration Plan

**Status:** Phase 0 in progress (2026-07-29)  
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
| [streamlit-shadcn-ui](https://github.com/ObservedObserver/streamlit-shadcn-ui) | Primary: `metric_card`, `tabs`, `card`, `alert`, `badges` |
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

- Sidebar cleanup (remove redundant target mirror caption)
- Trim `styles.py` dead CSS
- Mobile header toggle verified

### Phase 2 — Shared UI kit (3–4 days)

- `page_header()` replaces `page_hero()` gradually
- `info_banner()`, `metric_row()`, `section_tabs()` stable APIs

### Phase 3 — Page rollout (2–3 weeks)

| Sprint | Pages |
|---|---|
| 3a | Overview, Survival, Compare Targets |
| 3b | Patient Selection, Eligibility, Biomarker Panel |
| 3c | Drug Pipeline, PPI, Diagnostics, Dosimetry |
| 3d | KG, Query Explorer, Assistant, Strategy |

### Phase 4 — CSS debt paydown

Target: `styles.py` ≤80 lines; theme in `ui_kit.apply_theme()`.

### Phase 5 — Contingency (only if Phase 3 fails)

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
| shadcn iframe perf | Pilot biomarker panel in Phase 3b; cap iframes per page |
| shadcn + SAC visual mismatch | SAC for nav only |
| Streamlit upgrade breaks CSS | Pin `streamlit>=1.32,<2.0` |

## References

- [best-of-streamlit](https://github.com/jrieke/best-of-streamlit)
- [Beautify Streamlit with shadcn-ui](https://medium.com/@ericdennis7/how-to-beautify-streamlit-using-shadcn-ui-c70a6e828b77)
- [Streamlit alternatives (Anvil)](https://anvil.works/articles/4-alternatives-streamlit)
