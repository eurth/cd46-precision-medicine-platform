"""Fetch CD46 protein–protein interaction network from STRING DB and load into AuraDB.

STRING DB: https://string-db.org  (CC BY 4.0, no account required)
Parameters used:
  - Seed: 9606.ENSP00000313875 (CD46, Homo sapiens)
  - required_score ≥ 700  (high confidence; STRING scale 0-1000 → stored as 0-1)
  - limit = 50 interactions per seed (top-confidence neighborhood)
  - Expand to 1-hop neighbours then pull their highest-confidence partners

Nodes created:
  (:Gene) — one per unique interaction partner (symbol, string_id, annotation)
  NOTE: CD46 (:Gene) already exists in the KG; MERGE on symbol is idempotent.

Relationships created:
  (:Gene)-[:INTERACTS_WITH {score, escore, tscore, source}]->(:Gene)

Run:
    python scripts/load_kg_string.py
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

# ── Config ────────────────────────────────────────────────────────────────────
STRING_API      = "https://string-db.org/api/json"
CALLER          = "cd46_platform"
TAXON           = 9606          # Homo sapiens
SEED_STRING_ID  = "9606.ENSP00000313875"   # CD46
MIN_SCORE       = 0.70          # high-confidence (STRING stores 0-1 equiv.)
EDGE_LIMIT      = 50            # top interactions per query
RAW_OUT         = Path("data/raw/apis/string_cd46.json")
# ──────────────────────────────────────────────────────────────────────────────


def get_driver():
    uri      = os.getenv("NEO4J_URI")
    user     = os.getenv("NEO4J_USERNAME", "neo4j")
    password = os.getenv("NEO4J_PASSWORD")
    if not uri or not password:
        raise RuntimeError("NEO4J_URI and NEO4J_PASSWORD must be set in .env")
    driver = GraphDatabase.driver(uri, auth=(user, password))
    driver.verify_connectivity()
    return driver


def string_get(endpoint: str, params: dict) -> list:
    params = {**params, "caller_identity": CALLER}
    qs  = urllib.parse.urlencode(params)
    url = f"{STRING_API}/{endpoint}?{qs}"
    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def fetch_interactions(string_id: str, limit: int = EDGE_LIMIT) -> list:
    """Return interaction edges for a given STRING network id."""
    return string_get("network", {
        "identifiers":    string_id,
        "species":        TAXON,
        "required_score": int(MIN_SCORE * 1000),
        "limit":          limit,
    })


def fetch_partner_annotations(string_ids: list[str]) -> dict:
    """Return {stringId: {preferredName, annotation}} for a list of IDs."""
    if not string_ids:
        return {}
    # STRING allows multiple identifiers joined by %0d
    ids_param = "%0d".join(string_ids)
    url = (f"{STRING_API}/get_string_ids?"
           f"identifiers={ids_param}&species={TAXON}&limit=1"
           f"&caller_identity={CALLER}")
    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            rows = json.loads(resp.read().decode("utf-8"))
        return {r["stringId"]: {"name": r.get("preferredName", ""),
                                 "annotation": r.get("annotation", "")}
                for r in rows}
    except Exception as e:
        print(f"  Warning: annotation fetch failed: {e}")
        return {}


# ── Cypher ────────────────────────────────────────────────────────────────────
GENE_MERGE_CYPHER = """
MERGE (g:Gene {symbol: $symbol})
ON CREATE SET
    g.string_id      = $string_id,
    g.annotation     = $annotation,
    g.source         = 'STRING DB CC BY 4.0',
    g.is_ppi_partner = true
ON MATCH SET
    g.string_id  = COALESCE(g.string_id, $string_id),
    g.annotation = COALESCE(g.annotation, $annotation)
RETURN g.symbol AS sym
"""

INTERACTS_CYPHER = """
MATCH (a:Gene {symbol: $sym_a})
MATCH (b:Gene {symbol: $sym_b})
MERGE (a)-[r:INTERACTS_WITH {source: 'STRING DB'}]->(b)
ON CREATE SET
    r.score  = $score,
    r.escore = $escore,
    r.tscore = $tscore,
    r.dscore = $dscore
