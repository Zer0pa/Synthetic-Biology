# DSLNT — Structural Evidence Packet (Stub Mode)

## Boundary

Research infrastructure for in silico synthetic biology / metabolic pathway engineering. Outputs are research artifacts — predicted pathways, predicted KPIs, candidate genetic modification specifications. No regulatory certification claims. No clinical or human-subject use. No environmental release of GMOs. No biocontainment-level claims (the pipeline does not commission BSL-2/3 work). No human gene drive or eugenic application. Defence / weapons / dual-use bio applications excluded under operator policy.

## Status

**scientific_valid: False** — all GPU-bound layers are in stub mode; the
envelope chain is structurally complete but the numerical predictions
are canned, not derived from real models. PRD §15 Wave 4/5/9 are
required for `scientific_valid=True`.

## Envelope chain

11 envelopes recorded under
`audit/runtime/hmo_seed_DSLNT/envelopes.jsonl`. See
`envelope_chain.json` for the ordered list of envelope_ids.

## SBOL3 attestation

Attestation document: `/workspace/synbio-run/repo/audit/runtime/hmo_seed_DSLNT/sbol/gms_DSLNT_canonical.sbol3.xml`
sha256: `71419739ec4b820a3cb935f7337808fb9caca5534099f1fbffd992bcf6557aad`

## Pre-registered acceptance thresholds

See `acceptance.yaml`. The thresholds are pre-registered (committed to
Git before any engine output is produced) and serve as the binding
acceptance criteria for the full Runpod-backed scientific run.

## Threshold check

See `threshold_check.yaml`. In this stub-mode run, only the structural
checks pass. The numerical thresholds (titer-within-25%-of-literature,
kcat-within-0.5-log-units, MDF >= 1.0 kJ/mol, cross-model disagreement
< threshold) cannot be evaluated until the GPU-bound layers go live on
Runpod.

## Boundary discipline

This is a research artifact. No regulatory certification claim. No
clinical or human-subject use. No environmental release of GMOs. No
biocontainment-level claim. No human gene drive. Defence / weapons /
dual-use bio applications excluded.
