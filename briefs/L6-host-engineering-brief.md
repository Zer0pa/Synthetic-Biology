# L6 — Host engineering brief

**Adapter:** `L6HostEngineeringAdapter`
**Layer:** L6 · v0.1 · references PRD §6.9
**Status:** SBOL3 attestation real (pysbol3); OSTIR real RBS prediction; Salis v1.0 GPL subprocess wrapper deferred (license grant in place; binary install needed).

## Boundary

Research infrastructure for in silico synthetic biology / metabolic pathway engineering. Outputs are research artifacts — predicted pathways, predicted KPIs, candidate genetic modification specifications. No regulatory certification claims. No clinical or human-subject use. No environmental release of GMOs. No biocontainment-level claims (the pipeline does not commission BSL-2/3 work). No human gene drive or eugenic application. Defence / weapons / dual-use bio applications excluded under operator policy.

## Purpose

Emit a `GeneticModificationSpec` (SBOL3-attested) per `RankedPathway` consumed. Specifies knockouts, knockins, upregulations, downregulations, cofactor balancing, codon optimisation, RBS predictions, CRISPR gRNA selections.

## Tools

- Cello 2.0 (BSD, Class A) — circuit synthesis
- Salis Lab RBS Calculator v1.0 (GPL v3, Class C, **subprocess-isolated**) — RBS initiation rate. Grant: `audit/license_grants/salis_v1.yaml`.
- OSTIR (open-source, Class A) — permissive fallback; real prediction wired (expression rate + ΔG sub-energies).
- COBRApy OptKnock / OptForce — CRISPRi design recommendations
- Quorum-sensing CRISPRi toolkit (PMC 2025)
- De Novo DNA RBS v2 commercial (Class E) — parked behind `runtime/license_grants/denovodna.yaml`.

## SBOL3 attestation (PRD §4.2 + Audit-Trail Spec §5)

Every `GeneticModificationSpec` emitted by L6 carries:

- `sbol3_uri`: path to a strict-mode-validated SBOL3 document under `audit/runtime/<campaign_id>/sbol/<spec_id>.sbol3.xml`
- `sbol_attestation.document_sha256`
- `sbol_attestation.libsbolj3_validation_status` ∈ {pass, warn, fail}
- `sbol_attestation.prov_o_chain_uri`

The Pydantic envelope model enforces `falsification.sbol_attestation_present=True` on every L6 envelope. Falsifier `f019_valid_sbol_only` validates the document via pysbol3.

## Falsifiers in scope

- `f019_valid_sbol_only` (Tier A, fail) — invalid SBOL3 document → reject envelope.

## Open questions

- Production-quality SBOL3: requires `sbol3:Sequence` for knockin nucleotide sequences (with customer authorisation), full `sbol3:Interaction` for cofactor-balancing modules, and SynBioHub publication if customer opts in. Current minimal SBOL3 doc has Component nodes only.

## Plug-replaceability

`_build_rbs_predictions` returns OSTIR output if available, or a deterministic Salis-shaped stub otherwise. Both produce the same envelope shape. Real Salis subprocess wrapper activates when the binary is installed AND the license grant is present.
