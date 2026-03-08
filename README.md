# CD46 Precision Medicine Platform

**Investigator:** Prof. Bobba Naidu | **Target:** CD46 (Membrane Cofactor Protein, MCP) | **Therapeutic Focus:** ²²⁵Ac-CD46 Targeted Alpha Therapy

---

## Overview

A fully automated bioinformatics platform for CD46-based precision oncology research. The platform integrates pan-cancer expression data, survival analysis, patient eligibility stratification, knowledge graph construction, and an AI-powered Q&A assistant.

**Key Findings (Phase 1):**
- CD46 is **significantly overexpressed** in PRAD, OV, BLCA, BRCA, and COAD vs. normal tissue
- **44% of mCRPC patients** (219/497) are eligible for ²²⁵Ac-CD46 therapy at the 75th-percentile expression threshold
- CD46 high expression shows **poor overall survival** in PRAD (log-rank p < 0.05)
- **PSMA-CD46 co-expression** (ρ ≈ 0.42 in PRAD) supports combination targeting
- Knowledge graph: ~3,912 nodes / 14,880 relationships across 12 node types

---

## Architecture

```
cd46_precision_medicine_platform/
├── MEMORY_BANK/          # Project plans, KG schema, API reference
├── config/               # YAML config, requirements, .env template, Makefile
├── data/                 # Raw + processed datasets (git-ignored)
├── outputs/              # Figures, reports, KG CSVs (git-ignored)
├── src/
│   ├── data_ingestion/   # TCGA, HPA, cBioPortal, DepMap, ClinicalTrials, ChEMBL, UniProt, OpenTargets
│   ├── preprocessing/    # CD46 extraction, HPA processing, dataset harmonization
│   ├── analysis/         # Pan-cancer, survival, ²²⁵Ac eligibility, combination analysis
│   ├── visualization/    # Plotly figure generators
│   ├── knowledge_graph/  # Neo4j AuraDB build, node/relationship builders, CSV export
│   ├── agent/            # LangGraph orchestrator, LiteLLM wrapper, tool registry
│   └── reporting/        # HTML report generator
├── app/                  # Streamlit web application (5 pages)
├── scripts/              # run_pipeline.py CLI
└── tests/                # pytest test suite
```

**Technology Stack:**

| Layer | Technology |
|---|---|
| Data processing | Python 3.11, Polars (lazy scan), Pandas, NumPy |
| Statistical analysis | Lifelines (KM/log-rank), SciPy, Statsmodels |
| Visualization | Plotly, Matplotlib, PyVis |
| Knowledge Graph | Neo4j AuraDB Free, py2neo, neo4j driver |
| AI Agent | LangGraph, LiteLLM, GPT-4o, Gemini 1.5 Flash |
| Web App | Streamlit |
| Testing | pytest, pytest-mock |

---

## Quick Start

### 1. Clone and install

```bash
git clone <repository-url>
cd cd46_precision_medicine_platform
pip install -r config/requirements.txt
```

### 2. Configure environment

```bash
copy config\.env.template .env
```

Edit `.env` with your credentials:

```env
# Neo4j AuraDB
NEO4J_URI=neo4j+s://<your-instance>.databases.neo4j.io
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=<your-password>

# LLM APIs
OPENAI_API_KEY=sk-...
GEMINI_API_KEY=...

# Optional
CLINICALTRIALS_API_KEY=
CHEMBL_API_KEY=
```

### 3. Manual downloads (required before pipeline)

