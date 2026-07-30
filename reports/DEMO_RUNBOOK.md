# OncoBridge Demo Runbook

**Live site:** https://oncobridge.eurthtech.com  
**Duration:** 20–25 minutes (+ 5 min Q&A)  
**Positioning:** **Multi-target platform** — rotate FOLH1, FAP, SSTR2, GRPR, and CD46 via the target bar.

---

## Before you start (2 min)

- [ ] Open Chrome (desktop, full screen)
- [ ] Have this file on a second screen
- [ ] Know the five symbols: **FOLH1** (PSMA), **FAP**, **SSTR2**, **GRPR**, **CD46**

**Opening line (memorize):**

> “OncoBridge is a **multi-target theranostics research workbench**. Five surface targets — PSMA, FAP, SSTR2, GRPR, and CD46 — share the same sixteen modules, datasets, and knowledge graph. Switch the target bar and the whole platform follows.”

---

## Stop 1 — Platform Overview (2 min)

**URL:** https://oncobridge.eurthtech.com/

| Do | Say |
|----|-----|
| Point at target bar / five-gene mention on page | “Five theranostic targets on one architecture — not a single-gene tool.” |
| Scroll module cards | “Sixteen modules: expression, patients, drugs, survival, graph, strategy.” |
| Point at KG node count | “Neo4j graph — genes, trials, drugs, publications linked.” |

**Do not** open with CD46-only narrative.

---

## Stop 2 — Compare Targets (4 min) ⭐ lead multi-target here

**URL:** https://oncobridge.eurthtech.com/competitive_landscape

| Do | Say |
|----|-----|
| Show **Live Expression Compare** chart (all five genes) | “Same TCGA pipeline for **FOLH1, FAP, SSTR2, GRPR, CD46** — side by side.” |
| Tab **Trial Activity & Funnel** | “Trial density — PSMA saturated, others at different maturity.” |
| **Active Competitor Pipeline** table | “Public pipeline — Pluvicto for PSMA, FAP/SSTR2 emerging, CD46 green field.” |
| Tab **Target Biology** | “Biology comparison matrix across all five.” |

---

## Stop 3 — Expression Atlas (3 min) — rotate target bar

**URL:** https://oncobridge.eurthtech.com/cd46_expression_atlas

| Do | Say |
|----|-----|
| Target bar → **FOLH1** | “Expression Atlas follows the active target — PSMA pan-cancer profile.” |
| Note KPI chips refresh | “Twenty-five cancer types from TCGA.” |
| Target bar → **FAP** | “Same module, different gene — stromal FAP expression landscape.” |
| Optional → **SSTR2** | “Neuroendocrine-relevant receptor — NET context.” |

Use **active gene name** in speech, not “CD46 page.”

---

## Stop 4 — KG Query Explorer (5 min) ⭐ graph proof — rotate targets

**URL:** https://oncobridge.eurthtech.com/kg_query_explorer

| Step | Target | Template | Say |
|------|--------|----------|-----|
| 1 | **FOLH1** | 💊 Drugs: Agents targeting FOLH1? | “ChEMBL-linked drugs — Pluvicto-era PSMA landscape.” |
| 2 | **FAP** | 🧪 Clinical Trials | “NCT IDs from ClinicalTrials.gov — verifiable rows.” |
| 3 | **SSTR2** | 🎯 Expression: highest cancers | “Ranked TCGA codes from the graph.” |
| 4 | **GRPR** or **CD46** | 📊 Cell lines / Survival | “DepMap dependency or Cox HR — pre-computed, not LLM.” |

**Key line:**

> “One Cypher template set — we **switch the gene symbol** and rerun. That is multi-target at the graph layer.”

---

## Stop 5 — Research Assistant (4 min) — match active target

**URL:** https://oncobridge.eurthtech.com/research_assistant

| Step | Action |
|------|--------|
| 1 | Target bar → **FOLH1** |
| 2 | Click preset: **“Summarise FOLH1 expression across TCGA cancer types with hazard ratios.”** |
| 3 | Target bar → **FAP** |
| 4 | Click preset: **“What DepMap evidence supports FAP as a cancer dependency?”** |

**Say:**

> “Presets follow the **selected target**. Retrieval from our CSVs and graph — then the model explains.”

---

## Stop 6 — Patient Selection (2 min)

**URL:** https://oncobridge.eurthtech.com/patient_selection

| Do | Say |
|----|-----|
| Wait for load (~8s first time) | “AACR **GENIE** — 271,837 real-world sequenced tumours, target-agnostic cohort layer.” |

---

## Stop 7 — Clinical Strategy Engine (2 min)

**URL:** https://oncobridge.eurthtech.com/clinical_strategy_engine

| Do | Say |
|----|-----|
| Scroll pipeline | “End-to-end: target → biomarker → patient → trial → outcome — for whichever target you’re developing.” |

---

## Closing (1 min)

> “Five targets, one workbench, named datasets — TCGA, GENIE, ClinicalTrials.gov, ChEMBL, Neo4j. Research use only, not clinical advice.”

---

## Emergency fallbacks

| Problem | Fix |
|---------|-----|
| Blank table | Refresh; Survival → **Significance Table** tab |
| Assistant slow | KG Explorer template — faster |
| Wrong target | Use target bar — page reruns for new gene |

---

## Pages to de-emphasize in external demo

Dosimetry and Diagnostics still have uneven depth per target internally — use **Compare Targets + KG Explorer + Expression rotation** instead.

---

## Dataset name-drops (target-agnostic)

| Module | Dataset |
|--------|---------|
| Expression | TCGA / UCSC Xena |
| Protein | Human Protein Atlas |
| Cohorts | AACR GENIE |
| Trials | ClinicalTrials.gov |
| Drugs in KG | ChEMBL |
| Graph | Neo4j AuraDB |
