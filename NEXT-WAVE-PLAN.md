# NEXT-WAVE-PLAN — Synthetic Biology Pipeline 4

> What the next agent (Runpod-bound or sub-agent dispatch) should do
> after this overnight executor's commit. Open questions for the operator
> are listed at the bottom.

## Boundary

Research infrastructure for in silico synthetic biology / metabolic pathway engineering. Outputs are research artifacts — predicted pathways, predicted KPIs, candidate genetic modification specifications. No regulatory certification claims. No clinical or human-subject use. No environmental release of GMOs. No biocontainment-level claims (the pipeline does not commission BSL-2/3 work). No human gene drive or eugenic application. Defence / weapons / dual-use bio applications excluded under operator policy.

## A. Compute-escalation work (Runpod / GPU)

### A.1 Wave 4 — CEKM training (highest priority)

- **Why:** Zer0pa-owned kinetics model; corpus is the moat; survivorship-bias
  defended via three-tier adversarial sampler (PRD §12.2).
- **What to build:**
  - `src/zer0pa_synbio/cekm/__init__.py` (skeleton in repo) →
    `cekm/architecture.py` (ESM-2 + D-MPNN + condition MLP + adaptive gate),
    `cekm/corpus.py` (BRENDA + EnzyExtract + GotEnzymes2 + ProteinGym
    assembly with deduplication), `cekm/adversarial_negatives.py` (Tier α/β/γ
    sampler), `cekm/train.py` (entrypoint), `cekm/calibrate.py` (held-out
    blind eval per Tier).
  - HF push: `Architect-Prime/synbio-cekm-corpus-v0.1` (corpus slices),
    `Architect-Prime/synbio-cekm-v0.1` (trained weights).
- **Compute:** A100/H100 80 GB; 10-20 GPU-hours; ~$200-400.
- **Acceptance:** held-out calibration curve per Tier α/β/γ; CEKM
  envelope-correct under `runpod_rest` backend (cutover invariance test
  still passes).

### A.2 Wave 5 — L4.5 unknown-enzyme inference

- **Why:** Required to score the DSLNT seed acceptance gate (PRD §3.2 row 3:
  ≥ 1 Tier-2 unknown-enzyme classification).
- **What to bring up:** RFdiffusion3 (Foundry) + Baker catalytic motif
  scaffolding + MACE-OFF + ESMFold + ProDy + eQuilibrator + Genie-CAT.
  All adapter shells and REST stubs already exist; replace
  `gpu_rest_stub` with `runpod_rest`.
- **Compute:** A100/H100 40+ GB VRAM; ~$50-100 per HMO seed.
- **Acceptance:** Wave 11 cutover invariance test passes under
  `runpod_rest` for `/l4_5/rfdiffusion3/scaffold`,
  `/l4_5/mace_off/binding`, `/l4_5/esmfold/predict`.

### A.3 Wave 5 — L1 ESM-2 batched inference

- **Why:** Production-volume embeddings for the L1 ZPE encoder.
- **What:** swap `_hash_derived_embedding` (current CPU stub) for a real
  ESM-2 forward pass on A100/H100. Same `embedding_provenance` payload;
  `scientific_valid=True` only when `execution_mode=runpod_rest`.
- **Compute:** A100 24+ GB VRAM; per-batch.

### A.4 Wave 5 — L3 BioNavi / DeepRetro batched inference

- **Why:** real retrosynthesis ensemble outputs replacing the canned
  3-route slice.
- **Compute:** A100 16+ GB VRAM.

### A.5 Wave 9 — Full numerical HMO triple

- **Why:** the scientific validation triple cannot pass `scientific_valid=True`
  until A.1-A.4 are live. Stub mode runs already produced structural
  envelope chains.
- **Acceptance:** all three `validation/hmo-seed-evidence/<seed>/threshold_check.yaml`
  files report `pre_registered_acceptance` rows passing or honestly failing
  (with documented reason per PRD §3.2).

## B. CPU-feasible work that was deferred for time / scope

### B.1 Real LIRC corpus build (Wave 2)

