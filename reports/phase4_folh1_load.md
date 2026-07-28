# Phase 4 thin slice — FOLH1

Generated: 2026-07-28T18:10:00.927729+00:00

| Metric | Value |
|--------|-------|
| `symbol` | FOLH1 |
| `ensembl_id` | ENSG00000086205 |
| `string_ensp` | 9606.ENSP00000256999 |
| `ot_assoc_count` | 759 (API) / 200 loaded |
| `nodes_before` | 3069 |
| `rels_before` | 2517 |
| `nodes_after` | 3254 |
| `rels_after` | 2767 |
| `nodes_delta` | **+185** |
| `rels_delta` | **+250** |
| Aura headroom | ~196.7k nodes remaining (Free 200k) |

## Artifacts

- `data/processed/folh1_by_cancer.csv` (25 cancers) — UI
- `data/processed/folh1_expression.csv` (per-sample) — laptop/local
- Aura: Gene/Protein FOLH1 + OT ASSOCIATED_WITH + STRING INTERACTS_WITH

## Runbook — add next gene

```bash
# From repo root, with .env Neo4j creds and project venv:
.\.venv\Scripts\python.exe scripts/load_target_slice.py --symbol FAP

# After counts look sane (<100k nodes total):
# 1. Set FAP.kg_status: loaded in config/targets.yaml
# 2. Commit data/processed/fap_by_cancer.csv (+ code if any)
# 3. Push for Coolify
```

Same command works for `SSTR2` and `GRPR` (GRPR Ensembl must remain `ENSG00000126010`).

## Exit check (FOLH1)

- [x] Aura nodes still << 100k
- [x] `folh1_by_cancer.csv` non-empty (PRAD leads)
- [x] `kg_status: loaded` for FOLH1
- [ ] UI: select FOLH1 → Expression Atlas pan-cancer chart (verify after deploy)
