"""Load relevant therapeutic agents into AuraDB as Drug nodes.

Sources:
  1. ChEMBL REST API (CC BY-SA 4.0, no account needed) — complement inhibitors
     and PSMA-targeted agents that are clinically relevant to CD46 context
  2. Manually curated CD46-targeting agents from literature/clinical trials
     (antibodies/biologics not in ChEMBL small-molecule data)

CD46 note: CD46 is primarily an antibody/biologic target. ChEMBL's small-molecule
database does not contain direct CD46 bioactivity data. This loader instead loads:
  - CD46-targeting biologics (manually curated from NCT trials + publications)
  - Complement pathway inhibitors (ChEMBL — mechanistically relevant)
  - PSMA-targeted RLT agents (ChEMBL — competitive landscape context)

Run:
    python scripts/load_kg_chembl.py
Then verify:
    python scripts/audit_kg.py
"""
import json
import os
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1] / ".env")
sys.path.insert(0, str(Path(__file__).resolve().parent))

from neo4j import GraphDatabase


def get_driver():
    uri = os.getenv("NEO4J_URI")
    user = os.getenv("NEO4J_USERNAME", "neo4j")
    password = os.getenv("NEO4J_PASSWORD")
    if not uri or not password:
        raise RuntimeError("NEO4J_URI and NEO4J_PASSWORD must be set in .env")
    driver = GraphDatabase.driver(uri, auth=(user, password))
    driver.verify_connectivity()
    return driver


def chembl_get(endpoint: str, params: dict) -> dict:
    qs = urllib.parse.urlencode({**params, "format": "json"})
    url = f"https://www.ebi.ac.uk/chembl/api/data/{endpoint}?{qs}"
    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


# ---------------------------------------------------------------------------
# Curated CD46-targeting agents (antibodies/biologics from literature + NCT)
# Source: ClinicalTrials.gov, published Phase I data, PubMed
# ---------------------------------------------------------------------------
CD46_AGENTS = [
    {
        "name": "FOR46",
        "drug_type": "ADC",
        "mechanism": "Anti-CD46 antibody-drug conjugate (DM4 payload)",
        "target": "CD46",
        "developer": "Fortis Therapeutics / AstraZeneca",
        "max_phase": 1,
        "indication": "mCRPC, myeloma",
        "isotope": None,
        "source": "ClinicalTrials.gov NCT03959397 / PubMed",
        "chembl_id": None,
    },
    {
        "name": "225Ac-DOTA-CD46-Antibody",
        "drug_type": "RadioligandTherapy",
        "mechanism": "Anti-CD46 antibody conjugated to 225Ac alpha-emitter",
        "target": "CD46",
        "developer": "Academic / Preclinical",
        "max_phase": 0,
        "indication": "CD46+ solid tumours",
        "isotope": "225Ac",
        "source": "PubMed preclinical data",
        "chembl_id": None,
    },
    {
        "name": "BC8-CD46 (131I-BC8)",
        "drug_type": "RadioligandTherapy",
        "mechanism": "Anti-CD46 antibody radiolabelled with 131I",
        "target": "CD46",
        "developer": "Fred Hutchinson / Academic",
        "max_phase": 1,
        "indication": "AML, myeloma",
        "isotope": "131I",
        "source": "ClinicalTrials.gov / PubMed",
        "chembl_id": None,
    },
    {
        "name": "IMGN779 (CD33-ADC)",
        "drug_type": "ADC",
        "mechanism": "Anti-CD33 ADC — combination partner in CD46-high AML",
        "target": "CD33",
        "developer": "ImmunoGen",
        "max_phase": 2,
        "indication": "AML",
        "isotope": None,
        "source": "ClinicalTrials.gov / ChEMBL",
        "chembl_id": "CHEMBL3707330",
    },
]

# ---------------------------------------------------------------------------
# PSMA-targeted RLT agents — competitive landscape context
# Source: ChEMBL + FDA approvals
# ---------------------------------------------------------------------------
PSMA_RLT_CHEMBL_IDS = [
    "CHEMBL4523781",  # 177Lu-PSMA-617 (Pluvicto / lutetium vipivotide tetraxetan)
]

