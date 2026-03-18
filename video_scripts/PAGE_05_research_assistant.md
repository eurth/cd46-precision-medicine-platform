# PAGE 05 — Research Assistant
# ─────────────────────────────────────────────────────────────────────────────
# Purpose : Demonstrate the KG-grounded LLM research assistant with two live
#           scripted Q&A examples. Contrast explicitly vs ChatGPT / generic AI.
#           This is the MOST IMPORTANT page for the radiopharmaceutical panel.
# Audience : Dr. Bobba Naidu panel — scientific, clinical, sceptical of "AI hype"
# Data sources : Neo4j KG (3,047 nodes) · PubMed (55 papers) · TCGA · HPA
# Target length : ~5 minutes | ~620 spoken words
# Platform page : Page 5 — Research Assistant
# ─────────────────────────────────────────────────────────────────────────────

---

## OPENING — The Problem with Generic AI (60 seconds)

[DO: Click 'Research Assistant' in the sidebar. Let it load before speaking.]

[SAY:]
"I want to spend a moment addressing something your team almost certainly
has already experienced — you have probably asked ChatGPT or another large
language model a biology question. Maybe something about CD46. And you got
a confident, fluent answer.

The problem is that language models like ChatGPT operate from a compressed,
probabilistic representation of text on the internet up to their training
cutoff. They generate plausible language about CD46 biology.
They do not retrieve verified, source-traceable biological facts.
They have no connection to your TCGA expression values, your GENIE patient
counts, your active clinical trial IDs, or your PubMed corpus. They invent
or misrepresent statistics.

The Research Assistant on this page works on an entirely different principle.
Before the LLM writes a single word, the system queries the Neo4j knowledge
graph — 3,047 biology-specific nodes — and retrieves structured, verified
facts relevant to your question. The LLM then writes around those facts.
The answer is grounded. Every claim is traceable to a node in the graph —
TCGA, HPA, ClinicalTrials.gov, PubMed, DepMap.

This is retrieval-augmented generation on a structured scientific knowledge graph.
Not generic AI. Grounded AI."

---

## SCREEN 1 — Architecture Overview (30 seconds)

[DO: Point to the system architecture diagram or flow description at the top of the page —
     if visible, indicate the two-step flow: KG query → LLM synthesis.]

[SAY:]
"You can see the two-stage architecture here. Step one: the user question
is passed to a graph query layer that runs semantic search across the
knowledge graph nodes to retrieve relevant evidence.
Step two: the retrieved subgraph — typically 10 to 30 nodes and relationships —
is provided as structured context to the language model, which then writes
an answer strictly from that context.

The language model does not add anything the graph did not provide.
It translates graph facts into fluent scientific language."

---

## DEMO 1 — Clinical Question (90 seconds)

[DO: Click in the question input box. Type the following question exactly:]

→  What is the clinical rationale for targeting CD46 in metastatic castration-resistant prostate cancer?

[DO: Click Send / Submit. Wait for the response to appear fully. Do not scroll. Let the audience read.]

[SAY:]
"I am asking a clinical rationale question — the type of question a grant
submission or IND background section requires a precise answer to.

Look at what appears in the response. The assistant cites TCGA data:
CD46 mRNA overexpression in prostate adenocarcinoma with a specific
hazard ratio from the survival analysis. It references the SU2C mCRPC cohort.
It notes the 14 active clinical trials in the knowledge graph.
It mentions the AR-signalling axis and complement upregulation.

Now notice something critically important — at the end of the response,
the system shows you which knowledge graph nodes were retrieved to ground
this answer. You can trace every clinical claim back to its source data.

A generic AI answer to this question would give you a paragraph that sounds
good but could not tell you which clinical cohort or gene expression value
it cited. This can."

[PAUSE]

---

## DEMO 2 — Mechanism Question (90 seconds)

[DO: In the question box, clear the previous question and type:]

→  How does PTEN loss affect CD46 expression and what does that mean for patient selection?

[DO: Click Send / Submit. Wait for the full response.]

[SAY:]
"Now I am asking a mechanism question — the kind of question a wet-lab
scientist or translational researcher would ask before designing a companion
assay or a co-targeting experiment.

The assistant retrieves the PTEN-CD46 relationship node from the knowledge
graph — tagged with the source studies showing PI3K-AKT pathway activation
correlating with complement overexpression — and integrates it with the
patient data: PTEN deletion frequency in GENIE prostate cancer patients,
approximately 15%, and the GENIE molecular subtype data showing the PTEN-only
segment.

The answer tells you: PTEN loss activates downstream complement pathway
expression through PI3K-AKT co-signalling. For patient selection, PTEN-deleted
patients represent a molecularly defined enrichment population with potentially
higher CD46 expression and therefore higher likelihood of response to RLT.

This is a mechanistically grounded, clinically actionable answer.
It is exactly what a translational research team needs when designing
a biomarker-stratified Phase 1 protocol — and it was generated in under
30 seconds from 3,047 verified nodes."

---

## CLOSING (30 seconds)

[SAY:]
"Two more things to note: the research assistant works in real time —
if I update the knowledge graph with new publications or trial registrations
tonight, the assistant answers differently tomorrow. And the system logs
the retrieved nodes so your team can audit exactly what evidence set drove
any specific answer.

This is the Target Intelligence Layer — the first of three modules in the
radiopharmaceutical discovery orchestration architecture described in your
programme framework."
