"""
Process raw cBioPortal parquet files into analysis-ready summaries.
Produces:
  data/genie/genie_cd46_cna_summary.parquet
  data/genie/genie_psma_cd46_cooccurrence.parquet
  data/genie/genie_mutation_summary.parquet
"""
from pathlib import Path
import pandas as pd
import numpy as np

DATA_DIR = Path(__file__).resolve().parents[2] / "data" / "genie"

# Entrez ID → gene symbol mapping
ENTREZ_TO_GENE = {4179: "CD46", 2346: "FOLH1", 367: "AR", 4609: "MYC"}

# CNA value meaning
CNA_LABEL = {-2: "Deep Deletion", -1: "Shallow Deletion", 0: "Diploid",
             1: "Gain", 2: "Amplification"}


def load_cna() -> pd.DataFrame:
    path = DATA_DIR / "prad_cna.parquet"
    if not path.exists():
        return pd.DataFrame()
    df = pd.read_parquet(path)
    # Fix empty gene_symbol using entrez_id map
    if "entrez_id" in df.columns:
        df["gene_symbol"] = df["entrez_id"].map(ENTREZ_TO_GENE).fillna(df.get("gene_symbol", ""))
    df["cna_value"] = pd.to_numeric(df["value"], errors="coerce")
    return df


def load_clinical() -> pd.DataFrame:
    path = DATA_DIR / "prad_clinical.parquet"
    if not path.exists():
        return pd.DataFrame()
    df = pd.read_parquet(path)
    if "patientId" in df.columns:
        df = df.rename(columns={"patientId": "patient_id"})
    return df


def build_cna_summary(cna: pd.DataFrame, clinical: pd.DataFrame) -> pd.DataFrame:
    """Alteration rate per cohort per gene."""
    if cna.empty:
        return pd.DataFrame()

    # Merge clinical to get study_label (cohort name)
    if not clinical.empty and "patient_id" in cna.columns and "patient_id" in clinical.columns:
        keep = [c for c in ["patient_id", "study_label", "study_id"] if c in clinical.columns]
        cna = cna.merge(clinical[keep].drop_duplicates("patient_id"), on="patient_id", how="left")

    # Use study_label as cancer group (all are prostate cancer subtypes)
    if "study_label" not in cna.columns:
        cna["study_label"] = cna.get("study_id", "Unknown")

    cna["is_altered"]   = cna["cna_value"].abs() >= 1
    cna["is_amplified"] = cna["cna_value"] >= 2
    cna["is_deleted"]   = cna["cna_value"] <= -2

    rows = []
    for (cohort, gene), grp in cna.groupby(["study_label", "gene_symbol"]):
        n_total = grp["sample_id"].nunique() if "sample_id" in grp.columns else len(grp)
        n_alt = int(grp["is_altered"].sum())
        n_amp = int(grp["is_amplified"].sum())
        n_del = int(grp["is_deleted"].sum())
        rows.append({
            "cohort":          cohort,
            "gene_symbol":     gene,
            "n_samples":       n_total,
            "n_altered":       n_alt,
            "n_amplified":     n_amp,
            "n_deleted":       n_del,
            "alteration_pct":  round(n_alt / n_total * 100, 2) if n_total else 0,
            "amplification_pct": round(n_amp / n_total * 100, 2) if n_total else 0,
            "deletion_pct":    round(n_del / n_total * 100, 2) if n_total else 0,
        })

    return pd.DataFrame(rows).sort_values(
        ["gene_symbol", "alteration_pct"], ascending=[True, False]
    ).reset_index(drop=True)


