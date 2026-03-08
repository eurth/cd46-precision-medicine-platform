# CD46 Platform — KG Schema Reference
# Full node and relationship definitions for AuraDB (openCypher)
# March 7, 2026

---

## NODE LABELS & PROPERTIES

### (:Gene)
- symbol: String [indexed, unique]  e.g. "CD46"
- ensembl_id: String [indexed, unique]
- chromosome: String  e.g. "1q32.2"
- uniprot_id: String
- function: String
- therapeutic_rationale: String
- is_complement_regulator: Boolean

### (:Protein)
- symbol: String [indexed]
- uniprot_id: String [unique]
- isoform: String  e.g. "STA-1", "LCA-2"
- molecular_weight_kda: Float
- surface_expressed: Boolean
- cleaved_shed: Boolean  # relevant for sCD46

### (:Disease)
- name: String [indexed]
- tcga_code: String [indexed]  e.g. "PRAD"
- ncit_code: String
- icd10: String
- cancer_type: String
# TCGA-derived
- tcga_sample_count: Integer
- cd46_mean_tpm_log2: Float
- cd46_median_tpm_log2: Float
- cd46_std_tpm_log2: Float
- cd46_expression_rank: Integer   # 1=highest across 33 cancers
- cd46_survival_hr: Float
- cd46_survival_pval: Float
- cd46_survival_log_rank_p: Float
# DepMap-derived
- cd46_cna_amplification_freq: Float
- cd46_cna_deletion_freq: Float
# HPA-derived
- cd46_protein_tumor_score: String  # "Low"/"Medium"/"High"/"Not detected"
# Composite
- priority_score: Float   # 0.0-1.0
- priority_label: String  # "HIGH PRIORITY"/"MODERATE"/"EXPLORATORY"

### (:Tissue)
- name: String [indexed]
- type: String   # "normal" | "tumor"
- hpa_tissue_id: String
- organ_system: String

### (:PatientGroup)
- name: String [indexed, unique]  e.g. "PRAD_CD46_High_TCGA"
- cancer_type: String
- dataset: String   # "TCGA" | "cBioPortal"
- expression_group: String   # "CD46-High" | "CD46-Low"
- threshold_method: String   # "median" | "75th_pct" | "log2tpm_2.5"
- n_patients: Integer
- n_events: Integer
- median_os_months: Float
- median_pfi_months: Float
- cohort_subtype: String   # "localized" | "mCRPC" | "metastatic"

### (:AnalysisResult)
- result_id: String [unique]
- type: String   # "SurvivalHR" | "ExpressionStats" | "CNAFrequency" | "Correlation"
- value: Float
- confidence_interval_low: Float
- confidence_interval_high: Float
- p_value: Float
- fdr: Float
- method: String   # "CoxPH" | "KaplanMeier" | "Spearman" | "Wilcoxon"
- dataset: String
- computed_at: String   # ISO date

### (:Drug)
- name: String [indexed]
- drug_type: String   # "ADC" | "Bispecific" | "CAR-T" | "RadioligandTherapy" | "SmallMolecule"
- target_gene: String
- payload: String
- isotope: String   # "225Ac" | "177Lu" | "90Y"
- developer: String
- clinical_stage: String
- mechanism: String
- chembl_id: String

### (:ClinicalTrial)
- nct_id: String [indexed, unique]
- title: String
- phase: String   # "PHASE1" | "PHASE2" | "PHASE3"
- status: String   # "RECRUITING" | "ACTIVE_NOT_RECRUITING" | "COMPLETED"
- primary_endpoint: String
- enrollment_target: Integer
- sponsor: String
- start_date: String
- primary_completion_date: String
- cd46_expression_required: Boolean

### (:Pathway)
- name: String [indexed]
- reactome_id: String
- go_id: String
- category: String   # "complement" | "signal_transduction" | "immune_evasion"

### (:GenomicVariant)
- variant_id: String [unique]
- gene: String
- consequence: String   # "amplification" | "deletion" | "missense" | "frameshift"
- hgvs: String
- chromosome_locus: String

### (:CellLine)
- name: String [indexed]   e.g. "LNCaP"
- depmap_id: String [unique]
- cancer_type: String
- tissue: String
- cd46_expression_tpm: Float
- cd46_crispr_score: Float   # negative = dependency
- cd46_is_dependency: Boolean   # score < -0.5

