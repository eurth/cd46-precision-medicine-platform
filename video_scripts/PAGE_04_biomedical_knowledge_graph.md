# PAGE 04 — Biomedical Knowledge Graph
# ─────────────────────────────────────────────────────────────────────────────
# Purpose : Explain what a biomedical knowledge graph is to a scientific
#           audience, show the CD46-specific graph live, and run a simple
#           Cypher demo to illustrate structured biological reasoning.
# Audience : Dr. Bobba Naidu panel — wet-lab + clinical team; not software people
# Data sources : Neo4j AuraDB (3,047 nodes, 2,552 relationships)
#                TCGA · HPA · DepMap · ClinicalTrials.gov · ChEMBL · PubMed (55 papers)
# Target length : ~5 minutes | ~580 spoken words
# Platform page : Page 4 — Biomedical Knowledge Graph
# ─────────────────────────────────────────────────────────────────────────────

---

## OPENING — What Is a Knowledge Graph? (60 seconds)

[DO: Click 'Biomedical Knowledge Graph' in the sidebar. Let the graph visualisation load.]

[SAY:]
"The knowledge graph is the core infrastructure that makes this platform
different from a standard bioinformatics dashboard or a generic AI tool.
Let me explain what that means at a biological level, not a software level.

In a conventional research environment, your CD46 biology is fragmented.
PubMed publications are separated from your TCGA expression files.
Clinical trial records on ClinicalTrials.gov are disconnected from protein
interaction databases. Gene dependency data from DepMap exists in a
completely separate place from IHC data from the Human Protein Atlas.

A knowledge graph connects all of these — not as a file merge, but as a
formal network of biological relationships. Every node is an entity:
a gene, a protein, a disease, a drug, a pathway, a clinical trial, a publication.
Every edge is a typed relationship: CD46 IS EXPRESSED IN prostate cancer.
CD46 IS TARGETED BY a monoclonal antibody. CD46 INTERACTS WITH CD55.
CD46 expression CORRELATES WITH worse overall survival.

That formal structure is what enables precise, traceable, machine-readable
biological reasoning — far beyond key-word search or LLM inference alone."

---

## SCREEN 1 — Graph Statistics KPI Strip (30 seconds)

[DO: Point to the four metric cards at the top of the page.]

[SAY:]
"The graph as of March 2026 has 3,047 nodes and 2,552 relationships.
Let me contextualise the node types: 55 curated PubMed publications,
14 active clinical trials from ClinicalTrials.gov, 30 protein–protein interaction
partners from the STRING database, cancer type nodes linked to disease ontologies,
tissue type nodes from the Human Protein Atlas, cell line nodes from DepMap.

Everything CD46-relevant that is indexed in a public database is represented
as a connected entity in this graph."

---

## SCREEN 2 — Visual Graph Exploration (90 seconds)

[DO: Point to the force-directed graph visualisation. Hover over a few nodes to show tooltips.
     Click the CD46 central node if selectable. Let the relationships radiate outward.]

[SAY:]
"This is the live force-directed visualisation of the CD46 knowledge graph.
CD46 is at the centre. The nodes surrounding it are colour-coded by entity type:
pink for cancer types, green for protein interactors, blue for drugs and compounds,
purple for clinical trials, orange for biological pathways.

I am hovering over the CD46 node — this shows the full node properties:
UniProt ID, gene symbol, Ensembl ID, chromosomal location.

Now I click on PRAD — prostate adenocarcinoma — the relationship edge is labelled
EXPRESSED IN HIGH with the TCGA mRNA expression value, q-value, and tissue rank.

Every relationship carries its evidence metadata. This is not a curated assertion.
This is structured, sourced biological data — traceable to its origin database
at every step."

[PAUSE]

---

## SCREEN 3 — Live Cypher Query Demo (90 seconds)

[DO: Navigate to the Cypher Query Box section on this page — or click the 'Run Query' panel
     if it is separate. Type (or click demonstrate) the following query:]

→  MATCH (g:Gene {symbol:"CD46"})-[r]-(t) RETURN type(r), count(t) ORDER BY count(t) DESC

[SAY:]
"I am running a Cypher query directly against the Neo4j knowledge graph.
Cypher is the query language for graph databases — it reads almost like English.

This query says: find the CD46 gene node, return all relationship types and
count how many nodes exist on each side. In 200 milliseconds we get back the results:
EXPRESSED IN — the largest relationship class, connecting CD46 to cancer type nodes.
INTERACTS WITH — 30 protein partners.
TARGETED BY — drug and antibody nodes.
ASSOCIATED WITH — survival and expression outcomes.
HAS EVIDENCE FROM — publication and clinical trial nodes.

This is the complete biological universe we have indexed for CD46, structured
and queryable in real time. The next page shows you how this graph powers the
AI research assistant without hallucinating. The KG is where the facts live."
