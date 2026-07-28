"""Static audit of Streamlit pages for mojibake + duplicate widgets."""
from __future__ import annotations

import ast
import re
from pathlib import Path

PAGES = Path("app/pages")
MOJI = re.compile(r"(ðŸ|â€|Â·|Ã—|â†|â¬|âš|âœ|Î±|â”)")


def widget_keys(tree: ast.AST) -> list[str]:
    keys = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            for kw in node.keywords:
                if kw.arg == "key" and isinstance(kw.value, ast.Constant) and isinstance(kw.value.value, str):
                    keys.append(kw.value.value)
    return keys


def main() -> None:
    rows = []
    for p in sorted(PAGES.glob("*.py")):
        raw = p.read_bytes()
        bom = raw.startswith(b"\xef\xbb\xbf")
        text = raw.decode("utf-8-sig", errors="replace")
        moji_n = len(MOJI.findall(text))
        try:
            tree = ast.parse(text)
            parse_ok = True
            keys = widget_keys(tree)
        except SyntaxError as e:
            parse_ok = False
            keys = []
            print(f"SYNTAX {p.name}: {e}")
        from collections import Counter

        dup_keys = [k for k, c in Counter(keys).items() if c > 1]
        heroes = text.count("page_hero(")
        page_docs = len(re.findall(r'^"""Page ', text, re.M))
        rows.append(
            {
                "page": p.name,
                "bom": bom,
                "moji": moji_n,
                "parse_ok": parse_ok,
                "dup_keys": dup_keys,
                "page_hero": heroes,
                "page_docstrings": page_docs,
                "lines": text.count("\n") + 1,
            }
        )

    print("| page | bom | moji | parse | dup_keys | heroes | docs | lines |")
    print("|------|-----|------|-------|----------|--------|------|-------|")
    for r in rows:
        dups = ",".join(r["dup_keys"][:5]) + ("…" if len(r["dup_keys"]) > 5 else "")
        print(
            f"| {r['page']} | {r['bom']} | {r['moji']} | {r['parse_ok']} | "
            f"{dups or '—'} | {r['page_hero']} | {r['page_docstrings']} | {r['lines']} |"
        )


if __name__ == "__main__":
    main()
