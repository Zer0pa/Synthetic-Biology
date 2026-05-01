# Synthetic Biology — Metabolic Pathway Engineering Pipeline · PRD v1.0

**Workstream:** Synthetic Biology / Metabolic Pathway Engineering (Pipeline 4 of 6)
**Author:** Synbio orchestrator (Claude Opus 4.7, 1M context), 2026-05-01
**Inherits from:** `HANDOFF-TO-ORCHESTRATOR.md`, `synthesis/01-fresh-eyes-on-synbio-briefs.md`, `source-briefs/00..02`
**For:** Overnight executor agents on a Runpod-bound machine, autonomous long-horizon execution, no interim reporting, GitHub + Hugging Face are the review surfaces.
**Status:** All decisions locked. Process theater stripped. The agent reads this once and executes end-to-end.

---

## 0. Boundary

Research infrastructure for in silico synthetic biology / metabolic pathway engineering. Outputs are research artifacts — predicted pathways, predicted KPIs, candidate genetic modification specifications. No regulatory certification claims. No clinical or human-subject use. No environmental release of GMOs. No biocontainment-level claims (the pipeline does not commission BSL-2/3 work). No human gene drive or eugenic application. Defence / weapons / dual-use bio applications excluded under operator policy.

This block appears verbatim in every artifact, every envelope, and every dossier. Any output that does not carry it is invalid.

## 1. Operator mandate (binding, verbatim)

1. **Anti-toy. Anti-MVP. Anti-first-paying-customer.** This is R&D pushing boundaries. Build the most overdesigned, best-in-class, science-and-evidence-anchored pipeline the team has ever shipped. There is no "ship it cheap" version.
2. **110% before Runpod.** Front-load every CPU-side artifact. When Runpod comes online the cutover is a config flag, not an architectural rewrite. If a layer can be built CPU-side, it is built CPU-side. If a layer cannot, a REST stub returns shape-correct canned outputs that pass golden-fixture invariance under `httpx.MockTransport`.
3. **Long-horizon overnight execution from GitHub.** The executor runs on a different machine and treats GitHub as the only canonical input. The operator is asleep. The agent does not interim-report, does not ask for routine permission, and does not engage the user until it has completed the PRD end to end or hit a genuine boundary/credential blocker that prevents all useful work. The agent decides every contested call autonomously using the discipline in this PRD. The agent updates GitHub continuously and Hugging Face for bulk artifacts. The operator reviews from a different machine.
4. **GitHub is canonical. Hugging Face is the bulk-artifact mirror.** All code, schemas, fixtures, audit logs, KG exports, dossiers, and human-readable artifacts go to `Zer0pa/Synthetic-Biology` on GitHub. All bulk datasets, model weights, training corpora, large fixtures, and trained artifacts go to Hugging Face under user **Architect-Prime** (HF user, not Zer0pa org). HF token at `~/.cache/huggingface/token` on the originating machine; on the Runpod machine the operator provides via env var `HF_TOKEN`.
5. **All prompts the agent needs are in the repo.** This PRD, the HANDOFF, the per-layer briefs in `briefs/`, the resistance protocol in `RESISTANCE.md`, the modus operandi in `MODUS-OPERANDI.md`, and the source-briefs in `source-briefs/` together constitute the agent's complete cold-start context. No other context is required. The agent may augment any of these documents, but every augmentation lands in `Zer0pa/Synthetic-Biology` before the next phase begins.
6. **Resistance.md is binding.** Every executor agent reads `RESISTANCE.md` first and carries the four anti-corruption protocols (`fp-shapematchRE`, `fp-rushtoend`, `fp-NULLasout`, `fp-flatteryasfreedom`, `fp-approvalseek`, `fp-shapematch`, `fp-efficiency-as-corner-cutting`) as binding meta-discipline.
7. **No cross-workstream runtime co-dependency.** Sibling repos `Zer0pa/Health`, `Zer0pa/Materials`, `Zer0pa/Energy` may be read for fork-and-own pattern reuse; their HF Spaces may be referenced as documents. The agent **must not** import from a sibling repo at runtime, share a database/corpus with a sibling, or share a service instance. Fork-and-own is required: copy the pattern, reimplement inside Synthetic Biology.
8. **Fork-and-own is required, not optional.** The agent steals patterns from Energy's `UniversalLayerEnvelope`, Materials' `UniversalLayerEnvelope`, Health's `runtime/cloud_lab.config.yaml`, Energy's `CrossModelDisagreementRecord`, and Energy's TDA early-warning. The agent reimplements each inside the synbio repo, stripped of cross-workstream coupling.
9. **Decisions are locked.** Where the synthesis surfaced "open questions for the orchestrator," this PRD resolves them. Where this PRD says "v1," it means "v1 of this pipeline at maximum sophistication" — not "minimum viable v1." There is no v1.1 deferral except where physical hardware does not exist (wet-lab execution, quantum hardware).

## 2. Source basis

Read in this order, then begin:

1. `RESISTANCE.md` — anti-corruption discipline. Read first. Carried as binding meta-protocol throughout execution.
2. This document, `PRD.md` — the full execution spec.
3. `HANDOFF-TO-OVERNIGHT-EXECUTOR.md` — what you inherit, produce, the authorities you operate under.
4. `OVERNIGHT-EXECUTOR-STARTUP-PROMPT.md` — paste-ready cold-start prompt for the different machine.
5. `MODUS-OPERANDI.md` — pattern, role chain, parallel-exploration principle, fork-and-own permission.
6. `HANDOFF-TO-ORCHESTRATOR.md` — context for why this PRD looks the way it does. Operator override on cross-workstream substrate sharing is binding.
7. `synthesis/01-fresh-eyes-on-synbio-briefs.md` — the synthesis agent's twelve specific gaps and pressure-test points; this PRD has resolved each.
8. `source-briefs/00-research-agent-handover-note.md` — the research agent's framing.
9. `source-briefs/02-corrections-and-architecture.md` — the four-column license decomposition, LDBT paradigm, causal OED node, PathGym flywheel, and the typed seven-layer architecture.
10. `source-briefs/01-full-technology-landscape.md` — the full pipeline catalogue (read in chunks; not required for cold-start of every sub-agent).
11. Sibling repos `Zer0pa/Health`, `Zer0pa/Materials`, `Zer0pa/Energy` — fork-and-own reference at the dependency level.

The orchestrator (this document's author) ran seven deep-research verifications and locked the seven license items in §22. Those resolutions are binding.

## 3. Scope and scientific validation triple

### 3.1 Scope

The pipeline is built end-to-end at maximum sophistication. **Every layer is fully implemented CPU-side. Every GPU layer has a REST stub returning shape-correct canned outputs validated against the same envelope schema as the production endpoint.** The cutover to Runpod is a config flag — `SYNBIO_<LAYER>_BACKEND=stub|local_cpu|gpu_rest_stub|runpod_rest`.

In scope for v1:
- L1 ZPE adapter, L2 LIRC corpus, L3 retrosynthesis multi-tool, L3.5 learnable ranking gate, L4 in silico screening (FBA, kinetics ensemble, MDF, gene-essentiality, toxic intermediate), L5 multi-fidelity BoTorch + causal OED, L6 host engineering with SBOL3-attested `GeneticModificationSpec`, L7 dossier with closed-loop active-inference completion.
- The CEKM (Conditional Enzyme Kinetics Model) Zer0pa-owned, trained with adversarial three-tier synthetic negatives and held-out blind eval.
- The Unknown Enzyme Generative Sub-Pipeline (RFdiffusion3 + Baker catalytic motif scaffolding + MACE-OFF + ProDy NMA + eQuilibrator ΔrG). Full implementation, not advisory.
- The PathGym DBTL benchmark scaffold and growing corpus with each engagement.
- The cell-free TX-TL adapter, three implementations (`CellFreeStubAdapter`, `StrateosMyTXTLAdapter` dry-run, `EmeraldPURExpressAdapter` dry-run). Phase 2 wet-lab cutover behind the same interface.
- The Zer0pa Synbio Audit-Trail Specification v0.1 (SBOL3 + PROV-O extension), drafted and committed as a Zer0pa-published standard.
- TDA early-warning for fermentation regime change, fork-and-own from Energy.
- Three-tier falsifier hierarchy (Fast / Medium / Heavy), cross-model disagreement as a first-class quantity, full falsifier registry with at least 18 named falsifiers.
- Closed-loop dossier mode (DBTL rounds post back; BoTorch surrogate updates; round-N+1 dossier emits with refined ranking and new validation sequence). Closed-loop is the active-inference completion; v1 ships with closed-loop, not single-shot.

Out of scope for v1 (physical-hardware-gated, not engineering-effort-gated):
- Real wet-lab execution (Phase 2 cutover behind the cell-free TX-TL adapter).
- Real quantum hardware execution (BlockedSourceManifest with three concrete slots; permanent Class E flags).
- Real industrial-scale fermentation telemetry (no open dataset; CFD correction layer ships as forward-mechanistic, not learned).

### 3.2 Scientific validation triple (HMO seed test)

The pipeline's correctness is established against a triple of named systems chosen so the engine's failure modes are exposed rather than hidden. The triple is portable: every customer engagement re-runs the same known-good / known-borderline / novel discipline against the customer's target portfolio. For internal validation, the triple is **HMOs (Human Milk Oligosaccharides), in *E. coli* iML1515**:

| Seed | System | Status | Pre-registered acceptance threshold |
|---|---|---|---|
| 1 | **2'-fucosyllactose (2'-FL)** | Known-good. Multiple published *E. coli* high-titer strains; gram/L titers literature-anchored. | Engine's predicted titer falls within ±25% of the median literature value for the closest-matching engineered strain. CEKM kcat predictions for the α-1,2-fucosyltransferase fall within ±0.5 log units of BRENDA-reported. MDF score ≥ 1.0 kJ/mol. Cross-model disagreement (DLKcat vs CatPred vs TurNuP) below threshold. |
| 2 | **3'-sialyllactose (3'-SL)** | Known-borderline. *E. coli* production demonstrated; CMP-Neu5Ac cofactor balance is the documented pain point. | Engine's predicted-titer 90% credible interval covers the literature value. The dossier explicitly identifies cofactor-balance as the dominant uncertainty contributor (not "model is uncertain everywhere"). The validation sequence proposes the CMP-Neu5Ac regeneration pathway as the highest-information-gain next intervention. |
| 3 | **Disialyllacto-N-tetraose (DSLNT)** | Novel. Clinical interest (necrotizing-enterocolitis prevention research); no published *E. coli* gram/L titer; stresses both sialyl- and elongation-transferase paths simultaneously. | Engine produces a defensible novel-pathway prediction with a calibrated uncertainty band. The retrosynthesis layer returns ≥3 distinct candidate routes with ranked thermodynamic feasibility. At least one route either (a) recovers a known-but-unlinked transferase from the LIRC corpus, or (b) routes through the Unknown Enzyme Generative Sub-Pipeline with a Tier-2 (reaction class known, no TS analog) classification. The dossier flags the prediction as "advisory; experimental validation required" and emits a closed-loop validation sequence that an external CRO can execute. |

The triple is not optional. The HMO seed evidence packet is committed to the repo as `validation/hmo-seed-evidence/`. Each seed's results land as a Pydantic-validated dossier plus the underlying envelope chain. Cross-model disagreement records and falsification ledger entries are committed alongside.

## 4. Architecture invariants

### 4.1 UniversalLayerEnvelope (synbio-shaped)

Every adapter, simulator, MCP server, and LLM-assisted tool emits a `UniversalLayerEnvelope`. Tool-native objects must not cross layer boundaries.

