"""
Build the Neo4j knowledge graph in AuraDB.
Orchestrates node and relationship creation from processed CSV files.
Creates all constraints/indexes, then MERGE all nodes and relationships.
"""

import logging
import os
from pathlib import Path

from dotenv import load_dotenv
from neo4j import GraphDatabase
import pandas as pd
import yaml

load_dotenv()
log = logging.getLogger(__name__)

NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")

DATA_DIR = Path("data/processed")

CONSTRAINTS = [
    "CREATE CONSTRAINT gene_symbol IF NOT EXISTS FOR (g:Gene) REQUIRE g.symbol IS UNIQUE",
    "CREATE CONSTRAINT disease_tcga IF NOT EXISTS FOR (d:Disease) REQUIRE d.tcga_code IS UNIQUE",
    "CREATE CONSTRAINT drug_name IF NOT EXISTS FOR (dr:Drug) REQUIRE dr.name IS UNIQUE",
    "CREATE CONSTRAINT trial_nct IF NOT EXISTS FOR (t:ClinicalTrial) REQUIRE t.nct_id IS UNIQUE",
    "CREATE CONSTRAINT pub_pmid IF NOT EXISTS FOR (p:Publication) REQUIRE p.pmid IS UNIQUE",
    "CREATE CONSTRAINT pg_name IF NOT EXISTS FOR (pg:PatientGroup) REQUIRE pg.name IS UNIQUE",
    "CREATE CONSTRAINT cellline_id IF NOT EXISTS FOR (c:CellLine) REQUIRE c.depmap_id IS UNIQUE",
    "CREATE CONSTRAINT protein_uniprot IF NOT EXISTS FOR (pr:Protein) REQUIRE pr.uniprot_id IS UNIQUE",
    "CREATE CONSTRAINT source_name IF NOT EXISTS FOR (ds:DataSource) REQUIRE ds.name IS UNIQUE",
]

INDEXES = [
    "CREATE INDEX disease_name IF NOT EXISTS FOR (d:Disease) ON (d.name)",
    "CREATE INDEX gene_ensembl IF NOT EXISTS FOR (g:Gene) ON (g.ensembl_id)",
    "CREATE INDEX pg_cancer_group IF NOT EXISTS FOR (pg:PatientGroup) ON (pg.cancer_type, pg.expression_group)",
]


def get_driver():
    """Get authenticated Neo4j driver for AuraDB."""
    if not all([NEO4J_URI, NEO4J_PASSWORD]):
        raise ValueError(
            "NEO4J_URI and NEO4J_PASSWORD must be set in .env file. "
            "Create a free AuraDB account at https://neo4j.com/cloud/"
        )
    return GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD))


def run_schema_setup(driver):
    """Create all constraints and indexes."""
    with driver.session() as session:
        for stmt in CONSTRAINTS + INDEXES:
            try:
                session.run(stmt)
                log.debug("Schema: %s", stmt[:60])
            except Exception as e:
                log.warning("Schema statement failed (may already exist): %s", e)
    log.info("Schema setup complete")


def merge_gene_node(session, symbol: str, ensembl_id: str, **props):
    session.run("""
        MERGE (g:Gene {symbol: $symbol})
        SET g.ensembl_id = $ensembl_id,
            g.chromosome = $chromosome,
            g.uniprot_id = $uniprot_id,
            g.function = $function,
            g.therapeutic_rationale = $rationale,
            g.is_complement_regulator = true
    """, symbol=symbol, ensembl_id=ensembl_id,
        chromosome=props.get("chromosome", "1q32.2"),
        uniprot_id=props.get("uniprot_id", "P15529"),
        function=props.get("function", "complement regulator, binds C3b/C4b"),
        rationale=props.get("rationale", "overexpressed in cancer, enables complement evasion"))


def merge_protein_node(session, uniprot_id: str, symbol: str, **props):
    session.run("""
        MERGE (p:Protein {uniprot_id: $uniprot_id})
        SET p.symbol = $symbol,
            p.molecular_weight_kda = $mw,
            p.surface_expressed = true,
            p.cleaved_shed = true
    """, uniprot_id=uniprot_id, symbol=symbol,
        mw=props.get("molecular_weight_kda", 58.5))


