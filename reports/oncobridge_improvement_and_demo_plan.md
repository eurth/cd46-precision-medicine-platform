# OncoBridge Intelligence — Improvement Plan, Demo Guide & Dataset Encyclopedia

**Audience:** Platform owner (non-clinician) preparing for external demo  
**Site:** https://oncobridge.eurthtech.com  
**Data freeze:** `2026-07-28-phase4-five-targets` · Platform v1.3.0  
**Prepared:** 2026-07-30

---

## Executive summary

OncoBridge is a **multi-target theranostics research workbench** for five surface targets: **FOLH1 (PSMA), FAP, SSTR2, GRPR, and CD46**. All share sixteen modules, the same dataset layer, and one Neo4j knowledge graph. The **target bar** switches the active gene across Expression, survival, KG queries, and the Research Assistant.

**External positioning (presentations & demos):** Treat all five targets with **equal weight**. Lead with **Compare Targets**, rotate the target bar live, and run KG templates for different genes in sequence. Do not describe the product as a “CD46 platform.”

**Engineering backlog (internal — not for stakeholder decks):** Some modules still load richer CSV narratives for CD46 while PARAM depth catches up for other targets. That is a delivery gap, not the product definition. See Part 1C / Sprint RA1.

**Top 5 improvement priorities (post-demo):**

| Priority | Sprint | Status (2026-07-30) |
|----------|--------|---------------------|
| **P1** RA1 Multi-target agent | presets, KG retrieval all intents, `TargetResearchAgent` | **In progress — core shipped** |
| **P2** PARAM data depth | per-gene CSV/ETL, dosimetry, eligibility | Planned (additive ETL) |
| **P3** T1 Performance | CLS min-height, filter collapse | **Partial — CSS + survival** |
| **P4** RA2 KG-RAG | NL→Cypher every intent, source chips | Planned |
| **P5** Docs / README | multi-target positioning | **README updated** |

---

## 1A. Lighthouse & technical performance

**Baseline (2026-07-30 audit, homepage desktop):**

| Category | Score | Target (90-day) |
|----------|-------|-----------------|
| Performance | **38** | 55+ |
| Accessibility | **82** | 90+ |
| Best Practices | **100** | 100 |
| SEO | **82** | 85+ |

| Core Web Vital | Value | Issue | Fix |
|----------------|-------|-------|-----|
| FCP | 0.3–0.5s | OK | — |
| LCP | 1.3–1.4s | OK | — |
| **CLS** | **1.23** | **Critical** — Streamlit reruns shift sticky chrome | Skeleton CSS for target bar; `min-height` on chart containers; defer dimension rail paint |
| **TBT** | **970–1030ms** | Heavy JS (Streamlit + Plotly × N) | Lazy-render charts below fold; `@st.fragment` on filter expanders |
| TTI | 2.2–2.4s | Acceptable | — |

### Sprint T1 — Quick wins (1 week, no framework change)

| ID | Action | File(s) | Lighthouse impact |
|----|--------|---------|-------------------|
| T1.1 | Self-host IBM Plex / Inter / JetBrains Mono (remove blocking `@import`) | `theme_css.py` | FCP, LCP |
| T1.2 | Add `min-height` placeholders for Plotly containers before data load | `theme_css.py`, page patterns | CLS |
| T1.3 | Lazy-load PyVis KG network (render on tab click, not page load) | `4_biomedical_knowledge_graph.py` | TBT, LCP |
| T1.4 | Collapse filter bars by default on mobile via `filter_bar(expanded=False)` + session | `ui_kit.py`, Expression/Survival/Patient | CLS (mobile) |
| T1.5 | Add Lighthouse CI on deploy URL (weekly cron) | `.github/workflows/` or Coolify hook | Regression guard |
| T1.6 | Fix console 404s: `_stcore/health` per-path — reverse-proxy `baseUrlPath` | Coolify/nginx config | Best practices noise |

### Sprint T2 — Streamlit architecture (2–3 weeks)

