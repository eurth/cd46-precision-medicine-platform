#!/usr/bin/env python3
"""Aura Free keepalive — one WRITE so Free tier does not pause after 72h idle.

Aura Free counts only write queries as activity (reads do not). Run daily via
Coolify Scheduled Task: ``python scripts/aura_keepalive.py``.

ponytail: single MERGE node; not a backup. Rebuild from processed CSVs if Free dies.
"""
from __future__ import annotations

import os
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

try:
    from dotenv import load_dotenv

    load_dotenv(ROOT / ".env")
except ImportError:
    pass

CYPHER = """
MERGE (k:_KeepAlive {id: 'oncobridge'})
SET k.last_ping = datetime(), k.source = 'coolify-cron'
RETURN k.last_ping AS last_ping
"""

LOG_PATHS = (
    Path("/app/data/logs/aura_keepalive.log"),
    ROOT / "data" / "logs" / "aura_keepalive.log",
)


def _append_log(line: str) -> None:
    for path in LOG_PATHS:
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("a", encoding="utf-8") as f:
                f.write(line + "\n")
            return
        except OSError:
            continue


def main() -> int:
    uri = (os.getenv("NEO4J_URI") or "").strip()
    user = (os.getenv("NEO4J_USERNAME") or "neo4j").strip()
    pw = (os.getenv("NEO4J_PASSWORD") or "").strip()
    if not uri or not pw:
        print("FAIL: NEO4J_URI / NEO4J_PASSWORD missing", file=sys.stderr)
        return 1

    host = uri.split("://")[-1].split("/")[0]
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    try:
        from neo4j import GraphDatabase

        driver = GraphDatabase.driver(uri, auth=(user, pw))
        driver.verify_connectivity()
        with driver.session() as session:
            row = session.run(CYPHER).single()
            last_ping = row["last_ping"] if row else None
        driver.close()
    except Exception as exc:
        msg = f"{ts} FAIL host={host} err={type(exc).__name__}: {exc}"
        print(msg, file=sys.stderr)
        _append_log(msg)
        return 1

    msg = f"{ts} OK host={host} last_ping={last_ping}"
    print(msg)
    _append_log(msg)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
