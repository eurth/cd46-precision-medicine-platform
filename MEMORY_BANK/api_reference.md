# CD46 Platform — Dataset API Reference
# Last Updated: March 9, 2026
# STATUS KEY: ✅ LOADED | ⚠️ PARTIAL | ⬜ TODO | 🔒 BLOCKED

---

## STATUS SUMMARY (March 9, 2026)

| Source | Status | AuraDB Nodes | Notes |
|---|---|---|---|
| TCGA | ✅ LOADED | 50 Disease, 226 PatientGroup, 39 SurvivalResult | Aggregated |
| HPA | ✅ LOADED | 81 Tissue | Curated list (JSON lacked levels) |
| DepMap | ✅ LOADED | 1,186 CellLine | Expression + CRISPR as properties |
| ClinicalTrials.gov | ✅ LOADED | 14 ClinicalTrial | 9 via API + 5 manual |
| UniProt | ✅ LOADED | 4 Protein, 16 ProteinIsoform, 13 ProteinVariant | Full isoforms + variants |
| Open Targets | ⚠️ PARTIAL | 50 Disease (25 via OT) | 25/772 — re-fetch with size:772 |
| cBioPortal mCRPC | ⚠️ PARTIAL | 26 PatientGroup | Sample only; full 1,033 pending |
| PubMed Entrez | ✅ LOADED | 55 Publication | 47 new via biopython |
| ChEMBL | ⚠️ JSON ONLY | 0 new nodes | data/raw/apis/chembl_cd46.json on disk |
| DrugBank Academic | ⬜ TODO | 0 | Sign up at go.drugbank.com |
| STRING DB | ⬜ TODO (in UI) | 0 KG nodes | API works in Streamlit; not in AuraDB yet |
| GENIE Synapse | 🔒 BLOCKED | 0 | Synapse DUA pending |

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

## 6. Open Targets GraphQL API — ⚠️ PARTIAL (25/772 loaded)

Endpoint: https://api.platform.opentargets.org/api/v4/graphql

# CURRENT JSON: data/raw/apis/open_targets_cd46.json — only 25 rows (limit=25 at fetch)
# TODO: Re-fetch with size:772 to get all 772 associations

# FULL FETCH QUERY (run to get all 772):
  query CD46Full {
    target(ensemblId: "ENSG00000117335") {
      associatedDiseases(page: {index: 0, size: 772}) {
        count
        rows {
          disease { id name therapeuticAreas { id name } }
          score
          datasourceScores { id score }
        }
      }
    }
  }

# Original query (size:20 — too small):
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

## 10. DrugBank Academic — ⬜ TODO (next high-impact step)

Sign up: https://go.drugbank.com/releases/latest (free academic license, ~5 min)
Once approved, download: DrugBank Full Database XML
Filter for: CD46 (gene name) or P15529 (UniProt ID) in drug-target interactions
Load script to create: scripts/load_kg_drugbank.py
Expected: ~25 Drug nodes + ~50 TARGETS rels linking Drug → Gene(CD46)

---

## 11. STRING Protein Interactions — ⬜ TODO (in Streamlit UI, not yet in AuraDB)

CD46 interaction partners:
  URL: https://string-db.org/api/json/interaction_partners?identifiers=P15529&species=9606&limit=25
  Returns: array of {stringId_A, stringId_B, preferredName_A, preferredName_B, score, ...}

Currently: Streamlit tab auto-loads this (cached) for display only.
TODO: Load top 20 partners as Gene nodes with INTERACTS_WITH rel in AuraDB.
  Load script to create: scripts/load_kg_string.py

---

## 12. AACR GENIE (Synapse) — 🔒 BLOCKED (~1-2 weeks)

Dataset: syn7222066 (GENIE main release)
Access: synapseclient Python package
  import synapseclient
  syn = synapseclient.Synapse()
  syn.login(authToken=os.getenv("SYNAPSE_AUTH_TOKEN"))
  syn.get("syn7222066", downloadLocation="data/raw/genie/")

CD46 locus: chromosome 1, position ~207,600,000-207,660,000 (GRCh38)
CNA file: data_CNA.txt — look for CD46 or MCP column
Mutation file: data_mutations_extended.txt — filter Hugo_Symbol == "CD46"
Synapse dataset ID: syn7222066
Expected gain when approved: +~12,900 nodes, +~48,000 rels → total ~15,000 nodes
