"""Load UniProt CD46 protein isoforms and natural variants into AuraDB.

Input:  data/raw/apis/uniprot_cd46.json  (already on disk)
Loads:
  - 14+ ProteinIsoform nodes  (MERGE on uniprot_isoform_id)
  - 13  ProteinVariant nodes  (MERGE on variant_id / position+original)
  - HAS_ISOFORM relationships: Protein(CD46) -> ProteinIsoform
  - HAS_VARIANT  relationships: Protein(CD46) -> ProteinVariant
Expected gain: ~+27 nodes, ~+27 relationships

Run:
    python scripts/load_kg_protein_details.py
Then verify:
    python scripts/audit_kg.py
"""
import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

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


def load_protein_details(driver, data_path: Path):
    with open(data_path, encoding="utf-8") as f:
        uni = json.load(f)

    comments = uni.get("comments", [])
    features = uni.get("features", [])

    # ── Isoforms ──────────────────────────────────────────────────────────────
    alt_products = next((c for c in comments if c.get("commentType") == "ALTERNATIVE PRODUCTS"), {})
    isoforms = alt_products.get("isoforms", [])
    isoform_note = alt_products.get("note", {}).get("texts", [{}])[0].get("value", "")

    print(f"Found {len(isoforms)} isoforms in UniProt JSON.")

    isoform_cypher = """
        MATCH (p:Protein {symbol: 'CD46'}) WITH p LIMIT 1
        MERGE (iso:ProteinIsoform {uniprot_isoform_id: $iso_id})
        ON CREATE SET
            iso.name = $name,
            iso.synonyms = $synonyms,
            iso.sequence_status = $status,
            iso.gene_symbol = 'CD46',
            iso.source = 'UniProt'
        MERGE (p)-[:HAS_ISOFORM]->(iso)
        RETURN iso.uniprot_isoform_id AS id
    """

    isoform_count = 0
    with driver.session() as session:
        for iso in isoforms:
            name = iso.get("name", {}).get("value", "?")
            synonyms = [s.get("value", "") for s in iso.get("synonyms", [])]
            iso_ids = iso.get("isoformIds", [])
            iso_id = iso_ids[0] if iso_ids else f"P15529-{name}"
            status = iso.get("isoformSequenceStatus", "Described")

            session.run(
                isoform_cypher,
                iso_id=iso_id,
                name=name,
                synonyms=", ".join(synonyms),
                status=status,
            )
            isoform_count += 1
            print(f"  Isoform {name}: {iso_id} ({', '.join(synonyms) or '-'})")

    print(f"✅ {isoform_count} ProteinIsoform nodes upserted.")

    # ── Natural Variants ───────────────────────────────────────────────────────
    nat_variants = [f for f in features if f.get("type") == "Natural variant"]
    print(f"Found {len(nat_variants)} natural variants in UniProt JSON.")

    variant_cypher = """
        MATCH (p:Protein {symbol: 'CD46'}) WITH p LIMIT 1
        MERGE (v:ProteinVariant {variant_id: $variant_id})
        ON CREATE SET
            v.position = $position,
            v.original_aa = $original,
            v.variant_aa = $variant,
            v.dbsnp_id = $dbsnp_id,
            v.disease_note = $disease_note,
            v.feature_id = $feature_id,
            v.gene_symbol = 'CD46',
            v.source = 'UniProt'
        MERGE (p)-[:HAS_VARIANT]->(v)
        RETURN v.variant_id AS id
    """

    variant_count = 0
    with driver.session() as session:
        for v in nat_variants:
            pos = v.get("location", {}).get("start", {}).get("value")
            alt_seq = v.get("alternativeSequence", {})
            original = alt_seq.get("originalSequence", "?")
            alts = alt_seq.get("alternativeSequences", ["?"])
            variant_aa = alts[0] if alts else "?"

            cross_refs = v.get("featureCrossReferences", [])
            dbsnp_id = next((r["id"] for r in cross_refs if r.get("database") == "dbSNP"), "")

            raw_desc = v.get("description", "")
            # Parse disease from description e.g. "in AHUS2; dbSNP:rs121909591"
            parts = [p.strip() for p in raw_desc.split(";")]
            disease_parts = [p.replace("in ", "").strip() for p in parts
                             if p.strip() and not p.strip().lower().startswith("dbsnp")]
            disease_note = "; ".join(disease_parts) if disease_parts else ""

            feature_id = v.get("featureId", f"VAR_{pos}_{original}{variant_aa}")
            variant_id = feature_id or f"P15529_VAR_{pos}_{original}_{variant_aa}"

            session.run(
                variant_cypher,
                variant_id=variant_id,
                position=pos,
                original=original,
                variant=variant_aa,
                dbsnp_id=dbsnp_id,
                disease_note=disease_note,
                feature_id=feature_id,
            )
            variant_count += 1
            print(f"  Variant {original}{pos}{variant_aa} ({dbsnp_id or 'no dbSNP'}) — {disease_note or '-'}")

    print(f"✅ {variant_count} ProteinVariant nodes upserted.")
    print(f"Total new node types: ProteinIsoform ({isoform_count}), ProteinVariant ({variant_count})")
    print("Run scripts/audit_kg.py to confirm counts in AuraDB.")


def main():
    data_path = Path(__file__).resolve().parents[1] / "data" / "raw" / "apis" / "uniprot_cd46.json"
    if not data_path.exists():
        print(f"ERROR: {data_path} not found")
        sys.exit(1)

    driver = get_driver()
    try:
        load_protein_details(driver, data_path)
    finally:
        driver.close()


if __name__ == "__main__":
    main()