| ID | Action | Notes |
|----|--------|-------|
| T2.1 | `@st.fragment` on target bar switch + section tabs | Reduces full-page rerun CLS |
| T2.2 | Chart pagination: render max 2 Plotly charts per tab; “Load more” | Patient Selection has 3 charts + 300-row table |
| T2.3 | Cache Neo4j driver + KG stats with longer TTL on read-heavy pages | Cuts 4–8s cold loads |
| T2.4 | Preconnect hints for AuraDB, fonts (if self-hosted CDN) | `streamlit_app.py` inject |

### Sprint T3 — Accessibility (1 week)

| ID | Action |
|----|--------|
| T3.1 | Replace dark inline HTML in Research Assistant tabs 2–3 with `ob-tab-intro-*` classes |
| T3.2 | Ensure all Plotly charts have `title` + axis labels (screen reader via aria on container) |
| T3.3 | Breadcrumb `nav` already has `aria-label` — extend to dimension rail links |
| T3.4 | Alt text audit on Overview module card images |

---

## 1B. UI / product debt (from migration Phases 1–8)

| ID | Item | Status | Next step |
|----|------|--------|-----------|
| U1 | Phase 9 contingency (Panel/Dash) | Not needed | Close unless Streamlit blocks scale |
| U2 | `CD46Agent` class name | Misleading | Rename → `TargetResearchAgent` |
| U3 | Page filenames `1_cd46_*`, `14_cd46_*` | Cosmetic | Alias routes or rename in v2 |
| U4 | README lists 5 pages | Stale | Point to 16 modules + this doc |
| U5 | Encoding artifacts (`â€"`) in Patient Selection | Polish | Grep/fix across `app/pages/` |
| U6 | Research Assistant “How It Works” overclaims KG on every question | Honesty gap | Align copy with orchestrator reality |

---

## 1C. Research Assistant — beyond CD46 (your item #2)

### Current state (honest)

| Layer | CD46-aware? | Detail |
|-------|-------------|--------|
| **Quick-Start presets** | Partially | `{_GENE}` substituted, but complement-evasion question is CD46-only branch |
| **CAB presets** | Weak | PSMA comparison + mCRPC trial design are **prostate/CD46-framed** even for FAP/SSTR2 |
| **Evidence Context tab** | **No** | Hardcoded “CD46 over-expression”, “225Ac-CD46”, “PTEN loss → CD46” |
| **Intent routing** | Gene-param | Uses `get_active_symbol()` for CSV paths |
| **KG retrieval** | Minimal | **One Cypher** — `Gene→EXPRESSED_IN_CANCER→Disease` only when intent = `knowledge_graph` |
| **Eligibility / biomarker / drug intents** | **CD46 CSVs** | `patient_groups.csv`, `cd46_combination_biomarkers.csv`, `priority_score.csv` |
| **Class name** | `CD46Agent` | Psychological + code smell |

### Why it *feels* CD46-only in demo

1. Default target bar = **CD46** on every page load.  
2. CAB questions reference **mCRPC** and **PSMA** — wrong framing for SSTR2 (neuroendocrine) or GRPR (lung/GRPR+).  
3. Evidence tab shows a **CD46 walkthrough** regardless of active target.  
4. Most intents pull **CD46-only depth files** even when FOLH1 is selected.  
5. Only explicit “knowledge graph” / “neo4j” keywords trigger live Cypher — and that query is shallow.

### Sprint RA1 — Make multi-target credible (2 weeks)

| ID | Deliverable |
|----|-------------|
| RA1.1 | **Target-aware preset packs** — 6 Quick-Start + 5 CAB questions per target class: `surface_RLT`, `GPCR_radioligand`, `CAF_stroma` |
| RA1.2 | Rewrite Evidence Context tab dynamically from last answer + active gene |
| RA1.3 | Rename `CD46Agent` → `TargetResearchAgent`; update imports pages 5, 7 |
| RA1.4 | Wire `load_csv_data()` to `{gene}_*` files for **all** intents (drop CD46-only filenames when `gene != CD46`) |
| RA1.5 | Add honesty banner when medium-tier target lacks combination/eligibility CSVs |
| RA1.6 | Expand KG intent to run **template-matched Cypher** (reuse KG Explorer templates) |

### Sprint RA2 — True KG-grounded RAG (3 weeks)

