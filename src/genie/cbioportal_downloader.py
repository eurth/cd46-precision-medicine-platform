"""
Download CD46-relevant data from cBioPortal public API.
No authentication required — uses public study data.

Best available prostate cancer cohorts:
  prad_su2c_2019     — 444 mCRPC (SU2C/PCF, PNAS 2019) — MOST RELEVANT for 225Ac-CD46
  prad_tcga          — 499 localised PRAD (TCGA Firehose)
  prad_mich          — 61 metastatic (Michigan, Nature 2012)
  prostate_dkfz_2018 — 150 (DKFZ, Cancer Cell 2018)

Genes of interest:
  CD46   Entrez 4179 — primary therapeutic target
  FOLH1  Entrez 2346 — PSMA, complementarity biomarker
  AR     Entrez 367  — androgen receptor, CD46 upregulator
  MYC    Entrez 4609 — co-amplification marker
"""
import time
from pathlib import Path

import requests
import pandas as pd

BASE_URL = "https://www.cbioportal.org/api"
OUT_DIR = Path(__file__).resolve().parents[2] / "data" / "genie"

STUDIES = {
    "prad_su2c_2019": {
        "label": "SU2C mCRPC 2019",
        "description": "444 mCRPC: Abida et al., PNAS 2019",
        "mrna_profile": "prad_su2c_2019_mrna_seq_fpkm_polya",
        "cna_profile":  "prad_su2c_2019_gistic",
        "mut_profile":  "prad_su2c_2019_mutations",
    },
    "prad_tcga": {
        "label": "TCGA PRAD",
        "description": "499 localised prostate adenocarcinoma (TCGA Firehose Legacy)",
        "mrna_profile": "prad_tcga_rna_seq_v2_mrna",
        "cna_profile":  "prad_tcga_gistic",
        "mut_profile":  "prad_tcga_mutations",
    },
    "prad_mich": {
        "label": "Michigan mPRAD",
        "description": "61 metastatic prostate adenocarcinoma (MCTP, Nature 2012)",
        "mrna_profile": None,
        "cna_profile":  "prad_mich_cna",
        "mut_profile":  "prad_mich_mutations",
    },
    "prostate_dkfz_2018": {
        "label": "DKFZ Prostate 2018",
        "description": "150 prostate cancer (DKFZ, Cancer Cell 2018)",
        "mrna_profile": "prostate_dkfz_2018_mrna",
        "cna_profile":  "prostate_dkfz_2018_cna",
        "mut_profile":  "prostate_dkfz_2018_mutations",
    },
}

GENES = {"CD46": 4179, "FOLH1": 2346, "AR": 367, "MYC": 4609}

SESSION = requests.Session()
SESSION.headers.update({"Accept": "application/json", "Content-Type": "application/json"})


def _post(endpoint, payload, timeout=120):
    url = BASE_URL + endpoint
    for attempt in range(3):
        try:
            r = SESSION.post(url, json=payload, timeout=timeout)
            if r.status_code == 404:
                return []
            r.raise_for_status()
            return r.json() or []
        except requests.RequestException:
            if attempt == 2:
                return []
            time.sleep(2 ** attempt)
    return []


def _get(endpoint, params=None, timeout=60):
    url = BASE_URL + endpoint
    for attempt in range(3):
        try:
            r = SESSION.get(url, params=params, timeout=timeout)
            if r.status_code == 404:
                return []
            r.raise_for_status()
            return r.json() or []
        except requests.RequestException:
            if attempt == 2:
                return []
            time.sleep(2 ** attempt)
    return []


def fetch_molecular_data(profile_id, study_id, entrez_ids):
    if not profile_id:
        return pd.DataFrame()
    data = _post(
        "/molecular-profiles/" + profile_id + "/molecular-data/fetch",
        {"entrezGeneIds": entrez_ids, "sampleListId": study_id + "_all"},
    )
    if not data:
        return pd.DataFrame()
    rows = []
    for d in data:
        gene_info = d.get("gene", {})
        rows.append({
            "sample_id":   d.get("sampleId"),
            "patient_id":  d.get("patientId"),
            "study_id":    d.get("studyId", study_id),
            "entrez_id":   d.get("entrezGeneId"),
            "gene_symbol": gene_info.get("hugoGeneSymbol", ""),
            "profile_id":  d.get("molecularProfileId"),
            "value":       d.get("value"),
        })
    return pd.DataFrame(rows)


