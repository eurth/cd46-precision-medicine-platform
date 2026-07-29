# Step 3 — ClinicalTrials + HPA per target

**Date:** 2026-07-29  
**Aura after Step 3:** **4,672 nodes** (was 4,451 after Step 2)

## Loaded

| Gene | Trials fetched | Trials loaded | HPA RNA tissues linked | Nodes Δ |
|------|----------------|---------------|------------------------|---------|
| FOLH1 | 50 | 50 | 4 | +53 |
| FAP | 50 | 50 | 7 | +55 |
| SSTR2 | 42 | 42 | 11 | +51 |
| GRPR | 50 | 50 | 10 | +57 |
| CD46 | 9 (cache) | 9 | 5 | +5 |

## Schema

- `(:ClinicalTrial)-[:TARGETS_GENE]->(:Gene)` — **201** links
- `(:ClinicalTrial)-[:INVESTIGATES]->(:Disease)` — condition heuristic (kept)
- `(:Gene)-[:EXPRESSED_IN {source:'HPA', modality:'rna_ntpm'}]->(:Tissue)`
- Gene props: `hpa_rna_tissue_specificity`, `hpa_rna_tissue_distribution`, …

## Script

```bash
python scripts/load_gene_trials_hpa.py --all-non-cd46 --refresh
python scripts/load_gene_trials_hpa.py --symbol CD46
```

## Notes

- HPA v24 gene JSON often lacks IHC Tissue dicts; we load **RNA tissue / cell-type nTPM** when present (sparse for some genes).
- ClinicalTrials queries use symbol + aliases from `config/targets.yaml` (e.g. FOLH1 OR PSMA…).
- Research Assistant `search_trials` prefers `clinicaltrials_{gene}.json`.
- KG Query Explorer trials template uses `TARGETS_GENE`.

## Still later

- GENIE (Pro + DUA)
- Aura Pro fill-to-200k
- Fuller classic HPA IHC TSV (beyond protein-intensity dicts)

## Done next

- Step 3b: PubMed + ChEMBL → `reports/step3b_pubmed_chembl.md`
- Step 3c: UniProt + GTEx + DepMap + HPA protein intensity → `reports/step3c_uniprot_gtex_depmap.md`