| ID | Deliverable |
|----|-------------|
| RA2.1 | NL → Cypher for **every** question (not just `knowledge_graph` intent), with CSV fallback |
| RA2.2 | Retrieve subgraph: Gene → Drug → Trial → Publication → Disease (max 3 hops) |
| RA2.3 | Show **“Sources used”** chips: AuraDB node IDs, CSV filename, PubMed PMIDs |
| RA2.4 | Side-by-side “ChatGPT would guess / OncoBridge retrieved” panel on demo tab |

---

## 1D. Concept coverage study — all dimensions (your item #3)

### Platform positioning (one sentence)

**OncoBridge connects target biology → expression & safety → patient selection → trials & drugs → survival & strategy**, grounded in open datasets and a Neo4j knowledge graph — with **CD46 as the fully worked example**.

### Nine research dimensions × five targets

**Legend:** ● Full · ◐ Medium (gene-param CSV + KG) · ○ Case-study / CD46 narrative only · — Not applicable

| Dimension | Module | CD46 | FOLH1 (PSMA) | FAP | SSTR2 | GRPR |
|-----------|--------|------|--------------|-----|-------|------|
| **Home / orientation** | Platform Overview | ● | ● | ● | ● | ● |
| **Target / cancer biology** | Expression Atlas | ● | ◐ | ◐ | ◐ | ◐ |
| **Multi-target compare** | Compare Targets | ● | ● | ● | ● | ● |
| **Biomarkers & co-targeting** | Biomarker Panel | ● | ○ | ○ | ○ | ○ |
| **Protein structure & PPI** | PPI Network | ● | ◐ | ◐ | ◐ | ◐ |
| **Diagnostics / imaging** | Diagnostics & Early Detection | ● | ○ | ○ | ○ | ○ |
| **Patient cohorts** | Patient Selection | ● | ○ | ○ | ○ | ○ |
| **Eligibility scoring** | Eligibility Scorer | ● | ◐ | ◐ | ◐ | ◐ |
| **Survival & outcomes** | Survival Outcomes | ● | ◐ | ◐ | ◐ | ◐ |
| **Drug landscape** | Drug Pipeline | ● | ◐ | ◐ | ◐ | ◐ |
| **Radiation safety** | Dosimetry & Safety | ● | ○ | ○ | ○ | ○ |
| **Knowledge graph** | Biomedical KG | ● | ◐ | ◐ | ◐ | ◐ |
| **KG query & NL→Cypher** | KG Query Explorer | ● | ◐ | ◐ | ◐ | ◐ |
| **AI Q&A** | Research Assistant | ● | ◐ | ◐ | ◐ | ◐ |
| **End-to-end strategy** | Clinical Strategy Engine | ● | ○ | ○ | ○ | ○ |

### Coverage expansion roadmap

| Phase | Goal | Key ETL / code |
|-------|------|----------------|
| **C1** (2 wk) | PARAM prompts + UI honesty banners | `5_research_assistant.py`, `targets.py` |
| **C2** (3 wk) | Per-gene HPA dosimetry + GTEx normal tissue for all 5 | `scripts/load_gene_uniprot_gtex_depmap.py`, `12_dosimetry_safety.py` |
| **C3** (3 wk) | Per-gene trial + ChEMBL drug tables in KG + Drug Pipeline | `load_gene_trials_hpa.py`, `11_drug_pipeline.py` |
| **C4** (4 wk) | GENIE co-occurrence for FOLH1/FAP (not only CD46) | `fetch_genie_*.py`, `6_biomarker_panel.py` |
| **C5** (4 wk) | Disease-specific strategy templates (NET for SSTR2, mCRPC for PSMA, etc.) | `13_clinical_strategy_engine.py` |
| **C6** (ongoing) | Sixth target onboarding playbook | `config/targets.yaml` + `load_target_slice.py` |

### Concept gaps — if audience asks tough questions

| Question | What to say |
|----------|-------------|
| “Is this only for one gene?” | No — **five targets** on one workbench. Compare Targets and the target bar show that live. |
| “Which target is supported best?” | **Same modules and graph schema for all five**; we’re expanding narrative depth evenly in upcoming releases. |
| “Can it answer about FAP / SSTR2?” | Yes — expression, survival, trials, PPI, KG templates, and Assistant presets follow the **active target**. |

