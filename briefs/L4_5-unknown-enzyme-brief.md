# L4.5 — Unknown enzyme generative sub-pipeline brief

**Adapters:** `L4_5RFdiffusion3Adapter`, `L4_5MACEOFFAdapter`, `L4_5ESMFoldAdapter` (all gpu_rest_stub).
**Layer:** L4_5 · v0.1 · references PRD §6.6
**Status:** envelope shells; real GPU inference Runpod-bound (Wave 5).

## Boundary

Research infrastructure for in silico synthetic biology / metabolic pathway engineering. Outputs are research artifacts — predicted pathways, predicted KPIs, candidate genetic modification specifications. No regulatory certification claims. No clinical or human-subject use. No environmental release of GMOs. No biocontainment-level claims (the pipeline does not commission BSL-2/3 work). No human gene drive or eugenic application. Defence / weapons / dual-use bio applications excluded under operator policy.

## Purpose

Triggered only when Tier-B falsifier `f009` (novelty-without-retrosynthesis) or `f010` (novelty-without-TS-analog) fires. Three-tier novelty classification:

| Tier | Inputs available | Tools | Output |
|---|---|---|---|
| 1 | TS analog available | Baker catalytic motif scaffolding + RFdiffusion3 conditioned on TS geometry | Candidate enzyme structure + ESMFold sequence + MACE-OFF binding feasibility + ProDy NMA |
| 2 | reaction class known, no TS | RFdiffusion3 + Genie-CAT mechanistic hypothesis | Probabilistic enzyme structure ensemble; lower confidence; flag in dossier |
| 3 | fully novel reaction class | Genie-CAT advisory only | "experimental suggestion only"; lowest priority in closed-loop validation |

## Tools

- RFdiffusion3 — RosettaCommons Foundry, BSD 3-Clause (Class A); `audit/source_manifests/rfdiffusion3.yaml`
- MACE-OFF — MIT (Class A); binding-energy feasibility
- ESMFold — MIT (Class A); structure prediction
- ProDy — MIT (Class A); normal-mode analysis (CPU)
- eQuilibrator — MIT (Class A); ΔrG check
- Baker catalytic motif scaffolding — open methods (paper-derived implementation)
- Genie-CAT — open arXiv 2025; advisory wrapper

## Falsifiers in scope (Tier C — heavy)

- `f013_rfdiffusion3_motif_infeasible` (warn)
- `f014_mace_off_binding_implausible` (warn)
- `f015_prody_nma_misaligned` (warn)

## Wave 5 outstanding

A100/H100 40+ GB VRAM for RFdiffusion3; A100 24+ GB for ESMFold; A100 16+ GB for MACE-OFF. ProDy + eQuilibrator already CPU-feasible.

## Plug-replaceability

`L4_5RFdiffusion3Adapter` ships in `gpu_rest_stub` mode by default. Activating Foundry inference is a config flag (`SYNBIO_L4_5_BACKEND=runpod_rest`). Cutover invariance test in `tests/runpod_cutover/`.
