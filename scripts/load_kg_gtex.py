"""Load GTEx CD46 normal-tissue expression into AuraDB as properties on Tissue nodes.

Precondition: run scripts/fetch_gtex_cd46.py first to generate
  data/processed/gtex_cd46_normal.csv

Strategy:
  - MERGE on (:Tissue {name: tissue_name}) — adds GTEx properties to existing HPA Tissue nodes
    where names match, or creates new Tissue nodes with source='GTEx' for non-overlapping tissues.

Run:
    python scripts/load_kg_gtex.py
"""
import os
import sys
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from neo4j import GraphDatabase

load_dotenv(Path(__file__).resolve().parents[1] / ".env")
sys.path.insert(0, str(Path(__file__).resolve().parent))

CSV_PATH = Path("data/processed/gtex_cd46_normal.csv")

# Map GTEx tissue_site_detail → closest HPA tissue name (where they differ)
GTEX_TO_HPA = {
    "Adipose - Subcutaneous":                   "Adipose tissue",
    "Adipose - Visceral (Omentum)":              "Adipose tissue",
    "Artery - Aorta":                            "Aorta",
    "Artery - Coronary":                         "Artery",
    "Artery - Tibial":                           "Artery",
    "Brain - Amygdala":                          "Brain",
    "Brain - Anterior cingulate cortex (BA24)":  "Brain",
    "Brain - Caudate (basal ganglia)":           "Brain",
    "Brain - Cerebellar Hemisphere":             "Cerebellum",
    "Brain - Cerebellum":                        "Cerebellum",
    "Brain - Cortex":                            "Cerebral cortex",
    "Brain - Frontal Cortex (BA9)":              "Cerebral cortex",
    "Brain - Hippocampus":                       "Hippocampus",
    "Brain - Hypothalamus":                      "Brain",
    "Brain - Nucleus accumbens (basal ganglia)": "Brain",
    "Brain - Putamen (basal ganglia)":           "Brain",
    "Brain - Spinal cord (cervical c-1)":        "Spinal cord",
    "Brain - Substantia nigra":                  "Brain",
    "Breast - Mammary Tissue":                   "Breast",
    "Cells - Cultured fibroblasts":              None,
    "Cells - EBV-transformed lymphocytes":       None,
    "Cervix - Ectocervix":                       "Cervix",
    "Cervix - Endocervix":                       "Cervix",
    "Colon - Sigmoid":                           "Colon",
    "Colon - Transverse":                        "Colon",
    "Esophagus - Gastroesophageal Junction":     "Esophagus",
    "Esophagus - Mucosa":                        "Esophagus",
    "Esophagus - Muscularis":                    "Esophagus",
    "Fallopian Tube":                            "Fallopian tube",
    "Heart - Atrial Appendage":                  "Heart muscle",
    "Heart - Left Ventricle":                    "Heart muscle",
    "Kidney - Cortex":                           "Kidney",
    "Kidney - Medulla":                          "Kidney",
    "Muscle - Skeletal":                         "Skeletal muscle",
    "Nerve - Tibial":                            "Peripheral nerve",
    "Skin - Not Sun Exposed (Suprapubic)":       "Skin",
    "Skin - Sun Exposed (Lower leg)":            "Skin",
    "Small Intestine - Terminal Ileum":          "Small intestine",
    "Vagina":                                    "Vagina",
    "Whole Blood":                               "Bone marrow",
}


def get_driver():
    uri      = os.getenv("NEO4J_URI")
    user     = os.getenv("NEO4J_USERNAME", "neo4j")
    password = os.getenv("NEO4J_PASSWORD")
    if not uri or not password:
        raise RuntimeError("NEO4J_URI and NEO4J_PASSWORD must be set in .env")
    driver = GraphDatabase.driver(uri, auth=(user, password))
    driver.verify_connectivity()
    return driver


CYPHER = """
UNWIND $rows AS row
MERGE (t:Tissue {name: row.tissue_name})
  ON CREATE SET
    t.gtex_tissue_id    = row.tissue_site_id,
    t.gtex_median_tpm   = row.median_tpm,
    t.gtex_mean_tpm     = row.mean_tpm,
    t.gtex_q1_tpm       = row.q1_tpm,
    t.gtex_q3_tpm       = row.q3_tpm,
    t.gtex_n_samples    = row.n_samples,
    t.gtex_dataset      = row.dataset,
    t.source            = CASE WHEN row.hpa_matched THEN t.source ELSE 'GTEx' END,
    t.type              = 'normal'
  ON MATCH SET
    t.gtex_tissue_id    = row.tissue_site_id,
    t.gtex_median_tpm   = row.median_tpm,
    t.gtex_mean_tpm     = row.mean_tpm,
    t.gtex_q1_tpm       = row.q1_tpm,
    t.gtex_q3_tpm       = row.q3_tpm,
    t.gtex_n_samples    = row.n_samples,
    t.gtex_dataset      = row.dataset
RETURN count(t) AS upserted
"""


def main():
    print("=== GTEx → AuraDB Loader ===")

    if not CSV_PATH.exists():
        print(f"ERROR: {CSV_PATH} not found. Run fetch_gtex_cd46.py first.")
        sys.exit(1)

    df = pd.read_csv(CSV_PATH)
    print(f"Loaded {len(df)} GTEx tissue records")

    rows = []
    for _, rec in df.iterrows():
        detail      = rec["tissue_site_detail"]
        hpa_name    = GTEX_TO_HPA.get(detail)
        if hpa_name is None and detail in GTEX_TO_HPA:
            print(f"  Skipping cell-line tissue: {detail}")
            continue
        tissue_name = hpa_name if hpa_name else detail
        rows.append({
            "tissue_name":    tissue_name,
            "tissue_site_id": rec.get("tissue_site_id", ""),
            "median_tpm":     float(rec["median_tpm"]),
            "mean_tpm":       float(rec["mean_tpm"]),
            "q1_tpm":         float(rec["q1_tpm"]),
            "q3_tpm":         float(rec["q3_tpm"]),
            "n_samples":      int(rec["n_samples"]),
            "dataset":        str(rec.get("dataset", "gtex_v8")),
            "hpa_matched":    hpa_name is not None,
        })

    driver = get_driver()
    print(f"Connected to AuraDB. Loading {len(rows)} tissue rows...")
    with driver.session() as session:
        result = session.run(CYPHER, rows=rows)
        summary = result.consume()
        print(f"  ✅ {summary.counters.nodes_created} Tissue nodes created, "
              f"{summary.counters.properties_set} properties set")
    driver.close()
    print("\nDone. Run scripts/audit_kg.py to confirm counts.")


if __name__ == "__main__":
    main()
