"""Minimal self-check for feedback + LLM daily cap (no Streamlit)."""
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "app"))

# Force local logs dir via env-free monkey of candidates: write into tmp by
# pointing cwd-relative data/logs — components use /app then project data/logs.
from components import log_paths  # noqa: E402


def main() -> None:
    with tempfile.TemporaryDirectory() as td:
        fake = Path(td) / "logs"
        fake.mkdir()
        log_paths._CANDIDATES = (fake,)  # type: ignore[attr-defined]

        from components.feedback import append_feedback, load_feedback
        from components import llm_rate_limit as rl

        append_feedback(message="hello", category="bug", page="test", target="CD46")
        rows = load_feedback()
        assert len(rows) == 1 and rows[0]["message"] == "hello"

        os.environ["LLM_DAILY_CAP"] = "2"
        ok1, _ = rl.check_and_increment("t")
        ok2, _ = rl.check_and_increment("t")
        ok3, msg = rl.check_and_increment("t")
        assert ok1 and ok2 and not ok3
        assert "limit" in msg.lower()
        assert rl.usage_today("t") == 2
        print("OK feedback + llm_rate_limit")


if __name__ == "__main__":
    main()