---

# Part 2 — Demo Guide

## 2A. Recommended 20-minute demo script

| Min | Where | What to show | What to say (non-medico) |
|-----|-------|--------------|--------------------------|
| 0–2 | **Platform Overview** | Module grid, KG count, five-target framing | “Multi-target theranostics workbench — PSMA, FAP, SSTR2, GRPR, CD46 on one platform.” |
| 2–6 | **Compare Targets** | All five genes on one chart; Trial Activity tab | “Same TCGA pipeline for every registered target — side by side.” |
| 6–9 | **Expression Atlas** | Rotate target bar: FOLH1 → FAP → SSTR2 | “Switch the gene — charts and KPIs follow.” |
| 9–13 | **KG Query Explorer** | 💊 Drugs for FOLH1, then FAP, then SSTR2 | “Live graph queries — switch symbol, rerun template.” |
| 13–16 | **Research Assistant** | Presets with FOLH1 then FAP selected | “Retrieval-augmented Q&A for the active target.” |
| 16–18 | **Patient Selection** | GENIE scale | “271k real-world tumours — cohort layer across programs.” |
| 18–20 | **Clinical Strategy** | Pipeline scroll | “Target → patient → trial → outcome — any theranostic program.” |

### Demo don’ts

- Don’t describe the product as a “CD46 tool” in the opening or closing.  
- Don’t stay on one target for the whole demo — **rotate the bar** at least three times.  
- Don’t claim “every answer is full KG-RAG” — say **retrieval-augmented** from datasets + graph.

---

## 2B. OncoBridge vs generic ChatGPT — the differentiation story

| Question type | ChatGPT | OncoBridge |
|---------------|---------|------------|
| “Top cancers for PSMA?” | Generic text | FOLH1 → TCGA ranks / KG expression template |
| “FAP trial landscape?” | May invent NCT IDs | FAP → ClinicalTrials.gov + KG trial nodes |
| “SSTR2 drugs?” | Hallucinated list | SSTR2 → ChEMBL `Drug→TARGETS→Gene` |
| “GRPR survival impact?” | Guess | GRPR → Cox HR from survival CSV / graph |
| “CD46 DepMap dependency?” | Vague | CD46 → cell-line CRISPR rows from graph |

**One-liner:**  
> “ChatGPT **generates** text. OncoBridge **retrieves** rows for **whichever target you select** — then explains them.”

---

## 2C. Questions to ask — Research Assistant (by intent)

**Tip:** Switch target bar **before** asking. Use the matching section in `DEMO_QUESTIONS.md` (equal block per target).

### Expression (pulls TCGA + HPA CSVs)

```
Summarise CD46 expression across TCGA cancer types with hazard ratios.
Which cancers have the strongest combination of FOLH1 over-expression and survival impact?
What DepMap evidence supports FAP as a cancer dependency?
```

### Survival (pulls `{gene}_survival_results.csv`)

```
Which cancers show significant CD46-associated survival differences?
What is the hazard ratio for GRPR in lung adenocarcinoma?
```

### Trials (pulls ClinicalTrials.gov search)

```
What is the current CD46-targeted drug pipeline and which agents are in clinical trials?
What clinical trial evidence exists for anti-PSMA therapies?
```

### Drugs / biomarkers (⚠️ CD46-heavy CSVs today)

```
What are the combination biomarker correlations for CD46 in mCRPC?
[For FAP — expect thinner context until C3 ships]
```

### Knowledge graph (explicit KG keywords — live Cypher)

```
Show me CD46 knowledge graph expression across cancer types.
What does the knowledge graph say about FOLH1 disease relationships?
```

### Literature (PubMed)

```
What recent PubMed publications support CD46 as a radioligand target?
```

---

## 2D. Questions to ask — KG Query Explorer (strongest KG proof)

**Use Query Templates tab.** Results appear as tables you can screenshot.

