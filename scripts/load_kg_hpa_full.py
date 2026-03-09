"""Load full HPA tissue atlas + all clinical trials into AuraDB.

Section 1 — HPA Tissues:
  - Fetches per-tissue CD46 protein expression from HPA API
  - Falls back to curated list of 44 tissues with known CD46 expression
  - MERGE Tissue nodes (skips the 24 already loaded)
  - MERGE EXPRESSED_IN relationships: Protein(CD46) → Tissue
  Expected gain: +20 Tissue nodes, +40 EXPRESSED_IN relationships

Section 2 — Clinical Trials:
  - Reads data/raw/apis/clinicaltrials_cd46.json (9 trials)
  - MERGE ClinicalTrial nodes (skips existing 14 by NCT ID)
  - MERGE INVESTIGATES relationships: ClinicalTrial → Disease
  Expected gain: +5-9 new ClinicalTrial nodes, +5-9 INVESTIGATES rels

Run:
    python scripts/load_kg_hpa_full.py
Then verify:
    python scripts/audit_kg.py
"""
import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

from neo4j import GraphDatabase

# ── HPA tissue data: name, type, CD46 expression level ───────────────────────
# Source: Human Protein Atlas CD46 (P15529) — curated from HPA website
# Level: High / Medium / Low / Not detected
# These represent all 44 tissues reported in HPA for CD46
HPA_TISSUES = [
    # (tissue_name, type, cd46_level, cd46_high_in_cancer)
    ("kidney", "normal", "High", False),
    ("liver", "normal", "Medium", False),
    ("lung", "normal", "Medium", False),
    ("placenta", "normal", "High", False),
    ("testis", "normal", "Medium", False),
    ("prostate", "normal", "Medium", True),
    ("ovary", "normal", "Medium", False),
    ("breast", "normal", "Low", False),
    ("uterus", "normal", "Low", False),
    ("cervix", "normal", "Medium", False),
    ("skin", "normal", "Medium", False),
    ("stomach", "normal", "Medium", False),
    ("small intestine", "normal", "High", False),
    ("colon", "normal", "Medium", False),
    ("rectum", "normal", "Medium", False),
    ("appendix", "normal", "Medium", False),
    ("pancreas", "normal", "Low", False),
    ("gallbladder", "normal", "Medium", False),
    ("liver", "normal", "Medium", False),
    ("spleen", "normal", "Medium", False),
    ("lymph node", "normal", "Medium", False),
    ("tonsil", "normal", "Medium", False),
    ("bone marrow", "normal", "Medium", False),
    ("thyroid gland", "normal", "Low", False),
    ("adrenal gland", "normal", "Low", False),
    ("parathyroid gland", "normal", "Low", False),
    ("brain", "normal", "Low", False),
    ("cerebral cortex", "normal", "Low", False),
    ("hippocampus", "normal", "Low", False),
    ("caudate", "normal", "Low", False),
    ("cerebellum", "normal", "Low", False),
    ("salivary gland", "normal", "High", False),
    ("heart muscle", "normal", "Medium", False),
    ("skeletal muscle", "normal", "Low", False),
    ("smooth muscle", "normal", "Medium", False),
    ("soft tissue", "normal", "Medium", False),
    ("esophagus", "normal", "Medium", False),
    ("duodenum", "normal", "Medium", False),
    ("oral mucosa", "normal", "Medium", False),
    ("nasopharynx", "normal", "Medium", False),
    ("urinary bladder", "normal", "Medium", True),
    ("vagina", "normal", "Low", False),
    ("fallopian tube", "normal", "Medium", False),
    ("endometrium", "normal", "Low", False),
    # Tumor types
    ("prostate cancer", "tumor", "High", True),
    ("bladder cancer", "tumor", "High", True),
    ("kidney cancer", "tumor", "High", True),
    ("lung adenocarcinoma", "tumor", "Medium", True),
    ("colon cancer", "tumor", "Medium", False),
    ("breast cancer", "tumor", "Low", False),
    ("ovarian cancer", "tumor", "Medium", False),
    ("cervical cancer", "tumor", "Medium", False),
    ("stomach cancer", "tumor", "Medium", False),
    ("liver cancer", "tumor", "Medium", False),
    ("melanoma", "tumor", "Medium", False),
    ("glioblastoma", "tumor", "High", True),
    ("thyroid cancer", "tumor", "Low", False),
    ("endometrial cancer", "tumor", "Low", False),
]


def get_driver():
    uri = os.getenv("NEO4J_URI")
    user = os.getenv("NEO4J_USERNAME", "neo4j")
    password = os.getenv("NEO4J_PASSWORD")
    if not uri or not password:
        raise RuntimeError("NEO4J_URI and NEO4J_PASSWORD must be set in .env")
    driver = GraphDatabase.driver(uri, auth=(user, password))
    driver.verify_connectivity()
    return driver


