#!/usr/bin/env python3
"""Generate OncoBridge demo PowerPoint. Run: python scripts/build_demo_ppt.py"""
from pathlib import Path

from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "reports" / "OncoBridge_Demo_Presentation.pptx"

# Clinical Slate palette
NAVY = RGBColor(0x1E, 0x29, 0x3B)
BLUE = RGBColor(0x25, 0x63, 0xEB)
SLATE = RGBColor(0x64, 0x74, 0x8B)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
LIGHT_BG = RGBColor(0xF8, 0xFA, 0xFC)


def _box(slide, left, top, width, height, text, size=18, bold=False, color=NAVY, align=PP_ALIGN.LEFT):
    tb = slide.shapes.add_textbox(Inches(left), Inches(top), Inches(width), Inches(height))
    tf = tb.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = text
    p.font.size = Pt(size)
    p.font.bold = bold
    p.font.color.rgb = color
    p.alignment = align
    return tb


def title_slide(prs, title, subtitle=""):
    slide = prs.slides.add_slide(prs.slide_layouts[6])  # blank
    slide.background.fill.solid()
    slide.background.fill.fore_color.rgb = NAVY
    _box(slide, 0.6, 2.0, 8.8, 1.2, title, size=40, bold=True, color=WHITE, align=PP_ALIGN.LEFT)
    if subtitle:
        _box(slide, 0.6, 3.3, 8.8, 1.0, subtitle, size=20, color=RGBColor(0x94, 0xA3, 0xB8))
    _box(slide, 0.6, 6.8, 8.0, 0.4, "oncobridge.eurthtech.com  ·  Research use only", size=12, color=SLATE)


def content_slide(prs, title, bullets, footer=""):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    slide.background.fill.solid()
    slide.background.fill.fore_color.rgb = LIGHT_BG
    _box(slide, 0.5, 0.35, 9.0, 0.7, title, size=28, bold=True, color=NAVY)
    # accent line
    line = slide.shapes.add_shape(1, Inches(0.5), Inches(1.05), Inches(1.2), Inches(0.03))
    line.fill.solid()
    line.fill.fore_color.rgb = BLUE
    line.line.fill.background()
    y = 1.25
    for i, b in enumerate(bullets):
        prefix = "• " if not b.startswith("  ") else "   "
        text = b.strip() if not b.startswith("  ") else b.strip()
        if not text.startswith("•"):
            text = prefix + text
        _box(slide, 0.55, y, 8.9, 0.55, text, size=16 if i > 0 or len(bullets) > 6 else 17, color=NAVY if not b.startswith("  ") else SLATE)
        y += 0.52 if len(text) < 70 else 0.72
    if footer:
        _box(slide, 0.5, 6.9, 9.0, 0.4, footer, size=11, color=SLATE)


def two_col_slide(prs, title, left_title, left_items, right_title, right_items):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    slide.background.fill.solid()
    slide.background.fill.fore_color.rgb = LIGHT_BG
    _box(slide, 0.5, 0.35, 9.0, 0.7, title, size=28, bold=True, color=NAVY)
    _box(slide, 0.5, 1.2, 4.2, 0.4, left_title, size=16, bold=True, color=BLUE)
    y = 1.65
    for item in left_items:
        _box(slide, 0.5, y, 4.3, 0.5, "• " + item, size=14, color=NAVY)
        y += 0.48
    _box(slide, 5.0, 1.2, 4.2, 0.4, right_title, size=16, bold=True, color=BLUE)
    y = 1.65
    for item in right_items:
        _box(slide, 5.0, y, 4.3, 0.5, "• " + item, size=14, color=NAVY)
        y += 0.48


