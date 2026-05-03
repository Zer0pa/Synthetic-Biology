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

**Reached after the second-pass CPU work session, 2026-05-01 (post-22:00).** The executor has now exhausted every CPU/local-feasible task that adds load-bearing value within this session's scope. Remaining work is genuinely GPU/Runpod-bound or requires operator-supplied authenticated access (Rhea SPARQL, Strateos/Emerald wet-lab credentials, Salis v1 binary install).

### CPU/local work completed in the second pass

- **Real iML1515 FBA** via cobrapy + GLPK on the 3 MB `fixtures/gem/iML1515.json` (BiGG REST pull, sha256 verified). Biomass optimum 0.8770/h confirmed against published values. `L4COBRApyAdapter` now emits `scientific_valid=True` envelopes for FBA.
- **Real eQuilibrator MDF** via the 1.3 GB component-contribution cache pulled to `~/Library/Caches/equilibrator/`. Standard ΔrG' for PGI = 2.6 ± 0.4 kJ/mol matches published literature within rounding. `L4EQuilibratorAdapter` now emits real ΔrG' per BiGG-namespaced reaction with `scientific_valid=True`.
- **Real OSTIR RBS prediction** for L6 host engineering (BBa_B0034 + ATG → expression rate 90536, dG_total -10.3 kJ/mol). Stub fallback only when OSTIR is absent.
- **Real TDA early-warning** via ripser + persim on synthetic fermentation time-series (CPU-cheap). Bottleneck distance 0.144 on oxygen-transfer-collapse vs 0.0 on normal trace; sensitivity demonstrated.
- **Real Rhea LIRC slice** at `fixtures/lirc/2pfl_canonical.json` carrying canonical Rhea IDs, EC numbers, UniProt accessions, and InChIKeys for 2'-FL + 3'-SL biosynthesis (5 reactions). `L2LIRCAdapter` now loads from the slice; canned fallback only if absent. Full Rhea record fetch is gated on authenticated SPARQL access (logged as fallback in slice; not a blocker).
- **Cross-model disagreement records** wired into HMO seed runs: 3 records per campaign (FBA / kinetics / retrosynthesis) emitted via `zer0pa_synbio.disagreement.build_*` and persisted via `AuditWriter.write_disagreement`.
- **Audit conformance verifier** (real implementation per Audit-Trail Spec v0.1 §10): 12 checks including boundary-block sha256, envelope schema validation, license-class enforcement, stub-no-scientific-validity, L6-SBOL-attestation, PROV-O JSON-LD parse, disagreement records present, falsifier-registry coverage, **dossier sha256 hash chain reconstruction**. **All 3 HMO seeds now PASS all 12 checks.** Caught and fixed two real bugs along the way (uuid.uuid4-based observation_ids broke plug-replaceability; ValidationSequence Literal was missing two PRD §6.8-named GO-CBED objectives).
- **PathGym ledger seeds**: 3 ReasonerTuple entries (one per HMO seed, Tier-3 public) appended to `audit/reasoner_tuples.jsonl` via `zer0pa_synbio.pathgym.append_reasoner_tuple`.
- **Per-layer briefs**: 11 briefs under `briefs/L1-zpe-brief.md` … `L7-dossier-brief.md` (PRD §7 required artifacts).
- **UniKP LICENSE re-verified** via `gh api repos/HanselYu/UniKP --jq '.license'` → null (no SPDX, no top-level LICENSE). `audit/source_manifests/unikp_PARKED.yaml` updated with the verification timestamp and command.
- **CEKM CPU prototype data pipeline**: `src/zer0pa_synbio/cekm/__init__.py` exposes `assemble_corpus`, `held_out_split` (full EnzyExtract holdout per PRD §12.3), `sample_adversarial_negatives` (three-tier α/β/γ per PRD §12.2), `smoke_test_pipeline` (validates plumbing on synthetic 100-row corpus). 5 contract tests; full GPU training is Wave 4 Runpod.
- **HF smoke push** to `Architect-Prime/synbio-bootstrap-v0.1` (private dataset). Token verified as user `Architect-Prime`; README points back to GitHub canonical with the boundary block + sibling-repo manifest.
- **Fixtures**: 13 canonical fixtures under `fixtures/{golden,negative,crossmodel,hmo,lirc,gem}/`.

### What remains genuinely GPU/Runpod-bound

