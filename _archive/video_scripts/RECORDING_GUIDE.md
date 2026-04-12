# CD46 Platform — Video Recording Guide
# Read this first before recording any video

---

## Technical Setup

- **Screen:** 1920×1080. Browser at 100–110% zoom. Full-screen browser.
- **Bookmarks bar:** Hide it (right-click toolbar → uncheck bookmarks bar). Cleaner look.
- **Microphone:** Close to mouth. Quiet room. No fans, no AC noise if possible.
- **Cursor:** Move SLOWLY. Point and hold 2–3 seconds on anything you're naming. Never wave.
- **Loading:** If a chart is querying the live Neo4j database, say:
  *"This is querying the live knowledge graph in real time..."* — let it load naturally, do not skip.
- **Mistakes:** If you misspeak, pause 3 seconds (editing cut point), repeat the sentence, then continue.

---

## File Naming for Recordings

Save videos with these names so they match the script files:

```
CD46_OVERVIEW_A_Platform_Pitch.mp4
CD46_OVERVIEW_B_Orchestration_Vision.mp4
CD46_PAGE_00_Platform_Overview.mp4
CD46_PAGE_01_Expression_Atlas.mp4
CD46_PAGE_02_Patient_Selection.mp4
CD46_PAGE_03_Survival_Outcomes.mp4
CD46_PAGE_04_Knowledge_Graph.mp4
CD46_PAGE_05_Research_Assistant.mp4
CD46_PAGE_06_Biomarker_Panel.mp4
CD46_PAGE_07_KG_Query_Explorer.mp4
CD46_PAGE_08_Patient_Eligibility.mp4
CD46_PAGE_09_Competitive_Landscape.mp4
CD46_PAGE_10_PPI_Network.mp4
CD46_PAGE_11_Drug_Pipeline.mp4
CD46_PAGE_12_Dosimetry_Safety.mp4
CD46_PAGE_13_Clinical_Strategy.mp4
CD46_PAGE_14_Diagnostics.mp4
```

---

## Recommended Send Order to Panel

Send in this sequence — each video builds on the previous:

| # | File | Purpose | Length |
|---|------|---------|--------|
| 1 | OVERVIEW_A | Start here — 3-min orientation | ~3 min |
| 2 | OVERVIEW_B | Radiopharmaceutical vision context | ~4 min |
| 3 | PAGE_00 | Platform home — all datasets listed | ~4 min |
| 4 | PAGE_01 | Target expression — TCGA + HPA | ~5 min |
| 5 | PAGE_03 | Survival outcomes — PRAD HR | ~4 min |
| 6 | PAGE_10 | Protein network — complement biology | ~4 min |
| 7 | PAGE_04 | Knowledge graph — live queries | ~5 min |
| 8 | PAGE_07 | KG query explorer — 3 query modes | ~5 min |
| 9 | PAGE_05 | AI Research Assistant — core differentiator | ~5 min |
| 10 | PAGE_02 | Patient selection — GENIE 271k | ~5 min |
| 11 | PAGE_08 | Patient eligibility scorer | ~4 min |
| 12 | PAGE_06 | Biomarker panel — mCRPC 43% | ~5 min |
| 13 | PAGE_09 | Competitive landscape — PSMA vs CD46 | ~4 min |
| 14 | PAGE_11 | Drug pipeline — FOR46, BC8, 225Ac | ~5 min |
| 15 | PAGE_12 | Dosimetry & safety — therapeutic index | ~4 min |
| 16 | PAGE_13 | Clinical strategy engine — end-to-end | ~5 min |
| 17 | PAGE_14 | Diagnostics & companion diagnostic | ~5 min |

---

## Speaking Pace

- Target: **100–120 words per minute** (conversational, not rushed)
- Each `[PAUSE]` instruction = hold screen still for **2–3 seconds**
- Practice once without recording to get comfortable with the flow

---

## Key Numbers — Memorise Before Recording

These numbers appear across multiple videos. Say them confidently without looking down.

| Number | Meaning |
|--------|---------|
| **271,837** | AACR GENIE patients (Release 19.0-public) |
| **3,047** | Knowledge graph nodes in Neo4j AuraDB |
| **2,552** | Knowledge graph relationships |
| **33** | TCGA cancer types profiled |
| **81** | Human Protein Atlas tissues |
| **1,186** | DepMap CRISPR cell lines |
| **14** | Active CD46 clinical trials (ClinicalTrials.gov) |
| **55** | PubMed publications in the knowledge graph |
| **43.7%** | Prostate GENIE patients with named molecular subtype |
| **~35%** | mCRPC patients who are PSMA-low and CD46-high |
| **>85%** | mCRPC coverage: PSMA + CD46 dual targeting combined |
| **20×** | More DNA double-strand breaks: alpha vs beta per track |
| **9.9 days** | Actinium-225 half-life |
| **2–3 cells** | Alpha particle range (5.8 MeV) |
| **1.65** | PRAD OS hazard ratio (CD46-High vs CD46-Low, TCGA) |
| **9,251** | Prostate cancer patients in GENIE cohort |
| **444** | SU2C mCRPC cohort size |
| **43%** | mCRPC CD46 altered (SU2C cohort) |
| **9%** | Localised PRAD CD46 altered (TCGA baseline) |

---

## How to Describe the KG + LLM Combination (Key Message)

Use this framing consistently in Pages 4, 5, and 7:

> *"A standard language model gives you a plausible summary based on patterns
> in its training data. This system is different — the AI queries the live
> knowledge graph first, retrieves the actual numbers from real patient cohorts
> and real trials, and then the language model assembles those facts into a
> readable answer. The facts come from structured data. The language comes from
> the AI. Neither alone is sufficient."*

---

## Script File Format Conventions

In every script file:

- `[DO:]` — perform this action on screen before or as you begin the next SAY block
- `[SAY:]` — read this aloud, naturally (do not read robotically)
- `[PAUSE]` — stop speaking, hold screen for 2–3 seconds
- `→` — type exactly this text into the application (queries, questions)
- Text in *italics* within SAY blocks — optional phrasing you can improvise around
- Data source callouts in `[DATA SOURCE:]` — name the source naturally in speech

---

## Before You Start Recording — Checklist

- [ ] Streamlit Cloud URL open and platform is responsive
- [ ] All pages loading without errors (run through sidebar quickly)
- [ ] Microphone tested — record 10 seconds and play back
- [ ] Screen resolution set to 1920×1080
- [ ] Browser bookmarks bar hidden
- [ ] Key numbers table printed or visible (use second monitor if available)
- [ ] Script file open on second monitor or printed
- [ ] Recording software open and tested (OBS, Loom, or Windows Game Bar Win+G)