def build_psma_cd46_cooccurrence(cna: pd.DataFrame) -> pd.DataFrame:
    """
    Per-sample: is CD46 amplified AND FOLH1(PSMA) deleted/low?
    Core therapeutic rationale: PSMA-failed patients → CD46 targetable.
    """
    if cna.empty or "gene_symbol" not in cna.columns:
        return pd.DataFrame()

    id_col = "sample_id" if "sample_id" in cna.columns else "patient_id"

    cd46  = cna[cna["gene_symbol"] == "CD46"][[id_col, "cna_value"]].rename(columns={"cna_value": "cd46_cna"})
    folh1 = cna[cna["gene_symbol"] == "FOLH1"][[id_col, "cna_value"]].rename(columns={"cna_value": "folh1_cna"})

    if cd46.empty or folh1.empty:
        print("  PSMA/CD46: one gene missing from CNA data")
        return pd.DataFrame()

    merged = cd46.merge(folh1, on=id_col, how="inner")
    merged["cd46_status"]  = merged["cd46_cna"].apply(
        lambda v: "Amplified (≥2)" if v >= 2 else ("Gained (+1)" if v == 1 else
                  ("Shallow Del" if v == -1 else ("Deep Del (≤-2)" if v <= -2 else "Diploid"))))
    merged["folh1_status"] = merged["folh1_cna"].apply(
        lambda v: "PSMA Deleted (FOLH1≤-1)" if v <= -1 else "PSMA Normal/High")
    merged["psma_low_cd46_high"] = (merged["folh1_cna"] <= -1) & (merged["cd46_cna"] >= 1)

    n_total = len(merged)
    n_combo = int(merged["psma_low_cd46_high"].sum())
    print(f"  PSMA-low + CD46-altered: {n_combo:,} / {n_total:,} ({n_combo/n_total*100:.1f}%)")

    summary = merged.groupby(["folh1_status", "cd46_status"]).size().reset_index(name="n_samples")
    summary["pct_of_total"] = (summary["n_samples"] / n_total * 100).round(2)
    summary["therapeutic_relevance"] = summary.apply(
        lambda r: "HIGH — PSMA-failed, CD46 targetable" if (
            "Deleted" in r["folh1_status"] and r["cd46_status"] in ("Amplified (≥2)", "Gained (+1)")
        ) else "Low / Monitor", axis=1
    )
    return summary


def build_mutation_summary() -> pd.DataFrame:
    path = DATA_DIR / "prad_mutations.parquet"
    if not path.exists():
        return pd.DataFrame()
    mut = pd.read_parquet(path)
    if mut.empty or "gene_symbol" not in mut.columns:
        return pd.DataFrame()
    # Fix empty gene symbols
    if "entrez_id" in mut.columns:
        mut["gene_symbol"] = mut["entrez_id"].map(ENTREZ_TO_GENE).fillna(mut["gene_symbol"])

    cd46_mut = mut[mut["gene_symbol"] == "CD46"]
    if cd46_mut.empty:
        return pd.DataFrame()

    summary = cd46_mut.groupby("variant_class").size().reset_index(name="count")
    summary["pct"] = (summary["count"] / summary["count"].sum() * 100).round(1)
    return summary.sort_values("count", ascending=False)


def run():
    print("Loading cBioPortal parquet files...")
    cna = load_cna()
    clinical = load_clinical()
    print(f"CNA rows: {len(cna):,}  |  Clinical rows: {len(clinical):,}")
    print(f"Genes in CNA: {cna['gene_symbol'].value_counts().to_dict() if not cna.empty else 'none'}")

    if cna.empty:
        print("ERROR: No CNA data found. Run cbioportal_downloader.py first.")
        return

    print("\nBuilding CNA alteration summary by cohort...")
    cna_summary = build_cna_summary(cna, clinical)
    if not cna_summary.empty:
        out = DATA_DIR / "genie_cd46_cna_summary.parquet"
        cna_summary.to_parquet(out, index=False)
        print(f"Saved {out.name}  ({len(cna_summary)} rows)")
        print(cna_summary.to_string(index=False))

    print("\nBuilding PSMA / CD46 co-occurrence table...")
    cooccur = build_psma_cd46_cooccurrence(cna)
    if not cooccur.empty:
        out = DATA_DIR / "genie_psma_cd46_cooccurrence.parquet"
        cooccur.to_parquet(out, index=False)
        print(f"Saved {out.name}")
        print(cooccur.to_string(index=False))

    print("\nBuilding mutation summary...")
    mut_summary = build_mutation_summary()
    if not mut_summary.empty:
        out = DATA_DIR / "genie_mutation_summary.parquet"
        mut_summary.to_parquet(out, index=False)
        print(f"Saved {out.name}")
        print(mut_summary.to_string(index=False))

    print("\nProcessing complete.")


if __name__ == "__main__":
    run()
