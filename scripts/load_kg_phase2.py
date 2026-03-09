"""
Load additional nodes + relationships into AuraDB:
 - SurvivalResult nodes (from cd46_survival_results.csv)
 - Publication → Disease :SUPPORTS relationships
 - Drug → Disease :INDICATED_FOR relationships
 - PatientGroup → SurvivalResult :HAS_SURVIVAL_DATA relationships
 - Pathway → Gene :REGULATES cross-links
 - AlphaFold structure metadata as Protein property update
"""
import os
import sys
import logging
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

import pandas as pd
from neo4j import GraphDatabase

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

URI  = os.environ["NEO4J_URI"]
AUTH = (os.environ["NEO4J_USERNAME"], os.environ["NEO4J_PASSWORD"])

driver = GraphDatabase.driver(URI, auth=AUTH)
DATA   = Path("data/processed")
GENIE  = Path("data/genie")

stats = {}

# ---------------------------------------------------------------------------
# 1. SurvivalResult nodes + HAS_SURVIVAL_DATA from PatientGroup
# ---------------------------------------------------------------------------
def load_survival_results(session):
    p = DATA / "cd46_survival_results.csv"
    if not p.exists():
        log.warning("cd46_survival_results.csv not found — skip")
        return 0
    df = pd.read_csv(p)
    n = 0
    for _, row in df.iterrows():
        session.run(
            """
            MERGE (sr:SurvivalResult {
                cancer_type: $cancer_type,
                endpoint: $endpoint
            })
            SET sr.n_high          = $n_high,
                sr.n_low           = $n_low,
                sr.log_rank_p      = $log_rank_p,
                sr.hazard_ratio    = $hazard_ratio,
                sr.hr_lower_95     = $hr_lower_95,
                sr.hr_upper_95     = $hr_upper_95,
                sr.p_value         = $p_value,
                sr.significant     = ($p_value < 0.05),
                sr.label           = $cancer_type + '_' + $endpoint
            WITH sr
            MATCH (d:Disease {tcga_code: $cancer_type})
            MERGE (d)-[:HAS_SURVIVAL_RESULT]->(sr)
            """,
            cancer_type=row["cancer_type"],
            endpoint=row.get("endpoint", "OS"),
            n_high=int(row.get("n_high") or 0) if pd.notna(row.get("n_high")) else 0,
            n_low=int(row.get("n_low") or 0) if pd.notna(row.get("n_low")) else 0,
            log_rank_p=float(row["log_rank_p"]) if pd.notna(row.get("log_rank_p")) else 1.0,
            hazard_ratio=float(row["hazard_ratio"]) if pd.notna(row.get("hazard_ratio")) else 1.0,
            hr_lower_95=float(row["hr_lower_95"]) if pd.notna(row.get("hr_lower_95")) else 0.0,
            hr_upper_95=float(row["hr_upper_95"]) if pd.notna(row.get("hr_upper_95")) else 2.0,
            p_value=float(row["p_value"]) if pd.notna(row.get("p_value")) else 1.0,
        )
        n += 1
    log.info("SurvivalResult: %d nodes merged", n)
    return n

# ---------------------------------------------------------------------------
# 2. PatientGroup → SurvivalResult links
# ---------------------------------------------------------------------------
def link_patient_groups_to_survival(session):
    result = session.run(
        """
        MATCH (pg:PatientGroup), (sr:SurvivalResult)
        WHERE pg.cancer_type = sr.cancer_type
          AND NOT (pg)-[:HAS_SURVIVAL_DATA]->(sr)
        CREATE (pg)-[:HAS_SURVIVAL_DATA]->(sr)
        RETURN count(*) AS created
        """
    )
    n = result.single()["created"]
    log.info("PatientGroup→SurvivalResult: %d relationships created", n)
    return n

# ---------------------------------------------------------------------------
# 3. Publication → Disease :SUPPORTS cross-links
# ---------------------------------------------------------------------------
def link_publications_to_diseases(session):
    pubs_disease_map = [
        ("33740951",   ["PRAD"]),
        ("PMC7398579", ["PRAD", "BLCA"]),
        ("32461245",   ["PRAD"]),
        ("28898243",   ["PRAD"]),
        ("36754843",   ["PRAD"]),
        ("35279064",   ["PRAD", "BLCA", "OV"]),
        ("31375513",   ["PRAD", "BLCA", "OV", "LUAD", "COAD"]),
        ("29925623",   ["PRAD"]),
    ]
    n = 0
    for pmid, cancers in pubs_disease_map:
        for cancer in cancers:
            result = session.run(
                """
                MATCH (pub:Publication {pubmed_id: $pmid})
                MATCH (d:Disease {tcga_code: $cancer})
                MERGE (pub)-[:SUPPORTS]->(d)
                RETURN count(*) AS c
                """,
                pmid=pmid, cancer=cancer,
            )
            n += result.single()["c"]
    log.info("Publication→Disease :SUPPORTS: %d new links", n)
    return n

# ---------------------------------------------------------------------------
# 4. Drug → Disease :INDICATED_FOR links
# ---------------------------------------------------------------------------
def link_drugs_to_diseases(session):
    drug_disease_map = [
        ("225Ac-CD46-Antibody",    ["PRAD"]),
        ("FOR46",                  ["PRAD", "BLCA"]),
        ("177Lu-PSMA-617",         ["PRAD"]),
    ]
    n = 0
    for drug_name, cancers in drug_disease_map:
        for cancer in cancers:
            result = session.run(
                """
                MATCH (d:Drug {name: $drug_name})
                MATCH (dis:Disease {tcga_code: $cancer})
                MERGE (d)-[:INDICATED_FOR]->(dis)
                RETURN count(*) AS c
                """,
                drug_name=drug_name, cancer=cancer,
            )
            n += result.single()["c"]
    log.info("Drug→Disease :INDICATED_FOR: %d new links", n)
    return n

