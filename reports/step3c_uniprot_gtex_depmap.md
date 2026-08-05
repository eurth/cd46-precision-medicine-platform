# Step 3c — UniProt + GTEx + DepMap + HPA protein intensity

**Aura after Step 3c:** **100250 nodes**

| Gene | Protein | Isoforms | Variants | GTEx | DepMap DEPENDS_ON | HPA protein | Nodes Δ |
|------|---------|----------|----------|------|-------------------|-------------|---------|
| CD19 | 1 | 2 | 2 | 52 | 29 | 3 | 0 |

## Schema

- `Gene-[:ENCODES]->Protein` (+ capped isoform/variant children)
- `Gene-[:EXPRESSED_IN {source:'GTEx'}]->Tissue`
- `Gene-[:EXPRESSED_IN {source:'HPA', modality:'protein_intensity'}]->Tissue`
- `CellLine-[:DEPENDS_ON]->Gene` (existing CellLines only; CRISPR < -0.5)

```bash
python scripts/load_gene_uniprot_gtex_depmap.py --all --refresh
```
