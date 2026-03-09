# CD46 Precision Medicine Platform — Master Plan
# Version: 2.0 | Last Updated: March 9, 2026
# Context: Pitch sprint for Prof. Bobba Naidu (225Ac-CD46 therapy)
# Stack: VS Code local | Python 3.13.7 | GPT-4o + Gemini API | AuraDB Free
# Git: https://github.com/eurth/cd46-precision-medicine-platform | branch: main
# Streamlit local: http://localhost:8502 | Cloud: auto-deploys on push to main

---

## PROJECT GOAL
Build a multi-dataset AI-powered CD46 research platform that:
1. Integrates 6 public datasets into one knowledge graph
2. Answers "Which cancers have CD46 overexpression AND poor survival?"
3. Produces a patient eligibility score for 225Ac-CD46 therapy
4. Runs as a live Streamlit app with AI Q&A, deployable in 48 hours

---

## FOLDER STRUCTURE

```
cd46_precision_medicine_platform/
│
├── MEMORY_BANK/                  # All planning docs — this folder
├── config/
│   ├── config.yaml
│   ├── datasets.yaml
│   ├── kg_schema.yaml
│   └── .env.template
├── data/
│   ├── raw/{tcga/, hpa/, depmap/, apis/}
│   └── processed/{csv files + kg_ready/}
├── src/
│   ├── data_ingestion/
│   ├── preprocessing/
│   ├── analysis/
│   ├── visualization/
│   ├── knowledge_graph/
│   ├── agent/
│   └── reporting/
├── app/
│   ├── streamlit_app.py
│   ├── pages/
│   └── components/
├── reports/figures/
├── scripts/run_pipeline.py
├── tests/
├── notebooks/
├── requirements.txt
├── .env.template
├── Makefile
└── README.md
```

---

## DATASETS — STATUS AS OF MARCH 9, 2026

| Dataset | What | AuraDB Nodes | Status | Notes |
|---|---|---|---|---|
| TCGA (UCSC Xena) | CD46 mRNA, 33 cancers, survival | 50 Disease + 226 PatientGroup + 39 SurvivalResult | ✅ LOADED | Aggregated (High/Low groups per cancer) |
| HPA (Human Protein Atlas) | CD46 protein, 44+ tissues | 81 Tissue | ✅ LOADED | 57 via curated list; raw JSON had no per-tissue levels |
| DepMap | 1,800+ cell lines, CRISPR scores | 1,186 CellLine | ✅ LOADED | CD46 expression + CRISPR dependency as properties |
| ClinicalTrials.gov v2 | All CD46 NCT trials | 14 ClinicalTrial | ✅ LOADED | 9 new NCTs + 5 existing |
| ChEMBL | CD46 bioactivities | 0 new (data in JSON) | ⚠️ JSON ON DISK | Not yet loaded as nodes |
| UniProt | CD46 protein features | 4 Protein + 16 ProteinIsoform + 13 ProteinVariant | ✅ LOADED | All 16 isoforms, 13 AHUS2/somatic variants |
| Open Targets | CD46 disease associations | 50 Disease (25 via OT) | ⚠️ PARTIAL | Only 25/772 fetched (limit=25 at fetch time) |
| cBioPortal mCRPC | SU2C + MSK mCRPC cohorts | 26 PatientGroup | ⚠️ SAMPLE | JSON has 26 unique patients; full 1,033 MSK not saved |
| PubMed (Biopython Entrez) | CD46 publications | 55 Publication | ✅ LOADED | 47 new (5 search terms, deduplicated) |
| Drugs (manual seed) | FOR46, 225Ac-ADC, PSMA | 3 Drug | ✅ SEEDED | Manual; DrugBank full data pending |
| Pathways (manual seed) | Complement, immune evasion | 3 Pathway | ✅ SEEDED | Manual |
| DrugBank Academic | CD46 drug-target interactions | 0 | ⬜ TODO | Free academic signup → ~25 Drug nodes |
| STRING DB | CD46 protein interactions | 0 KG nodes (UI only) | ⬜ TODO | Tab auto-loads from API; not yet in AuraDB |
| GENIE (AACR Synapse) | 12k PRAD variant patients | 0 | 🔒 BLOCKED | Synapse DUA in review (~1-2 weeks) |

### CONFIRMED AURADB STATE (March 9, 2026 — audit_kg.py)
- **Total Nodes: 1,701**
- **Total Relationships: 1,118**
- Commit: `96641fb` | pushed to `main` ✅

### NEXT HIGHEST-IMPACT (in order):
1. **DrugBank Academic** — 5-min free signup → +~25 Drug nodes + TARGETS rels
2. **Open Targets full re-fetch** — one GraphQL call with `size:772` → +747 Disease associations
3. **STRING → KG** — load CD46 interaction partners as Gene nodes with INTERACTS_WITH rels

GENIE: DEFERRED to Phase 2 (Synapse DUA pending; 12k patients would push us to ~15k nodes)

---

## KG SIZE — ACTUAL vs PLAN

