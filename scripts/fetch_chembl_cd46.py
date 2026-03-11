"""Fetch CD46 drug-target interactions from ChEMBL REST API (no account needed, CC BY-SA 4.0).

Fetches:
  1. CD46 target record (CHEMBL2176768 — human CD46/MCP)
  2. All bioactivities against CD46
  3. Molecule details for each unique compound

Saves to: data/raw/apis/chembl_cd46_full.json

Run: python scripts/fetch_chembl_cd46.py
Then: python scripts/load_kg_chembl.py
"""
import json
import sys
import time
import urllib.request
import urllib.parse
from pathlib import Path

BASE_URL = "https://www.ebi.ac.uk/chembl/api/data"
CD46_CHEMBL_TARGET = "CHEMBL2176768"  # Human CD46 / Membrane Cofactor Protein
OUT_PATH = Path(__file__).resolve().parents[1] / "data" / "raw" / "apis" / "chembl_cd46_full.json"


def chembl_get(endpoint: str, params: dict) -> dict:
    """GET from ChEMBL REST API, returns parsed JSON."""
    qs = urllib.parse.urlencode({**params, "format": "json"})
    url = f"{BASE_URL}/{endpoint}?{qs}"
    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def fetch_all_pages(endpoint: str, params: dict, result_key: str) -> list:
    """Fetch all pages of a paginated ChEMBL endpoint."""
    all_results = []
    params = {**params, "limit": 100, "offset": 0}
    while True:
        data = chembl_get(endpoint, params)
        page = data.get(result_key, [])
        all_results.extend(page)
        page_meta = data.get("page_meta", {})
        next_url = page_meta.get("next")
        if not next_url or not page:
            break
        params["offset"] += params["limit"]
        time.sleep(0.3)  # polite rate limiting
    return all_results


def main():
    print("=== ChEMBL CD46 Fetch ===")

    # Step 1 — fetch target record
    print(f"Fetching target record: {CD46_CHEMBL_TARGET}...")
    target = chembl_get("target", {"target_chembl_id": CD46_CHEMBL_TARGET})
    targets = target.get("targets", [{}])
    if targets:
        t = targets[0]
        print(f"  Target: {t.get('pref_name')} | Type: {t.get('target_type')} | Organism: {t.get('organism')}")

    # Step 2 — fetch all bioactivities
    print("Fetching all bioactivities against CD46...")
    activities = fetch_all_pages(
        "activity",
        {
            "target_chembl_id": CD46_CHEMBL_TARGET,
            "standard_type__in": "IC50,Ki,Kd,EC50,Activity,Inhibition,GI50",
            "standard_relation__in": "=,<,<=",
        },
        "activities",
    )
    print(f"  Found {len(activities)} bioactivities")

    # Also fetch activities without type filter to get broader coverage
    all_activities = fetch_all_pages(
        "activity",
        {"target_chembl_id": CD46_CHEMBL_TARGET},
        "activities",
    )
    print(f"  Total activities (all types): {len(all_activities)}")

    # De-duplicate by activity_id
    seen = set()
    deduped = []
    for a in all_activities:
        aid = a.get("activity_id")
        if aid not in seen:
            seen.add(aid)
            deduped.append(a)

    # Step 3 — fetch molecule details for each unique compound
    mol_ids = list({a.get("molecule_chembl_id") for a in deduped if a.get("molecule_chembl_id")})
    print(f"Fetching details for {len(mol_ids)} unique molecules...")

    molecules = {}
    batch_size = 20
    for i in range(0, len(mol_ids), batch_size):
        batch = mol_ids[i : i + batch_size]
        ids_param = ",".join(batch)
        try:
            data = chembl_get("molecule", {"molecule_chembl_id__in": ids_param})
            for mol in data.get("molecules", []):
                mid = mol.get("molecule_chembl_id")
                molecules[mid] = {
                    "chembl_id": mid,
                    "name": mol.get("pref_name") or mol.get("molecule_chembl_id"),
                    "molecule_type": mol.get("molecule_type", ""),
                    "max_phase": mol.get("max_phase", 0),
                    "indication_class": mol.get("indication_class", ""),
                    "therapeutic_flag": mol.get("therapeutic_flag", False),
                    "smiles": (mol.get("molecule_structures") or {}).get("canonical_smiles", ""),
                    "inchi_key": (mol.get("molecule_structures") or {}).get("standard_inchi_key", ""),
                    "mw": (mol.get("molecule_properties") or {}).get("mw_freebase", None),
                    "alogp": (mol.get("molecule_properties") or {}).get("alogp", None),
                }
        except Exception as e:
            print(f"  Warning: could not fetch batch {i}–{i+batch_size}: {e}")
        time.sleep(0.3)

    print(f"  Resolved {len(molecules)} molecule records")

    # Step 4 — annotate activities with molecule names
    for act in deduped:
        mid = act.get("molecule_chembl_id")
        if mid and mid in molecules:
            act["_molecule_name"] = molecules[mid]["name"]
            act["_molecule_type"] = molecules[mid]["molecule_type"]
            act["_max_phase"] = molecules[mid]["max_phase"]

    # Step 5 — save full dataset
    output = {
        "target": targets[0] if targets else {},
        "activities": deduped,
        "molecules": molecules,
        "fetch_meta": {
            "target_chembl_id": CD46_CHEMBL_TARGET,
            "total_activities": len(deduped),
            "total_molecules": len(molecules),
            "source": "ChEMBL REST API v3 (CC BY-SA 4.0)",
            "fetched": "2026-03-09",
        },
    }
    OUT_PATH.write_text(json.dumps(output, indent=2), encoding="utf-8")
    print(f"\nSaved to {OUT_PATH}")
    print(f"Summary: {len(deduped)} activities | {len(molecules)} molecules")
    print("Now run: python scripts/load_kg_chembl.py")


if __name__ == "__main__":
    main()