def merge_disease_node(session, row: dict):
    session.run("""
        MERGE (d:Disease {tcga_code: $tcga_code})
        SET d.name = $name,
            d.ncit_code = $ncit_code,
            d.icd10 = $icd10,
            d.tcga_sample_count = $sample_count,
            d.cd46_mean_tpm_log2 = $cd46_mean,
            d.cd46_median_tpm_log2 = $cd46_median,
            d.cd46_std_tpm_log2 = $cd46_std,
            d.cd46_expression_rank = $rank,
            d.cd46_survival_hr = $hr,
            d.cd46_survival_pval = $pval,
            d.priority_score = $priority_score,
            d.priority_label = $priority_label
    """, **{
        "tcga_code": row.get("tcga_code", row.get("cancer_type", "")),
        "name": row.get("name", row.get("cancer_type", "")),
        "ncit_code": row.get("ncit_code", ""),
        "icd10": row.get("icd10", ""),
        "sample_count": int(row.get("n_samples", row.get("tcga_sample_count", 0) or 0)),
        "cd46_mean": float(row.get("cd46_mean", 0) or 0),
        "cd46_median": float(row.get("cd46_median", 0) or 0),
        "cd46_std": float(row.get("cd46_std", 0) or 0),
        "rank": int(row.get("expression_rank", 0) or 0),
        "hr": float(row.get("hazard_ratio", 1.0) or 1.0),
        "pval": float(row.get("p_value", 1.0) or 1.0),
        "priority_score": float(row.get("priority_score", 0) or 0),
        "priority_label": str(row.get("priority_label", "")),
    })


def merge_tissue_node(session, row: dict):
    session.run("""
        MERGE (t:Tissue {name: $name, type: $type})
        SET t.organ_system = $organ, t.hpa_tissue_id = $hpa_id
    """, name=row.get("tissue", ""), type=row.get("type", "normal"),
        organ=row.get("organ_system", ""), hpa_id=row.get("hpa_tissue_id", ""))


def merge_patient_group(session, row: dict):
    session.run("""
        MERGE (pg:PatientGroup {name: $name})
        SET pg.cancer_type = $cancer_type,
            pg.dataset = $dataset,
            pg.expression_group = $expr_group,
            pg.threshold_method = $threshold,
            pg.threshold_value = $threshold_val,
            pg.n_patients = $n_patients,
            pg.cohort_subtype = $subtype
    """, name=row.get("name", f"{row.get('cancer_type','')}_{row.get('expression_group','')}_{row.get('dataset','')}"),
        cancer_type=row.get("cancer_type", ""),
        dataset=row.get("dataset", "TCGA"),
        expr_group=row.get("expression_group", ""),
        threshold=row.get("threshold_method", "median"),
        threshold_val=float(row.get("threshold_value", 0) or 0),
        n_patients=int(row.get("n_eligible", 0) or 0),
        subtype=row.get("cohort_subtype", ""))


def merge_cell_line(session, row: dict):
    session.run("""
        MERGE (cl:CellLine {depmap_id: $depmap_id})
        SET cl.name = $name,
            cl.cancer_type = $cancer_type,
            cl.tissue = $tissue,
            cl.cd46_expression_tpm = $expr,
            cl.cd46_crispr_score = $crispr,
            cl.cd46_is_dependency = $is_dep
    """, depmap_id=row.get("depmap_id", ""),
        name=row.get("cell_line_name", row.get("depmap_id", "")),
        cancer_type=row.get("cancer_type", ""),
        tissue=row.get("tissue", ""),
        expr=float(row.get("cd46_expression", 0) or 0),
        crispr=float(row.get("cd46_crispr_score", 0) or 0),
        is_dep=bool(row.get("cd46_is_dependency", False)))


