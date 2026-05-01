# L4 — In silico screening (deep evaluation) brief

**Adapters:** L4COBRApy / L4GECKO / L4ECMpy / L4ETFL (FBA ensemble), L4EQuilibrator (MDF), L4DLKcat / L4CatPred / L4TurNuP / L4CEKM (kinetics ensemble; gpu_rest_stub).
**Layer:** L4 · v0.1 · references PRD §6.5
**Status:**
- L4 FBA — **scientific_valid=True** for L4COBRApyAdapter on iML1515 (real solve via cobra+GLPK).
- L4 thermodynamics — **scientific_valid=True** with eQuilibrator (real ΔrG').
- L4 kinetics — gpu_rest_stub canned values; real DLKcat/CatPred/TurNuP/CEKM Runpod-bound.
- L4 toxic intermediate / burden / FluxGAT — adapter shells.

## Boundary

Research infrastructure for in silico synthetic biology / metabolic pathway engineering. Outputs are research artifacts — predicted pathways, predicted KPIs, candidate genetic modification specifications. No regulatory certification claims. No clinical or human-subject use. No environmental release of GMOs. No biocontainment-level claims (the pipeline does not commission BSL-2/3 work). No human gene drive or eugenic application. Defence / weapons / dual-use bio applications excluded under operator policy.

## Purpose

Deep-evaluate Tier-A-passing candidates: FBA flux distribution, MDF thermodynamic check, kinetic-parameter ensemble, gene-expression burden, codon-adaptation index, toxic-intermediate screening, competing-pathway drain.

## Sub-layers

### L4A FBA / GEM solver ensemble

- COBRApy + GLPK (LGPL Class B; cobrapy real on `fixtures/gem/iML1515.json`)
- GECKO 3.0, ECMpy 2.0, ETFL — adapter shells (Class A); cross-model FBA disagreement record per pathway

### L4B Thermodynamics

- eQuilibrator 3.0 + PyTFA (MIT Class A) — real ΔrG' on BiGG-namespaced reactions; cache at `~/Library/Caches/equilibrator/` (1.3 GB; one-time pull). Reaction `bigg.metabolite:g6p = bigg.metabolite:f6p` returns 2.6 ± 0.4 kJ/mol — matches published PGI free energy.

### L4C Kinetics ensemble (gpu_rest_stub)

- DLKcat, CatPred, TurNuP, CEKM (Zer0pa-owned). UniKP/EF-UniKP excluded from v1 ensemble until LICENSE verified.
- `zer0pa_synbio.disagreement.build_kinetics_disagreement(...)` — σ-normalised ensemble dispersion. Pass < 0.3 < warn < 0.6 ≤ fail.

### L4D Burden — GECKO enzyme-constrained burden score (shell).

### L4E Codon optimisation — RDKit-based CAI computation per host codon table (shell).

### L4F Toxic intermediate — RDKit + ToxCast public alerts + ChEMBL CC BY (shell).

### L4G Competing pathway — COBRApy knockout simulation + FluxGAT (shell).

## Falsifiers in scope

- `f006_kinetics_disagreement_high` (Tier B, warn)
- `f007_fba_disagreement_high` (Tier B, warn)
- `f011_cekm_survivorship_bias_check` (Tier B, warn → blind eval)
- `f012_codec_as_mechanism_analog` (Tier B, fail) — every KPI must trace to genotype
- `f016_tda_regime_change` (Tier C, warn)
- `f017_industrial_scale_uncalibrated` (Tier C, fail)

## Plug-replaceability

`compare_envelopes` ignores the `tool_version` runtime field; CEKM swap (CPU prototype → Runpod-trained weights) preserves envelope schema.

## Wave 4 / 5 outstanding

- CEKM training on Runpod (Wave 4): A100/H100 80 GB, 10-20 GPU-hours.
- DLKcat / CatPred / TurNuP real inference: Runpod cutover.
- UniKP LICENSE verification.