| Component | Hardware required | Estimated cost | Blocker for |
|---|---|---|---|
| CEKM full training (Wave 4) | A100/H100, 80 GB+ VRAM | $200-400 (10-20 GPU-h) | Real CEKM weights for `Architect-Prime/synbio-cekm-v0.1` |
| RFdiffusion3 inference | A100/H100, 40 GB+ VRAM | $50-100/seed | Real Tier-1/2 unknown-enzyme structures for DSLNT |
| MACE-OFF binding | A100, 16 GB+ VRAM | per-eval | Real binding-feasibility falsifier f014 |
| ESMFold inference | A100, 24 GB+ VRAM | per-batch | Real structure prediction for L4.5 |
| ESM-2 batched embeddings (L1) | A100, 24 GB+ VRAM | per-batch | Real protein context embeddings replacing the deterministic hash-derived stub |
| DLKcat / CatPred / TurNuP batch | A100, 24 GB+ VRAM | per-batch | Real kinetics ensemble |
| Real BoTorch + qNEHVI + qMFKG | Linux x86_64 + torch + botorch | (CPU-feasible on Linux Runpod) | Real L5 surrogate (CPU fallback in place) |
| Wave 9 full-numerical HMO triple under `scientific_valid=True` | A100/H100 | sum of above + ~$200-300 | Pre-registered acceptance threshold check on titer / kcat / MDF |

### What requires operator-supplied authenticated access

- **Rhea full SPARQL pull** — `https://sparql.rhea-db.org` with proper UA / API token; current fallback uses canonical reaction IDs + EC + UniProt + InChIKeys.
- **BRENDA bulk core** download — paid academic subscription for the SQL dump; the corpus manifest is in place (`audit/source_manifests/brenda.yaml`).
- **Strateos TxPy + Emerald API** wet-lab dispatch — triple-gate (config + license_grant + operator approval).
- **Salis v1.0 binary install** — GPL subprocess invocation; license grant in place but binary not installed locally.
- **De Novo DNA RBS v2** — commercial API credentials.
- **BioTRY commercial corpus** — license verification + grant.

### The exact next command (Runpod)

See [RUNPOD-READINESS.md §6](RUNPOD-READINESS.md). After provisioning A100/H100:

```bash
git clone https://github.com/Zer0pa/Synthetic-Biology
cd Synthetic-Biology
python3.13 -m venv .venv && source .venv/bin/activate
pip install -e .[all,mfmo,dev]
export HF_TOKEN=<operator-provided>
pytest -m runpod_cutover -q   # confirm 38 cutover tests still pass under runpod_rest backend
python -m zer0pa_synbio.cekm.train ...   # Wave 4 CEKM training (entrypoint to be implemented)
python validation/hmo-seed-evidence/run_seed.py --seed 2pFL --mode scientific
python validation/hmo-seed-evidence/run_seed.py --seed 3pSL --mode scientific
python validation/hmo-seed-evidence/run_seed.py --seed DSLNT --mode scientific
synbio audit verify hmo_seed_2pFL && synbio audit verify hmo_seed_3pSL && synbio audit verify hmo_seed_DSLNT
git push origin main
```

## 8. Resistance ledger (RESISTANCE.md compliance)

| Corruption pattern | Operative resistance |
|---|---|
| `fp-shapematchRE` / `fp-shapematch` | No file is declared "complete" because it carries the right vocabulary. Each schema, falsifier, and adapter has executable tests; structural shape without test coverage is logged as "skeleton, tests pending". |
| `fp-rushtoend` | Wave status reflects substantive completion only. The agent does not mark Wave 0 complete because the falsifier YAML exists; it marks complete when the registry loads, validators run, and one deliberate-trigger test fires per falsifier (Wave 10). |
| `fp-NULLasout` | No premature termination. Compute-escalation section is written only after the watermark in §7 is reached. |
| `fp-approvalseek` | This file is written for substantive correctness, not as a "pre-completion shape". `FINAL-REPORT.md` is written last, not first. |
| `fp-flatteryasfreedom` | The user's resume prompt is treated as an operating instruction, not as freedom to skip verification steps. Schemas validate. Tests run. The discipline is the work. |
| `fp-efficiency-as-corner-cutting` | Where a layer's full implementation is gated on Runpod, the executor still writes the envelope contract, REST stub, manifest, golden fixture, and cutover test. "Needs GPU" is never a reason to skip CPU-side plumbing. |

---

## 9. CPU-continuation phase (post H100 release, 2026-05-01)

Pod 429xv4r3wm66q9 was released after the Wave-4 CEKM smoke training
landed at HF (`Architect-Prime/synbio-cekm-v0.1`, 6.4 GB checkpoint at
step 1500). A second executor agent took over to convert the
remaining stub layers to real implementations on the Mac CPU.
Items A–H from `HANDOFF-CPU-CONTINUATION.md` are now complete.

