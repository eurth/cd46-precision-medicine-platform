"""Step 3b — per-gene PubMed + ChEMBL/curated drugs into Aura (open-data recipe).

Usage (laptop, .env Neo4j):
  python scripts/load_gene_pubmed_chembl.py --symbol FOLH1
  python scripts/load_gene_pubmed_chembl.py --all-non-cd46
  python scripts/load_gene_pubmed_chembl.py --all

Schema:
  (:Publication)-[:SUPPORTS {source:'PubMed'}]->(:Gene)
  (:Drug)-[:TARGETS {source:...}]->(:Gene)

Caps (Aura Free): ~25 pubs / gene, ~15 ChEMBL molecules / gene + curated RLT agents.
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
from typing import Any

import yaml
from dotenv import load_dotenv
from neo4j import GraphDatabase

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT))
load_dotenv(_ROOT / ".env")

log = logging.getLogger(__name__)
RAW = _ROOT / "data" / "raw" / "apis"
PROC = _ROOT / "data" / "processed"
TARGETS_YAML = _ROOT / "config" / "targets.yaml"

# Resolved 2026-07-29 via UniProt accession → ChEMBL target API (Homo sapiens SINGLE PROTEIN).
# CD46: no ChEMBL protein target (antibody/biologic); curated agents only.
CHEMBL_BY_UNIPROT: dict[str, str] = {
    "Q04609": "CHEMBL1892",   # FOLH1 / PSMA
    "Q12884": "CHEMBL4683",   # FAP
    "P30874": "CHEMBL1804",   # SSTR2
    "P30550": "CHEMBL4959",   # GRPR
}
# CD46 is antibody/biologic — ChEMBL has no SINGLE PROTEIN target for P15529
NO_CHEMBL_UNIPROT = {"P15529"}

PUBMED_MAX_PER_GENE = 25
PUBMED_PER_QUERY = 15
CHEMBL_MOL_CAP = 15

# Theranostic / clinical agents not fully covered by ChEMBL small-molecule TARGETS.
CURATED_AGENTS: dict[str, list[dict[str, Any]]] = {
    "CD46": [
        {
            "name": "FOR46",
            "drug_type": "ADC",
            "mechanism": "Anti-CD46 antibody-drug conjugate (DM4 payload)",
            "developer": "Fortis Therapeutics / AstraZeneca",
            "max_phase": 1,
            "indication": "mCRPC, myeloma",
            "isotope": "",
            "chembl_id": "",
            "source": "ClinicalTrials.gov NCT03959397 / curated",
        },
        {
            "name": "225Ac-DOTA-CD46-Antibody",
            "drug_type": "RadioligandTherapy",
            "mechanism": "Anti-CD46 antibody conjugated to 225Ac alpha-emitter",
            "developer": "Academic / Preclinical",
            "max_phase": 0,
            "indication": "CD46+ solid tumours",
            "isotope": "225Ac",
            "chembl_id": "",
            "source": "PubMed preclinical / curated",
        },
    ],
    "FOLH1": [
        {
            "name": "177Lu-PSMA-617 (Pluvicto)",
            "drug_type": "RadioligandTherapy",
            "mechanism": "PSMA-targeting small molecule conjugated to 177Lu",
            "developer": "Novartis",
            "max_phase": 4,
            "indication": "PSMA+ mCRPC",
            "isotope": "177Lu",
            "chembl_id": "CHEMBL4523781",
            "source": "FDA 2022 / ChEMBL CHEMBL4523781",
        },
        {
            "name": "225Ac-PSMA-617",
            "drug_type": "RadioligandTherapy",
            "mechanism": "PSMA-targeting small molecule conjugated to 225Ac",
            "developer": "Various (investigational)",
            "max_phase": 2,
            "indication": "PSMA+ mCRPC",
            "isotope": "225Ac",
            "chembl_id": "",
            "source": "ClinicalTrials.gov / curated",
        },
    ],
    "FAP": [
        {
            "name": "68Ga-FAPI-46",
            "drug_type": "RadioligandTherapy",
            "mechanism": "FAP inhibitor (FAPI) PET tracer — theranostic pair lead-in",
            "developer": "Academic / SOFIE / various",
            "max_phase": 2,
            "indication": "FAP+ solid tumours (imaging)",
            "isotope": "68Ga",
            "chembl_id": "",
            "source": "ClinicalTrials.gov / curated",
        },
        {
            "name": "177Lu-FAPI-46",
            "drug_type": "RadioligandTherapy",
            "mechanism": "FAP-targeted radioligand therapy",
            "developer": "Academic / investigational",
            "max_phase": 1,
            "indication": "FAP+ solid tumours",
            "isotope": "177Lu",
            "chembl_id": "",
            "source": "ClinicalTrials.gov / curated",
        },
    ],
    "SSTR2": [
        {
            "name": "177Lu-DOTATATE (Lutathera)",
            "drug_type": "RadioligandTherapy",
            "mechanism": "SSTR2-targeting peptide conjugated to 177Lu",
            "developer": "Novartis",
            "max_phase": 4,
            "indication": "SSTR+ GEP-NET",
            "isotope": "177Lu",
            "chembl_id": "CHEMBL2108738",
            "source": "FDA approved / curated",
        },
        {
            "name": "68Ga-DOTATATE (Netspot)",
            "drug_type": "RadioligandTherapy",
            "mechanism": "SSTR2 PET imaging companion",
            "developer": "Novartis / Advanced Accelerator Applications",
            "max_phase": 4,
            "indication": "SSTR+ NET imaging",
            "isotope": "68Ga",
            "chembl_id": "",
            "source": "FDA approved / curated",
        },
    ],
    "GRPR": [
        {
            "name": "68Ga-RM2",
            "drug_type": "RadioligandTherapy",
            "mechanism": "GRPR antagonist PET tracer",
            "developer": "Academic / investigational",
            "max_phase": 2,
            "indication": "GRPR+ prostate / breast imaging",
            "isotope": "68Ga",
            "chembl_id": "",
            "source": "ClinicalTrials.gov / curated",
        },
        {
            "name": "177Lu-NeoB",
            "drug_type": "RadioligandTherapy",
            "mechanism": "GRPR-targeted radioligand (NeoB / NeoBOMB1 class)",
            "developer": "Novartis / investigational",
            "max_phase": 1,
            "indication": "GRPR+ solid tumours",
            "isotope": "177Lu",
            "chembl_id": "",
            "source": "ClinicalTrials.gov / curated",
        },
    ],
}


def get_target(symbol: str) -> dict[str, Any]:
    with TARGETS_YAML.open(encoding="utf-8") as f:
        reg = yaml.safe_load(f) or {}
    t = (reg.get("targets") or {}).get(symbol)
    if not t:
        raise KeyError(symbol)
    return {"symbol": symbol, **t}


def _driver():
    uri = os.environ.get("NEO4J_URI")
    user = os.environ.get("NEO4J_USERNAME", "neo4j")
    pwd = os.environ.get("NEO4J_PASSWORD")
    if not uri or not pwd:
        raise RuntimeError("NEO4J_URI / NEO4J_PASSWORD required")
    d = GraphDatabase.driver(uri, auth=(user, pwd))
    d.verify_connectivity()
    return d


def chembl_get(endpoint: str, params: dict, *, timeout: int = 60) -> dict:
    qs = urllib.parse.urlencode({**params, "format": "json"})
    url = f"https://www.ebi.ac.uk/chembl/api/data/{endpoint}?{qs}"
    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def resolve_chembl_target_id(t: dict) -> str | None:
    """Prefer registry, then UniProt map, then live ChEMBL lookup."""
    existing = (t.get("chembl_target_id") or "").strip()
    # Reject known-bad CD46 placeholder (CHEMBL2176 is mouse phosphatidyltransferase)
    if existing and existing not in ("CHEMBL2176",):
        return existing
    acc = (t.get("uniprot_id") or "").strip()
    if acc in NO_CHEMBL_UNIPROT:
        return None
    if acc in CHEMBL_BY_UNIPROT:
        return CHEMBL_BY_UNIPROT[acc]
    if not acc:
        return None
    try:
        data = chembl_get(
            "target",
            {"target_components__accession": acc, "limit": 10},
            timeout=60,
        )
        for tgt in data.get("targets") or []:
            if tgt.get("organism") == "Homo sapiens" and tgt.get("target_type") == "SINGLE PROTEIN":
                return tgt.get("target_chembl_id")
        for tgt in data.get("targets") or []:
            if tgt.get("organism") == "Homo sapiens":
                return tgt.get("target_chembl_id")
    except Exception as e:
        log.warning("ChEMBL target resolve failed for %s: %s", t.get("symbol"), e)
    return None


def patch_targets_yaml(symbol: str, chembl_id: str) -> None:
    """Write chembl_target_id into config/targets.yaml for the gene."""
    text = TARGETS_YAML.read_text(encoding="utf-8")
    # ponytail: line-oriented YAML patch; ceiling = nested key collisions — use pyyaml dump if schema grows
    lines = text.splitlines(keepends=True)
    out: list[str] = []
    in_gene = False
    patched = False
    for line in lines:
        if line.startswith(f"  {symbol}:"):
            in_gene = True
            out.append(line)
            continue
        if in_gene and line.startswith("  ") and not line.startswith("    ") and not line.startswith(f"  {symbol}:"):
            if not patched:
                # insert before leaving the gene block
                out.append(f"    chembl_target_id: {chembl_id}\n")
                patched = True
            in_gene = False
            out.append(line)
            continue
        if in_gene and line.strip().startswith("chembl_target_id:"):
            out.append(f"    chembl_target_id: {chembl_id}\n")
            patched = True
            continue
        out.append(line)
    if in_gene and not patched:
        out.append(f"    chembl_target_id: {chembl_id}\n")
        patched = True
    if patched:
        TARGETS_YAML.write_text("".join(out), encoding="utf-8")
        log.info("Patched %s chembl_target_id=%s", symbol, chembl_id)


# ---------------------------------------------------------------------------
# PubMed
# ---------------------------------------------------------------------------

def _pubmed_queries(t: dict) -> list[str]:
    sym = t["symbol"]
    aliases = [a for a in (t.get("aliases") or []) if a and a.upper() != sym.upper()][:3]
    name = (t.get("name") or "").split("(")[0].strip()
    terms = [
        f"{sym} cancer theranostics OR radioligand",
        f"{sym} prostate cancer OR solid tumor therapy",
    ]
    if aliases:
        terms.append(f"({sym} OR {aliases[0]}) cancer targeted therapy")
    if name and name.upper() != sym.upper():
        terms.append(f'"{name}" cancer biomarker OR therapy')
    return terms[:4]


def fetch_pubmed(symbol: str, *, refresh: bool = False) -> list[dict]:
    t = get_target(symbol)
    out = RAW / f"pubmed_{symbol.lower()}.json"
    RAW.mkdir(parents=True, exist_ok=True)
    if out.exists() and not refresh:
        log.info("Using cached PubMed %s", out.name)
        return json.loads(out.read_text(encoding="utf-8"))

    try:
        from Bio import Entrez
    except ImportError as e:
        raise RuntimeError("biopython required: pip install biopython") from e

    Entrez.email = os.environ.get("ENTREZ_EMAIL") or "oncobridge@research.local"
    Entrez.tool = "OncoBridgeGeneKG"

    all_articles: dict[str, dict] = {}
    for q in _pubmed_queries(t):
        log.info("PubMed search: %s", q)
        try:
            handle = Entrez.esearch(db="pubmed", term=q, retmax=PUBMED_PER_QUERY, sort="relevance")
            record = Entrez.read(handle)
            handle.close()
            ids = record.get("IdList", [])
            if not ids:
                continue
            time.sleep(0.4)
            handle = Entrez.efetch(db="pubmed", id=",".join(ids), rettype="xml", retmode="xml")
            records = Entrez.read(handle)
            handle.close()
            for rec in records.get("PubmedArticle", []):
                try:
                    med = rec.get("MedlineCitation", {})
                    article = med.get("Article", {})
                    journal = article.get("Journal", {})
                    pmid = str(med.get("PMID", ""))
                    title = str(article.get("ArticleTitle", ""))
                    if not pmid or not title:
                        continue
                    pub_date = journal.get("JournalIssue", {}).get("PubDate", {})
                    year = str(pub_date.get("Year", str(pub_date.get("MedlineDate", ""))[:4]))
                    author_list = article.get("AuthorList", [])
                    authors = []
                    for auth in author_list[:5]:
                        last = str(auth.get("LastName", ""))
                        initials = str(auth.get("Initials", ""))
                        if last:
                            authors.append(f"{last} {initials}".strip())
                    author_str = ", ".join(authors)
                    if len(author_list) > 5:
                        author_str += f" et al. ({len(author_list)} total)"
                    abstract_texts = article.get("Abstract", {}).get("AbstractText", [])
                    if isinstance(abstract_texts, list):
                        abstract = " ".join(str(x) for x in abstract_texts)
                    else:
                        abstract = str(abstract_texts)
                    abstract = abstract[:500] + ("..." if len(abstract) > 500 else "")
                    mesh_list = med.get("MeshHeadingList", [])
                    keywords = []
                    for mesh in mesh_list[:8]:
                        desc = mesh.get("DescriptorName", "")
                        if desc:
                            keywords.append(str(desc))
                    all_articles[pmid] = {
                        "pmid": pmid,
                        "title": title,
                        "authors": author_str,
                        "journal": str(journal.get("Title", "")),
                        "year": year,
                        "abstract": abstract,
                        "keywords": ", ".join(keywords),
                        "url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
                        "query_gene": symbol,
                    }
                except Exception as e:
                    log.warning("parse article: %s", e)
        except Exception as e:
            log.warning("Entrez error for '%s': %s", q, e)
        if len(all_articles) >= PUBMED_MAX_PER_GENE:
            break
        time.sleep(0.5)

    articles = list(all_articles.values())[:PUBMED_MAX_PER_GENE]
    out.write_text(json.dumps(articles, indent=2), encoding="utf-8")
    log.info("Saved %d PubMed → %s", len(articles), out.name)
    return articles


def _evidence_type(title: str, keywords: str) -> str:
    t = (title + " " + keywords).lower()
    if any(w in t for w in ("trial", "clinical", "patient", "phase")):
        return "Clinical trial"
    if any(w in t for w in ("review", "overview", "meta-analysis")):
        return "Review"
    if any(w in t for w in ("expression", "biomarker", "survival")):
        return "Biomarker"
    if any(w in t for w in ("mouse", "cell line", "in vitro", "in vivo", "xenograft")):
        return "Preclinical"
    return "Experimental"


def load_publications(session, symbol: str, articles: list[dict]) -> int:
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
        p.source = 'PubMed',
        p.query_gene = $gene
    ON MATCH SET
        p.abstract = COALESCE(p.abstract, $abstract),
        p.query_gene = COALESCE(p.query_gene, $gene)
    WITH p
    MATCH (g:Gene {symbol: $gene})
    MERGE (p)-[r:SUPPORTS]->(g)
    ON CREATE SET r.source = 'PubMed', r.gene_symbol = $gene
    """
    n = 0
    for art in articles:
        session.run(
            pub_cypher,
            pmid=art["pmid"],
            title=art["title"],
            authors=art.get("authors", ""),
            journal=art.get("journal", ""),
            year=art.get("year", ""),
            abstract=art.get("abstract", ""),
            keywords=art.get("keywords", ""),
            url=art.get("url", ""),
            evidence_type=_evidence_type(art.get("title", ""), art.get("keywords", "")),
            gene=symbol,
        )
        n += 1
    log.info("%s publications linked: %d", symbol, n)
    return n


