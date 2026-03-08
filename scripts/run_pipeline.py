"""
Master pipeline runner for CD46 Precision Medicine Platform.

Usage:
    python scripts/run_pipeline.py --mode download
    python scripts/run_pipeline.py --mode analyze
    python scripts/run_pipeline.py --mode kg
    python scripts/run_pipeline.py --mode agent
    python scripts/run_pipeline.py --mode report
    python scripts/run_pipeline.py --mode full
"""
from __future__ import annotations

import argparse
import logging
import sys
import time
from pathlib import Path

# Ensure project root is on sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("pipeline.log", encoding="utf-8"),
    ],
)
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Phase runners
# ---------------------------------------------------------------------------

def run_download() -> None:
    """Phase 1: Download all raw datasets."""
    logger.info("=" * 60)
    logger.info("PHASE 1 — DATA DOWNLOAD")
    logger.info("=" * 60)

    from src.data_ingestion.download_tcga import download_all as download_tcga_cd46
    from src.data_ingestion.fetch_hpa import fetch_hpa_cd46
    from src.data_ingestion.fetch_clinicaltrials import fetch_cd46_trials
    from src.data_ingestion.fetch_chembl import fetch_cd46_drugs as fetch_cd46_chembl
    from src.data_ingestion.fetch_open_targets import fetch_open_targets as fetch_cd46_open_targets
    from src.data_ingestion.fetch_uniprot import fetch_cd46_uniprot as fetch_uniprot_cd46
    from src.data_ingestion.fetch_cbioportal import fetch_mcrpc_data as fetch_cbioportal_mcrpc
    from src.data_ingestion.fetch_depmap import check_depmap_files

    steps = [
        ("TCGA/Xena bulk download", download_tcga_cd46),
        ("HPA protein expression", fetch_hpa_cd46),
        ("ClinicalTrials.gov", fetch_cd46_trials),
        ("ChEMBL bioactivity", fetch_cd46_chembl),
        ("Open Targets", fetch_cd46_open_targets),
        ("UniProt P15529", fetch_uniprot_cd46),
        ("cBioPortal mCRPC", fetch_cbioportal_mcrpc),
        ("DepMap file check", check_depmap_files),
    ]

    for name, fn in steps:
        logger.info("Downloading: %s", name)
        t0 = time.time()
        try:
            fn()
            logger.info("  ✓ %s done (%.1fs)", name, time.time() - t0)
        except Exception as e:
            logger.error("  ✗ %s failed: %s", name, e)

    logger.info("Phase 1 complete — raw data in data/raw/")


def run_analyze() -> None:
    """Phase 2: Preprocess raw data + run analysis."""
    logger.info("=" * 60)
    logger.info("PHASE 2 — PREPROCESSING + ANALYSIS")
    logger.info("=" * 60)

    # Preprocessing
    logger.info("--- Preprocessing ---")

    from src.preprocessing.extract_cd46 import run_extraction
    from src.preprocessing.process_hpa import process_hpa_data as process_hpa
    from src.preprocessing.process_depmap import extract_cd46_depmap as process_depmap
    from src.preprocessing.process_cbioportal import process_cbioportal
    from src.preprocessing.harmonize_datasets import harmonize_cancer_df

    preprocessing_steps = [
        ("Extract CD46 from TCGA matrix", run_extraction),
        ("Process HPA protein data", process_hpa),
        ("Process DepMap essentiality", process_depmap),
        ("Process cBioPortal mCRPC", process_cbioportal),
    ]

    for name, fn in preprocessing_steps:
        logger.info("Preprocessing: %s", name)
        t0 = time.time()
        try:
            fn()
            logger.info("  ✓ %s done (%.1fs)", name, time.time() - t0)
        except Exception as e:
            logger.error("  ✗ %s failed: %s", name, e)

    # Analysis
    logger.info("--- Analysis ---")

    from src.analysis.pan_cancer_cd46 import run_pan_cancer_analysis
    from src.analysis.survival_analysis import run_all_cancers as run_all_survival_analysis
    from src.analysis.ac225_analysis import run_ac225_analysis as run_ac225_eligibility
    from src.analysis.combination_analysis import run_combination_analysis

    analysis_steps = [
        ("Pan-cancer CD46 analysis + priority score", run_pan_cancer_analysis),
        ("Survival analysis (KM + Cox PH)", run_all_survival_analysis),
        ("225Ac eligibility analysis", run_ac225_eligibility),
        ("Combination biomarker correlations", run_combination_analysis),
    ]

    # Load expression data for analyses that need it
    import pandas as _pd
    try:
        _expr_df = _pd.read_csv("data/processed/cd46_expression.csv")
    except Exception:
        _expr_df = _pd.DataFrame()

    for name, fn in analysis_steps:
        logger.info("Analyzing: %s", name)
        t0 = time.time()
        try:
            import inspect as _inspect
            sig = _inspect.signature(fn)
            if "expr_df" in sig.parameters:
                fn(_expr_df)
            else:
                fn()
            logger.info("  ✓ %s done (%.1fs)", name, time.time() - t0)
        except Exception as e:
            logger.error("  ✗ %s failed: %s", name, e)

    # Visualizations
    logger.info("--- Generating Figures ---")
    try:
        import pandas as pd
        from src.visualization.cd46_plots import (
            plot_pan_cancer_boxplot,
            plot_hpa_protein,
            plot_priority_heatmap,
        )

        expr_df = pd.read_csv("data/processed/cd46_expression.csv")
        hpa_df = pd.read_csv("data/processed/hpa_cd46_protein.csv")
        priority_df = pd.read_csv("data/processed/priority_score.csv")

        plot_pan_cancer_boxplot(expr_df)
        plot_hpa_protein(hpa_df)
        plot_priority_heatmap(priority_df)
        logger.info("  ✓ Figures saved to reports/figures/")
    except Exception as e:
        logger.error("  ✗ Figure generation failed: %s", e)

    logger.info("Phase 2 complete — results in data/processed/ and reports/figures/")


