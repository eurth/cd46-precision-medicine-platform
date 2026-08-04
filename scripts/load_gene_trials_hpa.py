"""Step 3 — per-gene ClinicalTrials + HPA into Aura (open-data recipe parity).

Usage (laptop, .env Neo4j):
  python scripts/load_gene_trials_hpa.py --symbol FOLH1
  python scripts/load_gene_trials_hpa.py --all-non-cd46

Schema additions (gene-aware, does not overwrite CD46 Disease props):
  (:ClinicalTrial)-[:TARGETS_GENE]->(:Gene)
  (:Gene)-[:EXPRESSED_IN {source:'HPA', modality:'rna_ntpm'}]->(:Tissue)
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import sys
import time
from pathlib import Path
from typing import Any

import requests
import yaml
from dotenv import load_dotenv

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT))
load_dotenv(_ROOT / ".env")

log = logging.getLogger(__name__)
RAW = _ROOT / "data" / "raw" / "apis"
HPA_RAW = _ROOT / "data" / "raw" / "hpa"
PROC = _ROOT / "data" / "processed"
CT_URL = "https://clinicaltrials.gov/api/v2/studies"


def get_target(symbol: str) -> dict[str, Any]:
    with (_ROOT / "config" / "targets.yaml").open(encoding="utf-8") as f:
        reg = yaml.safe_load(f) or {}
    t = (reg.get("targets") or {}).get(symbol)
    if not t:
        raise KeyError(symbol)
    return {"symbol": symbol, **t}


def _driver():
    from neo4j import GraphDatabase

    uri = os.environ.get("NEO4J_URI")
    user = os.environ.get("NEO4J_USERNAME", "neo4j")
    pwd = os.environ.get("NEO4J_PASSWORD")
    if not uri or not pwd:
        raise RuntimeError("NEO4J_URI / NEO4J_PASSWORD required")
    d = GraphDatabase.driver(uri, auth=(user, pwd))
    d.verify_connectivity()
    return d


# Extra CT.gov terms per gene (RLT / ADC / PET) — keep short; pageSize still caps results
_TRIAL_EXTRA: dict[str, list[str]] = {
    "CD46": ["FOR46", "YS5", "radioligand"],
    "FOLH1": ["PSMA", "177Lu", "225Ac", "Pluvicto", "Pylarify"],
    "FAP": ["FAPI", "FAP-2286", "177Lu"],
    "SSTR2": ["DOTATATE", "Lutathera", "177Lu", "octreotide"],
    "GRPR": ["bombesin", "RM2", "NeoBOMB1", "68Ga"],
}


def _trial_query(t: dict) -> str:
    sym = t["symbol"]
    aliases = t.get("aliases") or []
    parts = [sym] + [a for a in aliases if a and a.upper() != sym.upper()]
    parts += _TRIAL_EXTRA.get(sym, [])
    # Dedupe case-insensitively, cap clause length
    seen: set[str] = set()
    uniq: list[str] = []
    for p in parts:
        k = p.upper()
        if k in seen:
            continue
        seen.add(k)
        uniq.append(p)
    or_clause = " OR ".join(uniq[:8])
    return f"({or_clause}) AND (cancer OR neoplasm OR tumor)"


def fetch_trials(
    symbol: str,
    *,
    refresh: bool = False,
    page_size: int = 100,
    max_trials: int = 100,
) -> list[dict]:
    t = get_target(symbol)
    out = RAW / f"clinicaltrials_{symbol.lower()}.json"
    RAW.mkdir(parents=True, exist_ok=True)
    if out.exists() and not refresh:
        log.info("Using cached trials %s", out.name)
        return json.loads(out.read_text(encoding="utf-8"))[:max_trials]

    q = _trial_query(t)
    log.info("Fetching ClinicalTrials.gov: %s (pageSize=%d)", q, page_size)
    r = requests.get(
        CT_URL,
        params={"query.term": q, "pageSize": page_size, "format": "json"},
        timeout=60,
    )
    r.raise_for_status()
    studies = r.json().get("studies", [])[:max_trials]
    out.write_text(json.dumps(studies, indent=2), encoding="utf-8")
    log.info("Saved %d trials → %s", len(studies), out)
    return studies


def load_trials(session, symbol: str, studies: list[dict]) -> int:
    trial_cypher = """
    MERGE (t:ClinicalTrial {nct_id: $nct_id})
    SET t.title = $title,
        t.status = $status,
        t.phase = $phase,
        t.sponsor = $sponsor,
        t.start_date = $start_date,
        t.condition = $condition,
        t.intervention = $intervention,
        t.source = 'ClinicalTrials.gov',
        t.query_gene = $gene
    WITH t
    MATCH (g:Gene {symbol: $gene})
    MERGE (t)-[r:TARGETS_GENE]->(g)
    ON CREATE SET r.source = 'ClinicalTrials.gov'
    """
    disease_cypher = """
    MATCH (t:ClinicalTrial {nct_id: $nct_id})
    MATCH (d:Disease)
    WHERE ($tcga <> '' AND d.tcga_code = $tcga)
       OR ($hint <> '' AND toLower(coalesce(d.name, '')) CONTAINS $hint)
    WITH t, d LIMIT 3
    MERGE (t)-[r:INVESTIGATES]->(d)
    ON CREATE SET r.source = 'ClinicalTrials.gov', r.via = 'condition_heuristic'
    """
    # crude condition → TCGA map for common cancers
    hint_map = [
        ("prostate", "PRAD", "prostate"),
        ("breast", "BRCA", "breast"),
        ("lung", "LUAD", "lung"),
        ("ovarian", "OV", "ovarian"),
        ("ovary", "OV", "ovary"),
        ("bladder", "BLCA", "bladder"),
        ("pancrea", "PAAD", "pancrea"),
        ("colorec", "COAD", "colorec"),
        ("colon", "COAD", "colon"),
        ("glioma", "LGG", "glioma"),
        ("melanoma", "SKCM", "melanoma"),
        ("kidney", "KIRC", "kidney"),
        ("renal", "KIRC", "renal"),
        ("neuroendocrine", "", "neuroendocrine"),
        ("somatostatin", "", "somatostatin"),
    ]
    n = 0
    for trial in studies:
        proto = trial.get("protocolSection", {})
        ident = proto.get("identificationModule", {})
        status_mod = proto.get("statusModule", {})
        design = proto.get("designModule", {})
        sponsor_mod = proto.get("sponsorCollaboratorsModule", {})
        cond_mod = proto.get("conditionsModule", {})
        arms = proto.get("armsInterventionsModule", {})
        nct_id = ident.get("nctId", "")
        if not nct_id:
            continue
        conditions = cond_mod.get("conditions", []) or []
        interventions = arms.get("interventions", []) or []
        intervention_names = [i.get("name", "") for i in interventions if isinstance(i, dict)]
        session.run(
            trial_cypher,
            nct_id=nct_id,
            title=ident.get("briefTitle", ""),
            status=status_mod.get("overallStatus", ""),
            phase=", ".join(design.get("phases", []) or []),
            sponsor=(sponsor_mod.get("leadSponsor") or {}).get("name", ""),
            start_date=(status_mod.get("startDateStruct") or {}).get("date", ""),
            condition=", ".join(conditions[:3]),
            intervention=", ".join(intervention_names[:2]),
            gene=symbol,
        )
        cond_blob = " ".join(conditions).lower()
        linked = False
        for needle, tcga, hint in hint_map:
            if needle in cond_blob:
                session.run(disease_cypher, nct_id=nct_id, tcga=tcga, hint=hint)
                linked = True
                break
        if not linked and conditions:
            # still try loose name match on first condition token
            token = conditions[0].split()[0].lower()
            session.run(disease_cypher, nct_id=nct_id, tcga="", hint=token)
        n += 1
    log.info("%s ClinicalTrial: %d", symbol, n)
    return n


def fetch_hpa(symbol: str, *, refresh: bool = False) -> dict:
    t = get_target(symbol)
    ens = t["ensembl_id"]
    out = HPA_RAW / f"{symbol.lower()}_protein_expression.json"
    HPA_RAW.mkdir(parents=True, exist_ok=True)
    if out.exists() and not refresh:
        log.info("Using cached HPA %s", out.name)
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


def _ntpm_rows(blob: Any, tissue_type: str) -> list[dict]:
    rows = []
    if not isinstance(blob, dict):
        return rows
    for tissue, val in blob.items():
        try:
            ntpm = float(val)
        except (TypeError, ValueError):
            continue
        rows.append(
            {
                "tissue": tissue,
                "type": tissue_type,
                "ntpm": ntpm,
                "staining_intensity": "",
                "data_source": "HPA_rna",
            }
        )
    return rows


def process_hpa_to_csv(symbol: str, raw: dict) -> Path:
    """Prefer RNA tissue / cell-type nTPM dicts from HPA JSON (IHC Tissue dict often absent in v24)."""
    records: list[dict] = []
    for key, ttype in (
        ("RNA tissue specific nTPM", "normal"),
        ("RNA single cell type specific nCPM", "single_cell"),
        ("RNA blood cell specific nTPM", "blood"),
    ):
        records.extend(_ntpm_rows(raw.get(key), ttype))

    # Always capture summary props even if no tissue dict
    summary = {
        "gene": symbol,
        "ensembl": raw.get("Ensembl", ""),
        "rna_tissue_specificity": raw.get("RNA tissue specificity", ""),
        "rna_tissue_distribution": raw.get("RNA tissue distribution", ""),
        "rna_cancer_specificity": raw.get("RNA cancer specificity", ""),
        "protein_class": ";".join(raw.get("Protein class") or [])
        if isinstance(raw.get("Protein class"), list)
        else str(raw.get("Protein class") or ""),
    }
    sum_path = PROC / f"hpa_{symbol.lower()}_summary.json"
    PROC.mkdir(parents=True, exist_ok=True)
    sum_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    path = PROC / f"hpa_{symbol.lower()}_rna_tissue.csv"
    import pandas as pd

    df = pd.DataFrame(records)
    if df.empty:
        # one row so we still have a file + can store gene-level HPA props on Gene
        df = pd.DataFrame(
            [
                {
                    "tissue": "_summary_only",
                    "type": "meta",
                    "ntpm": None,
                    "staining_intensity": "",
                    "data_source": "HPA_meta",
                }
            ]
        )
    df.to_csv(path, index=False)
    log.info("HPA CSV %s rows → %s", len(df), path.name)
    return path


def load_hpa(session, symbol: str, raw: dict, csv_path: Path) -> int:
    import pandas as pd

    summary_cypher = """
    MATCH (g:Gene {symbol: $gene})
    SET g.hpa_rna_tissue_specificity = $spec,
        g.hpa_rna_tissue_distribution = $dist,
        g.hpa_rna_cancer_specificity = $cancer_spec,
        g.hpa_ensembl = $ensembl,
        g.hpa_source = 'Human Protein Atlas'
    """
    session.run(
        summary_cypher,
        gene=symbol,
        spec=str(raw.get("RNA tissue specificity") or ""),
        dist=str(raw.get("RNA tissue distribution") or ""),
        cancer_spec=str(raw.get("RNA cancer specificity") or ""),
        ensembl=str(raw.get("Ensembl") or ""),
    )

    df = pd.read_csv(csv_path)
    tissue_cypher = """
    MERGE (t:Tissue {name: $name, type: $type})
    ON CREATE SET t.source = 'HPA'
    WITH t
    MATCH (g:Gene {symbol: $gene})
    MERGE (g)-[r:EXPRESSED_IN]->(t)
    SET r.source = 'HPA',
        r.modality = 'rna_ntpm',
        r.ntpm = $ntpm,
        r.gene_symbol = $gene
    """
    n = 0
    for _, row in df.iterrows():
        tissue = str(row.get("tissue", "")).strip()
        if not tissue or tissue == "_summary_only":
            continue
        ntpm = row.get("ntpm")
        try:
            ntpm_f = float(ntpm) if ntpm == ntpm and ntpm is not None else None
        except (TypeError, ValueError):
            ntpm_f = None
        session.run(
            tissue_cypher,
            name=tissue,
            type=str(row.get("type") or "normal"),
            gene=symbol,
            ntpm=ntpm_f,
        )
        n += 1
    log.info("%s HPA EXPRESSED_IN tissues: %d", symbol, n)
    return n


def run_symbol(
    symbol: str,
    *,
    refresh: bool = False,
    page_size: int = 100,
    max_trials: int = 100,
) -> dict:
    symbol = symbol.upper()
    get_target(symbol)  # validate
    report: dict[str, Any] = {"symbol": symbol}
    studies = fetch_trials(symbol, refresh=refresh, page_size=page_size, max_trials=max_trials)
    report["trials_fetched"] = len(studies)
    hpa = fetch_hpa(symbol, refresh=refresh)
    csv_path = process_hpa_to_csv(symbol, hpa)
    report["hpa_csv"] = str(csv_path.relative_to(_ROOT))

    driver = _driver()
    try:
        with driver.session() as session:
            before = session.run("MATCH (n) RETURN count(n) AS c").single()["c"]
            # ensure Gene exists
            session.run("MERGE (g:Gene {symbol: $s})", s=symbol)
            report["trials_loaded"] = load_trials(session, symbol, studies)
            report["hpa_tissues"] = load_hpa(session, symbol, hpa, csv_path)
            after = session.run("MATCH (n) RETURN count(n) AS c").single()["c"]
            report["nodes_before"] = before
            report["nodes_after"] = after
            report["nodes_delta"] = after - before
    finally:
        driver.close()
    return report


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    ap = argparse.ArgumentParser()
    ap.add_argument("--symbol")
    ap.add_argument("--all-non-cd46", action="store_true")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--refresh", action="store_true")
    ap.add_argument("--page-size", type=int, default=100, help="ClinicalTrials.gov pageSize")
    ap.add_argument("--max-trials", type=int, default=100, help="Max trials per gene")
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
            time.sleep(1.0)  # be polite to CT.gov / HPA
        reports.append(
            run_symbol(
                sym,
                refresh=args.refresh,
                page_size=args.page_size,
                max_trials=args.max_trials,
            )
        )
        print(json.dumps(reports[-1], indent=2))

    out = _ROOT / "reports" / "step3_trials_hpa.md"
    lines = [
        "# Step 3 — ClinicalTrials + HPA per target",
        "",
        "| Gene | Trials fetched | Trials loaded | HPA tissues | Nodes Δ |",
        "|------|----------------|---------------|-------------|---------|",
    ]
    for r in reports:
        lines.append(
            f"| {r['symbol']} | {r.get('trials_fetched')} | {r.get('trials_loaded')} | "
            f"{r.get('hpa_tissues')} | {r.get('nodes_delta')} |"
        )
    lines += [
        "",
        "Schema: `ClinicalTrial-[:TARGETS_GENE]->Gene`, `Gene-[:EXPRESSED_IN {source:HPA}]->Tissue`.",
        "",
    ]
    out.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {out}")


if __name__ == "__main__":
    main()