| Template (gene = active target) | What it proves | Good demo line |
|---------------------------------|----------------|----------------|
| 🎯 Expression: highest cancers | `Gene→EXPRESSED_IN_CANCER→Disease` with ranks | “Here are the exact TCGA codes and median TPM ranks from our graph.” |
| 📈 Survival: High = worse prognosis | `Disease→HAS_SURVIVAL_RESULT` with HR, p-value | “These hazard ratios are pre-computed Cox results, not LLM estimates.” |
| 💊 Drugs: Agents targeting gene | `Drug→TARGETS→Gene` from ChEMBL | “ChEMBL drug phases linked in the graph.” |
| 🧪 Clinical Trials | `ClinicalTrial→TARGETS_GENE→Gene` | “Real NCT IDs from ClinicalTrials.gov ingestion.” |
| 📚 Publications | `Publication→SUPPORTS→Gene` | “PubMed evidence nodes.” |
| 🔬 Co-expression in PRAD | `Gene→CORRELATED_WITH→Gene` | “Spearman ρ from TCGA co-expression load.” |
| 📊 Cell lines: DepMap dependency | `CellLine→DEPENDS_ON→Gene` | “CRISPR dependency scores — cell line names you can verify on depmap.org.” |
| 🧬 Protein / pathway | `Gene→PARTICIPATES_IN→Pathway` | “Pathway context from UniProt/GO load.” |

### Natural Language → Cypher (advanced demo)

```
Which diseases have the worst survival outcome when CD46 is high?
List all Phase 2 trials targeting FOLH1.
What proteins interact with FAP in the knowledge graph?
```

**Fallback:** If NL→Cypher fails, keyword-match routes to nearest template (show the generated Cypher in expander).

### Cypher Editor (expert audience)

```cypher
MATCH (g:Gene {symbol: 'CD46'})-[r:EXPRESSED_IN_CANCER]->(d:Disease)
RETURN d.tcga_code, r.median_tpm_log2, r.expression_rank
ORDER BY r.expression_rank LIMIT 10
```

---

## 2E. Getting more relevant KG searches

| Technique | How |
|-----------|-----|
| **Use gene symbol in question** | “FOLH1 trials” not “PSMA trials” (alias may miss) |
| **Name the relationship** | “drugs **targeting**”, “trials **investigating**”, “**co-expression**” |
| **Specify cancer code** | “in PRAD”, “LUAD”, “COAD” — matches `Disease.tcga_code` |
| **Use KG Explorer first** | Run template → copy working Cypher → adapt in editor |
| **Ask for numbers** | “hazard ratio”, “median TPM”, “CRISPR score” — forces structured retrieval |
| **Avoid vague “tell me about”** | Triggers `general` intent → thin priority summary |

---

# Part 3 — Dataset & Dimension Encyclopedia (your item #5)

*Plain-language reference for non-clinicians. “Specialty” = which field of medicine/research uses this data.*

---

## 3A. The five research targets

| Symbol | Common name | What it is (plain English) | Typical cancer context | Modality |
|--------|-------------|----------------------------|------------------------|----------|
| **CD46** | MCP / membrane cofactor protein | Surface protein that helps tumours evade immune complement attack | Pan-cancer; **mCRPC** case study | Alpha radioligand therapy (α-RLT) |
| **FOLH1** | **PSMA** | Prostate-specific membrane antigen — classic prostate cancer target | Prostate (mCRPC); Pluvicto® | Beta/gamma RLT (177Lu-PSMA) |
| **FAP** | Fibroblast activation protein | Marker on cancer-associated fibroblasts (stroma), not tumour cells themselves | Pancreatic, sarcoma, many solids | FAPI PET tracers, emerging RLT |
| **SSTR2** | Somatostatin receptor 2 | G-protein receptor overexpressed on neuroendocrine tumours | NET, GEP-NET | 177Lu-DOTATATE (Lutathera®) |
| **GRPR** | Gastrin-releasing peptide receptor | GPCR target in lung and other solid tumours | Lung, breast, prostate subsets | Bombesin-analogue radioligands |

**Data depth today:** CD46 = **full case study**. Others = **medium slice** (expression, survival, basic KG, trials sample).

---

## 3B. Dataset encyclopedia

### Genomics & expression