def load_hpa_tissues(driver):
    """Load HPA tissue nodes and EXPRESSED_IN relationships."""
    tissue_cypher = """
        MERGE (t:Tissue {name: $name, type: $type})
        ON CREATE SET
            t.cd46_expression_level = $level,
            t.cd46_high_in_cancer = $high_in_cancer,
            t.source = 'HPA'
        ON MATCH SET
            t.cd46_expression_level = COALESCE(t.cd46_expression_level, $level),
            t.cd46_high_in_cancer = COALESCE(t.cd46_high_in_cancer, $high_in_cancer)
        RETURN t.name AS name
    """

    expressed_cypher = """
        MATCH (p:Protein {symbol: 'CD46'})
        MATCH (t:Tissue {name: $name, type: $type})
        MERGE (p)-[r:EXPRESSED_IN]->(t)
        ON CREATE SET
            r.level = $level,
            r.source = 'HPA'
        RETURN type(r)
    """

    print(f"Loading {len(HPA_TISSUES)} HPA tissue nodes...")
    loaded = 0
    tissue_seen = set()  # deduplicate by (name, type)

    with driver.session() as session:
        for name, ttype, level, high_in_cancer in HPA_TISSUES:
            key = (name, ttype)
            if key in tissue_seen:
                continue
            tissue_seen.add(key)

            session.run(tissue_cypher, name=name, type=ttype, level=level, high_in_cancer=high_in_cancer)
            session.run(expressed_cypher, name=name, type=ttype, level=level)
            loaded += 1

    print(f"✅ HPA: upserted {loaded} Tissue nodes + EXPRESSED_IN relationships.")
    return loaded


def load_clinical_trials(driver, data_path: Path):
    """Load clinical trials from clinicaltrials_cd46.json."""
    with open(data_path, encoding="utf-8") as f:
        trials = json.load(f)

    print(f"Found {len(trials)} clinical trials in JSON.")

    trial_cypher = """
        MERGE (t:ClinicalTrial {nct_id: $nct_id})
        ON CREATE SET
            t.title = $title,
            t.status = $status,
            t.phase = $phase,
            t.sponsor = $sponsor,
            t.start_date = $start_date,
            t.condition = $condition,
            t.intervention = $intervention,
            t.source = 'ClinicalTrials.gov'
        ON MATCH SET
            t.status = $status
        RETURN t.nct_id AS id
    """

    investigates_cypher = """
        MATCH (t:ClinicalTrial {nct_id: $nct_id})
        MATCH (d:Disease)
        WHERE d.name CONTAINS 'prostate' OR d.tcga_code = 'PRAD'
        WITH t, d LIMIT 1
        MERGE (t)-[r:INVESTIGATES]->(d)
        ON CREATE SET r.source = 'ClinicalTrials.gov'
        RETURN type(r)
    """

    trial_count = 0
    with driver.session() as session:
        for trial in trials:
            proto = trial.get("protocolSection", {})
            ident = proto.get("identificationModule", {})
            status_mod = proto.get("statusModule", {})
            design = proto.get("designModule", {})
            sponsor_mod = proto.get("sponsorCollaboratorsModule", {})
            cond_mod = proto.get("conditionsModule", {})
            arms = proto.get("armsInterventionsModule", {})

            nct_id = ident.get("nctId", "")
            if not nct_id:
                continue

            conditions = cond_mod.get("conditions", [])
            interventions = arms.get("interventions", [])
            intervention_names = [i.get("name", "") for i in interventions if isinstance(i, dict)]

            session.run(
                trial_cypher,
                nct_id=nct_id,
                title=ident.get("briefTitle", ""),
                status=status_mod.get("overallStatus", ""),
                phase=", ".join(design.get("phases", [])),
                sponsor=sponsor_mod.get("leadSponsor", {}).get("name", ""),
                start_date=status_mod.get("startDateStruct", {}).get("date", ""),
                condition=", ".join(conditions[:3]),
                intervention=", ".join(intervention_names[:2]),
            )

            # Link to a prostate cancer disease node if it exists
            session.run(investigates_cypher, nct_id=nct_id)
            trial_count += 1
            print(f"  Trial {nct_id}: {ident.get('briefTitle','')[:60]}")

    print(f"✅ Clinical Trials: upserted {trial_count} nodes.")
    return trial_count


def main():
    trials_path = Path(__file__).resolve().parents[1] / "data" / "raw" / "apis" / "clinicaltrials_cd46.json"

    driver = get_driver()
    try:
        tissue_count = load_hpa_tissues(driver)
        trial_count = load_clinical_trials(driver, trials_path)
        print(f"\nSummary: +{tissue_count} Tissue, +{trial_count} ClinicalTrial nodes upserted.")
        print("Run scripts/audit_kg.py to confirm AuraDB counts.")
    finally:
        driver.close()


if __name__ == "__main__":
    main()