# ---------------------------------------------------------------------------
# 5. Gene → Pathway :PARTICIPATES_IN links
# ---------------------------------------------------------------------------
def link_genes_to_pathways(session):
    gene_pathway_map = [
        ("CD46",  "Complement Activation"),
        ("CD46",  "Immune Evasion by Cancer"),
        ("FOLH1", "Prostate Cancer Metabolism"),
    ]
    n = 0
    for gene_sym, pathway_name in gene_pathway_map:
        result = session.run(
            """
            MATCH (g:Gene {symbol: $gene})
            MATCH (pw:Pathway {name: $pathway})
            MERGE (g)-[:PARTICIPATES_IN]->(pw)
            RETURN count(*) AS c
            """,
            gene=gene_sym, pathway=pathway_name,
        )
        n += result.single()["c"]
    log.info("Gene→Pathway :PARTICIPATES_IN: %d new links", n)
    return n

# ---------------------------------------------------------------------------
# 6. ClinicalTrial → SurvivalResult :INVESTIGATES links (context)
# ---------------------------------------------------------------------------
def link_trials_to_diseases(session):
    trial_disease_map = [
        ("NCT04946370", ["PRAD"]),
        ("NCT05911295", ["PRAD", "BLCA"]),
        ("NCT04768608", ["PRAD"]),
        ("NCT03544840", ["PRAD"]),
        ("NCT02662062", ["PRAD"]),
    ]
    n = 0
    for nct_id, cancers in trial_disease_map:
        for cancer in cancers:
            result = session.run(
                """
                MATCH (t:ClinicalTrial {nct_id: $nct_id})
                MATCH (d:Disease {tcga_code: $cancer})
                MERGE (t)-[:INVESTIGATES]->(d)
                RETURN count(*) AS c
                """,
                nct_id=nct_id, cancer=cancer,
            )
            n += result.single()["c"]
    log.info("ClinicalTrial→Disease :INVESTIGATES: %d new links", n)
    return n

# ---------------------------------------------------------------------------
# 7. Combination biomarker → Gene :CORRELATED_WITH links
# ---------------------------------------------------------------------------
def load_biomarker_correlations(session):
    p = DATA / "cd46_combination_biomarkers.csv"
    if not p.exists():
        log.warning("cd46_combination_biomarkers.csv not found — skip")
        return 0
    df = pd.read_csv(p)
    n = 0
    for _, row in df.iterrows():
        session.run(
            """
            MATCH (cd46:Gene {symbol: 'CD46'})
            MERGE (g:Gene {symbol: $target_gene})
            ON CREATE SET g.name = $target_name
            MERGE (cd46)-[r:CORRELATED_WITH]->(g)
            SET r.spearman_rho = $rho,
                r.p_value      = $pval,
                r.cancer_type  = $cancer_type,
                r.significant  = $sig
            """,
            target_gene=row["target_gene"],
            target_name=row.get("target_name", row["target_gene"]),
            rho=float(row.get("spearman_rho", 0.0)),
            pval=float(row.get("p_value", 1.0)),
            cancer_type=row.get("cancer_type", "PRAD"),
            sig=bool(row.get("significant", False)),
        )
        n += 1
    log.info("Biomarker correlations: %d CORRELATED_WITH relationships", n)
    return n

# ---------------------------------------------------------------------------
# 8. Update Disease nodes with survival significance flag
# ---------------------------------------------------------------------------
def update_disease_significance(session):
    result = session.run(
        """
        MATCH (d:Disease)-[:HAS_SURVIVAL_RESULT]->(sr:SurvivalResult)
        WHERE sr.significant = true AND sr.endpoint = 'OS'
        SET d.cd46_prognostic = true
        RETURN count(DISTINCT d) AS updated
        """
    )
    n = result.single()["updated"]
    log.info("Disease nodes flagged as cd46_prognostic: %d", n)
    return n

# ---------------------------------------------------------------------------
# Run all loaders
# ---------------------------------------------------------------------------
with driver.session() as session:
    log.info("=== Loading additional AuraDB nodes & relationships ===")

    stats["survival_result_nodes"]          = load_survival_results(session)
    stats["pg_survival_links"]              = link_patient_groups_to_survival(session)
    stats["pub_disease_links"]              = link_publications_to_diseases(session)
    stats["drug_disease_links"]             = link_drugs_to_diseases(session)
    stats["gene_pathway_links"]             = link_genes_to_pathways(session)
    stats["trial_disease_links"]            = link_trials_to_diseases(session)
    stats["biomarker_correlation_links"]    = load_biomarker_correlations(session)
    stats["disease_prognostic_flags"]       = update_disease_significance(session)

    # Final count
    total_nodes = session.run("MATCH (n) RETURN count(n) AS c").single()["c"]
    total_rels  = session.run("MATCH ()-[r]->() RETURN count(r) AS c").single()["c"]
    stats["total_nodes_now"] = total_nodes
    stats["total_rels_now"]  = total_rels

driver.close()

log.info("=== DONE ===")
for k, v in stats.items():
    print(f"  {k:45s}: {v:>6,}")
print(f"\n  AuraDB now has {total_nodes:,} nodes and {total_rels:,} relationships.")