# ---------------------------------------------------------------------------
# ChEMBL + curated
# ---------------------------------------------------------------------------

def fetch_chembl_drugs(symbol: str, chembl_target_id: str | None, *, refresh: bool = False) -> list[dict]:
    out = RAW / f"chembl_{symbol.lower()}.json"
    RAW.mkdir(parents=True, exist_ok=True)
    if out.exists() and not refresh and chembl_target_id:
        cached = json.loads(out.read_text(encoding="utf-8"))
        if cached.get("target_chembl_id") == chembl_target_id:
            log.info("Using cached ChEMBL %s", out.name)
            return cached.get("drugs") or []

    drugs: list[dict] = []
    if chembl_target_id:
        log.info("Fetching ChEMBL activities for %s (%s)", symbol, chembl_target_id)
        try:
            data = chembl_get(
                "activity",
                {
                    "target_chembl_id": chembl_target_id,
                    "limit": 100,
                    "offset": 0,
                },
                timeout=90,
            )
            activities = data.get("activities") or []
            # Prefer named molecules with phase / potency
            by_mol: dict[str, dict] = {}
            for a in activities:
                mid = a.get("molecule_chembl_id")
                if not mid:
                    continue
                prev = by_mol.get(mid)
                score = (
                    (10 if a.get("canonical_smiles") else 0)
                    + (5 if a.get("standard_value") is not None else 0)
                )
                if prev is None or score > prev.get("_score", 0):
                    by_mol[mid] = {**a, "_score": score}
            mol_ids = list(by_mol.keys())[:CHEMBL_MOL_CAP]
            for i in range(0, len(mol_ids), 20):
                batch = mol_ids[i : i + 20]
                try:
                    mdata = chembl_get(
                        "molecule",
                        {"molecule_chembl_id__in": ",".join(batch)},
                        timeout=60,
                    )
                    for mol in mdata.get("molecules") or []:
                        mid = mol.get("molecule_chembl_id")
                        act = by_mol.get(mid, {})
                        name = mol.get("pref_name") or mid
                        drugs.append(
                            {
                                "name": name,
                                "drug_type": mol.get("molecule_type") or "SmallMolecule",
                                "mechanism": f"ChEMBL activity vs {chembl_target_id}"
                                + (
                                    f" ({act.get('standard_type')}={act.get('standard_value')} {act.get('standard_units') or ''})".rstrip()
                                    if act.get("standard_type")
                                    else ""
                                ),
                                "developer": "",
                                "max_phase": mol.get("max_phase") or 0,
                                "indication": mol.get("indication_class") or "",
                                "isotope": "",
                                "chembl_id": mid,
                                "smiles": (mol.get("molecule_structures") or {}).get("canonical_smiles") or "",
                                "molecule_type": mol.get("molecule_type") or "",
                                "source": f"ChEMBL {chembl_target_id} CC BY-SA 4.0",
                                "_from_chembl": True,
                            }
                        )
                except Exception as e:
                    log.warning("molecule batch failed: %s", e)
                time.sleep(0.35)
        except Exception as e:
            log.warning("ChEMBL activity fetch failed for %s: %s", symbol, e)

    payload = {
        "symbol": symbol,
        "target_chembl_id": chembl_target_id,
        "drugs": drugs,
        "source": "ChEMBL REST API v3 (CC BY-SA 4.0)",
    }
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    log.info("Saved %d ChEMBL drugs → %s", len(drugs), out.name)
    return drugs


