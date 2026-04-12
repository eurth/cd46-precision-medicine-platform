# PAGE 07 — KG Query Explorer
# ─────────────────────────────────────────────────────────────────────────────
# Purpose : Demonstrate the three query modes — Visual Builder, Cypher Editor,
#           Natural Language Translator — with 3 scripted live demos showing
#           how scientists can query the KG without software expertise.
# Audience : Dr. Bobba Naidu panel; assume zero graph database experience
# Data sources : Neo4j AuraDB (3,047 nodes, 2,552 relationships)
# Target length : ~4 minutes | ~540 spoken words
# Platform page : Page 7 — KG Query Explorer
# ─────────────────────────────────────────────────────────────────────────────

---

## OPENING — Who This Page Is For (30 seconds)

[DO: Click 'KG Query Explorer' in the sidebar. Let the three mode tabs load.]

[SAY:]
"The KG Query Explorer is built for researchers who want to explore the
knowledge graph directly — without going through the pre-built dashboards.
Three query modes are available, and they are designed for three different
user profiles.

Visual mode for scientists who want a point-and-click interface.
Cypher mode for those who know or want to learn graph database querying.
Natural Language mode for anyone who wants to ask a question in plain English
and have the system translate it into a graph query automatically."

---

## MODE 1 — Visual Builder (90 seconds)

[DO: Click the 'Visual Builder' tab.
     Set Node Type A = Gene. Set filter = CD46.
     Set Relationship Type = EXPRESSED_IN.
     Set Node Type B = CancerType.
     Click Run or Generate Query.]

[SAY:]
"In the Visual Builder I am selecting: Gene — CD46 — expressed in —
Cancer Type. I click run.

The system constructs and executes the Cypher query automatically. The results
come back as a table and a mini-graph: all cancer types in the knowledge graph
that have a confirmed CD46 expression relationship, with expression value,
rank, and data source for each.

No code written. No Cypher syntax. No database knowledge required. A wet-lab
scientist or a clinical researcher can use this interface on day one.

I will now try a second multi-hop query: Gene CD46 — interacts with — Protein —
associated with — Pathway.

[DO: Set up the multi-hop query or click a multi-hop preset if available.
     Click Run. Let the graph visualisation expand.]

You can see the complement system pathway appearing — CD46 connecting to CD55,
CD59, C3, C4B — the entire complement regulatory cluster that explains why
tumours overexpressing CD46 are protected from complement-dependent cytotoxicity."

[PAUSE]

---

## MODE 2 — Cypher Editor (60 seconds)

[DO: Click the 'Cypher Editor' tab.
     Clear any default text. Type the following Cypher query:]

→  MATCH (g:Gene {symbol:"CD46"})-[:TARGETED_BY]->(d:Drug) RETURN d.name, d.mechanism, d.phase

[SAY:]
"The Cypher Editor gives direct access for users comfortable with graph
database syntax. I am querying: find CD46, follow the TARGETED BY
relationship to drug nodes, and return the drug name, mechanism of action,
and clinical trial phase.

The results show FOR46 — the SAR-CD46 AstraZeneca antibody-drug conjugate,
Phase 1. BC8-CD46 — the Fred Hutchinson pretargeted radioimmunotherapy agent.
The bispecific antibody preclinical systems. Each drug node carries the
clinical phase, mechanism, and linked ClinicalTrials.gov identifiers.

This query executes in under 300 milliseconds. The data is live from the
Neo4j graph database."

[PAUSE]

---

## MODE 3 — Natural Language to Cypher (90 seconds)

[DO: Click the 'Natural Language' tab.
     Type the following in the NL input field:]

→  Which cancer types have CD46 overexpression AND active clinical trials?

[DO: Click Translate or Submit. Watch the system show the generated Cypher query
     before executing it, then show the results.]

[SAY:]
"This is the most accessible mode — plain English. I ask: which cancer types
have CD46 overexpression AND active clinical trials?

You can see two things happen. First, the system shows you the Cypher query
it generated from my question — this is fully transparent, not a black box.
Second, it executes the query and returns the results.

Prostate cancer, renal cell carcinoma, and glioblastoma match both conditions —
CD46 overexpression confirmed in the expression atlas AND at least one active
trial registered. Ovarian cancer and bladder cancer match the expression
criterion but have no currently indexed active trials, meaning there is an
unaddressed clinical gap.

For a radiopharmaceutical scientist thinking about expanding a CD46 programme
to adjacent indications, this query — typed in 10 seconds — gives you the
competitive white space map. No bioinformatics team needed."
