# BOUNDARY — Synthetic Biology Pipeline 4

> This file is canonical. Every artifact, envelope, dossier, schema, manifest,
> generated prompt, fixture, REST response, and test fixture must carry this
> exact paragraph verbatim. Hash discipline: the boundary block is hashed at
> module import (`zer0pa_synbio.boundary.BOUNDARY_SHA256`); any envelope whose
> `boundary` field does not match the hash fails the BoundaryGate and is
> rejected. Mutations to this paragraph are governed change events recorded in
> `audit/governance/boundary_changes.jsonl` and require a new envelope schema
> version.

## Boundary

Research infrastructure for in silico synthetic biology / metabolic pathway engineering. Outputs are research artifacts — predicted pathways, predicted KPIs, candidate genetic modification specifications. No regulatory certification claims. No clinical or human-subject use. No environmental release of GMOs. No biocontainment-level claims (the pipeline does not commission BSL-2/3 work). No human gene drive or eugenic application. Defence / weapons / dual-use bio applications excluded under operator policy.

## Authority chain

This boundary inherits from:

1. `MODUS-OPERANDI.md` § Boundary discipline through layers — the pattern-level
   rule that no role may relax the boundary across the role chain.
2. `PRD.md` § 0 Boundary — the synbio-specific block authored by the synbio
   orchestrator, which adds (a) environmental GMO release prohibition,
   (b) BSL-2/3 commissioning prohibition, (c) gene-drive prohibition,
   (d) human-germline prohibition, (e) defence / weapons / dual-use
   exclusion. These additions are materially different from Health, Materials,
   and Energy and are deliberate.
3. `RESISTANCE.md` — anti-corruption discipline that prevents premature
   relaxation of the boundary under "scientific honesty" or "frontier"
   framings.

## Operative consequences

- Outputs are *research artifacts*. They are not regulatory submissions, FDA
  filings, ICH-compliant pharma dossiers, IND/NDA-equivalent packets, EU REACH
  notifications, or any other certification artefact. Any consumer of a
  Zer0pa Synthetic Biology dossier is responsible for their own regulatory
  pathway.
- Outputs do not authorise wet-lab execution. The cell-free TX-TL adapter
  (`L6_BUILD`) ships three implementations: a CPU-only stub, a Strateos
  myTXTL dry-run wrapper, and an Emerald PURExpress dry-run wrapper. Real
  wet-lab dispatch is hard-gated behind `runtime/cloud_lab.config.yaml`,
  `runtime/license_grants/<provider>.yaml`, and explicit operator approval.
  See `RUNBOOK.md` § Wet-lab activation.
- Outputs are not authorised for environmental release of any genetically
  modified organism. No predicted pathway in any dossier may be promoted to
  field-trial or release framing. The boundary block in every dossier is the
  legal and scientific record of this constraint.
- The pipeline does not commission biocontainment-level (BSL-2 or BSL-3)
  work. Any candidate target whose realisation would require BSL-2/3
  containment fails the boundary check at L2 and is logged as a blocked
  candidate.
- No gene-drive constructs (CRISPR-based super-Mendelian inheritance bias)
  are designed or released. Any pathway attempting to insert a gene-drive
  cassette fails the L6 boundary check.
- No human-germline editing. Any pathway whose host organism is *Homo
  sapiens* with germline-targeting modifications fails closed.
- Defence, weapons, and dual-use bio applications are excluded under operator
  policy. Operator policy is binding; the orchestrator and overnight executor
  cannot relax it.

## Cross-link

- Falsifier `f000_boundary_violation` (registry: `audit/falsifiers.yaml`)
  fires on any envelope whose boundary block does not match
  `zer0pa_synbio.boundary.BOUNDARY_SHA256`.
- Test: `tests/falsification/test_boundary_gate.py`.
