"""Quick diagnostic: check Protein nodes and ProteinIsoform/ProteinVariant counts."""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1] / ".env")
from neo4j import GraphDatabase

driver = GraphDatabase.driver(
    os.environ["NEO4J_URI"], auth=(os.environ["NEO4J_USERNAME"], os.environ["NEO4J_PASSWORD"])
)

with driver.session() as s:
    print("=== Protein nodes ===")
    for rec in s.run("MATCH (p:Protein) RETURN p.symbol, p.uniprot_id"):
        print(dict(rec))

    print("\n=== ProteinIsoform count ===")
    print(s.run("MATCH (n:ProteinIsoform) RETURN count(n) AS cnt").single()["cnt"])

    print("\n=== ProteinVariant count ===")
    print(s.run("MATCH (n:ProteinVariant) RETURN count(n) AS cnt").single()["cnt"])

    print("\n=== HAS_ISOFORM / HAS_VARIANT rel counts ===")
    print("HAS_ISOFORM:", s.run("MATCH ()-[:HAS_ISOFORM]->() RETURN count(*) AS cnt").single()["cnt"])
    print("HAS_VARIANT:", s.run("MATCH ()-[:HAS_VARIANT]->() RETURN count(*) AS cnt").single()["cnt"])

driver.close()