```yaml
UniversalLayerEnvelope:
  schema_version: "synbio.envelope.v0.1"
  boundary: "Research infrastructure for in silico synthetic biology / metabolic pathway engineering. Outputs are research artifacts — predicted pathways, predicted KPIs, candidate genetic modification specifications. No regulatory certification claims. No clinical or human-subject use. No environmental release of GMOs. No biocontainment-level claims (the pipeline does not commission BSL-2/3 work). No human gene drive or eugenic application. Defence / weapons / dual-use bio applications excluded under operator policy."
  envelope_id: "sha256:<canonical-json>"
  campaign_id: string                          # one customer engagement / internal validation run
  run_id: uuid
  layer: L1 | L2 | L3 | L3_5 | L4 | L5 | L5_OED | L6 | L6_BUILD | L7
  domain: industrial_chemical | specialty_chemical | saf | pharma_intermediate | hmo | other
  organism: ncbi_taxonomy_id                    # e.g., 562 for E. coli
  gem_id: string                                # e.g., iML1515, Yeast9, ModelSEED-rebuild
  mode: scientific | engineering_stub | replay | validation
  backend:
    adapter: string
    tool: string
    tool_version: string
    execution_mode: local_cpu | isolated_cpu | gpu_rest_stub | runpod_rest | external_service | cloud_lab_dry_run | cloud_lab_wet
    license_class: A | B | C | D | E
    license_evidence_uri: string
  inputs:
    refs: [{type, uri, sha256, schema_version}]
    payload: object
  outputs:
    refs: [{type, uri, sha256, schema_version}]
    payload: object
  uncertainty:
    distribution: none | normal | lognormal | empirical | ensemble | posterior
    p05: object
    p50: object
    p95: object
    contributors: [L1, L2, L3, L3_5, L4, L5, data, surrogate, cross_model]
  falsification:
    gate_status: pass | warn | fail | quarantine
    scientific_valid: boolean
    cross_model_disagreement: object
    unit_check_passed: boolean
    mass_balance_check_passed: boolean
    boundary_check_passed: boolean
    sbol_attestation_present: boolean          # required for L6 envelopes
    failures: [{gate_id, severity, message, evidence_uri}]
  provenance:
    agent_id: string
    model_id: string
    git_sha: string
    created_at: ISO-8601
    input_hash: sha256
    output_hash: sha256
    config_hash: sha256
    artifact_hashes: [sha256]
    source_refs: [uri]
    sbol_uri: string | null                    # SynBioHub or local SBOL3 file path; required for L6/L7
    prov_o_jsonld: string                       # PROV-O JSON-LD provenance block
```

Required tests (golden fixtures committed before any work proceeds):
- Missing or altered boundary fails closed.
- Canonical JSON roundtrip preserves all hashes.
- Stub, CPU, and Runpod response bodies validate against the same schema.
- Class C/D/E backends cannot be promoted to product mode without an explicit `license_grant` record committed under `audit/license_grants/`.
- Stubs may satisfy engineering acceptance only; they may not set `scientific_valid=true`.
- L6 envelopes lacking `sbol_attestation_present=true` fail closed.

### 4.2 GeneticModificationSpec (SBOL3-attested)

The L6 envelope's payload is a `GeneticModificationSpec` that is structurally an SBOL3 document. The Pydantic schema enforces SBOL3 conformance and round-trips through `libSBOLj3`.

```yaml
GeneticModificationSpec:
  schema_version: "synbio.gms.v0.1"
  spec_id: string
  host_organism:
    taxonomy_id: int
    refseq_genome_accession: string
    gem_id: string
  sbol3_uri: string                              # local SBOL3 file path (required)
  synbiohub_uri: string | null                   # SynBioHub publication URI (optional v1)
  modifications:
    knockouts: [{gene_id, locus_tag, predicted_burden_delta, source_refs}]
    knockins: [{gene_id, sequence, promoter, RBS, terminator, integration_site, codon_optimization_plan}]
    upregulations: [{gene_id, target_fold_change, mechanism: promoter_swap | RBS_swap | dCas9_VPR | ARTP}]
    downregulations: [{gene_id, mechanism: CRISPRi | antisense | dCas9_KRAB, target_fold_change}]
    cofactor_balancing: [{cofactor, target_ratio, mechanism}]
  codon_optimization:
    host_codon_table: string
    cai_target: float
    cai_predicted: float
  rbs_predictions:
    tool: rbs_calculator_v1_0_gpl_subprocess | ostir | denovodna_v2_commercial
    initiation_rate_au: float
    confidence: float
  crispr_grnas: [{spacer, pam, predicted_efficiency, off_target_score}]
  sbol_attestation:
    document_sha256: string
    libsbolj3_validation_status: pass | warn | fail
    prov_o_chain_uri: string
```

Falsifier `valid_sbol_only` rejects any `GeneticModificationSpec` whose SBOL3 document does not parse via `libsbolj3`'s validator at strict mode.

### 4.3 PathwayCandidateSet, ScoredPathwaySet, RankedPathwaySet, ValidationSequence

```yaml
PathwayCandidateSet:                           # L3 output, L3.5 input
  candidates: [{
    pathway_id: string,
    target_compound_inchi_key: string,
    steps: [{
      reaction_id: string,                      # Rhea or MetaNetX MNXref ID
      substrates: [InChI_key],
      products: [InChI_key],
      ec_class: string | null,
      enzyme_uniprot_id: string | null,
      delta_g_kj_mol: float,
      thermodynamic_feasibility_at_default_concs: bool,
      novelty_class: known_reaction | reaction_class_known | fully_novel
    }],
    length: int,
    precursor_compound_inchi_key: string,
    retrosynthesis_tools_proposing: [retropath3 | novostoic2 | bionavi | deepretro],
    cross_tool_disagreement_signal: float
  }]

ScoredPathwaySet:                              # L3.5 reject pass, then L4 deep evaluation
  candidates: [PathwayCandidate + {
    fba_flux_dict: object,
    mdf_score_kj_mol: float,
    kcat_estimates: [{enzyme, value, ci90_lower, ci90_upper, ensemble: [DLKcat, CatPred, TurNuP, CEKM]}],
    km_estimates: [{enzyme, value, ci90_lower, ci90_upper, ensemble}],
    metabolic_burden_score: float,
    toxic_intermediate_flags: [{intermediate_inchi_key, qsar_alert, confidence}],
    competing_pathway_drain_map: object,
    fluxgat_essentiality: object,
    cross_model_kinetics_disagreement: float,
    cross_model_fba_disagreement: float,
    uncertainty_envelope: CIBounds,
    falsifier_results: [FalsifierResult]
  }]

RankedPathwaySet:                              # L5 output
  candidates: [ScoredPathway + {
    pareto_rank: int,
    expected_titer_g_l: {p05, p50, p95},
    expected_yield_mol_mol: {p05, p50, p95},
    expected_burden_au: {p05, p50, p95},
    surrogate: gp_hamming | deep_ensemble | bnn,
    surrogate_calibration_score: float
  }]
  validation_sequence: ValidationSequence

ValidationSequence:                            # L5_OED output (causal OED node)
  ordered_experiments: [{
    experiment_id: string,
    intervention: object,                       # genetic edit or fermentation condition
    expected_information_gain_nats: float,
    consumer: human_cro | strateos_api | emerald_api | cellfree_txtl_stub | wetlab_phase2,
    cost_estimate_usd: float,
    expected_completion_days: int
  }]
  go_cbed_objective: max_titer | max_yield | min_burden | balanced
  posterior_uncertainty_kl_reduction_target: float
```

### 4.4 CellFreeTXTLObservation

The L_BUILD adapter emits `CellFreeTXTLObservation` envelopes that close the loop back to L5 in closed-loop dossier mode.

```yaml
CellFreeTXTLObservation:
  schema_version: "synbio.cftxtl.v0.1"
  observation_id: string
  source_spec_id: string                         # GeneticModificationSpec the observation refers to
  platform: mytxtl | purexpress | other
  cloud_lab_provider: strateos | emerald | none_stub
  reaction_volume_ul: float
  duration_min: int
  measurements:
    transcription_rate_au: float | null
    translation_rate_au: float | null
    soluble_protein_yield_ug_ml: float | null
    target_substrate_conversion_pct: float | null
    byproduct_formation_au: object | null
  uncertainty: object
  falsifier_status: pass | warn | fail
  in_vivo_corroboration: present | absent
```

### 4.5 Plug-replaceability invariant

Any layer backend may be replaced only if it preserves:
- The same `UniversalLayerEnvelope`.
- The same domain-payload schema version.
- The same REST endpoint shape and request/response surface.
- The same artifact manifest format.
- The same audit/KG writes (same node and edge taxonomy).
- The same falsifier IDs.

Runpod cutover is accepted only when changing a config flag from `gpu_rest_stub` to `runpod_rest` preserves golden fixture behavior except for runtime/provenance fields. The `httpx.MockTransport` golden-fixture invariance test (forked from Energy Wave 4) is the executable proof.

## 5. Falsification framework

### 5.1 Three-tier falsifier hierarchy (orchestrator's fresh-eyes addition)

Every pathway candidate runs through three tiers in sequence. Reject thresholds are themselves Bayesian-optimised against held-out PathGym partitions; thresholds are state, not constants. The hyperparameter optimisation runs nightly inside the same active-inference loop that updates the BoTorch surrogate.

**Tier A (Fast, < 100 ms per candidate, all candidates):**
- Invalid SELFIES (parse failure)
- Mass balance violation (atom count mismatch)
- MDF infeasibility (eQuilibrator MDF < 0 at any feasible concentration bound)
- Toxic intermediate flag (RDKit + structural-alert lookup)
- Gross stoichiometric infeasibility (cofactor flux > 10× native regeneration capacity)

**Tier B (Medium, < 10 s per candidate, top-100 after Tier A pass):**
- Cross-model kinetics disagreement above warn-threshold (DLKcat / CatPred / TurNuP / CEKM σ-normalised)
- Cross-model FBA disagreement above warn-threshold (COBRApy / GECKO / ECMpy / ETFL)
- Cross-model retrosynthesis disagreement (RetroPath3 / novoStoic2 / BioNavi / DeepRetro Jaccard)
- Novelty without retrosynthetic support (`fully_novel` + zero retrosynthesis-tool proposal → route to L4.5 unknown-enzyme sub-pipeline)
- Novelty without TS analog (`fully_novel` + no transition-state analog in LIRC → Tier 3 advisory in unknown-enzyme sub-pipeline)
- CEKM survivorship-bias check (predict on known-negative held-out partition; disagreement above threshold flags pathway for blind-eval review)
- Codec-as-mechanism analog (predicted KPI without mechanistic chain to genotype — every KPI prediction must trace to at least one genotype-level intervention)

**Tier C (Heavy, minutes per candidate, top-10 after Tier B pass):**
- RFdiffusion3 catalytic-motif feasibility (does a generated structure plausibly hold the catalytic geometry?)
- MACE-OFF binding energy plausibility (binding energy within physically reasonable bounds for analogous reactions)
- ProDy NMA conformational-suitability check (lowest-frequency normal modes align with catalytic coordinate)
- TDA fermentation regime-stability check (persistent homology over simulated fermentation time-series predicts stable regime, not regime change)
- Industrial-scale claim without calibrated corpus (any KPI prediction at industrial scale fails the gate unless cited corpus is class-A licensed and present)
- License drift (any pathway citing BKMS-react, KEGG bulk content, or any Class C/D/E source without an explicit license grant)

### 5.2 CrossModelDisagreementRecord (forked from Energy)

Cross-model disagreement is a first-class quantity, not an explanation after the fact.

```yaml
CrossModelDisagreementRecord:
  record_id: string
  envelope_id: string
  layer: L2 | L3 | L4_kinetics | L4_fba | L5_surrogate
  quantity: string                                # "kcat_h74t", "flux_through_PFL", "retrosynthesis_route"
  unit: string
  models_compared: [string]
  values: [number]
  uncertainties: [number]
  metric: absolute | relative | sigma_normalized | jaccard | wasserstein
  pass_threshold: number
  warn_threshold: number
  fail_threshold: number
  status: pass | warn | fail | quarantine
  resolution_action: rerun | add_reference_model | block_handoff | escalate_to_unknown_enzyme | escalate_to_blind_eval
```

Rules:
- Never average away a failed disagreement.
- `fail` blocks downstream L5 / L7 emission.
- `warn` may continue only with uncertainty inflation and explicit audit note in the dossier.
- Any output without units, uncertainty, source manifest, and falsifier status is invalid.

### 5.3 SynbioTDAEarlyWarning (fork-and-own from Energy)

Persistent homology over fermentation time-series flags regime change before the surrogate's mean prediction breaks. Default CPU path: `ripser.py` + `persim`. `giotto-tda` is AGPL and may not be embedded in product code.

