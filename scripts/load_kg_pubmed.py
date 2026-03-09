"""Fetch CD46-related publications from PubMed via Entrez API and load into AuraDB.

Uses Biopython Entrez (free, no API key required for < 3 requests/second).
Searches for top 60 CD46 publications, loads 50 into AuraDB as Publication nodes.

Input:  PubMed E-utilities API (NCBI Entrez)
Loads:
  - Publication nodes (MERGE on pubmed_id)
  - SUPPORTS relationships: Publication → Gene(CD46)
Expected gain: ~+42 Publication nodes (8 already exist → target 50)

Run:
    pip install biopython   (if not already installed)
    python scripts/load_kg_pubmed.py
Then verify:
    python scripts/audit_kg.py
"""
import os
import sys
import time
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

from neo4j import GraphDatabase


def get_driver():
    uri = os.getenv("NEO4J_URI")
    user = os.getenv("NEO4J_USERNAME", "neo4j")
    password = os.getenv("NEO4J_PASSWORD")
    if not uri or not password:
        raise RuntimeError("NEO4J_URI and NEO4J_PASSWORD must be set in .env")
    driver = GraphDatabase.driver(uri, auth=(user, password))
    driver.verify_connectivity()
    return driver


SEARCH_TERMS = [
    "CD46 cancer radiotherapy alpha particle",
    "CD46 membrane cofactor protein prostate cancer",
    "CD46 complement evasion tumor immunotherapy",
    "CD46 CD46 225Ac targeted cancer therapy",
    "atypical hemolytic uremic syndrome CD46 MCP",
]

MAX_RESULTS_PER_QUERY = 20
TARGET_TOTAL = 60


def fetch_pubmed_articles(search_term: str, max_results: int = 20) -> list:
    """Fetch PubMed article metadata using Biopython Entrez."""
    try:
        from Bio import Entrez
    except ImportError:
        print("ERROR: biopython not installed. Run: pip install biopython")
        return []

    Entrez.email = "cd46platform@research.edu"  # Required by NCBI
    Entrez.tool = "CD46PrecisionMedicineKG"

    articles = []
    try:
        # Search
        handle = Entrez.esearch(db="pubmed", term=search_term, retmax=max_results, sort="relevance")
        record = Entrez.read(handle)
        handle.close()
        ids = record.get("IdList", [])

        if not ids:
            return []

        # Fetch details in batches of 20
        time.sleep(0.4)  # Respect NCBI rate limit (3/sec)
        handle = Entrez.efetch(
            db="pubmed",
            id=",".join(ids),
            rettype="xml",
            retmode="xml",
        )
        records = Entrez.read(handle)
        handle.close()

        for rec in records.get("PubmedArticle", []):
            try:
                med_citation = rec.get("MedlineCitation", {})
                article = med_citation.get("Article", {})
                journal = article.get("Journal", {})

                pmid = str(med_citation.get("PMID", ""))
                title = str(article.get("ArticleTitle", ""))
                journal_name = str(journal.get("Title", ""))

                # Year from pub date
                pub_date = journal.get("JournalIssue", {}).get("PubDate", {})
                year = str(pub_date.get("Year", pub_date.get("MedlineDate", "")[:4]))

                # Authors
                author_list = article.get("AuthorList", [])
                authors = []
                for auth in author_list[:5]:  # Limit to first 5 authors
                    last = str(auth.get("LastName", ""))
                    initials = str(auth.get("Initials", ""))
                    if last:
                        authors.append(f"{last} {initials}".strip())
                author_str = ", ".join(authors)
                if len(author_list) > 5:
                    author_str += f" et al. ({len(author_list)} total)"

                # Abstract (first 500 chars)
                abstract_texts = article.get("Abstract", {}).get("AbstractText", [])
                if isinstance(abstract_texts, list):
                    abstract = " ".join(str(t) for t in abstract_texts)
                else:
                    abstract = str(abstract_texts)
                abstract = abstract[:500] + "..." if len(abstract) > 500 else abstract

                # MeSH terms for keyword tagging
                mesh_list = med_citation.get("MeshHeadingList", [])
                keywords = []
                for mesh in mesh_list[:8]:
                    desc = mesh.get("DescriptorName", "")
                    if desc:
                        keywords.append(str(desc))

                if pmid and title:
                    articles.append({
                        "pmid": pmid,
                        "title": title,
                        "authors": author_str,
                        "journal": journal_name,
                        "year": year,
                        "abstract": abstract,
                        "keywords": ", ".join(keywords),
                        "url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
                    })
            except Exception as e:
                print(f"  Warning: could not parse article: {e}")
                continue

    except Exception as e:
        print(f"  Entrez fetch error for '{search_term}': {e}")

    return articles


