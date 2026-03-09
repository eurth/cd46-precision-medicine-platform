"""
PubMed E-utilities search module for CD46 Research Assistant.

Uses NCBI E-utilities (no API key required):
  - esearch.fcgi  → PMIDs for a query
  - efetch.fcgi   → abstracts/metadata for those PMIDs

Rate limit: 3 requests/second without key, 10/s with NCBI_API_KEY env var.
"""
from __future__ import annotations

import logging
import os
import time
from typing import Optional

import requests

logger = logging.getLogger(__name__)

EUTILS_BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
EMAIL = "info@ayutara.com"  # courtesy email for NCBI rate limits
TIMEOUT = 12  # seconds


def _get_api_key() -> Optional[str]:
    return os.getenv("NCBI_API_KEY")  # optional; raises rate limit from 3→10/s


def _esearch(query: str, max_results: int = 8) -> list[str]:
    """Return list of PubMed IDs for the query."""
    params = {
        "db": "pubmed",
        "term": query,
        "retmax": max_results,
        "retmode": "json",
        "sort": "relevance",
        "email": EMAIL,
    }
    api_key = _get_api_key()
    if api_key:
        params["api_key"] = api_key

    try:
        resp = requests.get(f"{EUTILS_BASE}/esearch.fcgi", params=params, timeout=TIMEOUT)
        resp.raise_for_status()
        data = resp.json()
        return data.get("esearchresult", {}).get("idlist", [])
    except Exception as e:
        logger.warning("PubMed esearch failed for '%s': %s", query, e)
        return []


def _efetch_summaries(pmids: list[str]) -> list[dict]:
    """Fetch article summaries (title, authors, journal, year, abstract) for PMIDs."""
    if not pmids:
        return []

    params = {
        "db": "pubmed",
        "id": ",".join(pmids),
        "retmode": "json",
        "rettype": "abstract",
        "email": EMAIL,
    }
    api_key = _get_api_key()
    if api_key:
        params["api_key"] = api_key

    try:
        resp = requests.get(f"{EUTILS_BASE}/esummary.fcgi", params=params, timeout=TIMEOUT)
        resp.raise_for_status()
        data = resp.json()
        result_map = data.get("result", {})
    except Exception as e:
        logger.warning("PubMed efetch failed: %s", e)
        return []

    articles = []
    for pmid in pmids:
        item = result_map.get(pmid)
        if not item or not isinstance(item, dict):
            continue

        # Extract author list (last names only for brevity)
        author_list = item.get("authors", [])
        authors = [a.get("name", "") for a in author_list[:4]]
        if len(author_list) > 4:
            authors.append("et al.")

        pub_date = item.get("pubdate", "")
        year = pub_date[:4] if pub_date and len(pub_date) >= 4 else "N/A"

        articles.append(
            {
                "pmid": pmid,
                "title": item.get("title", "").rstrip("."),
                "authors": ", ".join(authors),
                "journal": item.get("fulljournalname", item.get("source", "")),
                "year": year,
                "abstract_snippet": "",  # filled by efetch below
                "url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
                "doi": next(
                    (
                        a.get("value", "")
                        for a in item.get("articleids", [])
                        if a.get("idtype") == "doi"
                    ),
                    "",
                ),
            }
        )

    return articles


def _efetch_abstracts(pmids: list[str]) -> dict[str, str]:
    """Fetch abstract text for a list of PMIDs. Returns {pmid: abstract_text}."""
    if not pmids:
        return {}

    params = {
        "db": "pubmed",
        "id": ",".join(pmids),
        "retmode": "text",
        "rettype": "abstract",
        "email": EMAIL,
    }
    api_key = _get_api_key()
    if api_key:
        params["api_key"] = api_key

    try:
        resp = requests.get(f"{EUTILS_BASE}/efetch.fcgi", params=params, timeout=TIMEOUT)
        resp.raise_for_status()
        text = resp.text
    except Exception as e:
        logger.warning("PubMed abstract fetch failed: %s", e)
        return {}

    # Split by PMID sections and extract first 300 chars of each abstract
    abstracts: dict[str, str] = {}
    sections = text.split("\n\n\n")
    for i, pmid in enumerate(pmids):
        if i < len(sections):
            # Take lines that look like abstract content (skip author/title lines)
            lines = sections[i].strip().split("\n")
            abstract_lines = [l for l in lines if len(l) > 80]  # body-length lines
            snippet = " ".join(abstract_lines)[:350]
            if snippet:
                abstracts[pmid] = snippet + ("..." if len(snippet) >= 350 else "")

    return abstracts


def fetch_pubmed(query: str, max_results: int = 6) -> list[dict]:
    """
    Search PubMed and return structured article records.

    Args:
        query: Free-text search query (e.g., "CD46 prostate cancer therapy")
        max_results: Maximum articles to return (default 6, max 10)

    Returns:
        List of dicts: pmid, title, authors, journal, year, abstract_snippet, url, doi
    """
    max_results = min(max_results, 10)  # hard cap for context window

    pmids = _esearch(query, max_results)
    if not pmids:
        logger.info("No PubMed results for query: %s", query)
        return []

    # Courtesy delay
    time.sleep(0.35)

    articles = _efetch_summaries(pmids)

    # Attempt to get abstract snippets
    time.sleep(0.35)
    abstracts = _efetch_abstracts(pmids)

    for art in articles:
        art["abstract_snippet"] = abstracts.get(art["pmid"], "")

    logger.info(
        "PubMed: found %d articles for query '%s'",
        len(articles),
        query[:60],
    )
    return articles


def format_for_llm_context(articles: list[dict]) -> str:
    """Format PubMed results as a structured string for LLM context injection."""
    if not articles:
        return ""

    lines = ["=== Recent PubMed Literature ==="]
    for i, art in enumerate(articles, 1):
        lines.append(
            f"\n[{i}] {art['title']} ({art['year']})\n"
            f"    Authors: {art['authors']}\n"
            f"    Journal: {art['journal']}\n"
            f"    URL: {art['url']}"
        )
        if art.get("abstract_snippet"):
            lines.append(f"    Abstract: {art['abstract_snippet']}")

    return "\n".join(lines)
