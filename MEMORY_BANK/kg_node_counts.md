# CD46 Knowledge Graph — Node & Relationship Count Analysis
# REVISED: March 10, 2026 — Confirmed AuraDB state after Phase 1 loaders

---

## ✅ CONFIRMED AURADB STATE (audit_kg.py — March 10, 2026)

| Label | Count |
|---|---|
| CellLine | 1,186 |
| ClinicalTrial | 14 |
| DataSource | 5 |
| Disease | 50 |
| Drug | 3 |
| Gene | 6 |
| Pathway | 3 |
| PatientGroup | 226 |
| Protein | 4 |
| ProteinIsoform | 16 |
| ProteinVariant | 13 |
| Publication | 55 |
| SurvivalResult | 39 |
| Tissue | 81 |
| **TOTAL** | **1,701** |

**Relationships: 1,118 total**
Key rel types: ASSOCIATED_WITH(25), EXPRESSED_IN(324), HAS_CLINICAL_TRIAL(14),
HAS_ISOFORM(16), HAS_PATIENT_GROUP(226), HAS_SURVIVAL_DATA(312),
HAS_VARIANT(13), INVESTIGATES(14), OVEREXPRESSED_IN(20), SUPPORTS(70)

### IMPORTANT: Protein node uniprot_id format
Protein nodes use uniprot_id values like 'P15529-STA-1', NOT 'P15529'.
Always MATCH using `symbol = 'CD46'` when targeting CD46 protein nodes.

---

## AuraDB Free Tier Limits
- Nodes: ~200,000
- Relationships: ~400,000
- Storage: 200 MB

---

## PHASE 1 DESIGN DECISIONS

### GENIE: DEFERRED to Phase 2 — WHY?
- Option A (200k individual patients): FAILS — exceeds both AuraDB Free limits
- Option B (PRAD individual 12k + others aggregated): 12,900 nodes / 52,000 rels — fits but adds complexity
- Decision: Phase 1 completes without GENIE. SU2C mCRPC via cBioPortal provides comparable mCRPC data.

### SU2C mCRPC via cBioPortal (not dbGaP)
- Full dataset (dbGaP): 2-6 week controlled-access review → NOT feasible for 48-hr sprint
- cBioPortal public: 150 SU2C summarized + 1,033 MSK-IMPACT mCRPC patients = 1,183 individual nodes
- Clinically equivalent for pitch purposes

### HPA: Full Individual Tissue Nodes
- 44 normal tissues + 44 tumor tissue nodes = 88 Tissue nodes
- 88 EXPRESSED_IN relationships (protein → tissue)

### DepMap: Individual Cell Lines
- 1,800 CellLine nodes (CD46 expression + CRISPR score as properties)
- 3 rels each: DEPENDS_ON Gene + REPRESENTS Disease × 2

---

## GRAND TOTAL — PHASE 1

| Dataset | Representation | Nodes | Rels |
|---|---|---|---|
| TCGA | Aggregated (33 diseases + 66 groups + 99 results) | 198 | 380 |
| SU2C + MSK mCRPC (cBioPortal) | Individual 1,183 patients | 1,183 | 7,000 |
| HPA (full atlas) | 88 tissue nodes + 88 protein-tissue edges | 176 | 300 |
| DepMap (1,800 cell lines) | Individual + properties | 1,800 | 5,400 |
| Static seed (Gene, Protein, Pathway) | Individual | 395 | 1,200 |
| Drugs + Clinical Trials | Individual | 50 | 200 |
| Publications | Individual | 50 | 150 |
| Open Targets + ChEMBL | Individual | 60 | 250 |
| **TOTAL** | | **3,912** | **14,880** |

**AuraDB Free: 200,000 nodes / 400,000 rels**
**Usage: 3,912 (2.0%) nodes | 14,880 (3.7%) rels**
**✅ FITS — 51× headroom on nodes, 27× on relationships**

---

## PHASE 2 ADDITIONS (post-pitch)

| Dataset | Additional Nodes | Notes |
|---|---|---|
| GENIE PRAD individual (12k) | +12,000 | Synapse DUA required |
| GENIE non-PRAD aggregated | +900 | Included with PRAD batch |
| All TCGA sample nodes (11k) | +11,000 | Optional granularity |
| Full SU2C WGS variants | +5,000 | dbGaP access required |

Total Phase 2: ~32,812 nodes / ~80,000 rels — still within AuraDB Free!

## UPGRADE PATH
- Phase 1 (48hr pitch): AuraDB Free — NO cost
- Phase 2 (all GENIE 200k patients individually): AuraDB Pro $65/mo
- Phase 3 (clinical + PHI): Self-hosted Docker Neo4j Enterprise
