# PAGE 08 — Patient Eligibility Scorer
# ─────────────────────────────────────────────────────────────────────────────
# Purpose : Demonstrate the real-time eligibility scoring tool — switch cancer
#           types, show how scoring criteria shift, use the GENIE 8-segment bar
#           to quantify the eligible patient fraction.
# Audience : Dr. Bobba Naidu panel — clinical researchers / translational team
# Data sources : AACR GENIE Release 19 (271,837 patients)
#                TCGA mRNA/IHC · Literature-derived eligibility criteria
# Target length : ~4 minutes | ~520 spoken words
# Platform page : Page 8 — Patient Eligibility
# ─────────────────────────────────────────────────────────────────────────────

---

## OPENING — Clinical Protocol Reality (45 seconds)

[DO: Click 'Patient Eligibility' in the sidebar. Let the page load fully.]

[SAY:]
"The Patient Eligibility module is designed to answer one of the most
time-intensive questions in early clinical trial design: for a given cancer
type and target, which patients from a real-world population would be
eligible for enrolment based on currently accepted clinical criteria?

This is not a statistical model. This is a structured eligibility scoring
framework drawn from published inclusion and exclusion criteria from completed
and active CD46 clinical trials — applied in real time to the GENIE patient
population.

The question this page answers: of the patients who actually exist in the
real-world sequencing database, how many would realistically qualify for
a CD46-targeted trial today?"

---

## SCREEN 1 — Cancer Type Selection and Metric Cards (60 seconds)

[DO: Set Cancer Type selector = Prostate Cancer (PRAD). Let the KPI metrics update.]

[SAY:]
"I will start with prostate cancer — the primary indication. The five metric
cards update immediately.

Eligible patient fraction: this is the proportion of PRAD patients in GENIE
who meet the baseline molecular criteria — specifically: no MSI-high status
that would redirect to immune checkpoint, absence of homologous recombination
deficiency designation that would prioritise PARP inhibitor, and a cancer
type with confirmed CD46 expression ranking in the top three quartiles.

Prior therapy requirement: mCRPC status, meaning at least one prior line of
ARPI therapy. The platform codes this based on sample type annotation in GENIE —
metastatic biopsy samples from patients with prostate cancer who have known
prior ARPI exposure.

PSMA status consideration: patients who have progressed after or are ineligible
for lutetium-PSMA — the CD46 priority window."

---

## SCREEN 2 — Cancer Type Switcher Demo (90 seconds)

[DO: Switch Cancer Type to Ovarian Serous Cystadenocarcinoma (OV).]

[SAY:]
"I switch to ovarian cancer. The eligibility criteria shift automatically.
For ovarian cancer, the relevant clinical criteria are: platinum-resistant
disease — more than two prior lines of chemotherapy — and no current
clinical trial enrolling a genomically matched PARP inhibitor arm.

The eligible fraction is different from prostate. The molecular subtype bar
chart below also updates — now showing the ovarian cancer patient distribution
by primary alteration — BRCA1, BRCA2, TP53, and other.

[DO: Switch to Renal Cell Carcinoma (RCC) or Glioblastoma (GBM).]

In renal cell carcinoma you can see a very different eligibility profile.
The criteria here weight prior anti-VEGF or immunotherapy exposure heavily,
because the patient would need to have failed checkpoint inhibitor therapy
before a targted radiopharmaceutical would typically be considered.

This cancer-type switching capability means your protocol development team
can generate patient eligibility estimates for any target indication in minutes —
not weeks of manual chart review."

[PAUSE]

---

## SCREEN 3 — 8-Segment Eligibility Bar (60 seconds)

[DO: Scroll down to the molecular subtype bar chart. Reset to Prostate Cancer.
     Point to each molecular subtype bar and the portion highlighted as eligible.]

[SAY:]
"At the bottom of the page, the 8-segment molecular landscape bar shows
which patient subtype groups fall within the eligibility window.

Triple-hit patients — AR, PTEN, TP53 — are the highest priority from an
expression standpoint. They are also the most treatment-refractory and
therefore most likely to have met the prior therapy criterion for eligibility.

The bar gives you an approximate eligible patient count for each subtype.
This directly informs your screening ratio estimates for a Phase 1 expansion
protocol — a number that sponsors and IRBs ask for specifically and that
currently requires weeks of manual literature review to estimate."

---

## CLOSING (30 seconds)

[SAY:]
"The Patient Eligibility module does not replace your clinical trial protocol
review. It accelerates the protocol design analytical phase — from weeks to
real time. The numbers here come from 271,837 GENIE patients and are sortable,
filterable, and exportable for use in your trial design documents."
