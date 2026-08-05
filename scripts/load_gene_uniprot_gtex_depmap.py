"""Step 3c — UniProt + GTEx + DepMap DEPENDS_ON + denser HPA protein intensity.

Usage (laptop, .env Neo4j):
  python scripts/load_gene_uniprot_gtex_depmap.py --symbol FOLH1
  python scripts/load_gene_uniprot_gtex_depmap.py --all-non-cd46
  python scripts/load_gene_uniprot_gtex_depmap.py --all

Schema (gene-aware; does not overwrite CD46 Tissue.gtex_* / CellLine.cd46_* props):
  (:Gene)-[:ENCODES]->(:Protein {uniprot_id})
  (:Protein)-[:HAS_ISOFORM]->(:ProteinIsoform)   # capped
  (:Protein)-[:HAS_VARIANT]->(:ProteinVariant)   # capped
  (:Gene)-[:EXPRESSED_IN {source:'GTEx', median_tpm, ...}]->(:Tissue)
  (:Gene)-[:EXPRESSED_IN {source:'HPA', modality:'protein_intensity'}]->(:Tissue)
  (:CellLine)-[:DEPENDS_ON {gene_symbol, crispr_score, source:'DepMap'}]->(:Gene)
    # only existing CellLine nodes; only CRISPR score < -0.5
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

import pandas as pd
import requests
import yaml
from dotenv import load_dotenv
from neo4j import GraphDatabase

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT))
load_dotenv(_ROOT / ".env")

log = logging.getLogger(__name__)
RAW = _ROOT / "data" / "raw" / "apis"
HPA_RAW = _ROOT / "data" / "raw" / "hpa"
PROC = _ROOT / "data" / "processed"
DEPMAP_CRISPR = _ROOT / "data" / "raw" / "depmap" / "CRISPRGeneEffect.csv"
DEPMAP_META = _ROOT / "data" / "raw" / "depmap" / "Model.csv"
TARGETS_YAML = _ROOT / "config" / "targets.yaml"

GTEX_API = "https://gtexportal.org/api/v2"
GTEX_DATASET = "gtex_v8"
UNIPROT_BASE = "https://rest.uniprot.org/uniprotkb"
DEPENDENCY_THRESHOLD = -0.5
ISO_CAP = 0  # 0 = all UniProt isoforms
VAR_CAP = 0  # 0 = all Natural variant features

# From load_kg_gtex.py — map GTEx detail → HPA tissue name (None = skip cell-line tissues)
GTEX_TO_HPA = {
    "Adipose - Subcutaneous": "Adipose tissue",
    "Adipose - Visceral (Omentum)": "Adipose tissue",
    "Artery - Aorta": "Aorta",
    "Artery - Coronary": "Artery",
    "Artery - Tibial": "Artery",
    "Brain - Amygdala": "Brain",
    "Brain - Anterior cingulate cortex (BA24)": "Brain",
    "Brain - Caudate (basal ganglia)": "Brain",
    "Brain - Cerebellar Hemisphere": "Cerebellum",
    "Brain - Cerebellum": "Cerebellum",
    "Brain - Cortex": "Cerebral cortex",
    "Brain - Frontal Cortex (BA9)": "Cerebral cortex",
    "Brain - Hippocampus": "Hippocampus",
    "Brain - Hypothalamus": "Brain",
    "Brain - Nucleus accumbens (basal ganglia)": "Brain",
    "Brain - Putamen (basal ganglia)": "Brain",
    "Brain - Spinal cord (cervical c-1)": "Spinal cord",
    "Brain - Substantia nigra": "Brain",
    "Breast - Mammary Tissue": "Breast",
    "Cells - Cultured fibroblasts": None,
    "Cells - EBV-transformed lymphocytes": None,
    "Cervix - Ectocervix": "Cervix",
    "Cervix - Endocervix": "Cervix",
    "Colon - Sigmoid": "Colon",
    "Colon - Transverse": "Colon",
    "Esophagus - Gastroesophageal Junction": "Esophagus",
    "Esophagus - Mucosa": "Esophagus",
    "Esophagus - Muscularis": "Esophagus",
    "Fallopian Tube": "Fallopian tube",
    "Heart - Atrial Appendage": "Heart muscle",
    "Heart - Left Ventricle": "Heart muscle",
    "Kidney - Cortex": "Kidney",
    "Kidney - Medulla": "Kidney",
    "Muscle - Skeletal": "Skeletal muscle",
    "Nerve - Tibial": "Peripheral nerve",
    "Skin - Not Sun Exposed (Suprapubic)": "Skin",
    "Skin - Sun Exposed (Lower leg)": "Skin",
    "Small Intestine - Terminal Ileum": "Small intestine",
    "Vagina": "Vagina",
    "Whole Blood": "Bone marrow",
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


def _http_json(url: str, *, timeout: int = 60) -> dict:
    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


# ---------------------------------------------------------------------------
# UniProt
# ---------------------------------------------------------------------------

def fetch_uniprot(symbol: str, *, refresh: bool = False) -> dict:
    t = get_target(symbol)
    acc = t["uniprot_id"]
    out = RAW / f"uniprot_{symbol.lower()}.json"
    RAW.mkdir(parents=True, exist_ok=True)
    if out.exists() and not refresh:
        log.info("Using cached UniProt %s", out.name)
        return json.loads(out.read_text(encoding="utf-8"))
    url = f"{UNIPROT_BASE}/{acc}.json"
    log.info("Fetching UniProt %s", url)
    r = requests.get(url, timeout=60, headers={"Accept": "application/json"})
    r.raise_for_status()
    data = r.json()
    out.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return data


def _uniprot_function(data: dict) -> str:
    for c in data.get("comments") or []:
        if c.get("commentType") == "FUNCTION":
            texts = c.get("texts") or []
            if texts:
                return str(texts[0].get("value", ""))[:500]
    return ""


def load_uniprot(session, symbol: str, data: dict) -> dict[str, int]:
    uid = data.get("primaryAccession") or get_target(symbol)["uniprot_id"]
    seq = data.get("sequence") or {}
    protein_cypher = """
    MERGE (p:Protein {uniprot_id: $uid})
    SET p.symbol = $gene,
        p.gene_symbol = $gene,
        p.protein_name = $pname,
        p.function = $func,
        p.molecular_weight = $mw,
        p.length = $length,
        p.surface_expressed = true,
        p.source = 'UniProt'
    WITH p
    MATCH (g:Gene {symbol: $gene})
    MERGE (g)-[:ENCODES]->(p)
    SET g.uniprot_id = $uid
    """
    session.run(
        protein_cypher,
        uid=uid,
        gene=symbol,
        pname=data.get("uniProtkbId") or uid,
        func=_uniprot_function(data),
        mw=seq.get("molWeight"),
        length=seq.get("length"),
    )

    # Isoforms (capped)
    alt = next((c for c in (data.get("comments") or []) if c.get("commentType") == "ALTERNATIVE PRODUCTS"), {})
    isoforms = list(alt.get("isoforms") or [])
    if ISO_CAP > 0:
        isoforms = isoforms[:ISO_CAP]
    iso_cypher = """
    MATCH (p:Protein {uniprot_id: $uid})
    MERGE (iso:ProteinIsoform {uniprot_isoform_id: $iso_id})
    ON CREATE SET
        iso.name = $name,
        iso.synonyms = $synonyms,
        iso.sequence_status = $status,
        iso.gene_symbol = $gene,
        iso.source = 'UniProt'
    MERGE (p)-[:HAS_ISOFORM]->(iso)
    """
    n_iso = 0
    for iso in isoforms:
        name = (iso.get("name") or {}).get("value", "?")
        synonyms = [s.get("value", "") for s in iso.get("synonyms") or []]
        iso_ids = iso.get("isoformIds") or []
        iso_id = iso_ids[0] if iso_ids else f"{uid}-{name}"
        session.run(
            iso_cypher,
            uid=uid,
            iso_id=iso_id,
            name=name,
            synonyms=", ".join(synonyms),
            status=iso.get("isoformSequenceStatus", "Described"),
            gene=symbol,
        )
        n_iso += 1

    # Natural variants (capped)
    variants = [f for f in (data.get("features") or []) if f.get("type") == "Natural variant"]
    if VAR_CAP > 0:
        variants = variants[:VAR_CAP]
    var_cypher = """
    MATCH (p:Protein {uniprot_id: $uid})
    MERGE (v:ProteinVariant {variant_id: $variant_id})
    ON CREATE SET
        v.position = $position,
        v.original_aa = $original,
        v.variant_aa = $variant,
        v.dbsnp_id = $dbsnp_id,
        v.disease_note = $disease_note,
        v.feature_id = $feature_id,
        v.gene_symbol = $gene,
        v.source = 'UniProt'
    MERGE (p)-[:HAS_VARIANT]->(v)
    """
    n_var = 0
    for v in variants:
        pos = (v.get("location") or {}).get("start", {}).get("value")
        alt_seq = v.get("alternativeSequence") or {}
        original = alt_seq.get("originalSequence", "?")
        alts = alt_seq.get("alternativeSequences") or ["?"]
        variant_aa = alts[0] if alts else "?"
        cross_refs = v.get("featureCrossReferences") or []
        dbsnp_id = next((r["id"] for r in cross_refs if r.get("database") == "dbSNP"), "")
        raw_desc = v.get("description") or ""
        parts = [p.strip() for p in raw_desc.split(";")]
        disease_parts = [
            p.replace("in ", "").strip()
            for p in parts
            if p.strip() and not p.strip().lower().startswith("dbsnp")
        ]
        feature_id = v.get("featureId") or f"VAR_{pos}_{original}{variant_aa}"
        variant_id = feature_id or f"{uid}_VAR_{pos}_{original}_{variant_aa}"
        session.run(
            var_cypher,
            uid=uid,
            variant_id=variant_id,
            position=pos,
            original=original,
            variant=variant_aa,
            dbsnp_id=dbsnp_id,
            disease_note="; ".join(disease_parts),
            feature_id=feature_id,
            gene=symbol,
        )
        n_var += 1

    log.info("%s UniProt: protein=1 isoforms=%d variants=%d", symbol, n_iso, n_var)
    return {"protein": 1, "isoforms": n_iso, "variants": n_var}


# ---------------------------------------------------------------------------
# GTEx
# ---------------------------------------------------------------------------

def resolve_gencode_id(ensembl_id: str) -> str:
    """GTEx needs versioned gencodeId; resolve via reference API."""
    qs = urllib.parse.urlencode({"geneId": ensembl_id})
    data = _http_json(f"{GTEX_API}/reference/gene?{qs}", timeout=45)
    rows = data.get("data") or []
    if not rows:
        raise RuntimeError(f"GTEx gene not found: {ensembl_id}")
    return rows[0]["gencodeId"]


def fetch_gtex(symbol: str, *, refresh: bool = False) -> Path:
    t = get_target(symbol)
    csv_path = PROC / f"gtex_{symbol.lower()}_normal.csv"
    raw_path = RAW / f"gtex_{symbol.lower()}.json"
    PROC.mkdir(parents=True, exist_ok=True)
    RAW.mkdir(parents=True, exist_ok=True)
    if csv_path.exists() and not refresh:
        log.info("Using cached GTEx %s", csv_path.name)
        return csv_path

    gencode = resolve_gencode_id(t["ensembl_id"])
    log.info("GTEx %s gencodeId=%s", symbol, gencode)

    tissue_data = _http_json(
        f"{GTEX_API}/dataset/tissueSiteDetail?{urllib.parse.urlencode({'datasetId': GTEX_DATASET, 'pageSize': 100})}",
        timeout=45,
    )
    tissue_map = {
        trow["tissueSiteDetailId"]: {
            "tissue_site_detail": trow.get("tissueSiteDetail", trow["tissueSiteDetailId"]),
            "tissue_site": trow.get("tissueSite", ""),
        }
        for trow in tissue_data.get("data") or []
    }

    qs = urllib.parse.urlencode(
        {"datasetId": GTEX_DATASET, "gencodeId": gencode, "itemsPerPage": 300}
    )
    expr = _http_json(f"{GTEX_API}/expression/geneExpression?{qs}", timeout=90)
    raw_path.write_text(json.dumps(expr, indent=2), encoding="utf-8")

    rows = []
    for rec in expr.get("data") or []:
        tpm_values = rec.get("data") or []
        if not tpm_values:
            continue
        tpm_sorted = sorted(tpm_values)
        n = len(tpm_sorted)
        q1 = tpm_sorted[n // 4] if n >= 4 else tpm_sorted[0]
        median = tpm_sorted[n // 2]
        q3 = tpm_sorted[3 * n // 4] if n >= 4 else tpm_sorted[-1]
        mean_tpm = sum(tpm_sorted) / n
        tissue_id = rec.get("tissueSiteDetailId", "")
        info = tissue_map.get(
            tissue_id, {"tissue_site_detail": tissue_id, "tissue_site": ""}
        )
        rows.append(
            {
                "tissue_site_detail": info["tissue_site_detail"],
                "tissue_site": info["tissue_site"],
                "tissue_site_id": tissue_id,
                "median_tpm": round(median, 4),
                "mean_tpm": round(mean_tpm, 4),
                "q1_tpm": round(q1, 4),
                "q3_tpm": round(q3, 4),
                "n_samples": n,
                "unit": rec.get("unit", "TPM"),
                "dataset": GTEX_DATASET,
                "gene_symbol": symbol,
                "gencode_id": gencode,
            }
        )
    df = pd.DataFrame(rows).sort_values("median_tpm", ascending=False).reset_index(drop=True)
    df.to_csv(csv_path, index=False)
    log.info("Saved GTEx %d tissues → %s", len(df), csv_path.name)
    return csv_path


def load_gtex(session, symbol: str, csv_path: Path) -> int:
    df = pd.read_csv(csv_path)
    cypher = """
    MERGE (t:Tissue {name: $name})
    ON CREATE SET t.type = 'normal', t.source = 'GTEx'
    WITH t
    MATCH (g:Gene {symbol: $gene})
    MERGE (g)-[r:EXPRESSED_IN]->(t)
    SET r.source = 'GTEx',
        r.modality = 'rna_tpm',
        r.median_tpm = $median_tpm,
        r.mean_tpm = $mean_tpm,
        r.q1_tpm = $q1_tpm,
        r.q3_tpm = $q3_tpm,
        r.n_samples = $n_samples,
        r.dataset = $dataset,
        r.gene_symbol = $gene,
        r.gtex_tissue_id = $tissue_id
    """
    n = 0
    for _, rec in df.iterrows():
        detail = str(rec["tissue_site_detail"])
        if detail in GTEX_TO_HPA and GTEX_TO_HPA[detail] is None:
            continue
        tissue_name = GTEX_TO_HPA.get(detail) or detail
        session.run(
            cypher,
            name=tissue_name,
            gene=symbol,
            median_tpm=float(rec["median_tpm"]),
            mean_tpm=float(rec["mean_tpm"]),
            q1_tpm=float(rec["q1_tpm"]),
            q3_tpm=float(rec["q3_tpm"]),
            n_samples=int(rec["n_samples"]),
            dataset=str(rec.get("dataset", GTEX_DATASET)),
            tissue_id=str(rec.get("tissue_site_id", "")),
        )
        n += 1
    log.info("%s GTEx EXPRESSED_IN: %d", symbol, n)
    return n


# ---------------------------------------------------------------------------
# DepMap — DEPENDS_ON on existing CellLines only
# ---------------------------------------------------------------------------

def depmap_column_name(symbol: str, entrez_id: int | str) -> str:
    return f"{symbol} ({entrez_id})"


def extract_depmap(symbol: str, *, refresh: bool = False) -> Path:
    t = get_target(symbol)
    out = PROC / f"depmap_{symbol.lower()}_essentiality.csv"
    if out.exists() and not refresh:
        log.info("Using cached DepMap %s", out.name)
        return out
    if not DEPMAP_CRISPR.exists():
        raise FileNotFoundError(f"Missing {DEPMAP_CRISPR}")

    col = depmap_column_name(symbol, t["entrez_id"])
    hdr = pd.read_csv(DEPMAP_CRISPR, nrows=0).columns.tolist()
    if col not in hdr:
        raise KeyError(f"DepMap column not found: {col} (avoid substring matches like AFAP1)")
    id_col = hdr[0]
    log.info("Reading DepMap CRISPR column %s ...", col)
    crispr = pd.read_csv(DEPMAP_CRISPR, usecols=[id_col, col])
    crispr = crispr.rename(columns={id_col: "depmap_id", col: "crispr_score"})

    if DEPMAP_META.exists():
        meta = pd.read_csv(DEPMAP_META)
        id_col = next((c for c in meta.columns if c in ("ModelID", "DepMapID", "depmap_id")), None)
        if id_col:
            meta = meta.rename(columns={id_col: "depmap_id"})
        col_map = {
            "CellLineName": "cell_line_name",
            "OncotreePrimaryDisease": "cancer_type",
            "OncotreeLineage": "lineage",
        }
        for src, dst in col_map.items():
            if src in meta.columns:
                meta = meta.rename(columns={src: dst})
        keep = ["depmap_id"] + [c for c in ("cell_line_name", "cancer_type", "lineage") if c in meta.columns]
        meta = meta[keep].drop_duplicates("depmap_id")
        result = crispr.merge(meta, on="depmap_id", how="left")
    else:
        result = crispr.copy()
        result["cell_line_name"] = result["depmap_id"]
        result["cancer_type"] = "Unknown"
        result["lineage"] = "Unknown"

    result["is_dependency"] = result["crispr_score"].fillna(0) < DEPENDENCY_THRESHOLD
    result["gene_symbol"] = symbol
    PROC.mkdir(parents=True, exist_ok=True)
    result.to_csv(out, index=False)
    n_dep = int(result["is_dependency"].sum())
    log.info("DepMap %s: %d lines, %d dependencies → %s", symbol, len(result), n_dep, out.name)
    return out


def load_depmap(session, symbol: str, csv_path: Path) -> int:
    """Link existing CellLine nodes only — no new CellLine bulk create."""
    df = pd.read_csv(csv_path)
    deps = df[df["is_dependency"] == True]  # noqa: E712
    cypher = """
    MATCH (cl:CellLine {depmap_id: $depmap_id})
    MATCH (g:Gene {symbol: $gene})
    MERGE (cl)-[r:DEPENDS_ON]->(g)
    SET r.source = 'DepMap',
        r.gene_symbol = $gene,
        r.crispr_score = $score,
        r.is_essential = true,
        r.threshold = $threshold
    RETURN cl.depmap_id AS id
    """
    n = 0
    skipped = 0
    for _, row in deps.iterrows():
        res = session.run(
            cypher,
            depmap_id=str(row["depmap_id"]),
            gene=symbol,
            score=float(row["crispr_score"]),
            threshold=DEPENDENCY_THRESHOLD,
        )
        if res.single():
            n += 1
        else:
            skipped += 1
    log.info("%s DepMap DEPENDS_ON: %d linked, %d skipped (no CellLine)", symbol, n, skipped)
    return n


# ---------------------------------------------------------------------------
# HPA denser protein intensity (from gene JSON already used in 3a)
# ---------------------------------------------------------------------------

def fetch_hpa_cached(symbol: str, *, refresh: bool = False) -> dict:
    t = get_target(symbol)
    ens = t["ensembl_id"]
    out = HPA_RAW / f"{symbol.lower()}_protein_expression.json"
    HPA_RAW.mkdir(parents=True, exist_ok=True)
    if out.exists() and not refresh:
        return json.loads(out.read_text(encoding="utf-8"))
    url = f"https://www.proteinatlas.org/{ens}.json"
    log.info("Fetching HPA %s", url)
    r = requests.get(url, timeout=60, headers={"Accept": "application/json"})
    r.raise_for_status()
    data = r.json()
    if isinstance(data, list):
        data = next(
            (e for e in data if e.get("Ensembl") == ens or e.get("Gene", "").upper() == symbol),
            data[0] if data else {},
        )
    out.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return data if isinstance(data, dict) else {}


def process_hpa_protein_intensity(symbol: str, raw: dict) -> Path:
    rows = []
    for key, ttype in (
        ("Protein tissue specific Intensity", "normal"),
        ("Protein cell type specific Intensity", "cell_type"),
    ):
        blob = raw.get(key) or {}
        if not isinstance(blob, dict):
            continue
        for tissue, val in blob.items():
            try:
                score = float(val)
            except (TypeError, ValueError):
                continue
            rows.append(
                {
                    "tissue": tissue,
                    "type": ttype,
                    "intensity_score": score,
                    "data_source": "HPA_protein_intensity",
                }
            )
    path = PROC / f"hpa_{symbol.lower()}_protein_intensity.csv"
    PROC.mkdir(parents=True, exist_ok=True)
    cols = ["tissue", "type", "intensity_score", "data_source"]
    pd.DataFrame(rows, columns=cols).to_csv(path, index=False)
    # gene-level protein summary
    summary = {
        "gene": symbol,
        "protein_tissue_specificity": raw.get("Protein tissue specificity") or "",
        "protein_tissue_distribution": raw.get("Protein tissue distribution") or "",
        "protein_cell_type_specificity": raw.get("Protein cell type specificity") or "",
        "n_intensity_rows": len(rows),
    }
    (PROC / f"hpa_{symbol.lower()}_protein_summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )
    return path


def load_hpa_protein(session, symbol: str, raw: dict, csv_path: Path) -> int:
    session.run(
        """
        MATCH (g:Gene {symbol: $gene})
        SET g.hpa_protein_tissue_specificity = $spec,
            g.hpa_protein_tissue_distribution = $dist,
            g.hpa_protein_cell_type_specificity = $cell_spec
        """,
        gene=symbol,
        spec=str(raw.get("Protein tissue specificity") or ""),
        dist=str(raw.get("Protein tissue distribution") or ""),
        cell_spec=str(raw.get("Protein cell type specificity") or ""),
    )
    df = pd.read_csv(csv_path)
    if df.empty or "tissue" not in df.columns:
        log.info("%s HPA protein intensity: 0 rows", symbol)
        return 0
    cypher = """
    MERGE (t:Tissue {name: $name, type: $type})
    ON CREATE SET t.source = 'HPA'
    WITH t
    MATCH (g:Gene {symbol: $gene})
    MERGE (g)-[r:EXPRESSED_IN]->(t)
    SET r.source = 'HPA',
        r.modality = 'protein_intensity',
        r.intensity_score = $score,
        r.gene_symbol = $gene
    """
    n = 0
    for _, row in df.iterrows():
        session.run(
            cypher,
            name=str(row["tissue"]),
            type=str(row.get("type") or "normal"),
            gene=symbol,
            score=float(row["intensity_score"]),
        )
        n += 1
    log.info("%s HPA protein EXPRESSED_IN: %d", symbol, n)
    return n


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------

def run_symbol(symbol: str, *, refresh: bool = False) -> dict:
    symbol = symbol.upper()
    get_target(symbol)
    report: dict[str, Any] = {"symbol": symbol}

    uni = fetch_uniprot(symbol, refresh=refresh)
    gtex_csv = fetch_gtex(symbol, refresh=refresh)
    dep_csv = extract_depmap(symbol, refresh=refresh)
    hpa = fetch_hpa_cached(symbol, refresh=refresh)
    hpa_csv = process_hpa_protein_intensity(symbol, hpa)

    driver = _driver()
    try:
        with driver.session() as session:
            before = session.run("MATCH (n) RETURN count(n) AS c").single()["c"]
            session.run("MERGE (g:Gene {symbol: $s})", s=symbol)
            uni_counts = load_uniprot(session, symbol, uni)
            report.update({f"uniprot_{k}": v for k, v in uni_counts.items()})
            report["gtex_tissues"] = load_gtex(session, symbol, gtex_csv)
            report["depmap_depends_on"] = load_depmap(session, symbol, dep_csv)
            report["hpa_protein_tissues"] = load_hpa_protein(session, symbol, hpa, hpa_csv)
            after = session.run("MATCH (n) RETURN count(n) AS c").single()["c"]
            report["nodes_before"] = before
            report["nodes_after"] = after
            report["nodes_delta"] = after - before
    finally:
        driver.close()

    summary = {
        "symbol": symbol,
        "uniprot_id": get_target(symbol)["uniprot_id"],
        "gtex_tissues": report.get("gtex_tissues"),
        "depmap_depends_on": report.get("depmap_depends_on"),
        "hpa_protein_tissues": report.get("hpa_protein_tissues"),
        "uniprot": {k: report.get(f"uniprot_{k}") for k in ("protein", "isoforms", "variants")},
    }
    (PROC / f"step3c_{symbol.lower()}_summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )
    return report


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    ap = argparse.ArgumentParser()
    ap.add_argument("--symbol")
    ap.add_argument("--all-non-cd46", action="store_true")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--refresh", action="store_true")
    args = ap.parse_args()
    from src.knowledge_graph.registry import all_symbols, non_cd46_symbols

    if args.all:
        symbols = all_symbols()
    elif args.all_non_cd46:
        symbols = non_cd46_symbols()
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

    last_after = reports[-1].get("nodes_after") if reports else "?"
    out = _ROOT / "reports" / "step3c_uniprot_gtex_depmap.md"
    lines = [
        "# Step 3c — UniProt + GTEx + DepMap + HPA protein intensity",
        "",
        f"**Aura after Step 3c:** **{last_after} nodes**",
        "",
        "| Gene | Protein | Isoforms | Variants | GTEx | DepMap DEPENDS_ON | HPA protein | Nodes Δ |",
        "|------|---------|----------|----------|------|-------------------|-------------|---------|",
    ]
    for r in reports:
        lines.append(
            f"| {r['symbol']} | {r.get('uniprot_protein')} | {r.get('uniprot_isoforms')} | "
            f"{r.get('uniprot_variants')} | {r.get('gtex_tissues')} | "
            f"{r.get('depmap_depends_on')} | {r.get('hpa_protein_tissues')} | {r.get('nodes_delta')} |"
        )
    lines += [
        "",
        "## Schema",
        "",
        "- `Gene-[:ENCODES]->Protein` (+ capped isoform/variant children)",
        "- `Gene-[:EXPRESSED_IN {source:'GTEx'}]->Tissue`",
        "- `Gene-[:EXPRESSED_IN {source:'HPA', modality:'protein_intensity'}]->Tissue`",
        "- `CellLine-[:DEPENDS_ON]->Gene` (existing CellLines only; CRISPR < -0.5)",
        "",
        "```bash",
        "python scripts/load_gene_uniprot_gtex_depmap.py --all --refresh",
        "```",
        "",
    ]
    out.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {out}")


if __name__ == "__main__":
    main()
