# L5 — Multi-fidelity BoTorch optimisation (MFMO) brief

**Adapter:** `L5MFMOAdapter`
**Layer:** L5 · v0.1 · references PRD §6.7
**Status:** envelope shell with scipy-backed deterministic Pareto sort fallback; real BoTorch deferred to Runpod (torch wheels for Python 3.13 macOS x86_64 are spotty).

## Boundary

Research infrastructure for in silico synthetic biology / metabolic pathway engineering. Outputs are research artifacts — predicted pathways, predicted KPIs, candidate genetic modification specifications. No regulatory certification claims. No clinical or human-subject use. No environmental release of GMOs. No biocontainment-level claims (the pipeline does not commission BSL-2/3 work). No human gene drive or eugenic application. Defence / weapons / dual-use bio applications excluded under operator policy.

## Purpose

Multi-fidelity Bayesian optimisation over the (genotype, environment) design space. Pareto-optimal under {`max_titer`, `max_yield`, `min_burden`, `min_toxicity`}.

## Specifications (PRD §6.7 — locked)

- Acquisition: `qNEHVI` (multi-objective Pareto) + `qMFKG` (Knowledge Gradient over three fidelities: GEM/FBA cost 1×, kinetic/GECKO cost 10×, CFD-informed cost 100×).
- Surrogate: GP with **Hamming-distance kernel** over discrete ZPE-encoded design vectors (default; closed-form gradient).
- Plug-replaceable alternatives: deep ensemble (3-model), BNN — same `SurrogateAdapter` interface.
- Initialisation: ASR-thermostable variants seed first batch when any pathway enzyme has predicted Tm < 50°C (10-100× sample-efficiency gain).

## Tools

- BoTorch + Ax + GPyTorch (MIT, Class A) — full implementation on Runpod.
- scipy + scikit-learn — CPU fallback for development; deterministic Pareto sort.

## Outputs

`RankedPathwaySet` with Pareto rank, expected_titer/yield/burden CIs, surrogate calibration score, and a `ValidationSequence` (filled by L5_OED).

## Falsifiers in scope

- `f012_codec_as_mechanism_analog` (Tier B, fail) — KPI must trace to genotype.
- `f017_industrial_scale_uncalibrated` (Tier C, fail).

## Plug-replaceability

Swap Hamming-distance kernel for categorical-product kernel; calibration changes measurably; envelope schema unchanged. Test in `src/zer0pa_synbio/plug_replaceability/`.

## Wave 5 outstanding

Install `torch + botorch + ax-platform + gpytorch` on Runpod Linux; activate `qNEHVI + qMFKG`; ASR-thermostable seed batch when applicable.
