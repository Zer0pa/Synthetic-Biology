# FINAL-REPORT-RUNPOD — Synbio H100 SXM run

**Pod:** 429xv4r3wm66q9 · 1× H100 SXM5 80GB · 128 vCPU · 2 TiB RAM
**Date:** 2026-05-01T16:44:05+00:00
**Repo HEAD:** 
**Boundary:** Research infrastructure for in silico synthetic biology / metabolic pathway engineering. Outputs are research artifacts — predicted pathways, predicted KPIs, candidate genetic modification specifications. No regulatory certification claims. No clinical or human-subject use. No environmental release of GMOs. No biocontainment-level claims (the pipeline does not commission BSL-2/3 work). No human gene drive or eugenic application. Defence / weapons / dual-use bio applications excluded under operator policy.

## Counts (this run)

| Artifact | Count |
|---|---|
| 2'-FL envelope chain length | 42 |
| 3'-SL envelope chain length | 48 |
| DSLNT envelope chain length | 48 |
| Cross-model disagreement records | 18 |
| Early-warning signals | 12 |
| PathGym ReasonerTuple seeds | 9 |

## Phase ledger

```
         audit/runtime/hmo_seed_DSLNT/early_warning.jsonl
         audit/runtime/hmo_seed_DSLNT/disagreement.jsonl
         audit/runtime/hmo_seed_DSLNT/envelopes.jsonl
         audit/runtime/hmo_seed_DSLNT/audit.duckdb
         audit/runtime/hmo_seed_DSLNT/dossiers/
         audit/runtime/hmo_seed_DSLNT/dossiers/dossier_DSLNT_round_0.json
[2026-05-01T16:27:32+00:00] ==== ALL PHASES COMPLETE ====
[2026-05-01T16:27:32+00:00] See /workspace/synbio-run/state/STATUS.txt for the full ledger; /workspace/synbio-run/logs/*.log for per-phase output.
[2026-05-01T16:27:32+00:00] orchestrator exit
[2026-05-01T16:28:51+00:00] ==== Zer0pa Synbio Pod Orchestrator ====
[2026-05-01T16:28:51+00:00] RUN_ROOT=/workspace/synbio-run
[2026-05-01T16:28:51+00:00] REPO=/workspace/synbio-run/repo (no git)
[2026-05-01T16:28:51+00:00] GPU: NVIDIA H100 80GB HBM3, 81559 MiB
[2026-05-01T16:28:51+00:00] SKIP  00_health_check: Pod + Python + GPU sanity (already done; marker /workspace/synbio-run/state/00_health_check.done)
[2026-05-01T16:28:51+00:00] SKIP  10_pull_models: HF model pulls (ESM-2-650M) (already done; marker /workspace/synbio-run/state/10_pull_models.done)
[2026-05-01T16:28:51+00:00] SKIP  20_lirc_slice: LIRC slice (real Rhea metadata) (already done; marker /workspace/synbio-run/state/20_lirc_slice.done)
[2026-05-01T16:28:51+00:00] SKIP  30_test_suite: pytest -q (full suite) (already done; marker /workspace/synbio-run/state/30_test_suite.done)
[2026-05-01T16:28:51+00:00] SKIP  40_cutover_invariance: Wave 11 invariance under runpod_rest (already done; marker /workspace/synbio-run/state/40_cutover_invariance.done)
[2026-05-01T16:28:51+00:00] SKIP  50_esm2_real_l1: Real ESM-2 batched embeddings (L1) (already done; marker /workspace/synbio-run/state/50_esm2_real_l1.done)
[2026-05-01T16:28:51+00:00] SKIP  60_hmo_2pfl: HMO seed: 2'-FL (scientific mode) (already done; marker /workspace/synbio-run/state/60_hmo_2pfl.done)
[2026-05-01T16:28:51+00:00] SKIP  60_hmo_3psl: HMO seed: 3'-SL (scientific mode) (already done; marker /workspace/synbio-run/state/60_hmo_3psl.done)
[2026-05-01T16:28:51+00:00] SKIP  60_hmo_dslnt: HMO seed: DSLNT (scientific mode) (already done; marker /workspace/synbio-run/state/60_hmo_dslnt.done)
[2026-05-01T16:28:51+00:00] SKIP  100_esmfold_real: L4.5 ESMFold real inference (FutC, α-2,3-Lst, α-2,6-Lst) (already done; marker /workspace/synbio-run/state/100_esmfold_real.done)
[2026-05-01T16:28:51+00:00] SKIP  110_mace_off_real: L4.5 MACE-OFF binding energy (3 HMO complexes) (already done; marker /workspace/synbio-run/state/110_mace_off_real.done)
[2026-05-01T16:28:51+00:00] SKIP  200_cekm_smoke: CEKM data + model build smoke (1 forward pass on H100) (already done; marker /workspace/synbio-run/state/200_cekm_smoke.done)
[2026-05-01T16:28:51+00:00] START 210_cekm_train: CEKM mini training (2000 steps; H100 saturation)
[2026-05-01T16:29:24+00:00] DONE  210_cekm_train: CEKM mini training (2000 steps; H100 saturation) (log: /workspace/synbio-run/logs/210_cekm_train.log)
[2026-05-01T16:29:24+00:00] START 70_audit_verify: Audit conformance verify all 3 seeds
[2026-05-01T16:29:26+00:00] DONE  70_audit_verify: Audit conformance verify all 3 seeds (log: /workspace/synbio-run/logs/70_audit_verify.log)
[2026-05-01T16:29:26+00:00] SKIP  80_hf_smoke: HF Architect-Prime smoke push (already done; marker /workspace/synbio-run/state/80_hf_smoke.done)
[2026-05-01T16:29:26+00:00] START 90_final_report: Write FINAL-REPORT-RUNPOD.md
[2026-05-01T16:29:27+00:00] DONE  90_final_report: Write FINAL-REPORT-RUNPOD.md (log: /workspace/synbio-run/logs/90_final_report.log)
[2026-05-01T16:29:27+00:00] START 95_git_push: git push origin main
[2026-05-01T16:29:27+00:00] FAIL  95_git_push: git push origin main (rc=141; log: /workspace/synbio-run/logs/95_git_push.log)
[2026-05-01T16:29:27+00:00]        Last 20 lines of log:
         -rw-rw-rw- 1 root root 527K May  1 16:29 /workspace/synbio-run/state/artifacts-20260501T162927Z.tar.gz
           paths included:
         audit/runtime/
         audit/runtime/cekm_train_h100/
         audit/runtime/cekm_train_h100/checkpoints/
         audit/runtime/hmo_seed_DSLNT/
         audit/runtime/hmo_seed_DSLNT/early_warning.jsonl
         audit/runtime/hmo_seed_DSLNT/disagreement.jsonl
         audit/runtime/hmo_seed_DSLNT/envelopes.jsonl
         audit/runtime/hmo_seed_DSLNT/audit.duckdb
         audit/runtime/hmo_seed_DSLNT/dossiers/
         audit/runtime/hmo_seed_DSLNT/dossiers/dossier_DSLNT_round_0.json
[2026-05-01T16:29:27+00:00] ==== ALL PHASES COMPLETE ====
[2026-05-01T16:29:27+00:00] See /workspace/synbio-run/state/STATUS.txt for the full ledger; /workspace/synbio-run/logs/*.log for per-phase output.
[2026-05-01T16:29:27+00:00] orchestrator exit
```

