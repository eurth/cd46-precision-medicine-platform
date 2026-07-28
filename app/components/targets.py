"""Active research target from config/targets.yaml + Streamlit session."""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

import streamlit as st
import yaml

_ROOT = Path(__file__).resolve().parents[2]
_TARGETS_PATH = _ROOT / "config" / "targets.yaml"
_SESSION_KEY = "active_target"


@lru_cache(maxsize=1)
def load_registry() -> dict[str, Any]:
    with _TARGETS_PATH.open(encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    if "targets" not in data:
        raise ValueError("config/targets.yaml missing 'targets'")
    return data


def list_symbols() -> list[str]:
    reg = load_registry()
    return list(reg["targets"].keys())


def default_symbol() -> str:
    return str(load_registry().get("default_target") or "CD46")


def get_target(symbol: str | None = None) -> dict[str, Any]:
    sym = symbol or get_active_symbol()
    targets = load_registry()["targets"]
    if sym not in targets:
        raise KeyError(f"Unknown target: {sym}")
    return {"symbol": sym, **targets[sym]}


def is_loaded(symbol: str | None = None) -> bool:
    t = get_target(symbol)
    return str(t.get("kg_status", "stub")).lower() == "loaded"


def get_active_symbol() -> str:
    """Prefer Streamlit session; fall back to default."""
    try:
        sym = st.session_state.get(_SESSION_KEY)
        if sym and sym in load_registry()["targets"]:
            return str(sym)
    except Exception:
        pass
    return default_symbol()


def set_active_symbol(symbol: str) -> None:
    if symbol not in load_registry()["targets"]:
        raise KeyError(symbol)
    st.session_state[_SESSION_KEY] = symbol


def ensure_session_target() -> str:
    if _SESSION_KEY not in st.session_state:
        st.session_state[_SESSION_KEY] = default_symbol()
    elif st.session_state[_SESSION_KEY] not in load_registry()["targets"]:
        st.session_state[_SESSION_KEY] = default_symbol()
    return str(st.session_state[_SESSION_KEY])


def render_sidebar_target_selector() -> str:
    """Sidebar control — call from streamlit_app.py inside st.sidebar."""
    ensure_session_target()
    symbols = list_symbols()
    labels = []
    for s in symbols:
        t = get_target(s)
        tag = "loaded" if is_loaded(s) else "stub"
        labels.append(f"{s} ({tag})")
    current = get_active_symbol()
    try:
        idx = symbols.index(current)
    except ValueError:
        idx = 0
    choice = st.selectbox(
        "Research target",
        options=symbols,
        index=idx,
        format_func=lambda s: f"{s} · {'loaded' if is_loaded(s) else 'stub'}",
        help="Loaded = data in Aura + processed CSVs. Stub = registered, not sliced yet.",
        key="target_selector_box",
    )
    if choice != current:
        set_active_symbol(choice)
        st.rerun()
    t = get_target(choice)
    st.caption(f"{t.get('name', choice)} · {t.get('ensembl_id', '')}")
    return choice


def render_stub_gate(*, module: str = "This module") -> bool:
    """
    If active target is not loaded, show empty state and return True (caller should stop).
    """
    sym = get_active_symbol()
    if is_loaded(sym):
        return False
    t = get_target(sym)
    st.warning(
        f"**{module}** — target **{sym}** is registered but not loaded yet "
        f"(`kg_status: {t.get('kg_status', 'stub')}`)."
    )
    st.info(
        f"Ensembl `{t.get('ensembl_id')}` · UniProt `{t.get('uniprot_id')}`. "
        "Switch the sidebar **Research target** back to **CD46** for live case-study data, "
        "or wait until Phase 4 ETL slices land for this gene."
    )
    st.markdown(
        "- No CD46 CSV/graph bleed-through for stub targets.\n"
        "- KG Query Explorer still allows free Cypher; gene templates use this symbol "
        "(expect empty results until the gene is in Aura)."
    )
    return True


def format_gene_cypher(cypher: str, symbol: str | None = None) -> str:
    """Replace {symbol} / {SYMBOL} placeholders in Cypher templates."""
    sym = symbol or get_active_symbol()
    return (
        cypher.replace("{symbol}", sym)
        .replace("{SYMBOL}", sym)
        .replace("{symbol_high}", f"{sym}_High")
    )


def assert_phase2_targets() -> None:
    """ponytail: registry — five loaded seeds + GRPR Ensembl correct."""
    assert default_symbol() == "CD46"
    for sym in ("CD46", "FOLH1", "FAP", "SSTR2", "GRPR"):
        assert is_loaded(sym), sym
    assert get_target("GRPR")["ensembl_id"] == "ENSG00000126010"
    sample = format_gene_cypher("MATCH (g:Gene {symbol: '{symbol}'}) RETURN g")
    assert "CD46" in sample or "{symbol}" not in sample


if __name__ == "__main__":
    assert_phase2_targets()
    print("phase2_targets_ok")
