# PAGE 12 — Dosimetry Safety
# ─────────────────────────────────────────────────────────────────────────────
# Purpose : Explain the alpha particle dosimetry rationale, safety window
#           analysis (H-score 300/200, therapeutic index), and organs at risk.
#           This is the most radiopharmaceutical-specific page.
# Audience : Dr. Bobba Naidu panel — radiopharmaceutical scientists (core audience)
# Data sources : HPA IHC H-score data · TCGA mRNA · Published 225Ac dosimetry
#                MIRD committee dosimetry formalism
# Target length : ~5 minutes | ~600 spoken words
# Platform page : Page 12 — Dosimetry Safety
# ─────────────────────────────────────────────────────────────────────────────

---

## OPENING — The Question This Page Answers (45 seconds)

[DO: Click 'Dosimetry Safety' in the sidebar. Let the page load.]

[SAY:]
"The Dosimetry Safety module is the page that will be most immediately
relevant to the physicists and dosimetrists in your organisation.

The foundational safety question for any radioligand therapy programme is the
therapeutic index — the ratio of absorbed dose to tumour versus absorbed dose
to dose-limiting normal tissue. For 225Ac-labelled agents targeting a surface
antigen like CD46, the question is: how much CD46 is expressed in tumour tissue
versus dose-critical normal tissue?

If CD46 were expressed at equal levels in tumour and kidney, for example,
you would have a prohibitive safety profile. If tumour expression is
substantially higher than any normal tissue, you have a viable therapeutic
window.

This page provides the protein-level IHC data — H-scores from the Human Protein
Atlas — to construct a theoretically grounded safety assessment before any
dosimetry experiment is run."

---

## SCREEN 1 — Alpha Particle Physics Summary (60 seconds)

[DO: Point to the physics parameter card section at the top — alpha range, LET, half-life.]

[SAY:]
"Starting with the radiophysics parameters that define the treatment window.

225Ac half-life: 9.9 days. Roughly 10 days — a dosing interval compatible
with outpatient nuclear medicine infusion.

Alpha particle energy: approximately 5.8 MeV per decay event. Each 225Ac atom
produces a cascade of four decay events as it moves to stable lead-209 —
meaning 4 alpha particles per administered radioatom released in proximity
to the target cell.

Alpha particle tissue range: 40 to 100 micrometres. Approximately 2 to 3 cell
diameters. This is critical. The cytotoxic effect is microscopically confined
to the immediate neighbourhood of the targeted cell. Cells 2 mm away receive
essentially zero alpha particle dose — unlike beta emitters, where 2 to 3 mm
of tissue receives significant lateral dose.

Linear energy transfer: 60 to 80 keV per micrometre — roughly 400 times higher
than diagnostic X-ray. This high LET produces irreparable double-strand DNA
breaks — the reason alpha emitters kill cells refractory to conventional
radiation and chemotherapy."

---

## SCREEN 2 — H-Score Therapeutic Window (90 seconds)

[DO: Point to the H-score comparison chart or table —
     tumour H-score (300) vs normal tissue H-score (200).]

[SAY:]
"The H-score — histochemical score — quantifies protein expression on IHC
sections. Range: 0 to 300. Zero means no staining. 300 means every cell
uniformly intense positive.

From the Human Protein Atlas CD46 IHC panel across 81 tissues:

Tumour H-score in prostate adenocarcinoma: approximately 300. Maximum score.
Uniformly strong membrane staining in most specimens.

Key organs at risk — why they matter and what the data shows:

Kidney: H-score approximately 200. Kidneys are the primary dose-critical organ
for small-molecule radioligand agents because of renal clearance. For an
antibody-targeted RLT like a CD46-ADC or pretargeted RIT where the carrier
is a full antibody, renal clearance is slower than for small peptides. Still,
CD46 expression in renal tubular cells at 200 out of 300 is a risk to monitor.
This is why BC8-CD46 pretargeted RIT — with its fast-clearing small radiolabelled
effector molecule — may have a favourable renal dosimetry profile.

Liver: H-score approximately 200. Kupffer cells and hepatocytes express CD46.
Hepatic dosimetry monitoring will be required in Phase 1.

Normal prostate: H-score approximately 150 — lower than tumour.
This differential — 300 in tumour versus 150 in normal prostate — establishes
a theoretical therapeutic index of approximately 2-to-1 for prostate specifically."

[PAUSE]

---

## SCREEN 3 — Therapeutic Index Calculation (60 seconds)

[DO: Point to the TI calculation or visualisation on the page.]

[SAY:]
"The therapeutic index visualisation combines the expression ratio with the
alpha particle range to give a modelled differential dose estimate.

Because alpha particles travel only 2 to 3 cell diameters, the dose is
almost entirely absorbed by CD46-expressing cells and their immediate
neighbours. The ratio of dose to tumour over dose to normal tissue is
therefore primarily driven by the expression-level ratio rather than anatomy,
as it would be for a beta emitter with millimetre-range tissue penetration.

A tumour-to-kidney expression ratio of 1.5 in an alpha emitter context
translates to a more favourable clinical safety window than the same ratio
would provide for a beta emitter. This is one of the key physics rationales
for pursuing an actinium-225 programme for CD46 rather than a lutetium programme.

Phase 1 dosimetry studies will refine these theoretical estimates.
This platform provides the pre-clinical biology foundation that would support
an IND submission to justify proceeding to first-in-human dosimetry."
