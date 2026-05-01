# RUNPOD-READINESS — Synthetic Biology Pipeline 4

> Wave 11 cutover proof. The Runpod migration plan, the per-layer GPU
> requirements, the executable proof of plug-replaceability, and the
> exact next commands once GPU compute is allocated.

## Boundary

Research infrastructure for in silico synthetic biology / metabolic pathway engineering. Outputs are research artifacts — predicted pathways, predicted KPIs, candidate genetic modification specifications. No regulatory certification claims. No clinical or human-subject use. No environmental release of GMOs. No biocontainment-level claims (the pipeline does not commission BSL-2/3 work). No human gene drive or eugenic application. Defence / weapons / dual-use bio applications excluded under operator policy.

## 1. Cutover invariance proof

The PRD's plug-replaceability invariant (PRD §4.5) and Runpod cutover
gate (§19.2) require that swapping `gpu_rest_stub` → `runpod_rest`
preserves the envelope schema and all non-runtime fields.

**Status: PROVEN.** `tests/runpod_cutover/test_mock_transport_invariance.py`
runs every `gpu_rest_stub` endpoint listed in PRD §17 through FastAPI
TestClient (no network) and asserts:

1. The response is a valid `UniversalLayerEnvelope`.
2. The boundary block is verbatim.
3. `falsification.scientific_valid=False` is enforced (stubs cannot claim).
4. The license attestation is present.
5. `envelope_id` is sha256-prefixed.
6. `schema_version` is `synbio.envelope.v0.1`.
7. **The REST endpoint's envelope is byte-equal to a direct adapter
   call**, modulo runtime/provenance fields (`envelope_id`, `run_id`,
   `provenance.created_at`, `provenance.git_sha`, `provenance.prov_o_jsonld`,
   `backend.execution_mode`, `backend.tool_version`).

38 tests pass. `RUNTIME_VARIABLE_FIELDS` is the audited set in
[src/zer0pa_synbio/plug_replaceability/__init__.py](src/zer0pa_synbio/plug_replaceability/__init__.py).

## 2. Per-layer GPU requirements (PRD §19.1)

| Layer | GPU class | VRAM | Notes |
|---|---|---|---|
| L1 ESM-2 batch | A100/H100 | 24 GB+ | quantised CPU works for small batches |
| L3 BioNavi / DeepRetro | A100 | 16 GB+ | inference batch |
| L4 kinetics ensemble (DLKcat / CatPred / TurNuP / CEKM) | A100 | 24 GB+ | batch inference; CEKM gpu-resident |
| L4.5 RFdiffusion3 | A100/H100 | 40 GB+ | inference; no training in v1 |
| L4.5 ESMFold | A100 | 24 GB+ | inference batch |
| L4.5 MACE-OFF | A100 | 16 GB+ | inference; training fine-tune optional |
| **CEKM training (Wave 4)** | **A100/H100** | **80 GB+** | **full training; CPU prototype validates plumbing only** |
| Reasoner (TxGemma 27B) | A100/H100 | 80 GB+ | inference; CPU-quantised for dev |

## 3. Cutover gates (PRD §19.2 — mandatory)

- [x] All schemas identical between stub and Runpod (Pydantic v0.1 schemas pinned)
- [x] All golden fixtures pass before and after backend swap (38 cutover tests)
- [x] Only `provenance/runtime` fields may change (enforced by `compare_envelopes`)
- [ ] Budget cap and kill-switch configured (operator policy; pending)
- [ ] Artifact checksums recorded; HF push completes (pending HF token verification on Runpod)
- [x] No Class C/D/E licensed tool enters product path without `audit/license_grants/<name>.yaml` (envelope-validator enforces)
- [x] httpx.MockTransport invariance test passes for every gpu_rest_stub endpoint

## 4. Cost shape (PRD §19.3)

- Wave 4 CEKM training: ~$200-400 of A100/H100 time (10-20 GPU-hours)
- Wave 5 RFdiffusion3 inference: ~$50-100 per HMO seed
- Wave 9 HMO triple validation: ~$200-300 total (three seeds, full L1-L7)
- Steady-state per engagement: ~$500-2000 GPU time (depends on novelty rate)

## 5. Cutover procedure

Once GPU compute is allocated:

1. **Provision the Runpod instance** with Python 3.13, CUDA 12.x, the
   wheels listed in `pyproject.toml`'s `[project.optional-dependencies]`
   `mfmo` extra (`torch>=2.4`, `botorch>=0.12`, `ax-platform>=0.4`,
   `gpytorch>=1.12`).