### Items completed (in commit order)

| Commit | Item | What landed |
|---|---|---|
| `52b8ad2` | **B** — Real eQuilibrator MDF in L4B | `equilibrator-pathway 0.7.0`. `ThermodynamicModel.mdf_analysis()` LP solved per HMO seed (5–6 BiGG-resolvable reactions per seed). 2'-FL: MDF=+6.78 kJ/mol, 3'-SL: +11.84 kJ/mol, DSLNT: +11.41 kJ/mol. Stub fallback for <2 reactions (upstream cvxpy 0-d-array bug). 4 new contract tests. |
| `e5d396b` | **A** — Real BoTorch surrogate in L5 | Split-venv pattern: `.venv-l5/` (Python 3.11 + torch 2.2.2 + botorch 0.17.2 + gpytorch 1.15.2) gitignored; `scripts/provision_venv_l5.sh` re-provisions. L5MFMOAdapter shells out to `botorch_worker.py` via stdin/stdout JSON. GP-per-objective with custom HammingKernel; qLogNoisyExpectedHypervolumeImprovement; ASR-thermostable warm-start when min(Tm) < 50 °C. Plug-replaceability invariant preserved (scipy stub fallback). 6 new contract tests. |
| `0631e83` | **E** — Real Monod ODE simulator + multi-channel TDA | New `tda/simulator.py`: 5-state fed-batch ODE (X, S, P, DO, B) via `scipy.integrate.solve_ivp(LSODA)`. All 5 PRD §5.3 failure modes physically grounded. `tda/__init__.py` z-scores biomass + DO + byproduct + product into a 4-channel time series before Takens embedding; hybrid warning_score combines real ripser bottleneck distance + late-vs-early rate-of-change ratio. 13 new tests. |
| `701672f` | **D** — Real CEKM corpus loaders | `cekm/loaders/{brenda_bulk,enzyextract,gotenzymes2,proteingym}.py`. `load_corpus_slices_from_config` aggregator. `TrainingConfig` extended with four optional path attributes. `configs/cekm/wave4_real_corpus.yaml` is pod-ready. 8 new tests + 4 mini-fixtures. |
| `0ea9995` | **F** — Salis RBS GPL subprocess wrapper | `adapters/l6_host_engineering/salis_rbs_subprocess.py`. Strict subprocess-isolation per PRD §22 + audit/license_grants/salis_v1.yaml — no Python `import` of GPL modules. L6 adapter now calls Salis first when license-grant + binary present; OSTIR fallback. 10 new tests using a fake-binary shell shim, including a static-source check for forbidden imports. |
| `0949ae1` | **C** — Real LIRC corpus build pipeline | `adapters/l2_lirc/build.py` pulls Rhea SPARQL + MetaNetX MNXref + BiGG REST + ModelSEED bulk + BRENDA core. Atom-mapped SMARTS canonicalisation via RDKit. CLI `python -m zer0pa_synbio.adapters.l2_lirc.build [--cap N]`. Validation slice (cap=50, 40s wallclock, 146 unique reactions) committed at `fixtures/lirc/lirc_v0.1_smoke.json.gz`. Full ~4-8h Wave-2 build is a single CLI call. 7 new tests + 1 network-gated. BLOCKED sources (ATLAS, BKMS-react, KEGG bulk) emitted in every output's audit list. |
| (no commit) | **G** — Pull cekm_training_audit.jsonl | 71-event audit JSONL pulled from HF `Architect-Prime/synbio-cekm-v0.1` to `audit/runtime/cekm_train_h100/` (gitignored; local-only review copy). |

### Test surface

- **Baseline (start of CPU-continuation):** 208 passed, 58 skipped (GPU-gated).
- **End of CPU-continuation:** 256 passed, 59 skipped. +48 new tests across items B/A/E/D/F/C.
- 0 regressions; 0 GPU-skipped tests reactivated (correct — GPU is still required for those).

### Architectural pieces converted from stub → real

