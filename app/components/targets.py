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

# Honest depth labels (not “loaded” which lied once everything was thin-sliced)
_VALID_TIERS = frozenset({"stub", "thin", "medium", "full"})


@lru_cache(maxsize=1)
def load_registry() -> dict[str, Any]:
    with _TARGETS_PATH.open(encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    if "targets" not in data:
        raise ValueError("config/targets.yaml missing 'targets'")
    return data


def list_symbols() -> list[str]:
    return list(load_registry()["targets"].keys())


def default_symbol() -> str:
    return str(load_registry().get("default_target") or "CD46")


def get_target(symbol: str | None = None) -> dict[str, Any]:
    sym = symbol or get_active_symbol()
    targets = load_registry()["targets"]
    if sym not in targets:
        raise KeyError(f"Unknown target: {sym}")
    return {"symbol": sym, **targets[sym]}


def data_tier(symbol: str | None = None) -> str:
    """stub | thin | medium | full — prefers data_tier, falls back to kg_status."""
    t = get_target(symbol)
    raw = str(t.get("data_tier") or "").lower().strip()
    if raw in _VALID_TIERS:
        return raw
    # legacy: kg_status loaded → treat as thin unless case_study (then full)
    status = str(t.get("kg_status", "stub")).lower()
    if status == "loaded":
        return "full" if t.get("case_study") else "thin"
    return "stub"


def is_loaded(symbol: str | None = None) -> bool:
    """True if any graph/CSV slice exists (thin+)."""
    return data_tier(symbol) != "stub"


def is_case_study(symbol: str | None = None) -> bool:
    return bool(get_target(symbol).get("case_study"))


def get_active_symbol() -> str:
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


def _tier_help(tier: str) -> str:
    return {
        "stub": "Registered only — no open-data slice yet",
        "thin": "Starter open data (expression + OT/STRING sample)",
        "medium": (
            "Open-data pack: expression, survival, OT/STRING, trials, PubMed, "
            "ChEMBL/drugs, UniProt, GTEx, DepMap, HPA protein intensity"
        ),
        "full": "Deep case-study depth (CD46 reference modules + full narrative)",
    }.get(tier, tier)


def render_main_target_bar() -> str:
    """Sticky main-area target switcher — always visible above page content."""
    ensure_session_target()
    symbols = list_symbols()
    current = get_active_symbol()
    t = get_target(current)
    tier = data_tier(current)

    st.markdown('<div id="ob-target-bar">', unsafe_allow_html=True)
    left, right = st.columns([3, 2], gap="small")
    with left:
        st.markdown(
            '<div class="ob-tb-label">Research target</div>',
            unsafe_allow_html=True,
        )
        choice = current
        if st.session_state.get("target_segmented") not in symbols:
            st.session_state["target_segmented"] = current
        try:
            choice = st.segmented_control(
                "Research target",
                options=symbols,
                key="target_segmented",
                label_visibility="collapsed",
            )
        except (TypeError, AttributeError):
            try:
                import streamlit_antd_components as sac

                idx = symbols.index(current) if current in symbols else 0
                choice = sac.segmented(
                    items=symbols,
                    index=idx,
                    size="sm",
                    color="blue",
                    use_container_width=True,
                    key="target_sac",
                )
            except ImportError:
                if st.session_state.get("target_radio") not in symbols:
                    st.session_state["target_radio"] = current
                choice = st.radio(
                    "Research target",
                    options=symbols,
                    horizontal=True,
                    key="target_radio",
                    label_visibility="collapsed",
                )
        if choice and choice != current:
            set_active_symbol(str(choice))
            st.rerun()
        active = get_active_symbol()
        t = get_target(active)
        tier = data_tier(active)
    with right:
        tags = ", ".join(t.get("modality_tags") or []) or "—"
        case = " · CD46 deep case study" if is_case_study(active) else ""
        st.markdown(
            f'<div class="ob-tb-meta">'
            f'<strong>{t.get("name", active)}</strong><br/>'
            f'<span class="ob-tb-tier">Data: {tier}</span>'
            f'{case}<br/>'
            f'<span class="ob-tb-ens">{t.get("ensembl_id", "")}</span>'
            f' · {tags}'
            f"</div>",
            unsafe_allow_html=True,
        )
        st.caption(_tier_help(tier))
    st.markdown("</div>", unsafe_allow_html=True)
    return get_active_symbol()


def render_sidebar_target_selector() -> str:
    """Compact sidebar mirror (nav can bury this — main bar is primary)."""
    ensure_session_target()
    current = get_active_symbol()
    t = get_target(current)
    tier = data_tier(current)
    st.markdown(
        f'<div class="ob-side-target">'
        f'<div class="ob-side-target-kicker">Active target</div>'
        f'<div class="ob-side-target-sym">{current}</div>'
        f'<div class="ob-side-target-sub">{t.get("name", "")} · {tier}</div>'
        f"</div>",
        unsafe_allow_html=True,
    )
    return current


def render_stub_gate(*, module: str = "This module") -> bool:
    """Stop if active target has no data slice yet."""
    sym = get_active_symbol()
    if is_loaded(sym):
        return False
    t = get_target(sym)
    st.warning(
        f"**{module}** — target **{sym}** is registered but has no open-data slice yet "
        f"(tier `{data_tier(sym)}`)."
    )
    st.info(
        f"Ensembl `{t.get('ensembl_id')}` · UniProt `{t.get('uniprot_id')}`. "
        "Pick another target in the **Research target** bar, or wait until this gene is sliced."
    )
    return True


def render_case_study_gate(*, module: str = "This module") -> bool:
    """
    Depth banner only — never hard-stops.

    Formerly blocked non-CD46 targets. Now all modules stay open; we warn when
    some charts still use CD46-depth narratives while PARAM work catches up.
    Return value kept for call-site compat (`if gate: st.stop()`); always False.
    """
    sym = get_active_symbol()
    if is_case_study(sym):
        return False
    tier = data_tier(sym)
    st.info(
        f"**{module}** is open for **{sym}** (data tier `{tier}`). "
        "Curated cohort and biomarker depth is expanding across all registered targets."
    )
    return False


def render_depth_banner(*, module: str = "This module") -> None:
    """Explicit non-blocking depth note (preferred over gate for new code)."""
    render_case_study_gate(module=module)

def format_gene_cypher(cypher: str, symbol: str | None = None) -> str:
    sym = symbol or get_active_symbol()
    return (
        cypher.replace("{symbol}", sym)
        .replace("{SYMBOL}", sym)
        .replace("{symbol_high}", f"{sym}_High")
    )


def assert_phase2_targets() -> None:
    """ponytail: registry honesty — tiers + GRPR Ensembl + case_study flag."""
    assert default_symbol() == "CD46"
    assert data_tier("CD46") == "full"
    assert is_case_study("CD46")
    for sym in ("FOLH1", "FAP", "SSTR2", "GRPR"):
        assert data_tier(sym) == "medium", sym
        assert not is_case_study(sym), sym
    assert get_target("GRPR")["ensembl_id"] == "ENSG00000126010"
    assert "FOLH1" in format_gene_cypher(
        "MATCH (g:Gene {symbol: '{symbol}'}) RETURN g", "FOLH1"
    )


if __name__ == "__main__":
    assert_phase2_targets()
    print("phase2_targets_ok")
