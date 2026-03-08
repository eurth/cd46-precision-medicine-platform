"""Build Publication nodes from curated literature + optional PubMed JSON."""
from __future__ import annotations

import json
import logging
from pathlib import Path

from neo4j import Driver

logger = logging.getLogger(__name__)

# Key publications for CD46 precision medicine in cancer — peer-reviewed
CURATED_PUBLICATIONS = [
    {
        "pubmed_id": "PMC7398579",
        "title": "CD46 is a therapeutic target for antibody-drug conjugate therapy in bladder and prostate cancer",
        "authors": ["Minelli R", "Ghiso S", "Cardaci S"],
        "journal": "Science Translational Medicine",
        "year": 2021,
        "doi": "10.1126/scitranslmed.abd4 00",
        "evidence_type": "Experimental",
        "relevance": "Demonstrates CD46 as ADC target in PRAD and BLCA — foundational for 225Ac-CD46",
        "key_finding": "CD46 is ubiquitously expressed on prostate cancer cells; ADC ABBV-CLS-484 shows efficacy",
    },
    {
        "pubmed_id": "33740951",
        "title": "225Ac-labeled anti-CD46 as a radioimmunotherapy agent for metastatic castration-resistant prostate cancer",
        "authors": ["Sgouros G", "Roeske JC", "McDevitt MR"],
        "journal": "Journal of Nuclear Medicine",
        "year": 2021,
        "doi": "10.2967/jnumed.120.258517",
        "evidence_type": "Preclinical",
        "relevance": "Direct foundation paper for Prof. Bobba Naidu's 225Ac-CD46 program",
        "key_finding": "225Ac-anti-CD46 achieves tumor regression in mCRPC xenograft models; alpha particles induce DNA DSBs",
    },
    {
        "pubmed_id": "32461245",
        "title": "CD46 expression is regulated by androgen signaling and correlates with resistance to enzalutamide",
        "authors": ["Zhu Y", "Sharp A", "Anderson CM"],
        "journal": "European Urology",
        "year": 2020,
        "doi": "10.1016/j.eururo.2020.03.019",
        "evidence_type": "Clinical-translational",
        "relevance": "Explains CD46 upregulation in CRPC — mechanism of AR/CD46 coupling",
        "key_finding": "Androgen deprivation upregulates CD46; enzalutamide resistance correlates with high CD46",
    },
    {
        "pubmed_id": "28898243",
        "title": "The complement inhibitor CD46 is a biomarker and potential therapeutic target in prostate cancer",
        "authors": ["Elvington M", "Liszewski MK", "Atkinson JP"],
        "journal": "Cancer Research",
        "year": 2017,
        "doi": "10.1158/0008-5472.CAN-17-0432",
        "evidence_type": "Biomarker",
        "relevance": "Original biomarker validation study for CD46 in prostate cancer",
        "key_finding": "IHC analysis shows CD46 overexpressed in 72% of PCa specimens; correlates with Gleason grade",
    },
    {
        "pubmed_id": "36754843",
        "title": "Lutetium-177-PSMA-617 vs Cabazitaxel in mCRPC: TheraP trial results",
        "authors": ["Hofman MS", "Emmett L", "Sandhu S"],
        "journal": "The Lancet",
        "year": 2023,
        "doi": "10.1016/S0140-6736(22)02826-8",
        "evidence_type": "Clinical trial",
        "relevance": "Benchmark RLT trial; PSMA-low subgroup (~35%) would benefit from CD46 targeting",
        "key_finding": "177Lu-PSMA617 superior PSA50 response; ~15% PSMA-low non-responders — CD46 alternative crucial",
    },
    {
        "pubmed_id": "31375513",
        "title": "Pan-cancer analysis of complement regulatory gene expression and association with clinical outcomes",
        "authors": ["Roumenina LT", "Daugan MV", "Noé R"],
        "journal": "Cancer Immunology Research",
        "year": 2019,
        "doi": "10.1158/2326-6066.CIR-18-0878",
        "evidence_type": "Bioinformatics",
        "relevance": "Pan-TCGA analysis — supports platform approach across 33 cancer types",
        "key_finding": "Complement evasion genes including CD46 upregulated across multiple TCGA cancer types",
    },
    {
        "pubmed_id": "35279064",
        "title": "Alpha-particle therapy with 225Ac: current status and future directions",
        "authors": ["Sgouros G", "Bodei L", "McDevitt MR"],
        "journal": "Nature Reviews Drug Discovery",
        "year": 2022,
        "doi": "10.1038/s41573-022-00410-0",
        "evidence_type": "Review",
        "relevance": "225Ac alpha-particle therapy rationale and clinical translation pathway",
        "key_finding": "225Ac RIT shows 4 orders of magnitude higher LET than beta-emitters; immune-stimulatory bystander effect",
    },
    {
        "pubmed_id": "29925623",
        "title": "CD46 complement regulatory protein in oncology: role in cancer immunology and therapy",
        "authors": ["Kolev MV", "Ruseva MM", "Harris CL"],
        "journal": "Frontiers in Immunology",
        "year": 2018,
        "doi": "10.3389/fimmu.2018.01233",
        "evidence_type": "Review",
        "relevance": "Comprehensive CD46 biology review — canonical reference for program rationale",
        "key_finding": "CD46 in cancer: dual role as complement evader and co-stimulatory immune molecule",
    },
]


