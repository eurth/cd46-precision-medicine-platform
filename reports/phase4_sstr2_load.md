# Phase 4 thin slice — SSTR2

Generated: 2026-07-28T18:27:33.114636+00:00

| Metric | Value |
|--------|-------|
| `symbol` | SSTR2 |
| `ensembl_id` | ENSG00000180616 |
| `started_utc` | 2026-07-28T18:24:40.276192+00:00 |
| `expression_csv` | data\processed\sstr2_expression.csv |
| `by_cancer_csv` | data\processed\sstr2_by_cancer.csv |
| `string_ensp_resolved` | 9606.ENSP00000350198 |
| `ot_json` | data\raw\apis\open_targets_sstr2.json |
| `ot_assoc_count` | 1327 |
| `nodes_before` | 3358 |
| `rels_before` | 2971 |
| `ot_disease_nodes_top` | 50 |
| `ot_assoc_rels` | 200 |
| `string_rels` | 94 |
| `nodes_after` | 3503 |
| `rels_after` | 3266 |
| `nodes_delta` | 145 |
| `rels_delta` | 295 |
| `finished_utc` | 2026-07-28T18:27:33.114636+00:00 |

## Next gene

```bash
python scripts/load_target_slice.py --symbol FAP
```

Then set `kg_status: loaded` in `config/targets.yaml` after UI verification.
