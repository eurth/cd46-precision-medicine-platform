"""Self-check for Step 3b PubMed/ChEMBL gene loader (no network, no Neo4j)."""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "scripts"))

import load_gene_pubmed_chembl as m  # noqa: E402


def main() -> None:
    assert m.CHEMBL_BY_UNIPROT["Q04609"] == "CHEMBL1892"
    assert m.CHEMBL_BY_UNIPROT["Q12884"] == "CHEMBL4683"
    assert "FOLH1" in m.CURATED_AGENTS and len(m.CURATED_AGENTS["FOLH1"]) >= 1
    t = {"symbol": "FOLH1", "aliases": ["PSMA"], "name": "Folate hydrolase 1 (PSMA)", "uniprot_id": "Q04609"}
    qs = m._pubmed_queries(t)
    assert any("FOLH1" in q for q in qs)
    assert m._evidence_type("Phase I clinical trial of X", "") == "Clinical trial"
    # Bad CD46 placeholder rejected
    assert m.resolve_chembl_target_id({"chembl_target_id": "CHEMBL2176", "uniprot_id": "P15529"}) is None
    assert m.resolve_chembl_target_id({"chembl_target_id": "", "uniprot_id": "Q04609"}) == "CHEMBL1892"
    print("check_step3b_pubmed_chembl: OK")


if __name__ == "__main__":
    main()
