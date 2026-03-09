"""
Load Publications and ClinicalTrial nodes into AuraDB.

Run from project root:
    python scripts/load_kg_extras.py

Requires NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD in environment or .env.
"""
import logging
import os
import sys
from pathlib import Path

# Ensure project root on path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

from neo4j import GraphDatabase

logging.basicConfig(level=logging.INFO, format="%(levelname)s — %(message)s")
logger = logging.getLogger(__name__)

RAW_DIR = Path("data/raw")


def get_driver():
    uri = os.getenv("NEO4J_URI")
    user = os.getenv("NEO4J_USERNAME", "neo4j")
    password = os.getenv("NEO4J_PASSWORD")

    if not uri or not password:
        raise EnvironmentError(
            "NEO4J_URI and NEO4J_PASSWORD must be set in environment or .env file."
        )

    driver = GraphDatabase.driver(uri, auth=(user, password))
    driver.verify_connectivity()
    logger.info("Connected to AuraDB at %s", uri)
    return driver


def count_nodes(driver) -> dict:
    labels = ["Gene", "Protein", "Disease", "Drug", "Publication", "ClinicalTrial"]
    counts = {}
    with driver.session() as session:
        for label in labels:
            result = session.run(f"MATCH (n:{label}) RETURN count(n) AS c")
            counts[label] = result.single()["c"]
    return counts


def main():
    driver = get_driver()

    logger.info("\n=== BEFORE LOAD ===")
    before = count_nodes(driver)
    for label, count in before.items():
        logger.info("  %s: %d", label, count)

    # --- Load Publications ---
    logger.info("\n=== Loading Publication Nodes ===")
    try:
        from src.knowledge_graph.node_builders.build_publication_nodes import (
            build_publication_nodes,
        )
        pub_result = build_publication_nodes(driver, RAW_DIR)
        logger.info("Publications result: %s", pub_result)
    except Exception as e:
        logger.error("Publication load failed: %s", e)

    # --- Load ClinicalTrial Nodes ---
    logger.info("\n=== Loading ClinicalTrial Nodes ===")
    try:
        from src.knowledge_graph.node_builders.build_trial_nodes import (
            build_trial_nodes,
        )
        trial_result = build_trial_nodes(driver, RAW_DIR)
        logger.info("Trials result: %s", trial_result)
    except Exception as e:
        logger.error("Trial load failed: %s", e)

    logger.info("\n=== AFTER LOAD ===")
    after = count_nodes(driver)
    for label, count in after.items():
        delta = count - before.get(label, 0)
        delta_str = f" (+{delta})" if delta > 0 else ""
        logger.info("  %s: %d%s", label, count, delta_str)

    driver.close()
    logger.info("\n✅ Done — AuraDB updated.")


if __name__ == "__main__":
    main()
