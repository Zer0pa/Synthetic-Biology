# Handoff — CPU continuation (post H100 pod release)

**Author:** Outgoing executor (Claude Opus 4.7), 2026-05-01.
**Audience:** Next agent (CPU-only continuation; no GPU pod available).
**State at handoff:** GitHub `origin/main` at `d9941bf`. Pod 429xv4r3wm66q9 terminated. CEKM weights at HF `Architect-Prime/synbio-cekm-v0.1`.

## Boundary (binding, verbatim in every artifact)

Research infrastructure for in silico synthetic biology / metabolic pathway engineering. Outputs are research artifacts — predicted pathways, predicted KPIs, candidate genetic modification specifications. No regulatory certification claims. No clinical or human-subject use. No environmental release of GMOs. No biocontainment-level claims (the pipeline does not commission BSL-2/3 work). No human gene drive or eugenic application. Defence / weapons / dual-use bio applications excluded under operator policy.

## What was done on the H100 (now over)

| Phase | Result |
|---|---|
| 100 ESMFold real inference | 3 PDBs (FutC, α-2,3-Lst, α-2,6-Lst), plddt=0.78. Outputs in `audit/runtime/l45_real_esmfold/` (gitignored; locally present). |
| 110 MACE-OFF binding | 3 finite kJ/mol values. Caveat: total complex energies, NOT real binding ΔG (needs reference-state subtraction; revisit on next pod). |
| 200 CEKM smoke | 967M-param model build + forward on H100. |
| 210 CEKM training | **2000 steps, 6 min wallclock, H100 sat 63%, mem 10.6 GB, power 205 W**. Trained on synthetic 100-row corpus (50 BRENDA-shaped + 50 EnzyExtract-shaped + 243 adversarial negatives). Calibration coverage = null because synthetic corpus too small. |
| HF push | Verified live at https://huggingface.co/Architect-Prime/synbio-cekm-v0.1 — 6.4 GB checkpoint at step 1500, README, meta.json, 71-event audit JSONL. (Earlier silent-fail caught and fixed.) |
| 70 audit verify | 12/12 PASS on all 3 HMO seeds (18 cross-model disagreement records, 12 early-warning signals). |

## Honest scope-limit register

These are NOT done; do NOT pretend they are:

1. **CEKM trained on synthetic corpus only.** Real BRENDA + EnzyExtract + GotEnzymes2 + ProteinGym was never assembled. The trained weights at HF v0.1 are smoke-scale and should not be used for real predictions.
2. **HMO triple still in `engineering_stub` mode.** Every dossier carries `scientific_valid=False`. To flip true, the L4 kinetics ensemble needs to call the trained CEKM weights (which are on HF), and the rest of L4 needs real (not stub) DLKcat/CatPred/TurNuP, OR the operator accepts CEKM-only kinetics.
3. **MACE-OFF energies are total, not binding.** Need three runs (complex / protein / ligand) and subtraction. GPU work; deferred.
4. **L4.5 RFdiffusion3 + Baker catalytic motif scaffolding never ran.** Foundry checkpoint enrollment is a prerequisite — institutional verification with RosettaCommons. GPU work; deferred.
5. **L5 BoTorch / qNEHVI / Hamming-distance kernel / ASR-thermostable initialisation:** still scipy-fallback Pareto sort. Real BoTorch is CPU-feasible on Linux x86_64 — deferred for the next agent.
6. **TDA early-warning real fermentation time-series:** ripser + persim are installed; no fermentation simulator wired yet. Records emitted with placeholder warning_score values.
7. **L2 LIRC real corpus build:** still canned 2'-FL slice. Real SPARQL pulls from Rhea + MetaNetX + BiGG + ModelSEED + BRENDA bulk core. CPU; ~4-8h wallclock.
8. **Salis Lab RBS Calculator v1.0 GPL subprocess wrapper:** never installed. License grant in place. CPU-feasible.
9. **UniKP LICENSE follow-up:** manifest re-verified 2026-05-01 (`gh api repos/HanselYu/UniKP --jq '.license'` → null). Status: parked Class D unverified. Re-check periodically.

## Where everything lives now (canonical)