| Dataset | Full name | Specialty | What it contains | Version in platform | Used in modules |
|---------|-----------|-----------|------------------|---------------------|-----------------|
| **TCGA** | The Cancer Genome Atlas | Oncology genomics | Tumour RNA-seq, mutations, clinical for ~11,000 patients across 33 cancer types | PANCAN via **UCSC Xena** | Expression Atlas, Survival, Patient Selection, Eligibility, Compare, Strategy, Assistant, KG |
| **Xena** | UCSC Xena Browser | Bioinformatics | Harmonised TCGA matrices (log₂ TPM+1) | RNAseq v2 PANCAN | Same as TCGA |
| **GTEx** | Genotype-Tissue Expression | Normal tissue biology | Healthy tissue mRNA — **safety / off-tumour expression** | v8 | Expression Atlas, Diagnostics, Dosimetry |
| **DepMap** | Cancer Dependency Map | Functional genomics | CRISPR screens: is gene **required** for cancer cell survival? | 24Q2 / 25Q3 | Expression Atlas, Assistant, KG (CellLine nodes) |

### Proteomics & structure

| Dataset | Full name | Specialty | What it contains | Used in modules |
|---------|-----------|-----------|------------------|-----------------|
| **HPA** | Human Protein Atlas | Pathology / proteomics | Protein staining (IHC), H-scores, tissue maps | Expression, Biomarker, Dosimetry, Diagnostics, Assistant |
| **UniProt** | Universal Protein Resource | Molecular biology | Protein sequence, isoforms, domains | PPI, KG, Diagnostics, tooltips |
| **AlphaFold** | DeepMind structure DB | Structural biology | Predicted 3D protein structure | Expression (gene chip links), KG |
| **STRING** | Search Tool for Recurring Instances of Neighbouring Genes | Systems biology | Protein–protein interaction network | PPI Network, KG |

### Clinical & real-world

| Dataset | Full name | Specialty | What it contains | Used in modules |
|---------|-----------|-----------|------------------|-----------------|
| **GENIE** | AACR Project Genomics Evidence Neoplasia Information Exchange | Precision oncology / RWE | **271,837** sequenced tumours from academic centres | Patient Selection, Biomarker, Eligibility, Overview |
| **ClinicalTrials.gov** | US NIH trial registry | Clinical research ops | Phase, sponsor, status, NCT ID for interventional studies | Drug Pipeline, Assistant, KG, Compare, Strategy |
| **cBioPortal** | Cancer Genomics Portal | Translational oncology | Mutation frequencies (SU2C/MSK mCRPC studies) | Patient Selection, Biomarker, Diagnostics |

### Drug & target discovery

| Dataset | Full name | Specialty | What it contains | Used in modules |
|---------|-----------|-----------|------------------|-----------------|
| **ChEMBL** | EBI bioactivity database | Medicinal chemistry | Drugs, mechanisms, max clinical phase | Drug Pipeline, KG, Assistant |
| **Open Targets** | EBI / GSK / others | Target validation | Disease–gene associations, tractability | KG, Compare, Assistant |

### Literature & variants

| Dataset | Full name | Specialty | What it contains | Used in modules |
|---------|-----------|-----------|------------------|-----------------|
| **PubMed** | NCBI literature index | All biomedical | Paper titles, abstracts, PMIDs | Assistant (citations), KG Publication nodes |
| **ClinVar** | NCBI clinical variants | Medical genetics | Pathogenic germline/somatic variant records | Diagnostics (CD46 today) |

### Internal graph

| Dataset | Full name | Specialty | What it contains | Scale |
|---------|-----------|-----------|------------------|-------|
| **OncoBridge KG** | Neo4j AuraDB knowledge graph | Knowledge engineering | Genes, diseases, drugs, trials, publications, pathways, cell lines — linked | ~3,586 nodes / ~3,511 rels |

**Node types:** Gene, Protein, Disease, Tissue, PatientGroup, SurvivalResult, ClinicalTrial, Drug, Publication, Pathway, CellLine, DataSource  
**Key relationships:** EXPRESSED_IN_CANCER, HAS_SURVIVAL_RESULT, TARGETS, TARGETS_GENE, SUPPORTS, CORRELATED_WITH, DEPENDS_ON, PARTICIPATES_IN, INTERACTS_WITH

---

## 3C. Nine platform dimensions (what each module is *for*)

