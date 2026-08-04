# Step 3c — UniProt + GTEx + DepMap + HPA protein intensity

**Aura after Step 3c:** **6702 nodes**

| Gene | Protein | Isoforms | Variants | GTEx | DepMap DEPENDS_ON | HPA protein | Nodes Δ |
|------|---------|----------|----------|------|-------------------|-------------|---------|
| CD46 | 1 | 10 | 13 | 52 | 30 | 1 | 0 |
| FOLH1 | 1 | 8 | 4 | 52 | 50 | 5 | 0 |
| FAP | 1 | 2 | 1 | 52 | 0 | 3 | 0 |
| SSTR2 | 1 | 2 | 0 | 52 | 7 | 5 | 0 |
| GRPR | 1 | 0 | 0 | 52 | 0 | 0 | 0 |

## Schema

- `Gene-[:ENCODES]->Protein` (+ capped isoform/variant children)
- `Gene-[:EXPRESSED_IN {source:'GTEx'}]->Tissue`
- `Gene-[:EXPRESSED_IN {source:'HPA', modality:'protein_intensity'}]->Tissue`
- `CellLine-[:DEPENDS_ON]->Gene` (existing CellLines only; CRISPR < -0.5)

```bash
python scripts/load_gene_uniprot_gtex_depmap.py --all --refresh
```