### (:Publication)
- pmid: String [unique]
- title: String
- journal: String
- year: Integer
- doi: String
- key_finding: String

### (:DataSource)
- name: String [unique]   # "TCGA" | "HPA" | "DepMap" | "OpenTargets" | "cBioPortal"
- version: String
- access_date: String
- url: String
- patient_count: Integer
- data_type: String

---

## RELATIONSHIP TYPES & PROPERTIES

(:Gene)-[:ENCODES]->(:Protein)
(:Gene)-[:PARTICIPATES_IN]->(:Pathway) { role }
(:Gene)-[:CORRELATED_WITH]->(:Gene) { cancer_type, dataset, spearman_rho, p_value, n_samples }
(:Protein)-[:EXPRESSED_IN]->(:Tissue) { h_score, staining_intensity, fraction_positive, tissue_type }
(:Protein)-[:OVEREXPRESSED_IN]->(:Disease) { fold_change, p_value }
(:Disease)-[:HAS_PATIENT_GROUP]->(:PatientGroup) { group_definition }
(:PatientGroup)-[:HAS_ANALYSIS]->(:AnalysisResult) { analysis_type }
(:PatientGroup)-[:FROM_DATASOURCE]->(:DataSource)
(:Drug)-[:TARGETS]->(:Gene) { mechanism, binding_site, affinity_nm }
(:Drug)-[:TARGETS]->(:Protein) { mechanism, epitope }
(:Drug)-[:INDICATED_FOR]->(:Disease) { approval_status, evidence_level }
(:Drug)-[:TESTED_IN]->(:ClinicalTrial) { arm, dose, route }
(:ClinicalTrial)-[:ENROLLS]->(:Disease) { inclusion_criterion }
(:GenomicVariant)-[:FOUND_IN]->(:PatientGroup) { frequency_pct, frequency_ratio, fdr }
(:GenomicVariant)-[:CONFERS_RESISTANCE_TO]->(:Drug) { evidence_level, mechanism }
(:Pathway)-[:REGULATES]->(:Gene) { regulation_type }
(:Pathway)-[:DYSREGULATED_IN]->(:Disease) { alteration_type, evidence }
(:CellLine)-[:DEPENDS_ON]->(:Gene) { crispr_score, is_essential }
(:CellLine)-[:REPRESENTS]->(:Disease) { fidelity }
(:Publication)-[:SUPPORTS]->(:Drug) { finding }
(:Publication)-[:SUPPORTS]->(:Gene) { context }
(:DataSource)-[:PROVIDES]->(:PatientGroup)

---

## CYPHER CONSTRAINTS & INDEXES (run on graph init)

CREATE CONSTRAINT gene_symbol IF NOT EXISTS FOR (g:Gene) REQUIRE g.symbol IS UNIQUE;
CREATE CONSTRAINT disease_tcga IF NOT EXISTS FOR (d:Disease) REQUIRE d.tcga_code IS UNIQUE;
CREATE CONSTRAINT drug_name IF NOT EXISTS FOR (dr:Drug) REQUIRE dr.name IS UNIQUE;
CREATE CONSTRAINT trial_nct IF NOT EXISTS FOR (t:ClinicalTrial) REQUIRE t.nct_id IS UNIQUE;
CREATE CONSTRAINT pub_pmid IF NOT EXISTS FOR (p:Publication) REQUIRE p.pmid IS UNIQUE;
CREATE CONSTRAINT pg_name IF NOT EXISTS FOR (pg:PatientGroup) REQUIRE pg.name IS UNIQUE;
CREATE CONSTRAINT cellline_id IF NOT EXISTS FOR (c:CellLine) REQUIRE c.depmap_id IS UNIQUE;
CREATE CONSTRAINT protein_uniprot IF NOT EXISTS FOR (pr:Protein) REQUIRE pr.uniprot_id IS UNIQUE;
CREATE CONSTRAINT source_name IF NOT EXISTS FOR (ds:DataSource) REQUIRE ds.name IS UNIQUE;

CREATE INDEX disease_name IF NOT EXISTS FOR (d:Disease) ON (d.name);
CREATE INDEX gene_ensembl IF NOT EXISTS FOR (g:Gene) ON (g.ensembl_id);
CREATE INDEX pg_cancer_group IF NOT EXISTS FOR (pg:PatientGroup) ON (pg.cancer_type, pg.expression_group);