| # | Dimension | Module | One-line purpose | Primary datasets |
|---|-----------|--------|------------------|------------------|
| 1 | **Home** | Platform Overview | Orient visitor; show scope & pipeline | Neo4j KPIs, module map |
| 2 | **Target / Cancer** | Expression Atlas, Compare Targets | “Is this gene expressed in the right cancers?” | TCGA, HPA, GTEx, DepMap |
| 3 | **Biomarkers** | Biomarker Panel | “What else should we measure with the target?” | GENIE, combination CSVs, cBioPortal |
| 4 | **Proteins** | PPI Network, Diagnostics | Structure, interactions, imaging/diagnostic angle | STRING, UniProt, HPA, GTEx, ClinVar |
| 5 | **Patients** | Patient Selection, Eligibility | “Who gets the drug?” | GENIE, TCGA thresholds, patient_groups |
| 6 | **Survival** | Survival Outcomes | “Does high expression mean worse outcome?” | TCGA Cox/KM results |
| 7 | **Drugs / Safety** | Drug Pipeline, Dosimetry | Pipeline landscape + normal-tissue safety | ChEMBL, trials, HPA/GTEx |
| 8 | **Graph / Ask** | Biomedical KG, KG Explorer, Research Assistant | Query linked evidence; AI Q&A | Neo4j, all sources above |
| 9 | **Strategy** | Clinical Strategy Engine | End-to-end development narrative | All — curated storyline |

---

## 3D. Acronym cheat sheet (for slides)

| Acronym | Expand | Remember as |
|---------|--------|---------------|
| TCGA | The Cancer Genome Atlas | Big US cancer genomics project |
| mCRPC | metastatic castration-resistant prostate cancer | Late-stage prostate |
| RLT / RLT | radioligand therapy | Radioactive drug that binds a target |
| α-RLT | alpha radioligand therapy | Uses alpha emitters (e.g. 225Ac) |
| PSMA / FOLH1 | prostate-specific membrane antigen | Prostate target (Pluvicto) |
| NET | neuroendocrine tumour | SSTR2 indication |
| GENIE | AACR real-world genomics registry | Hospital sequencing at scale |
| HPA | Human Protein Atlas | Protein staining atlas |
| HR | hazard ratio | Survival statistics (>1 = worse) |
| KM | Kaplan-Meier | Survival curve method |
| NCT | National Clinical Trial number | Trial registry ID |
| KG | knowledge graph | Connected database of entities |
| CAB | Clinical Advisory Board | Expert review panel (your audience type) |

---

## 3E. Presentation slide outline (copy to PowerPoint / Canva)

1. **Title** — OncoBridge Intelligence: Multi-target theranostics research workbench  
2. **Problem** — Fragmented datasets; generic AI hallucinates oncology numbers  
3. **Solution** — 16 modules × 9 dimensions × 5 targets × 1 knowledge graph  
4. **Architecture** — Streamlit UI → CSV/parquet layer → Neo4j Aura → public APIs  
5. **Data freeze** — screenshot of banner; list 12 source logos  
6. **CD46 case study** — pipeline stepper (target → biomarker → patient → trial)  
7. **Multi-target** — Compare Targets screenshot (5 genes one chart)  
8. **KG proof** — KG Explorer drug query result table  
9. **AI differentiation** — ChatGPT vs OncoBridge table (from §2B)  
10. **Roadmap** — PARAM expansion, RA2 KG-RAG, performance  
11. **Disclaimer** — Research use only; not a medical device  

---

## Appendix — File references

| Topic | Path |
|-------|------|
| Target registry | `config/targets.yaml` |
| Data freeze banner | `config/data_freeze.yaml` |
| Research Assistant | `app/pages/5_research_assistant.py` |
| Agent orchestrator | `src/agent/orchestrator.py` |
| KG templates | `app/pages/7_kg_query_explorer.py` |
| Named Cypher Q1–Q8 | `src/knowledge_graph/queries.py` |
| UI migration status | `reports/ui_migration_plan.md` |
| Live audit 2026-07-30 | (Playwright session — ask to save `reports/live_audit_2026-07-30.md`) |

---

*Research use only. Not a medical device. Verify primary sources before clinical or publication decisions.*
