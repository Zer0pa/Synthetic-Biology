# FINAL-REPORT-RUNPOD — Synbio H100 SXM run

**Pod:** 429xv4r3wm66q9 · 1× H100 SXM5 80GB · 128 vCPU · 2 TiB RAM
**Date:** 2026-05-01T15:13:52+00:00
**Repo HEAD:** 
**Boundary:** Research infrastructure for in silico synthetic biology / metabolic pathway engineering. Outputs are research artifacts — predicted pathways, predicted KPIs, candidate genetic modification specifications. No regulatory certification claims. No clinical or human-subject use. No environmental release of GMOs. No biocontainment-level claims (the pipeline does not commission BSL-2/3 work). No human gene drive or eugenic application. Defence / weapons / dual-use bio applications excluded under operator policy.

## Counts (this run)

| Artifact | Count |
|---|---|
| 2'-FL envelope chain length | 21 |
| 3'-SL envelope chain length | 24 |
| DSLNT envelope chain length | 24 |
| Cross-model disagreement records | 9 |
| Early-warning signals | 6 |
| PathGym ReasonerTuple seeds | 6 |

## Phase ledger

```
[2026-05-01T15:11:21+00:00]        Last 20 lines of log:
         Running HMO seed: 3pSL} (scientific mode)
         usage: run_seed.py [-h] --seed {2pFL,3pSL,DSLNT}
         run_seed.py: error: argument --seed: invalid choice: '3pSL}' (choose from '2pFL', '3pSL', 'DSLNT')
[2026-05-01T15:11:21+00:00] START 60_hmo_dslnt: HMO seed: DSLNT (scientific mode)
[2026-05-01T15:11:24+00:00] FAIL  60_hmo_dslnt: HMO seed: DSLNT (scientific mode) (rc=2; log: /workspace/synbio-run/logs/60_hmo_dslnt.log)
[2026-05-01T15:11:24+00:00]        Last 20 lines of log:
         Running HMO seed: DSLNT} (scientific mode)
         usage: run_seed.py [-h] --seed {2pFL,3pSL,DSLNT}
         run_seed.py: error: argument --seed: invalid choice: 'DSLNT}' (choose from '2pFL', '3pSL', 'DSLNT')
[2026-05-01T15:11:24+00:00] START 70_audit_verify: Audit conformance verify all 3 seeds
[2026-05-01T15:11:25+00:00] FAIL  70_audit_verify: Audit conformance verify all 3 seeds (rc=1; log: /workspace/synbio-run/logs/70_audit_verify.log)
[2026-05-01T15:11:25+00:00]        Last 20 lines of log:
         === hmo_seed_2pFL ===
         Audit conformance — campaign hmo_seed_2pFL
           ✗ runtime_dir_present: No runtime at /workspace/synbio-run/repo/audit/runtime/hmo_seed_2pFL
         OVERALL: FAIL
[2026-05-01T15:11:25+00:00] START 80_hf_smoke: HF Architect-Prime smoke push
[2026-05-01T15:11:29+00:00] DONE  80_hf_smoke: HF Architect-Prime smoke push (log: /workspace/synbio-run/logs/80_hf_smoke.log)
[2026-05-01T15:11:30+00:00] START 90_final_report: Write FINAL-REPORT-RUNPOD.md
[2026-05-01T15:11:30+00:00] FAIL  90_final_report: Write FINAL-REPORT-RUNPOD.md (rc=1; log: /workspace/synbio-run/logs/90_final_report.log)
[2026-05-01T15:11:30+00:00]        Last 20 lines of log:
         /workspace/synbio-run/repo/runtime/phases/90_final_report.sh: line 10: /workspace/synbio-run/repo/audit/runtime/hmo_seed_2pFL/envelopes.jsonl: No such file or directory
         /workspace/synbio-run/repo/runtime/phases/90_final_report.sh: line 11: /workspace/synbio-run/repo/audit/runtime/hmo_seed_3pSL/envelopes.jsonl: No such file or directory
         /workspace/synbio-run/repo/runtime/phases/90_final_report.sh: line 12: /workspace/synbio-run/repo/audit/runtime/hmo_seed_DSLNT/envelopes.jsonl: No such file or directory
[2026-05-01T15:11:30+00:00] START 95_git_push: git push origin main
[2026-05-01T15:11:30+00:00] DONE  95_git_push: git push origin main (log: /workspace/synbio-run/logs/95_git_push.log)
[2026-05-01T15:11:30+00:00] ==== ALL PHASES COMPLETE ====
[2026-05-01T15:11:30+00:00] See /workspace/synbio-run/state/STATUS.txt for the full ledger; /workspace/synbio-run/logs/*.log for per-phase output.
[2026-05-01T15:11:30+00:00] orchestrator exit
[2026-05-01T15:12:28+00:00] ==== Zer0pa Synbio Pod Orchestrator ====
[2026-05-01T15:12:28+00:00] RUN_ROOT=/workspace/synbio-run
[2026-05-01T15:12:28+00:00] REPO=/workspace/synbio-run/repo (no git)
[2026-05-01T15:12:28+00:00] GPU: NVIDIA H100 80GB HBM3, 81559 MiB
[2026-05-01T15:12:28+00:00] SKIP  00_health_check: Pod + Python + GPU sanity (already done; marker /workspace/synbio-run/state/00_health_check.done)
[2026-05-01T15:12:28+00:00] SKIP  10_pull_models: HF model pulls (ESM-2-650M) (already done; marker /workspace/synbio-run/state/10_pull_models.done)
[2026-05-01T15:12:28+00:00] SKIP  20_lirc_slice: LIRC slice (real Rhea metadata) (already done; marker /workspace/synbio-run/state/20_lirc_slice.done)
[2026-05-01T15:12:28+00:00] SKIP  30_test_suite: pytest -q (full suite) (already done; marker /workspace/synbio-run/state/30_test_suite.done)
[2026-05-01T15:12:28+00:00] SKIP  40_cutover_invariance: Wave 11 invariance under runpod_rest (already done; marker /workspace/synbio-run/state/40_cutover_invariance.done)
[2026-05-01T15:12:28+00:00] SKIP  50_esm2_real_l1: Real ESM-2 batched embeddings (L1) (already done; marker /workspace/synbio-run/state/50_esm2_real_l1.done)
[2026-05-01T15:12:28+00:00] START 60_hmo_2pfl: HMO seed: 2'-FL (scientific mode)
[2026-05-01T15:12:56+00:00] DONE  60_hmo_2pfl: HMO seed: 2'-FL (scientific mode) (log: /workspace/synbio-run/logs/60_hmo_2pfl.log)
[2026-05-01T15:12:56+00:00] START 60_hmo_3psl: HMO seed: 3'-SL (scientific mode)
[2026-05-01T15:13:23+00:00] DONE  60_hmo_3psl: HMO seed: 3'-SL (scientific mode) (log: /workspace/synbio-run/logs/60_hmo_3psl.log)
[2026-05-01T15:13:23+00:00] START 60_hmo_dslnt: HMO seed: DSLNT (scientific mode)
[2026-05-01T15:13:50+00:00] DONE  60_hmo_dslnt: HMO seed: DSLNT (scientific mode) (log: /workspace/synbio-run/logs/60_hmo_dslnt.log)
[2026-05-01T15:13:50+00:00] START 70_audit_verify: Audit conformance verify all 3 seeds
[2026-05-01T15:13:52+00:00] DONE  70_audit_verify: Audit conformance verify all 3 seeds (log: /workspace/synbio-run/logs/70_audit_verify.log)
[2026-05-01T15:13:52+00:00] SKIP  80_hf_smoke: HF Architect-Prime smoke push (already done; marker /workspace/synbio-run/state/80_hf_smoke.done)
[2026-05-01T15:13:52+00:00] START 90_final_report: Write FINAL-REPORT-RUNPOD.md
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
  ✓ disagreement_records_present: 3 cross-model disagreement record(s)
  ✓ falsifier_registry_loaded: 23 falsifiers in registry; 10 layer(s) seen in run
  ✓ dossier_hash_chain_reconstructs: 1 dossier(s) reconstruct cleanly
OVERALL: PASS
=== hmo_seed_3pSL ===
Audit conformance — campaign hmo_seed_3pSL
  ✓ runtime_dir_present: Runtime at /workspace/synbio-run/repo/audit/runtime/hmo_seed_3pSL
  ✓ envelopes_present: 24 envelope(s) recorded
  ✓ boundary_block_canonical: All 24 envelopes carry canonical boundary
  ✓ envelope_schema_valid: All envelopes validate against synbio.envelope.v0.1
  ✓ envelope_id_format: All envelope_ids are sha256-prefixed
  ✓ license_class_grants: All Class C/D/E envelopes carry an audit/license_grants/ URI
  ✓ stub_no_scientific_validity: No stub envelope claimed scientific_valid=True
  ✓ l6_sbol_attestation: Every L6 envelope carries sbol_attestation_present=True
  ✓ prov_o_jsonld_valid: All envelopes carry parseable PROV-O JSON-LD with synbio: namespace
  ✓ disagreement_records_present: 3 cross-model disagreement record(s)
  ✓ falsifier_registry_loaded: 23 falsifiers in registry; 11 layer(s) seen in run
  ✓ dossier_hash_chain_reconstructs: 1 dossier(s) reconstruct cleanly
OVERALL: PASS
=== hmo_seed_DSLNT ===
Audit conformance — campaign hmo_seed_DSLNT
  ✓ runtime_dir_present: Runtime at /workspace/synbio-run/repo/audit/runtime/hmo_seed_DSLNT
  ✓ envelopes_present: 24 envelope(s) recorded
  ✓ boundary_block_canonical: All 24 envelopes carry canonical boundary
  ✓ envelope_schema_valid: All envelopes validate against synbio.envelope.v0.1
  ✓ envelope_id_format: All envelope_ids are sha256-prefixed
  ✓ license_class_grants: All Class C/D/E envelopes carry an audit/license_grants/ URI
  ✓ stub_no_scientific_validity: No stub envelope claimed scientific_valid=True
  ✓ l6_sbol_attestation: Every L6 envelope carries sbol_attestation_present=True
  ✓ prov_o_jsonld_valid: All envelopes carry parseable PROV-O JSON-LD with synbio: namespace
  ✓ disagreement_records_present: 3 cross-model disagreement record(s)
  ✓ falsifier_registry_loaded: 23 falsifiers in registry; 11 layer(s) seen in run
  ✓ dossier_hash_chain_reconstructs: 1 dossier(s) reconstruct cleanly
OVERALL: PASS
OK: all 3 HMO seeds pass conformance.
```

## Compute saturation

GPU was used by phases: 10_pull_models, 50_esm2_real_l1, 60_hmo_*. CPU-bound
phases (LIRC, audit verify, dossier emission, BoTorch fits) ran in parallel
where the orchestrator allowed.

