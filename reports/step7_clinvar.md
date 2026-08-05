# Step 7 — ClinVar per target

| Gene | Variants | Pathogenic | Nodes Δ |
|------|----------|------------|---------|
| CD19 | 577 | — | 0 |

Schema: `Protein-[:HAS_VARIANT]->ProteinVariant` (`source='ClinVar'`).

```bash
# Wave 7 — fetch then load (non-CD46)
python scripts/fetch_clinvar_cd46.py --all-non-cd46 --max-variants 75 --refresh
python scripts/load_gene_clinvar.py --all-non-cd46 --max-variants 75
```
