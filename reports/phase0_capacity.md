# Phase 0 capacity & decision sheet

**Date:** 2026-07-28  
**Scope:** Reality check only — no product rewrite, no OAuth, Aura Free only.

## Decisions locked by product owner

| Decision | Value |
|----------|--------|
| Aura tier this enhancement | **Free only** (Pro next release) |
| ETL location | **Laptop** downloads/slices; **not** on shared Linode |
| What ships to Coolify/UI | **Summaries / small processed CSVs** only |
| What lives in Aura KG | Graph nodes/rels (gene-sliced), not raw lakes |
| Google OAuth | **Deferred to next release** |
| Host caution | Shared box; **28 containers**; read-only / light checks only |

## Host (Linode / Coolify) — measured

| Metric | Value | Verdict |
|--------|--------|---------|
| Hostname | `eurthtech-primary` | — |
| RAM | 7.8 GiB total, **~4.7 GiB available** | OK if we add no heavy jobs on host |
| Swap | 495 MiB **fully used** | Soft warning — do not run ETL here |
| Disk `/` | 157G, **92G free** (39% used) | OK |
| Running containers | **28** | Crowded; OncoBridge must stay light |
| OncoBridge mem | **~149 MiB** | Fine |
| Heaviest neighbor | ~743 MiB (other app) | Do not compete |

**Go/no-go for host ETL:** **NO** — ETL stays on laptop.  
**Go/no-go for continuing Streamlit on this host:** **YES** (current footprint is fine).

## Aura Free — measured

| Metric | Value |
|--------|--------|
| Host | `fa8b2a7e.databases.neo4j.io` |
| Nodes | **3,069** / 200,000 (**1.53%**) |
| Relationships | **2,517** / 400,000 (**0.63%**) |
| Headroom | ~197k nodes, ~397k rels |
| Keepalive | Present (`_KeepAlive`, last ping 2026-07-28) |
| 5× current size estimate | ~15k nodes → **fits Free** (well under 150k gate) |

**Go/no-go: 5 thin theranostic targets on Aura Free:** **YES**

Labels present: Gene, Protein, Disease, Drug, ClinicalTrial, Tissue, CellLine, Pathway, Publication, PatientGroup, SurvivalResult, DataSource, ProteinIsoform, ProteinVariant, `_KeepAlive`.

## Local laptop data today

| Path | Size | Role |
|------|------|------|
| `data/raw/` | ~3 GB (gitignored) | Local ETL only — never deploy |
| `data/processed/` | **~8.6 MB** (15 files) | UI-ready summaries (deployable) |

Architecture confirmed:

```
[Public open data: OT S3 / GraphQL / Xena / APIs]
        → laptop ETL (download + slice)
        → data/processed/*.csv (small)
        → git / Coolify image volume (UI)
        → Aura Free KG (graph slice)
```

## Open data probes

### Open Targets GraphQL (interactive, free)

- Endpoint: `https://api.platform.opentargets.org/api/v4/graphql`
- Meta seen: API **26.6.3**, data version **26.06**
- Disease association counts (sample):

| Intended target | Ensembl used | Resolved symbol | Assoc. diseases |
|-----------------|--------------|-----------------|-----------------|
| CD46 | ENSG00000117335 | CD46 | 1111 |
| PSMA (FOLH1) | ENSG00000086205 | FOLH1 | 759 |
| FAP | ENSG00000078098 | FAP | 889 |
| SSTR2 | ENSG00000180616 | SSTR2 | 1327 |
| GRPR | ENSG00000164825 | **DEFB1 (WRONG)** | 455 |

**Action for Phase 2 registry:** verify GRPR Ensembl (likely `ENSG00000126010`) before any load.

### Open Targets on AWS Open Data (bulk, no account)

- Bucket: `s3://open-targets-public-data-releases/` (`eu-west-1`)
- Access: anonymous HTTPS list works (**AWS CLI not installed on this laptop** — not required for probe)
- Releases seen: `platform/25.12/`, `platform/26.03/`, `platform/26.06/`
- Latest dump root: `platform/26.06/output/` (listable)
- Useful prefixes for laptop slices (examples): `association_overall_direct/`, `baseline_expression/`, `disease/`, `drug_molecule/`, `drug_mechanism_of_action/`, `evidence_cancer_gene_census/`, `evidence_chembl/` (further keys under output/), `target/` (confirm when syncing)

**Use:** laptop `aws s3 cp` / HTTPS / polars for **selected Ensembl rows only** — never sync full release to Linode.

### TCGA open on AWS

- Bucket: `s3://tcga-2-open/` listable anonymously
- Prefer keep **UCSC Xena gene extract** path already in repo for Phase 1–4; TCGA S3 optional later

### Azure Genomics Open Datasets

- **Do not use** (deprecated / sunsetting)

### AWS CLI on laptop

- **Not installed** — install later when first OT S3 slice download is needed, or use Python HTTPS/polars readers

## Phase 0 exit checklist

- [x] Capacity sheet written
- [x] Aura Free headroom quantified → **5 targets OK**
- [x] OT GraphQL reachable
- [x] OT + TCGA S3 open listing works without credentials
- [x] OAuth deferred (per owner)
- [x] Host ETL forbidden (swap pressure + 28 containers)

## Next phase (Phase 1 — adjusted)

Per owner constraints, Phase 1 should **not** include Google OAuth. Suggested Phase 1 slice:

1. Research-oriented landing (de-bias CD46 hero) + LICENSE/NOTICE  
2. `config/targets.yaml` stub + freeze banner  
3. Keep admin password gate only  

Then Phase 2: parameterize pipeline for gene registry (CD46 still the only loaded gene until Phase 4).

## Scripts added for repeatability

- `scripts/phase0_aura_capacity.py`
- `scripts/phase0_aura_via_ssh.py`
- `scripts/phase0_probe_open_data.py`
- `scripts/phase0_ot_target_counts.py`
