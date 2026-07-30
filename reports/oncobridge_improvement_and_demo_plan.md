# OncoBridge Intelligence — Improvement Plan, Demo Guide & Dataset Encyclopedia

**Audience:** Platform owner (non-clinician) preparing for external demo  
**Site:** https://oncobridge.eurthtech.com  
**Data freeze:** `2026-07-28-phase4-five-targets` · Platform v1.3.0  
**Prepared:** 2026-07-30

---

## Executive summary

OncoBridge is a **multi-target theranostics research workbench** with **CD46 as the deep reference case study**. Five surface targets are registered (CD46, FOLH1/PSMA, FAP, SSTR2, GRPR), but **most narrative depth, eligibility logic, biomarker scoring, and Research Assistant context remain CD46-centric** even when another target is selected.

**For tomorrow’s demo:** Lead with CD46, show multi-target switching on **Compare Targets** and **Expression Atlas**, and use **KG Query Explorer** for live graph proof. Avoid non-CD46 targets on Dosimetry, Diagnostics, Patient Selection depth, or Clinical Strategy unless you explain “medium-tier slice.”

**Top 5 improvement priorities (post-demo):**

| # | Priority | Effort | Impact |
|---|----------|--------|--------|
| 1 | De-CD46 the Research Assistant (prompts, Evidence tab, orchestrator tools) | 2–3 weeks | Credibility as multi-target platform |
| 2 | PARAM data depth for FOLH1/FAP/SSTR2/GRPR (HPA dosimetry, trials, eligibility) | 3–4 weeks | Real cross-target demos |
| 3 | Performance: self-host fonts, lazy PyVis, skeleton loaders | 1 week | Lighthouse CLS/TBT |
| 4 | Expand KG retrieval in agent (multi-hop Cypher, not one template) | 2 weeks | “KG vs ChatGPT” story becomes true |
| 5 | Stakeholder docs sync (README, this file, slide deck export) | 3 days | Onboarding & fundraising |

---

# Part 1 — Improvement Plan

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

### Concept gaps to explain honestly in demo

| Gap | What to say |
|-----|-------------|
| “Why so much CD46?” | CD46 is our **reference case study** — full GENIE, eligibility, ClinVar, combination biomarkers. Other targets have **medium open-data slices**. |
| “Is this a CD46 company tool?” | No — it’s a **theranostics target intelligence platform**; CD46 is the deepest worked example today. |
| “Can it answer about FAP?” | Expression, survival, trials, PPI, and KG templates work for FAP. Dosimetry and patient eligibility narratives are still CD46-depth. |

---

# Part 2 — Demo Guide (your item #4)

## 2A. Recommended 20-minute demo script

| Min | Where | What to show | What to say (non-medico) |
|-----|-------|--------------|--------------------------|
| 0–2 | **Platform Overview** | Module grid, KG node count, CD46 pipeline stepper | “This is a research workbench for **radioligand drug targets** — not a hospital system. We connect public cancer datasets and a knowledge graph.” |
| 2–5 | **Expression Atlas** (CD46) | Pan-cancer bar chart, KPI chips, target bar | “We pull **TCGA** — US government cancer genomics — and rank 25 cancer types by how much CD46 is expressed.” |
| 5–7 | **Compare Targets** | Switch genes in chart; open **Trial Activity** tab | “Same analysis for **PSMA, FAP, SSTR2, GRPR** — we’re not a single-gene tool. Here’s competitive trial density.” |
| 7–10 | **KG Query Explorer** | Template: “Drugs targeting CD46” → Run → show table | “This hits our **Neo4j graph** — real nodes and edges from ChEMBL and ClinicalTrials.gov, not the LLM making things up.” |
| 10–13 | **Research Assistant** | Ask a preset survival question | “The assistant **retrieves** our CSVs and graph, then writes an answer. It cites PubMed.” |
| 13–16 | **Patient Selection** | GENIE cohort filters (wait ~8s load) | “**GENIE** is real-world cancer sequencing from hospitals — 271k patients. We explore who might be eligible.” |
| 16–18 | **Clinical Strategy Engine** | Scroll the pipeline stages | “This is the **investor/CAB story**: target → drug → patient → trial → outcome in one view.” |
| 18–20 | **Mobile** (optional) | Hamburger nav, hidden dimension rail | “Works on tablet — sidebar navigation, charts readable.” |

### Demo don’ts

- Don’t switch to FAP and open **Dosimetry** or **Diagnostics** (empty or CD46 fallback).  
- Don’t ask Research Assistant about **eligibility %** for non-CD46 (pulls CD46 `patient_groups.csv`).  
- Don’t stay on Survival default tab if you need a **table** — switch to **Significance Table**.  
- Don’t claim “every answer is KG-grounded” — say “**retrieval-augmented** from our datasets and graph.”

---

## 2B. OncoBridge vs generic ChatGPT — the differentiation story

| Question type | ChatGPT | OncoBridge |
|---------------|---------|------------|
| “What is CD46?” | Textbook biology, may hallucinate citations | UniProt + HPA + our TCGA medians with numbers |
| “CD46 hazard ratio in COAD?” | Might invent HR | **Exact HR** from `{gene}_survival_results.csv` / KG `SurvivalResult` node |
| “Trials for CD46?” | Outdated / fabricated NCT IDs | **ClinicalTrials.gov API** + KG `ClinicalTrial` nodes |
| “Drugs targeting PSMA?” | Generic list | **ChEMBL** `Drug-[:TARGETS]->Gene` query with phase |
| “% PRAD patients CD46-high?” | Guess | **PatientGroup** node: n_eligible / tcga_sample_count (CD46 only today) |
| “DepMap dependency?” | Vague | **CRISPR scores** per cell line from graph |

**One-liner for audience:**  
> “ChatGPT **generates** plausible oncology text. OncoBridge **retrieves** your TCGA expression ranks, Cox hazard ratios, trial registry rows, and graph relationships — then explains them.”

---

## 2C. Questions to ask — Research Assistant (by intent)

**Tip:** Switch target bar **before** asking. For CD46 depth, keep CD46 selected.

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
