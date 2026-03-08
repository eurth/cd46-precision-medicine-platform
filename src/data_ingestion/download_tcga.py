"""
Download TCGA expression, phenotype, and survival data from UCSC Xena.
Uses streaming download with progress bar — no full file loaded into RAM.
"""

import os
import hashlib
import logging
from pathlib import Path

import requests
from tqdm import tqdm
import yaml

log = logging.getLogger(__name__)

# Load dataset config
_CONFIG_PATH = Path(__file__).parents[2] / "config" / "datasets.yaml"
with open(_CONFIG_PATH) as f:
    _DS = yaml.safe_load(f)["tcga"]

TCGA_FILES = {
    "expression": {
        "url": _DS["expression"]["url"],
        "local": Path(_DS["expression"]["local_path"]),
    },
    "phenotype": {
        "url": _DS["phenotype"]["url"],
        "local": Path(_DS["phenotype"]["local_path"]),
    },
    "survival": {
        "url": _DS["survival"]["url"],
        "local": Path(_DS["survival"]["local_path"]),
    },
}


def download_file(url: str, dest: Path, chunk_size: int = 1024 * 1024) -> Path:
    """Stream-download a file to dest with tqdm progress bar."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists():
        log.info("Already downloaded: %s (%.1f MB)", dest.name, dest.stat().st_size / 1e6)
        return dest

    log.info("Downloading %s → %s", url, dest)
    with requests.get(url, stream=True, timeout=300) as r:
        r.raise_for_status()
        total = int(r.headers.get("content-length", 0))
        with open(dest, "wb") as f, tqdm(
            total=total, unit="B", unit_scale=True, desc=dest.name
        ) as bar:
            for chunk in r.iter_content(chunk_size=chunk_size):
                f.write(chunk)
                bar.update(len(chunk))

    log.info("Saved %s (%.1f MB)", dest.name, dest.stat().st_size / 1e6)
    return dest


def download_all(force: bool = False) -> dict[str, Path]:
    """Download all TCGA files. Returns dict of key → local path."""
    results = {}
    for key, info in TCGA_FILES.items():
        dest = info["local"]
        if force and dest.exists():
            dest.unlink()
        results[key] = download_file(info["url"], dest)
    return results


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    paths = download_all()
    for k, p in paths.items():
        print(f"  {k}: {p}")
