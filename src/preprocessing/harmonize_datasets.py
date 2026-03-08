"""
Disease name harmonization across TCGA, cBioPortal, Open Targets, and DepMap.
Maps TCGA cancer codes to standard disease names and synonyms.
"""

import logging
from pathlib import Path

import pandas as pd

log = logging.getLogger(__name__)

# TCGA code → standard disease name + synonyms
TCGA_DISEASE_MAP = {
    "ACC":  {"name": "Adrenocortical Carcinoma",       "icd10": "C74.0", "ncit": "C4017"},
    "BLCA": {"name": "Bladder Urothelial Carcinoma",    "icd10": "C67",   "ncit": "C4912"},
    "BRCA": {"name": "Breast Invasive Carcinoma",       "icd10": "C50",   "ncit": "C4872"},
    "CESC": {"name": "Cervical Squamous Cell Carcinoma","icd10": "C53",   "ncit": "C27676"},
    "CHOL": {"name": "Cholangiocarcinoma",              "icd10": "C22.1", "ncit": "C4908"},
    "COAD": {"name": "Colon Adenocarcinoma",            "icd10": "C18",   "ncit": "C4910"},
    "DLBC": {"name": "Diffuse Large B-cell Lymphoma",  "icd10": "C83.3", "ncit": "C8851"},
    "ESCA": {"name": "Esophageal Carcinoma",            "icd10": "C15",   "ncit": "C4024"},
    "GBM":  {"name": "Glioblastoma Multiforme",         "icd10": "C71.9", "ncit": "C3058"},
    "HNSC": {"name": "Head and Neck Squamous Cell Carcinoma", "icd10": "C14", "ncit": "C34447"},
    "KICH": {"name": "Kidney Chromophobe",              "icd10": "C64",   "ncit": "C27676"},
    "KIRC": {"name": "Kidney Renal Clear Cell Carcinoma","icd10": "C64",  "ncit": "C4033"},
    "KIRP": {"name": "Kidney Renal Papillary Cell Carcinoma","icd10": "C64","ncit": "C9385"},
    "LAML": {"name": "Acute Myeloid Leukemia",          "icd10": "C91.0", "ncit": "C3171"},
    "LGG":  {"name": "Brain Lower Grade Glioma",        "icd10": "C71",   "ncit": "C4978"},
    "LIHC": {"name": "Liver Hepatocellular Carcinoma",  "icd10": "C22.0", "ncit": "C3099"},
    "LUAD": {"name": "Lung Adenocarcinoma",             "icd10": "C34",   "ncit": "C3512"},
    "LUSC": {"name": "Lung Squamous Cell Carcinoma",    "icd10": "C34",   "ncit": "C4450"},
    "MESO": {"name": "Mesothelioma",                    "icd10": "C45",   "ncit": "C3490"},
    "OV":   {"name": "Ovarian Serous Cystadenocarcinoma","icd10": "C56",  "ncit": "C7833"},
    "PAAD": {"name": "Pancreatic Adenocarcinoma",       "icd10": "C25",   "ncit": "C8294"},
    "PCPG": {"name": "Pheochromocytoma and Paraganglioma","icd10": "C74.1","ncit": "C3306"},
    "PRAD": {"name": "Prostate Adenocarcinoma",         "icd10": "C61",   "ncit": "C7378"},
    "READ": {"name": "Rectum Adenocarcinoma",           "icd10": "C20",   "ncit": "C5765"},
    "SARC": {"name": "Sarcoma",                         "icd10": "C49",   "ncit": "C9118"},
    "SKCM": {"name": "Skin Cutaneous Melanoma",         "icd10": "C43",   "ncit": "C3510"},
    "STAD": {"name": "Stomach Adenocarcinoma",          "icd10": "C16",   "ncit": "C4004"},
    "TGCT": {"name": "Testicular Germ Cell Tumors",     "icd10": "C62",   "ncit": "C3407"},
    "THCA": {"name": "Thyroid Carcinoma",               "icd10": "C73",   "ncit": "C4815"},
    "THYM": {"name": "Thymoma",                         "icd10": "C37",   "ncit": "C17313"},
    "UCEC": {"name": "Uterine Corpus Endometrial Carcinoma","icd10": "C54","ncit": "C7550"},
    "UCS":  {"name": "Uterine Carcinosarcoma",          "icd10": "C54",   "ncit": "C8973"},
    "UVM":  {"name": "Uveal Melanoma",                  "icd10": "C69.4", "ncit": "C8562"},
}


def get_disease_name(tcga_code: str) -> str:
    """Resolve TCGA code to standard disease name."""
    return TCGA_DISEASE_MAP.get(tcga_code, {}).get("name", tcga_code)


def get_disease_meta(tcga_code: str) -> dict:
    """Return full disease metadata dict for a TCGA code."""
    meta = TCGA_DISEASE_MAP.get(tcga_code, {}).copy()
    meta["tcga_code"] = tcga_code
    meta.setdefault("name", tcga_code)
    meta.setdefault("icd10", "")
    meta.setdefault("ncit", "")
    return meta


def harmonize_cancer_df(df: pd.DataFrame, cancer_col: str = "cancer_type") -> pd.DataFrame:
    """Add disease_name, icd10, ncit_code columns to a DataFrame with TCGA codes."""
    df = df.copy()
    df["disease_name"] = df[cancer_col].map(
        lambda c: TCGA_DISEASE_MAP.get(c, {}).get("name", c)
    )
    df["icd10"] = df[cancer_col].map(
        lambda c: TCGA_DISEASE_MAP.get(c, {}).get("icd10", "")
    )
    df["ncit_code"] = df[cancer_col].map(
        lambda c: TCGA_DISEASE_MAP.get(c, {}).get("ncit", "")
    )
    return df


if __name__ == "__main__":
    print("Disease name harmonization table:")
    for code, meta in TCGA_DISEASE_MAP.items():
        print(f"  {code}: {meta['name']}")