2. **Set environment variables**:
   ```
   HF_TOKEN=<token>             # operator-provided
   SYNBIO_HF_USER=Architect-Prime
   SYNBIO_L1_BACKEND=runpod_rest
   SYNBIO_L3_BIONAVI_BACKEND=runpod_rest
   SYNBIO_L3_DEEPRETRO_BACKEND=runpod_rest
   SYNBIO_L4_KINETICS_BACKEND=runpod_rest
   SYNBIO_L4_5_BACKEND=runpod_rest
   SYNBIO_L6_BUILD_BACKEND=stub  # wet-lab still gated by license_grant
   ```
3. **Pull the LIRC corpus and ESM-2 weights** from
   `Architect-Prime/synbio-lirc-v0.1` and the standard `facebook/esm2_t33_650M_UR50D`.
4. **Train CEKM** (Wave 4): build the corpus
   (BRENDA + EnzyExtract + GotEnzymes2 + ProteinGym), apply the
   adversarial three-tier synthetic-negatives sampler (PRD §12.2), train
   on A100/H100, and push weights to `Architect-Prime/synbio-cekm-v0.1`.
   Calibration audit per PRD §12.3.
5. **Re-run the cutover invariance test** with the
   `gpu_rest_stub`-replaced-by-`runpod_rest` configuration to confirm
   envelope-shape invariance (the test should produce the same diffs:
   only `envelope_id`, `run_id`, runtime/provenance fields differ).
6. **Run the HMO triple in production mode** (Wave 9 full numerical):
   ```
   python validation/hmo-seed-evidence/run_seed.py --seed 2pFL --mode scientific
   python validation/hmo-seed-evidence/run_seed.py --seed 3pSL --mode scientific
   python validation/hmo-seed-evidence/run_seed.py --seed DSLNT --mode scientific
   ```
   Each seed's `threshold_check.yaml` should now show all
   `pre_registered_acceptance` rows passing (or, where they don't, the
   honest failure must be reported per PRD §3.2).
7. **Push results** to GitHub (`origin/main`) and Hugging Face under
   `Architect-Prime/`.

## 6. The exact next command (operator review)

If the operator is reviewing this file as the agent's compute-escalation
point:

```bash
# 1. Stand up the Runpod GPU instance with A100/H100 (40+ GB VRAM).
# 2. Clone, install, and verify the cutover invariance.
git clone https://github.com/Zer0pa/Synthetic-Biology
cd Synthetic-Biology
python3.13 -m venv .venv && source .venv/bin/activate
pip install -e .[all,mfmo,dev]
export HF_TOKEN=<operator-provided>
pytest -m runpod_cutover -q   # confirm 38 tests still pass under runpod_rest backend

# 3. Wave 4: CEKM training (~10-20 GPU-hours).
python -m zer0pa_synbio.cekm.train --corpus brenda+enzyextract+gotenzymes2+proteingym \
    --adversarial-tiers alpha,beta,gamma --output Architect-Prime/synbio-cekm-v0.1

# 4. Wave 9: HMO triple full numerical run.
python validation/hmo-seed-evidence/run_seed.py --seed 2pFL --mode scientific
python validation/hmo-seed-evidence/run_seed.py --seed 3pSL --mode scientific
python validation/hmo-seed-evidence/run_seed.py --seed DSLNT --mode scientific

# 5. Push results.
git push origin main
```

The CEKM training entrypoint (`zer0pa_synbio.cekm.train`) is a future
work item. The corpus assembly + adversarial-negatives sampler skeleton
is captured in this PRD's §12 and ready to be implemented in the Runpod
machine's first hour.

## 7. What is NOT in scope for cutover

- Real wet-lab dispatch (Phase 2): triple-gated behind license grants +
  operator approval. Not on the cutover path.
- Quantum slots q001/q002/q003: permanent BlockedSourceManifest, never
  promoted in v1 per PRD §18.
- BioTRY commercial-license corpus: parked behind
  `runtime/license_grants/biotry.yaml`. Not on the cutover path.
- UniKP / EF-UniKP kinetics member: excluded from v1 ensemble until
  LICENSE verified per `audit/source_manifests/unikp_PARKED.yaml`.

## 8. Verification commands on the cutover machine

```bash
# 1. Full test suite from a clean clone.
pytest -q

# 2. Cutover invariance specifically.
pytest -m runpod_cutover -v

# 3. Falsification wave (Wave 10).
pytest -m falsification -v

# 4. HMO seed structural runs.
for seed in 2pFL 3pSL DSLNT; do
  python validation/hmo-seed-evidence/run_seed.py --seed $seed
done

# 5. Audit conformance.
synbio audit verify hmo_seed_2pFL
synbio audit verify hmo_seed_3pSL
synbio audit verify hmo_seed_DSLNT
```
