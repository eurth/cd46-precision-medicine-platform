# Sixth-target onboarding playbook (C6)

Add a new theranostic target to OncoBridge in six steps — **additive only**; never remove CD46 case-study files.

## 1. Register the gene

Edit `config/targets.yaml`:

```yaml
  NEWGENE:
    symbol: NEWGENE
    name: Full protein name
    ensembl_id: ENSG...
    uniprot_id: ...
    data_tier: thin   # stub | thin | medium | full
    case_study: false
    kg_status: stub
    modality_tags: [surface_antigen, radioligand]
```

## 2. Open-data slice (thin → medium)

```bash
python scripts/load_target_slice.py --symbol NEWGENE
python scripts/load_gene_uniprot_gtex_depmap.py --symbol NEWGENE
python scripts/load_gene_trials_hpa.py --symbol NEWGENE
python scripts/build_gene_param_slices.py --symbol NEWGENE
python scripts/build_gene_coverage_slices.py --symbol NEWGENE --fetch-trials
```

Produces: `{gene}_by_cancer.csv`, `{gene}_survival_results.csv`, `{gene}_priority_score.csv`, `{gene}_patient_groups.csv`, `{gene}_trials_summary.csv`, `gtex_{gene}_normal.csv`, etc.

## 3. Agent + UI presets

- Add CAB + mechanism lines in `app/components/agent_prompts.py`
- Add strategy block in `app/components/target_narratives.py`

## 4. Verify

```bash
python scripts/verify_gene_param_slices.py
python scripts/verify_page_links.py
python scripts/verify_kg_rag.py
python -m components.target_narratives  # if __main__ added
```

## 5. Neo4j (optional)

```bash
python scripts/load_gene_trials_hpa.py --symbol NEWGENE
python scripts/load_gene_uniprot_gtex_depmap.py --symbol NEWGENE
```

## 6. Demo checklist

- Target bar shows NEWGENE
- Expression Atlas + Survival load `{gene}_*` CSVs
- Research Assistant presets + source chips reference NEWGENE
- Compare Targets includes the new symbol when expression slice exists

**Depth tiers:** `thin` = expression + survival; `medium` = + trials, GTEx, DepMap, PARAM slices; `full` = curated case-study modules (CD46 reference).
