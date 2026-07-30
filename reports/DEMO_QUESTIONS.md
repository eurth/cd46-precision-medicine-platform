# OncoBridge Demo Questions — Copy-Paste Bank

**Positioning:** Five targets share the same modules. **Select the target in the bar first**, then use the questions below.

Symbols: **FOLH1** (PSMA) · **FAP** · **SSTR2** · **GRPR** · **CD46**

---

## A. Research Assistant — presets (click buttons)

Presets use `{active gene}` — they change when you switch the target bar.

### FOLH1 (PSMA)

1. `Summarise FOLH1 expression across TCGA cancer types with hazard ratios.`
2. `What is the current FOLH1-targeted drug pipeline and which agents are in clinical trials?`
3. `What is the therapeutic rationale for targeting FOLH1 in solid tumours?`
4. `What DepMap evidence supports FOLH1 as a cancer dependency?`
5. `How does FOLH1 compare to other prostate surface targets in the trial landscape?`

### FAP

1. `Summarise FAP expression across TCGA cancer types with hazard ratios.`
2. `What is the current FAP-targeted drug pipeline and which agents are in clinical trials?`
3. `What is the therapeutic rationale for targeting FAP in solid tumours?`
4. `What DepMap evidence supports FAP as a cancer dependency?`
5. `What are the FAP isoforms and which are most relevant for therapeutic targeting?`

### SSTR2

1. `Summarise SSTR2 expression across TCGA cancer types with hazard ratios.`
2. `What is the current SSTR2-targeted drug pipeline and which agents are in clinical trials?`
3. `What is the therapeutic rationale for targeting SSTR2 in solid tumours?`
4. `What DepMap evidence supports SSTR2 as a cancer dependency?`
5. `Which cancers have the strongest combination of SSTR2 over-expression and survival impact?`

### GRPR

1. `Summarise GRPR expression across TCGA cancer types with hazard ratios.`
2. `What is the current GRPR-targeted drug pipeline and which agents are in clinical trials?`
3. `What is the therapeutic rationale for targeting GRPR in solid tumours?`
4. `What DepMap evidence supports GRPR as a cancer dependency?`
5. `Which cancers have the strongest combination of GRPR over-expression and survival impact?`

### CD46

1. `Summarise CD46 expression across TCGA cancer types with hazard ratios.`
2. `What is the current CD46-targeted drug pipeline and which agents are in clinical trials?`
3. `How does CD46 regulate complement evasion in tumour cells?`
4. `What DepMap evidence supports CD46 as a cancer dependency?`
5. `Which cancers have the strongest combination of CD46 over-expression and survival impact?`

### CAB-style (switch target to match question)

| Target | Question |
|--------|----------|
| FOLH1 | `Which cancers have the strongest case for FOLH1-targeted RLT based on expression and survival?` |
| FAP | `What is the optimal biomarker strategy for FAP patient selection in a Phase I trial?` |
| SSTR2 | `What clinical trial evidence exists for anti-SSTR2 therapies?` |
| GRPR | `Design key elements for a Phase I GRPR-targeted RLT dose-escalation study.` |
| CD46 | `How does CD46 compare to PSMA as a therapeutic target in mCRPC?` |

---

## B. KG Query Explorer — templates (per target)

**Path:** Graph → KG Query Explorer → select target → Query Templates → Run

Use the **same seven templates** for every target; only the symbol in the dropdown changes.

| Template | Demo line (any target) |
|----------|------------------------|
| 🎯 Expression: highest cancers | “Ranked TCGA codes from our graph.” |
| 📈 Survival: High = worse prognosis | “Pre-computed Cox hazard ratios.” |
| 💊 Drugs: Agents targeting {gene}? | “ChEMBL-linked drug nodes.” |
| 🧪 Clinical Trials | “NCT IDs from registry.” |
| 📊 Cell lines: DepMap dependency | “Named cell lines + CRISPR scores.” |
| 🔬 Co-expression in PRAD | “Spearman ρ from TCGA.” |
| 📚 Publications | “PubMed nodes in the graph.” |

### Suggested demo rotation (60 sec each)

1. **FOLH1** → 💊 Drugs  
2. **FAP** → 🧪 Clinical Trials  
3. **SSTR2** → 🎯 Expression  
4. **GRPR** → 📚 Publications  
5. **CD46** → 📈 Survival  

---

## C. Natural Language → Cypher (KG Explorer)

**FOLH1:**
```
What clinical trials in the knowledge graph target FOLH1?
```

**FAP:**
```
Which cell lines are most dependent on FAP according to DepMap?
```

**SSTR2:**
```
Which diseases have the highest SSTR2 expression in the knowledge graph?
```

**GRPR:**
```
List drugs in the knowledge graph that target GRPR.
```

**CD46:**
```
Which diseases have the worst survival outcome when CD46 expression is high?
```

---

## D. Cypher Editor (technical audience)

Replace `{SYMBOL}` with FOLH1, FAP, SSTR2, GRPR, or CD46:

```cypher
MATCH (g:Gene {symbol: '{SYMBOL}'})-[r:EXPRESSED_IN_CANCER]->(d:Disease)
RETURN d.tcga_code AS cancer, r.median_tpm_log2 AS median, r.expression_rank AS rank
ORDER BY r.expression_rank ASC
LIMIT 10
```

```cypher
MATCH (drug:Drug)-[:TARGETS]->(g:Gene {symbol: '{SYMBOL}'})
RETURN drug.name, drug.drug_type, drug.max_phase
ORDER BY drug.max_phase DESC
```

```cypher
MATCH (t:ClinicalTrial)-[:TARGETS_GENE]->(g:Gene {symbol: '{SYMBOL}'})
RETURN t.nct_id, t.phase, t.status, t.title
LIMIT 15
```

---

## E. ChatGPT vs OncoBridge

| Generic ChatGPT | OncoBridge (any active target) |
|-----------------|--------------------------------|
| “Top cancers for PSMA?” | FOLH1 → Expression template or Atlas chart |
| “FAP clinical trials?” | FAP → 🧪 Trials template |
| “SSTR2 drugs?” | SSTR2 → 💊 Drugs template |
| “GRPR hazard ratios?” | GRPR → 📈 Survival template |
| “CD46 cell line dependency?” | CD46 → 📊 Cell lines template |

**Sound bite:** “Same platform — **switch the target**, get **verifiable rows**.”

---

## F. Terminology (non-medico)

| Term | Plain English |
|------|---------------|
| FOLH1 / PSMA | Prostate surface target (Pluvicto class) |
| FAP | Stromal marker on cancer-associated fibroblasts |
| SSTR2 | Receptor on neuroendocrine tumours |
| GRPR | Receptor on several solid tumours (e.g. lung) |
| CD46 | Pan-cancer surface antigen |
| TCGA | US government cancer genomics |
| GENIE | Hospital real-world sequencing registry |
| NCT | Trial ID on clinicaltrials.gov |
| KG | Linked database (Neo4j) |
