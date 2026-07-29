"""Enrich config/tooltip_terms.csv from AlphaFold (+ optional UniProt) into tooltip_cache.

Laptop ETL pattern: UI reads cache offline; this script hits live APIs.
"""
from __future__ import annotations

import csv
import json
import re
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CSV_PATH = ROOT / "config" / "tooltip_terms.csv"
CACHE_DIR = ROOT / "data" / "processed" / "tooltip_cache"
AF_API = "https://alphafold.ebi.ac.uk/api/prediction/{acc}"


def _safe_id(term_id: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "_", term_id)


def _fetch_json(url: str) -> list | dict | None:
    try:
        with urllib.request.urlopen(url, timeout=30) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as exc:
        print(f"  warn: {url} -> {exc}")
        return None


def _pick_entry(payload: list | dict | None, entry_id: str) -> dict | None:
    if not payload:
        return None
    rows = payload if isinstance(payload, list) else [payload]
    if entry_id:
        for row in rows:
            if str(row.get("entryId") or row.get("modelEntityId") or "") == entry_id:
                return row
            # isoform pages sometimes use modelEntityId
            if entry_id in str(row.get("entryId") or "") or entry_id in str(row.get("uniprotAccession") or ""):
                return row
    return rows[0] if rows else None


def main() -> None:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    with CSV_PATH.open(encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))

    out_rows = []
    for row in rows:
        if str(row.get("enabled", "true")).lower() not in ("1", "true", "yes"):
            out_rows.append(row)
            continue
        tid = row["term_id"]
        acc = (row.get("uniprot_id") or "").strip()
        # isoform accessions like P30874-2 work on AF API as-is for some; also try base
        print(f"enrich {tid} ({acc})")
        payload = _fetch_json(AF_API.format(acc=acc)) if acc else None
        if payload is None and "-" in acc:
            payload = _fetch_json(AF_API.format(acc=acc.split("-")[0]))
        entry = _pick_entry(payload, row.get("alphafold_entry_id") or "")
        cache = {
            "term_id": tid,
            "canonical_name": row.get("canonical_name"),
            "uniprot_id": acc,
            "alphafold_entry_id": row.get("alphafold_entry_id"),
            "alphafold_entry_url": row.get("alphafold_entry_url"),
            "summary_short": row.get("summary_short"),
        }
        if entry:
            eid = entry.get("entryId") or row.get("alphafold_entry_id")
            if eid and not row.get("alphafold_entry_id"):
                row["alphafold_entry_id"] = eid
            if eid:
                row["alphafold_entry_url"] = f"https://alphafold.ebi.ac.uk/entry/{eid}"
                cache["alphafold_entry_id"] = eid
                cache["alphafold_entry_url"] = row["alphafold_entry_url"]
            if entry.get("paeImageUrl"):
                row["alphafold_pae_image_url"] = entry["paeImageUrl"]
                cache["alphafold_pae_image_url"] = entry["paeImageUrl"]
            if entry.get("pdbUrl"):
                row["alphafold_pdb_url"] = entry["pdbUrl"]
                cache["alphafold_pdb_url"] = entry["pdbUrl"]
            if entry.get("globalMetricValue") is not None:
                cache["globalMetricValue"] = entry["globalMetricValue"]
            cache["raw_entry"] = {
                k: entry.get(k)
                for k in ("entryId", "uniprotAccession", "uniprotDescription", "modelCreatedDate")
                if k in entry
            }
        cache_path = CACHE_DIR / f"{_safe_id(tid)}.json"
        cache_path.write_text(json.dumps(cache, indent=2), encoding="utf-8")
        out_rows.append(row)

    if out_rows:
        fieldnames = list(out_rows[0].keys())
        with CSV_PATH.open("w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=fieldnames)
            w.writeheader()
            w.writerows(out_rows)
    print(f"wrote {len(out_rows)} cache files under {CACHE_DIR}")


if __name__ == "__main__":
    main()
