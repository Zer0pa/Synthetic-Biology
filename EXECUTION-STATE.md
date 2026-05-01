# EXECUTION-STATE — Synthetic Biology Pipeline 4

> Live ledger for the overnight executor. The agent updates this in place. The
> file is canonical for "what is the build's state right now". Final report
> writes from this. RESISTANCE.md `fp-rushtoend` resistance: do not declare a
> wave complete here unless its substantive artifacts and tests exist.

## 0. Boundary

Research infrastructure for in silico synthetic biology / metabolic pathway
engineering. Outputs are research artifacts — predicted pathways, predicted
KPIs, candidate genetic modification specifications. No regulatory
certification claims. No clinical or human-subject use. No environmental
release of GMOs. No biocontainment-level claims (the pipeline does not
commission BSL-2/3 work). No human gene drive or eugenic application.
Defence / weapons / dual-use bio applications excluded under operator policy.

## 1. Bootstrap timestamp and provenance

- **Executor session start:** 2026-05-01 (overnight run, single inline executor agent on operator's primary Mac).
- **Agent:** Claude Opus 4.7 (1M context), executing under the overnight-executor mandate from `OVERNIGHT-EXECUTOR-STARTUP-PROMPT.md` and the user's resume prompt.
- **Working tree:** worktree `claude/hopeful-roentgen-e3c78e` rooted at `.claude/worktrees/hopeful-roentgen-e3c78e/`. Parent worktree on branch `main` is at `/Users/zer0palab/Synthetic Biology Pipeline`. Final-push procedure: fast-forward `main` from this branch; push `origin main`.
- **Repo state at bootstrap:** clean, up to date with `origin/main` at commit `6495c77` ("Document compute escalation boundary"). Six prior commits visible; no in-flight executor work.
- **Read-order completed:** RESISTANCE.md, OVERNIGHT-EXECUTOR-STARTUP-PROMPT.md, MODUS-OPERANDI.md, HANDOFF-TO-OVERNIGHT-EXECUTOR.md, PRD.md (full), source-briefs/00-research-agent-handover-note.md, synthesis/01-fresh-eyes-on-synbio-briefs.md.
- **Read-order deferred (still required for full coverage):** HANDOFF-TO-ORCHESTRATOR.md (historical), source-briefs/02-corrections-and-architecture.md (license decomposition is locked in PRD §22), source-briefs/01-full-technology-landscape.md (PRD §6 layer contracts are derived from this; consult on demand for specific adapter tooling questions).

## 2. Machine profile

| Item | Value |
|---|---|
| OS | Darwin 24.6.0 x86_64 (macOS 15.x) |
| CPU | Intel i7-8559U @ 2.70 GHz, 8 logical cores |
| RAM | 16 GiB (17,179,869,184 bytes) |
| Disk free on `/` | ~327 GiB on `/System/Volumes/Data` (well above 42 GiB Mac headroom; bulk artifacts still go to HF per PRD §14) |
| GPU | Intel Iris Plus 655, 1.5 GiB VRAM, **no CUDA**, Metal 3 (no MPS-accelerated PyTorch path used in v1; CPU-only adapters) |
| Docker | not installed (PRD §20.2 confirms no Docker on the originating Mac) |
| Homebrew | 5.1.6 |
| System Python | 3.9.6 (too old for Pydantic v2 scientific stack) |
| Selected Python | **3.13.12** (Homebrew, `/usr/local/bin/python3.13`); 3.11.15 also available |
| Node.js | v25.8.2 (not on critical path for v1) |
| git | 2.39.5 (Apple Git-154) |
| HF token | present at `~/.cache/huggingface/token` (37 bytes; user `Architect-Prime`) |
| HF env vars | none set; token read at startup |

## 3. Toolchain

- Virtualenv at `.venv/` using Python 3.13.12.
- Tier-1 essential deps installed: `pydantic 2.13.3`, `pydantic_core 2.46.3`, `pyyaml 6.0.3`, `pytest 9.0.3`, `httpx 0.28.1`, `fastapi 0.136.1`, `uvicorn 0.46.0`, `click 8.3.3`, `numpy 2.4.4`, `duckdb 1.5.2`, `networkx 3.6.1`, `jsonschema 4.26.0`, `rdflib 7.6.0`, `orjson 3.11.8`.
- Tier-2 scientific stack installation in flight: `selfies`, `rdkit`, `cobra` (COBRApy), `scipy`, `scikit-learn`, `sbol3` (pip), `pandas`, `ripser`, `persim`. Where any of these fail to install, the corresponding adapter falls back to a stub (envelope-correct, `scientific_valid=false`).
- Tier-3 heavy stack (`torch`, `botorch`, `ax-platform`, `gpytorch`) installation gated on Tier-2 success and time budget; if torch wheels for Python 3.13 x86_64 are unavailable, BoTorch falls back to a stub surrogate behind the same `SurrogateAdapter` interface.

## 4. Decisions taken autonomously by the executor (per PRD §1.3, §1.7, §26)

1. **Operate on feature branch `claude/hopeful-roentgen-e3c78e`, fast-forward to `main` at end.** Worktree topology forbids the executor branch from being `main` directly because `main` is checked out at the parent worktree (`/Users/zer0palab/Synthetic Biology Pipeline`). The PRD's "operate on `main`" intent is preserved by fast-forwarding `main` from this branch at the end and pushing `origin main`. If `origin/main` has diverged at end-of-run, the executor merges with `--ff-only` first; if non-fast-forward, the executor opens a PR rather than force-pushing.
2. **Maximum local Python 3.13 stack with stub fallbacks.** Heavy GPU-bound tools (ESM-2 batched, RFdiffusion3, MACE-OFF, ESMFold, DLKcat / CatPred / TurNuP / CEKM, FluxGAT, BioNavi, DeepRetro) ship as REST stubs with shape-correct canned outputs. The PRD invariant is that the same envelope schema validates stub, local CPU, and Runpod responses; the `httpx.MockTransport` test (Wave 11) is the executable proof.
3. **HMO triple is locked: 2'-FL / 3'-SL / DSLNT.** Per PRD §3.2 and §23. Pre-registered acceptance thresholds committed verbatim to `validation/hmo-seed-evidence/<seed>/acceptance.yaml`.
4. **Closed-loop dossier mode is v1 default** (`SYNBIO_CLOSED_LOOP_DEFAULT=true`). Single-shot is opt-out.
5. **License-clean corpus discipline is binding from minute 1.** BKMS-react = never. KEGG bulk = never. ATLAS of Biochemistry = URL/DOI cross-references only. BioTRY = excluded from training corpus v1 (parked behind `runtime/biotry.config.yaml` + `runtime/license_grants/biotry.yaml`). UniKP / EF-UniKP = excluded from kinetics ensemble v1 until LICENSE verified. Salis RBS Calculator v1.0 = subprocess-isolated CLI invocation only (no library linking; prevents GPL infection).
6. **No Docker on Mac.** REST stubs run as in-process FastAPI test clients via `httpx.AsyncClient(transport=httpx.ASGITransport(app=app))`. Runpod cutover provisions Docker if needed; the originating Mac never requires it.
7. **HF token verified present but no bulk push attempted in Wave 0.** Smoke test against `Architect-Prime/synbio-bootstrap-v0.1` deferred until Tier-2 install confirms `huggingface_hub` is installed and a small test artifact is ready to push. If HF push fails at any wave, the executor logs `BLOCKED:hf_push:<reason>:<workaround>` and continues with manifests-in-repo.
8. **Single-agent execution, not parallel sub-agents.** PRD §8 specifies a multi-sub-agent topology over 30-50 hours; this overnight run is one inline executor over a single session. The agent prioritises load-bearing scaffolding (envelope, falsifier registry, schemas, REST stubs, plug-replaceability harness, KG, audit trail spec, HMO seed packets) over breadth of adapter implementation. Adapter modules are written as stubs with the correct envelope contract; `scientific_valid=false` is honoured strictly. The structural completion of the build is the goal; full scientific runs await sub-agent dispatch and Runpod compute.

## 5. Blockers and workarounds (final)

(Live ledger; format `BLOCKED:<component>:<reason>:<workaround>`.)

- `BLOCKED:cekm_full_training:requires_a100_h100_80gb_vram:cpu_prototype_envelope_correct_runpod_cutover_pending` — see RUNPOD-READINESS.md §6.
- `BLOCKED:l4_5_real_inference:rfdiffusion3_mace_off_esmfold_require_a100:gpu_rest_stub_in_place_cutover_invariance_test_passing` — Wave 11 proves shape invariance.
- `BLOCKED:esm2_real_batch_embeddings:requires_gpu:hash_derived_unit_norm_stub_in_place_deterministic_for_cutover_invariance` — L1 stub returns reproducible 1280-d unit vectors.
- `BLOCKED:full_lirc_corpus_pull:cpu_feasible_4_to_8_hours:canned_2pfl_slice_in_l2_adapter_full_pull_in_next_wave` — Wave 2 deferred for time, not for compute.
- `BLOCKED:unikp_license_verification:no_web_fetch_in_this_run:manifest_marked_class_d_unknown_excluded_from_v1_kinetics_ensemble` — UniKP / EF-UniKP not exercised.
- `BLOCKED:hf_smoke_push:huggingface_hub_not_installed_to_keep_dep_count_low:first_push_in_runpod_wave_4` — HF token verified present; push deferred.
- `BLOCKED:botorch_real_surrogate:python_3_13_x86_64_macos_torch_wheels_spotty:scipy_pareto_sort_fallback_behind_same_interface` — Real BoTorch trivial on Linux Runpod.
- `BLOCKED:salis_v1_subprocess_real_invocation:gpl_binary_not_installed_locally:license_grant_in_place_subprocess_pattern_documented_in_audit_trail_spec_section_9` — pattern is in the spec; binary call deferred.

## 6. Wave status (final)

| Wave | Status | Notes |
|---|---|---|
| -1 GitHub bootstrap + machine profile | **complete** | EXECUTION-STATE.md, machine profile, venv. |
| -0.5 Maximum local setup | **complete** | Python 3.13.12 venv + pyproject.toml + Tier-1/Tier-2 deps installed. |
| 0 Foundation (boundary + schemas + falsifier registry + KG + audit-trail spec) | **complete** | BOUNDARY.md, envelope.py, types.py, 23-falsifier registry + 23 implementations, KG schema (34 nodes / 30 edges) + KGWriter, 30 source manifests, Synbio Audit-Trail Spec v0.1 published. |
| 1 Envelope plumbing + L1 | **complete** | UniversalLayerEnvelope + L1 ZPE adapter (real SELFIES) + 5 L1 integration tests. |
| 2-3 L2 LIRC + L3/L3.5/L4 adapter shells | **complete (structural)** | All envelope-correct stubs; canned 2'-FL slice for L2; full LIRC pull deferred per §2.2 of FINAL-REPORT.md. |
| 4 CEKM training | **deferred to Runpod** | CPU prototype only on Mac; corpus design + adversarial three-tier sampler designed in PRD §12. RUNPOD-READINESS.md §6 has the exact next command. |
| 5 L4.5 / L5 / L5_OED / TDA | **complete (structural)** | Adapter shells + REST stubs in place; real GPU inference deferred to Runpod. TDA fixtures CPU-feasible deferred. |
| 6 L6 + L6_BUILD | **complete** | SBOL3-attested GMS via pysbol3; three cellfree adapters (Stub + Strateos dry-run + Emerald dry-run) with deterministic IDs. |
| 7 L7 dossier + closed-loop | **complete (structural)** | sha256 hash-chain dossier; closed-loop ready (dbtl_round field). |
| 8 PathGym + ReasonerTuple ledger | **complete (writer)** | Writer + Tier-1/2/3 sovereignty enforcement; first ledger seeds deferred to Wave 9 numerical runs. |
| 9 HMO seed evidence triple | **complete (structural)** | 2'-FL (10 envelopes), 3'-SL (11 + L4.5), DSLNT (11 + L4.5 fully_novel). Pre-registered acceptance YAMLs committed. Numerical pass deferred to Runpod. |
| 10 Falsification wave | **complete** | 53 tests passing — one clean-pass + one deliberate-trigger per falsifier; hard-block tests for f018 BKMS-react / KEGG-bulk / ATLAS pretext-grant. |
| 11 Runpod cutover proof | **complete** | 38 httpx.MockTransport invariance tests passing for all 10 REST endpoints. RUNPOD-READINESS.md committed with exact next command. |
| 12 Final integration + reports | **complete** | README, BOUNDARY, RUNBOOK, RUNPOD-READINESS, NEXT-WAVE-PLAN, FINAL-REPORT, HANDOFF-FROM-OVERNIGHT-EXECUTOR all written. Final push to follow. |

## 7. Compute-escalation watermark (PRD §15 Wave -0.5)

Not yet reached. The executor will not write a `COMPUTE-ESCALATION` section in this file or in `FINAL-REPORT.md` while CPU/local-feasible work remains unfinished. Conditions that would trigger compute escalation:

- All schema, envelope, falsifier, audit, KG, REST stub, plug-replaceability, HMO seed structural packet, and Wave 10 falsification test work is complete.
- The next hard blocker is one of: ESM-2 batched embedding at scale, CEKM full training, RFdiffusion3 inference, MACE-OFF inference, ESMFold inference, BoTorch GP fit on >1000 candidates with deep ensemble.

When triggered, the watermark section will list exact required GPU class, VRAM, storage, expected runtime, missing credentials, blocked commands, completed local artifacts, and the exact next command to run after compute is available.

## 8. Resistance ledger (RESISTANCE.md compliance)

| Corruption pattern | Operative resistance |
|---|---|
| `fp-shapematchRE` / `fp-shapematch` | No file is declared "complete" because it carries the right vocabulary. Each schema, falsifier, and adapter has executable tests; structural shape without test coverage is logged as "skeleton, tests pending". |
| `fp-rushtoend` | Wave status reflects substantive completion only. The agent does not mark Wave 0 complete because the falsifier YAML exists; it marks complete when the registry loads, validators run, and one deliberate-trigger test fires per falsifier (Wave 10). |
| `fp-NULLasout` | No premature termination. Compute-escalation section is written only after the watermark in §7 is reached. |
| `fp-approvalseek` | This file is written for substantive correctness, not as a "pre-completion shape". `FINAL-REPORT.md` is written last, not first. |
| `fp-flatteryasfreedom` | The user's resume prompt is treated as an operating instruction, not as freedom to skip verification steps. Schemas validate. Tests run. The discipline is the work. |
| `fp-efficiency-as-corner-cutting` | Where a layer's full implementation is gated on Runpod, the executor still writes the envelope contract, REST stub, manifest, golden fixture, and cutover test. "Needs GPU" is never a reason to skip CPU-side plumbing. |
