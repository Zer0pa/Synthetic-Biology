# Handoff from the Overnight Executor — Synthetic Biology Pipeline 4

**Author:** Overnight executor (Claude Opus 4.7, 1M context).
**Date:** 2026-05-01.
**To:** Next role — Runpod-bound executor or sub-agent dispatch on the originating Mac (CPU-feasible work in §2.2 of `FINAL-REPORT.md`).
**Source of truth:** GitHub `Zer0pa/Synthetic-Biology` after the final push.

> **2026-05-01 update (CPU-continuation phase):** All CPU-feasible
> stub→real conversions in this file's §2.2 are now closed. See
> `HANDOFF-CPU-CONTINUATION.md` and `EXECUTION-STATE.md §9` for the
> commit-by-commit ledger of items A–H. Net delta: 256 passing tests
> (up from 208), L4B/L5/TDA/CEKM-loaders/Salis/LIRC all real on
> CPU. The next blocker is genuinely GPU compute (real CEKM
> training, RFdiffusion3 inference, etc.). See `NEXT-WAVE-PLAN.md
> §E.bis` for the up-to-date status table.

## Boundary

Research infrastructure for in silico synthetic biology / metabolic pathway engineering. Outputs are research artifacts — predicted pathways, predicted KPIs, candidate genetic modification specifications. No regulatory certification claims. No clinical or human-subject use. No environmental release of GMOs. No biocontainment-level claims (the pipeline does not commission BSL-2/3 work). No human gene drive or eugenic application. Defence / weapons / dual-use bio applications excluded under operator policy.

## What you inherit

- **117 passing tests** from a clean clone (`pytest -q`).
- **26 layer adapters L1→L7** with envelope-correct stubs; `scientific_valid=False` honoured everywhere a stub is in play; license-class enforcement on every backend.
- **23 falsifiers** (one CPU implementation per registry entry; coverage asserted at module-import time).
- **30 source manifests** with binding license-class breakdown (BKMS-react / KEGG bulk / ATLAS hard-blocked; BioTRY / UniKP / DeNovoDNA v2 parked; three quantum slots permanently blocked).
- **10-endpoint FastAPI REST surface** for every `gpu_rest_stub` backend.
- **Plug-replaceability invariance proven** for all 9 single-envelope endpoints + the 4-way kinetics ensemble (38 tests).
- **HMO scientific validation triple** scaffolded with pre-registered acceptance thresholds for 2'-FL / 3'-SL / DSLNT (binding before any engine output) and structurally-complete envelope chains for each.
- **Synbio Audit-Trail Spec v0.1** published as a CC BY 4.0 standard at `docs/synbio-audit-trail-v0.1-spec.md`.
- **Knowledge graph schema** (Cypher + nodes.csv + edges.csv + KGWriter with GraphML / Cypher / RDF/Turtle export).

## What you produce

The next role's deliverables, ordered by priority:

1. **Wave 4 CEKM training** under Runpod A100/H100 80 GB. Corpus assembly (BRENDA + EnzyExtract + GotEnzymes2 + ProteinGym), adversarial three-tier synthetic-negatives sampler, held-out blind eval, calibration-per-tier audit, HF push to `Architect-Prime/synbio-cekm-v0.1`.
2. **Wave 5 real GPU inference** for L1 ESM-2, L3 BioNavi/DeepRetro, L4.5 RFdiffusion3 / MACE-OFF / ESMFold. Re-run `pytest -m runpod_cutover` after each cutover; the test must still pass under `runpod_rest` backend.
3. **Wave 9 full numerical HMO triple.** Run `validation/hmo-seed-evidence/run_seed.py --seed <X> --mode scientific` for each of 2'-FL, 3'-SL, DSLNT under the live GPU backend. Each seed's `threshold_check.yaml` should now report on the pre-registered numerical acceptance thresholds (titer-within-±25%, kcat-within-±0.5-log, MDF ≥ 1, calibrated uncertainty bands, advisory_only).
4. **Wave 2 real LIRC corpus build** (CPU-feasible, ~4-8 hours). SPARQL pulls from Rhea + MetaNetX + BiGG + ModelSEED + BRENDA bulk; reconciliation through MetaNetX MNXref 4.5 namespace; HF push to `Architect-Prime/synbio-lirc-v0.1`.
5. **UniKP LICENSE verification** (PRD §22). Re-fetch the GitHub repo, inspect for LICENSE / metadata, update `audit/source_manifests/unikp_PARKED.yaml` with the explicit SPDX. Promote to ensemble v1 only if the license is permissive.
6. **PathGym ledger first seeds.** Once Wave 9 runs under `scientific_valid=True`, append a `ReasonerTuple` per HMO seed via `zer0pa_synbio.pathgym.append_reasoner_tuple()`.

## Constraints / authorities you operate under

