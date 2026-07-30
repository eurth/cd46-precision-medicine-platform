"""C2–C4 coverage slices: trials summary, GTEx dosimetry, GENIE co-occurrence."""
from __future__ import annotations

import json
import logging
from pathlib import Path

import pandas as pd
import yaml

log = logging.getLogger(__name__)

_ROOT = Path(__file__).resolve().parents[2]
PROC = _ROOT / "data" / "processed"
RAW = _ROOT / "data" / "raw" / "apis"
TARGETS = _ROOT / "config" / "targets.yaml"

GENIE = PROC / "genie_full_cohort.parquet"
COGENES = ["AR", "TP53", "PTEN", "FOLH1", "CD46"]


def list_medium_targets() -> list[str]:
    with TARGETS.open(encoding="utf-8") as f:
        reg = yaml.safe_load(f) or {}
    return [
        s for s, m in (reg.get("targets") or {}).items()
        if (m or {}).get("data_tier") in ("medium", "full")
    ]


def build_trials_summary(symbol: str) -> pd.DataFrame:
    """Parse clinicaltrials_{gene}.json → processed CSV (C3)."""
    raw_path = RAW / f"clinicaltrials_{symbol.lower()}.json"
    if not raw_path.exists():
        return pd.DataFrame()
    studies = json.loads(raw_path.read_text(encoding="utf-8"))
    rows: list[dict] = []
    for s in studies[:50]:
        proto = s.get("protocolSection") or {}
        ident = proto.get("identificationModule") or {}
        status = proto.get("statusModule") or {}
        design = proto.get("designModule") or {}
        desc = proto.get("descriptionModule") or {}
        phases = design.get("phases") or []
        phase = phases[0] if phases else "NA"
        rows.append(
            {
                "nct_id": ident.get("nctId", ""),
                "title": (ident.get("briefTitle") or ident.get("officialTitle") or "")[:200],
                "status": status.get("overallStatus", ""),
                "phase": phase,
                "condition": (desc.get("briefSummary") or "")[:120],
                "gene_symbol": symbol.upper(),
            }
        )
    df = pd.DataFrame(rows)
    out = PROC / f"{symbol.lower()}_trials_summary.csv"
    if not df.empty:
        df.to_csv(out, index=False)
        log.info("Wrote %s (%d trials)", out.name, len(df))
    return df


def build_gtex_dosimetry(symbol: str) -> pd.DataFrame:
    """Top GTEx normal tissues for dosimetry context (C2)."""
    p = PROC / f"gtex_{symbol.lower()}_normal.csv"
    if not p.exists():
        return pd.DataFrame()
    df = pd.read_csv(p)
    med_col = next((c for c in ("median_tpm", "mean_tpm") if c in df.columns), None)
    tissue_col = next((c for c in ("tissue_site", "tissue_site_detail", "tissue") if c in df.columns), None)
    if not med_col or not tissue_col:
        return pd.DataFrame()
    out_df = (
        df[[tissue_col, med_col]]
        .rename(columns={tissue_col: "tissue", med_col: "median_tpm"})
        .sort_values("median_tpm", ascending=False)
        .head(15)
    )
    out_df["gene_symbol"] = symbol.upper()
    out_path = PROC / f"{symbol.lower()}_gtex_dosimetry.csv"
    out_df.to_csv(out_path, index=False)
    log.info("Wrote %s", out_path.name)
    return out_df


def build_genie_cooccurrence(symbol: str) -> pd.DataFrame:
    """Mutation co-occurrence from GENIE (C4) — genes with Mutated columns only."""
    if not GENIE.exists():
        return pd.DataFrame()
    gene_col = f"{symbol.upper()}_Mutated"
    full = pd.read_parquet(GENIE)
    if gene_col not in full.columns:
        log.info("No GENIE column %s — skip co-occurrence", gene_col)
        return pd.DataFrame()
    rows: list[dict] = []
    base = full[gene_col].fillna(0).astype(bool)
    n_pos = int(base.sum())
    for other in COGENES:
        if other.upper() == symbol.upper():
            continue
        ocol = f"{other}_Mutated"
        if ocol not in full.columns:
            continue
        both = base & full[ocol].fillna(0).astype(bool)
        n_both = int(both.sum())
        rows.append(
            {
                "gene_symbol": symbol.upper(),
                "co_gene": other,
                "n_gene_positive": n_pos,
                "n_co_positive": int(full[ocol].fillna(0).astype(bool).sum()),
                "n_both": n_both,
                "pct_of_gene_pos": round(100 * n_both / n_pos, 2) if n_pos else 0.0,
            }
        )
    out_df = pd.DataFrame(rows)
    out_path = PROC / f"{symbol.lower()}_genie_cooccurrence.csv"
    if not out_df.empty:
        out_df.to_csv(out_path, index=False)
        log.info("Wrote %s", out_path.name)
    return out_df


def build_coverage(symbol: str) -> dict[str, int]:
    return {
        "trials": len(build_trials_summary(symbol)),
        "gtex_dosimetry": len(build_gtex_dosimetry(symbol)),
        "genie_cooc": len(build_genie_cooccurrence(symbol)),
    }
