# PAGE 02 — Patient Selection
# ─────────────────────────────────────────────────────────────────────────────
# Purpose : Show how 271,837 real-world GENIE patients are stratified into
#           molecular subtypes. Explain why CD46 is an expression-level target.
#           Demonstrate the 8-segment prostate landscape and cohort explorer.
# Audience : Dr. Bobba Naidu panel — radiopharmaceutical scientists / clinical team
# Data sources : AACR GENIE Release 19 (271,837 patients, Synapse syn72382128)
#                TCGA (mRNA + IHC context) · SU2C mCRPC cohort
# Target length : ~5 minutes | ~600 spoken words
# Platform page : Page 2 — Patient Selection
# ─────────────────────────────────────────────────────────────────────────────

---

## OPENING — The Critical Biology Point (45 seconds)

[DO: Click 'Patient Selection' in the sidebar. Let the page load fully.]

[SAY:]
"The Patient Selection module answers the foundational clinical question:
which patients are real-world candidates for 225Ac-CD46 therapy, and from
what evidence base?

Before I show you the charts, I need to make one biological point that is
essential for correctly interpreting everything on this page.

CD46 does not appear as a genomic alteration in next-generation sequencing data.
No mutations. No amplifications. No deletions at any meaningful frequency.
This is expected. This is not a limitation of the programme. CD46 is an
expression-level target — it is overexpressed at the protein level, detected
by immunohistochemistry or RNA sequencing, not by DNA panel sequencing.

The largest DNA sequencing dataset in the world — AACR Project GENIE —
will show no CD46 genomic events. What GENIE does show — and what is
directly relevant — is the genomic driver landscape of the patient population
most likely to carry CD46 protein overexpression."

---

## SCREEN 1 — GENIE Dataset Introduction (45 seconds)

[DO: Click the 'GENIE Real-World Data' tab on Page 2 if not already selected.]

[SAY:]
"AACR Project GENIE — Genomics Evidence Neoplasia Information Exchange.
Release 19.0, public edition. 271,837 cancer patients. Sequenced at
major academic institutions: Memorial Sloan Kettering, Dana-Farber Cancer
Institute, MD Anderson, the Netherlands Cancer Institute, Vall d'Hebron
in Barcelona, and others. This is not a single-institution dataset.
It is a multi-centre real-world genomic registry — the most representative
publicly available cancer sequencing cohort in the world.

We downloaded and processed this dataset from the Synapse data repository
and it is integrated directly into the platform."

---

## SCREEN 2 — Pan-Cancer Driver Landscape (90 seconds)

[DO: Point to the grouped bar chart showing AR%, PTEN%, TP53% by cancer type.
     Let it load fully before speaking about specific numbers.]

[SAY:]
"This chart shows the alteration frequency of three key driver genes —
androgen receptor, PTEN tumour suppressor, and TP53 — across the top
cancer types in GENIE by patient count. Sorted by AR alteration frequency
to bring prostate cancer to the top.

In prostate cancer — 9,251 patients in GENIE — AR is amplified or gain-of-function
mutated in 12% of patients. PTEN is homozygously deleted in nearly 15%.
TP53 is mutated in 29%. These are not rare events. They are the defining
molecular features of treatment-resistant prostate cancer.

Why these three genes and not CD46? Because AR amplification drives androgen
signalling, which suppresses CD46 transcription — so AR-altered tumours have
upregulated CD46 after AR blockade. PTEN loss activates PI3K-AKT signalling,
which co-operates with androgen resistance and complement upregulation.
TP53 mutation is a marker of aggressive, treatment-refractory disease — exactly
the patient population with highest CD46 expression by IHC in published studies."

[PAUSE]

---

## SCREEN 3 — 8-Segment Molecular Landscape Donut (90 seconds)

[DO: Point to the 8-segment donut chart on the right side of the page.
     Point to each segment in order from largest to smallest as you describe them.]

[SAY:]
"This donut chart is the key visualisation on this page.
It segments all 9,251 prostate cancer patients in GENIE into eight named
molecular subtypes based on their combination of AR, PTEN, and TP53 alterations.

Previously this view showed one large grey segment — 'unknown or other' —
representing 76% of patients. That was clinically useless. Now we have
a full named landscape.

The deepest purple at the top — triple-hit: AR plus PTEN plus TP53 — 1.5%
of patients. Most treatment-resistant. Most aggressive biology. These patients
have failed or are failing every standard-line therapy.

Purple — AR plus PTEN, which we identify as the highest priority CD46 targeting
group based on the complement upregulation biology — 1.4% of patients.

Blue — AR plus TP53: 3.5%. Orange — PTEN plus TP53: 4.6%.

Sky blue — AR only: 5.5%. Amber — PTEN only: 7.4%.

Coral — TP53 only: nearly 20% — the single largest named subtype.
Dark slate — no detected driver alteration in these three genes: 56.3%.

In total, 43.7% of prostate patients in GENIE now have a named molecular
subtype — up from 12% before this expanded model. That characterisation
directly informs which patients to prioritise in a CD46 clinical protocol."

[PAUSE]

---

## SCREEN 4 — Cohort Explorer (30 seconds)

[DO: Scroll down to the cohort explorer filter section if visible.
     Set Cancer Type = Prostate Cancer. Set Gene = PTEN deleted. Show the filtered table.]

[SAY:]
"The cohort explorer below lets you filter the GENIE cohort by cancer type
and specific gene alteration. I will select prostate cancer and PTEN deleted.
The table below shows the matching patients — count, age distribution, sex,
sample type — directly from the 271,837-patient GENIE dataset.

This is not modelled data. Every row in that table represents a real patient
whose tumour was sequenced at a major cancer centre. This is what the platform
brings to clinical protocol design — real-world population estimates from
the most comprehensive cancer sequencing cohort available."
