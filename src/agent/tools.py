"""LangChain-compatible tools for the CD46 AI agent."""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Optional

import pandas as pd

logger = logging.getLogger(__name__)

DATA_DIR = Path("data/processed")
RAW_DIR = Path("data/raw")


# ---------------------------------------------------------------------------
# Helper — safe CSV loader
# ---------------------------------------------------------------------------

def _load_csv(filename: str) -> Optional[pd.DataFrame]:
    path = DATA_DIR / filename
    if not path.exists():
        logger.warning("Tool data file not found: %s", path)
        return None
    return pd.read_csv(path)


# ---------------------------------------------------------------------------
# Tool 1: Query Knowledge Graph via Cypher
# ---------------------------------------------------------------------------

def query_kg(cypher: str, params: Optional[dict] = None) -> str:
    """
    Execute a read-only Cypher query against AuraDB and return results as JSON string.

    Args:
        cypher: Cypher query string (SELECT-only — no MERGE/CREATE/DELETE).
        params: Optional query parameters dict.

    Returns:
        JSON string with query results or error message.
    """
    import os
    from neo4j import GraphDatabase

    # Security: block write operations
    cypher_upper = cypher.strip().upper()
    forbidden = ["CREATE", "MERGE", "DELETE", "SET ", "REMOVE", "DROP"]
    if any(cypher_upper.startswith(kw) or f" {kw} " in cypher_upper for kw in forbidden):
        return json.dumps({"error": "Write operations are not permitted via agent query tool"})

    uri = os.getenv("NEO4J_URI")
    user = os.getenv("NEO4J_USERNAME", "neo4j")
    password = os.getenv("NEO4J_PASSWORD")

    if not uri or not password:
        return json.dumps({"error": "NEO4J_URI and NEO4J_PASSWORD must be set in environment"})

    try:
        driver = GraphDatabase.driver(uri, auth=(user, password))
        with driver.session() as session:
            result = session.run(cypher, **(params or {}))
            records = [dict(rec) for rec in result]
        driver.close()
        return json.dumps(records[:50], default=str, indent=2)  # cap at 50 rows
    except Exception as e:
        logger.error("KG query failed: %s", e)
        return json.dumps({"error": str(e)})


# ---------------------------------------------------------------------------
# Tool 2: Load processed CSV data
# ---------------------------------------------------------------------------

def load_csv_data(dataset: str, cancer_type: Optional[str] = None, top_n: int = 20) -> str:
    """
    Load a processed dataset CSV and return a summary or filtered subset.

    Args:
        dataset: One of: "expression", "priority", "survival", "eligibility",
                 "hpa", "depmap", "cbioportal", "combination".
        cancer_type: Optional TCGA cancer code to filter (e.g., "PRAD").
        top_n: Maximum rows to return.

    Returns:
        JSON string with data summary.
    """
    file_map = {
        "expression": "cd46_expression.csv",
        "by_cancer": "cd46_by_cancer.csv",
        "priority": "priority_score.csv",
        "survival": "cd46_survival_results.csv",
        "eligibility": "patient_groups.csv",
        "hpa": "hpa_cd46_protein.csv",
        "depmap": "depmap_cd46_essentiality.csv",
        "cbioportal": "cbioportal_mcrpc.csv",
        "combination": "cd46_combination_biomarkers.csv",
    }

    filename = file_map.get(dataset.lower())
    if not filename:
        available = list(file_map.keys())
        return json.dumps({"error": f"Unknown dataset '{dataset}'. Available: {available}"})

    df = _load_csv(filename)
    if df is None:
        return json.dumps(
            {"error": f"File not found: data/processed/{filename}. Run pipeline first."}
        )

    if cancer_type and "cancer_type" in df.columns:
        df = df[df["cancer_type"].str.upper() == cancer_type.upper()]

    return json.dumps(
        {
            "dataset": dataset,
            "cancer_type_filter": cancer_type,
            "total_rows": len(df),
            "columns": list(df.columns),
            "data": df.head(top_n).to_dict(orient="records"),
        },
        default=str,
        indent=2,
    )


# ---------------------------------------------------------------------------
# Tool 3: Get eligibility summary
# ---------------------------------------------------------------------------

def get_eligibility(cancer_type: str = "PRAD", threshold: str = "75th_pct") -> str:
    """
    Get 225Ac-CD46 patient eligibility statistics for a cancer type and threshold.

    Args:
        cancer_type: TCGA cancer code (e.g., "PRAD", "OV", "BLCA").
        threshold: One of: "median", "75th_pct", "log2_2.5", "log2_3.0".

    Returns:
        JSON string with eligibility stats.
    """
    df = _load_csv("patient_groups.csv")
    if df is None:
        # Return static fallback for PRAD
        if cancer_type.upper() == "PRAD":
            return json.dumps(
                {
                    "cancer_type": "PRAD",
                    "threshold": threshold,
                    "n_eligible": 219,
                    "n_total": 497,
                    "pct_eligible": 44.1,
                    "note": "Static estimate — run pipeline for computed values",
                }
            )
        return json.dumps({"error": "patient_groups.csv not found — run pipeline first"})

    mask = (df["cancer_type"].str.upper() == cancer_type.upper()) & (df["threshold_method"] == threshold)
    subset = df[mask]

    if subset.empty:
        return json.dumps(
            {"error": f"No data for {cancer_type} at threshold {threshold}"}
        )

    row = subset.iloc[0]
    return json.dumps(
        {
            "cancer_type": cancer_type.upper(),
            "threshold": threshold,
            "n_eligible": int(row.get("n_eligible", 0)),
            "n_total": int(row.get("n_total", 0)),
            "pct_eligible": round(float(row.get("pct_eligible", 0)), 1),
            "mean_expression_eligible": row.get("mean_expression_eligible"),
        },
        default=str,
    )