- Currently L2 returns a canned 2'-FL slice. Full LIRC build pulls
  Rhea SPARQL + MetaNetX MNXref 4.5 + BiGG REST + ModelSEED + BRENDA bulk
  CC BY 4.0, reconciles into one atom-mapped SMARTS namespace, and pushes
  to `Architect-Prime/synbio-lirc-v0.1`.
- ATLAS, BKMS-react, KEGG bulk are excluded by construction (manifests
  in place; falsifier f018 fires on any embedding attempt).
- Estimated runtime: 4-8 hours on local CPU once SPARQL queries are wired.

### B.2 PathGym corpus growth + nightly re-optimisation

- The PathGym writer is in place (`src/zer0pa_synbio/pathgym/__init__.py`).
- The nightly retrain hook (PRD §11) updates L3.5 thresholds, CEKM weights,
  and BoTorch surrogate prior against the latest corpus state. Skeleton
  not yet wired; needs a scheduler entry-point.

### B.3 BoTorch real surrogate

- L5 MFMO currently uses a scipy-backed deterministic Pareto sort.
- Real BoTorch + qNEHVI + qMFKG + Hamming-distance kernel + ASR
  initialisation requires `torch + botorch + ax-platform + gpytorch`.
  Wheels for Python 3.13 x86_64 macOS are spotty; on Linux Runpod,
  install is straightforward.

### B.4 TDA early-warning real time-series

- ripser + persim are installed. The adapter shell (PRD §5.3) needs:
  - simulated fermentation time-series fixtures (from cell-free TX-TL
    canned data),
  - the `SynbioTDAEarlyWarning` writer,
  - integration into the L4 envelope chain.

### B.5 Real eQuilibrator MDF computation

- `equilibrator-api` is installed. First use requires a one-time
  ~100 MB cache download. Wire into L4B for real MDF scores per pathway
  step.

### B.6 SBOL3 attestation hardening

- Current L6 SBOL3 documents are minimal (Component nodes for host strain
  + target genes). Production-quality SBOL3 needs `sbol3:Sequence` for
  knockin nucleotide sequences (with customer authorisation), full
  `sbol3:Interaction` for cofactor-balancing modules, and SynBioHub
  publication if the customer opts in.

## C. Operator-level open questions (PRD §24)

These remain unresolved and require operator input:

1. **Pipeline 4 of 6 mapping.** What are pipelines 5 and 6? Drug Process
   Development is the explicit upcoming candidate; pipeline 6 unspecified.
2. **First Phase 2 wet-lab activation customer.** When the closed-loop
   dossier mode is functional, which customer's wet-lab activates first?
   Glycom / DSM-Firmenich / Inbiose / ZuChem / Gnubiotics / internal Zer0pa wet-lab?
3. **HF mirror visibility from sibling repos.** Should this synbio HF
   namespace be cross-referenced from the Health, Materials, Energy
   sibling-workstream READMEs as part of the cross-workstream pattern
   catalogue?

## D. License-status follow-ups

- **UniKP / EF-UniKP**: PRD §22 resolution says executor verifies LICENSE
  in repo and commits SPDX in `audit/source_manifests/unikp_PARKED.yaml`.
  This overnight executor did not perform that verification (web fetch
  not exercised); the manifest is correctly marked as PARKED with
  `license_class: D` (unverified). Next agent: re-fetch the GitHub repo,
  inspect for LICENSE file or repository metadata, update the manifest.
- **BioTRY commercial license**: same. PRD §22 left this as v2-gated.
  Agent should re-confirm the codebase MIT and surface the database
  content's commercial-use terms with a Perplexity / Gemini deep-research
  query.

## E.bis CPU-continuation phase (2026-05-01) — what is now done

After the H100 release, a second executor closed `HANDOFF-CPU-CONTINUATION.md`
items A–H on the Mac (Python 3.13 + a Python-3.11 `.venv-l5` for
torch wheels). Status delta:

| Item | Status | Where |
|---|---|---|
| A. Real BoTorch surrogate (qLogNEHVI + Hamming kernel + ASR warm-start) | **DONE** | `src/zer0pa_synbio/adapters/l5_mfmo/{__init__,botorch_worker}.py`. `.venv-l5` provisioning script: `scripts/provision_venv_l5.sh`. |
| B. Real eQuilibrator MDF in L4B | **DONE** | `src/zer0pa_synbio/adapters/l4_thermodynamics/__init__.py`. HMO seeds emit `stub_mode=False` with real LP MDF. |
| C. Real LIRC corpus build | **DONE (architecture)** | `src/zer0pa_synbio/adapters/l2_lirc/build.py`. Validation slice `fixtures/lirc/lirc_v0.1_smoke.json.gz` (50 reactions per source, 40s wallclock). Full ~4-8h Wave-2 build is a single CLI call: `python -m zer0pa_synbio.adapters.l2_lirc.build`. **Operator action remaining:** run the full build and HF-push the result. |
| D. Real CEKM corpus loaders | **DONE** | `src/zer0pa_synbio/cekm/loaders/`. Pod-ready config: `configs/cekm/wave4_real_corpus.yaml`. |
| E. TDA real fermentation simulator + warning_score | **DONE** | `src/zer0pa_synbio/tda/{simulator,__init__}.py`. All 5 PRD §5.3 failure modes implemented as physically-grounded ODE perturbations. Detector calibration deferred to PathGym. |
| F. Salis Lab RBS Calculator GPL subprocess wrapper | **DONE (wrapper)** | `src/zer0pa_synbio/adapters/l6_host_engineering/salis_rbs_subprocess.py`. License-grant gate + binary discovery + parser. **Operator action remaining:** install Salis v1.0 binary on the GPU pod and point `SALIS_RBS_BIN` at it. |
| G. Pull cekm_training_audit.jsonl from HF | **DONE** | `audit/runtime/cekm_train_h100/cekm_training_audit.jsonl` (gitignored; 71 events). |
| H. Update reports | **DONE** | This section + `EXECUTION-STATE.md §9` + `FINAL-REPORT-RUNPOD.md §11`. |

### What is genuinely still GPU-bound

After items A–H, the CPU side is exhausted modulo BLOCKED-by-credentials
work. The next pod-rental is required for:

1. **Real CEKM training on the assembled real corpus** (10–20 GPU-h
   on H100). The data pipeline + config are now ready.
2. **L4.5 RFdiffusion3 / Baker scaffolding / MACE-OFF / ESMFold
   inference** (per A.2 above; needs Foundry enrollment for
   RFdiffusion3 + GPU).
3. **Real DLKcat / CatPred / TurNuP / FluxGAT batch inference at
   industrial scale.**

### What is BLOCKED on operator action

These do not need a GPU but they do need an operator decision:

1. **Salis v1.0 binary install + license-grant activation.** The wrapper
   is in place but the GPL binary isn't installed anywhere. Operator
   step: `git clone https://github.com/salislab/RBS_Calculator_v1`,
   wrap the Python-2 entrypoint in a small CLI shim that emits
   `INITIATION_RATE_AU=<float> CONFIDENCE=<float>`, set
   `SALIS_RBS_BIN`. Then L6 will use Salis on every run that touches
   `_build_rbs_predictions`.
2. **Full LIRC corpus run + HF push.** ~4-8h CPU + ~5 GB output.
   Operator step: `python -m zer0pa_synbio.adapters.l2_lirc.build`,
   then `huggingface-cli upload Architect-Prime/synbio-lirc-v0.1
   fixtures/lirc/lirc_v0.1.json.gz`. Could run on a small CPU VM rather
   than a GPU pod.

## E. PathGym corpus seed

The PathGym ledger (`audit/reasoner_tuples.jsonl`) is currently empty.
The first seed entries should come from the Wave 9 HMO triple runs
once they execute under `scientific_valid=True` mode. The runtime call
is in `validation/hmo-seed-evidence/run_seed.py`; add a
`make_reasoner_tuple` + `append_reasoner_tuple` invocation at the end of
each seed run when the rights_label is `tier_3_public` (default for the
HMO triple per PRD §10).