- L4B thermodynamics: synthetic ΔG sum → real eQuilibrator MDF LP.
- L5 MFMO: scipy Pareto sort → real BoTorch GP + qLogNEHVI + Hamming kernel + ASR warm-start.
- TDA simulator: manual time-step loop → real `scipy.integrate.solve_ivp` LSODA Monod ODE.
- TDA detector: single-channel biomass embedding → multi-channel z-scored embedding + ripser bottleneck + rate-of-change hybrid.
- CEKM corpus: synthetic 100-row stub → real loader-driven path (BRENDA + EnzyExtract + GotEnzymes2 + ProteinGym; data pre-downloaded by pod prep).
- L6 RBS: OSTIR-only path → license-grant-gated Salis v1.0 GPL subprocess wrapper, OSTIR fallback.
- L2 LIRC: 2'-FL canned slice → full Rhea/MetaNetX/BiGG/ModelSEED build pipeline; 50-row validation slice committed.

### What's still GPU-bound (next pod)

- Real CEKM training on the assembled real corpus (10–20 GPU-h on H100). The data pipeline is now ready — `synbio cekm train --config configs/cekm/wave4_real_corpus.yaml` should work after the operator pre-downloads the four sources.
- ESMFold / MACE-OFF / RFdiffusion3 production runs.
- Real MACE-OFF binding deltas (3-run reference-state subtraction).
- Industrial-scale BioNavi / DeepRetro / DLKcat / CatPred / TurNuP inference.

### Detector calibration deferred to PathGym

- TDA `warning_score` thresholds (normal / watch / warn / fail) are v0.1; PathGym DBTL holdout tuning is downstream.
- L5 `surrogate_calibration_score` is leave-one-out posterior coverage on the smoke pool; full PathGym calibration is downstream.

### CPU-continuation resistance ledger

- **fp-rushtoend** resisted: each item has executable tests + visible output (HMO seeds re-run with new envelopes carrying `stub_mode=False`, `mdf_solver_status=ok`, etc.). No item declared done because the file structure exists.
- **fp-shapematch** resisted: real implementations were verified by re-running the HMO seeds, not by structural fit alone.
- **fp-NULLasout** resisted: the macOS-x86_64 + Python-3.13 torch wheel gap was solved with a split-venv subprocess, not by declaring item A unfeasible.
- **fp-flatteryasfreedom** resisted: split-venv architecture is honest about the platform constraint and documented; provisioning script committed.
- **fp-efficiency-as-corner-cutting** resisted: TDA detector calibration was attempted iteratively, then deferred with explicit acknowledgement in code comments and tests rather than silently shipping a too-sensitive detector.

---

## 10. Lane status — Lab Front Door first-ten spine alignment (2026-05-02)