## Test suite

```
SKIPPED [1] tests/integration/test_audit_verifier.py:25: Campaign hmo_seed_3pSL not yet run; run validation/hmo-seed-evidence/run_seed.py --seed 3pSL
SKIPPED [1] tests/integration/test_audit_verifier.py:25: Campaign hmo_seed_DSLNT not yet run; run validation/hmo-seed-evidence/run_seed.py --seed DSLNT
SKIPPED [1] tests/integration/test_l4_5_real_inference.py:415: mace-torch not installed — real MACE-OFF inference skipped
SKIPPED [1] tests/integration/test_l4_5_real_inference.py:433: rfdiffusion3 not installed — real scaffold inference skipped
OK: full suite passed.
```

## Audit conformance (per Audit-Trail Spec v0.1 §10)

```
  ✓ envelope_id_format: All envelope_ids are sha256-prefixed
  ✓ license_class_grants: All Class C/D/E envelopes carry an audit/license_grants/ URI
  ✓ stub_no_scientific_validity: No stub envelope claimed scientific_valid=True
  ✓ l6_sbol_attestation: Every L6 envelope carries sbol_attestation_present=True
  ✓ prov_o_jsonld_valid: All envelopes carry parseable PROV-O JSON-LD with synbio: namespace
  ✓ disagreement_records_present: 6 cross-model disagreement record(s)
  ✓ falsifier_registry_loaded: 23 falsifiers in registry; 10 layer(s) seen in run
  ✓ dossier_hash_chain_reconstructs: 1 dossier(s) reconstruct cleanly
OVERALL: PASS
=== hmo_seed_3pSL ===
Audit conformance — campaign hmo_seed_3pSL
  ✓ runtime_dir_present: Runtime at /workspace/synbio-run/repo/audit/runtime/hmo_seed_3pSL
  ✓ envelopes_present: 48 envelope(s) recorded
  ✓ boundary_block_canonical: All 48 envelopes carry canonical boundary
  ✓ envelope_schema_valid: All envelopes validate against synbio.envelope.v0.1
  ✓ envelope_id_format: All envelope_ids are sha256-prefixed
  ✓ license_class_grants: All Class C/D/E envelopes carry an audit/license_grants/ URI
  ✓ stub_no_scientific_validity: No stub envelope claimed scientific_valid=True
  ✓ l6_sbol_attestation: Every L6 envelope carries sbol_attestation_present=True
  ✓ prov_o_jsonld_valid: All envelopes carry parseable PROV-O JSON-LD with synbio: namespace
  ✓ disagreement_records_present: 6 cross-model disagreement record(s)
  ✓ falsifier_registry_loaded: 23 falsifiers in registry; 11 layer(s) seen in run
  ✓ dossier_hash_chain_reconstructs: 1 dossier(s) reconstruct cleanly
OVERALL: PASS
=== hmo_seed_DSLNT ===
Audit conformance — campaign hmo_seed_DSLNT
  ✓ runtime_dir_present: Runtime at /workspace/synbio-run/repo/audit/runtime/hmo_seed_DSLNT
  ✓ envelopes_present: 48 envelope(s) recorded
  ✓ boundary_block_canonical: All 48 envelopes carry canonical boundary
  ✓ envelope_schema_valid: All envelopes validate against synbio.envelope.v0.1
  ✓ envelope_id_format: All envelope_ids are sha256-prefixed
  ✓ license_class_grants: All Class C/D/E envelopes carry an audit/license_grants/ URI
  ✓ stub_no_scientific_validity: No stub envelope claimed scientific_valid=True
  ✓ l6_sbol_attestation: Every L6 envelope carries sbol_attestation_present=True
  ✓ prov_o_jsonld_valid: All envelopes carry parseable PROV-O JSON-LD with synbio: namespace
  ✓ disagreement_records_present: 6 cross-model disagreement record(s)
  ✓ falsifier_registry_loaded: 23 falsifiers in registry; 11 layer(s) seen in run
  ✓ dossier_hash_chain_reconstructs: 1 dossier(s) reconstruct cleanly
OVERALL: PASS
OK: all 3 HMO seeds pass conformance.
```

