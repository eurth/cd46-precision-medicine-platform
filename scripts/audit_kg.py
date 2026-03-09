"""Quick AuraDB audit — prints node/relationship counts and samples."""
import os
from pathlib import Path
from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parent.parent / ".env")
from neo4j import GraphDatabase

uri  = os.environ["NEO4J_URI"]
auth = (os.environ["NEO4J_USERNAME"], os.environ["NEO4J_PASSWORD"])
driver = GraphDatabase.driver(uri, auth=auth)

with driver.session() as s:
    print("=== NODE COUNTS BY LABEL ===")
    labels = [r["label"] for r in s.run("CALL db.labels() YIELD label RETURN label ORDER BY label")]
    total_nodes = 0
    for lbl in labels:
        cnt = s.run(f"MATCH (n:`{lbl}`) RETURN count(n) AS c").single()["c"]
        total_nodes += cnt
        print(f"  {lbl:30s}: {cnt:>6,}")
    print(f"  {'TOTAL':30s}: {total_nodes:>6,}")

    print("\n=== RELATIONSHIP COUNTS BY TYPE ===")
    reltypes = [r["relationshipType"] for r in s.run("CALL db.relationshipTypes() YIELD relationshipType RETURN relationshipType ORDER BY relationshipType")]
    total_rels = 0
    for rt in reltypes:
        cnt = s.run(f"MATCH ()-[r:`{rt}`]->() RETURN count(r) AS c").single()["c"]
        total_rels += cnt
        print(f"  {rt:30s}: {cnt:>6,}")
    print(f"  {'TOTAL':30s}: {total_rels:>6,}")

    print("\n=== SAMPLE NODES PER LABEL (first 2) ===")
    for lbl in labels:
        rows = s.run(f"MATCH (n:`{lbl}`) RETURN n LIMIT 2").data()
        for row in rows:
            props = dict(row["n"].items())
            preview = {k: v for k, v in list(props.items())[:4]}
            print(f"  [{lbl}] {preview}")

driver.close()
print("\nAudit complete.")