def load_drugs(session, symbol: str, drugs: list[dict]) -> int:
    merge_cypher = """
    MERGE (d:Drug {name: $name})
    ON CREATE SET
        d.drug_type = $drug_type,
        d.mechanism = $mechanism,
        d.target_protein = $target,
        d.developer = $developer,
        d.max_phase = $max_phase,
        d.indication = $indication,
        d.isotope = $isotope,
        d.source = $source,
        d.chembl_id = $chembl_id,
        d.smiles = $smiles,
        d.molecule_type = $molecule_type,
        d.query_gene = $gene
    ON MATCH SET
        d.max_phase = CASE WHEN $max_phase > coalesce(d.max_phase, 0) THEN $max_phase ELSE d.max_phase END,
        d.chembl_id = COALESCE(d.chembl_id, $chembl_id),
        d.smiles = COALESCE(d.smiles, $smiles),
        d.query_gene = COALESCE(d.query_gene, $gene)
    WITH d
    MATCH (g:Gene {symbol: $gene})
    MERGE (d)-[r:TARGETS]->(g)
    ON CREATE SET r.source = $source, r.evidence = $mechanism, r.gene_symbol = $gene
    """
    n = 0
    for drug in drugs:
        session.run(
            merge_cypher,
            name=drug["name"],
            drug_type=drug.get("drug_type") or "",
            mechanism=drug.get("mechanism") or "",
            target=symbol,
            developer=drug.get("developer") or "",
            max_phase=drug.get("max_phase") or 0,
            indication=drug.get("indication") or "",
            isotope=drug.get("isotope") or "",
            source=drug.get("source") or "ChEMBL",
            chembl_id=drug.get("chembl_id") or "",
            smiles=drug.get("smiles") or "",
            molecule_type=drug.get("molecule_type") or "",
            gene=symbol,
        )
        n += 1
    log.info("%s drugs linked: %d", symbol, n)
    return n


