# PAGE 01 — CD46 Expression Atlas
# ─────────────────────────────────────────────────────────────────────────────
# Purpose : Show CD46 expression across 33 TCGA cancer types (mRNA) and 30 HPA
#           tissues (protein). Establish biological target validity.
# Audience : Dr. Bobba Naidu panel — radiopharmaceutical scientists / clinical team
# Data sources : TCGA (mRNA, 33 cancers, 11,000+ patients) · Human Protein Atlas
#                (protein IHC, 30 tissues) · DepMap (CRISPR, 1,186 cell lines)
# Target length : ~5 minutes | ~600 spoken words
# Platform page : Page 1 — CD46 Expression Atlas
# ─────────────────────────────────────────────────────────────────────────────

---

## OPENING — Why Expression Data Comes First (30 seconds)

[DO: Click 'CD46 Expression Atlas' in the sidebar.]

[SAY:]
"The CD46 Expression Atlas is where the scientific case for this target begins.
Before you can design a radioligand, before you can select patients, before you
can calculate dosimetry — you must first answer: where is CD46 expressed,
at what level, at the mRNA level and at the protein level, and is that expression
functionally relevant in cancer?

This page answers all three questions using two independent datasets and a
CRISPR functional screen."

---

## SCREEN 1 — KPI Strip (30 seconds)

[DO: Point to the four KPI metric boxes at the top of Page 1.]

[SAY:]
"Four quick orientation metrics. 33 cancer types profiled from TCGA.
Top indicator: prostate adenocarcinoma — PRAD — shows the highest CD46 expression.
30 tissue pairs from the Human Protein Atlas — both normal and tumour IHC data.
And the therapeutic threshold: log₂ TPM of 2.5 or higher. That is the
expression cut-off we use to define patients likely to be CD46-accessible
for an antibody-based radioligand."

---

## SCREEN 2 — Tab 1: mRNA Expression (90 seconds)

[DO: Click Tab 1 — 'mRNA Expression'. Let the pan-cancer bar chart load fully.
     Point to the PRAD bar — highest value. Point to the dashed threshold line.]

[SAY:]
"Tab 1 is the pan-cancer mRNA expression chart. Every bar represents one
TCGA cancer type. The y-axis is median log₂ TPM — log-2 of transcripts
per million, the standard RNA-seq expression unit.

Prostate adenocarcinoma — PRAD — sits at the top. Consistently, across every
TCGA analysis. Ovarian cancer — OV — and bladder urothelial carcinoma — BLCA —
follow. The dashed horizontal line is the 225Ac-CD46 eligibility threshold.
Cancers below this line have insufficient target expression to justify a
radioligand programme.

The data here comes from TCGA via the UCSC Xena data portal — the same
public resource used in thousands of cancer genomics publications.
We are not using curated or pre-selected data — this is the complete 33-cancer
pan-cancer analysis.

You will notice some cancers — glioblastoma, acute myeloid leukaemia — sit
below the threshold. Those are immediately deprioritised. This computational
filter removes them from consideration before any wet-lab work begins.
That is the value of a target intelligence platform."

[PAUSE]

[DO: Use the 'Sort by' control to switch between Median Expression,
     Priority Score, and Cancer Type A-Z. Show how the ranking changes.]

[SAY:]
"You can reorder the chart — by raw expression, by multivariate priority score,
or alphabetically. The priority score ordering is the most clinically useful —
it combines five factors, not just expression rank."

---

## SCREEN 3 — Tab 2: Priority Score (75 seconds)

[DO: Click Tab 2 — 'Priority Score'. Let the heatmap and ranking table load.]

[SAY:]
"Tab 2 is the Priority Score view. This is where the platform moves beyond
simple expression ranking.

The priority score combines five independent evidence dimensions.
First — mRNA expression level from TCGA.
Second — protein evidence from the Human Protein Atlas IHC data.
Third — copy number alteration frequency in TCGA — whether CD46 is amplified
at the DNA level in tumour tissue.
Fourth — survival impact from our Kaplan-Meier analysis — whether CD46-high
patients have significantly different outcomes.
Fifth — clinical trial activity on ClinicalTrials.gov — how much the field
has already validated this cancer type as a CD46 target.

A cancer that scores high on all five dimensions is a much safer bet than
one that is top-ranked purely on expression. The heatmap shows you which
cancers score at which dimensions. You can see that prostate cancer is not
the highest expression in every column — but it is consistently high across
all five. That consistency is what makes it the top priority."

[PAUSE]

---

## SCREEN 4 — Tab 3: Protein Atlas (75 seconds)

[DO: Click Tab 3 — 'Protein Atlas'. Let the IHC chart or tissue panel load.
     Point to the prostate tumour bar and the normal tissue bars.]

[SAY:]
"Tab 3 is the protein expression data from the Human Protein Atlas.
This is the most directly relevant data for a radiopharmaceutical programme
because it validates that CD46 is present at the cell surface — where the
antibody will bind — not just transcribed.

The HPA data uses IHC H-score — a histological scoring system that
multiplies staining intensity by the percentage of positive cells.
Maximum H-score is 300.

Prostate tumour tissue — specifically metastatic castration-resistant
prostate cancer — scores 300 out of 300. Maximum protein expression.
Normal prostate epithelium scores approximately 200. The tumour-to-normal
ratio of 1.5-fold in prostate is the starting point for the safety calculation
on the dosimetry page.

Look also at kidney — high normal tissue expression. Liver — moderate.
Blood cells — moderate. These are the primary organs at risk for systemic
CD46-targeted therapy. The alpha particle's 2-to-3 cell range is the safety
mechanism — it only irradiates tissue where the antibody physically binds.
We will quantify this in the dosimetry module."

---

## SCREEN 5 — Tab 4: Data Table (30 seconds)

[DO: Click Tab 4 — 'Data Table'. Show the full table briefly.]

[SAY:]
"Finally, the full data table — every cancer type, its sample count,
median and mean CD46 expression, protein evidence tier, and prognostic
significance flag. Fully downloadable. Every number here links to a
publicly accessible dataset. This is the raw evidence base behind
every chart on this page."