def run_kg() -> None:
    """Phase 3: Build Knowledge Graph in AuraDB."""
    logger.info("=" * 60)
    logger.info("PHASE 3 — KNOWLEDGE GRAPH BUILD")
    logger.info("=" * 60)

    from src.knowledge_graph.build_graph import build_full_graph
    from src.knowledge_graph.kg_to_csv import export_kg_to_csv

    logger.info("Building AuraDB knowledge graph...")
    t0 = time.time()

    try:
        import os
        from neo4j import GraphDatabase

        uri = os.getenv("NEO4J_URI")
        user = os.getenv("NEO4J_USERNAME", "neo4j")
        password = os.getenv("NEO4J_PASSWORD")

        if not uri or not password:
            logger.error("NEO4J_URI and NEO4J_PASSWORD must be set in .env file")
            logger.error("Copy .env.template to .env and fill in your AuraDB credentials")
            return

        driver = GraphDatabase.driver(uri, auth=(user, password))
        results = build_full_graph()
        logger.info("  KG build complete: %s", results)
        logger.info("  Time: %.1fs", time.time() - t0)

        # Export to CSV
        logger.info("Exporting KG to CSV...")
        from pathlib import Path
        export_results = export_kg_to_csv(driver, Path("data/processed/kg_ready"))
        total_nodes = sum(v["rows"] for v in export_results["nodes"].values())
        total_edges = sum(v["rows"] for v in export_results["edges"].values())
        logger.info("  Exported %d node rows + %d edge rows to data/processed/kg_ready/", total_nodes, total_edges)

        driver.close()
    except Exception as e:
        logger.error("KG build failed: %s", e)
        logger.error("Check AuraDB credentials and connection in .env")

    logger.info("Phase 3 complete")


def run_agent_demo() -> None:
    """Phase 4: Test agent with preset questions."""
    logger.info("=" * 60)
    logger.info("PHASE 4 — AGENT DEMO")
    logger.info("=" * 60)

    from src.agent.orchestrator import CD46Agent, PRESET_QUESTIONS

    try:
        agent = CD46Agent(provider="auto")
        logger.info("Agent initialized successfully")

        for i, question in enumerate(PRESET_QUESTIONS[:3], 1):
            logger.info("\nQ%d: %s", i, question)
            answer = agent.ask(question)
            logger.info("A%d: %s...", i, answer[:200])

    except Exception as e:
        logger.error("Agent demo failed: %s", e)
        logger.error("Check OPENAI_API_KEY or GEMINI_API_KEY in .env")

    logger.info("Phase 4 complete")


def run_report() -> None:
    """Phase 5: Generate HTML/PDF report."""
    logger.info("=" * 60)
    logger.info("PHASE 5 — REPORT GENERATION")
    logger.info("=" * 60)

    try:
        from src.reporting.generate_report import generate_html_report
        generate_html_report()
        logger.info("  ✓ Report saved to reports/cd46_precision_medicine_report.html")
    except Exception as e:
        logger.error("Report generation failed: %s", e)

    logger.info("Phase 5 complete")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="CD46 Precision Medicine Platform — Pipeline Runner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Modes:
  download  — Download all raw datasets (TCGA, HPA, cBioPortal, etc.)
  analyze   — Preprocess + run statistics + generate figures
  kg        — Build AuraDB knowledge graph (requires NEO4J credentials in .env)
  agent     — Run AI agent demo with preset questions (requires LLM API key)
  report    — Generate HTML report
  full      — Run all phases sequentially

Examples:
  python scripts/run_pipeline.py --mode download
  python scripts/run_pipeline.py --mode full
  python scripts/run_pipeline.py --mode kg
        """,
    )
    parser.add_argument(
        "--mode",
        choices=["download", "analyze", "kg", "agent", "report", "full"],
        required=True,
        help="Pipeline phase to run",
    )
    parser.add_argument(
        "--skip-download",
        action="store_true",
        help="Skip download phase when running full mode",
    )

    args = parser.parse_args()

    t_start = time.time()
    logger.info("CD46 Precision Medicine Platform — Pipeline starting")
    logger.info("Mode: %s", args.mode)

    if args.mode == "download":
        run_download()
    elif args.mode == "analyze":
        run_analyze()
    elif args.mode == "kg":
        run_kg()
    elif args.mode == "agent":
        run_agent_demo()
    elif args.mode == "report":
        run_report()
    elif args.mode == "full":
        if not args.skip_download:
            run_download()
        run_analyze()
        run_kg()
        run_agent_demo()
        run_report()

    elapsed = time.time() - t_start
    logger.info("Pipeline complete — total time: %.1fs (%.1f min)", elapsed, elapsed / 60)


if __name__ == "__main__":
    main()
