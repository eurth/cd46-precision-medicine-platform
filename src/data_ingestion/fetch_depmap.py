"""
DepMap data handler — expects manual download of CCLE_expression.csv
and CRISPRGeneEffect.csv from https://depmap.org/portal/data_page/

Files are too large for automated API download (~600MB each).
This module verifies files exist and provides extraction utilities.
"""

import logging
from pathlib import Path

import yaml

log = logging.getLogger(__name__)

_CONFIG_PATH = Path(__file__).parents[2] / "config" / "datasets.yaml"
with open(_CONFIG_PATH) as f:
    _DS = yaml.safe_load(f)["depmap"]

CRISPR_PATH = Path(_DS["files"]["crispr"]["local_path"])
META_PATH = Path(_DS["files"]["metadata"]["local_path"])
CD46_COLUMN = _DS["files"]["crispr"]["cd46_column"]


def check_depmap_files() -> dict[str, bool]:
    """Check whether required DepMap files exist."""
    return {
        "crispr": CRISPR_PATH.exists(),
        "metadata": META_PATH.exists(),
    }


def get_download_instructions() -> str:
    return """
DepMap Manual Download Instructions (25Q3):
============================================
1. Go to https://depmap.org/portal/data_page/
2. Download: CRISPRGeneEffect.csv
3. Download: Model.csv
4. Place both files in: data/raw/depmap/

Files needed:
  - data/raw/depmap/CCLE_expression.csv     (~600 MB)
  - data/raw/depmap/CRISPRGeneEffect.csv    (~200 MB)
"""


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    status = check_depmap_files()
    for name, exists in status.items():
        icon = "✅" if exists else "❌"
        print(f"  {icon} {name}: {'found' if exists else 'MISSING'}")
    if not all(status.values()):
        print(get_download_instructions())
