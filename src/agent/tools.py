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


def _active_gene() -> str:
    try:
        from components.targets import get_active_symbol
        return get_active_symbol()
    except Exception:
        return "CD46"


def _load_csv(filename: str) -> Optional[pd.DataFrame]:
    path = DATA_DIR / filename
    if not path.exists():
        logger.warning("Tool data file not found: %s", path)
        return None
    return pd.read_csv(path)


def _gene_file_map(gene: str) -> dict[str, str]:
    g = gene.lower()
    return {
        "expression": f"{g}_expression.csv",
        "by_cancer": f"{g}_by_cancer.csv",
        "priority": f"{g}_priority_score.csv",
        "survival": f"{g}_survival_results.csv",
        "eligibility": f"{g}_patient_groups.csv",
        "hpa": f"hpa_{g}_protein.csv",
        "hpa_intensity": f"hpa_{g}_protein_intensity.csv",
        "depmap": f"depmap_{g}_essentiality.csv",
        "cbioportal": "cbioportal_mcrpc.csv",
        "combination": f"{g}_combination_biomarkers.csv",
        "gtex": f"gtex_{g}_normal.csv",
    }


def _resolve_dataset_df(dataset: str, gene: str) -> tuple[Optional[pd.DataFrame], str]:
    """Load CSV for dataset; try fallbacks without removing CD46-only files."""
    key = dataset.lower()
    file_map = _gene_file_map(gene)
    g = gene.lower()

    candidates: list[str] = []
    primary = file_map.get(key)
    if primary:
        candidates.append(primary)
    if key == "hpa":
        candidates.append(f"hpa_{g}_protein_intensity.csv")
    if key == "priority" and gene.upper() == "CD46":
        candidates.append("priority_score.csv")
    if key == "eligibility" and gene.upper() == "CD46":
        candidates.append("patient_groups.csv")
    if key == "combination" and gene.upper() == "CD46":
        candidates.append("cd46_combination_biomarkers.csv")

    seen: set[str] = set()
    for fname in candidates:
        if not fname or fname in seen:
            continue
        seen.add(fname)
        df = _load_csv(fname)
        if df is not None:
            return df, fname
    return None, primary or ""


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
    gene = _active_gene()
    file_map = _gene_file_map(gene)
    case_only = {"combination", "eligibility", "priority", "cbioportal"}

    if dataset.lower() not in file_map and dataset.lower() != "hpa":
        available = list(file_map.keys())
        return json.dumps({"error": f"Unknown dataset '{dataset}'. Available: {available}"})

    df, filename = _resolve_dataset_df(dataset, gene)
    if df is None:
        hint = ""
        if dataset.lower() in case_only and gene.upper() != "CD46":
            hint = (
                f" Dataset '{dataset}' may be CD46 case-study depth only. "
                f"For {gene} use expression/by_cancer/survival/hpa/depmap where CSVs exist."
            )
        return json.dumps(
            {
                "error": f"File not found for dataset '{dataset}' (tried processed/*).{hint}",
                "active_gene": gene,
            }
        )

    if cancer_type and "cancer_type" in df.columns:
        df = df[df["cancer_type"].str.upper() == cancer_type.upper()]

    return json.dumps(
        {
            "dataset": dataset,
            "active_gene": gene,
            "file": filename,
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
    Get patient eligibility statistics for a cancer type and threshold.

    Args:
        cancer_type: TCGA cancer code (e.g., "PRAD", "OV", "BLCA").
        threshold: One of: "median", "75th_pct", "log2tpm_2.5", "log2tpm_3.0".

    Returns:
        JSON string with eligibility stats.
    """
    gene = _active_gene()
    df, src = _resolve_dataset_df("eligibility", gene)
    if df is None:
        if cancer_type.upper() == "PRAD" and gene.upper() == "CD46":
            return json.dumps(
                {
                    "cancer_type": "PRAD",
                    "threshold": threshold,
                    "n_eligible": 219,
                    "n_total": 497,
                    "pct_eligible": 44.1,
                    "note": "Static estimate — run pipeline for computed values",
                    "active_gene": gene,
                }
            )
        return json.dumps({"error": f"No eligibility slice for {gene}", "active_gene": gene})

    sym = gene.upper()
    high = f"{sym}-High"
    thr = threshold.replace("log2_2.5", "log2tpm_2.5").replace("log2_3.0", "log2tpm_3.0")
    mask = (
        (df["cancer_type"].str.upper() == cancer_type.upper())
        & (df["threshold_method"].astype(str) == thr)
        & (df.get("expression_group", high) == high)
    )
    subset = df[mask]

    if subset.empty:
        return json.dumps(
            {"error": f"No data for {cancer_type} at threshold {threshold}", "active_gene": gene, "file": src}
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
            "active_gene": gene,
            "source_file": src,
        },
        default=str,
    )


# ---------------------------------------------------------------------------
# Tool 4: Search clinical trials
# ---------------------------------------------------------------------------

def search_trials(query: Optional[str] = None, status: Optional[str] = None) -> str:
    """
    Search ClinicalTrials.gov JSON for relevant trials.

    Args:
        query: Search term to match in trial title or intervention.
               Defaults to the active gene symbol (not hard-coded CD46).
        status: Optional status filter (e.g., "Recruiting", "Completed").

    Returns:
        JSON string with matching trials.
    """
    gene = _active_gene()
    if not query:
        query = gene
    gene_path = RAW_DIR / "apis" / f"clinicaltrials_{gene.lower()}.json"
    # Only fall back to CD46 cache when the active gene is CD46
    trials_path = gene_path
    if not trials_path.exists() and gene.upper() == "CD46":
        trials_path = RAW_DIR / "apis" / "clinicaltrials_cd46.json"

    results: list[dict] = []
    query_lower = query.lower()

    # Curated CD46 / PSMA seeds — only for CD46, never bleed into other genes
    if gene.upper() == "CD46":
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
        results = [
            t for t in curated
            if query_lower in t["title"].lower()
            or query_lower in t.get("intervention", "").lower()
            or "cd46" in t["title"].lower()
        ]
        if status:
            results = [t for t in results if t.get("status", "").lower() == status.lower()]

    # Load from API file if available (active gene cache only)
    if trials_path.exists():
        with open(trials_path, encoding="utf-8") as f:
            data = json.load(f)
        studies = data if isinstance(data, list) else data.get("studies", [])
        for study in studies[:30]:
            try:
                ps = study.get("protocolSection", {})
                nct_id = ps.get("identificationModule", {}).get("nctId", "")
                title = ps.get("identificationModule", {}).get("briefTitle", "")
                st_raw = ps.get("statusModule", {}).get("overallStatus", "")
                # Normalize ClinicalTrials.gov v2 uppercase codes (e.g. RECRUITING → Recruiting)
                st = st_raw.replace("_", " ").title()
                if not status or st.lower() == status.lower():
                    if nct_id not in {r["nct_id"] for r in results}:
                        results.append(
                            {
                                "nct_id": nct_id,
                                "title": title,
                                "status": st,
                                "source_file": trials_path.name,
                            }
                        )
            except Exception:
                continue

    return json.dumps(
        {"active_gene": gene, "file": trials_path.name if trials_path.exists() else None, "trials": results[:15]},
        indent=2,
    )


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
        gene = _active_gene()
        df, fname = _resolve_dataset_df("priority", gene)
        if df is None:
            # ponytail: fallback to expression ranks when no priority CSV for gene
            bc, bc_name = _resolve_dataset_df("by_cancer", gene)
            if bc is not None and "cancer_type" in bc.columns:
                med = "gene_median" if "gene_median" in bc.columns else bc.columns[-1]
                top = bc.nlargest(10, med) if med in bc.columns else bc.head(10)
                return json.dumps(
                    {
                        "analysis": f"Top TCGA expression by cancer ({gene})",
                        "active_gene": gene,
                        "note": "priority_score.csv not found — using by_cancer medians",
                        "top_10_cancers": top[["cancer_type", med]].to_dict(orient="records")
                        if med in top.columns
                        else top.head(10).to_dict(orient="records"),
                    },
                    default=str,
                    indent=2,
                )
            return json.dumps({"error": "priority_score.csv not found", "active_gene": gene})
        score_col = "priority_score" if "priority_score" in df.columns else df.columns[-1]
        df_sorted = df.sort_values(score_col, ascending=False)
        cols = [c for c in ["cancer_type", score_col] if c in df_sorted.columns]
        return json.dumps(
            {
                "analysis": f"{gene} priority / ranking",
                "active_gene": gene,
                "file": fname,
                "top_10_cancers": df_sorted.head(10)[cols].to_dict(orient="records"),
            },
            default=str,
            indent=2,
        )

    elif analysis == "survival_significant":
        gene = _active_gene()
        fname = f"{gene.lower()}_survival_results.csv"
        df = _load_csv(fname)
        if df is None:
            return json.dumps({"error": f"{fname} not found", "active_gene": gene})
        # Cox rows use p_value; KM rows use log_rank_p
        pcol = "p_value" if "p_value" in df.columns else "log_rank_p"
        if pcol in df.columns:
            sig = df[df[pcol].notna() & (df[pcol] < 0.05)]
            cols = [c for c in ["cancer_type", "endpoint", "hazard_ratio", pcol, "log_rank_p"] if c in sig.columns]
            return json.dumps(
                {
                    "analysis": f"Significant survival associations for {gene} (p<0.05)",
                    "active_gene": gene,
                    "n_significant": len(sig),
                    "results": sig[cols].to_dict(orient="records"),
                },
                default=str,
                indent=2,
            )

    elif analysis == "top_eligible":
        gene = _active_gene()
        df, src = _resolve_dataset_df("eligibility", gene)
        if df is None:
            return json.dumps({"error": f"eligibility slice not found for {gene}"})
        sym = gene.upper()
        high = f"{sym}-High"
        method_col = "threshold_method" if "threshold_method" in df.columns else "threshold"
        pct_col = "pct_eligible" if "pct_eligible" in df.columns else "fraction_eligible"
        df75 = df[
            df[method_col].astype(str).str.contains("75th", case=False, na=False)
            & (df.get("expression_group", high) == high)
        ].sort_values(pct_col, ascending=False)
        cols = [c for c in ["cancer_type", "n_eligible", "n_total", pct_col] if c in df75.columns]
        return json.dumps(
            {
                "analysis": f"Top eligible cancers at 75th percentile ({gene})",
                "active_gene": gene,
                "source_file": src,
                "top_10": df75.head(10)[cols].to_dict(orient="records"),
            },
            default=str,
            indent=2,
        )

    elif analysis == "combination_correlations":
        gene = _active_gene()
        df, fname = _resolve_dataset_df("combination", gene)
        if df is None:
            return json.dumps(
                {"error": f"No combination biomarker CSV for {gene}", "active_gene": gene}
            )
        return json.dumps(
            {
                "analysis": f"{gene} vs co-biomarker correlations",
                "active_gene": gene,
                "file": fname,
                "data": df.head(20).to_dict(orient="records"),
            },
            default=str,
            indent=2,
        )

    return json.dumps({"error": f"Unknown analysis type: {analysis}"})


# ---------------------------------------------------------------------------
# Tool 6: Search PubMed live
# ---------------------------------------------------------------------------

def search_pubmed(query: str, max_results: int = 6) -> str:
    """
    Search PubMed via NCBI E-utilities and return article metadata with abstracts.

    Args:
        query: Free-text search query (e.g., "CD46 prostate cancer therapy")
        max_results: Maximum articles to return (default 6)

    Returns:
        JSON string with article list: pmid, title, authors, journal, year, url, abstract_snippet
    """
    try:
        from src.agent.pubmed_search import fetch_pubmed, format_for_llm_context
        articles = fetch_pubmed(query, max_results)
        return json.dumps(
            {
                "query": query,
                "total_found": len(articles),
                "articles": articles,
                "formatted_context": format_for_llm_context(articles),
            },
            indent=2,
        )
    except Exception as e:
        logger.error("PubMed search failed: %s", e)
        return json.dumps({"error": str(e), "query": query})


# ---------------------------------------------------------------------------
# Tool registry for LangGraph
# ---------------------------------------------------------------------------

TOOL_REGISTRY = {
    "query_kg": query_kg,
    "load_csv_data": load_csv_data,
    "get_eligibility": get_eligibility,
    "search_trials": search_trials,
    "run_analysis_summary": run_analysis_summary,
    "search_pubmed": search_pubmed,
}
