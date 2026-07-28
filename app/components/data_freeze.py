"""Data-freeze banner for research provenance."""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import streamlit as st
import yaml

_ROOT = Path(__file__).resolve().parents[2]
_FREEZE_PATH = _ROOT / "config" / "data_freeze.yaml"


@lru_cache(maxsize=1)
def load_data_freeze() -> dict:
    if not _FREEZE_PATH.exists():
        return {
            "platform_version": "dev",
            "freeze_label": "No freeze file",
            "disclaimer": "Research use only.",
            "sources": [],
        }
    with _FREEZE_PATH.open(encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def render_data_freeze_banner(*, compact: bool = True) -> None:
    """Render a short provenance strip (call near top of research pages)."""
    freeze = load_data_freeze()
    label = freeze.get("freeze_label") or freeze.get("freeze_id") or "unknown"
    version = freeze.get("platform_version") or ""
    disclaimer = (freeze.get("disclaimer") or "").strip()
    sources = freeze.get("sources") or []
    src_bits = " · ".join(
        f"{s.get('name', '?')} ({s.get('access_date', 'n/a')})" for s in sources[:3]
    )
    parts = [
        f'<strong style="color:#CBD5E1;">Data freeze</strong> · {label}',
    ]
    if version:
        parts[0] += f" · v{version}"
    if src_bits and not compact:
        parts.append(src_bits)
    if disclaimer:
        parts.append(f'<span style="color:#4E637A;">{disclaimer}</span>')
    inner = "<br/>".join(parts)
    st.markdown(
        '<div style="margin:8px 0 18px;padding:10px 14px;border:1px solid #16243C;'
        'border-radius:8px;background:#0B1526;font-size:12px;line-height:1.45;color:#7A90AB;">'
        f"{inner}</div>",
        unsafe_allow_html=True,
    )


def assert_targets_registry() -> None:
    """ponytail: one runnable check — registry loads and GRPR Ensembl is correct."""
    path = _ROOT / "config" / "targets.yaml"
    with path.open(encoding="utf-8") as f:
        reg = yaml.safe_load(f)
    assert reg["default_target"] == "CD46"
    assert reg["targets"]["CD46"]["kg_status"] == "loaded"
    assert reg["targets"]["GRPR"]["ensembl_id"] == "ENSG00000126010"
    freeze = load_data_freeze()
    assert freeze.get("freeze_id")


if __name__ == "__main__":
    assert_targets_registry()
    print("phase1_registry_ok")
