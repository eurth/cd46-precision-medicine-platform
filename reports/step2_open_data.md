# Step 2 — copy CD46 open-data recipe to other targets

**Date:** 2026-07-29  
**Aura after Step 2:** **4,451 nodes / 5,111 rels** (was 3,586 / 3,511 before Step 2)

## What landed (same recipe classes as CD46)

| Asset | CD46 | FOLH1 | FAP | SSTR2 | GRPR |
|-------|------|-------|-----|-------|------|
| Gene–cancer expression (`EXPRESSED_IN_CANCER`) | 25 | 25 | 25 | 25 | 25 |
| Survival results (`SurvivalResult` + `HAS_SURVIVAL`) | 53 | 53 | 48 | 61 | 63 |
| Open Targets diseases (top MERGE) | case-study | 200 | 200 | 200 | 200 |
| Open Targets assoc rels (fetched page) | — | 500 | 500 | 500 | 219 |
| STRING PPI edges | — | 49 | 3* | 94 | 47 |

\*FAP: STRING returns only 3 edges at score ≥700 — not a loader bug.

## Caps raised (thin → mediumer)

| Param | Old thin | Step 2 |
|-------|----------|--------|
| OT page size | 200 | **500** |
| OT disease MERGE top_n | 50 | **200** |
| STRING edge_limit | 50 | **200** |

## New script

```bash
# TCGA by_cancer + survival → Aura (all five)
python scripts/load_gene_open_data.py --all

# Expand OT/STRING for one gene
python scripts/load_target_slice.py --symbol FOLH1 --skip-extract --refresh-ot --ot-size 500 --ot-top 200 --edge-limit 200
```

Schema note: multi-gene survival uses `SurvivalResult.gene_symbol` + `kind` (km/cox). Expression uses `(:Gene)-[:EXPRESSED_IN_CANCER]->(:Disease)` instead of overwriting CD46 Disease properties.

## Still CD46-only (next data sprints)

- HPA / GTEx normal tissue
- DepMap cell-line depth
- Trials / curated drugs / PubMed packs
- GENIE (needs Pro + DUA)

## Honesty

`config/targets.yaml` `data_tier` for FOLH1/FAP/SSTR2/GRPR → **medium**. CD46 remains **full** case study.