def build_cd46_static_seeds(driver):
    """Create the core CD46 gene, protein, and pathway nodes."""
    with driver.session() as session:
        # CD46 gene
        merge_gene_node(session, "CD46", "ENSG00000117335",
                        chromosome="1q32.2", uniprot_id="P15529",
                        function="Membrane cofactor protein; complement C3b/C4b binding",
                        rationale="Overexpressed in multiple cancers; enables complement evasion")

        # PSMA gene (for co-expression)
        session.run("MERGE (g:Gene {symbol: 'FOLH1'}) SET g.ensembl_id = 'ENSG00000086205'")

        # CD46 protein isoforms
        for isoform, mw in [("STA-1", 58.5), ("STA-2", 56.0), ("LCA-1", 55.0), ("LCA-2", 53.5)]:
            session.run("""
                MERGE (p:Protein {uniprot_id: $uid})
                SET p.symbol = 'CD46', p.isoform = $iso, p.molecular_weight_kda = $mw,
                    p.surface_expressed = true, p.cleaved_shed = true
            """, uid=f"P15529-{isoform}", iso=isoform, mw=mw)

        # Connect gene → protein
        session.run("""
            MATCH (g:Gene {symbol: 'CD46'}), (p:Protein {uniprot_id: 'P15529-STA-1'})
            MERGE (g)-[:ENCODES]->(p)
        """)

        # Key pathways
        pathways = [
            ("Complement Activation", "R-HSA-166658", "GO:0006958", "complement"),
            ("Immune Evasion by Cancer", "R-HSA-9613354", "GO:0001566", "immune_evasion"),
            ("T Cell Activation", "R-HSA-202403", "GO:0042110", "signal_transduction"),
        ]
        for name, reactome_id, go_id, category in pathways:
            session.run("""
                MERGE (pw:Pathway {name: $name})
                SET pw.reactome_id = $rid, pw.go_id = $go, pw.category = $cat
            """, name=name, rid=reactome_id, go=go_id, cat=category)
            session.run("""
                MATCH (g:Gene {symbol: 'CD46'}), (pw:Pathway {name: $name})
                MERGE (g)-[:PARTICIPATES_IN]->(pw)
            """, name=name)

        # Known CD46-targeting drugs
        drugs = [
            {"name": "FOR46", "type": "ADC", "payload": "DM4",
             "developer": "Fortis Therapeutics / AstraZeneca", "stage": "Phase_I",
             "isotope": "", "mechanism": "Anti-CD46 ADC, DM4 maytansinoid payload"},
            {"name": "225Ac-CD46-Antibody", "type": "RadioligandTherapy",
             "payload": "", "developer": "Academic / Preclinical", "stage": "Preclinical",
             "isotope": "225Ac", "mechanism": "Alpha-emitting radioligand, CD46-targeted"},
            {"name": "Anti-CD46 BiTE", "type": "Bispecific",
             "payload": "", "developer": "Various", "stage": "Preclinical",
             "isotope": "", "mechanism": "CD46 × CD3 T-cell engaging bispecific"},
        ]
        for d in drugs:
            session.run("""
                MERGE (dr:Drug {name: $name})
                SET dr.drug_type = $type, dr.payload = $payload,
                    dr.developer = $dev, dr.clinical_stage = $stage,
                    dr.isotope = $isotope, dr.mechanism = $mechanism,
                    dr.target_gene = 'CD46'
            """, name=d["name"], type=d["type"], payload=d["payload"],
                dev=d["developer"], stage=d["stage"], isotope=d["isotope"],
                mechanism=d["mechanism"])
            session.run("""
                MATCH (dr:Drug {name: $name}), (g:Gene {symbol: 'CD46'})
                MERGE (dr)-[:TARGETS]->(g)
            """, name=d["name"])

        # DataSource nodes
        sources = [
            ("TCGA", "GDC-2022", "https://xena.ucsc.edu", "mRNA", 11000),
            ("HPA", "v23", "https://www.proteinatlas.org", "Protein", 0),
            ("DepMap", "23Q4", "https://depmap.org", "CellLine", 1800),
            ("cBioPortal-mCRPC", "2024", "https://www.cbioportal.org", "Clinical", 1183),
            ("OpenTargets", "24.06", "https://platform.opentargets.org", "Evidence", 0),
        ]
        for name, ver, url, dtype, count in sources:
            session.run("""
                MERGE (ds:DataSource {name: $name})
                SET ds.version = $ver, ds.url = $url, ds.data_type = $dtype,
                    ds.patient_count = $count
            """, name=name, ver=ver, url=url, dtype=dtype, count=count)

    log.info("Static seed nodes created (Gene, Protein, Pathways, Drugs, DataSources)")


