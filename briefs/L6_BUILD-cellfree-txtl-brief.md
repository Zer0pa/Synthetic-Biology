# L6_BUILD — Cell-free TX-TL adapter (LDBT rapid Build-Test substrate) brief

**Adapters:** `L6BuildCellFreeStubAdapter`, `L6BuildStrateosAdapter`, `L6BuildEmeraldAdapter`
**Layer:** L6_BUILD · v0.1 · references PRD §6.10
**Status:** all three adapters return shape-correct stub observations; wet-lab Phase 2 dispatch triple-gated.

## Boundary

Research infrastructure for in silico synthetic biology / metabolic pathway engineering. Outputs are research artifacts — predicted pathways, predicted KPIs, candidate genetic modification specifications. No regulatory certification claims. No clinical or human-subject use. No environmental release of GMOs. No biocontainment-level claims (the pipeline does not commission BSL-2/3 work). No human gene drive or eugenic application. Defence / weapons / dual-use bio applications excluded under operator policy.

## Purpose

Cell-free TX-TL platforms (myTXTL, PURExpress) are the rapid Build-Test substrate per the LDBT paradigm (Clark-ElSayed et al. 2025). Inputs `GeneticModificationSpec`; outputs `CellFreeTXTLObservation` (transcription/translation rate, soluble protein yield, target conversion).

## Three implementations (all v1)

### `CellFreeStubAdapter` — Phase 0 stub

- Canned shape-correct outputs from a calibrated lookup table.
- CPU-only; engineering-mode only (`scientific_valid=False` enforced).
- Used by every test and every dry-run.

### `StrateosMyTXTLAdapter` — Phase 0 dry-run + Phase 2 wet-lab

- Wraps Strateos TxPy programmatic Python client.
- **Default = dry-run** with simulated outputs validated against canned myTXTL benchmark data.
- **Phase 2 wet-lab dispatch** requires ALL of:
  1. `runtime/cloud_lab.config.yaml` populated with provider credentials
  2. `runtime/license_grants/strateos.yaml` present
  3. Explicit operator approval (signed off in the same file)

  Hard interlock — no wet-lab dispatch without all three.

### `EmeraldPURExpressAdapter` — Phase 0 dry-run + Phase 2 wet-lab

Same shape, Emerald Cloud Lab + NEB PURExpress kit. Same triple-gate.

## Falsifiers in scope

- `f020_txtl_observation_without_in_vivo` (Tier B, warn → route_to_phase_2) — every Phase 0 dry-run output that drives a host-engineering decision is flagged.

## Closed-loop dossier mode

`L6_BUILD` envelopes post back to L5 via the closed-loop router. The BoTorch surrogate updates; the L7 dossier emits round-N+1 with refined ranking and a new validation sequence. Active-inference loop closes across the cell-free TX-TL boundary, fully CPU-side, fully functional in stub mode.

## Plug-replaceability

All three adapters return envelopes that pass the same downstream-consumer tests; closed-loop dossier mode works with any of the three. Cutover from stub → real wet-lab is a config-flag change, not a re-architecture.
