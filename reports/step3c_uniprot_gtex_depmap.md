# Step 3c — UniProt + GTEx + DepMap + HPA protein intensity

**Date:** 2026-07-29  
**Aura after Step 3c:** **4,850 nodes** (was 4,824 after Step 3b)

## Loaded

| Gene | Protein | Isoforms | Variants | GTEx tissues | DepMap DEPENDS_ON | HPA protein intensity | Notes |
|------|---------|----------|----------|--------------|-------------------|----------------------|-------|
| CD46 | 1 | 10 | 13 | 52 | 30 | 1 | CD46 CellLines already present |
| FOLH1 | 1 | 8 | 4 | 52 | 50 | 5 | |
| FAP | 1 | 2 | 1 | 52 | 0 | 3 | No CRISPR deps below −0.5 |
| SSTR2 | 1 | 2 | 0 | 52 | 7 | 5 | |
| GRPR | 1 | 0 | 0 | 52 | 0 | 0 | HPA protein intensity empty in v24 JSON |

## Schema

- `(:Gene)-[:ENCODES]->(:Protein {uniprot_id})`
- `(:Protein)-[:HAS_ISOFORM]->(:ProteinIsoform)` (cap 10)
- `(:Protein)-[:HAS_VARIANT]->(:ProteinVariant)` (cap 20)
- `(:Gene)-[:EXPRESSED_IN {source:'GTEx', modality:'rna_tpm', median_tpm, …}]->(:Tissue)`
- `(:Gene)-[:EXPRESSED_IN {source:'HPA', modality:'protein_intensity'}]->(:Tissue)`
- `(:CellLine)-[:DEPENDS_ON {gene_symbol, crispr_score, source:'DepMap'}]->(:Gene)` — **existing CellLines only**

## Script

```bash
python scripts/load_gene_uniprot_gtex_depmap.py --all --refresh
python scripts/check_step3c_uniprot_gtex_depmap.py
```

## Notes

- GTEx TPM lives on the **relationship**, not Tissue node props (avoids CD46-only `Tissue.gtex_*` overwrite).
- DepMap columns matched as `SYMBOL (entrez_id)` so FAP does not pick up AFAP1.
- FAP / GRPR: zero CRISPR fitness dependencies at threshold −0.5 — expected for many surface targets.
- HPA denser IHC uses `Protein tissue/cell type specific Intensity` dicts from gene JSON (sparse vs classic IHC atlas).
- KG Query Explorer cell-line template is gene-aware via `DEPENDS_ON`.
