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
