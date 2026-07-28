# Phase 4 thin slice — GRPR

Generated: 2026-07-28T18:29:38.861133+00:00

| Metric | Value |
|--------|-------|
| `symbol` | GRPR |
| `ensembl_id` | ENSG00000126010 |
| `started_utc` | 2026-07-28T18:27:36.058900+00:00 |
| `expression_csv` | data\processed\grpr_expression.csv |
| `by_cancer_csv` | data\processed\grpr_by_cancer.csv |
| `string_ensp_resolved` | 9606.ENSP00000369643 |
| `ot_json` | data\raw\apis\open_targets_grpr.json |
| `ot_assoc_count` | 219 |
| `nodes_before` | 3503 |
| `rels_before` | 3266 |
| `ot_disease_nodes_top` | 50 |
| `ot_assoc_rels` | 200 |
| `string_rels` | 47 |
| `nodes_after` | 3586 |
| `rels_after` | 3511 |
| `nodes_delta` | 83 |
| `rels_delta` | 245 |
| `finished_utc` | 2026-07-28T18:29:38.861133+00:00 |

## Next gene

```bash
python scripts/load_target_slice.py --symbol FAP
```

Then set `kg_status: loaded` in `config/targets.yaml` after UI verification.
