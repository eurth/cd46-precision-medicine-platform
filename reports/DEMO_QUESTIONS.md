# OncoBridge Demo Questions — Copy-Paste Bank

Use these **exact strings** during the demo. Organized by module.

**Golden rule:** Research Assistant + deep patient/biomarker questions → **CD46 only**.  
**KG Query Explorer** → works for all five targets (CD46, FOLH1, FAP, SSTR2, GRPR).

---

## A. Research Assistant — click presets (safest)

These appear as buttons when the chat is empty. **Click; don’t type.**

### Quick-Start (CD46 selected)

1. `Summarise CD46 expression across TCGA cancer types with hazard ratios.`
2. `What is the current CD46-targeted drug pipeline and which agents are in clinical trials?`
3. `How does CD46 regulate complement evasion in tumour cells?`
4. `What DepMap evidence supports CD46 as a cancer dependency?`
5. `What are the CD46 isoforms and which are most relevant for therapeutic targeting?`

### CAB Focus (CD46 selected — clinical audience)

1. `Which cancers have the strongest case for CD46-targeted RLT based on expression and survival?`
2. `What is the optimal biomarker strategy for CD46 patient selection in a Phase I trial?`
3. `How does CD46 compare to PSMA as a therapeutic target in mCRPC?`
4. `Design a Phase I dose-escalation trial for CD46-targeted RLT in mCRPC — key elements?`
5. `What clinical trial evidence exists for anti-CD46 therapies and what are the emerging readouts?`

### Type-in questions (if presets used up)

| Intent | Copy-paste question | What it retrieves |
|--------|---------------------|-------------------|
| Expression | `Which TCGA cancer types show the highest CD46 median expression?` | `{gene}_by_cancer.csv` |
| Survival | `Which cancers have a significant CD46 hazard ratio for overall survival?` | `{gene}_survival_results.csv` |
| Trials | `List active clinical trials targeting CD46.` | ClinicalTrials.gov API |
| KG | `Show me CD46 knowledge graph expression across cancer types.` | Live Neo4j Cypher |
| Literature | `What recent PubMed publications support CD46 as a radioligand target?` | PubMed |
| Protein | `Summarise CD46 protein expression from the Human Protein Atlas.` | HPA CSV |

### Research Assistant — avoid today (non-CD46 or thin data)

- `What percentage of PRAD patients are CD46-high eligible?` — OK on CD46 only
- `What combination biomarkers predict CD46 response with AR-V7?` — CD46 CSV only
- Same eligibility/biomarker questions with **FAP** or **SSTR2** — thin context until post-demo fixes

---

## B. KG Query Explorer — template dropdown (best KG proof)

**Path:** Graph → KG Query Explorer → Query Templates → Run Query

### CD46 (default target)

| # | Select this template | Demo line |
|---|----------------------|-----------|
| 1 | 🎯 Expression: Which cancers have highest CD46? | “Ranked TCGA codes from our graph.” |
| 2 | 📈 Survival: Which cancers show CD46-High = worse prognosis? | “Pre-computed Cox hazard ratios.” |
| 3 | 💊 Drugs: Agents targeting CD46? | “ChEMBL-linked drug nodes.” |
| 4 | 🧪 Clinical Trials: Trials investigating CD46 / related diseases? | “NCT IDs from registry.” |
| 5 | 📊 Cell lines: Which lines depend on CD46? | “DepMap CRISPR dependency.” |
| 6 | 🔬 Co-expression: Genes correlated with CD46 in PRAD? | “Spearman correlation in prostate cancer.” |
| 7 | 📚 Publications: Evidence linked to CD46? | “PubMed nodes in the graph.” |

### FOLH1 / PSMA (switch target bar first)

| # | Template |
|---|----------|
| 1 | 💊 Drugs: Agents targeting FOLH1? |
| 2 | 🧪 Clinical Trials: Trials investigating FOLH1 / related diseases? |
| 3 | 🎯 Expression: Which cancers have highest FOLH1? |

**Say:** “PSMA is FOLH1 in our registry — same graph, prostate radioligand benchmark.”

### FAP (switch target bar)

| # | Template |
|---|----------|
| 1 | 💊 Drugs: Agents targeting FAP? |
| 2 | 📊 Cell lines: Which lines depend on FAP? |

---

## C. KG Query Explorer — Natural Language tab

Paste into the question box (CD46 selected):

```
Which diseases have the worst survival outcome when CD46 expression is high?
```

```
List all drugs in the knowledge graph that target CD46 with max phase 2 or higher.
```

