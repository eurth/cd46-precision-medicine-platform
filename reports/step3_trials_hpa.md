# Step 3 — ClinicalTrials + HPA per target

| Gene | Trials fetched | Trials loaded | HPA tissues | Nodes Δ |
|------|----------------|---------------|-------------|---------|
| CD46 | 100 | 100 | 5 | 97 |
| FOLH1 | 100 | 100 | 4 | 81 |
| FAP | 100 | 100 | 7 | 55 |
| SSTR2 | 100 | 100 | 11 | 42 |
| GRPR | 100 | 100 | 10 | 39 |

Schema: `ClinicalTrial-[:TARGETS_GENE]->Gene`, `Gene-[:EXPRESSED_IN {source:HPA}]->Tissue`.