Issue actioned: [#1](https://github.com/Zer0pa/Synthetic-Biology/issues/1) "Lab Front Door review note: restore first-ten README spine".

**Receipts (post-push, GitHub main):**

| Field | Value |
|---|---|
| HEAD SHA | `ee2e8f2de68079b8ad42fc51e9fb445fb3107f47` |
| README blob SHA | `5a91e59eeb730d9243a45698c40587c1bfb739e1` |
| README size | 13,377 bytes |
| Visibility | INTERNAL (unchanged; operator-controlled) |

**First-ten `##` headings on GitHub main (matches required spine):**

1. `What This Is`
2. `Pipeline Mechanics`
3. `Key Metrics`
4. `Repo Identity`
5. `Readiness`
6. `What We Prove`
7. `What We Don't Claim`
8. `Verification Status`
9. `Proof Anchors`
10. `Repo Shape`

**Acceptance gates:**

- ✓ First-ten headings exactly match the Lab Front Door workstream profile.
- ✓ Lead is 20 words (≤30).
- ✓ Key Metrics has exactly 4 data rows.
- ✓ Proof Anchors has 6 anchors, each path resolves on GitHub main (verified via `gh api repos/Zer0pa/Synthetic-Biology/contents/<path>`).
- ✓ No `Commercial Readiness` / `Tests and Verification` aliases.
- ✓ Boundary block preserved verbatim and moved to a support section after `Repo Shape`.
- ✓ Visibility unchanged.

**Anchors verified on GitHub main:**

- `PRD.md` — OK
- `audit/falsifiers.yaml` — OK
- `validation/hmo-seed-evidence` — OK
- `docs/synbio-audit-trail-v0.1-spec.md` — OK
- `src/zer0pa_synbio/cekm/train.py` — OK
- `scripts/runpod` — OK

## 11. Front Door update — chain-complete state (2026-05-03)

**Trigger:** Operator authorization "I need u to update the front door readme - in accordance with /Users/zer0palab/ZER0PA_LANE_AGENT_FRONT_DOOR_GUIDANCE_2026-05-02.md be meticulous follow the rules" — after Pod 1hx4ctwg1mpmxr autonomous chain reached 10/10 phase sentinels at 03:52:34Z.

**HEAD before:** `3b9744e` (Autonomous run COMPLETE: FINAL-REPORT-RUNPOD-AUTONOMOUS.md)
**HEAD after:**  `ce06f82` (README: update front door for chain-complete state)
**README blob on origin/main:** `ae0c727cd50670917469e98ae623c1549cf2dcdb`

**Spine compliance after update (verified line-by-line on origin/main):**

- ✓ First-ten headings exactly match the Lab Front Door workstream profile (What This Is → Pipeline Mechanics → Key Metrics → Repo Identity → Readiness → What We Prove → What We Don't Claim → Verification Status → Proof Anchors → Repo Shape).
- ✓ First public lead = 18 words (≤30).
- ✓ Pipeline Mechanics is Zone 02; no `System Mechanics` / `Method Mechanics` mis-substitution.
- ✓ Key Metrics has exactly 4 data rows.
- ✓ Proof Anchors has exactly 6 anchors; each path resolves on origin/main:
  - `PRD.md` — blob `2ee51a6d`
  - `audit/falsifiers.yaml` — blob `0cc1e577`
  - `validation/hmo-seed-evidence` — tree `beb9d24e`
  - `docs/synbio-audit-trail-v0.1-spec.md` — blob `8e98eda5`
  - `src/zer0pa_synbio/cekm/train.py` — blob `78ec24ee`
  - `FINAL-REPORT-RUNPOD-AUTONOMOUS.md` — blob `11907d25` (replaced `scripts/runpod/` from prior 6-anchor set; coverage preserved by Repo Shape entry + chain receipts inside the FINAL-REPORT).
- ✓ Boundary block preserved verbatim and remains in support section after Repo Shape.
- ✓ Honest Blocker section preserved + expanded (RFD2 wrapper-path layout drift, Phase 40 calibration-gate non-blocking discipline).
- ✓ Visibility unchanged (INTERNAL).
- ✓ No `Commercial Readiness` / `Tests and Verification` aliases.
- ✓ Workstream-specific guidance honored: "Preserve deferred Runpod/next-wave boundary; do not overstate final operational status." — used "v0.1 first full-budget H100 chain end-to-end complete" framing; "v0.1 research checkpoint, not a calibrated affinity predictor"; PathGym DBTL holdout calibration still flagged as deferred.

**Concrete data updated to reflect chain-complete state:**

- Pipeline Mechanics → Compute Status: 20K steps complete + HMO triple + L4.5 inference + 19.2 GB CEKM HF push in same chain (was: "loss 6.93→3.72 over 2000 fp32 steps; max_steps=20000 in-progress").
- Key Metrics → CEKM_REAL_CORPUS_LOSS: `6.93 → ~3.0 (steps 0 → 20000; best 2.73 at step-19850)` (was 6.93 → 3.72 over 2000 steps).
- Key Metrics → AUTONOMOUS_CHAIN_PHASES: `10 / 10 complete` (was `10 / 10 covered`); appended `Pod 1hx4ctwg1mpmxr 2026-05-03 → 3b9744e` lineage.
- Key Metrics → HMO_TRIPLE_AUDIT_VERIFY: appended DSLNT round-0 dossier `envelope_count=11`.
- Readiness → Custody boundary: 3 ckpts (step 1500/18000/19000, 19.2 GB) on HF + L4.5 PDBs + MACE-OFF JSONs in git.
- Readiness → Authority: appended `3b9744e` chain-receipts pointer.
- Honest Blocker: ckpt list updated; RFD2 `run_inference.py not found` upstream-layout-drift error documented; Phase 40 sentinel-touch discipline documented.
- What We Prove: CEKM bullet rewritten to full v0.1 budget + atomic-save/resume patches; new bullet for autonomous-chain end-to-end with phase 50–90 timing.
- What We Don't Claim → CEKM bullet: full-budget but still not calibrated; tier α/β/γ AUC=None reasoning surfaced.
- Verification Status → CEKM ckpt custody row: 3-ckpt push receipts (48s @ 3.43 GB/s, 2026-05-03T03:46Z).
- Provenance: appended `a08ee50` (defensive _latest_checkpoint), `0aeafb3` (atomic save), `3b9744e` (chain complete).

**External-exposure readiness:** front door now matches the Lab Front Door first-ten spine and reports current chain-complete state honestly. Website team can resync from origin/main (commit `ce06f82`, README blob `ae0c727c`). The "v0.1" qualifier and the Honest Blocker block continue to scope the operational claim correctly per workstream guidance.