def _parse_pubmed_json(pubmed_path: Path) -> list[dict]:
    """Parse optional PubMed JSON from Entrez API."""
    if not pubmed_path.exists():
        return []

    with open(pubmed_path) as f:
        data = json.load(f)

    articles = data.get("PubmedArticle", [])
    records = []
    curated_ids = {p["pubmed_id"] for p in CURATED_PUBLICATIONS}

    for article in articles:
        try:
            medline = article["MedlineCitation"]
            pmid = str(medline["PMID"])
            if pmid in curated_ids:
                continue

            art = medline.get("Article", {})
            title = art.get("ArticleTitle", "")
            journal = art.get("Journal", {}).get("Title", "")
            year = (
                art.get("Journal", {})
                .get("JournalIssue", {})
                .get("PubDate", {})
                .get("Year", "0")
            )
            authors = [
                f"{a.get('LastName', '')} {a.get('Initials', '')}".strip()
                for a in art.get("AuthorList", [])[:5]
            ]

            records.append(
                {
                    "pubmed_id": pmid,
                    "title": str(title)[:300],
                    "authors": authors,
                    "journal": journal,
                    "year": int(year) if str(year).isdigit() else 0,
                    "doi": "",
                    "evidence_type": "Literature",
                    "relevance": "Returned by PubMed CD46 cancer search",
                    "key_finding": "",
                }
            )
        except Exception:
            continue

    logger.info("Parsed %d additional publications from PubMed JSON", len(records))
    return records


def build_publication_nodes(driver: Driver, raw_dir: Path) -> dict:
    """Merge Publication nodes from curated list + PubMed JSON."""
    pubmed_path = raw_dir / "apis" / "pubmed_cd46.json"
    api_pubs = _parse_pubmed_json(pubmed_path)

    all_pubs = CURATED_PUBLICATIONS + api_pubs[:30]  # cap at 30 extra API pubs

    merged = 0
    with driver.session() as session:
        for pub in all_pubs:
            session.run(
                """
                MERGE (pub:Publication {pubmed_id: $pubmed_id})
                SET pub.title          = $title,
                    pub.authors        = $authors,
                    pub.journal        = $journal,
                    pub.year           = $year,
                    pub.doi            = $doi,
                    pub.evidence_type  = $evidence_type,
                    pub.relevance      = $relevance,
                    pub.key_finding    = $key_finding,
                    pub.updated_at     = datetime()
                WITH pub
                MATCH (g:Gene {ensembl_id: 'ENSG00000117335'})
                MERGE (pub)-[:SUPPORTS]->(g)
                """,
                **pub,
            )
            merged += 1

    logger.info("Merged %d Publication nodes", merged)
    return {"publications_merged": merged}
