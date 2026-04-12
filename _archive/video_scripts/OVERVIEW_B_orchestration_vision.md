# OVERVIEW VIDEO B — Radiopharmaceutical Discovery Orchestration Vision
# ─────────────────────────────────────────────────────────────────────────────
# Purpose : Explain WHERE this platform fits in the global radiopharma ecosystem
#           and WHY it was designed the way it was. Sets the strategic context
#           for all individual page videos.
# Audience : Dr. Bobba Naidu panel — radiopharmaceutical scientists / clinical team
# Target length : ~4 minutes | ~480 spoken words
# Platform page : Page 0 sidebar — scroll through during narration
# ─────────────────────────────────────────────────────────────────────────────

---

## OPENING — The Problem with the Current Ecosystem (60 seconds)

[DO: Open Page 0. Stay on it throughout most of this video.
     Sidebar visible. Do NOT navigate away for the first 2 minutes.]

[SAY:]
"Let me explain the strategic context for this platform — why it was built
the way it was, and where it fits in the radiopharmaceutical discovery landscape.

Radiopharmaceutical research today is structured in four layers.
Isotope production — companies focused on manufacturing actinium-225, lutetium-177,
lead-212. Drug discovery — target identification, ligand synthesis, radiolabeling.
Contract manufacturing — CDMO infrastructure for clinical-grade production.
And clinical imaging workflows — PET centres, dosimetry, theranostics clinics.

Most organisations specialise in exactly one of those layers. The field is
highly fragmented. What is almost entirely missing is a computational layer
that connects the scientific evidence across all of them."

[PAUSE]

---

## THE THREE UNSOLVED WORKFLOW GAPS (90 seconds)

[SAY:]
"Specifically, three workflow problems remain largely unsolved by the
radiopharmaceutical field today.

The first is target intelligence. Researchers still manually search literature
to identify tumour receptors suitable for radiolabeling. There is no integrated
system that combines tumour genomics, receptor expression data, and existing ligand
databases to computationally rank and prioritise targets. Every programme
starts with a literature review that takes months.

The second is radioligand design. Nearly all existing AI drug discovery tools
were built for small molecules. Radiopharmaceuticals frequently use peptides,
antibody fragments, or engineered proteins — molecules that must also be
chemically compatible with a specific chelator chemistry and isotope half-life.
Very few computational platforms specialise in this constraint space.

The third is preclinical data analytics. Alpha-emitter and PET imaging experiments
generate large imaging datasets and biodistribution measurements that most
wet laboratories still analyse manually — hand-measuring tumour uptake from
PET images, manually calculating absorbed dose. Automated tumour segmentation,
tracer quantification, and dosimetry modelling are emerging in academic centres
but are not yet standard infrastructure."

[PAUSE]

---

## WHERE THIS PLATFORM FITS (60 seconds)

[DO: Scroll the sidebar slowly, pointing to page names as you name the modules.]

[SAY:]
"This platform directly solves the first gap today — target intelligence.
Look at the page list. Expression atlas. Survival analysis. Patient stratification.
Biomarker panel. Knowledge graph. These are the exact components of a
computational target intelligence pipeline — from 'where is this receptor
expressed' through 'which patients are candidates' to 'what does the clinical
evidence say'.

The CD46 programme is the first use case. But the architecture is generalisable
to any receptor target — PSMA, somatostatin receptors, integrins, FAP, folate
receptor. The data ingestion pipeline, the knowledge graph schema, and the AI
query system are not CD46-specific. They are the infrastructure."

[PAUSE]

---

## THE KNOWLEDGE GRAPH ADVANTAGE (60 seconds)

[SAY:]
"The knowledge graph is the core technical differentiator.
3,047 nodes and 2,552 typed relationships connecting CD46 biology,
patient cohorts across 271,837 real-world cancer patients, drugs,
clinical trials, publications, protein interactions, and tissue expression.
Stored in Neo4j AuraDB and queried in real time.

When the AI research assistant answers a scientific question — 'which patients
benefit most from 225Ac-CD46 therapy?' — it is not generating a statistical
summary from training data. It is querying the actual patient group nodes,
survival result nodes, and drug nodes in the graph and returning structured
facts. The language model assembles the answer. The graph provides the facts.

That distinction is critical. It is the difference between a plausible answer
and a precise, auditable, data-grounded answer."

---

## CLOSING — The Roadmap (30 seconds)

[SAY:]
"This is Stage 1 of a multi-stage orchestration system. Target intelligence
is built. The preclinical analytics layer — automating biodistribution and
dosimetry from imaging data — and the radioligand design workflow are
the next development stages.

What you are seeing right now is a working, deployed, live system.
Not a prototype. Not a slide deck. The individual module videos will show you
exactly what each analytical capability does and what data powers it."