def load_publications(driver, articles: list):
    """Load Publication nodes into AuraDB."""
    pub_cypher = """
        MERGE (p:Publication {pubmed_id: $pmid})
        ON CREATE SET
            p.title = $title,
            p.authors = $authors,
            p.journal = $journal,
            p.year = $year,
            p.abstract = $abstract,
            p.keywords = $keywords,
            p.url = $url,
            p.evidence_type = $evidence_type,
            p.source = 'PubMed'
        ON MATCH SET
            p.abstract = COALESCE(p.abstract, $abstract)
        RETURN p.pubmed_id AS id
    """

    supports_cypher = """
        MATCH (pub:Publication {pubmed_id: $pmid})
        MATCH (g:Gene {symbol: 'CD46'})
        MERGE (pub)-[r:SUPPORTS]->(g)
        ON CREATE SET r.source = 'PubMed'
        RETURN type(r)
    """

    count = 0
    with driver.session() as session:
        for art in articles:
            # Guess evidence type from title/keywords
            title_lower = art["title"].lower()
            keywords_lower = art["keywords"].lower()
            if any(w in title_lower for w in ["trial", "clinical", "patient", "phase"]):
                evidence_type = "Clinical trial"
            elif any(w in title_lower for w in ["review", "overview", "meta-analysis"]):
                evidence_type = "Review"
            elif any(w in title_lower for w in ["expression", "biomarker", "survival"]):
                evidence_type = "Biomarker"
            elif any(w in title_lower for w in ["mouse", "cell line", "in vitro", "in vivo", "xenograft"]):
                evidence_type = "Preclinical"
            else:
                evidence_type = "Experimental"

            session.run(
                pub_cypher,
                pmid=art["pmid"],
                title=art["title"],
                authors=art["authors"],
                journal=art["journal"],
                year=art["year"],
                abstract=art["abstract"],
                keywords=art["keywords"],
                url=art["url"],
                evidence_type=evidence_type,
            )
            session.run(supports_cypher, pmid=art["pmid"])
            count += 1

    return count


def main():
    driver = get_driver()

    all_articles = {}
    for search_term in SEARCH_TERMS:
        print(f"\nSearching PubMed: '{search_term}'...")
        articles = fetch_pubmed_articles(search_term, max_results=MAX_RESULTS_PER_QUERY)
        print(f"  Found {len(articles)} articles.")
        for art in articles:
            if art["pmid"] not in all_articles:
                all_articles[art["pmid"]] = art
        if len(all_articles) >= TARGET_TOTAL:
            break
        time.sleep(0.5)  # Between searches

    unique_articles = list(all_articles.values())[:TARGET_TOTAL]
    print(f"\nTotal unique articles collected: {len(unique_articles)}")

    if not unique_articles:
        print("No articles found — check network connectivity and biopython installation.")
        driver.close()
        return

    print(f"Loading {len(unique_articles)} publications into AuraDB...")
    try:
        count = load_publications(driver, unique_articles)
        print(f"✅ {count} Publication nodes upserted.")
        print("Run scripts/audit_kg.py to confirm AuraDB counts.")
    finally:
        driver.close()


if __name__ == "__main__":
    main()
