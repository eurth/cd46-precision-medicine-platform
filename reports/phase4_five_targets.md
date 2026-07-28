# Phase 4 complete — five-target thin slices

**Date:** 2026-07-28  
**Aura after loads:** **3,586 nodes / 3,511 rels** (~1.8% of Free 200k) — safe headroom.

| Gene | Δ nodes | Δ rels | OT assoc (API) | STRING edges | by_cancer CSV |
|------|---------|--------|----------------|--------------|---------------|
| CD46 | (baseline) | — | case-study depth | — | `cd46_by_cancer.csv` |
| FOLH1 | +185 | +250 | 759 | 49 | `folh1_by_cancer.csv` |
| FAP | +104 | +204 | 889 | 3 | `fap_by_cancer.csv` |
| SSTR2 | +145 | +295 | 1327 | 94 | `sstr2_by_cancer.csv` |
| GRPR | +83 | +245 | 219 | 47 | `grpr_by_cancer.csv` |

## What each thin slice includes

- TCGA/Xena by-cancer mRNA CSV  
- Gene + Protein MERGE in Aura  
- Top Open Targets associations (200 page / 50 disease nodes prioritized)  
- STRING high-confidence neighborhood  

## What is still CD46-only (backlog)

- Survival / eligibility / HPA curated tables / 225Ac drugs / DepMap depth  
- Compare-targets page rewrite  
- Full Phase 3: LLM daily caps, feedback inbox, lazy Plotly audit  
- Google OAuth (owner deferred)

## Recipe (already used)

```bash
.\.venv\Scripts\python.exe scripts/load_target_slice.py --symbol <SYMBOL>
```