PSMA_RLT_MANUAL = [
    {
        "name": "177Lu-PSMA-617 (Pluvicto)",
        "drug_type": "RadioligandTherapy",
        "mechanism": "PSMA-targeting small molecule conjugated to 177Lu beta-emitter",
        "target": "PSMA (FOLH1)",
        "developer": "Novartis",
        "max_phase": 4,
        "indication": "PSMA+ mCRPC",
        "isotope": "177Lu",
        "source": "FDA approved 2022 / ChEMBL CHEMBL4523781",
        "chembl_id": "CHEMBL4523781",
    },
    {
        "name": "225Ac-PSMA-617",
        "drug_type": "RadioligandTherapy",
        "mechanism": "PSMA-targeting small molecule conjugated to 225Ac alpha-emitter",
        "target": "PSMA (FOLH1)",
        "developer": "Various (investigational)",
        "max_phase": 2,
        "indication": "PSMA+ mCRPC",
        "isotope": "225Ac",
        "source": "ClinicalTrials.gov multiple NCTs",
        "chembl_id": None,
    },
]

# ---------------------------------------------------------------------------
# Complement pathway inhibitors — mechanistically relevant to CD46
# ---------------------------------------------------------------------------
COMPLEMENT_CHEMBL_IDS = [
    "CHEMBL1201823",  # Eculizumab (anti-C5, Soliris) — complement inhibitor, aHUS
    "CHEMBL4296393",  # Ravulizumab (anti-C5, Ultomiris) — complement inhibitor
]


def fetch_chembl_molecule(chembl_id: str) -> dict:
    try:
        data = chembl_get("molecule", {"molecule_chembl_id": chembl_id})
        mols = data.get("molecules", [])
        if not mols:
            return {}
        m = mols[0]
        return {
            "chembl_id": chembl_id,
            "name": m.get("pref_name") or chembl_id,
            "molecule_type": m.get("molecule_type", ""),
            "max_phase": m.get("max_phase", 0),
            "smiles": (m.get("molecule_structures") or {}).get("canonical_smiles", ""),
            "mw": (m.get("molecule_properties") or {}).get("mw_freebase", None),
        }
    except Exception as e:
        print(f"    Warning: could not fetch {chembl_id}: {e}")
        return {"chembl_id": chembl_id}


DRUG_MERGE_CYPHER = """
MERGE (d:Drug {name: $name})
ON CREATE SET
    d.drug_type      = $drug_type,
    d.mechanism      = $mechanism,
    d.target_protein = $target,
    d.developer      = $developer,
    d.max_phase      = $max_phase,
    d.indication     = $indication,
    d.isotope        = $isotope,
    d.source         = $source,
    d.chembl_id      = $chembl_id,
    d.smiles         = $smiles,
    d.molecule_type  = $molecule_type
ON MATCH SET
    d.max_phase  = $max_phase,
    d.chembl_id  = COALESCE(d.chembl_id, $chembl_id),
    d.smiles     = COALESCE(d.smiles, $smiles)
RETURN d.name AS name
"""

# Relationship: Drug TARGETS Gene/Protein
TARGET_CYPHER = """
MATCH (d:Drug {name: $drug_name})
MATCH (g:Gene {symbol: $gene_symbol})
MERGE (d)-[r:TARGETS]->(g)
ON CREATE SET r.source = $source, r.evidence = $evidence
RETURN type(r)
"""

INDICATED_FOR_CYPHER = """
MATCH (d:Drug {name: $drug_name})
MATCH (dis:Disease)
WHERE dis.name CONTAINS $disease_fragment OR dis.tcga_code = $tcga_code
WITH d, dis LIMIT 1
MERGE (d)-[r:INDICATED_FOR]->(dis)
ON CREATE SET r.source = $source
RETURN type(r)
"""


