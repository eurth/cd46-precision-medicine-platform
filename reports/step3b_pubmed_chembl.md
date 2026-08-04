# Step 3b — PubMed + ChEMBL per target

**Aura after Step 3b:** **6656 nodes**

| Gene | PubMed | Pubs loaded | ChEMBL ID | Drugs loaded | SUPPORTS | TARGETS | Nodes Δ |
|------|--------|-------------|-----------|--------------|----------|---------|---------|
| CD46 | 50 | 50 | — | 2 | 99 | 6 | 22 |
| FOLH1 | 50 | 50 | CHEMBL1892 | 32 | 50 | 32 | 29 |
| FAP | 50 | 50 | CHEMBL4683 | 32 | 50 | 32 | 29 |
| SSTR2 | 50 | 50 | CHEMBL1804 | 32 | 50 | 32 | 31 |
| GRPR | 50 | 50 | CHEMBL4959 | 32 | 50 | 32 | 24 |

## Schema

- `(:Publication)-[:SUPPORTS {source:'PubMed'}]->(:Gene)`
- `(:Drug)-[:TARGETS]->(:Gene)` — ChEMBL molecules + curated theranostic agents

## Script

```bash
python scripts/load_gene_pubmed_chembl.py --all --refresh
```

## Notes

- ChEMBL IDs resolved via UniProt: FOLH1=`CHEMBL1892`, FAP=`CHEMBL4683`, SSTR2=`CHEMBL1804`, GRPR=`CHEMBL4959`.
- CD46 has no ChEMBL SINGLE PROTEIN target; curated biologics/RLT only (removed incorrect `CHEMBL2176` placeholder).
- Caps: ≤50 PubMed / gene, ≤30 ChEMBL molecules / gene + curated agents.
