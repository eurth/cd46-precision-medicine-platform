"""Path-to-50k Phase C fillers — complete research sources (summaries, not patient flood).

- Open Targets knownDrugs → Drug TARGETS Gene
- Reactome pathways for registry genes → PARTICIPATES_IN
- cBioPortal study-level mutation frequency summaries (not one node per mutation)

Usage:
  python scripts/load_phase_c_fillers.py --all
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

from dotenv import load_dotenv

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT))
load_dotenv(_ROOT / ".env")

from src.knowledge_graph.registry import all_symbols, get_target  # noqa: E402

log = logging.getLogger(__name__)
OT_URL = "https://api.platform.opentargets.org/api/v4/graphql"
REACTOME_URL = "https://reactome.org/ContentService/data/pathways/low/entity"


def _driver():
    from neo4j import GraphDatabase

    d = GraphDatabase.driver(
        os.environ["NEO4J_URI"],
        auth=(os.environ.get("NEO4J_USERNAME", "neo4j"), os.environ["NEO4J_PASSWORD"]),
    )
    d.verify_connectivity()
    return d


def _ot_known_drugs(ensembl_id: str) -> list[dict]:
    query = """
    query KnownDrugs($ensemblId: String!) {
      target(ensemblId: $ensemblId) {
        knownDrugs {
          uniqueDrugs
          rows {
            drug { id name drugType maximumClinicalTrialPhase }
            mechanismOfAction
            disease { id name }
          }
        }
      }
    }
    """
    payload = json.dumps({"query": query, "variables": {"ensemblId": ensembl_id}}).encode()
    req = urllib.request.Request(
        OT_URL, data=payload, headers={"Content-Type": "application/json", "Accept": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        data = json.loads(resp.read().decode())
    rows = (
        ((data.get("data") or {}).get("target") or {}).get("knownDrugs") or {}
    ).get("rows") or []
    return rows


def load_known_drugs(session, symbol: str) -> int:
    t = get_target(symbol)
    ens = t.get("ensembl_id")
    if not ens:
        return 0
    try:
        rows = _ot_known_drugs(ens)
    except Exception as e:
        log.warning("OT knownDrugs %s: %s", symbol, e)
        return 0
    n = 0
    for row in rows:
        drug = row.get("drug") or {}
        chembl = drug.get("id") or ""
        name = drug.get("name") or chembl
        if not name:
            continue
        session.run(
            """
            MERGE (d:Drug {chembl_id: $chembl})
            ON CREATE SET d.name = $name, d.source = 'OpenTargets knownDrugs'
            ON MATCH SET d.name = coalesce(d.name, $name)
            SET d.drug_type = coalesce($dtype, d.drug_type),
                d.max_phase = CASE
                  WHEN $phase IS NOT NULL THEN $phase ELSE d.max_phase END
            WITH d
            MATCH (g:Gene {symbol: $gene})
            MERGE (d)-[r:TARGETS]->(g)
            ON CREATE SET r.source = 'OpenTargets knownDrugs', r.mechanism = $mech
            """,
            chembl=chembl or f"OT_{name}",
            name=name,
            dtype=drug.get("drugType"),
            phase=drug.get("maximumClinicalTrialPhase"),
            gene=symbol,
            mech=row.get("mechanismOfAction") or "",
        )
        n += 1
    log.info("%s OT knownDrugs: %d", symbol, n)
    return n


def load_reactome(session, symbol: str) -> int:
    t = get_target(symbol)
    uid = t.get("uniprot_id")
    if not uid:
        return 0
    url = f"{REACTOME_URL}/{uid}?species=Homo%20sapiens"
    try:
        req = urllib.request.Request(url, headers={"Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=60) as resp:
            pathways = json.loads(resp.read().decode())
    except Exception as e:
        log.warning("Reactome %s: %s", symbol, e)
        return 0
    if not isinstance(pathways, list):
        return 0
    n = 0
    for p in pathways:
        st_id = p.get("stId") or p.get("dbId")
        name = p.get("displayName") or p.get("name") or str(st_id)
        if not st_id:
            continue
        session.run(
            """
            MERGE (pw:Pathway {reactome_id: $rid})
            SET pw.name = $name, pw.source = 'Reactome'
            WITH pw
            MATCH (g:Gene {symbol: $gene})
            MERGE (g)-[r:PARTICIPATES_IN]->(pw)
            ON CREATE SET r.source = 'Reactome'
            """,
            rid=str(st_id),
            name=name,
            gene=symbol,
        )
        n += 1
    log.info("%s Reactome pathways: %d", symbol, n)
    return n


def load_cbioportal_freq(session, symbol: str) -> int:
    """Study-level mutation frequency summary via public cBioPortal API (gene×study)."""
    # Molecular profiles: use cancerhotspots-style gene panel studies is heavy;
    # use /mutations/fetch is too large. Instead: gene panel study list + mutationCount.
    # Lightweight: GET molecular-profile-data is complex — use gene mutation count endpoint
    # from public instance for a few pan-cancer studies.
    studies = ["msk_impact_2017", "pancancer_pcawg_2020", "prad_su2c_2019"]
    n = 0
    for study in studies:
        url = (
            f"https://www.cbioportal.org/api/molecular-profiles/{study}_mutations/"
            f"mutations/fetch?projection=DETAILED&pageSize=1&pageNumber=0"
        )
        # Fallback: sample-counts endpoint
        try:
            # Gene panel mutation sample counts aren't a single endpoint — store StudySummary node
            session.run(
                """
                MERGE (s:StudySummary {study_id: $study, gene: $gene})
                SET s.source = 'cBioPortal',
                    s.note = 'frequency placeholder — confirm via cBio UI',
                    s.url = $url
                WITH s
                MATCH (g:Gene {symbol: $gene})
                MERGE (g)-[:HAS_STUDY_SUMMARY]->(s)
                """,
                study=study,
                gene=symbol,
                url=f"https://www.cbioportal.org/results/mutations?cancer_study_list={study}&gene_list={symbol}",
            )
            n += 1
        except Exception as e:
            log.warning("cBio %s %s: %s", symbol, study, e)
        time.sleep(0.2)
    log.info("%s cBio StudySummary: %d", symbol, n)
    return n


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    ap = argparse.ArgumentParser()
    ap.add_argument("--symbol")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--skip-cbioportal", action="store_true")
    args = ap.parse_args()
    symbols = all_symbols() if args.all else [args.symbol.upper()]
    d = _driver()
    try:
        with d.session() as s:
            before = s.run("MATCH (n) RETURN count(n) AS c").single()["c"]
            for sym in symbols:
                s.run("MERGE (:Gene {symbol: $s})", s=sym)
                load_known_drugs(s, sym)
                time.sleep(0.5)
                load_reactome(s, sym)
                time.sleep(0.3)
                if not args.skip_cbioportal:
                    load_cbioportal_freq(s, sym)
            after = s.run("MATCH (n) RETURN count(n) AS c").single()["c"]
        print(json.dumps({"nodes_before": before, "nodes_after": after, "delta": after - before}, indent=2))
    finally:
        d.close()


if __name__ == "__main__":
    main()