def fetch_mutations(profile_id, study_id, entrez_ids):
    if not profile_id:
        return pd.DataFrame()
    data = _post(
        "/molecular-profiles/" + profile_id + "/mutations/fetch",
        {"entrezGeneIds": entrez_ids, "sampleListId": study_id + "_all"},
    )
    if not data:
        return pd.DataFrame()
    rows = []
    for m in data:
        gene_info = m.get("gene", {})
        rows.append({
            "sample_id":      m.get("sampleId"),
            "patient_id":     m.get("patientId"),
            "study_id":       m.get("studyId", study_id),
            "gene_symbol":    gene_info.get("hugoGeneSymbol", ""),
            "entrez_id":      m.get("entrezGeneId"),
            "mutation_type":  m.get("mutationType"),
            "variant_class":  m.get("variantClassification"),
            "protein_change": m.get("proteinChange"),
        })
    return pd.DataFrame(rows)


def fetch_clinical(study_id):
    data = _get(
        "/studies/" + study_id + "/clinical-data",
        params={"clinicalDataType": "PATIENT", "pageSize": 100000},
    )
    if not data:
        return pd.DataFrame()
    df = pd.DataFrame(data)
    if "clinicalAttributeId" in df.columns:
        df = df.pivot_table(
            index="patientId", columns="clinicalAttributeId",
            values="value", aggfunc="first",
        ).reset_index()
        df.columns.name = None
        df = df.rename(columns={"patientId": "patient_id"})
    return df


def run():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    entrez_ids = list(GENES.values())
    all_mrna, all_cna, all_mut, all_clin = [], [], [], []

    for study_id, cfg in STUDIES.items():
        print("\n" + "=" * 60)
        print("Study : " + cfg["label"])
        print("Detail: " + cfg["description"])

        mrna = fetch_molecular_data(cfg["mrna_profile"], study_id, entrez_ids)
        if not mrna.empty:
            mrna["data_type"] = "mrna_fpkm"
            all_mrna.append(mrna)
            print("  mRNA : " + str(len(mrna)) + " records")
        else:
            print("  mRNA : not available")

        cna = fetch_molecular_data(cfg["cna_profile"], study_id, entrez_ids)
        if not cna.empty:
            cna["data_type"] = "cna_gistic"
            all_cna.append(cna)
            print("  CNA  : " + str(len(cna)) + " records")
        else:
            print("  CNA  : not available")

        mut = fetch_mutations(cfg["mut_profile"], study_id, entrez_ids)
        if not mut.empty:
            all_mut.append(mut)
            print("  Mut  : " + str(len(mut)) + " records")
        else:
            print("  Mut  : none found")

        clin = fetch_clinical(study_id)
        if not clin.empty:
            clin["study_id"] = study_id
            clin["study_label"] = cfg["label"]
            all_clin.append(clin)
            print("  Clin : " + str(len(clin)) + " patients")

    def save(frames, name):
        if not frames:
            print("  (no data for " + name + ")")
            return
        combined = pd.concat(frames, ignore_index=True)
        path = OUT_DIR / name
        combined.to_parquet(path, index=False)
        print("Saved " + name + "  (" + str(len(combined)) + " rows)")

    print("\n" + "=" * 60)
    print("Saving files...")
    save(all_mrna, "prad_mrna.parquet")
    save(all_cna,  "prad_cna.parquet")
    save(all_mut,  "prad_mutations.parquet")
    save(all_clin, "prad_clinical.parquet")
    print("\nDownload complete. Run src/genie/processor.py next.")


if __name__ == "__main__":
    run()
