"""Build Disease nodes from harmonized cancer data + priority scores."""
from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd

from neo4j import Driver

logger = logging.getLogger(__name__)

# Full TCGA → ICD10 / NCIT / treatment relevance mapping
DISEASE_META = {
    "PRAD": {
        "full_name": "Prostate Adenocarcinoma",
        "icd10": "C61",
        "ncit": "NCIT:C7378",
        "primary_site": "Prostate",
        "treatment_relevance": "Primary target — 225Ac-CD46 Phase I design basis",
    },
    "OV":   {"full_name": "Ovarian Serous Cystadenocarcinoma",  "icd10": "C56",  "ncit": "NCIT:C7431",  "primary_site": "Ovary",     "treatment_relevance": "High CD46 overexpression — candidate"},
    "BLCA": {"full_name": "Bladder Urothelial Carcinoma",        "icd10": "C67",  "ncit": "NCIT:C4912",  "primary_site": "Bladder",   "treatment_relevance": "Elevated CD46 in MIBC subtype"},
    "LUAD": {"full_name": "Lung Adenocarcinoma",                 "icd10": "C34",  "ncit": "NCIT:C3512",  "primary_site": "Lung",      "treatment_relevance": "Moderate expression — exploratory"},
    "LUSC": {"full_name": "Lung Squamous Cell Carcinoma",        "icd10": "C34",  "ncit": "NCIT:C3493",  "primary_site": "Lung",      "treatment_relevance": "Moderate expression — exploratory"},
    "BRCA": {"full_name": "Breast Invasive Carcinoma",           "icd10": "C50",  "ncit": "NCIT:C4872",  "primary_site": "Breast",    "treatment_relevance": "TNBC subset shows elevated CD46"},
    "COAD": {"full_name": "Colon Adenocarcinoma",                "icd10": "C18",  "ncit": "NCIT:C5105",  "primary_site": "Colon",     "treatment_relevance": "Moderate — microsatellite status interaction"},
    "READ": {"full_name": "Rectum Adenocarcinoma",               "icd10": "C20",  "ncit": "NCIT:C9382",  "primary_site": "Rectum",    "treatment_relevance": "Similar to COAD"},
    "STAD": {"full_name": "Stomach Adenocarcinoma",              "icd10": "C16",  "ncit": "NCIT:C4004",  "primary_site": "Stomach",   "treatment_relevance": "Exploratory"},
    "LIHC": {"full_name": "Liver Hepatocellular Carcinoma",      "icd10": "C22",  "ncit": "NCIT:C3099",  "primary_site": "Liver",     "treatment_relevance": "Complement evasion mechanism relevant"},
    "KIRC": {"full_name": "Kidney Renal Clear Cell Carcinoma",   "icd10": "C64",  "ncit": "NCIT:C4033",  "primary_site": "Kidney",    "treatment_relevance": "Exploratory"},
    "KIRP": {"full_name": "Kidney Renal Papillary Cell Carcinoma","icd10": "C64", "ncit": "NCIT:C7956",  "primary_site": "Kidney",    "treatment_relevance": "Exploratory"},
    "KICH": {"full_name": "Kidney Chromophobe",                  "icd10": "C64",  "ncit": "NCIT:C4033",  "primary_site": "Kidney",    "treatment_relevance": "Low expression"},
    "THCA": {"full_name": "Thyroid Carcinoma",                   "icd10": "C73",  "ncit": "NCIT:C7067",  "primary_site": "Thyroid",   "treatment_relevance": "Low expression"},
    "UCEC": {"full_name": "Uterine Corpus Endometrial Carcinoma","icd10": "C54",  "ncit": "NCIT:C7359",  "primary_site": "Uterus",    "treatment_relevance": "Moderate"},
    "CESC": {"full_name": "Cervical Squamous Cell Carcinoma",    "icd10": "C53",  "ncit": "NCIT:C9311",  "primary_site": "Cervix",    "treatment_relevance": "HPV interaction with CD46 receptor"},
    "HNSC": {"full_name": "Head and Neck Squamous Cell Carcinoma","icd10": "C14", "ncit": "NCIT:C3077",  "primary_site": "Head/Neck", "treatment_relevance": "HPV+ subset relevant"},
    "SKCM": {"full_name": "Skin Cutaneous Melanoma",             "icd10": "C43",  "ncit": "NCIT:C3510",  "primary_site": "Skin",      "treatment_relevance": "Complement evasion in melanoma"},
    "GBM":  {"full_name": "Glioblastoma Multiforme",             "icd10": "C71",  "ncit": "NCIT:C3058",  "primary_site": "Brain",     "treatment_relevance": "Low — BBB challenge"},
    "LGG":  {"full_name": "Brain Lower Grade Glioma",            "icd10": "C71",  "ncit": "NCIT:C3059",  "primary_site": "Brain",     "treatment_relevance": "Low — BBB challenge"},
    "PCPG": {"full_name": "Pheochromocytoma and Paraganglioma",  "icd10": "C74",  "ncit": "NCIT:C3337",  "primary_site": "Adrenal",   "treatment_relevance": "Low expression"},
    "ACC":  {"full_name": "Adrenocortical Carcinoma",            "icd10": "C74",  "ncit": "NCIT:C3483",  "primary_site": "Adrenal",   "treatment_relevance": "Low expression"},
    "TGCT": {"full_name": "Testicular Germ Cell Tumors",         "icd10": "C62",  "ncit": "NCIT:C3408",  "primary_site": "Testis",    "treatment_relevance": "Exploratory"},
    "THYM": {"full_name": "Thymoma",                             "icd10": "C37",  "ncit": "NCIT:C7569",  "primary_site": "Thymus",    "treatment_relevance": "Low expression"},
    "MESO": {"full_name": "Mesothelioma",                        "icd10": "C45",  "ncit": "NCIT:C3234",  "primary_site": "Pleura",    "treatment_relevance": "Complement pathway activated"},
    "UVM":  {"full_name": "Uveal Melanoma",                      "icd10": "C69",  "ncit": "NCIT:C7517",  "primary_site": "Eye",       "treatment_relevance": "Low — exploratory"},
    "UCS":  {"full_name": "Uterine Carcinosarcoma",              "icd10": "C54",  "ncit": "NCIT:C7359",  "primary_site": "Uterus",    "treatment_relevance": "Exploratory"},
    "DLBC": {"full_name": "Lymphoid Neoplasm Diffuse Large B-cell Lymphoma","icd10":"C83","ncit":"NCIT:C3018","primary_site":"Lymph Node","treatment_relevance": "CD46 expressed on B-cells"},
    "LAML": {"full_name": "Acute Myeloid Leukemia",              "icd10": "C91",  "ncit": "NCIT:C3171",  "primary_site": "Blood",     "treatment_relevance": "Complement resistance mechanism"},
    "SARC": {"full_name": "Sarcoma",                             "icd10": "C49",  "ncit": "NCIT:C9306",  "primary_site": "Soft Tissue","treatment_relevance": "Low — exploratory"},
    "CHOL": {"full_name": "Cholangiocarcinoma",                  "icd10": "C22",  "ncit": "NCIT:C4024",  "primary_site": "Bile Duct", "treatment_relevance": "Low expression"},
    "PAAD": {"full_name": "Pancreatic Adenocarcinoma",           "icd10": "C25",  "ncit": "NCIT:C8294",  "primary_site": "Pancreas",  "treatment_relevance": "Low stromal accessibility"},
    "ESCA": {"full_name": "Esophageal Carcinoma",                "icd10": "C15",  "ncit": "NCIT:C4024",  "primary_site": "Esophagus", "treatment_relevance": "Exploratory"},
}