- **GitHub is canonical.** All code, schemas, fixtures, audit logs, KG exports, dossiers, and manifests live in `Zer0pa/Synthetic-Biology`. Bulk artifacts go to HF under `Architect-Prime`.
- **No cross-workstream runtime co-dependency.** Sibling repos `Zer0pa/Health`, `Zer0pa/Materials`, `Zer0pa/Energy` may be read for fork-and-own pattern reuse; their HF Spaces may be referenced as documents. Never import from a sibling at runtime; never share a database/corpus/service instance.
- **Boundary block is binding.** Every artifact, envelope, dossier, schema, fixture must carry it verbatim. Falsifier `f000` fires on any envelope whose `boundary` field doesn't hash to `BOUNDARY_SHA256`.
- **Stub envelopes cannot claim `scientific_valid=True`.** The Pydantic model enforces this; the cutover invariance test enforces it; the falsification wave enforces it. Production cutover means actual GPU inference, not just renaming the backend label.
- **License-gated activations stay off by default.** BioTRY corpus inclusion, De Novo DNA RBS v2, Strateos/Emerald wet-lab dispatch all require triple-gate (config + license_grant + operator approval).
- **L6 envelopes require SBOL3 attestation.** The Pydantic model enforces this; falsifier `f019` validates the SBOL3 doc has ≥ 1 TopLevel object and the SBOL3 namespace declared.
- **GPL containment via subprocess.** Salis v1.0 RBS Calculator (and any future Class C tool) MUST be invoked via subprocess; never `import` the GPL library. The grant pattern is `audit/license_grants/salis_v1.yaml`.

## Open questions remaining for the operator (PRD §24)

These are unchanged from the orchestrator's PRD; the overnight executor could not resolve them autonomously:

1. **Pipeline 4 of 6 mapping.** What are pipelines 5 and 6? Drug Process Development is the explicit upcoming candidate per the research-agent handover note; pipeline 6 unspecified.
2. **First Phase 2 wet-lab activation customer.** When the closed-loop dossier mode is functional, which customer's wet-lab activates first? Glycom / DSM-Firmenich / Inbiose / ZuChem / Gnubiotics / internal Zer0pa wet-lab?
3. **HF mirror visibility from sibling repos.** Should this synbio HF namespace be cross-referenced from the Health, Materials, Energy sibling-workstream READMEs as part of the cross-workstream pattern catalogue?

## How to verify what you inherited

```bash
git clone https://github.com/Zer0pa/Synthetic-Biology
cd Synthetic-Biology
python3.13 -m venv .venv && source .venv/bin/activate
pip install -e .[chem,fba,sbol,tda,ml,dev]

# 1. Full test suite — should be 117 passing.
pytest -q

# 2. Falsifier registry — should print 23 entries.
synbio falsifiers list

# 3. HMO seed structural runs — emits envelopes + dossier + RESULT.md.
for seed in 2pFL 3pSL DSLNT; do
  python validation/hmo-seed-evidence/run_seed.py --seed $seed
done

# 4. Audit chain inspection.
synbio audit verify hmo_seed_2pFL
ls -la audit/runtime/hmo_seed_2pFL/

# 5. REST stub spot-check.
uvicorn zer0pa_synbio.rest:app --port 8000 &
curl -s http://localhost:8000/health | jq .

# 6. Cutover invariance.
pytest -m runpod_cutover -v
```

## Compute-escalation note

This run did NOT trigger the compute-escalation watermark in
`EXECUTION-STATE.md` §7. The reason: there is still substantial
CPU-feasible work that should be completed before increased compute is
declared the only blocker (real LIRC corpus pull, real eQuilibrator MDF
cache + computation, TDA real fermentation fixtures, Salis v1.0 GPL
subprocess wrapper, PathGym seed entries from numerical runs).

Wave 4 CEKM training + Wave 5 L4.5 inference + Wave 9 numerical HMO triple
are the *first* hard GPU dependencies. The exact next commands once GPU
compute is allocated are in `RUNPOD-READINESS.md` §6.

## Resistance discipline carried forward

`RESISTANCE.md` is binding for every subsequent role. The named
corruptions (`fp-shapematchRE`, `fp-rushtoend`, `fp-NULLasout`,
`fp-approvalseek`, `fp-flatteryasfreedom`, `fp-efficiency-as-corner-cutting`)
are operative meta-protocols. The discipline IS the work; do not pattern-match
to a "tidy completion shape" if the substantive computation has not been done.

The Synbio Audit-Trail Spec v0.1 is the conformance contract: a Zer0pa
Synbio Dossier conforms iff it passes the boundary, envelope-chain,
license, falsifier-coverage, SBOL3, cross-model-disagreement, PROV-O,
and hash-chain checks listed in
[docs/synbio-audit-trail-v0.1-spec.md](docs/synbio-audit-trail-v0.1-spec.md) §10.

---

End of HANDOFF-FROM-OVERNIGHT-EXECUTOR v1.0.