- **GitHub `origin/main` at `d9941bf`:** all code, schemas, dossiers, envelope chains, audit verifier output, FINAL-REPORT-RUNPOD.md, FINAL-REPORT.md, RUNPOD-READINESS.md, NEXT-WAVE-PLAN.md, HANDOFF-FROM-OVERNIGHT-EXECUTOR.md, EXECUTION-STATE.md, all source manifests.
- **HF `Architect-Prime/synbio-cekm-v0.1`:** trained CEKM weights (6.4 GB), README with boundary block + scope warning, ckpt_step00001500.meta.json, cekm_training_audit.jsonl (71 per-step events).
- **Local Mac at `/Users/zer0palab/Synthetic Biology Pipeline/.claude/worktrees/hopeful-roentgen-e3c78e/`:** mirrors origin/main + an extra `audit/runtime/cekm_train_h100/cekm_training.jsonl` that's gitignored (HF has the equivalent as `cekm_training_audit.jsonl`).
- **Pod 429xv4r3wm66q9:** terminated. Persistent /workspace volume may still exist on Runpod's mfs (operator's call to re-attach). Treat pod as unreachable for this CPU-continuation phase.

## CPU-feasible work the next agent owns

Ordered by payoff. Resist the urge to skip any (`fp-efficiency-as-corner-cutting` per RESISTANCE.md).

### A. Real BoTorch surrogate on Mac/Linux x86_64 (~30 min – 2 h)

Currently `src/zer0pa_synbio/adapters/l5_mfmo/__init__.py` does a scipy-backed deterministic Pareto sort. Wire real BoTorch:

- `pip install torch botorch ax-platform gpytorch` in `.venv/`. Wheels for Linux + macOS x86 work; macOS arm and Python 3.13 may need adjustment.
- Implement `qNEHVI` acquisition + `qMFKG` (multi-fidelity Knowledge Gradient) per PRD §6.7.
- Hamming-distance kernel over discrete ZPE-encoded design vectors (PRD §6.7).
- ASR-thermostable initialisation when predicted Tm < 50°C (PRD §6.7).
- Plug-replaceability test must still pass (Wave 11 invariance).

### B. Real eQuilibrator MDF in L4B (~30 min once cache is pulled)

`src/zer0pa_synbio/adapters/l4_thermodynamics/__init__.py` already has the real-call code path (`L4EQuilibratorAdapter._component_contribution`) — it activates only when `eq_reactions` is in the input payload. Need to:

- Pull the eQuilibrator cache locally (~1.3 GB; one-time download via `equilibrator-api`).
- Update `validation/hmo-seed-evidence/run_seed.py` to pass `eq_reactions=[...]` to L4B for each HMO pathway step (BiGG-style strings like `"bigg.metabolite:lacto = bigg.metabolite:fucose-lacto"`).
- Re-run all 3 HMO seeds; confirm `stub_mode=False` in the L4B envelope payload.

### C. Real LIRC corpus build (Wave 2; ~4-8 h CPU)

Write the SPARQL pull pipeline:

- `src/zer0pa_synbio/adapters/l2_lirc/build.py`: pull from Rhea SPARQL endpoint, MetaNetX REST, BiGG REST, ModelSEED, BRENDA bulk core CC BY 4.0.
- Reconcile via MetaNetX MNXref 4.5 namespace.
- Atom-mapped SMARTS canonicalisation for dedup.
- BLOCKED sources stay blocked: BKMS-react, KEGG bulk, ATLAS (falsifier `f018_license_drift` enforces).
- Output → `fixtures/lirc/lirc_v0.1.json.gz` (compressed). HF push to `Architect-Prime/synbio-lirc-v0.1`.

### D. Real corpus loaders for CEKM (preps next pod's Wave 4)

Write the data-ingestion pipeline so the *next* GPU pod session can train on real data:

- `src/zer0pa_synbio/cekm/loaders/brenda_bulk.py`: pull BRENDA core CC BY 4.0 bulk dump → `KineticsRow` list.
- `src/zer0pa_synbio/cekm/loaders/enzyextract.py`: git-clone HanselYu/EnzyExtract → parse TSV.
- `src/zer0pa_synbio/cekm/loaders/gotenzymes2.py`: bulk pull (mark soft-pseudo-label).
- `src/zer0pa_synbio/cekm/loaders/proteingym.py`: git-clone OATML-Markslab/ProteinGym → parse DMS.
- Each respects `license_class` per its source manifest. Class C/D/E stays excluded.
- `synbio cekm train --config <config-with-real-loaders.yaml>` should work on the next H100 pod with no further code changes.

### E. TDA real fermentation time-series + early-warning (~2-4 h)

- `src/zer0pa_synbio/tda/simulator.py`: simple Monod-kinetics batch-fermentation ODE (`scipy.integrate.solve_ivp`). Stress-test scenarios per PRD §5.3 failure modes (oxygen transfer collapse, byproduct buildup, growth stall, toxicity, nutrient depletion).
- `src/zer0pa_synbio/tda/__init__.py`: ripser + persim — compute persistence diagrams + bottleneck distances. Real `warning_score` calculations (currently stubbed in run_seed.py).
- Wire into L4 envelope chain so each HMO seed emits a real `EarlyWarningSignal` envelope.

