"""Resolve writable log dir: Coolify volume first, then local data/logs."""
from __future__ import annotations

from pathlib import Path

_CANDIDATES = (
    Path("/app/data/logs"),
    Path(__file__).resolve().parents[2] / "data" / "logs",
)


def logs_dir() -> Path:
    for p in _CANDIDATES:
        try:
            p.mkdir(parents=True, exist_ok=True)
            probe = p / ".write_ok"
            probe.write_text("ok", encoding="utf-8")
            probe.unlink(missing_ok=True)
            return p
        except OSError:
            continue
    # last resort — may still fail on write
    return _CANDIDATES[-1]