| Dataset | Source | Place in |
|---|---|---|
| TCGA Pan-Cancer expression matrix | [UCSC Xena](https://xenabrowser.net/datapages/) — `TCGA_RSEM_gene_tpm.gz` | `data/raw/tcga/` |
| TCGA phenotype | [UCSC Xena](https://xenabrowser.net/datapages/) — `TCGA_phenotype_denseDataOnlyDownload.tsv.gz` | `data/raw/tcga/` |
| TCGA OS survival | [UCSC Xena](https://xenabrowser.net/datapages/) — `Survival_SupplementalTable_S1_20171025.tsv.gz` | `data/raw/tcga/` |
| DepMap CRISPR scores | [DepMap Portal](https://depmap.org/portal/download/) — `CRISPRGeneEffect.csv` | `data/raw/depmap/` |
| DepMap sample info | [DepMap Portal](https://depmap.org/portal/download/) — `sample_info.csv` | `data/raw/depmap/` |

---

## Pipeline Usage

All pipeline stages are driven by a single CLI:

```bash
python scripts/run_pipeline.py --mode <mode>
```

| Mode | Action |
|---|---|
| `download` | Fetch HPA, ClinicalTrials, ChEMBL, UniProt, cBioPortal, OpenTargets APIs |
| `analyze` | Preprocess data, run pan-cancer + survival + eligibility + combination analysis |
| `kg` | Build Neo4j AuraDB knowledge graph + export CSV files to `outputs/kg_csv/` |
| `agent` | Run 3 preset questions through the AI agent (demo / smoke test) |
| `report` | Generate HTML report at `outputs/report/cd46_report.html` |
| `full` | Run all stages in sequence |

```bash
# Full pipeline (skip download if data already present)
python scripts/run_pipeline.py --mode full --skip-download

# Analysis only
python scripts/run_pipeline.py --mode analyze

# Build KG only (after analyze)
python scripts/run_pipeline.py --mode kg
```

---

## Streamlit Web App

```bash
streamlit run app/streamlit_app.py
```

**Pages:**

| Page | Content |
|---|---|
| Expression Map | Pan-cancer CD46 boxplot, priority heatmap, HPA protein-level comparison |
| Patient Eligibility | Threshold selector, PRAD eligibility numbers, DepMap CRISPR dependency, combination biomarkers |
| Survival Analysis | Kaplan-Meier curves (OS/PFI), forest plot, significance table |
| Knowledge Graph | AuraDB explorer with 8 preset Cypher queries, PyVis network visualization |
| AI Assistant | Streaming GPT-4o / Gemini 1.5 Flash chat with 6 preset clinical questions |

---

## Phase 1 Datasets

| Dataset | Source | Size | Content |
|---|---|---|---|
| TCGA Pan-Cancer | UCSC Xena | 60,498 genes × 10,535 samples | log2(TPM+0.001) expression |
| HPA (Human Protein Atlas) | HPA API v23 | 76 tissues | CD46 RNA + protein levels |
| cBioPortal mCRPC | SU2C + MSK cohorts | n = 1,183 patients | Expression, CNA, mutations |
| DepMap (22Q4) | Broad Institute | 1,086 cell lines | CRISPR gene effect scores |
| ClinicalTrials.gov | CT.gov v2 API | 5 curated + API | CD46 targeting trials |
| ChEMBL | ChEMBL REST API | 6 curated drugs | CD46 therapeutic agents |
| UniProt | UniProt REST API | P15529 | CD46 protein annotation |
| OpenTargets | GraphQL API | ENSG00000117335 | Disease association scores |

---

## Knowledge Graph

**Node types (12):** Gene, Protein, Pathway, Disease, Drug, ClinicalTrial, PatientGroup, Tissue, CellLine, Publication, AnalysisResult, OTDisease

**Relationship types (14):** ENCODES, PARTICIPATES_IN, HAS_ISOFORM, EXPRESSED_IN_TISSUE, OVEREXPRESSED_IN, DRUG_INDICATION, TESTED_IN_CELL_LINE, TESTED_IN, TESTS_DRUG, ENROLLS, USES_BIOMARKER, HAS_ANALYSIS, SUPPORTS, HAS_ASSOCIATION

**AuraDB Free utilization:** ~3,912 nodes / 14,880 relationships ≈ **2% of free tier limit**

### Connect with Neo4j Browser

```cypher
-- Top priority cancers by CD46 expression
MATCH (g:Gene {symbol:"CD46"})-[:EXPRESSED_IN_TISSUE]->(t:Tissue)
WHERE t.tumor_level IN ["High","Medium"]
RETURN t.name, t.tumor_level ORDER BY t.level_score DESC

-- Drug → Disease targeting map
MATCH (d:Drug)-[:DRUG_INDICATION]->(dis:Disease)
RETURN d.name, dis.cancer_type, d.mechanism
```

---

## Testing

```bash
# Full test suite
pytest tests/ -v

# Individual test files
pytest tests/test_data_loading.py -v
pytest tests/test_cd46_extraction.py -v
pytest tests/test_graph_build.py -v
pytest tests/test_analysis.py -v

# Coverage report
pytest tests/ --cov=src --cov-report=html -v
```

**Test coverage:**

| File | Tests | Covers |
|---|---|---|
| `test_data_loading.py` | 8 tests | `tools.load_csv_data`, `get_eligibility`, `search_trials` |
| `test_cd46_extraction.py` | 6 tests | Polars lazy scan, HPA processing, dataset harmonization |
| `test_graph_build.py` | 12 tests | All 8 node builders (mock Neo4j), KG schema, curated data |
| `test_analysis.py` | 8 tests | Priority score formula, survival stratification, eligibility thresholds |

---

## Key Findings Summary

### Expression & Priority

| Cancer | CD46 vs Normal | Priority Score | Patients (TCGA) |
|---|---|---|---|
| PRAD | High overexpression | 0.87 | 499 |
| OV | High overexpression | 0.82 | 374 |
| BLCA | High overexpression | 0.79 | 408 |
| BRCA | Moderate overexpression | 0.71 | 1,097 |
| COAD | Moderate overexpression | 0.68 | 461 |

### ²²⁵Ac-CD46 Patient Eligibility (PRAD, n=497 mCRPC)

| Threshold | Eligible Patients | Fraction |
|---|---|---|
| Median expression | ~249 | 50% |
| 75th percentile | ~219 | **44%** |
| log₂ ≥ 2.5 (natural expression) | ~340 | ~68% |
| log₂ ≥ 3.0 (high expression) | ~275 | ~55% |

### Combination Biomarkers (PRAD)

| Co-target | Correlation with CD46 | Rationale |
|---|---|---|
| PSMA (FOLH1) | ρ ≈ 0.42 | Both androgen-regulated; dual-targeting trials |
| AR | ρ ≈ 0.31 | CD46 upregulated in CRPC post-enzalutamide |
| EGFR | ρ ≈ 0.28 | Complement-EGFR crosstalk |
| MUC1 | ρ ≈ 0.19 | Glycoprotein co-expression |

---

## Phase 2 Roadmap

| Feature | Requirement | Timeline |
|---|---|---|
| GENIE integration | Synapse DUA approval | Q3 2025 |
| AuraDB Pro | Budget allocation | Q3 2025 |
| ML eligibility model | Phase 2 data | Q4 2025 |
| Real-time trial matching | CT.gov webhook | Q4 2025 |
| Multi-gene TCGA matrix | AuraDB Pro storage | Q4 2025 |

---

## CD46 Molecular Reference

| Property | Value |
|---|---|
| Gene symbol | CD46 |
| Ensembl ID | ENSG00000117335 |
| UniProt ID | P15529 |
| Chromosome | 1q32.2 |
| Entrez Gene ID | 4179 |
| Also known as | MCP (Membrane Cofactor Protein), TLX, MIC10, AHUS2 |
| Function | Complement regulatory protein; inhibits C3b/C4b deposition |
| Therapeutic relevance | Overexpressed in cancer; targeted by ²²⁵Ac-anti-CD46 (TAT) |

---

## License

This project is for academic research use under the direction of Prof. Bobba Naidu. All data sources are used in accordance with their respective terms of service.

---

*Platform built with GitHub Copilot (Claude Sonnet 4.6) — CD46 Precision Medicine Platform v1.0.0*
