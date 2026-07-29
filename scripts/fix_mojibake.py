"""Fix mojibake: UTF-8 bytes that were decoded as latin-1/cp1252 and saved."""
from __future__ import annotations

import argparse
from pathlib import Path


def fix_mojibake(text: str) -> str:
    """Best-effort: encode as latin-1 then decode utf-8 for broken sequences."""
    # Common replacements when full round-trip fails
    manual = {
        "â€”": "—",
        "â€“": "–",
        "â€˜": "‘",
        "â€™": "’",
        "â€œ": "“",
        "â€": "”",
        "Â·": "·",
        "Ã—": "×",
        "â†‘": "↑",
        "â†’": "→",
        "â†“": "↓",
        "â†”": "↔",
        "â‰¥": "≥",
        "â‰¤": "≤",
        "â‰ˆ": "≈",
        "Â": "",  # stray from Â· already handled; leftover Â
        "Î±": "α",
        "â‚‚": "₂",
        "âœ…": "✅",
        "âš¡": "⚡",
        "âŒ": "❌",
        "â­•": "⭕",
        "â¬‡ï¸": "⬇️",
        "â¬†ï¸": "⬆️",
        "âš ï¸": "⚠️",
        "ðŸŽ¯": "🎯",
        "ðŸŒ": "🌍",
        "ðŸ”—": "🔗",
        "ðŸ“‹": "📋",
        "ðŸ§¬": "🧬",
        "ðŸ“š": "📚",
        "ðŸ”": "🔍",
        "ðŸ“¥": "📥",
        "ðŸ“Š": "📊",
        "ðŸ¥": "🏥",
        "ðŸ”¬": "🔬",
        "ðŸ”´": "🔴",
        "ðŸŸ ": "🟠",
        "ðŸŸ¡": "🟡",
        "ðŸŸ¢": "🟢",
        "ðŸ”¶": "🔷",
        "ðŸ’¡": "💡",
        "ðŸ“ˆ": "📈",
    }
    out = text
    # Prefer long keys first
    for bad, good in sorted(manual.items(), key=lambda kv: -len(kv[0])):
        out = out.replace(bad, good)
    # Attempt latin-1 → utf-8 for remaining high bytes in runs
    try:
        repaired = out.encode("latin-1").decode("utf-8")
        # Only accept if it reduces mojibake markers
        if repaired.count("ðŸ") + repaired.count("â€") < out.count("ðŸ") + out.count("â€"):
            out = repaired
    except (UnicodeDecodeError, UnicodeEncodeError):
        pass
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("files", nargs="+")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    for f in args.files:
        p = Path(f)
        raw = p.read_text(encoding="utf-8-sig")
        fixed = fix_mojibake(raw)
        before = raw.count("ðŸ") + raw.count("â€") + raw.count("Â·")
        after = fixed.count("ðŸ") + fixed.count("â€") + fixed.count("Â·")
        print(f"{p}: mojibake markers {before} -> {after}")
        if not args.dry_run and fixed != raw:
            p.write_text(fixed, encoding="utf-8")
            print(f"  wrote {p}")


if __name__ == "__main__":
    main()
