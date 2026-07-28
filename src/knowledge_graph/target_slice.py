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


def fetch_open_targets(ensembl_id: str, *, size: int = 200) -> dict:
    query = (
        "query TargetDiseases($ensemblId: String!, $size: Int!) {"
        " target(ensemblId: $ensemblId) {"
        "  id approvedSymbol"
        "  associatedDiseases(page: {index: 0, size: $size}) {"
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
        {"query": query, "variables": {"ensemblId": ensembl_id, "size": size}}
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


def load_ot_associations(session, symbol: str, ot_payload: dict, *, top_n: int = 50) -> tuple[int, int]:
    rows = (
        ot_payload.get("data", {})
        .get("target", {})
        .get("associatedDiseases", {})
        .get("rows", [])
    )
    if not rows:
        return 0, 0
    rows_sorted = sorted(rows, key=lambda r: r.get("score", 0), reverse=True)
    disease_cypher = """
        MERGE (d:Disease {mondo_id: $mondo_id})
        ON CREATE SET
            d.name = $name,
            d.therapeutic_area = $therapeutic_area,
            d.ot_score = $score,
            d.source = 'OpenTargets'
        ON MATCH SET
            d.ot_score = CASE WHEN $score > coalesce(d.ot_score, 0) THEN $score ELSE d.ot_score END,
            d.therapeutic_area = COALESCE(d.therapeutic_area, $therapeutic_area)
    """
    assoc_cypher = """
        MATCH (g:Gene {symbol: $symbol})
        MATCH (d:Disease {mondo_id: $mondo_id})
        MERGE (g)-[r:ASSOCIATED_WITH {source: 'OpenTargets'}]->(d)
        ON CREATE SET
            r.score = $score,
            r.genetics_score = $genetics_score,
            r.expression_score = $expression_score,
            r.literature_score = $literature_score
        ON MATCH SET
            r.score = $score
    """
    # Upsert top disease nodes first, then all assoc edges in fetched page
    for row in rows_sorted[:top_n]:
        disease = row.get("disease", {})
        areas = disease.get("therapeuticAreas") or []
        session.run(
            disease_cypher,
            mondo_id=disease.get("id", ""),
            name=disease.get("name", ""),
            therapeutic_area=areas[0].get("name", "other") if areas else "other",
            score=row.get("score", 0),
        )
    rels = 0
    for row in rows_sorted:
        disease = row.get("disease", {})
        mondo_id = disease.get("id", "")
        if not mondo_id:
            continue
        areas = disease.get("therapeuticAreas") or []
        session.run(
            disease_cypher,
            mondo_id=mondo_id,
            name=disease.get("name", ""),
            therapeutic_area=areas[0].get("name", "other") if areas else "other",
            score=row.get("score", 0),
        )
        ds = {d["id"]: d["score"] for d in row.get("datasourceScores", [])}
        session.run(
            assoc_cypher,
            symbol=symbol,
            mondo_id=mondo_id,
            score=row.get("score", 0),
            genetics_score=ds.get("eva", ds.get("gwas_catalog", 0)),
            expression_score=ds.get("expression_atlas", 0),
            literature_score=ds.get("europepmc", ds.get("uniprot_literature", 0)),
        )
        rels += 1
    return min(top_n, len(rows_sorted)), rels


def assert_target_slice_helpers() -> None:
    t = get_target("FOLH1")
    assert t["ensembl_id"] == "ENSG00000086205"
    assert get_target("GRPR")["ensembl_id"] == "ENSG00000126010"


if __name__ == "__main__":
    assert_target_slice_helpers()
    print("target_slice_ok")