# ---------------------------------------------------------------------------
# Tool 4: Search clinical trials
# ---------------------------------------------------------------------------

def search_trials(query: str = "CD46", status: Optional[str] = None) -> str:
    """
    Search ClinicalTrials.gov JSON for relevant trials.

    Args:
        query: Search term to match in trial title or intervention.
        status: Optional status filter (e.g., "Recruiting", "Completed").

    Returns:
        JSON string with matching trials.
    """
    trials_path = RAW_DIR / "apis" / "clinicaltrials_cd46.json"

    # Curated trials always available
    curated = [
        {"nct_id": "NCT04768608", "title": "ABBV-CLS-484 (anti-CD46 ADC) in mCRPC",
         "phase": "Phase I/II", "status": "Active, not recruiting", "sponsor": "AbbVie"},
        {"nct_id": "NCT05911295", "title": "CD46-Targeted CAR-T Cell Therapy",
         "phase": "Phase I", "status": "Recruiting", "sponsor": "City of Hope"},
        {"nct_id": "NCT04946370", "title": "225Ac-PSMA-617 and Carboplatin in mCRPC",
         "phase": "Phase I", "status": "Recruiting", "sponsor": "Peter MacCallum"},
        {"nct_id": "NCT03544840", "title": "177Lu-PSMA-617 vs Cabazitaxel (TheraP)",
         "phase": "Phase II", "status": "Completed", "sponsor": "PCTA Australia"},
        {"nct_id": "NCT04986683", "title": "225Ac-PSMA617 in mCRPC (ANZA-002)",
         "phase": "Phase I", "status": "Recruiting", "sponsor": "Anza Therapeutics"},
    ]

    # Filter curated
    query_lower = query.lower()
    results = [
        t for t in curated
        if query_lower in t["title"].lower() or query_lower in t.get("intervention", "").lower()
    ]

    if status:
        results = [t for t in results if status.lower() in t.get("status", "").lower()]

    # Also load from API file if available
    if trials_path.exists():
        with open(trials_path) as f:
            data = json.load(f)
        for study in data.get("studies", [])[:20]:
            try:
                ps = study.get("protocolSection", {})
                nct_id = ps.get("identificationModule", {}).get("nctId", "")
                title = ps.get("identificationModule", {}).get("briefTitle", "")
                st = ps.get("statusModule", {}).get("overallStatus", "")
                if query_lower in title.lower():
                    if not status or status.lower() in st.lower():
                        if nct_id not in {r["nct_id"] for r in results}:
                            results.append({"nct_id": nct_id, "title": title, "status": st})
            except Exception:
                continue

    return json.dumps(results[:10], indent=2)


# ---------------------------------------------------------------------------
# Tool 5: Run analysis summary
# ---------------------------------------------------------------------------

def run_analysis_summary(analysis: str = "priority") -> str:
    """
    Return a pre-computed analysis result summary.

    Args:
        analysis: One of: "priority", "survival_significant", "top_eligible",
                  "combination_correlations".

    Returns:
        JSON string with analysis summary.
    """
    if analysis == "priority":
        df = _load_csv("priority_score.csv")
        if df is None:
            return json.dumps({"error": "priority_score.csv not found"})
        df_sorted = df.sort_values("priority_score", ascending=False)
        return json.dumps(
            {
                "analysis": "CD46 Priority Score",
                "top_10_cancers": df_sorted.head(10)[["cancer_type", "priority_score"]].to_dict(orient="records"),
                "formula": "0.35*expression_rank + 0.35*survival_impact + 0.15*cna_freq + 0.15*protein_score",
            },
            default=str,
            indent=2,
        )

    elif analysis == "survival_significant":
        df = _load_csv("cd46_survival_results.csv")
        if df is None:
            return json.dumps({"error": "cd46_survival_results.csv not found"})
        if "log_rank_p" in df.columns:
            sig = df[df["log_rank_p"] < 0.05]
            return json.dumps(
                {
                    "analysis": "Significant survival associations (p<0.05)",
                    "n_significant": len(sig),
                    "results": sig[["cancer_type", "endpoint", "hazard_ratio", "log_rank_p"]].to_dict(orient="records"),
                },
                default=str,
                indent=2,
            )

    elif analysis == "top_eligible":
        df = _load_csv("patient_groups.csv")
        if df is None:
            return json.dumps({"error": "patient_groups.csv not found"})
        if "threshold" in df.columns:
            df75 = df[df["threshold"] == "75th_pct"].sort_values("fraction_eligible", ascending=False)
            return json.dumps(
                {
                    "analysis": "Top eligible cancers at 75th percentile threshold",
                    "top_10": df75.head(10)[["cancer_type", "n_eligible", "n_total", "fraction_eligible"]].to_dict(orient="records"),
                },
                default=str,
                indent=2,
            )

    elif analysis == "combination_correlations":
        df = _load_csv("cd46_combination_biomarkers.csv")
        if df is None:
            return json.dumps({"error": "cd46_combination_biomarkers.csv not found"})
        return json.dumps(
            {
                "analysis": "CD46 vs co-biomarker Spearman correlations",
                "data": df.head(20).to_dict(orient="records"),
            },
            default=str,
            indent=2,
        )

    return json.dumps({"error": f"Unknown analysis type: {analysis}"})


# ---------------------------------------------------------------------------
# Tool registry for LangGraph
# ---------------------------------------------------------------------------

TOOL_REGISTRY = {
    "query_kg": query_kg,
    "load_csv_data": load_csv_data,
    "get_eligibility": get_eligibility,
    "search_trials": search_trials,
    "run_analysis_summary": run_analysis_summary,
}
