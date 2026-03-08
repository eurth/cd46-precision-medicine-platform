# CD46 Platform — Dataset API Reference
# All endpoints verified March 7, 2026

---

## 1. TCGA — UCSC Xena (Stream Download)

Expression matrix:
  URL: https://toil-xena-hub.s3.us-east-1.amazonaws.com/download/TcgaTargetGtex_rsem_gene_tpm.gz
  Size: ~2.5 GB compressed
  Format: TSV, rows=genes (60,499), cols=samples (19,131)
  CD46 Ensembl ID: ENSG00000117335
  Strategy: Polars scan_csv lazy → filter row → never load full file

Phenotype metadata:
  URL: https://toil-xena-hub.s3.us-east-1.amazonaws.com/download/TcgaTargetGtex_phenotype.gz

Survival data:
  URL: https://toil-xena-hub.s3.us-east-1.amazonaws.com/download/Survival_SupplementalTable_S1_20171025_xena_sp.gz

---

## 2. HPA — Human Protein Atlas REST API

CD46 protein expression:
  URL: https://www.proteinatlas.org/api/search.php?search=CD46&format=json
  Also: https://www.proteinatlas.org/ENSG00000117335-CD46/tissue

Tissue expression JSON:
  URL: https://www.proteinatlas.org/api/search.php?search=ENSG00000117335&format=json
  Returns: tissue-level RNA + protein expression, pathology scores

---

## 3. ClinicalTrials.gov API v2

CD46 trials:
  URL: https://clinicaltrials.gov/api/v2/studies?query.term=CD46&pageSize=100&format=json
  Also: https://clinicaltrials.gov/api/v2/studies?query.term=CD46+cancer&filter.overallStatus=RECRUITING,ACTIVE_NOT_RECRUITING&format=json

---

## 4. ChEMBL REST API

CD46 target:
  URL: https://www.ebi.ac.uk/chembl/api/data/target/search?q=CD46&format=json
  CD46 ChEMBL target ID: CHEMBL2176 (verify on fetch)

CD46 bioactivities:
  URL: https://www.ebi.ac.uk/chembl/api/data/activity?target_chembl_id=CHEMBL2176&limit=100&format=json

---

## 5. UniProt REST API

CD46 human protein:
  URL: https://rest.uniprot.org/uniprotkb/P15529.json
  Also: https://rest.uniprot.org/uniprotkb/search?query=gene:CD46+AND+organism_id:9606&format=json

---

## 6. Open Targets GraphQL API

Endpoint: https://api.platform.opentargets.org/api/v4/graphql

Query:
  query CD46Target {
    target(ensemblId: "ENSG00000117335") {
      id
      approvedSymbol
      biotype
      associatedDiseases(page: {index: 0, size: 20}) {
        rows {
          disease { id name }
          score
          datatypeScores { id score }
        }
      }
      knownDrugs(size: 20) {
        rows {
          drug { id name maximumClinicalTrialPhase }
          diseaseFromSource { name }
          phase
        }
      }
    }
  }

---

## 7. cBioPortal REST API (SU2C mCRPC)

All prostate studies:
  URL: https://www.cbioportal.org/api/studies?keyword=prostate&projection=SUMMARY

SU2C mCRPC study: su2c_mcrpc_2019
MSK-IMPACT mCRPC: prad_msk_2019

CD46 expression in cohort:
  URL: https://www.cbioportal.org/api/molecular-profiles/{profileId}/genes/{geneId}/values

Sample list endpoint:
  URL: https://www.cbioportal.org/api/sample-lists/{studyId}/sample-ids

Clinical data:
  URL: https://www.cbioportal.org/api/studies/{studyId}/clinical-data

---

## 8. DepMap (Broad Institute)

Download portal: https://depmap.org/portal/data_page/
Files needed:
  - CCLE_expression.csv (all cell lines RNA-seq) ~600MB
  - CRISPRGeneEffect.csv (CRISPR knockout fitness scores)

CD46 column: "CD46 (4179)" in expression file
CD46 CRISPR: same column header pattern

Terms: Non-commercial research use only

---

## 9. PubMed Entrez API (via Biopython)

  from Bio import Entrez
  Entrez.email = "your@email.com"
  handle = Entrez.esearch(db="pubmed", term="CD46 cancer expression therapy", retmax=50)
  records = Entrez.read(handle)
  # Then efetch for abstracts

---

## 10. AACR GENIE (Synapse) — PHASE 2 ONLY

Dataset: syn7222066 (GENIE main release)
Access: synapseclient Python package
  import synapseclient
  syn = synapseclient.Synapse()
  syn.login(authToken=os.getenv("SYNAPSE_AUTH_TOKEN"))
  syn.get("syn7222066", downloadLocation="data/raw/genie/")

CD46 locus: chromosome 1, position ~207,600,000-207,660,000 (GRCh38)
CNA file: data_CNA.txt — look for CD46 or MCP column
Mutation file: data_mutations_extended.txt — filter Hugo_Symbol == "CD46"