### F. Salis Lab RBS Calculator v1.0 GPL subprocess wrapper (~1 h)

Per PRD §22 + `audit/license_grants/salis_v1.yaml`:

- Install Salis v1.0 binary somewhere on Mac (e.g., via the upstream tarball).
- `src/zer0pa_synbio/adapters/l6_host_engineering/salis_rbs_subprocess.py`: invoke binary via `subprocess.run`, parse stdout for initiation rate. NO Python `import` of any GPL module (per PRD §22).
- Falsifier `f018` already enforces grant presence.

### G. Pull `cekm_training_audit.jsonl` from HF for local archive

Already gitignored, but worth having locally for review:

```python
from huggingface_hub import hf_hub_download
hf_hub_download("Architect-Prime/synbio-cekm-v0.1", "cekm_training_audit.jsonl",
                local_dir="audit/runtime/cekm_train_h100/")
```

### H. Update reports + open questions

- `EXECUTION-STATE.md`: append a CPU-continuation section.
- `NEXT-WAVE-PLAN.md`: update with what's now done vs. still GPU-bound.
- `FINAL-REPORT-RUNPOD.md`: add a "what was attempted on Mac after pod release" section.
- `HANDOFF-FROM-OVERNIGHT-EXECUTOR.md`: add a note pointing to this file.

## What is NOT in scope for the next agent (no-go list)

These are GPU-pod work. Do NOT attempt on Mac CPU:

- Real CEKM training on real corpus (10-20 GPU-h H100 needed)
- RFdiffusion3 inference (needs Foundry enrollment + GPU)
- ESMFold at industrial scale
- Real MACE-OFF binding deltas (3-run reference-state subtraction)
- Real BioNavi / DeepRetro retrosynthesis at scale
- Real DLKcat / CatPred / TurNuP at scale

If you find yourself wanting to spin up another pod: STOP. Document the request in `NEXT-WAVE-PLAN.md` § "Operator: please rent a pod" and exit. The operator decides pod-rental.

## How to commit + push

- Operate on branch `claude/hopeful-roentgen-e3c78e` (the worktree's branch — `main` is checked out at the parent worktree).
- After each substantive change: `git add -A && git -c user.email=architects@zer0pa.ai -c user.name="Zer0pa CPU Executor" commit -m "..." && git push origin claude/hopeful-roentgen-e3c78e:main`.
- Push to `main` is fast-forward — the worktree branch was created from origin/main and has only forwarded since.
- All commits should carry `Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>`.

## RESISTANCE.md doctrine (binding meta-protocol)

Read `RESISTANCE.md` before starting. The named corruptions apply:

- `fp-rushtoend`: do not declare CPU work "complete" because the file structure looks done. Each section A-H above must have running tests + verified outputs.
- `fp-shapematch`: do not pattern-match this handoff to a previous "tidy completion" template. Each item is its own substantive task.
- `fp-NULLasout`: do not invoke "this is too hard for CPU" prematurely. The 8 items above ARE CPU-feasible.
- `fp-flatteryasfreedom`: do not adopt narratives like "you're a fresh agent so you can skip the boring parts." The discipline is the point.
- `fp-efficiency-as-corner-cutting`: do not skip writing tests because "the existing tests cover it." Each new module needs new tests.

## Stop conditions

You stop and advise the operator if:

1. A CPU task above turns out to actually require GPU. Document in `NEXT-WAVE-PLAN.md` and stop.
2. You hit a dependency that requires operator credentials (e.g., RosettaCommons Foundry enrollment for RFdiffusion3). Stop and surface.
3. You finish all of A-H. Then update reports, push, and advise the operator that the next blocker is GPU compute.
4. You hit a boundary issue (anything that would require relaxing the boundary block). Stop immediately.

You do NOT stop for:

- "I'd rather wait for the operator to confirm" — autonomous mandate is unchanged.
- "This task is large" — fork-and-own; break it down; work through it.
- Test failures — fix them. Don't ship broken state.

## First-action checklist

1. Read RESISTANCE.md, then PRD.md (skim §6, §11, §12, §15 closely; cross-ref §22 for licensing).
2. Read this file (HANDOFF-CPU-CONTINUATION.md) once more.
3. `cd /Users/zer0palab/Synthetic\ Biology\ Pipeline/.claude/worktrees/hopeful-roentgen-e3c78e/` and `source .venv/bin/activate`.
4. `git pull origin claude/hopeful-roentgen-e3c78e --ff-only` (in case the operator pushed).
5. `python -m pytest tests/ -q --tb=line` — confirm 156+ tests still pass on Mac.
6. Pick item A (BoTorch) or item B (eQuilibrator real MDF) — both are sub-2h tasks and high-leverage.
7. Commit + push frequently.

End of handoff.
