# L3 — Retrosynthetic pathway generation brief

**Adapters:** `L3RetroPath3Adapter`, `L3NovoStoic2Adapter`, `L3BioNaviAdapter` (gpu_rest_stub), `L3DeepRetroAdapter` (gpu_rest_stub)
**Layer:** L3 · v0.1 · references PRD §6.3
**Status:** ensemble shells with canned 2'-FL routes; real BioNavi/DeepRetro inference Runpod-bound (Wave 5).

## Boundary

Research infrastructure for in silico synthetic biology / metabolic pathway engineering. Outputs are research artifacts — predicted pathways, predicted KPIs, candidate genetic modification specifications. No regulatory certification claims. No clinical or human-subject use. No environmental release of GMOs. No biocontainment-level claims (the pipeline does not commission BSL-2/3 work). No human gene drive or eugenic application. Defence / weapons / dual-use bio applications excluded under operator policy.

## Purpose

Generate hundreds-to-thousands of `PathwayCandidate` records for a target compound, in parallel, across an ensemble of four retrosynthesis tools plus an advisory Genie-CAT layer. Cross-tool agreement is signalled per pathway via `cross_tool_disagreement_signal` (Jaccard distance over candidate-route sets).

## Tools

| Adapter | Tool | Backend | Notes |
|---|---|---|---|
| L3RetroPath3Adapter | RetroPath3.0 | local_cpu | MIT |
| L3NovoStoic2Adapter | novoStoic2.0 | local_cpu | MIT |
| L3BioNaviAdapter | BioNavi | gpu_rest_stub → runpod_rest | MIT |
| L3DeepRetroAdapter | DeepRetro | gpu_rest_stub → runpod_rest | MIT |
| (advisory) | Genie-CAT | external API | open arXiv 2025; advisory only |

## Cross-model disagreement

`zer0pa_synbio.disagreement.build_retrosynthesis_disagreement(...)` computes max-pairwise Jaccard distance across the four tools' route sets. `pass < 0.5 < warn < 0.85 ≤ fail`.

## Falsifiers in scope

- `f008_retrosynthesis_disagreement_high` (Tier B, warn) — high cross-tool Jaccard distance.
- `f009_novelty_without_retrosynthesis` (Tier B, warn) — `fully_novel` + zero retrosynthesis tool support → route to L4.5 unknown-enzyme.
- `f010_novelty_without_ts_analog` (Tier B, warn) — `fully_novel` + no TS analog in LIRC → Tier-3 advisory.
- `f018_license_drift` (Tier C, fail).

## Wave 5 outstanding

Real BioNavi + DeepRetro inference on A100; CPU stubs preserve envelope shape so cutover is a config flag (`SYNBIO_L3_BIONAVI_BACKEND=runpod_rest`).
