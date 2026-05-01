"""Domain payload types for envelopes — v0.1 schemas.

Each Pydantic model corresponds to a YAML schema under `schemas/`. The
Pydantic model is the executable spec; the YAML is documentation. Models
are the payloads that ride inside `UniversalLayerEnvelope.outputs.payload`.

References: PRD.md § 4.2 (GeneticModificationSpec), § 4.3 (pathway sets),
§ 4.4 (CellFreeTXTLObservation), § 5.2 (CrossModelDisagreementRecord),
§ 5.3 (EarlyWarningSignal), § 6.11 (Dossier), § 9 (Audit trail), § 11
(ReasonerTuple).

All schema_versions are pinned to `v0.1` for the v1 release. New fields
require a schema-version bump and golden-fixture extension.
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


# ─── L3 / L4 / L5 — pathway sets ───────────────────────────────────────


class PathwayStep(BaseModel):
    model_config = ConfigDict(extra="forbid")
    reaction_id: str  # Rhea or MetaNetX MNXref ID
    substrates: list[str]  # InChIKey list
    products: list[str]
    ec_class: str | None = None
    enzyme_uniprot_id: str | None = None
    delta_g_kj_mol: float = 0.0
    thermodynamic_feasibility_at_default_concs: bool = True
    novelty_class: Literal["known_reaction", "reaction_class_known", "fully_novel"] = "known_reaction"


class PathwayCandidate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    pathway_id: str
    target_compound_inchi_key: str
    steps: list[PathwayStep]
    length: int
    precursor_compound_inchi_key: str
    retrosynthesis_tools_proposing: list[Literal["retropath3", "novostoic2", "bionavi", "deepretro", "genie_cat"]] = Field(default_factory=list)
    cross_tool_disagreement_signal: float = 0.0


class PathwayCandidateSet(BaseModel):
    """L3 output, L3.5 input."""

    model_config = ConfigDict(extra="forbid")
    schema_version: Literal["synbio.pathway_candidate_set.v0.1"] = "synbio.pathway_candidate_set.v0.1"
    candidates: list[PathwayCandidate]


class CIBounds(BaseModel):
    model_config = ConfigDict(extra="forbid")
    p05: float
    p50: float
    p95: float


class KineticEstimate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    enzyme: str
    value: float
    ci90_lower: float
    ci90_upper: float
    ensemble: list[Literal["DLKcat", "CatPred", "TurNuP", "CEKM"]]


class ToxicIntermediateFlag(BaseModel):
    model_config = ConfigDict(extra="forbid")
    intermediate_inchi_key: str
    qsar_alert: str
    confidence: float


class FalsifierResultRef(BaseModel):
    model_config = ConfigDict(extra="forbid")
    falsifier_id: str
    triggered: bool
    severity: Literal["warn", "fail"]
    gate_action: str
    message: str = ""


class ScoredPathway(PathwayCandidate):
    """L4 deep-evaluation output for a single pathway."""

    fba_flux_dict: dict[str, float] = Field(default_factory=dict)
    mdf_score_kj_mol: float = 0.0
    kcat_estimates: list[KineticEstimate] = Field(default_factory=list)
    km_estimates: list[KineticEstimate] = Field(default_factory=list)
    metabolic_burden_score: float = 0.0
    toxic_intermediate_flags: list[ToxicIntermediateFlag] = Field(default_factory=list)
    competing_pathway_drain_map: dict[str, float] = Field(default_factory=dict)
    fluxgat_essentiality: dict[str, Any] = Field(default_factory=dict)
    cross_model_kinetics_disagreement: float = 0.0
    cross_model_fba_disagreement: float = 0.0
    uncertainty_envelope: dict[str, CIBounds] = Field(default_factory=dict)
    falsifier_results: list[FalsifierResultRef] = Field(default_factory=list)


class ScoredPathwaySet(BaseModel):
    """L4 output."""

    model_config = ConfigDict(extra="forbid")
    schema_version: Literal["synbio.scored_pathway_set.v0.1"] = "synbio.scored_pathway_set.v0.1"
    candidates: list[ScoredPathway]


class RankedPathway(ScoredPathway):
    pareto_rank: int = 0
    expected_titer_g_l: CIBounds | None = None
    expected_yield_mol_mol: CIBounds | None = None
    expected_burden_au: CIBounds | None = None
    surrogate: Literal["gp_hamming", "deep_ensemble", "bnn"] = "gp_hamming"
    surrogate_calibration_score: float = 0.0


class ValidationExperiment(BaseModel):
    model_config = ConfigDict(extra="forbid")
    experiment_id: str
    intervention: dict[str, Any]
    expected_information_gain_nats: float
    consumer: Literal["human_cro", "strateos_api", "emerald_api", "cellfree_txtl_stub", "wetlab_phase2"]
    cost_estimate_usd: float
    expected_completion_days: int


class ValidationSequence(BaseModel):
    model_config = ConfigDict(extra="forbid")
    schema_version: Literal["synbio.validation_sequence.v0.1"] = "synbio.validation_sequence.v0.1"
    ordered_experiments: list[ValidationExperiment]
    go_cbed_objective: Literal["max_titer", "max_yield", "min_burden", "balanced"]
    posterior_uncertainty_kl_reduction_target: float


class RankedPathwaySet(BaseModel):
    """L5 output."""

    model_config = ConfigDict(extra="forbid")
    schema_version: Literal["synbio.ranked_pathway_set.v0.1"] = "synbio.ranked_pathway_set.v0.1"
    candidates: list[RankedPathway]
    validation_sequence: ValidationSequence


# ─── L6 — GeneticModificationSpec (SBOL3-attested) ──────────────────────


class HostOrganism(BaseModel):
    model_config = ConfigDict(extra="forbid")
    taxonomy_id: int
    refseq_genome_accession: str
    gem_id: str


class Knockout(BaseModel):
    model_config = ConfigDict(extra="forbid")
    gene_id: str
    locus_tag: str
    predicted_burden_delta: float
    source_refs: list[str] = Field(default_factory=list)


class Knockin(BaseModel):
    model_config = ConfigDict(extra="forbid")
    gene_id: str
    sequence: str  # nucleotide sequence
    promoter: str
    rbs: str
    terminator: str
    integration_site: str
    codon_optimization_plan: str = ""


class Upregulation(BaseModel):
    model_config = ConfigDict(extra="forbid")
    gene_id: str
    target_fold_change: float
    mechanism: Literal["promoter_swap", "RBS_swap", "dCas9_VPR", "ARTP"]


class Downregulation(BaseModel):
    model_config = ConfigDict(extra="forbid")
    gene_id: str
    mechanism: Literal["CRISPRi", "antisense", "dCas9_KRAB"]
    target_fold_change: float


class CofactorBalancing(BaseModel):
    model_config = ConfigDict(extra="forbid")
    cofactor: str
    target_ratio: float
    mechanism: str


class CodonOptimization(BaseModel):
    model_config = ConfigDict(extra="forbid")
    host_codon_table: str
    cai_target: float
    cai_predicted: float


class RbsPrediction(BaseModel):
    model_config = ConfigDict(extra="forbid")
    tool: Literal["rbs_calculator_v1_0_gpl_subprocess", "ostir", "denovodna_v2_commercial"]
    initiation_rate_au: float
    confidence: float


class CrisprGrna(BaseModel):
    model_config = ConfigDict(extra="forbid")
    spacer: str
    pam: str
    predicted_efficiency: float
    off_target_score: float


class SbolAttestation(BaseModel):
    model_config = ConfigDict(extra="forbid")
    document_sha256: str
    libsbolj3_validation_status: Literal["pass", "warn", "fail"]
    prov_o_chain_uri: str


class Modifications(BaseModel):
    model_config = ConfigDict(extra="forbid")
    knockouts: list[Knockout] = Field(default_factory=list)
    knockins: list[Knockin] = Field(default_factory=list)
    upregulations: list[Upregulation] = Field(default_factory=list)
    downregulations: list[Downregulation] = Field(default_factory=list)
    cofactor_balancing: list[CofactorBalancing] = Field(default_factory=list)


class GeneticModificationSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")
    schema_version: Literal["synbio.gms.v0.1"] = "synbio.gms.v0.1"
    spec_id: str
    host_organism: HostOrganism
    sbol3_uri: str
    synbiohub_uri: str | None = None
    modifications: Modifications
    codon_optimization: CodonOptimization
    rbs_predictions: RbsPrediction
    crispr_grnas: list[CrisprGrna] = Field(default_factory=list)
    sbol_attestation: SbolAttestation


# ─── L6_BUILD — CellFreeTXTLObservation ─────────────────────────────────


class CellFreeMeasurements(BaseModel):
    model_config = ConfigDict(extra="forbid")
    transcription_rate_au: float | None = None
    translation_rate_au: float | None = None
    soluble_protein_yield_ug_ml: float | None = None
    target_substrate_conversion_pct: float | None = None
    byproduct_formation_au: dict[str, float] | None = None


class CellFreeTXTLObservation(BaseModel):
    model_config = ConfigDict(extra="forbid")
    schema_version: Literal["synbio.cftxtl.v0.1"] = "synbio.cftxtl.v0.1"
    observation_id: str
    source_spec_id: str
    platform: Literal["mytxtl", "purexpress", "other"]
    cloud_lab_provider: Literal["strateos", "emerald", "none_stub"]
    reaction_volume_ul: float
    duration_min: int
    measurements: CellFreeMeasurements
    uncertainty: dict[str, Any] = Field(default_factory=dict)
    falsifier_status: Literal["pass", "warn", "fail"] = "pass"
    in_vivo_corroboration: Literal["present", "absent"] = "absent"


# ─── Cross-model disagreement and early warning ────────────────────────


class CrossModelDisagreementRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")
    schema_version: Literal["synbio.disagreement.v0.1"] = "synbio.disagreement.v0.1"
    record_id: str
    envelope_id: str
    layer: str
    quantity: str
    unit: str
    models_compared: list[str]
    values: list[float]
    uncertainties: list[float]
    metric: Literal["absolute", "relative", "sigma_normalized", "jaccard", "wasserstein"]
    pass_threshold: float
    warn_threshold: float
    fail_threshold: float
    status: Literal["pass", "warn", "fail", "quarantine"]
    resolution_action: Literal[
        "rerun",
        "add_reference_model",
        "block_handoff",
        "escalate_to_unknown_enzyme",
        "escalate_to_blind_eval",
    ]


class WindowSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")
    length_min: float
    stride_min: float
    embedding_dim: int
    delay_min: float


class TDAFeatures(BaseModel):
    model_config = ConfigDict(extra="forbid")
    persistence_entropy: float
    max_lifetime_h0: float
    max_lifetime_h1: float
    bottleneck_delta: float
    landscape_delta: float


class EarlyWarningSignal(BaseModel):
    model_config = ConfigDict(extra="forbid")
    schema_version: Literal["synbio.early_warning.v0.1"] = "synbio.early_warning.v0.1"
    signal_id: str
    source_envelope_id: str
    domain: Literal["cellfree_txtl", "in_cell_dbtl", "industrial_scale_simulated"]
    window_spec: WindowSpec
    features: TDAFeatures
    warning_score: float
    lead_time_estimate_min: float
    false_positive_rate_estimate: float
    status: Literal["normal", "watch", "warn", "fail"]
    failure_modes: list[
        Literal[
            "oxygen_transfer_collapse",
            "byproduct_buildup",
            "growth_stall",
            "toxicity_threshold_crossing",
            "nutrient_depletion",
        ]
    ] = Field(default_factory=list)


# ─── L7 — Dossier ───────────────────────────────────────────────────────


class DossierLiteratureRef(BaseModel):
    model_config = ConfigDict(extra="forbid")
    title: str
    doi: str | None = None
    pubmed_id: str | None = None
    license_class: Literal["A", "B", "C", "D", "E"]
    quote: str | None = None  # only short quotes; full-text never embedded


class DossierKpiPrediction(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str  # "predicted_titer_g_l", "predicted_yield_mol_mol", "burden_au"
    unit: str
    distribution: Literal["normal", "lognormal", "empirical", "ensemble", "posterior"]
    p05: float
    p50: float
    p95: float
    contributors: list[str]


class Dossier(BaseModel):
    """L7 output. Pydantic v2-validated, SBOL3-attested, PROV-O-anchored,
    sha256-hash-chained."""

    model_config = ConfigDict(extra="forbid")
    schema_version: Literal["synbio.dossier.v0.1"] = "synbio.dossier.v0.1"
    boundary: str  # canonical block; verified at envelope level
    dossier_id: str
    campaign_id: str
    dbtl_round: int = 0  # 0 = single-shot; >0 = closed-loop round N
    target_compound_inchi_key: str
    host_organism: HostOrganism
    domain: str
    ranked_pathway_set_envelope_id: str
    gms_envelope_id: str
    cftxtl_observation_envelope_ids: list[str] = Field(default_factory=list)
    kpi_predictions: list[DossierKpiPrediction]
    validation_sequence: ValidationSequence
    falsifier_summary: list[FalsifierResultRef] = Field(default_factory=list)
    cross_model_disagreement_summary: list[CrossModelDisagreementRecord] = Field(default_factory=list)
    early_warning_summary: list[EarlyWarningSignal] = Field(default_factory=list)
    literature_refs: list[DossierLiteratureRef] = Field(default_factory=list)
    sbol_attestation_uri: str  # path to the SBOL3 doc attesting the GMS
    prov_o_chain_uri: str
    sha256_hash_chain: list[str]  # ordered chain of sha256 hashes across the canonical fields
    advisory_only: bool = True  # default True; PRD §3.2 DSLNT case requires it
    consumer_recommendation: Literal["human_cro", "strateos_api", "emerald_api", "cellfree_txtl_stub", "wetlab_phase2"] = "human_cro"


# ─── ReasonerTuple — PathGym training point ────────────────────────────


class ReasonerTuple(BaseModel):
    model_config = ConfigDict(extra="forbid")
    schema_version: Literal["synbio.reasoner_tuple.v0.1"] = "synbio.reasoner_tuple.v0.1"
    tuple_id: str
    campaign_id: str
    problem_context: str
    input_spec_ref: str
    tool_plan: dict[str, Any]
    simulation_request_ref: str
    raw_result_ref: str
    reduced_observables_ref: str
    falsifier_results: list[str]
    disagreement_records: list[str]
    ground_truth_ref: str | None = None
    outcome_label: Literal["pass", "fail", "inconclusive", "superseded"]
    rights_label: Literal["tier_1_customer", "tier_2_aggregated", "tier_3_public"]
    next_action: str


# ─── SourceManifest (audit/source_manifests/) ──────────────────────────


class SourceManifest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    schema_version: Literal["synbio.source_manifest.v0.1"] = "synbio.source_manifest.v0.1"
    source_id: str
    uri: str
    retrieval_method: Literal["api", "git", "hf", "manual", "fixture", "claude_deep_research"]
    retrieved_at: str  # ISO-8601
    license_spdx_or_text: str
    license_class: Literal["A", "B", "C", "D", "E"]
    allowed_use: Literal["research", "commercial", "noncommercial", "unknown"]
    geography_restrictions: str | None = None
    checksum: str
    local_slice_size_mb: float
    hf_mirror_uri: str | None = None
    bulk_data_stored_locally: bool = False
    citation: str
    rights_notes: str = ""
    excluded_from_training_corpus: bool = False


__all__ = [
    "PathwayStep",
    "PathwayCandidate",
    "PathwayCandidateSet",
    "CIBounds",
    "KineticEstimate",
    "ToxicIntermediateFlag",
    "FalsifierResultRef",
    "ScoredPathway",
    "ScoredPathwaySet",
    "RankedPathway",
    "ValidationExperiment",
    "ValidationSequence",
    "RankedPathwaySet",
    "HostOrganism",
    "Knockout",
    "Knockin",
    "Upregulation",
    "Downregulation",
    "CofactorBalancing",
    "CodonOptimization",
    "RbsPrediction",
    "CrisprGrna",
    "SbolAttestation",
    "Modifications",
    "GeneticModificationSpec",
    "CellFreeMeasurements",
    "CellFreeTXTLObservation",
    "CrossModelDisagreementRecord",
    "WindowSpec",
    "TDAFeatures",
    "EarlyWarningSignal",
    "DossierLiteratureRef",
    "DossierKpiPrediction",
    "Dossier",
    "ReasonerTuple",
    "SourceManifest",
]
