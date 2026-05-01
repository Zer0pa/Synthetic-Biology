// Zer0pa Synthetic Biology — Knowledge Graph schema (Cypher)
//
// Reference: PRD.md § 9 Audit trail and KG, § 9.2 KG nodes, § 9.3 KG edges.
//
// This file is the canonical schema. The audit writer (zer0pa_synbio.audit)
// emits node/edge rows into `kg/nodes.csv` and `kg/edges.csv`; export to
// GraphML and RDF lives under `kg/exports/`. Neo4j is optional and not
// blocking; the CSV + GraphML + RDF surface is the source-of-truth.

// ─── Boundary attestation node ───────────────────────────────────────────
// Every campaign carries a Boundary node attesting the boundary text hash;
// every other node DERIVED_FROM it. f000_boundary_violation fires if any
// path from a node to its Boundary attestation breaks.
CREATE CONSTRAINT boundary_id IF NOT EXISTS FOR (b:Boundary) REQUIRE b.sha256 IS UNIQUE;

// ─── Constraints (uniqueness) ───────────────────────────────────────────
CREATE CONSTRAINT compound_inchi_key IF NOT EXISTS FOR (c:Compound) REQUIRE c.inchi_key IS UNIQUE;
CREATE CONSTRAINT reaction_id IF NOT EXISTS FOR (r:Reaction) REQUIRE r.reaction_id IS UNIQUE;
CREATE CONSTRAINT pathway_id IF NOT EXISTS FOR (p:Pathway) REQUIRE p.pathway_id IS UNIQUE;
CREATE CONSTRAINT enzyme_uniprot IF NOT EXISTS FOR (e:Enzyme) REQUIRE e.uniprot_id IS UNIQUE;
CREATE CONSTRAINT organism_taxonomy IF NOT EXISTS FOR (o:Organism) REQUIRE o.taxonomy_id IS UNIQUE;
CREATE CONSTRAINT strain_id IF NOT EXISTS FOR (s:Strain) REQUIRE s.strain_id IS UNIQUE;
CREATE CONSTRAINT modification_id IF NOT EXISTS FOR (m:Modification) REQUIRE m.modification_id IS UNIQUE;
CREATE CONSTRAINT assay_id IF NOT EXISTS FOR (a:Assay) REQUIRE a.assay_id IS UNIQUE;
CREATE CONSTRAINT gms_id IF NOT EXISTS FOR (g:GeneticModificationSpec) REQUIRE g.spec_id IS UNIQUE;
CREATE CONSTRAINT cftxtl_id IF NOT EXISTS FOR (c:CellFreeTXTLObservation) REQUIRE c.observation_id IS UNIQUE;
CREATE CONSTRAINT dossier_id IF NOT EXISTS FOR (d:Dossier) REQUIRE d.dossier_id IS UNIQUE;
CREATE CONSTRAINT envelope_id IF NOT EXISTS FOR (e:Envelope) REQUIRE e.envelope_id IS UNIQUE;
CREATE CONSTRAINT sbol_id IF NOT EXISTS FOR (s:SBOLDocument) REQUIRE s.document_sha256 IS UNIQUE;
CREATE CONSTRAINT prov_activity_id IF NOT EXISTS FOR (a:ProvActivity) REQUIRE a.activity_id IS UNIQUE;
CREATE CONSTRAINT prov_agent_id IF NOT EXISTS FOR (a:ProvAgent) REQUIRE a.agent_id IS UNIQUE;
CREATE CONSTRAINT prov_entity_id IF NOT EXISTS FOR (e:ProvEntity) REQUIRE e.entity_id IS UNIQUE;
CREATE CONSTRAINT tool_adapter_id IF NOT EXISTS FOR (t:ToolAdapter) REQUIRE t.adapter_id IS UNIQUE;
CREATE CONSTRAINT model_checkpoint_id IF NOT EXISTS FOR (c:ModelCheckpoint) REQUIRE c.checkpoint_id IS UNIQUE;
CREATE CONSTRAINT simulation_run_id IF NOT EXISTS FOR (s:SimulationRun) REQUIRE s.run_id IS UNIQUE;
CREATE CONSTRAINT pathway_candidate_id IF NOT EXISTS FOR (p:PathwayCandidate) REQUIRE p.pathway_id IS UNIQUE;
CREATE CONSTRAINT scored_pathway_id IF NOT EXISTS FOR (p:ScoredPathway) REQUIRE p.pathway_id IS UNIQUE;
CREATE CONSTRAINT ranked_pathway_id IF NOT EXISTS FOR (p:RankedPathway) REQUIRE p.pathway_id IS UNIQUE;
CREATE CONSTRAINT validation_experiment_id IF NOT EXISTS FOR (e:ValidationExperiment) REQUIRE e.experiment_id IS UNIQUE;
CREATE CONSTRAINT falsifier_result_id IF NOT EXISTS FOR (f:FalsifierResult) REQUIRE f.result_id IS UNIQUE;
CREATE CONSTRAINT disagreement_record_id IF NOT EXISTS FOR (d:DisagreementRecord) REQUIRE d.record_id IS UNIQUE;
CREATE CONSTRAINT early_warning_id IF NOT EXISTS FOR (w:EarlyWarningSignal) REQUIRE w.signal_id IS UNIQUE;
CREATE CONSTRAINT license_finding_id IF NOT EXISTS FOR (l:LicenseFinding) REQUIRE l.finding_id IS UNIQUE;
CREATE CONSTRAINT rights_policy_id IF NOT EXISTS FOR (r:RightsPolicy) REQUIRE r.policy_id IS UNIQUE;
CREATE CONSTRAINT source_manifest_id IF NOT EXISTS FOR (s:SourceManifest) REQUIRE s.source_id IS UNIQUE;
CREATE CONSTRAINT reasoner_tuple_id IF NOT EXISTS FOR (t:ReasonerTuple) REQUIRE t.tuple_id IS UNIQUE;
CREATE CONSTRAINT tda_diagram_id IF NOT EXISTS FOR (d:TDADiagram) REQUIRE d.diagram_id IS UNIQUE;
CREATE CONSTRAINT flux_graph_id IF NOT EXISTS FOR (g:FluxGraph) REQUIRE g.graph_id IS UNIQUE;
CREATE CONSTRAINT embedding_id IF NOT EXISTS FOR (e:Embedding) REQUIRE e.embedding_id IS UNIQUE;

