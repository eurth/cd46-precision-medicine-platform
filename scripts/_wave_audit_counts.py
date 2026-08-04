"""ponytail: one-off Aura count helper for expansion waves (ASCII-safe)."""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from neo4j import GraphDatabase

_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(_ROOT / ".env")

GENES = ["CD46", "FOLH1", "FAP", "SSTR2", "GRPR"]


def main() -> None:
    uri = os.getenv("NEO4J_URI")
    user = os.getenv("NEO4J_USERNAME", "neo4j")
    pwd = os.getenv("NEO4J_PASSWORD")
    d = GraphDatabase.driver(uri, auth=(user, pwd))
    d.verify_connectivity()
    out: dict = {}
    with d.session() as s:
        out["nodes"] = s.run("MATCH (n) RETURN count(n) AS c").single()["c"]
        out["rels"] = s.run("MATCH ()-[rel]->() RETURN count(rel) AS c").single()["c"]
        out["ot_by_gene"] = [
            dict(r)
            for r in s.run(
                "MATCH (g:Gene)-[r:ASSOCIATED_WITH]->() "
                "WHERE g.symbol IN $genes "
                "RETURN g.symbol AS gene, count(r) AS n ORDER BY gene",
                genes=GENES,
            )
        ]
        out["trials_by_gene"] = [
            dict(r)
            for r in s.run(
                "MATCH (t:ClinicalTrial)-[:TARGETS_GENE]->(g:Gene) "
                "WHERE g.symbol IN $genes "
                "RETURN g.symbol AS gene, count(t) AS n ORDER BY gene",
                genes=GENES,
            )
        ]
        out["interacts_by_gene"] = [
            dict(r)
            for r in s.run(
                "MATCH (g:Gene)-[r:INTERACTS_WITH]-() "
                "WHERE g.symbol IN $genes "
                "RETURN g.symbol AS gene, count(DISTINCT r) AS n ORDER BY gene",
                genes=GENES,
            )
        ]
        # ponytail: per-label MATCH avoids deprecated CALL {} scope warning
        labs = [row["label"] for row in s.run("CALL db.labels() YIELD label RETURN label")]
        out["labels"] = {
            lab: s.run(f"MATCH (n:`{lab}`) RETURN count(n) AS c").single()["c"]
            for lab in labs
        }
    d.close()
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
    sys.exit(0)
