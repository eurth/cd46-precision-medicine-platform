import re
from pathlib import Path

p = Path("app/pages/5_research_assistant.py")
text = p.read_text(encoding="utf-8")
text = re.sub(
    r"'<div class=\"ob-tab-intro ob-tab-intro-neutral\">\"\s*\n\s*\"(padding:[^\"]+)'>\"",
    r"'<div class=\"ob-tab-intro ob-tab-intro-neutral\" style=\"\1\">'",
    text,
)
p.write_text(text, encoding="utf-8")
print("fixed")
