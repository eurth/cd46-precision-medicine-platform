"""Self-check for Step 3c loader helpers (no network, no Neo4j)."""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "scripts"))

import load_gene_uniprot_gtex_depmap as m  # noqa: E402


def main() -> None:
    assert m.depmap_column_name("FAP", 2191) == "FAP (2191)"
    assert m.depmap_column_name("FOLH1", 2346) == "FOLH1 (2346)"
    # Substring trap: AFAP1 must not be used for FAP
    assert "AFAP1" not in m.depmap_column_name("FAP", 2191)

    # HPA intensity processing
    raw = {
        "Protein tissue specific Intensity": {"intestine": "100.5", "skin": "bad"},
        "Protein cell type specific Intensity": {"Neurons": "50"},
        "Protein tissue specificity": "Tissue enriched",
        "Protein tissue distribution": "Detected in single",
        "Protein cell type specificity": "Cell type enhanced",
    }
    path = m.process_hpa_protein_intensity("TESTGENE", raw)
    import pandas as pd

    df = pd.read_csv(path)
    assert len(df) == 2  # intestine + Neurons; 'bad' skipped
    assert set(df["tissue"]) == {"intestine", "Neurons"}
    path.unlink(missing_ok=True)
    (m.PROC / "hpa_testgene_protein_summary.json").unlink(missing_ok=True)

    # GTEx skip cell-line tissues
    assert m.GTEX_TO_HPA["Cells - Cultured fibroblasts"] is None
    print("check_step3c_uniprot_gtex_depmap: OK")


if __name__ == "__main__":
    main()
