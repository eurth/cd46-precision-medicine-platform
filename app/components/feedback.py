"""Sidebar feedback → append-only JSONL on the data volume."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import streamlit as st

from components.log_paths import logs_dir

_FEEDBACK_FILE = "feedback.jsonl"


def feedback_path() -> Path:
    return logs_dir() / _FEEDBACK_FILE


def append_feedback(
    *,
    message: str,
    category: str,
    page: str = "",
    target: str = "",
    session_id: str = "",
) -> None:
    row = {
        "ts": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "category": category,
        "message": message.strip(),
        "page": page,
        "target": target,
        "session_id": session_id,
    }
    path = feedback_path()
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")


def load_feedback(limit: int = 500) -> list[dict]:
    path = feedback_path()
    if not path.exists():
        return []
    rows: list[dict] = []
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return rows[-limit:]


def render_sidebar_feedback() -> None:
    """Call inside st.sidebar after target selector."""
    with st.expander("Feedback", expanded=False):
        cat = st.selectbox(
            "Type",
            ["bug", "data", "ux", "idea", "other"],
            key="fb_cat",
        )
        msg = st.text_area(
            "Message",
            max_chars=2000,
            placeholder="What broke / what's missing / what would help…",
            key="fb_msg",
            height=80,
        )
        if st.button("Send feedback", key="fb_send", use_container_width=True):
            if not (msg or "").strip():
                st.warning("Write a short message first.")
                return
            try:
                from components.targets import get_active_symbol

                target = get_active_symbol()
            except Exception:
                target = ""
            sid = st.session_state.get("session_id", "") or ""
            append_feedback(
                message=msg,
                category=cat,
                page=st.session_state.get("current_page", ""),
                target=target,
                session_id=str(sid),
            )
            st.success("Thanks — logged.")
