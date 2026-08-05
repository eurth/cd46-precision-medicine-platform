"""Target registry helpers — symbols come from config/targets.yaml only."""
from __future__ import annotations

from src.knowledge_graph.target_slice import get_target, load_registry


def all_symbols() -> list[str]:
    """Stable order as declared in targets.yaml."""
    return list(load_registry()["targets"].keys())


def non_cd46_symbols() -> list[str]:
    return [s for s in all_symbols() if s.upper() != "CD46"]


def case_study_symbol() -> str:
    reg = load_registry()
    default = reg.get("default_target") or "CD46"
    for sym, meta in (reg.get("targets") or {}).items():
        if meta.get("case_study"):
            return sym
    return default


def pending_symbols() -> list[str]:
    return [
        s
        for s, m in load_registry()["targets"].items()
        if (m.get("kg_status") or "").lower() in ("pending", "stub", "")
    ]


__all__ = [
    "all_symbols",
    "non_cd46_symbols",
    "case_study_symbol",
    "pending_symbols",
    "get_target",
    "load_registry",
]