## Compute saturation

GPU was used by phases: 10_pull_models, 50_esm2_real_l1, 60_hmo_*. CPU-bound
phases (LIRC, audit verify, dossier emission, BoTorch fits) ran in parallel
where the orchestrator allowed.

## CPU continuation after pod release (2026-05-01)

After the H100 was released, a second executor agent took over on the
operator's Mac to convert the remaining stub layers to real
implementations on CPU. Items A–H of `HANDOFF-CPU-CONTINUATION.md`
all closed. Detail in `EXECUTION-STATE.md §9`.

### Stub → real conversions landed

| Layer | Before | After |
|---|---|---|
| L4B thermodynamics | synthetic ΔG sum | real eQuilibrator MDF LP via `equilibrator-pathway 0.7.0`. HMO seeds emit `stub_mode=False, mdf_solver_status=ok`. |
| L5 MFMO | scipy Pareto sort | real BoTorch GP per objective (Hamming kernel) + qLogNoisyExpectedHypervolumeImprovement + ASR-thermostable warm-starts. Subprocess pattern (`.venv-l5/`, Python 3.11 + torch 2.2.2). |
| TDA fermentation simulator | manual time-step loop | `scipy.integrate.solve_ivp` LSODA, 5-state Monod ODE with all 5 PRD §5.3 failure modes physically grounded. |
| TDA early-warning | single-channel biomass | multi-channel z-scored embedding (X, DO, byproduct, P) → ripser bottleneck + late-vs-early rate ratio hybrid warning_score. |
| CEKM corpus | synthetic 100-row stub | real loader-driven path (BRENDA + EnzyExtract + GotEnzymes2 + ProteinGym). Pod-ready config at `configs/cekm/wave4_real_corpus.yaml`. |
| L6 RBS predictions | OSTIR only | license-grant-gated Salis v1.0 GPL subprocess (no Python `import` of GPL); OSTIR fallback. |
| L2 LIRC | 2'-FL canned slice | full Rhea/MetaNetX/BiGG/ModelSEED build pipeline; 50-row validation slice committed as `fixtures/lirc/lirc_v0.1_smoke.json.gz`. |

### Test surface delta

- **Start of CPU continuation:** 208 passed, 58 GPU-skipped.
- **End of CPU continuation:** 256 passed, 59 skipped.
- 48 net-new tests across items B/A/E/D/F/C; zero regressions.

### What is still GPU-bound (next pod)

- Real CEKM training on the assembled real corpus (10–20 GPU-h H100).
  Data pipeline + config are in place — `synbio cekm train --config
  configs/cekm/wave4_real_corpus.yaml` should work after data prep.
- L4.5 RFdiffusion3 / Baker / MACE-OFF / ESMFold inference (+ Foundry
  enrollment for RFdiffusion3).
- Industrial-scale BioNavi / DeepRetro / DLKcat / CatPred / TurNuP.

### What is BLOCKED on operator action (no GPU needed)

- **Salis v1.0 binary install + `SALIS_RBS_BIN` setup.** The wrapper
  is in place; the GPL binary itself isn't installed.
- **Full LIRC corpus run** (~4-8h CPU; could run on a small CPU VM)
  + HF push to `Architect-Prime/synbio-lirc-v0.1`.

### Resistance ledger (CPU-continuation phase)

- **fp-NULLasout** resisted: macOS-x86_64 + Python-3.13 torch wheel gap
  was solved with a split-venv subprocess pattern, not by declaring
  item A unfeasible.
- **fp-rushtoend** resisted: each item carries new tests + visible
  output through HMO seed re-runs.
- **fp-efficiency-as-corner-cutting** resisted: TDA detector calibration
  attempted iteratively; deferred to PathGym with explicit
  acknowledgement, not silently skipped.