def build_from_processed_data(driver):
    """Load processed CSVs and build graph nodes/relationships."""
    with driver.session() as session:

        # Disease nodes from cd46_by_cancer.csv
        cancer_path = DATA_DIR / "cd46_by_cancer.csv"
        if cancer_path.exists():
            cancer_df = pd.read_csv(cancer_path)
            priority_path = DATA_DIR / "priority_score.csv"
            priority_df = pd.read_csv(priority_path) if priority_path.exists() else pd.DataFrame()

            from src.preprocessing.harmonize_datasets import get_disease_meta
            for _, row in cancer_df.iterrows():
                tcga_code = row.get("cancer_type", "")
                meta = get_disease_meta(tcga_code)
                combined = {**meta, **row.to_dict()}
                if not priority_df.empty and "cancer_type" in priority_df.columns:
                    pri_row = priority_df[priority_df["cancer_type"] == tcga_code]
                    if not pri_row.empty:
                        combined.update(pri_row.iloc[0].to_dict())
                merge_disease_node(session, combined)

            log.info("Merged %d disease nodes", len(cancer_df))

            # Connect CD46 protein → diseases (overexpressed_in)
            session.run("""
                MATCH (p:Protein {uniprot_id: 'P15529-STA-1'}), (d:Disease)
                WHERE d.cd46_expression_rank <= 20
                MERGE (p)-[:OVEREXPRESSED_IN]->(d)
            """)

        # Patient groups
        groups_path = DATA_DIR / "patient_groups.csv"
        if groups_path.exists():
            groups_df = pd.read_csv(groups_path)
            for _, row in groups_df.iterrows():
                cancer = row.get("cancer_type", "")
                expr_group = row.get("expression_group", "")
                method = row.get("threshold_method", "median")
                row_dict = row.to_dict()
                row_dict["name"] = f"{cancer}_{expr_group.replace('-','_')}_{method}_TCGA"
                merge_patient_group(session, row_dict)

            # Link disease → patient group
            session.run("""
                MATCH (d:Disease), (pg:PatientGroup)
                WHERE pg.cancer_type = d.tcga_code
                  AND pg.dataset = 'TCGA'
                MERGE (d)-[:HAS_PATIENT_GROUP]->(pg)
            """)
            log.info("Merged %d patient group nodes", len(groups_df))

        # HPA tissue nodes
        hpa_path = DATA_DIR / "hpa_cd46_protein.csv"
        if hpa_path.exists():
            hpa_df = pd.read_csv(hpa_path)
            for _, row in hpa_df.iterrows():
                merge_tissue_node(session, row.to_dict())

            session.run("""
                MATCH (p:Protein {symbol: 'CD46'}), (t:Tissue)
                MERGE (p)-[e:EXPRESSED_IN]->(t)
                SET e.data_source = 'HPA'
            """)
            log.info("Merged %d tissue nodes from HPA", len(hpa_df))

        # DepMap cell lines
        depmap_path = DATA_DIR / "depmap_cd46_essentiality.csv"
        if depmap_path.exists():
            dm_df = pd.read_csv(depmap_path)
            for _, row in dm_df.iterrows():
                merge_cell_line(session, row.to_dict())

            session.run("""
                MATCH (cl:CellLine), (g:Gene {symbol: 'CD46'})
                WHERE cl.cd46_is_dependency = true
                MERGE (cl)-[dep:DEPENDS_ON]->(g)
                SET dep.crispr_score = cl.cd46_crispr_score,
                    dep.is_essential = true
            """)
            log.info("Merged %d DepMap cell line nodes", len(dm_df))


def verify_graph(driver) -> dict:
    """Run basic node count verification queries."""
    counts = {}
    labels = ["Gene", "Protein", "Disease", "Tissue", "PatientGroup",
              "Drug", "ClinicalTrial", "CellLine", "Pathway", "DataSource"]
    with driver.session() as session:
        for label in labels:
            result = session.run(f"MATCH (n:{label}) RETURN count(n) AS cnt")
            counts[label] = result.single()["cnt"]
    return counts


def build_full_graph():
    """Main entry: build complete CD46 knowledge graph in AuraDB."""
    log.info("Connecting to AuraDB: %s", NEO4J_URI)
    driver = get_driver()

    try:
        log.info("Step 1/4: Setting up schema constraints + indexes")
        run_schema_setup(driver)

        log.info("Step 2/4: Creating static seed nodes")
        build_cd46_static_seeds(driver)

        log.info("Step 3/4: Ingesting processed data")
        build_from_processed_data(driver)

        log.info("Step 4/4: Verifying graph")
        counts = verify_graph(driver)
        total = sum(counts.values())
        log.info("Graph build complete! Total nodes: %d", total)
        for label, count in counts.items():
            log.info("  %s: %d", label, count)

        return counts

    finally:
        driver.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    counts = build_full_graph()
    print("\n✅ Knowledge Graph built successfully!")
    print("Node counts:")
    for k, v in counts.items():
        print(f"  {k}: {v}")