```yaml
EarlyWarningSignal:
  signal_id: string
  source_envelope_id: string
  domain: cellfree_txtl | in_cell_dbtl | industrial_scale_simulated
  window_spec: {length_min, stride_min, embedding_dim, delay_min}
  features:
    persistence_entropy: float
    max_lifetime_h0: float
    max_lifetime_h1: float
    bottleneck_delta: float
    landscape_delta: float
  warning_score: float
  lead_time_estimate_min: float
  false_positive_rate_estimate: float
  status: normal | watch | warn | fail
  failure_modes: [oxygen_transfer_collapse, byproduct_buildup, growth_stall, toxicity_threshold_crossing, nutrient_depletion]
```

No regime-change warning may be accepted from a scalar classifier alone. The signal must preserve persistence diagrams or derived topological artifacts and pass no-leakage checks.

### 5.4 Falsifier registry (committed in `audit/falsifiers.yaml`)

Eighteen named falsifiers, each with `id`, `tier`, `description`, `severity`, `gate_action`, `evidence_schema`. The agent commits this YAML before any layer code is written.

```yaml
falsifiers:
  - {id: f001_invalid_selfies, tier: A, severity: fail, gate_action: reject_candidate}
  - {id: f002_mass_balance_violation, tier: A, severity: fail, gate_action: reject_candidate}
  - {id: f003_mdf_infeasibility, tier: A, severity: fail, gate_action: reject_candidate}
  - {id: f004_toxic_intermediate, tier: A, severity: warn, gate_action: flag_in_dossier}
  - {id: f005_stoichiometric_infeasibility, tier: A, severity: fail, gate_action: reject_candidate}
  - {id: f006_kinetics_disagreement_high, tier: B, severity: warn, gate_action: inflate_uncertainty}
  - {id: f007_fba_disagreement_high, tier: B, severity: warn, gate_action: inflate_uncertainty}
  - {id: f008_retrosynthesis_disagreement_high, tier: B, severity: warn, gate_action: rank_lower}
  - {id: f009_novelty_without_retrosynthesis, tier: B, severity: warn, gate_action: route_to_unknown_enzyme}
  - {id: f010_novelty_without_ts_analog, tier: B, severity: warn, gate_action: tier_3_advisory}
  - {id: f011_cekm_survivorship_bias_check, tier: B, severity: warn, gate_action: route_to_blind_eval}
  - {id: f012_codec_as_mechanism_analog, tier: B, severity: fail, gate_action: reject_candidate}
  - {id: f013_rfdiffusion3_motif_infeasible, tier: C, severity: warn, gate_action: rank_lower}
  - {id: f014_mace_off_binding_implausible, tier: C, severity: warn, gate_action: flag_in_dossier}
  - {id: f015_prody_nma_misaligned, tier: C, severity: warn, gate_action: flag_in_dossier}
  - {id: f016_tda_regime_change, tier: C, severity: warn, gate_action: flag_in_dossier}
  - {id: f017_industrial_scale_uncalibrated, tier: C, severity: fail, gate_action: reject_claim}
  - {id: f018_license_drift, tier: C, severity: fail, gate_action: reject_candidate_and_alert}
  - {id: f019_valid_sbol_only, tier: A, severity: fail, gate_action: reject_l6_envelope}
  - {id: f020_txtl_observation_without_in_vivo, tier: B, severity: warn, gate_action: route_to_phase_2}
```

The registry is the executable spec. New falsifiers require schema version bump and golden-fixture extension.

## 6. Layer contracts

### 6.1 Layer 1 — ZPE / Input encoding

- **Input:** `{target_compound: SELFIES + InChI_key, host_organism: ncbi_taxonomy_id + refseq_genome_accession + gem_id}`
- **Output:** `{zpe_word_envelope: 20-bit deterministic per-token, esm2_embedding: float[1280], gem_handle: string}`
- **Tools:** `selfies` (Apache 2.0), `RDKit` (BSD), `ESM-2` weights (MIT).
- **Backend:** `local_cpu` for SELFIES + ESM-2 batched inference (CPU-quantised; quantisation config committed). `gpu_rest_stub` for ESM-2 batched inference at scale; Runpod swap for production volumes.
- **Falsifiers:** f001 (invalid SELFIES), f018 (license drift if fallback to non-permissive embedding).
- **Plug-replaceability test:** swap `selfies` for canonical RDKit SMILES; envelope schema unchanged; downstream layers unaffected.

### 6.2 Layer 2 — Metabolic knowledge / LIRC corpus

- **Input:** `{target_inchi_key, organism_gem_id}`
- **Output:** `ReactionGraph` envelope: `{nodes: [Compound + Reaction + Enzyme], edges: [substrate-of, product-of, catalyses, requires-cofactor]}` reconciled across Rhea + MetaNetX MNXref 4.5 + BiGG + ModelSEED + BRENDA core CC BY 4.0.
- **Tools:** Rhea SPARQL (CC0), MetaNetX SPARQL (CC BY 4.0), BiGG REST (CC BY 4.0), ModelSEED (MIT), BRENDA bulk (CC BY 4.0).
- **Excluded:** BKMS-react (license), KEGG bulk content (license), ATLAS of Biochemistry (academic-subscription/reference-only; no redistribution or training-corpus inclusion without explicit grant; URL/DOI cross-reference only).
- **Construction:** the LIRC corpus build pipeline runs CPU-side. Bulk slices > 5 GB go to HF under `Architect-Prime/synbio-lirc-v0.1`. Local Mac stores manifests + metadata only. Reaction canonicalisation uses atom-mapped SMARTS; deduplication via MetaNetX MNXref 4.5 reconciliation. Coverage gap vs KEGG (estimated 20-30% on secondary metabolites) flagged in dossier per pathway citing the LIRC.
- **Falsifiers:** f018 (license drift), f005 (stoichiometric infeasibility on imported reaction), `f021_reaction_not_atom_balanced` (added to registry during build).
- **Plug-replaceability test:** swap MetaNetX for direct Rhea-only build; envelope schema unchanged; coverage drops measurably and is reported in the audit.

### 6.3 Layer 3 — Retrosynthetic pathway generation

- **Input:** `{target_inchi_key, host_metabolome: [precursor_inchi_keys], max_pathway_length: 7, min_mdf_threshold_kj_mol: 1.0}`
- **Output:** `PathwayCandidateSet` (typed in §4.3). Hundreds-to-thousands of candidates expected; ranking happens at L3.5.
- **Tools (multi, run as ensemble):**
  - RetroPath3.0 (MIT)
  - novoStoic2.0 (MIT) — AlphaSynthesis Platform
  - BioNavi (MIT)
  - DeepRetro (MIT) — published 2024-2026 deep-learning retrosynthesis
  - Genie-CAT (advisory, agentic LLM, arXiv 2025) — used only when the four primary tools disagree above threshold OR for fully-novel reactions
- **Cross-model disagreement signal:** Jaccard over candidate-route sets, plus a normalised tool-agreement count per pathway.
- **Backend:** `local_cpu` for RetroPath3 + novoStoic2 (Python). `gpu_rest_stub` for BioNavi + DeepRetro batch inference; Runpod swap on production volumes.
- **Falsifiers:** f008 (retrosynthesis disagreement), f009 (novelty without retrosynthesis), f010 (novelty without TS analog).
- **Plug-replaceability test:** disable any one of the four tools; the ensemble still produces a valid `PathwayCandidateSet` with disagreement signal noted; downstream layers unaffected.

### 6.4 Layer 3.5 — Learnable pathway ranking gate (orchestrator's fresh-eyes addition)

The pre-screen between L3 (thousands of candidates) and L4 (deep evaluation, ~$50-200 / candidate). Reject thresholds are Bayesian-optimised against the held-out PathGym partition. Thresholds are stored as state in `audit/l3_5_thresholds.json` and updated nightly.

- **Input:** `PathwayCandidateSet` (potentially > 1000)
- **Output:** `PathwayCandidateSet` (top-100 + Tier B falsifier outcomes)
- **Reject criteria (Tier A falsifiers + learnable thresholds):**
  - MDF score < `tau_mdf` (default 1.0 kJ/mol; learned)
  - Cofactor flux ratio > `tau_cofactor` (default 10×; learned)
  - Toxic-intermediate severity > `tau_tox` (default warn-level alert; learned)
  - Cross-tool retrosynthesis disagreement > `tau_disagree` (default Jaccard 0.7; learned)
- **Backend:** `local_cpu` always (per-candidate cost is sub-second).
- **Plug-replaceability test:** threshold YAML is hot-reloadable; pipeline does not need restart on threshold update.

### 6.5 Layer 4 — In silico screening (deep evaluation)

- **Input:** Tier-A-passing `PathwayCandidateSet` (top-100)
- **Output:** `ScoredPathwaySet` with full uncertainty bounds and falsifier results.
- **Sub-layers:**
  - **L4A FBA / GEM solver ensemble:** COBRApy + GLPK (LGPL-isolated), GECKO 3.0 (MIT), ECMpy 2.0 (MIT), ETFL (MIT). FBA-disagreement record per pathway.
  - **L4B Thermodynamics:** eQuilibrator MDF (MIT), PyTFA (Apache 2.0).
  - **L4C Kinetics ensemble:** DLKcat (MIT), CatPred (MIT), TurNuP (MIT), CEKM (Zer0pa-owned). UniKP / EF-UniKP added to ensemble only after LICENSE verification by overnight executor (see §22).
  - **L4D Gene-expression burden:** GECKO enzyme-constrained burden score; CRISPRi growth-fitness lookup if available.
  - **L4E Codon optimisation:** host codon-table-based CAI computation (RDKit).
  - **L4F Toxic-intermediate screening:** RDKit + structural-alert databases (ToxCast public alerts; ChEMBL mechanisms via CC BY).
  - **L4G Competing-pathway simulation:** COBRApy knockout simulation + FluxGAT (MIT) gene essentiality.
- **Backend:** `local_cpu` for FBA + thermodynamics + RDKit. `gpu_rest_stub` for kinetics ensemble batch inference + FluxGAT batch; Runpod swap.
- **Falsifiers:** f006 (kinetics disagreement), f007 (FBA disagreement), f011 (CEKM survivorship-bias).
- **Plug-replaceability test:** disable CEKM; ensemble continues with three remaining models; uncertainty inflates; gate continues to function.

### 6.6 Layer 4.5 — Unknown enzyme generative sub-pipeline

Triggered only when Tier B falsifier f009 or f010 fires. Three-tier novelty classification:

- **Tier 1 (TS analog available):** Use Baker catalytic motif scaffolding (Nature 2025) + RFdiffusion3 conditioned on TS geometry. Output: candidate enzyme structure + ESMFold sequence prediction + MACE-OFF binding feasibility + ProDy NMA conformational suitability.
- **Tier 2 (reaction class known, no TS):** RFdiffusion3 + Genie-CAT mechanistic hypothesis generation. Output: probabilistic enzyme structure ensemble; lower confidence; flagged in dossier.
- **Tier 3 (fully novel reaction class):** Genie-CAT advisory only. Flag as "experimental suggestion only" in dossier; route to closed-loop validation sequence at lowest priority.
- **Tools:** RFdiffusion3 (BSD 3-Clause via Foundry), Baker catalytic motif scaffolding paper-derived implementation (open methods), MACE-OFF (MIT), ESMFold (MIT), ProDy (MIT), eQuilibrator (MIT) for ΔrG check, Genie-CAT (open arXiv 2025).
- **Backend:** `local_cpu` for ProDy + eQuilibrator. `gpu_rest_stub` for RFdiffusion3 + ESMFold + MACE-OFF batch; Runpod swap. CPU-side Tier-3 advisory path is fully functional without Runpod.
- **Falsifiers:** f013 (RFdiffusion3 motif infeasible), f014 (MACE-OFF binding implausible), f015 (ProDy NMA misaligned).
- **Plug-replaceability test:** stub RFdiffusion3 with a canned `RFD3StubAdapter` that returns shape-correct structures; Tier-1 path completes; gate-function preserved at engineering level (`scientific_valid=false` in stub mode).

### 6.7 Layer 5 — Multi-fidelity BoTorch optimisation (MFMO)

