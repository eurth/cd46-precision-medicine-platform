# CD46 Precision Medicine Platform — Master Plan
# Version: 1.0 | Date: March 7, 2026
# Context: 48-hour pitch sprint for Prof. Bobba Naidu (225Ac-CD46 therapy)
# Stack: VS Code local | Python 3.11 | GPT-4o + Gemini API | AuraDB Free

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

## DATASETS — PHASE 1 (48-hour sprint)

| Dataset | What | Access | Time |
|---|---|---|---|
| TCGA (UCSC Xena) | CD46 mRNA, 19k samples, 33 cancers, survival | Free download | 4 min |
| HPA API | CD46 protein per 44 tissues, tumor vs normal | Free REST | 5 sec |
| SU2C mCRPC (cBioPortal) | 1,183 mCRPC patients (150 SU2C + 1,033 MSK) | Free REST | 1 min |
| DepMap | 1,800 cell lines, CRISPR essentiality | Free download | 10 min |
| ClinicalTrials.gov v2 | All CD46 NCT trials | Free REST | 10 sec |
| ChEMBL | CD46 compounds | Free REST | 10 sec |
| UniProt | CD46 protein annotation | Free REST | 5 sec |
| Open Targets | CD46 target-disease scores | Free GraphQL | 30 sec |

GENIE: DEFERRED to Phase 2 (200k individual patients exceed AuraDB Free node limit)

---

## KG SIZE — PHASE 1

| Dataset | Nodes | Rels |
|---|---|---|
| TCGA (aggregated) | 198 | 380 |
| SU2C via cBioPortal (individual) | 1,183 | 7,000 |
| HPA (44 tissues individual) | 176 | 300 |
| DepMap (1,800 cell lines) | 1,800 | 5,400 |
| Static seed (genes, proteins, pathways) | 395 | 1,200 |
| Drugs + Trials | 50 | 200 |
| Publications | 50 | 150 |
| Open Targets + ChEMBL | 60 | 250 |
| **TOTAL** | **~3,912** | **~14,880** |

AuraDB Free: 200,000 nodes / 400,000 rels → **~2% utilization**

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

## 48-HOUR SPRINT PHASES

### PRE-SPRINT SETUP (30 min)
- Create AuraDB Free account → get Bolt URI + username + password
- Create .env file with OPENAI_API_KEY, GEMINI_API_KEY, NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD

### PHASE 1 — Download (Hours 0-2)
  python scripts/run_pipeline.py --mode download

### PHASE 2 — Analysis (Hours 2-8)
  python scripts/run_pipeline.py --mode analyze

### PHASE 3 — KG Build (Hours 8-12)
  python scripts/run_pipeline.py --mode kg

### PHASE 4 — Streamlit App (Hours 12-24)
  streamlit run app/streamlit_app.py

### PHASE 5 — Deploy (Hours 24-36)
  Push to GitHub → deploy Streamlit Community Cloud

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
