"""Build Gene and Protein nodes from static CD46 data + UniProt."""
from __future__ import annotations

import json
import logging
from pathlib import Path

from neo4j import Driver

logger = logging.getLogger(__name__)

CD46_GENE = {
    "ensembl_id": "ENSG00000117335",
    "symbol": "CD46",
    "entrez_id": "4179",
    "chromosome": "1q32.2",
    "full_name": "CD46 molecule",
    "function": (
        "Regulator of complement activation; protects host cells from "
        "complement-mediated lysis; receptor for multiple pathogens including "
        "measles virus; involved in T-cell activation and immune tolerance."
    ),
    "molecular_weight_da": 43686,
    "isoforms": ["BC1 (short)", "BC2 (long)", "C1 (short)", "C2 (long)"],
    "cancer_relevance": (
        "Overexpressed in multiple cancers; targetable antigen for "
        "225Ac-labeled radioimmunotherapy."
    ),
}

CD46_PROTEIN = {
    "uniprot_id": "P15529",
    "name": "Membrane cofactor protein",
    "symbol": "CD46",
    "molecular_weight_da": 43686,
    "subcellular_location": "Cell membrane",
    "post_translational_modifications": ["N-glycosylation", "O-glycosylation", "Phosphorylation"],
    "domains": ["SCR1", "SCR2", "SCR3", "SCR4", "STP region", "Transmembrane", "Cytoplasmic tail"],
}

PATHWAYS = [
    {
        "pathway_id": "R-HSA-166658",
        "name": "Complement cascade",
        "source": "Reactome",
        "relevance": "CD46 is a core complement regulator",
    },
    {
        "pathway_id": "R-HSA-6785807",
        "name": "Complement evasion by pathogens",
        "source": "Reactome",
        "relevance": "Exploited by measles, N. gonorrhoeae via CD46",
    },
    {
        "pathway_id": "GO:0006957",
        "name": "Complement activation, alternative pathway",
        "source": "GO",
        "relevance": "CD46 inhibits convertase formation",
    },
    {
        "pathway_id": "GO:0002250",
        "name": "Adaptive immune response",
        "source": "GO",
        "relevance": "CD46 modulates Treg / Th1 switching",
    },
    {
        "pathway_id": "KEGG:hsa04610",
        "name": "Complement and coagulation cascades",
        "source": "KEGG",
        "relevance": "CD46 CCP domains inhibit C3b deposition",
    },
]


def build_gene_nodes(driver: Driver) -> dict:
    """Merge GeneNode for CD46 into AuraDB."""
    gene_created = 0
    protein_created = 0
    pathway_created = 0

    with driver.session() as session:
        # Gene node
        session.run(
            """
            MERGE (g:Gene {ensembl_id: $ensembl_id})
            SET g.symbol              = $symbol,
                g.entrez_id           = $entrez_id,
                g.chromosome          = $chromosome,
                g.full_name           = $full_name,
                g.function            = $function,
                g.molecular_weight_da = $molecular_weight_da,
                g.isoforms            = $isoforms,
                g.cancer_relevance    = $cancer_relevance,
                g.updated_at          = datetime()
            """,
            **CD46_GENE,
        )
        gene_created = 1
        logger.info("Merged Gene node: CD46 (%s)", CD46_GENE["ensembl_id"])

        # Protein node
        session.run(
            """
            MERGE (p:Protein {uniprot_id: $uniprot_id})
            SET p.name                              = $name,
                p.symbol                            = $symbol,
                p.molecular_weight_da               = $molecular_weight_da,
                p.subcellular_location              = $subcellular_location,
                p.post_translational_modifications  = $post_translational_modifications,
                p.domains                           = $domains,
                p.updated_at                        = datetime()
            """,
            **CD46_PROTEIN,
        )
        protein_created = 1
        logger.info("Merged Protein node: P15529")

        # Gene → Protein relationship
        session.run(
            """
            MATCH (g:Gene {ensembl_id: 'ENSG00000117335'})
            MATCH (p:Protein {uniprot_id: 'P15529'})
            MERGE (g)-[:ENCODES]->(p)
            """
        )

        # Pathway nodes + Gene links
        for pw in PATHWAYS:
            session.run(
                """
                MERGE (pw:Pathway {pathway_id: $pathway_id})
                SET pw.name      = $name,
                    pw.source    = $source,
                    pw.relevance = $relevance
                WITH pw
                MATCH (g:Gene {ensembl_id: 'ENSG00000117335'})
                MERGE (g)-[:PARTICIPATES_IN]->(pw)
                """,
                **pw,
            )
            pathway_created += 1
        logger.info("Merged %d Pathway nodes", pathway_created)

    return {
        "genes_merged": gene_created,
        "proteins_merged": protein_created,
        "pathways_merged": pathway_created,
    }


def enrich_from_uniprot(driver: Driver, raw_dir: Path) -> int:
    """Optionally enrich Protein node with parsed UniProt JSON fields."""
    uniprot_path = raw_dir / "apis" / "uniprot_P15529.json"
    if not uniprot_path.exists():
        logger.warning("UniProt file not found: %s — skipping enrichment", uniprot_path)
        return 0

    with open(uniprot_path) as f:
        data = json.load(f)

    # Extract function text from UniProt API response
    try:
        comments = data.get("comments", [])
        func_text = next(
            (
                c["texts"][0]["value"]
                for c in comments
                if c.get("commentType") == "FUNCTION"
            ),
            None,
        )
        keywords = [kw["name"] for kw in data.get("keywords", [])]
    except (KeyError, StopIteration, TypeError):
        logger.warning("Could not parse UniProt function/keywords — skipping enrichment")
        return 0

    if func_text or keywords:
        with driver.session() as session:
            session.run(
                """
                MATCH (p:Protein {uniprot_id: 'P15529'})
                SET p.uniprot_function = $func_text,
                    p.keywords         = $keywords
                """,
                func_text=func_text,
                keywords=keywords,
            )
        logger.info("Enriched Protein P15529 from UniProt JSON")
        return 1
    return 0
