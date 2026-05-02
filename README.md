# Synthetic-Biology

> Live window into the Zer0pa lab. Synthetic Biology / Metabolic Pathway Engineering — Pipeline 4 of 6.

## What This Is

In silico metabolic-pathway-engineering pipeline (L1→L7 + L4.5 + L5_OED) producing predicted pathways, KPIs, and SBOL3-attested genetic-modification specs as research artifacts.

The pipeline trains a Zer0pa-owned **Conditional Enzyme Kinetics Model
(CEKM)** on real BRENDA / EnzyExtract / GotEnzymes2 / ProteinGym
corpora, runs the four-tool L4 kinetics ensemble (DLKcat / CatPred /
TurNuP / CEKM) plus eQuilibrator MDF / COBRApy FBA / FluxGAT
essentiality, scaffolds the L4.5 unknown-enzyme path with RFdiffusion2
+ MACE-OFF + ESMFold + ProDy + Genie-CAT, and emits SBOL3-attested
genetic-modification specifications via L6 host engineering. Every
adapter emits a `UniversalLayerEnvelope` whose 23-falsifier registry,
boundary-block sha256, and license-class enforcement are first-class
audit invariants.

The Human Milk Oligosaccharide (HMO) seed triple — 2'-fucosyllactose,
3'-sialyllactose, and disialyllacto-N-tetraose in *E. coli* iML1515 —
is the validation triple. Pre-registered acceptance thresholds
(`validation/hmo-seed-evidence/<seed>/acceptance.yaml`) are the
binding numerical gates; structural envelope-chain conformance passes
3/3 today.

## Boundary

Research infrastructure for in silico synthetic biology / metabolic pathway engineering. Outputs are research artifacts — predicted pathways, predicted KPIs, candidate genetic modification specifications. No regulatory certification claims. No clinical or human-subject use. No environmental release of GMOs. No biocontainment-level claims (the pipeline does not commission BSL-2/3 work). No human gene drive or eugenic application. Defence / weapons / dual-use bio applications excluded under operator policy.

## Pipeline Mechanics

| Field | Value |
| --- | --- |
| Architecture | METABOLIC_PATHWAY_PIPELINE (L1 ZPE → L2 LIRC → L3 retrosynthesis → L3.5 ranking → L4 deep-eval → L4.5 unknown-enzyme → L5 MFMO → L5_OED → L6 host engineering → L6_BUILD cell-free TX-TL → L7 dossier) |
| Substrate | UniversalLayerEnvelope (Pydantic v2 + canonical-JSON sha256), SBOL3-attested L6 spec, PROV-O JSON-LD chain, DuckDB audit + GraphML/Cypher/RDF KG export |
| Execution | Mac CPU + H100 SXM 80 GB (autonomous orchestrator on Runpod, 10-phase chain with resume sentinels) |
| Toolchain | torch 2.2/cu130 + transformers (ESM-2 650M / ESMFold) + RFdiffusion2 (BSD-3) + MACE-OFF (medium) + equilibrator-pathway (MDF LP) + COBRApy + ripser/persim (TDA) + BoTorch (Hamming kernel + qLogNEHVI) + selfies + RDKit |
| Discipline | 23 falsifiers across 3 tiers (Tier-A fast / Tier-B medium / Tier-C heavy) + cross-model disagreement first-class + GPL-subprocess isolation (Salis RBS Calculator v1.0) + RESISTANCE.md anti-corruption protocol |
| Compute Status | v0.1 CEKM training on real corpus on H100 (loss 6.93→3.72 over 2000 fp32 steps; max_steps=20000 in-progress); HMO triple Wave 9 + L4.5 inference scheduled in same chain |

## Key Metrics

| Metric | Value | Baseline |
| --- | --- | --- |
| CEKM_REAL_CORPUS_LOSS | 6.93 → 3.72 (steps 0 → 2000) | total: 33,851 in-corpus rows + 5,961 held-out + 101,553 adversarial Tier α/β/γ negatives |
| HMO_TRIPLE_AUDIT_VERIFY | 3/3 PASS | conformance verifier per docs/synbio-audit-trail-v0.1-spec.md §10 (envelope schema, boundary sha256, SBOL3 attestation, license-class) |
| CPU_PIPELINE_TESTS | 256 passing, 59 GPU-skipped | 0 regressions across CPU continuation A-H |
| AUTONOMOUS_CHAIN_PHASES | 10 / 10 covered | preflight → install → stage → CEKM train → eval → HF push → L4.5 inference → HMO triple → audit verify → finalize |

