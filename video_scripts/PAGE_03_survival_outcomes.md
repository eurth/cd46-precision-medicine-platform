# PAGE 03 — Survival Outcomes
# ─────────────────────────────────────────────────────────────────────────────
# Purpose : Demonstrate that high CD46 expression predicts worse survival —
#           the prognostic rationale for targeting CD46 in treatment-resistant
#           disease. Walk through KM curves, forest plot, and results table.
# Audience : Dr. Bobba Naidu panel — radiopharmaceutical scientists / clinical team
# Data sources : TCGA (11,160 patients, 33 cancer types, OS + PFI endpoints)
# Target length : ~5 minutes | ~580 spoken words
# Platform page : Page 3 — Survival Outcomes
# ─────────────────────────────────────────────────────────────────────────────

---

## OPENING — Why Survival Data Matters Here (45 seconds)

[DO: Click 'Survival Outcomes' in the sidebar. Let all three tabs load.]

[SAY:]
"Survival Outcomes is one of the most important clinical validation pages in
the platform. This is where we move from overexpression — which tells you
CD46 is elevated — to prognostic significance — which tells you that elevation
actually matters.

There is a direct clinical logic here. If CD46 overexpression associates with
worse survival in treatment-naive TCGA patients, that means CD46-high tumours
are biologically more aggressive. It also means CD46-high patients are
the ones most likely to be treatment-resistant by the time they reach
second- or third-line therapy — exactly the patient population for a
next-generation radioligand therapy like 225Ac-CD46 RLT.

All data on this page comes from The Cancer Genome Atlas — 11,160 patients,
33 cancer types, with survival data linked to gene expression. Two endpoints:
overall survival and progression-free interval."

---

## SCREEN 1 — KPI Strip (30 seconds)

[DO: Point to the top KPI strip showing 4 metric cards.]

[SAY:]
"The summary strip at the top tells you at a glance: 14 statistically
significant survival associations. Hazard ratios across cancer types
ranging from approximately 1.2 to 2.3. The primary endpoint is overall
survival. Pancreatic adenocarcinoma, prostate cancer, and ovarian cancer
show the strongest and most clinically relevant associations."

---

## SCREEN 2 — Kaplan-Meier Curves Tab (120 seconds)

[DO: Click the 'Kaplan-Meier Curves' tab. Set Cancer Type = Prostate Cancer.
     Set Endpoint = Overall Survival. Wait for the curve to render.]

[SAY:]
"I am selecting prostate cancer and overall survival. You can see two survival
curves: CD46-high expression in deep blue, CD46-low in orange. The curves
diverge from approximately 36 months.

By 84 months — seven years — the difference in survival probability is
substantial. The hazard ratio is approximately 1.65. That means patients in
the CD46-high group have a 65% higher risk of death over the follow-up
period compared to CD46-low patients, after adjusting for expression median split.

In the context of prostate cancer, this is clinically meaningful. The CD46-high
population is the castration-resistant, treatment-refractory fraction.
These are the patients for whom PSMA-targeted therapy may already be failing
or may not be an option, and for whom CD46 represents the next targeting axis.

[DO: Change Cancer Type = Ovarian Serous Cystadenocarcinoma. Wait for curves to update.]

Let me switch to ovarian cancer. At the OV endpoint you see a similar pattern —
CD46-high associates with shorter progression-free interval. This is relevant
because ovarian cancer has poor response to platinum after recurrence.
CD46 expression may stratify the subset with inherent resistance.

The platform runs these survival computations live across all 33 TCGA cancer
types. You can explore any cancer type, any endpoint, in real time."

[PAUSE]

---

## SCREEN 3 — Forest Plot Tab (90 seconds)

[DO: Click the 'Forest Plot' tab. Let it load fully. Point to the centre line at HR = 1.0.]

[SAY:]
"The forest plot is a standard clinical publication format. Each row is one
cancer type. The horizontal axis is the hazard ratio for CD46-high versus
CD46-low expression. The centre line at 1.0 is the null — no effect.

Dots to the right of the line, where the confidence interval does not
cross 1.0, represent statistically significant positive associations:
CD46-high means worse survival in those cancer types. Dots to the left
represent significant protective or inverse associations.

In the forest plot here, prostate cancer, pancreatic adenocarcinoma, and
thyroid carcinoma show consistently elevated hazard ratios above 1.3 with
confidence intervals that do not cross 1.0. These are the priority cancer types.

This forest plot could go directly into a grant application or an IND-enabling
study document as published evidence of CD46 prognostic significance.
The underlying data is TCGA with full citation: Cancer Genome Atlas Research
Network, curated via cBioPortal."

[PAUSE]

---

## SCREEN 4 — Significant Results Table (45 seconds)

[DO: Click the 'Significant Results' tab. Show the data table with HR, CI, and p-value columns.]

[SAY:]
"This third tab shows the exportable data table. Cancer type, number of patients
in the high versus low group, hazard ratio, 95% confidence interval, p-value,
and FDR-corrected q-value.

Every row with a q-value below 0.05 represents a statistically robust
association after multiple hypothesis correction. The table is sortable
and exportable.

For your research team: if you are submitting a proposal to study CD46 as
a prognostic biomarker or therapeutic target in any specific cancer type,
this table gives you the statistical foundation — 14 cancer types with
FDR-corrected significance — drawn from one of the largest harmonised
clinical genomics datasets in the world."
