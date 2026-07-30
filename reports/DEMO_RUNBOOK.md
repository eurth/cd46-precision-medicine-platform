# OncoBridge Demo Runbook — Tomorrow

**Live site:** https://oncobridge.eurthtech.com  
**Duration:** 20–25 minutes (+ 5 min Q&A)  
**Rule:** Keep **CD46** selected except on **Compare Targets** and when showing **PSMA/FAP** in KG Explorer.

---

## Before you start (2 min)

- [ ] Open Chrome (desktop, full screen)
- [ ] Confirm target bar shows **CD46** selected
- [ ] Have this file open on a second screen or printed
- [ ] Optional: pre-load Patient Selection in a background tab (slow first load ~8s)

**Opening line (memorize):**

> “OncoBridge is an open research workbench for **radioligand and surface-antigen target intelligence**. It connects public cancer datasets and a knowledge graph — so we **retrieve real numbers**, not generic AI guesses. CD46 is our deepest worked example; the platform supports five theranostic targets.”

---

## Stop 1 — Platform Overview (2 min)

**URL:** https://oncobridge.eurthtech.com/

| Do | Say |
|----|-----|
| Scroll module cards slowly | “Sixteen modules across nine research dimensions — expression, patients, drugs, survival, knowledge graph, and strategy.” |
| Point at KG node count | “About three and a half thousand nodes in our Neo4j graph — genes, trials, drugs, publications, linked together.” |
| Point at CD46 pipeline stepper | “CD46 is our reference **alpha radioligand** case study — from target biology through trials.” |

**Do not:** Click into modules yet. Set the frame.

---

## Stop 2 — Expression Atlas (4 min)

**URL:** https://oncobridge.eurthtech.com/cd46_expression_atlas

| Do | Say |
|----|-----|
| Point at KPI chips (25 cancers, COAD top) | “TCGA pan-cancer survey — government genomics data, twenty-five cancer types profiled.” |
| Show horizontal bar chart | “Highest median CD46 expression — colon, lung, prostate among the leaders.” |
| Expand **Chart options** only if asked | “Filters are collapsed so the chart is above the fold.” |
| Click tab **Protein & Safety** | “Human Protein Atlas — protein-level evidence, not just RNA.” |

**If chart doesn’t load:** Refresh once. Wait 3s.

---

## Stop 3 — Compare Targets (4 min) ⭐ multi-target moment

**URL:** https://oncobridge.eurthtech.com/competitive_landscape

| Do | Say |
|----|-----|
| Show default **Live Expression Compare** chart | “Same TCGA pipeline for **five targets**: CD46, PSMA, FAP, SSTR2, GRPR — not a single-gene tool.” |
| Click tab **Trial Activity & Funnel** | “Competitive trial density — PSMA is saturated; CD46 is greener field.” |
| Scroll to **Active Competitor Pipeline** table | “Curated public pipeline — Pluvicto for PSMA, emerging CD46 agents.” |
| Click tab **Target Biology** | “Side-by-side biology comparison matrix.” |

---

## Stop 4 — KG Query Explorer (5 min) ⭐ “not ChatGPT” moment

**URL:** https://oncobridge.eurthtech.com/kg_query_explorer

**Ensure CD46 is selected in target bar.**

| Step | Action |
|------|--------|
| 1 | Tab: **Query Templates** |
| 2 | Dropdown: **💊 Drugs: Agents targeting CD46?** |
| 3 | Click **Run Query** |
| 4 | Point at results table (drug name, type, max phase) | |

**Say:**

> “This is a live Cypher query against our Aura knowledge graph — ChEMBL and curated theranostic agents. ChatGPT would invent drug names; we return **linked nodes with clinical phase**.”

**Optional second query (30 sec):**

- Template: **🧪 Clinical Trials: Trials investigating CD46 / related diseases?**
- Say: “Real **NCT IDs** from ClinicalTrials.gov ingestion.”

**Optional third query (switch target):**

- Target bar → **FOLH1** (PSMA)
- Template: **💊 Drugs: Agents targeting FOLH1?**
- Say: “Same graph schema — different gene symbol. Multi-target is real at the graph layer.”

**Advanced (only if audience is technical):**

- Tab **Cypher Editor** → paste from `DEMO_QUESTIONS.md` § Cypher examples → Run

---

## Stop 5 — Research Assistant (4 min)

**URL:** https://oncobridge.eurthtech.com/research_assistant

**Ensure CD46 selected.**

| Step | Action |
|------|--------|
| 1 | Click preset button (don’t type yet): **“Summarise CD46 expression across TCGA cancer types with hazard ratios.”** |
| 2 | Wait for stream to finish (~15–30s) |
| 3 | Expand **Sources** / citations if visible |
| 4 | Click second preset: **“What is the current CD46-targeted drug pipeline and which agents are in clinical trials?”** |

**Say:**

> “The assistant **classifies the question**, pulls our CSVs and graph context, then synthesizes an answer. PubMed citations are appended — retrieval-augmented, not pure generation.”

**Do not ask (today):** eligibility %, combination biomarkers, or PTEN/CD46 for non-CD46 targets.

---

## Stop 6 — Patient Selection (3 min)

**URL:** https://oncobridge.eurthtech.com/patient_selection

| Do | Say |
|----|-----|
| Wait for load | “AACR **GENIE** — real-world sequencing from academic hospitals, two hundred seventy-one thousand patients.” |
| Open **Filter 271,837 GENIE patients** expander briefly | “Cohort filters — cancer type, alteration context.” |
| Show table / charts | “Who might be in scope for a precision trial — grounded in observed genomics.” |

---

## Stop 7 — Clinical Strategy Engine (2 min)

**URL:** https://oncobridge.eurthtech.com/clinical_strategy_engine

| Do | Say |
|----|-----|
| Scroll top to bottom | “End-to-end narrative: target → biomarker → patient → trial → outcome — the CAB / investor view.” |

---

## Closing (1 min)

**Closing line:**

> “We’re research-grade, not clinical advice. Everything traces to named datasets — TCGA, GENIE, ClinicalTrials.gov, ChEMBL, and our Neo4j graph. Happy to go deeper on any module.”

**Disclaimer (if asked):** Research use only. Not a medical device.

---

## Emergency fallbacks

| Problem | Fix |
|---------|-----|
| Blank table | Refresh; switch tab (Survival → Significance Table) |
| Assistant timeout | Use KG Explorer template instead — faster, more reliable |
| Slow Patient Selection | Skip or say “pre-loading cohort” and use Strategy instead |
| Wrong target selected | Click **CD46** in target bar; page reruns |
| Neo4j offline | KG Explorer shows fallback stats; use Expression Atlas + Assistant CSV intents |

---

## Pages to skip in main demo

| Page | Why |
|------|-----|
| Dosimetry & Safety | CD46-static HPA data only |
| Diagnostics & Early Detection | CD46-depth narrative |
| Admin / Debug | Internal |

---

## Quick reference — dataset name-drops

| When you show… | Say this dataset |
|----------------|------------------|
| Expression chart | **TCGA** via UCSC Xena |
| Protein tab | **Human Protein Atlas (HPA)** |
| GENIE cohort | **AACR GENIE** real-world genomics |
| Trial table | **ClinicalTrials.gov** |
| Drug query in KG | **ChEMBL** + graph |
| Survival HR | **TCGA Cox** survival results |
| Assistant citations | **PubMed** |