def build():
    prs = Presentation()
    prs.slide_width = Inches(10)
    prs.slide_height = Inches(7.5)

    title_slide(
        prs,
        "OncoBridge Intelligence",
        "Multi-target theranostics research workbench\nCD46 reference case study · 5 targets · 16 modules · Knowledge graph",
    )

    content_slide(prs, "The problem", [
        "Radioligand / surface-antigen programs need dozens of disconnected datasets",
        "TCGA, GENIE, trials, ChEMBL, protein atlases — each with different formats",
        "Generic AI (ChatGPT) generates plausible oncology text without verifiable numbers",
        "Teams lack a single workbench to go from target → patient → trial → strategy",
    ])

    content_slide(prs, "What OncoBridge is", [
        "Open research platform — not a hospital system or medical device",
        "16 modules across 9 research dimensions",
        "5 theranostic targets: CD46, PSMA (FOLH1), FAP, SSTR2, GRPR",
        "Neo4j knowledge graph (~3,586 nodes) linking genes, drugs, trials, publications",
        "Retrieval-augmented AI — retrieves your data, then explains it",
    ], footer="Data freeze: 2026-07-28-phase4-five-targets")

    two_col_slide(
        prs,
        "Five targets — plain English",
        "CD46 · FOLH1 (PSMA)",
        [
            "Complement evasion surface antigen",
            "Pan-cancer; mCRPC case study",
            "Alpha radioligand (α-RLT) focus",
            "Prostate membrane antigen",
            "Pluvicto® benchmark target",
        ],
        "FAP · SSTR2 · GRPR",
        [
            "Cancer-associated fibroblast marker",
            "FAPI PET / emerging RLT",
            "Neuroendocrine receptor (Lutathera® class)",
            "Lung / solid tumour GPCR target",
            "Bombesin-analogue radioligands",
        ],
    )

    content_slide(prs, "Nine research dimensions", [
        "Home — Platform orientation & module map",
        "Target / Cancer — Expression Atlas, Compare Targets",
        "Biomarkers — Multi-marker clinical decision views",
        "Proteins — PPI network, Diagnostics & imaging",
        "Patients — GENIE cohorts, Eligibility scoring",
        "Survival — Cox hazard ratios, forest plots",
        "Drugs / Safety — Pipeline, Dosimetry",
        "Graph / Ask — KG visualizer, Query Explorer, AI Assistant",
        "Strategy — End-to-end clinical development narrative",
    ])

    content_slide(prs, "Datasets included (name-drop for credibility)", [
        "TCGA / UCSC Xena — pan-cancer RNA & survival (US government genomics)",
        "AACR GENIE — 271,837 real-world sequenced tumours",
        "Human Protein Atlas (HPA) — protein tissue staining",
        "GTEx — normal tissue expression (safety window)",
        "DepMap — CRISPR cancer dependency screens",
        "ClinicalTrials.gov · ChEMBL · Open Targets · PubMed · STRING · UniProt",
        "Neo4j AuraDB — OncoBridge knowledge graph",
    ])

    two_col_slide(
        prs,
        "ChatGPT vs OncoBridge",
        "Generic ChatGPT",
        [
            "Generates plausible paragraphs",
            "May invent NCT IDs and hazard ratios",
            "No live link to your TCGA extracts",
            "Cannot query your knowledge graph",
        ],
        "OncoBridge",
        [
            "Retrieves ranked TCGA expression rows",
            "Returns verifiable NCT trial IDs",
            "Pre-computed Cox HR from your CSVs",
            "Live Cypher against Neo4j graph",
        ],
    )

    content_slide(prs, "Live demo flow (20 min)", [
        "1. Platform Overview — scope & KG scale",
        "2. Expression Atlas (CD46) — TCGA pan-cancer chart",
        "3. Compare Targets — five genes, trial funnel tab",
        "4. KG Query Explorer — Drugs targeting CD46 (live graph)",
        "5. Research Assistant — preset survival / trial question",
        "6. Patient Selection — GENIE cohort scale",
        "7. Clinical Strategy Engine — end-to-end narrative",
    ], footer="Full script: reports/DEMO_RUNBOOK.md")

    content_slide(prs, "KG Query Explorer — demo query #1", [
        "Navigate: Graph → KG Query Explorer",
        "Ensure CD46 selected in target bar",
        "Template: 💊 Drugs: Agents targeting CD46?",
        "Click Run Query → show drug name, type, max phase",
        "",
        "Say: “ChEMBL-linked nodes — not LLM invention.”",
    ])

    content_slide(prs, "KG Query Explorer — demo query #2", [
        "Template: 🧪 Clinical Trials: Trials investigating CD46?",
        "Show NCT ID, phase, status columns",
        "",
        "Optional — switch target to FOLH1 (PSMA):",
        "Same 💊 Drugs template → Pluvicto-era competitive context",
    ])

    content_slide(prs, "Research Assistant — demo questions", [
        "Click preset (do not type):",
        "“Summarise CD46 expression across TCGA cancer types with hazard ratios.”",
        "",
        "Second preset:",
        "“What is the current CD46-targeted drug pipeline and which agents are in clinical trials?”",
        "",
        "For CAB audience — use CAB Focus preset buttons",
    ], footer="Full list: reports/DEMO_QUESTIONS.md")

    content_slide(prs, "Acronym cheat sheet", [
        "TCGA — US cancer genomics atlas",
        "mCRPC — metastatic castration-resistant prostate cancer",
        "RLT — radioligand therapy (radioactive drug binds target)",
        "PSMA / FOLH1 — prostate surface target",
        "GENIE — AACR real-world sequencing registry",
        "HR — hazard ratio (>1 = worse survival)",
        "NCT — clinical trial registry number",
        "KG — knowledge graph (Neo4j)",
    ])

    content_slide(prs, "Honest positioning", [
        "CD46 = full reference case study (eligibility, biomarkers, diagnostics depth)",
        "FOLH1, FAP, SSTR2, GRPR = medium open-data slices",
        "Expression, survival, trials, PPI, and KG templates work for all five",
        "Research use only — not clinical advice, not a medical device",
    ])

    title_slide(
        prs,
        "Thank you",
        "OncoBridge Intelligence\noncobridge.eurthtech.com\n\nQuestions?",
    )

    OUT.parent.mkdir(parents=True, exist_ok=True)
    prs.save(str(OUT))
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    build()
    assert OUT.exists() and OUT.stat().st_size > 5000
