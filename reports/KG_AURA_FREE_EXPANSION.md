# Aura Free KG Expansion Log

**Instance:** Aura Free (200k node / 400k rel ceiling)  
**Budget stop:** ≤40k nodes  
**Baseline freeze prior:** `2026-07-28-phase4-five-targets`

## Wave 0 — Baseline (2026-08-04)

| Metric | Count |
|--------|------:|
| Nodes | 4,850 |
| Relationships | 6,337 |
| Headroom to Free ceiling | ~195k nodes |

### Labels

| Label | Count |
|-------|------:|
| Disease | 1,840 |
| CellLine | 1,186 |
| PatientGroup | 789 |
| SurvivalResult | 317 |
| ClinicalTrial | 203 |
| Publication | 142 |
| Tissue | 141 |
| Gene | 92 |
| Drug | 76 |
| ProteinIsoform | 28 |
| ProteinVariant | 18 |
| Protein | 9 |
| DataSource | 5 |
| Pathway | 3 |

### Open Targets `ASSOCIATED_WITH` by gene

| Gene | Edges |
|------|------:|
| CD46 | 772 |
| FAP | 500 |
| FOLH1 | 500 |
| SSTR2 | 500 |
| GRPR | 219 |

### Trials `TARGETS_GENE` by gene

| Gene | Trials |
|------|-------:|
| CD46 | 9 |
| FAP | 50 |
| FOLH1 | 50 |
| GRPR | 50 |
| SSTR2 | 42 |

---

## Wave 1 — Open Targets caps (done 2026-08-04)

CLI (OT-only): `--ot-size 1000 --ot-top 500 --refresh-ot --skip-extract --skip-string`

**After Wave 1:** 6,207 nodes / 8,260 rels (+1,357 nodes / +1,923 rels)

| Gene | Before OT edges | After | Gene Δ nodes | Notes |
|------|----------------:|------:|-------------:|-------|
| CD46 | 772 | 1,546 | +561 | API total 1,111; loaded 1,000 |
| FOLH1 | 500 | 758 | +148 | API total 759 |
| FAP | 500 | 888 | +222 | API total 889 |
| SSTR2 | 500 | 1,000 | +426 | API total 1,327; loaded 1,000 |
| GRPR | 219 | 219 | 0 | API exhausted at 219 |

---

## Wave 2 — ClinicalTrials.gov (done 2026-08-04)

CLI: `--all --refresh --page-size 100 --max-trials 100` + RLT/ADC query extras.

**After Wave 2:** 6,521 nodes (+314 from Wave 1 end). All 5 genes: 100 trials loaded each.

| Gene | Trials loaded | HPA tissues | Nodes Δ |
|------|--------------:|------------:|--------:|
| CD46 | 100 | 5 | +97 |
| FOLH1 | 100 | 4 | +81 |
| FAP | 100 | 7 | +55 |
| SSTR2 | 100 | 11 | +42 |
| GRPR | 100 | 10 | +39 |

---

## Wave 3 — PubMed / ChEMBL (done 2026-08-04)

CLI: `--all --refresh --pubmed-max 50 --chembl-cap 30`

**After Wave 3:** 6,656 nodes (+135 from Wave 2). 50 pubs/gene; ~30 ChEMBL drugs for FOLH1/FAP/SSTR2/GRPR.

| Gene | Pubs | Drugs | Nodes Δ |
|------|-----:|------:|--------:|
| CD46 | 50 | 2 | +22 |
| FOLH1 | 50 | 32 | +29 |
| FAP | 50 | 32 | +29 |
| SSTR2 | 50 | 32 | +31 |
| GRPR | 50 | 32 | +24 |

---

## Wave 4 — STRING PPI (done 2026-08-04)

CLI: `load_kg_string.py --symbol SYM --required-score 700` (FAP: 400).

**After Wave 4:** 6,702 nodes / 10,181 rels.

| Gene | Score | Edges fetched | Genes upserted | INTERACTS_WITH (degree) |
|------|------:|--------------:|---------------:|------------------------:|
| CD46 | 700 | 103 | 30 | 29 |
| FOLH1 | 700 | 49 | 24 | 23 |
| FAP | 400 | 450 | 51 | 50 |
| SSTR2 | 700 | 94 | 19 | 18 |
| GRPR | 700 | 47 | 17 | 16 |

---

## Waves 5–6 — HPA / GTEx / UniProt / DepMap (done 2026-08-04)

CLI: `python scripts/load_gene_uniprot_gtex_depmap.py --all --refresh`

Idempotent refresh (nodes stayed 6,702). GTEx 52 tissues/gene; DepMap: CD46 30, FOLH1 50, SSTR2 7, FAP/GRPR 0.

---

## Wave 7 — ClinVar non-CD46 (done 2026-08-04)

CLI: fetch + `load_gene_clinvar.py --all-non-cd46 --max-variants 75`

**After Wave 7:** 6,982 nodes (+280 ProteinVariant). FOLH1/FAP/GRPR 75 each; SSTR2 55.

cBioPortal per-gene somatic mutations deferred (cohort PatientGroups already in KG).

---

## Wave 8 — TCGA combo (done 2026-08-04)

- `load_gene_open_data.py --all` — 25 EXPRESSED_IN_CANCER/gene; survival MERGE (idempotent)
- `load_kg_phase2.py` — +2,224 HAS_SURVIVAL_DATA; 8 CORRELATED_WITH; misc SUPPORTS/INDICATED_FOR

**After Wave 8:** 6,982 nodes / **12,704** rels.

---

## Wave 9 — UI / data freeze (done 2026-08-04)

- Dossier + KG Explorer templates: OT, trials, PubMed, ChEMBL, STRING PPI
- Freeze: `config/data_freeze.yaml` → `2026-08-04-aura-free-expand`

---

## Final budget (vs Aura Free 200k / 400k)

| Metric | Baseline | Final | Headroom |
|--------|---------:|------:|---------:|
| Nodes | 4,850 | **6,982** | ~193k |
| Rels | 6,337 | **12,704** | ~387k |

Well under the ≤40k node soft stop.
