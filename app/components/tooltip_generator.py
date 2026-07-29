"""Tooltip / entity card lookup from config/tooltip_terms.csv + offline cache."""
from __future__ import annotations

import csv
import json
import re
from functools import lru_cache
from pathlib import Path
from typing import Any

import streamlit as st

_ROOT = Path(__file__).resolve().parents[2]
_CSV = _ROOT / "config" / "tooltip_terms.csv"
_CACHE = _ROOT / "data" / "processed" / "tooltip_cache"


def _safe_id(term_id: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "_", term_id)


@lru_cache(maxsize=1)
def _load_terms() -> list[dict[str, str]]:
    if not _CSV.exists():
        return []
    with _CSV.open(encoding="utf-8", newline="") as f:
        return [
            r
            for r in csv.DictReader(f)
            if str(r.get("enabled", "true")).lower() in ("1", "true", "yes")
        ]


def _alias_index() -> dict[str, dict[str, str]]:
    idx: dict[str, dict[str, str]] = {}
    for row in _load_terms():
        keys = [row.get("canonical_name", ""), *(row.get("aliases") or "").split("|")]
        for k in keys:
            k = (k or "").strip()
            if not k:
                continue
            idx[k.upper()] = row
            idx[k.lower()] = row
    return idx


def lookup(term: str) -> dict[str, Any] | None:
    """Return mapping row + optional cache fields for a display term."""
    if not term or not str(term).strip():
        return None
    raw = str(term).strip()
    idx = _alias_index()
    row = idx.get(raw) or idx.get(raw.upper()) or idx.get(raw.lower())
    if not row:
        return None
    out: dict[str, Any] = dict(row)
    cache_path = _CACHE / f"{_safe_id(row['term_id'])}.json"
    if cache_path.exists():
        try:
            cached = json.loads(cache_path.read_text(encoding="utf-8"))
            for k, v in cached.items():
                if v and k != "raw_entry":
                    out[k] = v
            out["_cache"] = cached
        except Exception:
            pass
    return out


def render_entity_popover(term: str, *, label: str | None = None) -> None:
    """Streamlit click → popover entity card (v1; hover deferred)."""
    hit = lookup(term)
    title = label or term
    if hit is None:
        st.caption(title)
        return
    with st.popover(title):
        st.markdown(f"**{hit.get('canonical_name') or term}**")
        aliases = (hit.get("aliases") or "").replace("|", ", ")
        if aliases:
            st.caption(aliases)
        if hit.get("summary_short"):
            st.write(hit["summary_short"])
        uid = hit.get("uniprot_id")
        if uid:
            st.markdown(
                f"UniProt: [`{uid}`](https://www.uniprot.org/uniprotkb/{str(uid).split('-')[0]}/entry)"
            )
        af_url = hit.get("alphafold_entry_url")
        af_id = hit.get("alphafold_entry_id")
        if af_url:
            st.markdown(f"AlphaFold: [`{af_id or 'structure'}`]({af_url})")
        pae = hit.get("alphafold_pae_image_url")
        if pae:
            st.image(pae, caption="Predicted aligned error (PAE)", use_container_width=True)
        metric = hit.get("globalMetricValue")
        if metric is not None:
            st.caption(f"Mean pLDDT / global metric: {metric}")
        extras = []
        if hit.get("hpa_url"):
            extras.append(f"[HPA]({hit['hpa_url']})")
        if hit.get("ot_url"):
            extras.append(f"[Open Targets]({hit['ot_url']})")
        if hit.get("chembl_target_id"):
            extras.append(f"ChEMBL `{hit['chembl_target_id']}`")
        if extras:
            st.markdown(" · ".join(extras))


def linkify_label(term: str) -> str:
    """Markdown label; pages should prefer render_entity_popover for interactivity."""
    hit = lookup(term)
    if not hit:
        return term
    url = hit.get("alphafold_entry_url") or (
        f"https://www.uniprot.org/uniprotkb/{hit['uniprot_id']}/entry"
        if hit.get("uniprot_id")
        else ""
    )
    if url:
        return f"[{hit.get('canonical_name') or term}]({url})"
    return hit.get("canonical_name") or term


def assert_tooltip_seed() -> None:
    """ponytail: registry five + SSTR2 isoform AlphaFold URLs."""
    sstr2 = lookup("SSTR2")
    assert sstr2 and "AF-P30874-F1" in (sstr2.get("alphafold_entry_url") or "")
    iso = lookup("SSTR2 isoform 2") or lookup("P30874-2")
    assert iso and "AF-P30874-2-F1" in (iso.get("alphafold_entry_url") or "")
    assert lookup("FOLH1") and lookup("CD46") and lookup("FAP") and lookup("GRPR")


if __name__ == "__main__":
    assert_tooltip_seed()
    print("tooltip_seed_ok")
