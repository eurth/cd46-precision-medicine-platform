# Phase 4 thin slice — FAP

Generated: 2026-07-28T18:24:37.241739+00:00

| Metric | Value |
|--------|-------|
| `symbol` | FAP |
| `ensembl_id` | ENSG00000078098 |
| `started_utc` | 2026-07-28T18:22:34.483854+00:00 |
| `expression_csv` | data\processed\fap_expression.csv |
| `by_cancer_csv` | data\processed\fap_by_cancer.csv |
| `string_ensp_resolved` | 9606.ENSP00000188790 |
| `ot_json` | data\raw\apis\open_targets_fap.json |
| `ot_assoc_count` | 889 |
| `nodes_before` | 3254 |
| `rels_before` | 2767 |
| `ot_disease_nodes_top` | 50 |
| `ot_assoc_rels` | 200 |
| `string_rels` | 3 |
| `nodes_after` | 3358 |
| `rels_after` | 2971 |
| `nodes_delta` | 104 |
| `rels_delta` | 204 |
| `finished_utc` | 2026-07-28T18:24:37.241739+00:00 |

## Next gene

```bash
python scripts/load_target_slice.py --symbol FAP
```

Then set `kg_status: loaded` in `config/targets.yaml` after UI verification.