```
What genes are co-expressed with CD46 in prostate cancer?
```

```
Which cell lines are most dependent on CD46 according to DepMap?
```

**FOLH1 (switch target first):**

```
What clinical trials in the knowledge graph target FOLH1?
```

---

## D. KG Query Explorer — Cypher Editor (technical audience)

Read-only queries — paste and **Run**:

### Expression rank
```cypher
MATCH (g:Gene {symbol: 'CD46'})-[r:EXPRESSED_IN_CANCER]->(d:Disease)
RETURN d.tcga_code AS cancer, r.median_tpm_log2 AS median, r.expression_rank AS rank
ORDER BY r.expression_rank ASC
LIMIT 10
```

### Survival (significant, worse prognosis)
```cypher
MATCH (d:Disease)-[:HAS_SURVIVAL_RESULT]->(sr:SurvivalResult)
WHERE sr.gene_symbol = 'CD46'
  AND sr.hazard_ratio > 1.0
  AND sr.p_value < 0.05
RETURN d.tcga_code, sr.hazard_ratio, sr.p_value, sr.endpoint
ORDER BY sr.hazard_ratio DESC
LIMIT 15
```

### Drugs targeting gene
```cypher
MATCH (drug:Drug)-[:TARGETS]->(g:Gene {symbol: 'FOLH1'})
RETURN drug.name, drug.drug_type, drug.max_phase, drug.mechanism
ORDER BY drug.max_phase DESC
```

### Trials
```cypher
MATCH (t:ClinicalTrial)-[:TARGETS_GENE]->(g:Gene {symbol: 'CD46'})
RETURN t.nct_id, t.phase, t.status, t.title
LIMIT 20
```

### DepMap dependency
```cypher
MATCH (cl:CellLine)-[r:DEPENDS_ON]->(g:Gene {symbol: 'CD46'})
RETURN cl.name, cl.cancer_type, r.crispr_score
ORDER BY r.crispr_score ASC
LIMIT 15
```

---

## E. ChatGPT vs OncoBridge — side-by-side script

Read this if audience asks “why not ChatGPT?”

| You ask ChatGPT | You ask OncoBridge | Difference |
|-----------------|-------------------|------------|
| “Top cancers for CD46 expression?” | Expression Atlas chart OR KG template 🎯 | **Numbers from TCGA**, ranked |
| “CD46 hazard ratio in COAD?” | Research Assistant survival question | **Exact HR** from Cox CSV |
| “CD46 clinical trials?” | KG template 🧪 or Assistant trial preset | **NCT IDs** from registry |
| “Drugs targeting PSMA?” | KG → FOLH1 → 💊 Drugs template | **ChEMBL graph edges** |
| “Is CD46 a dependency?” | KG → 📊 Cell lines template | **Named cell lines + CRISPR scores** |

**Sound bite:**

> “ChatGPT writes plausible paragraphs. OncoBridge returns **rows you can verify** — cancer codes, hazard ratios, NCT numbers, cell line names.”

---

## F. Audience-specific question picks

### Investor / business (5 min AI segment only)

1. Assistant preset: `How does CD46 compare to PSMA as a therapeutic target in mCRPC?`
2. KG: 💊 Drugs targeting CD46
3. Compare Targets → Trial Activity tab

### Scientific / translational (full KG segment)

1. KG: 📈 Survival CD46-High worse prognosis
2. KG: 🔬 Co-expression PRAD
3. Cypher: DepMap dependency query (§ D)
4. Assistant: `What DepMap evidence supports CD46 as a cancer dependency?`

### Clinical advisory board (CAB)

Use all five **CAB Focus** presets in Research Assistant (§ A).

### Technical / data engineer

1. KG → Cypher Editor → paste § D queries
2. Show **View Cypher** expander on templates
3. Mention data freeze: `2026-07-28-phase4-five-targets`, Neo4j ~3,586 nodes

---

## G. One-liner answers (if you blank on terminology)

| Term | Your answer |
|------|-------------|
| TCGA | US government cancer genomics — tumour RNA and survival |
| GENIE | Hospital real-world sequencing registry — 271k patients |
| PSMA | Prostate target; our symbol is FOLH1 |
| RLT | Radioligand therapy — radioactive molecule binds a cell-surface target |
| HR > 1 | Higher expression linked to **worse** survival |
| NCT | Clinical trial registry ID — verifiable on clinicaltrials.gov |
| KG / Neo4j | Our linked database of genes, drugs, trials, papers |
| HPA | Human Protein Atlas — where protein is found in tissues |
| DepMap | Which cancer cell lines **need** a gene to survive |