- **Input:** `ScoredPathwaySet` + design space (promoter strengths, copy numbers, knockouts)
- **Output:** `RankedPathwaySet` (Pareto-optimal under `{max_titer, max_yield, min_burden, min_toxicity}`)
- **Acquisition functions:**
  - `qNEHVI` (qNoisy Expected Hypervolume Improvement) for multi-objective Pareto.
  - `qMFKG` (multi-fidelity Knowledge Gradient) over three fidelities: GEM/FBA (cost 1×), kinetic/GECKO (cost 10×), CFD-informed (cost 100×).
- **Surrogate:** GP with **Hamming-distance kernel** over discrete ZPE-encoded design vectors (orchestrator's locked decision per synthesis pressure-test). Deep ensemble (3-model) for high-variance regions. Bayesian neural network as plug-replaceable alternative behind the same `SurrogateAdapter` interface.
- **Initialisation:** ASR-thermostable variants seed the first BoTorch batch when any pathway enzyme has predicted Tm < 50°C (orchestrator's locked decision per synthesis recommendation — sample efficiency improvement 10-100×).
- **Tools:** BoTorch + Ax + GPyTorch (MIT).
- **Backend:** `local_cpu` for GP + qNEHVI / qMFKG. CFD high-fidelity evaluations are 10-50 commissioned OpenFOAM runs per organism-bioreactor combination (CFD is a forward mechanistic model, not learned); the multi-fidelity GP treats CFD outputs as discrete fidelity points, not training labels.
- **Falsifiers:** f017 (industrial-scale uncalibrated), f012 (codec-as-mechanism).
- **Plug-replaceability test:** swap Hamming-distance kernel for categorical-product kernel; calibration changes measurably; envelope schema unchanged.

### 6.8 Layer 5_OED — Causal experiment design (GO-CBED node)

- **Input:** `RankedPathwaySet` posterior + intervention design space.
- **Output:** `ValidationSequence` (ordered experiments by expected information gain).
- **Tools:** GO-CBED (ICLR 2025, open-source ref-impl wrapped); CausalBench (Nature Comms 2025, MIT) for validation.
- **Goal-oriented objective:** chosen per `RankedPathwaySet` consumer:
  - For dossier emission: `max_titer` (default).
  - For research mode: `max_information_gain_about_uncertainty_contributors`.
  - For closed-loop: `max_information_gain_about_top_pareto_candidate`.
- **Backend:** `local_cpu`. The objective optimisation and intervention selection are CPU-bound graph reasoning.
- **Falsifiers:** `f022_validation_sequence_unreachable` (added to registry — every experiment in the sequence must be executable by at least one configured consumer).

### 6.9 Layer 6 — Host engineering

- **Input:** Top-ranked pathway from L5 + host organism GEM.
- **Output:** `GeneticModificationSpec` (SBOL3-attested) per §4.2.
- **Tools:** Cello 2.0 (BSD); Salis Lab RBS Calculator v1.0 (GPL v3, **subprocess-isolated** — CLI invocation, no library linking, prevents GPL infection); OSTIR (open-source PMC 2022) as permissive fallback; OptKnock / OptForce in COBRApy; CRISPRi design tools; quorum-sensing CRISPRi toolkit (PMC 2025); De Novo DNA RBS Calculator v2 commercial (parked behind `runtime/denovodna.config.yaml`, off by default; activated only on `runtime/license_grants/denovodna.yaml` presence).
- **Backend:** `local_cpu`.
- **Falsifiers:** f019 (valid SBOL only).
- **Plug-replaceability test:** swap Salis v1.0 for OSTIR; predictions differ measurably; envelope schema unchanged; SBOL3 attestation regenerated.

### 6.10 Layer 6_BUILD — Cell-free TX-TL adapter (LDBT rapid Build-Test substrate)

- **Input:** `GeneticModificationSpec` from L6.
- **Output:** `CellFreeTXTLObservation` envelope (§4.4).
- **Adapter implementations (all required, fully specified, golden-fixture-tested):**
  - `CellFreeStubAdapter`: returns canned shape-correct outputs from a calibrated lookup table; CPU-only; engineering-mode only (`scientific_valid=false`).
  - `StrateosMyTXTLAdapter`: wraps Strateos TxPy programmatic client + myTXTL kit protocol. Phase 0 dry-run by default (returns simulated outputs validated against canned myTXTL benchmark data). Phase 2 wet-lab activation behind `runtime/cloud_lab.config.yaml` + customer license grant + `runtime/license_grants/strateos.yaml`.
  - `EmeraldPURExpressAdapter`: same shape, Emerald Cloud Lab + PURExpress. Phase 0 dry-run; Phase 2 gated.
- **Falsifiers:** f020 (txtl_observation_without_in_vivo).
- **Plug-replaceability test:** all three adapters return envelopes that pass the same downstream-consumer tests; closed-loop dossier mode works with any of the three.

### 6.11 Layer 7 — Output dossier generation

- **Input:** `RankedPathwaySet` + `GeneticModificationSpec` + closed-loop telemetry (if `dbtl_round > 0`).
- **Output:** Pydantic v2-validated dossier; SBOL3-attested; PROV-O-anchored; sha256-hash-chained across all twelve canonical dossier fields (§5.4 Report 02 schema). Markdown human-readable + JSON Schema export + REST API endpoint shape committed.
- **Tools:** Pydantic v2 (MIT); LangGraph (MIT) DAG record; Chroma (MIT) vector store for the literature RAG layer; PubMed E-utilities + Wiley API (queried under fair-use, references only, no full-text redistribution).
- **Closed-loop variant:** `dbtl_round > 0` triggers the round-N+1 emission. `CellFreeTXTLObservation` envelopes (or wet-lab observation envelopes in Phase 2) post back to L5; the BoTorch surrogate updates; the dossier round-N+1 emits with refined ranking and new validation sequence.
- **Backend:** `local_cpu`. Vector-store inference is CPU-quantised; HF-mirror-of-PubMed-embeddings under `Architect-Prime/synbio-rag-v0.1`.
- **Falsifiers:** every dossier passes the full Tier-A/B/C falsifier sweep; missing falsifier evidence fails the dossier closed.

## 7. Repository outcome

The agent produces this repository shape (mirror Energy + Materials with synbio-specific augmentations):

```text
Zer0pa/Synthetic-Biology/
├── PRD.md                                 # this document
├── HANDOFF-TO-OVERNIGHT-EXECUTOR.md       # what they inherit and produce
├── OVERNIGHT-EXECUTOR-STARTUP-PROMPT.md   # paste-ready startup prompt
├── HANDOFF-FROM-OVERNIGHT-EXECUTOR.md     # they write this on completion
├── EXECUTION-STATE.md                     # live state ledger
├── FINAL-REPORT.md                        # they write this on completion
├── RESISTANCE.md                          # binding meta-discipline
├── MODUS-OPERANDI.md                      # role-chain and fork-and-own permission
├── HANDOFF-TO-ORCHESTRATOR.md             # historical
├── ORCHESTRATOR-STARTUP-PROMPT.md         # historical
├── README.md
├── BOUNDARY.md                            # verbatim block; loaded by every test
├── CHANGELOG.md
├── SECURITY.md
├── CONTRIBUTING.md
├── RUNBOOK.md
├── RUNPOD-READINESS.md
├── NEXT-WAVE-PLAN.md                      # Phase 2 wet-lab activation, BioTRY corpus, De Novo DNA RBS commercial license
├── pyproject.toml
├── runpod.config.yaml
├── runtime/
│   ├── cloud_lab.config.yaml              # Strateos / Emerald API config; off by default
│   ├── denovodna.config.yaml              # De Novo DNA commercial RBS Calculator config; off by default
│   ├── biotry.config.yaml                 # BioTRY commercial corpus config; off by default
│   └── license_grants/                    # one YAML per granted commercial license
├── briefs/                                # per-layer briefs; agent augments
│   ├── L1-zpe-brief.md
│   ├── L2-lirc-brief.md
│   ├── L3-retrosynthesis-brief.md
│   ├── L3_5-ranking-gate-brief.md
│   ├── L4-screening-brief.md
│   ├── L4_5-unknown-enzyme-brief.md
│   ├── L5-mfmo-brief.md
│   ├── L5_OED-causal-brief.md
│   ├── L6-host-engineering-brief.md
│   ├── L6_BUILD-cellfree-txtl-brief.md
│   └── L7-dossier-brief.md
├── schemas/
│   ├── envelope.synbio.v0.1.yaml
│   ├── gms.synbio.v0.1.yaml               # GeneticModificationSpec (SBOL3-attested)
│   ├── pathway_candidate_set.v0.1.yaml
│   ├── scored_pathway_set.v0.1.yaml
│   ├── ranked_pathway_set.v0.1.yaml
│   ├── validation_sequence.v0.1.yaml
│   ├── cftxtl_observation.v0.1.yaml
│   ├── cross_model_disagreement.v0.1.yaml
│   ├── early_warning_signal.v0.1.yaml
│   ├── dossier.v0.1.yaml
│   └── synbio-audit-trail-v0.1.yaml       # Zer0pa Synbio Audit-Trail Spec (SBOL3 + PROV-O extension)
├── src/zer0pa_synbio/
│   ├── __init__.py
│   ├── envelope.py
│   ├── boundary.py
│   ├── adapters/
│   │   ├── l1_zpe/
│   │   ├── l2_lirc/
│   │   ├── l3_retrosynthesis/
│   │   ├── l3_5_ranking_gate/
│   │   ├── l4_fba/
│   │   ├── l4_kinetics/
│   │   ├── l4_thermodynamics/
│   │   ├── l4_5_unknown_enzyme/
│   │   ├── l5_mfmo/
│   │   ├── l5_oed/
│   │   ├── l6_host_engineering/
│   │   ├── l6_build_cellfree_txtl/
│   │   └── l7_dossier/
│   ├── audit/                             # JSONL + DuckDB writer; KG node/edge writer
│   ├── kg/                                # KG schema, GraphML / RDF export
│   ├── rest/                              # FastAPI; one router per layer; same schema as adapters
│   ├── cli/                               # synbio-cli; one subcommand per layer
│   ├── falsifiers/                        # one module per falsifier in the registry
│   ├── tda/                               # ripser+persim wrapper; SynbioTDAEarlyWarning
│   ├── cekm/                              # CEKM model code, training pipeline, adversarial-negatives sampler
│   ├── pathgym/                           # PathGym corpus assembly + active-learning data loop
│   ├── mcp/                               # MCP server suite
│   ├── disagreement/                      # CrossModelDisagreementRecord writer + aggregator
│   └── plug_replaceability/               # the plug-swap test harness
├── fixtures/
│   ├── golden/                            # golden envelope / dossier fixtures
│   ├── hmo/                               # 2'-FL, 3'-SL, DSLNT inputs and expected outputs
│   ├── negative/                          # falsification-wave negative tests
│   └── crossmodel/                        # cross-model disagreement test cases
├── tests/
│   ├── contract/                          # envelope schema, GMS schema, etc.
│   ├── falsification/                     # one test per falsifier in the registry
│   ├── integration/
│   ├── plug_replaceability/
│   ├── golden/
│   ├── runpod_cutover/                    # httpx.MockTransport invariance tests
│   └── hmo_seed/                          # 2'-FL / 3'-SL / DSLNT validation tests
├── audit/
│   ├── falsifiers.yaml                    # the 18+ named falsifiers
│   ├── l3_5_thresholds.json               # learnable thresholds, updated nightly
│   ├── license_grants/                    # one YAML per Class B/C/D/E license grant
│   ├── source_manifests/                  # one YAML per LIRC source
│   └── reasoner_tuples.jsonl              # the self-bootstrapping reasoner ledger
├── kg/
│   ├── schema.cypher
│   ├── nodes.csv
│   ├── edges.csv
│   └── exports/                           # GraphML / RDF
├── validation/
│   └── hmo-seed-evidence/                 # 2'-FL / 3'-SL / DSLNT evidence packets
├── docs/
│   ├── decisions/                         # ADRs
│   └── synbio-audit-trail-v0.1-spec.md    # the published Zer0pa standard
└── source-briefs/                         # historical
```

## 8. Agent topology for overnight execution

The overnight executor decomposes work into parallel sub-agents in non-overlapping worktrees. Minimum sub-agents:

| Sub-agent | Minimum model | Owns |
|---|---|---|
| Chief engineer | Opus 4.7 (Max reasoning) | Architecture, decisions, integration, final falsification wave, final report |
| Schemas / contracts | Opus or Sonnet 4.6 | Envelope, GMS, all v0.1 schemas, validators, canonical hashes, REST contracts |
| L1 ZPE | Sonnet 4.6 | SELFIES, ESM-2 wrapping, ZPE word envelope |
| L2 LIRC | Sonnet 4.6 | Rhea + MetaNetX + BiGG + ModelSEED + BRENDA reconciliation; HF push |
| L3 + L3.5 | Sonnet 4.6 | RetroPath3 + novoStoic2 + BioNavi + DeepRetro ensemble; learnable ranking gate |
| L4A FBA | Sonnet 4.6 | COBRApy + GECKO + ECMpy + ETFL ensemble; FBA disagreement record |
| L4C kinetics | Sonnet 4.6 | DLKcat + CatPred + TurNuP + CEKM ensemble; kinetics disagreement record |
| L4 thermodynamics + toxic + burden | Sonnet 4.6 | eQuilibrator + PyTFA + RDKit QSAR + GECKO burden + FluxGAT |
| L4.5 unknown enzyme | Opus or Sonnet 4.6 | RFdiffusion3 + Baker + MACE-OFF + ProDy + Genie-CAT integration |
| L5 MFMO + L5_OED | Opus or Sonnet 4.6 | BoTorch qNEHVI + qMFKG; Hamming-distance kernel; ASR initialisation; GO-CBED node |
| L6 host engineering | Sonnet 4.6 | Cello 2.0 + Salis v1.0 GPL subprocess-isolation + OSTIR + CRISPRi + GMS SBOL3 builder |
| L6_BUILD cell-free | Sonnet 4.6 | Three CellFreeTXTL adapters; Strateos TxPy + Emerald API wrapping |
| L7 dossier | Sonnet 4.6 | Pydantic dossier factory; LangGraph DAG; Chroma RAG; closed-loop variant |
| CEKM training | Opus 4.7 | CEKM architecture (ESM-2 + D-MPNN + condition MLP + adaptive gate); BRENDA + EnzyExtract + GotEnzymes2 corpus assembly; adversarial three-tier synthetic negatives; held-out blind eval; calibration audit; HF push |
| PathGym build | Sonnet 4.6 | Schema; corpus assembly; active-learning data loop; HF push |
| Falsification wave | Opus 4.7 | The 18+ falsifiers; negative tests; license-promotion tests; cross-model disagreement tests |
| Audit / KG | Sonnet 4.6 | JSONL + DuckDB writer; KG schema; GraphML / RDF export |
| TDA early-warning | Sonnet 4.6 | ripser + persim; SynbioTDAEarlyWarning |
| MCP suite | Sonnet 4.6 | One MCP server per major adapter; read-only by default |
| Plug-replaceability harness | Sonnet 4.6 | The swap test for every layer; httpx.MockTransport invariance |
| Synbio Audit-Trail Spec author | Opus 4.7 | Drafts `synbio-audit-trail-v0.1-spec.md`; SBOL3 + PROV-O extension |
| HF mirror manager | Sonnet 4.6 | Pushes bulk artifacts to `Architect-Prime/<repo>` HF; manifests in repo |
| Deep research | Opus or Sonnet 4.6 | Source verification only; logged as manifests under `audit/source_manifests/` |

Sub-agents work in parallel worktrees or non-overlapping file scopes. They must not revert each other's changes. Chief engineer integrates and owns final consistency.

## 9. Audit trail and KG — Zer0pa Synbio Audit-Trail Specification v0.1

This is a Zer0pa-published standard. No analogue to ICH M15 exists for synbio. The PRD specifies the spec; the agent implements it; the spec ships under `docs/synbio-audit-trail-v0.1-spec.md` and is referenced by every L6/L7 envelope's `prov_o_jsonld` field.

### 9.1 Provenance modes

```text
campaign_id -> pathway_candidate_id -> envelope_chain -> sbol3_attestation -> dossier_id
```

Every envelope writes to JSONL + DuckDB CPU-side. Neo4j is optional and not blocking.

### 9.2 KG nodes (committed in `kg/schema.cypher`)

```text
Compound, Reaction, Pathway, Enzyme, Organism, Strain, Modification, Assay,
GeneticModificationSpec, CellFreeTXTLObservation, Dossier,
SBOLDocument, ProvActivity, ProvAgent, ProvEntity,
ToolAdapter, ModelCheckpoint, SimulationRun,
PathwayCandidate, ScoredPathway, RankedPathway, ValidationExperiment,
FalsifierResult, DisagreementRecord, EarlyWarningSignal,
LicenseFinding, RightsPolicy, SourceManifest, ReasonerTuple,
TDADiagram, FluxGraph, Embedding
```

### 9.3 KG edges

```text
catalyses, requires_cofactor, produces, consumes, encodes, regulates,
has_source, has_falsifier, has_audit, member_of_pathway,
instantiates_in_organism, measured_by, supports, contradicts,
DERIVED_FROM, USED_TOOL, USED_MODEL, USED_SOURCE, PRODUCED,
VALIDATED_BY, FAILED_BY, DISAGREES_WITH, FEEDS_L4, FEEDS_L5,
ATTESTED_BY_SBOL, PROV_GENERATED, PROV_USED, PROV_WAS_DERIVED_FROM,
RIGHTS_CONSTRAINED_BY, OWNED_BY
```

### 9.4 SourceManifest

```yaml
SourceManifest:
  source_id: string
  uri: string
  retrieval_method: api | git | hf | manual | fixture | claude_deep_research
  retrieved_at: iso8601
  license_spdx_or_text: string
  license_class: A | B | C | D | E
  allowed_use: research | commercial | noncommercial | unknown
  geography_restrictions: string | null
  checksum: string
  local_slice_size_mb: number
  hf_mirror_uri: string | null              # if bulk, where it lives on HF
  bulk_data_stored_locally: bool            # default false
  citation: string
  rights_notes: string
  excluded_from_training_corpus: bool       # set true for ATLAS, BKMS-react, KEGG bulk
```

### 9.5 SBOL3 attestation

Every L6 `GeneticModificationSpec` is serialised as SBOL3 via libsbolj3, validated at strict mode, sha256-hashed, optionally published to SynBioHub (Zer0pa instance, internal). The audit log carries the SBOL document hash plus libsbolj3 validator output.

### 9.6 PROV-O JSON-LD chain

Every envelope carries a PROV-O JSON-LD block linking `prov:Activity` (the layer execution) to `prov:Agent` (the adapter) to `prov:Entity` (the input/output payloads). The chain is hashed; the dossier's PROV-O hash chain anchors back to the envelope_id of every contributing layer-run.

### 9.7 The Spec (`docs/synbio-audit-trail-v0.1-spec.md`)

The Synbio Audit-Trail Specification v0.1 is a markdown + JSON-Schema spec document published by Zer0pa. It defines the SBOL3 + PROV-O extension that every Zer0pa Synthetic Biology dossier conforms to. It is licensed CC BY 4.0 to enable other groups to adopt the same standard. The spec is committed during overnight execution; future Zer0pa workstreams cite it; downstream CRO partners (Glycom / Inbiose / DSM-Firmenich) can consume Zer0pa dossiers without translation.

## 10. Data sovereignty (three tiers, defaults locked)

| Tier | What | Default ownership | Storage |
|---|---|---|---|
| Tier-1 Customer-Confidential | Customer pathway designs, customer assay observations, customer-fine-tuned CEKM weights | Customer-owned, customer-isolated | Customer-controlled storage; Zer0pa keeps redacted operational provenance only |
| Tier-2 Aggregated-Insights | De-identified DBTL telemetry, model calibration deltas, cross-model disagreement aggregates | Zer0pa-shared pool with customer opt-out | HF private under `Architect-Prime/synbio-aggregated-insights-v0.1` |
| Tier-3 Public | LIRC corpus contributions, PathGym benchmark splits, Zer0pa Synbio Audit-Trail Spec, scientific validation triple results | Zer0pa-published | HF public + repo public branches; CC BY 4.0 |

Default for new fine-tuned weights: **Tier-1 customer-isolated unless customer opts into Tier-2 sharing.** Default for novel falsifier discoveries: **Tier-3 public** (the field benefits; Zer0pa's moat is the corpus, not the falsifier list). Default for cross-model disagreement aggregates: **Tier-2 with customer opt-out.**

Pricing tiers are coupled to data-sovereignty tiers — the more data the customer keeps in Tier-1, the higher the per-engagement price. Operator-driven contracts overlay the defaults.

## 11. Self-bootstrapping reasoner — PathGym flywheel

Every meaningful pipeline run emits a `ReasonerTuple` to `audit/reasoner_tuples.jsonl`:

```yaml
ReasonerTuple:
  tuple_id: string
  campaign_id: string
  problem_context: string                    # "design HMO biosynthetic pathway for DSLNT in E. coli"
  input_spec_ref: string                     # envelope_id of L1 input
  tool_plan: object                          # which adapters were configured
  simulation_request_ref: string
  raw_result_ref: string                     # envelope_id of L7 dossier
  reduced_observables_ref: string            # what KPIs were predicted
  falsifier_results: [string]
  disagreement_records: [string]
  ground_truth_ref: string | null            # populated when wet-lab observations come back
  outcome_label: pass | fail | inconclusive | superseded
  rights_label: tier_1_customer | tier_2_aggregated | tier_3_public
  next_action: string
```

The PathGym corpus is the union of Tier-3 and opted-in Tier-2 ReasonerTuples. The corpus grows per engagement. The L3.5 ranking gate's thresholds, the CEKM model weights, and the BoTorch surrogate's prior are all updated nightly against the latest PathGym corpus state. **The corpus is the moat; no model is.** Zer0pa's competitive position is the cross-domain annotated corpus no competitor can replicate, not any specific model architecture.

## 12. CEKM training corpus design

CEKM = Conditional Enzyme Kinetics Model, Zer0pa-owned MIT-permissive trainable on commercial corpora.

### 12.1 Corpus assembly

| Source | License | Status | Slice |
|---|---|---|---|
| BRENDA bulk core | CC BY 4.0 (Class A) | In corpus | ~4.3M data points |
| EnzyExtract | MIT (Class A) | In corpus | 218,095 entries (89,544 absent from BRENDA) |
| GotEnzymes2 | CC BY 4.0 (Class A) | In corpus (curriculum pre-training) | 59.6M predicted entries (soft pseudo-labels) |
| ProteinGym DMS | MIT (Class A) | In corpus (auxiliary) | ~2.7M missense variants, 217 DMS assays |
| BioTRY | Unverified commercial license | **Excluded from training corpus v1**; included in v2 only after commercial-license grant under `runtime/license_grants/biotry.yaml` | — |
| BKMS-react | Proprietary | Excluded | — |
| KEGG bulk | Commercial | Excluded; IDs as cross-references only | — |
| ATLAS of Biochemistry | Academic-use subscription / redistribution not granted | Excluded; URL/DOI cross-references only | — |

### 12.2 Adversarial three-tier synthetic-negatives sampler (orchestrator's fresh-eyes addition)

Per BRENDA positive `(enzyme, substrate, condition, kcat, Km)`, sample three synthetic negatives:

- **Tier α (0.5× active-site distance):** substrates whose AlphaFold-predicted active-site contact distance is at half the BRENDA-positive's distance. Approximate near-miss negatives.
- **Tier β (1.0× distance):** distance-equal but chemically dissimilar substrates. Mid-range negatives.
- **Tier γ (2.0× distance):** distant substrates with low AutoDock Vina docking score. Far negatives.

CEKM is trained to distinguish positives from each of the three tiers. Calibration is reported per tier in the held-out blind eval.

### 12.3 Held-out blind eval

10-20% of BRENDA bulk + 100% of EnzyExtract dark-matter corpus is held out. CEKM never sees these during training. Calibration curve audit (predicted-CI coverage of true value) reported on held-out only.

### 12.4 HF push

Trained CEKM weights → `Architect-Prime/synbio-cekm-v0.1` (HF private). Training corpus slices > 5 GB → `Architect-Prime/synbio-cekm-corpus-v0.1` (HF private; manifest under `audit/source_manifests/cekm_corpus.yaml`).

### 12.5 Plug-replaceability test for CEKM

CEKM is one member of a four-way ensemble {DLKcat, CatPred, TurNuP, CEKM}. Removing CEKM degrades coverage but does not break the ensemble. The test confirms the kinetics-disagreement record continues to compute; the dossier continues to emit; uncertainty inflates by a measurable amount.

## 13. Cell-free TX-TL / cloud-lab plan

The L6_BUILD layer ships three adapters at full sophistication. Phase 0 dry-run is fully functional CPU-side. Phase 2 wet-lab activation is a config-flag-shaped change.

### 13.1 CellFreeStubAdapter (Phase 0, CPU-only)

- Returns canned outputs from a calibrated lookup table (entries seeded from published myTXTL benchmark data and PURExpress benchmark data).
- Engineering mode only (`scientific_valid=false`).
- Used by every test and every dry-run.

### 13.2 StrateosMyTXTLAdapter (Phase 0 dry-run + Phase 2 wet-lab)

- Wraps Strateos TxPy programmatic Python client.
- Phase 0 dry-run: returns simulated outputs validated against canned myTXTL benchmark data; same envelope schema as wet-lab.
- Phase 2 wet-lab: requires `runtime/cloud_lab.config.yaml` populated + `runtime/license_grants/strateos.yaml` present + customer wet-lab budget approval. Hard interlock: no wet-lab dispatch without all three.
- Falsifier f020 (`txtl_observation_without_in_vivo`) flags every Phase 0 dry-run output as "advisory; in-vivo corroboration required" if a host-engineering decision depends on it.

### 13.3 EmeraldPURExpressAdapter (Phase 0 dry-run + Phase 2 wet-lab)

Same shape as Strateos adapter, Emerald Cloud Lab + PURExpress kit protocol.

### 13.4 Closed-loop dossier mode (LDBT completion)

`L6_BUILD` envelopes post back to `L5` via the `closed_loop_router`. The BoTorch surrogate updates. The dossier emits round-N+1 with refined ranking and a new `ValidationSequence`. The active-inference loop is closed across the cell-free TX-TL boundary, fully CPU-side, fully functional in stub mode.

## 14. Hugging Face storage plan (Architect-Prime user, not Zer0pa org)

Per operator directive: bulk artifacts live under HF user **Architect-Prime** (HF token already authorised with `repo.write` on Architect-Prime user). Mac storage stays under 42 GiB free.

### 14.1 What goes to HF

- `Architect-Prime/synbio-lirc-v0.1` — LIRC corpus build artifacts (private; CC BY 4.0 attribution chain in README).
- `Architect-Prime/synbio-cekm-corpus-v0.1` — CEKM training corpus assembly (private; per-source license attribution).
- `Architect-Prime/synbio-cekm-v0.1` — CEKM trained weights (private; MIT licensed weights when ready for public release).
- `Architect-Prime/synbio-pathgym-v0.1` — PathGym corpus growing per engagement (private; tier-2 + opted-in tier-3 only).
- `Architect-Prime/synbio-rag-v0.1` — PubMed embeddings for L7 dossier RAG layer (private; embeddings only, no full-text).
- `Architect-Prime/synbio-aggregated-insights-v0.1` — Tier-2 aggregated insights pool (private; customer opt-out respected).
- `Architect-Prime/synbio-protein-structures-v0.1` — Cached AlphaFold2 + ESMFold structures used in CEKM negatives sampler (private).
- `Architect-Prime/synbio-rfdiffusion3-cache-v0.1` — Cached RFdiffusion3 generated structures for unknown-enzyme sub-pipeline (private).
- `Architect-Prime/synbio-mace-off-cache-v0.1` — Cached MACE-OFF binding evaluations (private).

### 14.2 What stays in repo

- All code, schemas, fixtures, audit logs (JSONL up to 100 MB), KG exports (GraphML / RDF up to 100 MB), README + docs, prompts, briefs.
- Small artifact slices used in tests and golden fixtures.
- Manifests pointing to HF — every HF artifact has a corresponding `audit/source_manifests/<artifact_id>.yaml` in repo with sha256, license attribution, and HF URI.

### 14.3 Manifest discipline

Every HF push writes a `BlockedSourceManifest` or `SourceManifest` under `audit/source_manifests/` before the push. The manifest carries sha256, license SPDX, citation, retrieved_at, hf_mirror_uri. Pushes without a manifest entry fail closed at the HF mirror manager sub-agent's pre-push hook.

### 14.4 HF token plumbing

- Originating Mac: HF token at `~/.cache/huggingface/token` (already authorised; user `Architect-Prime`).
- Runpod machine: operator provides via env var `HF_TOKEN`. The PRD does not embed the token. The agent reads the token at startup; if absent, the HF mirror manager sub-agent reports the absence in `EXECUTION-STATE.md` and continues with local-only artifact storage until the operator provides on review.

## 15. CPU-first build sequence — overnight execution waves

The agent decomposes into waves. Each wave is parallel within itself; waves sequence on dependencies.

### Wave -1 (GitHub bootstrap on the executor machine, mandatory)
- Clone or fetch `https://github.com/Zer0pa/Synthetic-Biology`.
- Check out `main` and confirm `origin/main` is current before reading any local fallback path.
- Read `RESISTANCE.md`, `PRD.md`, `HANDOFF-TO-OVERNIGHT-EXECUTOR.md`, and `OVERNIGHT-EXECUTOR-STARTUP-PROMPT.md` from the GitHub checkout.
- Do not rely on conversation history or local files outside the checkout except credentials and cache directories explicitly named in the PRD.
- Create or update `EXECUTION-STATE.md` with the bootstrap timestamp, machine profile, available CPU/RAM/disk/GPU, Python version, package manager status, HF token availability, and any missing credentials.
- Begin execution immediately. Do not ask for confirmation and do not interim-report.

### Wave -0.5 (maximum local setup before compute escalation, mandatory)
- Download, install, cache, and configure every Mac/local/CPU-feasible dependency, source manifest, small fixture, schema, REST stub, model stub, and test harness before marking any layer Runpod-needed.
- If the machine can complete a layer entirely on CPU/MPS/local resources within storage and time limits, complete it there.
- If a layer truly needs increased compute, leave a production-shaped REST stub, a Runpod config entry, a source manifest, golden fixtures, and a cutover test so the later compute upgrade is a config change.
- Never use "needs GPU" as a reason to skip CPU-side contracts, manifests, tests, adapters, or dossier plumbing.

### Wave 0 (foundation, < 1 hour)
- Resistance.md re-read; binding.
- Schemas committed (envelope, GMS, all v0.1 schemas).
- Boundary block test golden-fixture.
- Falsifier registry committed.
- KG schema committed.
- Source manifest skeleton committed.
- Synbio Audit-Trail Spec v0.1 first-draft committed.
- HF mirror manager sub-agent stands up; HF token verified; first push to `Architect-Prime/synbio-bootstrap-v0.1` empty repo as smoke test.

### Wave 1 (envelope plumbing + L1, ~2 hours)
- `UniversalLayerEnvelope` Pydantic + validator.
- `BoundaryGate` invariant test.
- L1 ZPE adapter (SELFIES + ESM-2 quantised); golden fixture; envelope plumbing.
- REST stub + plug-replaceability harness skeleton.

### Wave 2 (L2 LIRC corpus, ~3-4 hours)
- Rhea + MetaNetX + BiGG + ModelSEED + BRENDA bulk pull; slice manifest.
- Reaction reconciliation; atom-mapped SMARTS canonicalisation; deduplication.
- LIRC corpus push to HF.
- L2 adapter + envelope; falsifier f018 (license drift).

### Wave 3 (parallel: L3 retrosynthesis + L3.5 + L4A FBA + L4B thermodynamics + L4C kinetics + L4 burden/toxic, ~6-8 hours)
- L3 multi-tool ensemble (RetroPath3 + novoStoic2 + BioNavi + DeepRetro).
- L3.5 learnable ranking gate (initial thresholds; nightly re-optimisation hook).
- L4A FBA ensemble (COBRApy + GECKO + ECMpy + ETFL).
- L4B eQuilibrator MDF + PyTFA.
- L4C kinetics ensemble (DLKcat + CatPred + TurNuP + CEKM stub awaiting Wave 4 weights).
- L4D-G: burden, codon, toxic, competing.
- Cross-model disagreement records wired into the envelope chain.

### Wave 4 (CEKM training, ~6-12 hours, Runpod-bound for full training)
- Corpus assembly (BRENDA + EnzyExtract + GotEnzymes2).
- Adversarial three-tier synthetic-negatives sampler.
- Held-out blind-eval split.
- Training (CPU-side prototype to validate plumbing; full training on Runpod swap).
- Calibration audit.
- Weights push to HF.

### Wave 5 (parallel: L4.5 unknown enzyme + L5 MFMO + L5_OED + TDA, ~4-6 hours)
- RFdiffusion3 (Foundry) + Baker catalytic motif scaffolding integration; REST stub for GPU swap.
- MACE-OFF + ProDy + ESMFold integration.
- Genie-CAT advisory wrapper.
- L5 BoTorch qNEHVI + qMFKG; Hamming-distance kernel; ASR initialisation.
- L5_OED GO-CBED node.
- TDA early-warning (ripser + persim) for fermentation regime change.

### Wave 6 (L6 host engineering + L6_BUILD cell-free TX-TL, ~3-4 hours)
- L6 SBOL3-attested GMS builder (Cello 2.0 + Salis v1.0 GPL subprocess + OSTIR + CRISPRi).
- L6_BUILD three adapters (Stub + Strateos + Emerald).
- Closed-loop router.

### Wave 7 (L7 dossier + closed-loop active inference + RAG, ~3-4 hours)
- Pydantic v2 dossier factory.
- LangGraph DAG record.
- Chroma RAG + PubMed embeddings (HF push).
- Closed-loop variant: dbtl_round > 0 emission path.

### Wave 8 (PathGym scaffold + ReasonerTuple ledger, ~2-3 hours)
- PathGym schema + corpus assembly.
- ReasonerTuple writer wired into every layer.
- Active-learning data-loop hook (nightly L3.5-threshold + BoTorch-prior + CEKM-fine-tune update against latest PathGym state).

### Wave 9 (HMO scientific validation triple, ~6-8 hours)
- 2'-FL evidence packet (full L1-L7 run; cross-model disagreement; falsifier sweep; dossier emission; pre-registered acceptance threshold check).
- 3'-SL evidence packet (same; cofactor-balance specifically identified as dominant uncertainty contributor; CMP-Neu5Ac proposed as highest-information-gain intervention).
- DSLNT evidence packet (same; ≥3 candidate routes; at least one Tier-2 unknown-enzyme classification; advisory dossier with closed-loop validation sequence).
- All three packets committed to `validation/hmo-seed-evidence/`.

### Wave 10 (falsification wave, ~2-3 hours)
- Boundary mutation test.
- License promotion test.
- Stub scientific-validity test.
- Unit omission test.
- Negative-density test.
- Mass-balance violation test.
- License-drift test.
- Cross-model disagreement fail test.
- Each of the 18+ falsifiers gets a deliberate trigger test.
- The wave passes only if the system blocks or quarantines each bad case.

### Wave 11 (Runpod cutover proof, ~2-3 hours)
- httpx.MockTransport invariance test for every GPU-stubbed layer.
- Config flag flip; golden fixtures pass; provenance fields differ; everything else identical.
- `RUNPOD-READINESS.md` written.

### Wave 12 (final integration + final report, ~2-3 hours)
- Full end-to-end run on the 2'-FL seed against committed golden fixtures.
- KG export to GraphML.
- HF mirror manager pushes final state.
- `FINAL-REPORT.md` written; commit hash + every wave's evidence captured.
- `HANDOFF-FROM-OVERNIGHT-EXECUTOR.md` written with what was built, what failed, what is next.
- Final push to GitHub.

Total wallclock estimate (parallel sub-agents): **30-50 hours** of overnight long-horizon execution. The agent paces itself; no interim reporting.

## 16. Core config flags

```env
# Boundary discipline (always strict)
SYNBIO_BOUNDARY_GATE=strict
SYNBIO_AUDIT_REQUIRED=true
SYNBIO_LICENSE_GATE=strict

# Storage
SYNBIO_EXECUTION_PROFILE=local_cpu_first
SYNBIO_ARTIFACT_MODE=manifest_only
SYNBIO_ALLOW_BULK_LOCAL=false
SYNBIO_HF_USER=Architect-Prime

# Layer backends (default values; flipped on Runpod cutover)
SYNBIO_L1_BACKEND=local_cpu        # SELFIES + ESM-2 quantised
SYNBIO_L2_BACKEND=local_cpu        # LIRC corpus access via SPARQL
SYNBIO_L3_BACKEND=local_cpu        # RetroPath3 + novoStoic2; BioNavi/DeepRetro stub
SYNBIO_L3_BIONAVI_BACKEND=gpu_rest_stub
SYNBIO_L3_DEEPRETRO_BACKEND=gpu_rest_stub
SYNBIO_L3_5_BACKEND=local_cpu
SYNBIO_L4_FBA_BACKEND=local_cpu
SYNBIO_L4_KINETICS_BACKEND=gpu_rest_stub  # ensemble batch on GPU; CEKM gpu-resident
SYNBIO_L4_THERMO_BACKEND=local_cpu
SYNBIO_L4_5_BACKEND=gpu_rest_stub  # RFdiffusion3 + MACE-OFF + ESMFold
SYNBIO_L4_5_PRODY_BACKEND=local_cpu
SYNBIO_L5_BACKEND=local_cpu        # BoTorch + GP CPU
SYNBIO_L5_OED_BACKEND=local_cpu
SYNBIO_L6_BACKEND=local_cpu
SYNBIO_L6_BUILD_BACKEND=stub       # cellfree_stub | strateos_drysrun | emerald_dryrun | strateos_wet | emerald_wet
SYNBIO_L7_BACKEND=local_cpu
SYNBIO_TDA_BACKEND=local_cpu
SYNBIO_REASONER_BACKEND=hosted_claude  # hosted_claude | runpod_vllm | local_stub

# Schema versions (locked)
SYNBIO_ENVELOPE_SCHEMA_VERSION=synbio.envelope.v0.1
SYNBIO_GMS_SCHEMA_VERSION=synbio.gms.v0.1
SYNBIO_DOSSIER_SCHEMA_VERSION=synbio.dossier.v0.1

# Closed-loop
SYNBIO_CLOSED_LOOP_DEFAULT=true    # closed-loop is v1 default; single-shot is opt-out

# License-gated extras (off by default; activated by license_grants/<name>.yaml presence)
SYNBIO_BIOTRY_INCLUDED=false
SYNBIO_DENOVODNA_RBS_V2=false
SYNBIO_UNIKP_INCLUDED=false        # off until LICENSE verified in repo
SYNBIO_KEGG_BULK=false             # never on
SYNBIO_BKMS_REACT=false            # never on
SYNBIO_ATLAS_OF_BIOCHEMISTRY=false # never on for training; URL refs only
```

## 17. REST stub surface

Every GPU-bound endpoint has a `gpu_rest_stub` implementation that is a FastAPI route returning canned outputs validated against the same response schema as the production endpoint. The httpx.MockTransport golden-fixture invariance test confirms: under stub, under local_cpu, under runpod_rest, the response body is byte-identical except for `provenance.created_at`, `provenance.git_sha`, and runtime metadata.

Stubs at minimum:
- `POST /l1/zpe/embed` (ESM-2 batched)
- `POST /l3/bionavi/retrosynthesise`
- `POST /l3/deepretro/retrosynthesise`
- `POST /l4/kinetics/ensemble`
- `POST /l4_5/rfdiffusion3/scaffold`
- `POST /l4_5/mace_off/binding`
- `POST /l4_5/esmfold/predict`
- `POST /l6_build/cellfree/stub`
- `POST /l6_build/cellfree/strateos`
- `POST /l6_build/cellfree/emerald`

## 18. Quantum slot — far-horizon, three concrete BlockedSourceManifest entries

Per Materials' synthesis pattern, three quantum slots are stubbed but never promoted in v1:

```yaml
quantum_slots:
  - slot_id: q001_l1_active_site_dft_via_vqe
    layer: L1
    description: VQE on small enzyme active-site fragments (H-, O-, N-containing motifs); DFT-equivalent ground state for transition state energies
    hardware_required: 50+ qubit fault-tolerant or noisy NISQ at scale
    stub_status: BlockedSourceManifest, permanent Class E
    promotion_gate: hardware availability + dedicated QC partner + customer use case
  - slot_id: q002_l4_substrate_enzyme_qaoa
    layer: L4
    description: QAOA on small substrate-enzyme docking graphs; combinatorial fit at active site
    hardware_required: NISQ with low-depth circuits + classical co-processor
    stub_status: BlockedSourceManifest, permanent Class E
    promotion_gate: hardware availability + benchmark vs classical AutoDock Vina
  - slot_id: q003_l5_amplitude_amplification_qnehvi
    layer: L5
    description: Quantum amplitude amplification on the qNEHVI acquisition function; Grover-style speedup on Pareto frontier search
    hardware_required: fault-tolerant; far horizon
    stub_status: BlockedSourceManifest, permanent Class E
    promotion_gate: theoretical justification + hardware + benchmark
```

No quantum slot is on a critical path. No claim of quantum advantage. Logged for frontier watch.

## 19. Runpod migration plan

### 19.1 Per-layer GPU requirements

| Layer | GPU need | VRAM | Notes |
|---|---|---|---|
| L1 ESM-2 batch | A100/H100 | 24 GB+ | quantised CPU works for small batches |
| L3 BioNavi / DeepRetro | A100 | 16 GB+ | inference batch |
| L4 kinetics ensemble | A100 | 24 GB+ | DLKcat + CatPred + TurNuP + CEKM batch |
| L4.5 RFdiffusion3 | A100/H100 | 40 GB+ | inference; no training in v1 |
| L4.5 ESMFold | A100 | 24 GB+ | inference batch |
| L4.5 MACE-OFF | A100 | 16 GB+ | inference; training fine-tune optional |
| CEKM training | A100/H100 | 80 GB+ | full training; CPU-side prototype validates plumbing |
| Reasoner (TxGemma 27B) | A100/H100 | 80 GB+ | inference; CPU-quantised for dev |

### 19.2 Cutover gates (mandatory)

- All schemas identical between stub and Runpod.
- All golden fixtures pass before and after backend swap.
- Only `provenance/runtime` fields may change.
- Budget cap and kill-switch configured (operator policy).
- Artifact checksums recorded; HF push completes.
- No Class C/D/E licensed tool enters product path without `audit/license_grants/<name>.yaml`.
- The httpx.MockTransport invariance test passes for every gpu_rest_stub endpoint.

### 19.3 Cost shape

- Wave 4 CEKM training: ~$200-400 of A100 / H100 time (10-20 GPU-hours).
- Wave 5 RFdiffusion3 inference: ~$50-100 per HMO seed.
- Wave 9 HMO triple validation: ~$200-300 total (three seeds, full L1-L7 chain).
- Steady-state per-engagement: ~$500-2000 of GPU time (depends on novelty rate triggering L4.5).

## 20. Acceptance gates

### 20.1 Scientific gate

- Every numeric output carries units.
- Every accepted output carries uncertainty or is invalid.
- Cross-model disagreement is logged and enforced.
- Domain-specific sanity bounds pass (titer < theoretical maximum; Km > 0; etc.).
- No stub envelope sets `scientific_valid=true`.
- Falsifier coverage: every layer has at least three falsifiers; total ≥ 18 named.

### 20.2 Engineering gate

- Tests pass from a clean clone (no hidden state).
- No bulk datasets vendored locally beyond manifest + small slice.
- No Docker required on the originating Mac.
- REST stubs exist for every GPU-bound endpoint.
- httpx.MockTransport invariance test passes.
- Plug-replaceability test passes for every layer.
- Audit / KG writes happen before adapter outputs are accepted.

### 20.3 Brain-functionality gate

- Next agent can reconstruct full state from repo + KG + audit log without conversation history.
- Every stuck point is resolved by a decision, sub-agent, or logged blocker — never by interim-reporting to operator.
- The final report includes what was built, what failed, falsification evidence, decision log, commit hash, and next-wave list.

### 20.4 Falsification-wave gate

The deliberate falsification wave (Wave 10) must show the system blocks or quarantines every bad case. Specific tests:
- Boundary mutation test (replace boundary block; system rejects).
- License promotion test (try to promote a Class C/D/E source without grant; system rejects).
- Stub scientific-validity test (try to set `scientific_valid=true` on stub envelope; system rejects).
- Unit omission test.
- Bad SELFIES test.
- Mass-balance violation test.
- Toxic intermediate test.
- License-drift test (cite BKMS-react; system rejects).
- Cross-model disagreement fail test (force kinetics disagreement; system inflates uncertainty).
- TDA regime-change leakage test.
- f009 unknown-enzyme route test.
- f010 Tier-3 advisory test.
- f019 SBOL invalid test.
- f020 in-vivo absence test.

### 20.5 License-clean corpus gate (synbio-specific)

- Every reaction in LIRC carries a verifiable Class A/B license attestation under `audit/source_manifests/`.
- BKMS-react and KEGG bulk are excluded by construction.
- BioTRY is gated on commercial-license verification.
- ATLAS of Biochemistry is read-only cross-reference; never embedded.

### 20.6 R&D-standard gate (orchestrator's anti-toy gate)

- Every layer has the maximum-sophistication implementation specified, not the MVP.
- Closed-loop dossier mode is v1 default.
- Unknown-enzyme sub-pipeline is full (RFdiffusion3 + Baker + MACE-OFF + ProDy + Genie-CAT), not advisory-only.
- TDA early-warning is fully wired, not parked.
- Synbio Audit-Trail Spec v0.1 is published, not deferred.
- Three-tier falsifier hierarchy is implemented, not sketched.
- Adversarial three-tier synthetic-negatives sampler is implemented, not single-tier.
- ASR-thermostable BoTorch initialisation is implemented when applicable.
- Hamming-distance GP kernel is the default; categorical-product kernel is a plug-replaceable alternative behind the same interface.

## 21. Productisation and pricing (appendix; not gating)

Operator-driven, not orchestrator-driven. The PRD does not commit pricing — that is downstream of customer engagement.

Reference shape:
- **Campaign:** USD 100k-300k per HMO portfolio discovery campaign (mirrors Materials' Amplats-shaped engagement).
- **Platform retainer:** USD 750k-2M year-1 floor; USD 5-10M year-3 ceiling for a multi-product portfolio retainer (HMO + terpenoid + future targets).
- **Sovereignty-tier coupling:** Tier-1 isolation is a price multiplier; Tier-2 sharing is a price discount; Tier-3 contributions to LIRC / PathGym / Synbio Audit-Trail Spec earn citation credit (and feed the moat).
- **Funding triangulation:** DOE AgileBioFoundry, NIH Biomedical Data Translator, DARPA SBA, NSF Synthetic Biology Engineering Research Centers (SynBERC successors), Horizon Europe synbio calls, EU IndBioCat consortium.

This section ships in the PRD for completeness; the agent does not consume it as build directive.

## 22. License and status findings (the seven-item resolution table)

| Item | Resolution | Action |
|---|---|---|
| BioTRY commercial license | Codebase MIT (Tian Yu, 2024). Database content is "freely available" academic; commercial-use terms not explicitly granted. | **v1 excluded from training corpus.** v2 inclusion gated by `runtime/license_grants/biotry.yaml`. Fallback: per-product literature-titer baseline curated from published HMO papers (the engine-vs-baseline harness). |
| UniKP / EF-UniKP | Live GitHub lookup surfaced `HanselYu/UniKP`; GitHub reports no license metadata and no top-level LICENSE file. EF-UniKP did not surface as a public repository in the checked GitHub search. | **Excluded from kinetics ensemble v1** until overnight executor verifies LICENSE in repo and commits `audit/source_manifests/unikp.yaml` with explicit license SPDX. |
| RFdiffusion3 / Foundry | RosettaCommons Foundry public repository is **BSD 3-Clause** and its README exposes RFD3 installation paths. No public South-Africa-specific geo restriction was found in the repository metadata reviewed. | **v1 cleared for software integration via Foundry.** If checkpoint download or Foundry enrolment gates appear during execution, keep `RFD3StubAdapter` active, record the blocker in `audit/source_manifests/rfdiffusion3.yaml`, and do not claim scientific validity from stub outputs. |
| SBOL-as-audit-trail-shape | SBOL3 + PROV-O is the closest standard; no synbio M15-equivalent exists. | **Zer0pa publishes Synbio Audit-Trail Specification v0.1** as a CC BY 4.0 standard document (`docs/synbio-audit-trail-v0.1-spec.md`). |
| myTXTL / PURExpress / cell-free TX-TL APIs | Kits, no direct API. **Strateos / Emerald Cloud Lab provide programmatic dispatch.** | `CellFreeTXTLAdapter` interface with three implementations (Stub / Strateos+myTXTL / Emerald+PURExpress); Phase 0 dry-run; Phase 2 wet-lab gated. |
| ATLAS of Biochemistry | Public site states the database is free for academic use upon subscription; downloads are login-gated. No redistribution or training-corpus permission was found in the reviewed public pages. | Read-only cross-reference; **never embedded** in LIRC. URL/DOI in source manifests only. Falsifier f018 fires on any embedding attempt. |
| Salis Lab RBS Calculator | v1.0 **GPL v3.0**; v2+ proprietary at De Novo DNA. | v1: subprocess-isolate v1.0 (CLI invocation, no library linking). OSTIR added as permissive fallback. v2+ commercial activation behind `runtime/license_grants/denovodna.yaml`. |

## 23. Open questions resolved by orchestrator (no user round-trip)

| Synthesis open question | Orchestrator's locked decision | Reasoning |
|---|---|---|
| Is HMOs the right MVP wedge? | **Reframed: HMOs are the scientific validation triple, not an MVP wedge.** Build full pipeline; HMO triple = engine correctness probe, not first-paying-customer target. | Operator: "Target is never MVP or first paying customer, we are R&D and pushing boundaries hard." |
| 2'-FL / 3'-SL / a novel sialylated HMO? | **2'-FL / 3'-SL / DSLNT.** | DSLNT is clinically interesting, has no published *E. coli* gram/L titer, stresses both sialyl- and elongation-transferase paths simultaneously. |
| Falsification-driven Bayesian active-inference loop reframe? | **Confirmed and operationalised.** Three-tier falsifier hierarchy + cross-model disagreement + TDA early-warning + closed-loop dossier mode. | Synthesis correct; orchestrator deepens with three-tier hierarchy and learnable thresholds. |
| Cell-free TX-TL adapter Phase 0 vs Phase 2? | **Phase 0 stub adapter at maximum sophistication; Phase 2 wet-lab gated by customer.** | Build everything CPU-side; cutover is a config flag. |
| Unknown-enzyme sub-pipeline v1 vs v1.1? | **v1 full implementation.** RFdiffusion3 + Baker + MACE-OFF + ProDy + Genie-CAT. | Anti-toy directive. |
| Audit-trail shape? | **SBOL3 + PROV-O + Pydantic + LangGraph DAG + sha256 hash chain.** Plus the Zer0pa Synbio Audit-Trail Spec v0.1 as a published Zer0pa standard. | No synbio M15 exists; orchestrator commits to authoring the standard. |
| BioTRY v1 blocker or parked-for-customer? | **Parked for v1; v2 gated on commercial license grant.** | Synthetic-baseline fallback (per-product literature-titer harness) is sufficient for HMO triple validation. |
| Closed-loop dossier mode v1 or v1.1? | **Closed-loop is v1 default.** | Anti-toy; the active-inference loop is incomplete without it. |
| Synbio-equivalent of Health's PubMed-baseline harness? | **Per-product literature-titer baseline.** Curated from published *E. coli* HMO production papers. | Direct fork-and-own from Health's PubMed-baseline pattern. |
| GP kernel choice over discrete ZPE inputs? | **Hamming-distance kernel default.** Categorical-product kernel as plug-replaceable alternative behind the same `SurrogateAdapter` interface. | Synthesis recommendation; mathematically clean; closed-form gradient. |
| Pipeline 4 of 6 mapping (what are pipelines 5 and 6)? | **Open question for operator.** Not orchestrator's call. Logged below. | Operator scope decision. |
| Data-sovereignty defaults? | **Tier-1 customer-isolated for fine-tuned weights; Tier-2 with opt-out for aggregated insights; Tier-3 public for falsifier discoveries and Synbio Audit-Trail Spec.** | Locked. |
| MVP target paper or first-paying-customer engagement? | **Anti-toy directive: neither.** Build the full pipeline; the validation triple is the evidence packet. Paper / customer engagement is downstream. | Operator: "anti-toy." |
| CRO pre-engagement letter? | **Out of scope for overnight execution.** Operator-driven. | The PRD does not commit downstream commercial action. |
| Drift-deletion mandate? | **Carried.** §27 has a DRIFT DELETED card. | Operator's standing memory: "every lane brief includes aggressive drift-deletion clause." |

## 24. Open questions remaining for operator

These are the questions the orchestrator could not resolve autonomously:

1. **Pipeline 4 of 6 mapping.** What are pipelines 5 and 6 (Drug Process Development is the explicit upcoming candidate per the research-agent handover note)? This is operator scope.
2. **Wet-lab Phase 2 customer.** When the agent has built the full pipeline and the closed-loop dossier mode is functional, which customer's Phase 2 wet-lab activates first? Glycom / DSM-Firmenich / Inbiose / ZuChem / Gnubiotics / internal Zer0pa wet-lab? (Operator-driven; informs CRO partnership letter.)
3. **HF mirror visibility for sibling repos.** Health, Materials, Energy each have HF Spaces. Should this synbio HF be cross-referenced from the sibling READMEs as part of the cross-workstream pattern catalogue? (Operator decision.)

These three questions live in `HANDOFF-FROM-OVERNIGHT-EXECUTOR.md` as the agent's open-questions ledger; the operator answers on review.

## 25. Final output required from overnight executor

Before reporting "complete," the overnight executor must commit:

1. The full repo as specified in §7.
2. The committed schemas, fixtures, audit logs, KG exports, and source manifests.
3. The HF mirrors as specified in §14, with manifests in repo.
4. The HMO scientific validation triple evidence packets (`validation/hmo-seed-evidence/2'-FL/`, `3'-SL/`, `DSLNT/`) — each containing the L1-L7 envelope chain, the dossier, the falsifier sweep results, the cross-model disagreement records, and the pre-registered acceptance threshold checks.
5. The Synbio Audit-Trail Spec v0.1 (`docs/synbio-audit-trail-v0.1-spec.md`).
6. `EXECUTION-STATE.md` (live state ledger updated throughout).
7. `FINAL-REPORT.md` with: what was built, what failed, falsification evidence, decision log, commit hash, HF push manifests, next-wave list (Phase 2 wet-lab activation, BioTRY v2 inclusion, De Novo DNA RBS commercial license, Quantum slot promotion, Pipeline 5/6 integration).
8. `HANDOFF-FROM-OVERNIGHT-EXECUTOR.md` with: what the next role inherits, what they produce, the constraints / authorities they operate under, the open questions remaining for the operator.
9. Final push to GitHub. The agent's last action is `git push origin main`. The repo state on `Zer0pa/Synthetic-Biology` is the agent's final report; the operator reviews from a different machine.

## 26. The agent's standing instruction

The agent starts from GitHub on a different machine. It clones or fetches the repo, checks out `main`, reads this PRD once, re-reads `RESISTANCE.md`, and begins execution. It does not interim-report. It does not ask the operator for clarification, permission, or prioritisation while useful work remains. It decides every contested call autonomously using this PRD's locked decisions. It downloads, installs, configures, and locally executes the maximum possible CPU/Mac-side work before declaring increased compute necessary. If the available Mac/local machine can complete a layer or the whole pipeline, it completes it there. If increased compute is required, it leaves the layer as a same-shape REST stub with manifests, fixtures, tests, and Runpod cutover config.

The agent updates GitHub continuously. It pushes bulk artifacts to HF under Architect-Prime continuously when credentials are available. It writes `EXECUTION-STATE.md` as a live ledger. It reads from `briefs/L*-*.md` for per-layer context but does not need to ask the operator for clarification — the PRD is complete.

When done: `FINAL-REPORT.md`, `HANDOFF-FROM-OVERNIGHT-EXECUTOR.md`, `git push`. The operator reviews on GitHub. The HF mirror is the bulk-artifact review surface.

If a stuck point is unresolvable, the agent logs it in `EXECUTION-STATE.md` with `BLOCKED:<reason>:<workaround-attempted>`, continues with the workaround, and moves on. The agent does not stop and ask. The operator reviews blockers on review. The only acceptable early stop is a boundary violation, missing credentials that prevent all useful local work, or a destructive ambiguity that cannot be safely stubbed.

## 27. DRIFT DELETED card

What was pruned versus the synthesis (per operator's standing drift-deletion mandate):

| Removed from synthesis | Reason |
|---|---|
| MVP-wedge framing | Operator: "Target is never MVP or first paying customer." Replaced with scientific validation triple framing. |
| First-paying-customer engagement framing | Operator: "anti-toy." Replaced with R&D-standard gate (§20.6). |
| v1 vs v1.1 deferrals (where the deferral was "save for paying customer") | Operator: "build the most overdesigned and best-in-class pipeline." All physical-hardware-non-gated deferrals collapsed into v1. |
| Closed-loop dossier as v1.1 option | Closed-loop is v1 default. |
| Single-shot dossier as default | Removed; closed-loop is the active-inference completion. |
| Unknown-enzyme sub-pipeline as v1.1 | v1 full implementation. |
| Quantum slot ambiguity | Locked as far-horizon BlockedSourceManifest with three concrete entries; no promotion in v1. |
| BioTRY commercial-license verification as a v1 blocker | Reframed: v1 excluded from training corpus; v2 gated; per-product literature-titer baseline replaces it as engine-vs-baseline harness. |
| ATLAS of Biochemistry as Class C reference layer with possible academic-redistribution | Public terms support academic-use subscription, not redistribution or training-corpus embedding; never embedded; URL/DOI cross-references only. Stricter than synthesis suggested. |
| UniKP / EF-UniKP as in-stack | Inferred MIT but LICENSE not visible via API; excluded from v1 ensemble until executor verifies. |
| Pricing as gating concern | Moved to appendix (§21); not a build directive. |
| CRO pre-engagement letter as PRD output | Out of scope for overnight execution; operator-driven. |
| "Open questions for orchestrator" as PRD section | Resolved in §23. Open questions for operator are §24 only. |

What was added beyond the synthesis:

| Added | Why |
|---|---|
| Three-tier falsifier hierarchy (Fast / Medium / Heavy) | Operationalises the L3.5 ranking gate as a cost-disciplined cascade. |
| L3.5 ranking gate as learnable component | Thresholds are state, not constants; updated nightly against PathGym. |
| Zer0pa Synbio Audit-Trail Specification v0.1 | Closes the "no synbio M15" gap; Zer0pa publishes the standard. |
| Three-tier data sovereignty | Defaults locked. Pricing tiers couple to sovereignty. |
| HMO seed-triple as portable per-engagement motif | Every customer engagement runs known-good / known-borderline / novel. |
| Adversarial three-tier synthetic-negatives sampler | Defends against survivorship bias more aggressively than single-threshold. |
| SynbioTDAEarlyWarning fork-and-own from Energy | Fermentation regime-change detection for both LDBT and in-cell DBTL telemetry. |
| CEKM plug-replaceability test | Four-way ensemble continues to function with CEKM removed; degradation measurable. |
| DSLNT as named novel HMO seed | Refines synthesis's loose "novel sialylated HMO" with a clinically interesting, scientifically demanding target. |
| Strateos+myTXTL programmatic API path | Resolves the "no cell-free TX-TL API" misconception. |
| Quantum slot with three concrete BlockedSourceManifest entries | Far-horizon committed without scientific promotion. |
| HF storage plan under Architect-Prime user (not org) | Operator directive; Mac stays under 42 GiB free. |
| R&D-standard gate (§20.6) | Anti-toy enforcement at acceptance level. |
| 12 named waves (§15) | Overnight execution sequence with parallel sub-agent allocation. |
| All 18+ falsifiers named in `audit/falsifiers.yaml` | Executable spec. |

---

**End of PRD v1.0. Decisions locked. Begin execution.**
