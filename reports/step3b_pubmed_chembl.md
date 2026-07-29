# Step 3b — PubMed + ChEMBL per target

**Date:** 2026-07-29  
**Aura after Step 3b:** **4,824 nodes** (was 4,672 after Step 3a)

## Loaded

| Gene | PubMed | Pubs loaded | ChEMBL ID | Drugs loaded | SUPPORTS→Gene | TARGETS→Gene | Nodes Δ |
|------|--------|-------------|-----------|--------------|---------------|--------------|---------|
| CD46 | 25 | 25 | — (no protein target) | 2 curated | 76 | 6 | +20 |
| FOLH1 | 25 | 25 | CHEMBL1892 | 17 (15+2) | 25 | 17 | +39 |
| FAP | 25 | 25 | CHEMBL4683 | 17 (15+2) | 25 | 17 | +35 |
| SSTR2 | 25 | 25 | CHEMBL1804 | 17 (15+2) | 25 | 17 | +27 |
| GRPR | 25 | 25 | CHEMBL4959 | 17 (15+2) | 25 | 17 | +31 |

## Schema

- `(:Publication)-[:SUPPORTS {source:'PubMed'}]->(:Gene)`
- `(:Drug)-[:TARGETS]->(:Gene)` — ChEMBL molecules + curated theranostic agents

## Script

```bash
python scripts/load_gene_pubmed_chembl.py --all --refresh
python scripts/check_step3b_pubmed_chembl.py
```

## Notes

- ChEMBL IDs via UniProt: FOLH1=`CHEMBL1892`, FAP=`CHEMBL4683`, SSTR2=`CHEMBL1804`, GRPR=`CHEMBL4959`.
- CD46 has no ChEMBL SINGLE PROTEIN target; curated biologics/RLT only. Removed incorrect `CHEMBL2176` placeholder (that ID is a mouse enzyme).
- Caps: ≤25 PubMed / gene, ≤15 ChEMBL molecules / gene + curated agents (Pluvicto, FAPI, Lutathera, NeoB, FOR46, …).
- KG Query Explorer: Publications / Drugs templates are gene-aware (`SUPPORTS`/`TARGETS` → Gene).
- Assistant still uses live PubMed API; KG now holds Publication nodes for offline graph queries.
- Raw caches under `data/raw/apis/` (gitignored); summaries in `data/processed/step3b_*_summary.json`.