def load_drugs(driver, drugs: list[dict]) -> int:
    count = 0
    with driver.session() as session:
        for drug in drugs:
            session.run(
                DRUG_MERGE_CYPHER,
                name=drug["name"],
                drug_type=drug.get("drug_type", ""),
                mechanism=drug.get("mechanism", ""),
                target=drug.get("target", ""),
                developer=drug.get("developer", ""),
                max_phase=drug.get("max_phase", 0),
                indication=drug.get("indication", ""),
                isotope=drug.get("isotope") or "",
                source=drug.get("source", "ChEMBL CC BY-SA 4.0"),
                chembl_id=drug.get("chembl_id") or "",
                smiles=drug.get("smiles", ""),
                molecule_type=drug.get("molecule_type", ""),
            )
            count += 1

            # TARGETS relationship for CD46 agents
            target_gene = drug.get("_target_gene")
            if target_gene:
                session.run(
                    TARGET_CYPHER,
                    drug_name=drug["name"],
                    gene_symbol=target_gene,
                    source=drug.get("source", ""),
                    evidence=drug.get("mechanism", ""),
                )
    return count


def main():
    print("=== ChEMBL / Curated Drug Loader ===")
    print("Note: CD46 is an antibody/biologic target; loading curated agents + complement inhibitors\n")

    driver = get_driver()
    all_drugs = []

    # --- CD46-targeting agents (curated) ---
    print("1. CD46-targeting agents (curated from NCT/PubMed)...")
    for agent in CD46_AGENTS:
        agent["_target_gene"] = "CD46"
        all_drugs.append(agent)
        print(f"   + {agent['name']} (Phase {agent['max_phase']})")

    # --- PSMA RLT agents ---
    print("\n2. PSMA RLT agents (competitive landscape context)...")
    for agent in PSMA_RLT_MANUAL:
        if agent.get("chembl_id"):
            mol = fetch_chembl_molecule(agent["chembl_id"])
            agent["smiles"] = mol.get("smiles", "")
            agent["molecule_type"] = mol.get("molecule_type", "SmallMolecule")
            time.sleep(0.3)
        agent["_target_gene"] = "FOLH1"
        all_drugs.append(agent)
        print(f"   + {agent['name']} (Phase {agent['max_phase']})")

    # --- Complement inhibitors ---
    print("\n3. Complement pathway inhibitors (ChEMBL CC BY-SA 4.0)...")
    complement_meta = {
        "CHEMBL1201823": {
            "name": "Eculizumab (Soliris)",
            "drug_type": "Antibody",
            "mechanism": "Anti-C5 complement inhibitor — blocks terminal complement cascade (mechanistically relevant to CD46 biology)",
            "target": "C5 (Complement component 5)",
            "developer": "Alexion / AstraZeneca",
            "indication": "aHUS, PNH",
            "isotope": None,
            "source": "ChEMBL CHEMBL1201823 CC BY-SA 4.0",
        },
        "CHEMBL4296393": {
            "name": "Ravulizumab (Ultomiris)",
            "drug_type": "Antibody",
            "mechanism": "Long-acting anti-C5 complement inhibitor (next-gen eculizumab)",
            "target": "C5 (Complement component 5)",
            "developer": "Alexion / AstraZeneca",
            "indication": "aHUS, PNH, gMG",
            "isotope": None,
            "source": "ChEMBL CHEMBL4296393 CC BY-SA 4.0",
        },
    }
    for chembl_id in COMPLEMENT_CHEMBL_IDS:
        mol = fetch_chembl_molecule(chembl_id)
        meta = complement_meta.get(chembl_id, {})
        drug = {
            **meta,
            "chembl_id": chembl_id,
            "smiles": mol.get("smiles", ""),
            "molecule_type": mol.get("molecule_type", "Antibody"),
            "max_phase": mol.get("max_phase", 4),
            "_target_gene": None,
        }
        all_drugs.append(drug)
        print(f"   + {drug['name']} (Phase {drug['max_phase']})")
        time.sleep(0.3)

    # --- Load all into AuraDB ---
    print(f"\n4. Loading {len(all_drugs)} Drug nodes into AuraDB...")
    try:
        n = load_drugs(driver, all_drugs)
        print(f"   ✅ {n} Drug nodes upserted")
    finally:
        driver.close()

    print("\nRun scripts/audit_kg.py to confirm counts.")


if __name__ == "__main__":
    main()
