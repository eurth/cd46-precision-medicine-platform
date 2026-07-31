---
name: browser-verify-ui
description: >-
  Verify Streamlit/UI changes end-to-end with Playwright MCP before telling the
  user a feature is complete. Use when building or fixing navigation, widgets,
  tooltips, hero bands, rails, or any click-driven UI in this repo.
---

# Browser-verify UI (OncoBridge)

**Rule:** Do not mark a UI feature complete until Playwright confirms it on a running app (local or https://oncobridge.eurthtech.com).

## Workflow

1. **Implement** — smallest diff; native Streamlit widgets over HTML `onclick`.
2. **Static check** — run the matching `scripts/verify_*.py` if one exists.
3. **Browser test** (required for interactive UI):
   - `browser_navigate` → app URL
   - `browser_wait_for` ~8s for Streamlit load
   - `browser_console_messages` — **0 errors** required
   - Perform the user action (hover rail, click target, switch tab)
   - Assert URL, visible text, and active state changed
4. **Fix from logs** — read console errors (e.g. React #231 = string passed to onClick); fix root cause; retest.
5. **Report done** only with evidence: action taken, URL/state after, console error count.

## Playwright patterns (this app)

```javascript
// Right rail — hover to expand, then click
const col = page.locator('[data-testid="stColumn"]:has(.ob-right-rail-host)').first();
const box = await col.boundingBox();
await page.mouse.move(box.x + box.width / 2, box.y + 40);
await page.waitForTimeout(500);
await col.getByRole('button', { name: 'PSMA' }).first().click();
```

```javascript
// Landing spotlight gene label
await page.locator('.lp-carousel-gene').textContent();
```

## Anti-patterns (do not repeat)

| Pattern | Why it fails |
|---------|----------------|
| HTML `<button onclick="...">` in `st.markdown` | React #231 — clicks dead |
| Rail/widgets after `pg.run()` for state that page body needs | Page renders stale target |
| Ship without `browser_console_messages` | User becomes your QA |

## Checklist (copy per task)

```
- [ ] Static verify script passes
- [ ] Playwright: primary user action works
- [ ] Playwright: console errors = 0
- [ ] Playwright: URL/session state matches expectation
- [ ] User told: what was tested and result
```
