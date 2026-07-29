"""Phase 0: Aura Free capacity check (no secrets printed)."""
from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv

load_dotenv(ROOT / ".env")


def main() -> int:
    from neo4j import GraphDatabase

    uri = os.getenv("NEO4J_URI")
    user = os.getenv("NEO4J_USERNAME", "neo4j")
    pw = os.getenv("NEO4J_PASSWORD")
    if not uri or not pw:
        print("FAIL: NEO4J credentials missing in .env")
        return 1

    host = uri.split("://")[-1].split("/")[0]
    driver = GraphDatabase.driver(uri, auth=(user, pw))
    driver.verify_connectivity()
    with driver.session() as s:
        nodes = s.run("MATCH (n) RETURN count(n) AS c").single()["c"]
        rels = s.run("MATCH ()-[r]->() RETURN count(r) AS c").single()["c"]
        labels = s.run(
            "CALL db.labels() YIELD label RETURN collect(label) AS labels"
        ).single()["labels"]
        keepalive = s.run(
            "MATCH (k:_KeepAlive {id:'oncobridge'}) RETURN k.last_ping AS p"
        ).single()
    driver.close()

    free_nodes, free_rels = 200_000, 400_000
    print(f"aura_host={host}")
    print(f"nodes={nodes} free_cap={free_nodes} used_pct={100*nodes/free_nodes:.2f}")
    print(f"rels={rels} free_cap={free_rels} used_pct={100*rels/free_rels:.2f}")
    print(f"headroom_nodes={free_nodes - nodes}")
    print(f"headroom_rels={free_rels - rels}")
    print(f"labels={sorted(labels)}")
    print(f"keepalive_last_ping={keepalive['p'] if keepalive else None}")
    # 5-target estimate at ~4k nodes each
    est5 = nodes * 5
    print(f"est_5x_current_nodes={est5} fits_free={est5 < 150_000}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
