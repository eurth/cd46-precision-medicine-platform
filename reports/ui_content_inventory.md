# OncoBridge UI content inventory (retention lock)

**Rule:** Do not delete a page or tab without updating this file and explicit owner OK.  
**Plan:** remapping + parameterization — not a greenfield rewrite.  
**Date locked:** 2026-07-29

## Action codes

| Code | Meaning |
|------|---------|
| KEEP | Chart/section stays as-is |
| PARAM | Same UI; gene/cancer-keyed data |
| REHOME | Same content; new nav path |
| EXTEND | Additive filters/cards |
| MERGE-NAV | Entry points only; content preserved |

## Page → dimension home

| ID | Page file | Title | Dimension home | Gate was |
|----|-----------|-------|----------------|----------|
| 0 | `0_platform_overview.py` | Platform Overview | Home | none |
| 1 | `1_cd46_expression_atlas.py` | Expression Atlas | Target + Cancer | stub |
| 2 | `2_patient_selection.py` | Patient Selection | Patients | stub+case_study → depth banner |
| 3 | `3_survival_outcomes.py` | Survival Outcomes | Survival | stub |
| 4 | `4_biomedical_knowledge_graph.py` | Knowledge Graph | Graph | stub |
| 5 | `5_research_assistant.py` | Research Assistant | Ask AI | stub |
| 6 | `6_biomarker_panel.py` | Biomarker Panel | Biomarkers | stub+case_study → depth banner |
| 7 | `7_kg_query_explorer.py` | KG Query Explorer | Graph → Query | none |
| 8 | `8_patient_eligibility.py` | Eligibility Scorer | Patients → Eligibility | stub+case_study → depth banner |
| 9 | `9_competitive_landscape.py` | Compare Targets | Target → Compare | none |
| 10 | `10_ppi_network.py` | PPI Network Explorer | Proteins → PPI | stub+case_study → depth banner |
| 11 | `11_drug_pipeline.py` | Drug Pipeline | Drugs | stub+case_study → depth banner |
| 12 | `12_dosimetry_safety.py` | Dosimetry & Safety | Drugs → Dosimetry | stub+case_study → depth banner |
| 13 | `13_clinical_strategy_engine.py` | Clinical Strategy Engine | Strategy | stub+case_study → depth banner |
| 14 | `14_cd46_diagnostics.py` | Diagnostics & Early Detection | Proteins → Diagnostics | stub+case_study → depth banner |

## Tab inventory (must remain after remaps)

| Page | Tabs / stages (count) |
|------|------------------------|
| 0 | Hero, Research Hub, Evidence Modules, Case Study CD46, Pipeline stepper, Summary expander |
| 1 | Pan-Cancer mRNA · Protein & Safety · Functional Screen · Priority & Data (4) |
| 2 | GENIE Landscape · Eligibility & Thresholds · Therapeutic Context · Data & Downloads (4) |
| 3 | Forest Plot · Significance & KM · Cancer Explorer (3) |
| 4 | Network · Cypher · Protein+Evidence (3) |
| 5 | Research Assistant · How It Works · Evidence Context (3) |
| 6 | Inclusion · Co-targeting · Resistance · Complement · Evidence · Patient Scoring (6) |
| 7 | Templates · Cypher · NL · Graph Visualizer (4) |
| 8 | Form+gauge · Evidence Summary · GENIE Context · Similar Indications |
| 9 | Live Compare · CD46 vs PSMA · Trial Funnel · Target Biology · Why CD46 (5) |
| 10 | Network Graph · Partner Table · Pathway · Biology Narrative (4) |
| 11 | Pipeline Overview · CD46 Agents · PSMA Competitive · Complement · Combination (5) |
| 12 | Tumour vs Normal · TI Ranking · Risk Monitor · mCRPC Safety · Clinical Interpretation (5) |
| 13 | Stages 1–5 + End-to-End summary (vertical) |
| 14 | GTEx · PET · IHC · Mutations · Liquid Biopsy · Early Detection · Co-Biomarker (7) |

## Sprint sign-off checklist

- [x] Sprint 0 — this file committed
- [x] Sprint 1 — no `st.stop()` from case_study gate; dimension nav live
- [x] Sprint 2 — Expression/Survival/Assistant/KG Explorer gene labels clean
- [x] Sprint 3 — Survival multi-select; all 3 tabs present
- [x] Sprint 4 — Patients/Biomarker/Eligibility open for FOLH1 (gene-keyed loaders; CD46-only slices honest-empty)
- [x] Sprint 5 — Drugs/PPI/Compare open for FOLH1 (STRING/ChEMBL PARAM; curated CD46 depth retained)
- [x] Sprint 6 — Dosimetry/Strategy/Diagnostics open for FOLH1 (no silent CD46 CSV fallback)
- [x] Sprint 7 — `config/tooltip_terms.csv` + generator + cache; SSTR2 AlphaFold popover
- [x] Sprint 8 — `py_compile` smoke on remapped pages; tab inventory unchanged (15 pages)

### Smoke notes (2026-07-29)

- `render_case_study_gate` always returns False (depth banner only).
- Survival: multi-gene / cancer / endpoint filters; forest + 3 tabs retained.
- Tooltip: `TooltipGenerator.lookup("SSTR2")` → `AF-P30874-F1`; isoform → `AF-P30874-2-F1`.
- Wired popovers on Expression Atlas + Survival Outcomes.
- Honesty: non-CD46 never silently loads `cd46_*.csv` / static CD46 GTEx fallback.
