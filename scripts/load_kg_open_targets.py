"""Load Open Targets CD46 disease associations into AuraDB.

Input:  data/raw/apis/open_targets_cd46.json  (772 associations already on disk)
Loads:
  - Disease nodes (top 50 by score, MERGE on mondo_id to avoid duplicates)
  - ASSOCIATED_WITH relationships: Gene(CD46) -> Disease with score + datasource scores
Expected gain: ~+25 new Disease nodes, +772 ASSOCIATED_WITH relationships

Run:
    python scripts/load_kg_open_targets.py
Then verify:
    python scripts/audit_kg.py
"""
import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

sys.path.insert(0, str(Path(__file__).resolve().parent))

from neo4j import GraphDatabase


def get_driver():
    uri = os.getenv("NEO4J_URI")
    user = os.getenv("NEO4J_USERNAME", "neo4j")
    password = os.getenv("NEO4J_PASSWORD")
    if not uri or not password:
        raise RuntimeError("NEO4J_URI and NEO4J_PASSWORD must be set in .env")
    driver = GraphDatabase.driver(uri, auth=(user, password))
    driver.verify_connectivity()
    return driver


def load_open_targets(driver, data_path: Path):
    with open(data_path, encoding="utf-8") as f:
        raw = json.load(f)

    rows = (
        raw.get("data", {})
        .get("target", {})
        .get("associatedDiseases", {})
        .get("rows", [])
    )
    if not rows:
        print("ERROR: No rows found in open_targets_cd46.json")
        return

    print(f"Found {len(rows)} disease associations. Loading top 50 by score...")

    # Sort by score descending
    rows_sorted = sorted(rows, key=lambda r: r.get("score", 0), reverse=True)
    top_rows = rows_sorted[:50]

    disease_merge_cypher = """
        MERGE (d:Disease {mondo_id: $mondo_id})
        ON CREATE SET
            d.name = $name,
            d.therapeutic_area = $therapeutic_area,
            d.ot_score = $score,
            d.source = 'OpenTargets'
        ON MATCH SET
            d.ot_score = $score,
            d.therapeutic_area = COALESCE(d.therapeutic_area, $therapeutic_area)
        RETURN d.mondo_id AS id
    """

    assoc_merge_cypher = """
        MATCH (g:Gene {symbol: 'CD46'})
        MATCH (d:Disease {mondo_id: $mondo_id})
        MERGE (g)-[r:ASSOCIATED_WITH {source: 'OpenTargets'}]->(d)
        ON CREATE SET
            r.score = $score,
            r.genetics_score = $genetics_score,
            r.expression_score = $expression_score,
            r.literature_score = $literature_score
        ON MATCH SET
            r.score = $score
        RETURN type(r)
    """

    disease_count = 0
    rel_count = 0

    with driver.session() as session:
        for row in top_rows:
            disease = row.get("disease", {})
            mondo_id = disease.get("id", "")
            name = disease.get("name", "")
            therapeutic_areas = disease.get("therapeuticAreas", [])
            therapeutic_area = therapeutic_areas[0].get("name", "other") if therapeutic_areas else "other"
            score = row.get("score", 0)

            # Extract datasource scores
            ds_scores = {ds["id"]: ds["score"] for ds in row.get("datasourceScores", [])}

            result = session.run(
                disease_merge_cypher,
                mondo_id=mondo_id,
                name=name,
                therapeutic_area=therapeutic_area,
                score=score,
            )
            disease_count += 1

            session.run(
                assoc_merge_cypher,
                mondo_id=mondo_id,
                score=score,
                genetics_score=ds_scores.get("eva", ds_scores.get("gwas_catalog", 0)),
                expression_score=ds_scores.get("expression_atlas", 0),
                literature_score=ds_scores.get("europepmc", ds_scores.get("uniprot_literature", 0)),
            )
            rel_count += 1

    # Now load ALL 772 associations as relationships (some diseases already exist)
    print(f"  Loaded top {disease_count} disease nodes. Now creating ASSOCIATED_WITH for all {len(rows_sorted)} associations...")

    with driver.session() as session:
        for row in rows_sorted:
            disease = row.get("disease", {})
            mondo_id = disease.get("id", "")
            name = disease.get("name", "")
            therapeutic_areas = disease.get("therapeuticAreas", [])
            therapeutic_area = therapeutic_areas[0].get("name", "other") if therapeutic_areas else "other"
            score = row.get("score", 0)
            ds_scores = {ds["id"]: ds["score"] for ds in row.get("datasourceScores", [])}

            # MERGE disease node (may already exist from above)
            session.run(
                disease_merge_cypher,
                mondo_id=mondo_id,
                name=name,
                therapeutic_area=therapeutic_area,
                score=score,
            )

            # MERGE relationship
            result = session.run(
                assoc_merge_cypher,
                mondo_id=mondo_id,
                score=score,
                genetics_score=ds_scores.get("eva", ds_scores.get("gwas_catalog", 0)),
                expression_score=ds_scores.get("expression_atlas", 0),
                literature_score=ds_scores.get("europepmc", ds_scores.get("uniprot_literature", 0)),
            )
            rel_count += 1

    print(f"✅ Load complete. Processed {len(rows_sorted)} associations.")
    print(f"   Disease nodes upserted: {len(rows_sorted)}")
    print(f"   ASSOCIATED_WITH relationships upserted: {rel_count}")
    print("Run scripts/audit_kg.py to confirm counts in AuraDB.")


def main():
    data_path = Path(__file__).resolve().parents[1] / "data" / "raw" / "apis" / "open_targets_cd46.json"
    if not data_path.exists():
        print(f"ERROR: {data_path} not found")
        sys.exit(1)

    driver = get_driver()
    try:
        load_open_targets(driver, data_path)
    finally:
        driver.close()


if __name__ == "__main__":
    main()
