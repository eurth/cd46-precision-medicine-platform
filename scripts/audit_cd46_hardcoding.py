#!/usr/bin/env python3
"""Inventory CD46 hardcoding in UI/agent code.

Usage:
  python scripts/audit_cd46_hardcoding.py
"""
from __future__ import annotations

import argparse
import re
from collections import Counter
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
_PATTERN = re.compile(r"\bCD46\b|cd46_|225Ac-CD46|FOR46")
_SCAN = [_ROOT / "app" / "pages", _ROOT / "app" / "components", _ROOT / "src" / "agent"]

# Critical surfaces that must stay gene-neutral (zero CD46 literals preferred)
_CRITICAL = {
    "app/pages/4_biomedical_knowledge_graph.py",
    "app/pages/7_kg_query_explorer.py",
    "app/pages/3_survival_outcomes.py",
    "app/pages/5_research_assistant.py",
    "app/pages/13_clinical_strategy_engine.py",
}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--fail-on-critical", action="store_true")
    args = ap.parse_args()

    hits: list[tuple[str, int, str]] = []
    for base in _SCAN:
        if not base.exists():
            continue
        for path in base.rglob("*.py"):
            text = path.read_text(encoding="utf-8", errors="replace")
            rel = path.relative_to(_ROOT).as_posix()
            for i, line in enumerate(text.splitlines(), 1):
                if not _PATTERN.search(line):
                    continue
                # skip streamlit page path strings
                if "pages/" in line and "_cd46_" in line:
                    continue
                hits.append((rel, i, line.strip()[:140]))

    by = Counter(r for r, _, _ in hits)
    crit = [h for h in hits if h[0] in _CRITICAL]
    out = _ROOT / "reports" / "CD46_HARDCODING_INVENTORY.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# CD46 hardcoding inventory",
        "",
        f"**Total hits (app/components/agent):** {len(hits)}",
        f"**Critical-surface hits:** {len(crit)}",
        "",
        "## By file (top)",
        "",
    ]
    for f, n in by.most_common(30):
        mark = " **CRITICAL**" if f in _CRITICAL else ""
        lines.append(f"- `{f}`: {n}{mark}")
    lines += ["", "## Critical surface details", ""]
    for rel, i, snip in crit:
        lines.append(f"- `{rel}:{i}` `{snip}`")
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"total={len(hits)} critical={len(crit)} wrote {out.relative_to(_ROOT)}")
    if args.fail_on_critical and crit:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