// ─── Indexes ─────────────────────────────────────────────────────────────
CREATE INDEX compound_smiles IF NOT EXISTS FOR (c:Compound) ON (c.smiles);
CREATE INDEX compound_selfies IF NOT EXISTS FOR (c:Compound) ON (c.selfies);
CREATE INDEX reaction_ec_class IF NOT EXISTS FOR (r:Reaction) ON (r.ec_class);
CREATE INDEX enzyme_organism IF NOT EXISTS FOR (e:Enzyme) ON (e.organism_taxonomy_id);
CREATE INDEX falsifier_result_gate_status IF NOT EXISTS FOR (f:FalsifierResult) ON (f.gate_status);

// ─── Edge taxonomy (relationship types only — Cypher creates lazily) ────
// Per PRD §9.3:
//   catalyses, requires_cofactor, produces, consumes, encodes, regulates,
//   has_source, has_falsifier, has_audit, member_of_pathway,
//   instantiates_in_organism, measured_by, supports, contradicts,
//   DERIVED_FROM, USED_TOOL, USED_MODEL, USED_SOURCE, PRODUCED,
//   VALIDATED_BY, FAILED_BY, DISAGREES_WITH, FEEDS_L4, FEEDS_L5,
//   ATTESTED_BY_SBOL, PROV_GENERATED, PROV_USED, PROV_WAS_DERIVED_FROM,
//   RIGHTS_CONSTRAINED_BY, OWNED_BY
// (Cypher does not enforce edge-type constraints at schema time; consumer
// code under src/zer0pa_synbio/kg/ enforces them.)
