# PAGE 10 — PPI Network
# ─────────────────────────────────────────────────────────────────────────────
# Purpose : Show the CD46 protein–protein interaction network from STRING DB —
#           30 direct partners, 103 relationships, complement cluster (CD55/CD59),
#           immune and drug resistance nodes.
# Audience : Dr. Bobba Naidu panel — wet-lab and molecular biology focused
# Data sources : STRING DB (v12.0, minimum confidence 0.7) · UniProt · KEGG
# Target length : ~4 minutes | ~500 spoken words
# Platform page : Page 10 — PPI Network
# ─────────────────────────────────────────────────────────────────────────────

---

## OPENING — Why Protein Interactions Matter for RLT (45 seconds)

[DO: Click 'PPI Network' in the sidebar. Let the force-directed network visualise fully.]

[SAY:]
"The Protein–Protein Interaction network module is directly relevant to wet-lab
researchers on your team — this is the molecular neighbourhood of CD46.

In the context of radioligand therapy, knowing your target's interaction
partners matters for three reasons:
First — on-target off-tumour toxicity: where else in the proteome is CD46
functionally connected, and would you expect downstream signalling changes
after targeting?
Second — resistance mechanisms: which interacting proteins can upregulate
to compensate if CD46 is blocked or destroyed?
Third — co-targeting opportunities: are there adjacent partners that could
be simultaneously targeted with a bispecific approach?

All interaction data on this page comes from STRING database, version 12,
minimum confidence score 0.7 — a widely accepted threshold for biologically
validated or experimentally confirmed interactions."

---

## SCREEN 1 — Network Overview (60 seconds)

[DO: Point to the full force-directed graph. CD46 is the large central node.
     Point to the colour-coded clusters. Hover over 2–3 nodes.]

[SAY:]
"Central node: CD46 — Membrane Cofactor Protein, also known as MCP.
30 direct protein interaction partners visualised here. 103 total interactions
in the STRING subgraph, including second-degree connections.

The node colours represent functional clusters. Blue nodes — the complement
regulatory cluster: CD55, CD59, C3, C4B, Factor H. These are the complement
system proteins that CD46 co-regulates to protect tumour cells from
complement-dependent cytotoxicity. This is the primary therapeutic logic cluster —
tumours overexpress CD46, CD55, and CD59 together as a complement evasion mechanism.

Orange nodes — the immune checkpoint adjacent proteins: C1s, MASP1, MASP2.
CD46 has established interactions with the lectin pathway of complement
at this interface.

Grey/white nodes — broader signalling interactors with lower confidence scores,
included at 0.7 threshold."

[PAUSE]

---

## SCREEN 2 — Complement Regulatory Cluster (90 seconds)

[DO: Click or highlight the complement cluster nodes — CD55, CD59 in particular.
     If a filter for 'complement' is available, apply it.]

[SAY:]
"Let me focus on the complement regulatory cluster — the most clinically
actionable region of the network.

CD55 — Decay Accelerating Factor — prevents C3 convertase assembly.
CD59 — Protectin — blocks the membrane attack complex. CD46 — prevents
phagocytosis by inactivating C3b deposited on the tumour surface.

These three proteins form a co-regulated complement evasion shield.
In IHC studies of prostate cancer — particularly biopsy tissue from mCRPC
patients — all three are frequently co-upregulated. This co-expression
pattern is not coincidental; it represents a tumour survival mechanism
against immune-complement killing.

The therapeutic implication: if you target CD46 with a radioligand,
you are not just delivering radiation — you are also disabling one member
of the complement evasion shield. Whether CD55 and CD59 compensate
is a critical open biological question that your wet-lab team could
investigate in vitro with CD46-expressing cell lines.

DepMap data from 1,186 cell lines, accessible through our Knowledge Graph,
shows CD46 expression levels across 900 prostate cancer cell lines tested.
That data is integrated here as a companion layer."

---

## SCREEN 3 — Interaction Table (30 seconds)

[DO: Scroll to the data table below the network visualisation.]

[SAY:]
"The table below the network shows the structured interaction data:
gene symbol, STRING confidence score, known interaction type —
experimental, co-occurrence, gene fusion, text-mining, or co-expression.

The table is sortable and exportable. Confidence score descending will
show you the most robustly validated interactions at the top.
For a publication-ready supplement or a target validation document,
the export CSV from this table gives you a complete STRING-sourced
interaction evidence set for CD46."
