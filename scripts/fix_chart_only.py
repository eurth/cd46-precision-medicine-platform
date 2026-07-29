from pathlib import Path

CHART = [
    ('paper_bgcolor="#0f172a"', 'paper_bgcolor="#FFFFFF"'),
    ('plot_bgcolor="#0f172a"', 'plot_bgcolor="#EEF2F7"'),
    ('"bgcolor": "#0f172a"', '"bgcolor": "#FFFFFF"'),
    ('bgcolor="#0f172a"', 'bgcolor="#FFFFFF"'),
]
for name in ("5_research_assistant.py", "6_biomarker_panel.py"):
    p = Path("app/pages") / name
    t = p.read_text(encoding="utf-8")
    for a, b in CHART:
        t = t.replace(a, b)
    p.write_text(t, encoding="utf-8")
    print("chart", name)
