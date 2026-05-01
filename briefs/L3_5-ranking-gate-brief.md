# L3.5 — Learnable pathway ranking gate brief

**Adapter:** `L3_5RankingGateAdapter`
**Layer:** L3_5 · v0.1 · references PRD §6.4
**Status:** complete; thresholds at `audit/l3_5_thresholds.json`; nightly re-optimisation hook deferred (Wave 8 PathGym integration).

## Boundary

Research infrastructure for in silico synthetic biology / metabolic pathway engineering. Outputs are research artifacts — predicted pathways, predicted KPIs, candidate genetic modification specifications. No regulatory certification claims. No clinical or human-subject use. No environmental release of GMOs. No biocontainment-level claims (the pipeline does not commission BSL-2/3 work). No human gene drive or eugenic application. Defence / weapons / dual-use bio applications excluded under operator policy.

## Purpose

Pre-screen the L3 → L4 cost cliff. Reject thermodynamically-infeasible, toxic, or grossly-disagreeing pathway candidates *cheap* (~sub-second per candidate) so deep evaluation (`L4`, $50-200 per candidate) only runs on the top-100 after Tier-A gates.

## Thresholds (state, not constants)

| Threshold | Default | Source of truth | Re-optimised on |
|---|---|---|---|
| `tau_mdf_kj_mol` | 1.0 | `audit/l3_5_thresholds.json` | nightly PathGym held-out partition |
| `tau_cofactor_flux_ratio` | 10.0 | same | same |
| `tau_toxic_severity` | 0.5 | same | same |
| `tau_retrosynthesis_jaccard` | 0.7 | same | same |

The thresholds are state. The nightly re-optimisation hook (Wave 8) Bayesian-optimises against the latest PathGym corpus state.

## Falsifiers in scope (Tier A — fast)

- `f001_invalid_selfies`
- `f002_mass_balance_violation`
- `f003_mdf_infeasibility`
- `f004_toxic_intermediate`
- `f005_stoichiometric_infeasibility`

## Outputs

```yaml
output_payload:
  schema_version: "synbio.pathway_candidate_set.v0.1"
  candidates: [...]                  # annotated with ranking_gate sub-block
  thresholds: {...}                  # current threshold snapshot
  thresholds_source: "audit/l3_5_thresholds.json (default)"
```

## Plug-replaceability

Threshold YAML is hot-reloadable; pipeline does not need restart on threshold update.
