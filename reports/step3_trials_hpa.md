# Step 3 — ClinicalTrials + HPA per target

| Gene | Trials fetched | Trials loaded | HPA tissues | Nodes Δ |
|------|----------------|---------------|-------------|---------|
| CD19 | 1553 | 1553 | 12 | 0 |

Schema: `ClinicalTrial-[:TARGETS_GENE]->Gene`, `Gene-[:EXPRESSED_IN {source:HPA}]->Tissue`.
