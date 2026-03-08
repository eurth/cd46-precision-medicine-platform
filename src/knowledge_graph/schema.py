"""
KG Schema — dataclasses for all node and relationship types.
Used by both build_graph.py (Neo4j) and kg_to_csv.py (CSV export).
"""

from dataclasses import dataclass, field, asdict
from typing import Optional
import datetime


def _today() -> str:
    return datetime.date.today().isoformat()


@dataclass
class GeneNode:
    symbol: str
    ensembl_id: str
    chromosome: str = ""
    uniprot_id: str = ""
    function: str = ""
    therapeutic_rationale: str = ""
    is_complement_regulator: bool = False

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class ProteinNode:
    uniprot_id: str
    symbol: str
    isoform: str = ""
    molecular_weight_kda: Optional[float] = None
    surface_expressed: bool = True
    cleaved_shed: bool = False

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class DiseaseNode:
    tcga_code: str
    name: str
    ncit_code: str = ""
    icd10: str = ""
    cancer_type: str = ""
    tcga_sample_count: Optional[int] = None
    cd46_mean_tpm_log2: Optional[float] = None
    cd46_median_tpm_log2: Optional[float] = None
    cd46_std_tpm_log2: Optional[float] = None
    cd46_expression_rank: Optional[int] = None
    cd46_survival_hr: Optional[float] = None
    cd46_survival_pval: Optional[float] = None
    cd46_survival_log_rank_p: Optional[float] = None
    cd46_cna_amplification_freq: Optional[float] = None
    cd46_protein_tumor_score: str = ""
    priority_score: Optional[float] = None
    priority_label: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class TissueNode:
    name: str
    type: str  # "normal" | "tumor"
    organ_system: str = ""
    hpa_tissue_id: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class PatientGroupNode:
    name: str
    cancer_type: str
    dataset: str
    expression_group: str
    threshold_method: str = "median"
    threshold_value: Optional[float] = None
    n_patients: Optional[int] = None
    n_events: Optional[int] = None
    median_os_months: Optional[float] = None
    median_pfi_months: Optional[float] = None
    cohort_subtype: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class AnalysisResultNode:
    result_id: str
    type: str
    value: Optional[float] = None
    confidence_interval_low: Optional[float] = None
    confidence_interval_high: Optional[float] = None
    p_value: Optional[float] = None
    fdr: Optional[float] = None
    method: str = ""
    dataset: str = ""
    computed_at: str = field(default_factory=_today)

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class DrugNode:
    name: str
    drug_type: str = ""
    target_gene: str = "CD46"
    payload: str = ""
    isotope: str = ""
    developer: str = ""
    clinical_stage: str = ""
    mechanism: str = ""
    chembl_id: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class ClinicalTrialNode:
    nct_id: str
    title: str
    phase: str = ""
    status: str = ""
    primary_endpoint: str = ""
    enrollment_target: Optional[int] = None
    sponsor: str = ""
    start_date: str = ""
    primary_completion_date: str = ""
    cd46_expression_required: bool = False

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class PathwayNode:
    name: str
    reactome_id: str = ""
    go_id: str = ""
    category: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class CellLineNode:
    depmap_id: str
    name: str
    cancer_type: str = ""
    tissue: str = ""
    cd46_expression_tpm: Optional[float] = None
    cd46_crispr_score: Optional[float] = None
    cd46_is_dependency: bool = False

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class PublicationNode:
    pmid: str
    title: str = ""
    journal: str = ""
    year: Optional[int] = None
    doi: str = ""
    key_finding: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class DataSourceNode:
    name: str
    version: str = ""
    access_date: str = field(default_factory=_today)
    url: str = ""
    patient_count: Optional[int] = None
    data_type: str = ""

    def to_dict(self) -> dict:
        return asdict(self)
