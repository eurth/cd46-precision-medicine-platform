# Step 3b — PubMed + ChEMBL per target

**Aura after Step 3b:** **100250 nodes**

| Gene | PubMed | Pubs loaded | ChEMBL ID | Drugs loaded | SUPPORTS | TARGETS | Nodes Δ |
|------|--------|-------------|-----------|--------------|----------|---------|---------|
| CD19 | 784 | 784 | CHEMBL3390821 | 0 | 784 | 0 | 0 |

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