> Source: PRD.md, FINAL-REPORT.md, FINAL-REPORT-RUNPOD.md, FINAL-REPORT-RUNPOD-AUTONOMOUS.md, validation/hmo-seed-evidence/, audit/runtime/runpod/.

## Repo Identity

| Field | Value |
| --- | --- |
| Identifier | Synthetic-Biology |
| Repository | https://github.com/Zer0pa/Synthetic-Biology |
| Portfolio | Bio-Engineering |
| Visibility | INTERNAL |
| Default Branch | main |
| Authority Source | PRD.md (locked v1.0 decisions) |
| License | repository license file |

## Readiness

| Field | Value |
| --- | --- |
| Evidence posture | live in-progress workstream; not a productized service |
| Checks | 256 passing tests + 23 falsifiers + 3/3 HMO seed audit-verify PASS |
| Custody boundary | bulk weights + audit JSONL on HF [Architect-Prime/synbio-cekm-v0.1](https://huggingface.co/Architect-Prime/synbio-cekm-v0.1); envelope chains + dossiers + manifests in git |
| Confidence | scoped by Tier-A/B/C falsifier hierarchy; PathGym DBTL-holdout calibration deferred |
| Authority | PRD.md (locked decisions); FINAL-REPORT-RUNPOD-AUTONOMOUS.md (current chain); HANDOFF-CPU-CONTINUATION.md (post-pod release record) |

### Honest Blocker

CEKM v0.1 is a real-corpus smoke checkpoint mid-training (target step 20000; current ckpts on HF at step 500/1000/1500/2000). Wet-lab Phase 2 dispatch is triple-gated and never on the cutover path. PathGym DBTL holdout calibration of TDA `warning_score` thresholds and L5 surrogate calibration scores is deferred to held-out post-experiment data. Real RFdiffusion2 motif-conditional designs require curated TS-mimetic geometry, downstream of v0.1 (current path produces unconditional 100-residue scaffolds as proof-of-life). BRENDA bulk download requires registration; v0.1 trains on EnzyExtract dark-matter + GotEnzymes2 + ProteinGym subsets, not full BRENDA core.

## What We Prove

- Real CEKM training on real corpus runs end-to-end on H100 SXM (EnzyExtract 60K + GotEnzymes2 17K → 33K in-corpus + 6K held-out + 100K adversarial Tier α/β/γ negatives; loss curve 6.93 → 3.72 over 2000 fp32 steps with sustained 0.35 steps/s throughput; resume-safe across mfs-quota-induced ckpt-save corruption).
- HMO scientific-validation triple emits structurally complete L1→L7 envelope chains for 2'-fucosyllactose / 3'-sialyllactose / disialyllacto-N-tetraose; `synbio audit verify` passes 3/3 under the conformance verifier (envelope-schema valid, boundary-sha256 canonical, SBOL3 attestation present on every L6 envelope, Class C/D/E license-grants enforced, cross-model disagreement records emitted, falsifier registry loaded).
- L4B real eQuilibrator MDF on HMO precursor pathway: 2'-FL MDF=+6.78, 3'-SL +11.84, DSLNT +11.41 kJ/mol via `equilibrator_pathway.ThermodynamicModel.mdf_analysis()` with per-compound optimal concentrations in the 1 μM – 10 mM physiological window.
- L5 real BoTorch surrogate: GP per objective with custom Hamming-distance kernel + `qLogNoisyExpectedHypervolumeImprovement` + ASR-thermostable warm-starts (split-venv subprocess pattern; weights stay float32, autocast handles per-op casting; plug-replaceability invariant preserved across real-vs-stub paths).
- TDA real fermentation simulator: 5-state Monod ODE via `scipy.integrate.solve_ivp(LSODA)` covering all five PRD §5.3 failure modes (oxygen-transfer collapse / byproduct buildup / growth stall / toxicity threshold / nutrient depletion) with multi-channel ripser bottleneck + late-vs-early rate-of-change hybrid early-warning.
- Synbio Audit-Trail Specification v0.1 (CC BY 4.0, Zer0pa-published): SBOL3 + PROV-O extension + canonical-JSON sha256 hash chain + Class A/B/C/D/E license-class enforcement + GPL-subprocess-isolation pattern (Salis RBS Calculator v1.0 binary wrapper, no Python `import` of GPL modules).

## What We Don't Claim

- This is not a clinical or human-subject pipeline. No diagnostic, therapeutic, or device claims.
- This is not a deployed industrial production system. No commercial titer guarantees.
- The CEKM v0.1 checkpoint is not a calibrated affinity predictor; it is a real-corpus smoke checkpoint with bounded loss-decline evidence on a held-out partition.
- HMO predictions are advisory research artifacts, not regulatory submissions or product specifications. Wet-lab validation is operator-gated and never on the cutover path.
- The L4.5 unknown-enzyme path emits Tier-1 / Tier-2 / Tier-3 advisories per PRD §6.6; these are research suggestions, not enzyme designs warranting downstream synthesis without independent verification.
- No environmental release of GMOs. No human gene drive or eugenic application. Defence / weapons / dual-use bio applications excluded under operator policy.

## Repo Shape

- `src/zer0pa_synbio/` — adapters L1-L7, envelope, falsifiers, CEKM model + train + loaders, KG writer, audit writer, TDA simulator, runpod_inference, CLI
- `audit/` — falsifiers.yaml, source_manifests/, license_grants/, runtime/ (gitignored except runpod state surface)
- `validation/hmo-seed-evidence/` — 2'-FL / 3'-SL / DSLNT triple with acceptance.yaml + dossier.json + envelope_chain.json + RESULT.md per seed
- `kg/` — schema.cypher + nodes.csv + edges.csv (Neo4j-shaped + GraphML/Cypher/RDF/Turtle export)
- `tests/` — 256 passing tests across contract / integration / falsification waves / cutover invariance
- `docs/` — Synbio Audit-Trail Spec v0.1 (CC BY 4.0)
- `scripts/runpod/` — autonomous H100 SXM chain (bootstrap, orchestrator, heartbeat, watchdog, 10 phase scripts) + Mac-side wake-up watcher + corpus stager
- `configs/` — wave4 real-corpus CEKM training + runpod orchestrator phase config
- `fixtures/` — LIRC slice + CEKM mini-fixtures + per-source manifests

## Read Order (for next agents)

1. [BOUNDARY.md](BOUNDARY.md) — the binding boundary block.
2. [PRD.md](PRD.md) — the controlling spec (orchestrator's locked v1.0 decisions).
3. [RESISTANCE.md](RESISTANCE.md) — anti-corruption discipline; binding meta-protocol.
4. [HANDOFF-CPU-CONTINUATION.md](HANDOFF-CPU-CONTINUATION.md) — what the CPU-continuation phase did (items A-H).
5. [FINAL-REPORT-RUNPOD-AUTONOMOUS.md](FINAL-REPORT-RUNPOD-AUTONOMOUS.md) — what the autonomous H100 chain produced.
6. [RUNPOD-AUTONOMOUS-RUNBOOK.md](RUNPOD-AUTONOMOUS-RUNBOOK.md) — operator runbook for the autonomous chain.
7. [NEXT-WAVE-PLAN.md](NEXT-WAVE-PLAN.md) — open work, ordered by priority.
8. [docs/synbio-audit-trail-v0.1-spec.md](docs/synbio-audit-trail-v0.1-spec.md) — the published Zer0pa standard.
9. [MODUS-OPERANDI.md](MODUS-OPERANDI.md) — the multi-agent role chain.

## Cross-workstream principle

This workstream runs in parallel with `Zer0pa/Health`, `Zer0pa/Materials`, and `Zer0pa/Energy`. Each workstream is built end-to-end as an independent pipeline. **No substrate is shared at runtime.** Fork-and-own is required: copy the pattern, reimplement inside Synthetic Biology. The research agent's three cross-workstream substrate-sharing recommendations (Shared Infrastructure Layer, Cross-Pipeline Gym Flywheel, single SE(3) MACE service) are captured-and-overridden per operator policy.

## Provenance

- Initial commit: 2026-05-01.
- CPU continuation phase (items A-H): 2026-05-01 — see commits `52b8ad2` through `3d8317f`.
- Autonomous H100 SXM chain bootstrap + 10-phase orchestrator: 2026-05-01 — `29dc4f2`.
- Real MACE-OFF binding ΔG + RFdiffusion2 inference modules: 2026-05-02 — `a5fc98e`.
- Pod 1hx4ctwg1mpmxr autonomous run: 2026-05-02.
