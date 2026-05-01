# L5_OED — Goal-Oriented Causal Bayesian Experimental Design brief

**Adapter:** `L5OEDAdapter`
**Layer:** L5_OED · v0.1 · references PRD §6.8
**Status:** envelope shell with stub validation sequence emitter.

## Boundary

Research infrastructure for in silico synthetic biology / metabolic pathway engineering. Outputs are research artifacts — predicted pathways, predicted KPIs, candidate genetic modification specifications. No regulatory certification claims. No clinical or human-subject use. No environmental release of GMOs. No biocontainment-level claims (the pipeline does not commission BSL-2/3 work). No human gene drive or eugenic application. Defence / weapons / dual-use bio applications excluded under operator policy.

## Purpose

Choose the next batch of experiments by goal-oriented information gain. Promoted to **Tier-1 architecture-critical** by Report 2 (Clark-ElSayed et al. 2025 + GO-CBED ICLR 2025).

## Tools

- GO-CBED (ICLR 2025) — open-source ref-impl (MIT, Class A)
- CausalBench (Nature Comms 2025, MIT) — validation

## Goal-oriented objectives

| Mode | Objective |
|---|---|
| Default (dossier emission) | `max_titer` |
| Research mode | `max_information_gain_about_uncertainty_contributors` |
| Closed-loop mode (v1 default) | `max_information_gain_about_top_pareto_candidate` |

## Outputs

`ValidationSequence` with `ordered_experiments` (each carrying `consumer ∈ {human_cro, strateos_api, emerald_api, cellfree_txtl_stub, wetlab_phase2}`).

## Falsifiers in scope

- `f022_validation_sequence_unreachable` (Tier B, fail) — every experiment's consumer must be a configured adapter for the campaign.

## Plug-replaceability

GO-CBED objective is a string; new objectives can be added by extending the `ValidationSequence.go_cbed_objective` Literal (already extended in v0.1 to include the two info-gain modes).