def run_symbol(symbol: str, *, refresh: bool = False) -> dict:
    symbol = symbol.upper()
    t = get_target(symbol)
    report: dict[str, Any] = {"symbol": symbol}

    articles = fetch_pubmed(symbol, refresh=refresh)
    report["pubmed_fetched"] = len(articles)

    chembl_id = resolve_chembl_target_id(t)
    report["chembl_target_id"] = chembl_id
    if chembl_id and chembl_id != (t.get("chembl_target_id") or ""):
        patch_targets_yaml(symbol, chembl_id)
    elif t.get("chembl_target_id") == "CHEMBL2176":
        # Clear bad CD46 placeholder — leave unset (no ChEMBL protein target)
        patch_targets_yaml_remove_bad_cd46()

    chembl_drugs = fetch_chembl_drugs(symbol, chembl_id, refresh=refresh)
    curated = [dict(x) for x in CURATED_AGENTS.get(symbol, [])]
    # Dedup curated vs ChEMBL by name / chembl_id
    seen_names = {d["name"].lower() for d in chembl_drugs}
    seen_ids = {d.get("chembl_id") for d in chembl_drugs if d.get("chembl_id")}
    for c in curated:
        if c["name"].lower() in seen_names:
            continue
        if c.get("chembl_id") and c["chembl_id"] in seen_ids:
            continue
        chembl_drugs.append(c)
    report["drugs_total"] = len(chembl_drugs)
    report["drugs_chembl"] = sum(1 for d in chembl_drugs if d.get("_from_chembl"))
    report["drugs_curated"] = len(chembl_drugs) - report["drugs_chembl"]

    # processed summary (git-friendly)
    PROC.mkdir(parents=True, exist_ok=True)
    summary = {
        "symbol": symbol,
        "pubmed_count": len(articles),
        "chembl_target_id": chembl_id,
        "drug_names": [d["name"] for d in chembl_drugs],
    }
    (PROC / f"step3b_{symbol.lower()}_summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )

    driver = _driver()
    try:
        with driver.session() as session:
            before = session.run("MATCH (n) RETURN count(n) AS c").single()["c"]
            session.run("MERGE (g:Gene {symbol: $s})", s=symbol)
            report["pubmed_loaded"] = load_publications(session, symbol, articles)
            report["drugs_loaded"] = load_drugs(session, symbol, chembl_drugs)
            after = session.run("MATCH (n) RETURN count(n) AS c").single()["c"]
            report["nodes_before"] = before
            report["nodes_after"] = after
            report["nodes_delta"] = after - before
            # sanity counts
            pub_n = session.run(
                "MATCH (:Publication)-[:SUPPORTS]->(g:Gene {symbol:$s}) RETURN count(*) AS c",
                s=symbol,
            ).single()["c"]
            drug_n = session.run(
                "MATCH (:Drug)-[:TARGETS]->(g:Gene {symbol:$s}) RETURN count(*) AS c",
                s=symbol,
            ).single()["c"]
            report["supports_rels"] = pub_n
            report["targets_rels"] = drug_n
    finally:
        driver.close()
    return report


def patch_targets_yaml_remove_bad_cd46() -> None:
    """Remove incorrect chembl_target_id: CHEMBL2176 under CD46."""
    text = TARGETS_YAML.read_text(encoding="utf-8")
    lines = text.splitlines(keepends=True)
    out: list[str] = []
    in_cd46 = False
    for line in lines:
        if line.startswith("  CD46:"):
            in_cd46 = True
            out.append(line)
            continue
        if in_cd46 and line.startswith("  ") and not line.startswith("    "):
            in_cd46 = False
        if in_cd46 and "chembl_target_id: CHEMBL2176" in line:
            log.info("Removed bad CD46 chembl_target_id CHEMBL2176")
            continue
        out.append(line)
    TARGETS_YAML.write_text("".join(out), encoding="utf-8")


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    ap = argparse.ArgumentParser()
    ap.add_argument("--symbol")
    ap.add_argument("--all-non-cd46", action="store_true")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--refresh", action="store_true")
    args = ap.parse_args()
    if args.all:
        symbols = ["CD46", "FOLH1", "FAP", "SSTR2", "GRPR"]
    elif args.all_non_cd46:
        symbols = ["FOLH1", "FAP", "SSTR2", "GRPR"]
    elif args.symbol:
        symbols = [args.symbol.upper()]
    else:
        ap.error("Need --symbol, --all-non-cd46, or --all")

    reports = []
    for i, sym in enumerate(symbols):
        if i:
            time.sleep(1.0)
        reports.append(run_symbol(sym, refresh=args.refresh))
        print(json.dumps(reports[-1], indent=2))

    # Aggregate Aura count from last report
    last_after = reports[-1].get("nodes_after") if reports else "?"
    out = _ROOT / "reports" / "step3b_pubmed_chembl.md"
    lines = [
        "# Step 3b — PubMed + ChEMBL per target",
        "",
        f"**Aura after Step 3b:** **{last_after} nodes**",
        "",
        "| Gene | PubMed | Pubs loaded | ChEMBL ID | Drugs loaded | SUPPORTS | TARGETS | Nodes Δ |",
        "|------|--------|-------------|-----------|--------------|----------|---------|---------|",
    ]
    for r in reports:
        lines.append(
            f"| {r['symbol']} | {r.get('pubmed_fetched')} | {r.get('pubmed_loaded')} | "
            f"{r.get('chembl_target_id') or '—'} | {r.get('drugs_loaded')} | "
            f"{r.get('supports_rels')} | {r.get('targets_rels')} | {r.get('nodes_delta')} |"
        )
    lines += [
        "",
        "## Schema",
        "",
        "- `(:Publication)-[:SUPPORTS {source:'PubMed'}]->(:Gene)`",
        "- `(:Drug)-[:TARGETS]->(:Gene)` — ChEMBL molecules + curated theranostic agents",
        "",
        "## Script",
        "",
        "```bash",
        "python scripts/load_gene_pubmed_chembl.py --all --refresh",
        "```",
        "",
        "## Notes",
        "",
        "- ChEMBL IDs resolved via UniProt: FOLH1=`CHEMBL1892`, FAP=`CHEMBL4683`, "
        "SSTR2=`CHEMBL1804`, GRPR=`CHEMBL4959`.",
        "- CD46 has no ChEMBL SINGLE PROTEIN target; curated biologics/RLT only "
        "(removed incorrect `CHEMBL2176` placeholder).",
        "- Caps: ≤25 PubMed / gene, ≤15 ChEMBL molecules / gene + curated agents.",
        "",
    ]
    out.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {out}")


if __name__ == "__main__":
    main()
