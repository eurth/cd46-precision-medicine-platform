"""
AACR Project GENIE Data Pipeline - FULL DATASET
"""
import synapseclient
import pandas as pd
import os
from pathlib import Path

RAW_DIR = Path("data/raw")
PROC_DIR = Path("data/processed")
TARGET_GENES = {"CD46", "AR", "PTEN", "TP53", "FOLH1"}

paths = {
    "patient": str(RAW_DIR / "data_clinical_patient.txt"),
    "sample": str(RAW_DIR / "data_clinical_sample.txt"),
    "mutation": str(RAW_DIR / "data_mutations_extended.txt"),
    "cna": str(RAW_DIR / "data_cna.txt")
}

print("\n1. Loading Clinical Data (ALL samples)...")
df_p = pd.read_csv(paths["patient"], sep="\t", comment="#")
df_s = pd.read_csv(paths["sample"], sep="\t", comment="#")
df_final = pd.merge(df_s, df_p, on="PATIENT_ID", how="left")

print("\n2. Processing Mutations for target genes...")
mut_chunks = []
mut_cols = ["Tumor_Sample_Barcode", "Hugo_Symbol"]
for chunk in pd.read_csv(paths["mutation"], sep="\t", comment="#", usecols=mut_cols, chunksize=500000):
    mut_chunks.append(chunk[chunk["Hugo_Symbol"].isin(TARGET_GENES)])
df_mut = pd.concat(mut_chunks, ignore_index=True)

print("\n3. Processing Copy Number Alterations (CNA) memory-efficiently...")
cna_records = []
import csv
with open(paths["cna"], "r") as f:
    reader = csv.reader(f, delimiter="\t")
    headers = next(reader)
    sample_cols = headers[1:]
    for row in reader:
        gene = row[0]
        if gene in TARGET_GENES:
            for i, val in enumerate(row[1:]):
                if val in ["2", "-2", 2, -2, "2.0", "-2.0"]:
                    cna_records.append((sample_cols[i], gene, float(val)))

df_cna_melt = pd.DataFrame(cna_records, columns=["Tumor_Sample_Barcode", "Hugo_Symbol", "CNA"])

print("\n4. Annotating Full Cohort...")
for gene in TARGET_GENES:
    gene_mut_samples = set(df_mut[df_mut["Hugo_Symbol"] == gene]["Tumor_Sample_Barcode"])
    df_final[f"{gene}_Mutated"] = df_final["SAMPLE_ID"].isin(gene_mut_samples)
    
    gene_amp_samples = set(df_cna_melt[(df_cna_melt["Hugo_Symbol"] == gene) & (df_cna_melt["CNA"] == 2)]["Tumor_Sample_Barcode"])
    df_final[f"{gene}_Amplified"] = df_final["SAMPLE_ID"].isin(gene_amp_samples)
    
    gene_del_samples = set(df_cna_melt[(df_cna_melt["Hugo_Symbol"] == gene) & (df_cna_melt["CNA"] == -2)]["Tumor_Sample_Barcode"])
    df_final[f"{gene}_Deleted"] = df_final["SAMPLE_ID"].isin(gene_del_samples)

cols_to_keep = [
    "PATIENT_ID", "SAMPLE_ID", "AGE_AT_SEQ_REPORT", "SEX", "PRIMARY_RACE",
    "CANCER_TYPE", "CANCER_TYPE_DETAILED", "SAMPLE_TYPE", "SEQ_ASSAY_ID",
    "CD46_Mutated", "CD46_Amplified", "CD46_Deleted",
    "AR_Mutated", "AR_Amplified", "AR_Deleted",
    "TP53_Mutated", "TP53_Amplified", "TP53_Deleted",
    "PTEN_Mutated", "PTEN_Amplified", "PTEN_Deleted",
    "FOLH1_Mutated", "FOLH1_Amplified", "FOLH1_Deleted",
]
df_final = df_final[[c for c in cols_to_keep if c in df_final.columns]]

out_path = PROC_DIR / "genie_full_cohort.parquet"
df_final.to_parquet(out_path, index=False)
print(f"\nSaved FULL GENIE cohort to {out_path} ({os.path.getsize(out_path) / 1024 / 1024:.2f} MB)")
print(f"Total samples annotated: {len(df_final)}")