| Label | Planned | Actual (March 9) | Gap / Note |
|---|---|---|---|
| CellLine | 1,800 | 1,186 | DepMap loaded subset |
| PatientGroup | 1,183 | 226 | cBioPortal JSON has 26; rest from TCGA aggregates |
| Tissue | 176 | 81 | Curated list; HPA JSON lacked per-tissue data |
| Disease | 60 | 50 | 33 TCGA + 25 Open Targets (partial) |
| Publication | 50 | 55 | 47 PubMed + 8 manual = 55 ✅ |
| ClinicalTrial | 50 | 14 | 14 loaded |
| ProteinIsoform | 16 | 16 | ✅ All 16 UniProt isoforms |
| ProteinVariant | 13 | 13 | ✅ All 13 natural variants |
| Drug | 25 | 3 | DrugBank Academic pending |
| SurvivalResult | — | 39 | Added from TCGA analysis |
| Protein | 4 | 4 | CD46 splice isoform Protein nodes |
| Gene | 6 | 6 | CD46 + related genes |
| Pathway | 3 | 3 | Complement, immune evasion |
| DataSource | 5 | 5 | TCGA, HPA, DepMap, ChEMBL, STRING |
| **TOTAL** | **~3,912** | **1,701** | **43% of plan; gap = GENIE + DrugBank + full OT** |

AuraDB Free: 200,000 nodes / 400,000 rels → **~0.85% utilization — massive headroom**

### Path to ~2,500 nodes (without GENIE):
- DrugBank Academic: +~25 nodes
- Open Targets full 772: +~747 Disease/ASSOCIATED_WITH
- STRING → KG: +~20 Gene nodes
- Full cBioPortal mCRPC 1,033 patients: +~1,007 PatientGroup nodes

---

## KEY CONSTANTS
- CD46 Ensembl ID: ENSG00000117335
- CD46 UniProt: P15529
- CD46 chromosome: 1q32.2
- Priority score formula: 0.35×expression_rank + 0.35×survival_impact + 0.15×cna_freq + 0.15×protein_score
- HIGH PRIORITY threshold: ≥ 0.70
- MODERATE threshold: ≥ 0.45
- EXPLORATORY: < 0.45

---

## SPRINT EXECUTION STATUS

| Phase | Task | Status |
|---|---|---|
| Setup | AuraDB Free + .env | ✅ DONE |
| Phase 1 | Download all datasets | ✅ DONE |
| Phase 2 | TCGA survival analysis | ✅ DONE |
| Phase 3 | KG build (all loaders run) | ✅ DONE — 1,701 nodes |
| Phase 4 | Streamlit app (all 6 pages) | ✅ DONE — running on :8502 |
| Phase 4a | AlphaFold tab → protein biology panel | ✅ DONE — 7 sections |
| Phase 4b | STRING tab auto-load | ✅ DONE |
| Phase 5 | Push to GitHub | ✅ DONE — commit 96641fb |
| Phase 5 | Streamlit Cloud deploy | ✅ AUTO-DEPLOY on push |

## REMAINING WORK (short queue)

| Task | Script / Action | Expected Gain | Priority |
|---|---|---|---|
| DrugBank Academic data | Sign up at go.drugbank.com → run `load_kg_drugbank.py` | +~25 Drug nodes, +~50 TARGETS rels | HIGH |
| Open Targets full 772 rows | Re-fetch with `size:772` → re-run `load_kg_open_targets.py` | +~747 ASSOCIATED_WITH rels | HIGH |
| STRING interactions → KG | Load 20 interaction partners from STRING API into AuraDB | +~20 Gene nodes, +~25 INTERACTS_WITH rels | MEDIUM |
| Full mCRPC 1,033 patients | Re-fetch cBioPortal with all sample IDs → load | +~1,007 PatientGroup nodes | MEDIUM |
| GENIE PRAD variants | Synapse DUA approval → `download_genie.py` + `load_kg_genie.py` | +~12,900 nodes | 🔒 BLOCKED |

## IMPORTANT TECHNICAL NOTES
- **Protein node MATCH**: Use `symbol = 'CD46'`, NOT `uniprot_id = 'P15529'`
  (actual uniprot_id values are 'P15529-STA-1', 'P15529-LCA-1' etc.)
- **AuraDB credentials**: NEO4J_URI + NEO4J_USERNAME + NEO4J_PASSWORD in `.env`
- **Local Streamlit**: `.venv\Scripts\streamlit.exe run app/streamlit_app.py --server.port 8502`
- **Syntax check**: `.venv\Scripts\python.exe -m py_compile <file>` before every commit
- **Audit**: `python scripts/audit_kg.py` after every loader run

### PHASE 6 — Polish + Practice (Hours 36-48)

---

## 6 PRESET AI QUESTIONS (for Prof. Bobba Naidu demo)

1. "Which cancers have CD46 overexpression AND poor survival?"
2. "What % of prostate cancer patients qualify for 225Ac-CD46 therapy?"
3. "Is CD46 co-expressed with PSMA? Does that support dual-targeting?"
4. "Which cancer type should be the first 225Ac-CD46 target, and why?"
5. "How does CD46 compare to PSMA as a prostate cancer target?"
6. "What active clinical trials are targeting CD46 right now?"

---

## KEY CYPHER QUERIES (see queries.py for full implementations)
- Q1: Cancers with CD46 overexpression + poor survival (ORDER BY priority_score)
- Q2: % of PRAD patients eligible for 225Ac
- Q3: CD46 + PSMA Spearman correlation in PRAD
- Q4: Active clinical trials targeting CD46
- Q5: CD46 protein therapeutic window (HPA H-scores by tissue)
- Q6: Resistance genomics (variants in CD46-low tumors)
- Q7: Full CD46 2-hop neighborhood
- Q8: Priority ranking across all cancers

---

## PRIORITY SCORE FORMULA
priority_score = (
    0.35 * expression_rank_normalized +
    0.35 * survival_impact_score +
    0.15 * cna_amplification_freq +
    0.15 * protein_expression_score
)
Labels: HIGH PRIORITY (≥0.70) | MODERATE (≥0.45) | EXPLORATORY (<0.45)