RETURN type(r)
"""
# ──────────────────────────────────────────────────────────────────────────────


def load_into_kg(driver, edges: list, annotations: dict) -> tuple[int, int]:
    """Load Gene nodes + INTERACTS_WITH rels. Returns (genes_added, rels_added)."""
    # Collect all unique gene symbols from edges
    seen_symbols: dict[str, str] = {}  # symbol → string_id
    for e in edges:
        for sym_key, sid_key in [("preferredName_A", "stringId_A"),
                                  ("preferredName_B", "stringId_B")]:
            sym = e.get(sym_key, "")
            sid = e.get(sid_key, "")
            if sym and sym not in seen_symbols:
                seen_symbols[sym] = sid

    gene_count = rel_count = 0
    with driver.session() as session:
        # Upsert Gene nodes
        for sym, sid in seen_symbols.items():
            ann = annotations.get(sid, {}).get("annotation", "")[:500]
            session.run(GENE_MERGE_CYPHER,
                        symbol=sym, string_id=sid, annotation=ann)
            gene_count += 1

        # Upsert INTERACTS_WITH relationships
        for e in edges:
            sym_a = e.get("preferredName_A", "")
            sym_b = e.get("preferredName_B", "")
            if not sym_a or not sym_b:
                continue
            session.run(
                INTERACTS_CYPHER,
                sym_a=sym_a,
                sym_b=sym_b,
                score=round(e.get("score", 0), 4),
                escore=round(e.get("escore", 0), 4),
                tscore=round(e.get("tscore", 0), 4),
                dscore=round(e.get("dscore", 0), 4),
            )
            rel_count += 1

    return gene_count, rel_count


def main():
    print("=== STRING DB → KG Loader ===")
    print(f"Seed: CD46  ({SEED_STRING_ID})")
    print(f"Min score: {MIN_SCORE} (high confidence)  |  Max edges: {EDGE_LIMIT}\n")

    # ── 1. Fetch CD46's direct interaction neighbourhood ─────────────────────
    print("1. Fetching CD46 interaction network from STRING DB...")
    edges = fetch_interactions(SEED_STRING_ID, limit=EDGE_LIMIT)
    print(f"   Retrieved {len(edges)} edges")
    time.sleep(0.5)

    # ── 2. Collect all unique STRING IDs for annotation lookup ────────────────
    all_ids = set()
    for e in edges:
        all_ids.add(e.get("stringId_A", ""))
        all_ids.add(e.get("stringId_B", ""))
    all_ids.discard("")
    print(f"   Unique proteins in network: {len(all_ids)}")

    # ── 3. Fetch annotations (names, descriptions) ────────────────────────────
    print("2. Fetching protein annotations...")
    # STRING limit: batch up to 100 IDs per call
    all_ids_list = list(all_ids)
    annotations: dict = {}
    for i in range(0, len(all_ids_list), 100):
        batch = all_ids_list[i:i+100]
        batch_ann = fetch_partner_annotations(batch)
        annotations.update(batch_ann)
        time.sleep(0.3)
    print(f"   Got annotations for {len(annotations)} proteins")

    # ── 4. Save raw data ──────────────────────────────────────────────────────
    RAW_OUT.parent.mkdir(parents=True, exist_ok=True)
    payload = {"seed": SEED_STRING_ID, "min_score": MIN_SCORE,
               "edges": edges, "annotations": annotations}
    RAW_OUT.write_text(json.dumps(payload, indent=2))
    print(f"   Raw data saved → {RAW_OUT}  ({len(edges)} edges)")

    # ── 5. Load into AuraDB ───────────────────────────────────────────────────
    print("3. Loading into AuraDB...")
    driver = get_driver()
    try:
        genes, rels = load_into_kg(driver, edges, annotations)
        print(f"   ✅ {genes} Gene nodes upserted")
        print(f"   ✅ {rels} INTERACTS_WITH relationships upserted")
    finally:
        driver.close()

    print("\nRun scripts/audit_kg.py to confirm updated counts.")


if __name__ == "__main__":
    main()
