"""Daily LLM call cap — file-backed counter under data/logs.

Env: LLM_DAILY_CAP (default 40). Keyed by UTC date + optional session id.
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path

from components.log_paths import logs_dir

_STORE = "llm_rate_limit.json"


def daily_cap() -> int:
    raw = (os.environ.get("LLM_DAILY_CAP") or "40").strip()
    try:
        return max(0, int(raw))
    except ValueError:
        return 40


def _today() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def _path() -> Path:
    return logs_dir() / _STORE


def _load() -> dict:
    p = _path()
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def _save(data: dict) -> None:
    p = _path()
    p.write_text(json.dumps(data, indent=0), encoding="utf-8")


def usage_today(bucket: str = "global") -> int:
    data = _load()
    day = data.get(_today()) or {}
    return int(day.get(bucket, 0))


def check_and_increment(bucket: str = "global") -> tuple[bool, str]:
    """Return (allowed, message). Increments only when allowed."""
    cap = daily_cap()
    if cap <= 0:
        return False, "LLM daily cap is 0 (disabled). Set LLM_DAILY_CAP > 0."
    used = usage_today(bucket)
    if used >= cap:
        return (
            False,
            f"Daily LLM limit reached ({used}/{cap}). Try again after UTC midnight.",
        )
    data = _load()
    day = _today()
    slot = data.setdefault(day, {})
    slot[bucket] = used + 1
    # ponytail: keep only today + yesterday; upgrade to Redis if multi-instance
    keep = {k: v for k, v in data.items() if k >= day or k == _yesterday()}
    keep[day] = slot
    _save(keep)
    return True, f"{used + 1}/{cap} LLM calls today (UTC)"


def _yesterday() -> str:
    from datetime import timedelta

    return (datetime.now(timezone.utc) - timedelta(days=1)).strftime("%Y-%m-%d")