def build_disease_nodes(driver: Driver, processed_dir: Path) -> dict:
    """Merge Disease nodes from harmonized cancer CSV + priority scores."""
    disease_file = processed_dir / "cd46_by_cancer.csv"
    priority_file = processed_dir / "priority_score.csv"

    # Load expression stats per cancer
    if disease_file.exists():
        expr_df = pd.read_csv(disease_file)
        expr_map = expr_df.set_index("cancer_type").to_dict("index")
    else:
        logger.warning("cd46_by_cancer.csv not found — using static metadata only")
        expr_map = {}

    # Load priority scores
    if priority_file.exists():
        prio_df = pd.read_csv(priority_file)
        prio_map = prio_df.set_index("cancer_type")["priority_score"].to_dict()
    else:
        logger.warning("priority_score.csv not found — priority_score will be null")
        prio_map = {}

    merged = 0
    with driver.session() as session:
        for tcga_code, meta in DISEASE_META.items():
            expr = expr_map.get(tcga_code, {})
            priority = prio_map.get(tcga_code)

            params = {
                "tcga_code": tcga_code,
                "full_name": meta["full_name"],
                "icd10": meta["icd10"],
                "ncit": meta["ncit"],
                "primary_site": meta["primary_site"],
                "treatment_relevance": meta["treatment_relevance"],
                # Expression stats — may be None
                "mean_log2_expression": expr.get("mean"),
                "median_log2_expression": expr.get("median"),
                "std_log2_expression": expr.get("std"),
                "n_samples": int(expr["count"]) if "count" in expr else None,
                "priority_score": priority,
            }

            session.run(
                """
                MERGE (d:Disease {tcga_code: $tcga_code})
                SET d.full_name                = $full_name,
                    d.icd10                    = $icd10,
                    d.ncit                     = $ncit,
                    d.primary_site             = $primary_site,
                    d.treatment_relevance      = $treatment_relevance,
                    d.mean_log2_expression     = $mean_log2_expression,
                    d.median_log2_expression   = $median_log2_expression,
                    d.std_log2_expression      = $std_log2_expression,
                    d.n_samples                = $n_samples,
                    d.cd46_priority_score      = $priority_score,
                    d.updated_at               = datetime()
                WITH d
                MATCH (g:Gene {ensembl_id: 'ENSG00000117335'})
                MERGE (g)-[:EXPRESSED_IN]->(d)
                """,
                **params,
            )
            merged += 1

    logger.info("Merged %d Disease nodes", merged)
    return {"diseases_merged": merged}
