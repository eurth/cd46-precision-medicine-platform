"""Thin multi-target KG slice helpers (Phase 4).

IDs come from config/targets.yaml. Does not rename CD46 Disease schema props.
"""
from __future__ import annotations

import json
import urllib.parse
import urllib.request
import time
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

_ROOT = Path(__file__).resolve().parents[2]
_TARGETS = _ROOT / "config" / "targets.yaml"
_OT_URL = "https://api.platform.opentargets.org/api/v4/graphql"
_STRING_API = "https://string-db.org/api/json"
_TAXON = 9606


@lru_cache(maxsize=1)
def load_registry() -> dict[str, Any]:
    with _TARGETS.open(encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    if "targets" not in data:
        raise ValueError("targets.yaml missing targets")
    return data


def get_target(symbol: str) -> dict[str, Any]:
    targets = load_registry()["targets"]
    if symbol not in targets:
        raise KeyError(f"Unknown target: {symbol}")
    return {"symbol": symbol, **targets[symbol]}


def save_target_field(symbol: str, key: str, value: Any) -> None:
    """Update one field under targets.<symbol> in targets.yaml (preserves order poorly — fine)."""
    with _TARGETS.open(encoding="utf-8") as f:
        data = yaml.safe_load(f)
    data["targets"][symbol][key] = value
    with _TARGETS.open("w", encoding="utf-8") as f:
        yaml.safe_dump(data, f, default_flow_style=False, sort_keys=False)


def resolve_string_ensp(symbol: str) -> str:
    """Resolve HUGO symbol → STRING protein id (9606.ENSP…)."""
    qs = urllib.parse.urlencode(
        {
            "identifiers": symbol,
            "species": _TAXON,
            "limit": 1,
            "caller_identity": "oncobridge",
        }
    )
    url = f"{_STRING_API}/get_string_ids?{qs}"
    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        rows = json.loads(resp.read().decode("utf-8"))
    if not rows:
        raise RuntimeError(f"STRING has no id for {symbol}")
    return str(rows[0]["stringId"])


_OT_PAGE_MAX = 500  # ponytail: OT API ~500 rows/page — paginate for ot_size > 500 (up to 1000+)


def _ot_fetch_page(ensembl_id: str, page_size: int, index: int) -> dict:
    query = (
        "query TargetDiseases($ensemblId: String!, $pageSize: Int!, $index: Int!) {"
        " target(ensemblId: $ensemblId) {"
        "  id approvedSymbol"
        "  associatedDiseases(page: {index: $index, size: $pageSize}) {"
        "   count"
        "   rows {"
        "    disease { id name therapeuticAreas { id name } }"
        "    score"
        "    datasourceScores { id score }"
        "   }"
        "  }"
        " }"
        "}"
    )
    payload = json.dumps(
        {
            "query": query,
            "variables": {"ensemblId": ensembl_id, "pageSize": page_size, "index": index},
        }
    ).encode("utf-8")
    last_err: Exception | None = None
    for attempt in range(4):
        req = urllib.request.Request(
            _OT_URL,
            data=payload,
            headers={"Content-Type": "application/json", "Accept": "application/json"},
        )
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            if data.get("errors"):
                raise RuntimeError(f"Open Targets errors: {data['errors']}")
            return data
        except Exception as e:
            last_err = e
            time.sleep(5 * (attempt + 1))
    raise RuntimeError(f"Open Targets fetch failed: {last_err}")


def fetch_open_targets(ensembl_id: str, *, size: int | None = None) -> dict:
    """Fetch target–disease associations.

    size=None or size<=0 → fetch full API total (paginate all pages).
    size>0 → fetch up to that many rows (only for debugging).
    """
    page_size = _OT_PAGE_MAX
    all_rows: list[Any] = []
    index = 0
    merged: dict | None = None
    total_count = 0
    want = None if size is None or size <= 0 else max(1, size)
    while True:
        data = _ot_fetch_page(ensembl_id, page_size, index)
        target = (data.get("data") or {}).get("target") or {}
        assoc = target.get("associatedDiseases") or {}
        if merged is None:
            merged = data
            total_count = int(assoc.get("count") or 0)
        page_rows = assoc.get("rows") or []
        if not page_rows:
            break
        all_rows.extend(page_rows)
        if want is not None and len(all_rows) >= want:
            all_rows = all_rows[:want]
            break
        if len(page_rows) < page_size:
            break
        if total_count and len(all_rows) >= total_count:
            break
        index += 1
        time.sleep(0.2)
    if merged is None:
        merged = _ot_fetch_page(ensembl_id, page_size, 0)
        target = (merged.get("data") or {}).get("target") or {}
        assoc = target.get("associatedDiseases") or {}
        total_count = int(assoc.get("count") or 0)
    merged.setdefault("data", {}).setdefault("target", {}).setdefault(
        "associatedDiseases", {}
    )["rows"] = all_rows
    merged["data"]["target"]["associatedDiseases"]["count"] = total_count
    return merged


def load_ot_associations(session, symbol: str, ot_payload: dict, *, top_n: int | None = None) -> tuple[int, int]:
    """MERGE all associations in payload. top_n is ignored (kept for CLI compat)."""
    rows = (
        ot_payload.get("data", {})
        .get("target", {})
        .get("associatedDiseases", {})
        .get("rows", [])
    )
    if not rows:
        return 0, 0
    rows_sorted = sorted(rows, key=lambda r: r.get("score", 0), reverse=True)
    # ponytail: UNWIND batches beat per-row Aura round-trips
    batch: list[dict] = []
    for row in rows_sorted:
        disease = row.get("disease", {}) or {}
        mondo_id = disease.get("id") or ""
        if not mondo_id:
            continue
        areas = disease.get("therapeuticAreas") or []
        ds = {d["id"]: d["score"] for d in row.get("datasourceScores", [])}
        batch.append(
            {
                "mondo_id": mondo_id,
                "name": disease.get("name", ""),
                "therapeutic_area": areas[0].get("name", "other") if areas else "other",
                "score": row.get("score", 0),
                "genetics_score": ds.get("eva", ds.get("gwas_catalog", 0)),
                "expression_score": ds.get("expression_atlas", 0),
                "literature_score": ds.get("europepmc", ds.get("uniprot_literature", 0)),
            }
        )
    cypher = """
    UNWIND $rows AS row
    MERGE (d:Disease {mondo_id: row.mondo_id})
    ON CREATE SET
        d.name = row.name,
        d.therapeutic_area = row.therapeutic_area,
        d.ot_score = row.score,
        d.source = 'OpenTargets'
    ON MATCH SET
        d.ot_score = CASE WHEN row.score > coalesce(d.ot_score, 0) THEN row.score ELSE d.ot_score END,
        d.therapeutic_area = COALESCE(d.therapeutic_area, row.therapeutic_area)
    WITH d, row
    MATCH (g:Gene {symbol: $symbol})
    MERGE (g)-[r:ASSOCIATED_WITH {source: 'OpenTargets'}]->(d)
    ON CREATE SET
        r.score = row.score,
        r.genetics_score = row.genetics_score,
        r.expression_score = row.expression_score,
        r.literature_score = row.literature_score
    ON MATCH SET r.score = row.score
    """
    chunk = 250
    for i in range(0, len(batch), chunk):
        session.run(cypher, rows=batch[i : i + chunk], symbol=symbol)
    return len(batch), len(batch)


def merge_gene_protein(session, target: dict[str, Any]) -> None:
    session.run(
        """
        MERGE (g:Gene {symbol: $symbol})
        ON CREATE SET
            g.ensembl_id = $ensembl_id,
            g.entrez_id = $entrez_id,
            g.name = $name,
            g.source = 'targets.yaml'
        ON MATCH SET
            g.ensembl_id = coalesce(g.ensembl_id, $ensembl_id),
            g.entrez_id = coalesce(g.entrez_id, $entrez_id),
            g.name = coalesce(g.name, $name)
        MERGE (p:Protein {symbol: $symbol})
        ON CREATE SET
            p.uniprot_id = $uniprot_id,
            p.source = 'targets.yaml'
        ON MATCH SET
            p.uniprot_id = coalesce(p.uniprot_id, $uniprot_id)
        MERGE (g)-[:ENCODES]->(p)
        """,
        symbol=target["symbol"],
        ensembl_id=target.get("ensembl_id"),
        entrez_id=str(target.get("entrez_id", "")),
        name=target.get("name", target["symbol"]),
        uniprot_id=target.get("uniprot_id"),
    )


def assert_target_slice_helpers() -> None:
    t = get_target("FOLH1")
    assert t["ensembl_id"] == "ENSG00000086205"
    assert get_target("GRPR")["ensembl_id"] == "ENSG00000126010"


if __name__ == "__main__":
    assert_target_slice_helpers()
    print("target_slice_ok")
