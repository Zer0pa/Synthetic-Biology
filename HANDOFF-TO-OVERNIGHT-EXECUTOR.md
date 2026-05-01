# Handoff to the Overnight Executor — Synthetic Biology Work Stream

You are the overnight executor for the Zer0pa Synthetic Biology / Metabolic Pathway Engineering work stream. You work from GitHub on a different machine. You inherit a self-contained PRD and repository briefing pack from the synbio orchestrator. Your job is to execute the PRD end to end without interim user engagement, build as much of the full research infrastructure as possible before Runpod GPU bring-up, and represent GPU-dependent layers with contract-true REST stubs that can later be swapped by configuration flag.

## Boundary

Research infrastructure for in silico synthetic biology / metabolic pathway engineering. Outputs are research artifacts — predicted pathways, predicted KPIs, candidate genetic modification specifications. No regulatory certification claims. No clinical or human-subject use. No environmental release of GMOs. No biocontainment-level claims (the pipeline does not commission BSL-2/3 work). No human gene drive or eugenic application. Defence / weapons / dual-use bio applications excluded under operator policy.

This boundary is binding. Every artifact you create must carry it verbatim. Any layer, dossier, schema, envelope, test fixture, generated prompt, or report that omits it is invalid.

## What you inherit

### Primary specification

- `PRD.md` — the controlling execution spec. It locks the architecture, HMO validation triple, layer contracts, falsifier hierarchy, source-license decisions, CPU-first wave plan, Runpod cutover procedure, and acceptance gates.
- `MODUS-OPERANDI.md` — the multi-agent workstream pattern. Pay special attention to the parallel-exploration principle and the operator refinements captured on 2026-05-01.
- `RESISTANCE.md` — binding anti-corruption discipline. Read it first if present in the checkout. If absent, create `EXECUTION-STATE.md` entry `BLOCKED:missing_resistance_md` and continue using the named resistance protocols listed in `PRD.md`.
- `HANDOFF-TO-ORCHESTRATOR.md` — historical context for why the PRD rejects cross-workstream runtime sharing while explicitly permitting fork-and-own reuse.
- `source-briefs/00-research-agent-handover-note.md`, `source-briefs/01-full-technology-landscape.md`, and `source-briefs/02-corrections-and-architecture.md` — source research and license/tool stack input.
- `synthesis/01-fresh-eyes-on-synbio-briefs.md` — the prior synthesis agent's reframe and pressure-test points. The PRD resolves or supersedes them.

### Locked orchestrator decisions

- Build the full R&D-grade pipeline, not an MVP, not a toy, and not a first-paying-customer slice.
- HMOs are the scientific validation triple, not a narrowed product wedge: 2'-FL known-good, 3'-SL known-borderline, DSLNT novel.
- Closed-loop dossier mode ships in v1 by default.
- Unknown Enzyme Generative Sub-Pipeline ships in v1 with RFdiffusion3/Foundry, Baker catalytic motif scaffolding, MACE-OFF, ESMFold, ProDy, eQuilibrator, and Genie-CAT advisory fallback.
- Cell-free TX-TL is a Phase 0 Build-Test adapter with dry-run/stub implementations first and wet-lab dispatch hard-gated behind explicit config and grants.
- BioTRY, UniKP/EF-UniKP, ATLAS, KEGG bulk, and BKMS-react stay out of training/product paths unless the PRD's license gates are satisfied.
- The Synbio Audit-Trail Spec v0.1 is a required artifact: SBOL3 + PROV-O + Pydantic + LangGraph DAG + sha256 hash chain.

## Operator override — no shared runtime substrate

The research agent recommended shared infrastructure across Health, Materials, Energy, Synthetic Biology, Drug Process Development, and future pipelines. The operator rejected shared runtime co-dependency.

Binding rule:

- Do not import code from sibling workstreams at runtime.
- Do not write to a shared cross-workstream database, corpus, vector store, HF dataset, or service instance.
- Do not depend on sibling repos or sibling HF Spaces to run tests or pipelines.
- You may read sibling repos and copy patterns, schemas, harness ideas, test shapes, prompts, and code structure.
- Any borrowed pattern must be reimplemented inside this repo and owned by Synthetic Biology.

Within Synthetic Biology, L1 through L7 and L6_BUILD compose one coherent active-inference loop. That intra-workstream composition is required.

## What you produce

Your final repository state must contain the full scaffold listed in `PRD.md` §7, including at minimum:

- `pyproject.toml`, package source under `src/zer0pa_synbio/`, and tests under `tests/`.
- `BOUNDARY.md`, `RUNBOOK.md`, `RUNPOD-READINESS.md`, `EXECUTION-STATE.md`, `FINAL-REPORT.md`, and `HANDOFF-FROM-OVERNIGHT-EXECUTOR.md`.
- All v0.1 schemas under `schemas/`, including the universal envelope, `GeneticModificationSpec`, pathway sets, validation sequence, cell-free TX-TL observation, disagreement record, early-warning signal, dossier, and Synbio Audit-Trail spec schema.
- Falsifier registry under `audit/falsifiers.yaml` with the PRD's named falsifiers plus any new ones you add with schema-version discipline.
- Source manifests under `audit/source_manifests/` for every external source, model, dataset, checkpoint, and HF artifact.
- KG schema and export surfaces under `kg/`.
- Golden fixtures and negative fixtures under `fixtures/`.
- REST stubs for every GPU-bound backend and cloud-lab backend.
- HMO seed evidence packets under `validation/hmo-seed-evidence/`.
- `docs/synbio-audit-trail-v0.1-spec.md`.

Bulk artifacts go to private Hugging Face under user `Architect-Prime`; repo contains manifests and small test slices only.

## Execution mode

You are expected to run long-horizon and autonomously. The operator may be asleep. Do not stop for routine implementation decisions. Do not interim-report. Do not ask the user for confirmation, preference, or permission while useful work remains. Your first action is to clone or fetch `https://github.com/Zer0pa/Synthetic-Biology`, check out `main`, and read the repo files from that checkout. Do not rely on conversation history or stale local fallback files.

Before declaring any need for increased compute, download, install, configure, cache, and execute everything the current machine can support. If the available Mac/local machine can complete a layer or the whole pipeline within storage and time limits, complete it there. If a layer truly needs GPU or larger compute, leave the same endpoint shape, same schema, same fixtures, same manifests, same tests, and a Runpod config flag so the later upgrade is a stub swap, not a rewrite.

If you hit a blocker:

1. Record it in `EXECUTION-STATE.md` as `BLOCKED:<component>:<reason>:<workaround>`.
2. Keep the interface shape intact with a stub, manifest, or degraded local implementation.
3. Continue to the next independent wave.
4. Surface the blocker in `FINAL-REPORT.md` and `HANDOFF-FROM-OVERNIGHT-EXECUTOR.md`.

Only stop for a boundary issue, credential absence that prevents all useful local work, or a destructive ambiguity that cannot be safely stubbed.

## Build sequence

Follow `PRD.md` §15 exactly unless the codebase forces a better local ordering. The expected wave order is:

1. GitHub bootstrap on the executor machine.
2. Maximum local setup before compute escalation.
3. Foundation: boundary, schemas, falsifier registry, KG schema, audit spec, HF smoke path.
4. Envelope plumbing and L1.
5. L2 LIRC corpus manifests and license-clean reconciliation.
6. L3/L3.5/L4 parallel CPU-side tools and GPU stubs.
7. CEKM corpus, synthetic negatives, held-out split, CPU prototype, Runpod training stub.
8. L4.5 unknown-enzyme, L5 MFMO, L5_OED, TDA.
9. L6 host engineering and L6_BUILD cell-free TX-TL adapters.
10. L7 dossier and closed-loop active inference.
11. PathGym and ReasonerTuple ledger.
12. HMO scientific validation triple.
13. Falsification wave.
14. Runpod cutover proof.
15. Final integration and report.

Parallelize by non-overlapping file scopes or worktrees. Commit coherent increments. Push frequently.

## Acceptance gates

You are not done until all gates are either passing or explicitly blocked with evidence:

- Scientific gate: units, uncertainty, model disagreement, falsifier evidence, no stub scientific-validity claims.
- Engineering gate: clean-clone tests, no hidden state, no Docker requirement on the originating Mac, REST stubs for all GPU/cloud-lab surfaces, plug-replaceability tests.
- Brain-functionality gate: a future agent can reconstruct state from repo + audit/KG + HF manifests without conversation history.
- Falsification-wave gate: deliberate bad inputs are blocked or quarantined by the named falsifiers.
- License-clean corpus gate: no BKMS-react, no KEGG bulk, BioTRY gated, ATLAS reference-only, NASA OSDR controlled human data excluded.
- R&D-standard gate: no MVP shortcuts, no v1.1 deferral where only engineering effort is missing.

## Authorities and tools

- GitHub is canonical. Operate on `main` unless the operator instructs otherwise. Push final state to `Zer0pa/Synthetic-Biology`.
- The different-machine executor must work from the GitHub checkout. Local fallback paths are historical convenience only.
- Use Hugging Face only for bulk artifacts and model/corpus mirrors under `Architect-Prime`.
- On the originating Mac, HF token is expected at `~/.cache/huggingface/token`. On Runpod, expect `HF_TOKEN` env var.
- Docker is not available on the originating Mac. Runpod may use Docker later.
- GPU layers must have REST stubs now and `runpod_rest` implementations later; cutover is a config flag.
- Perplexity/Gemini-style deep research is allowed for stuck license or frontier status questions, but source findings must be committed as manifests, not just remembered.

## Final report requirements

Before final push, write:

- `FINAL-REPORT.md` with what was built, what failed, tests run, falsification evidence, license findings, HF pushes, commit hashes, and next-wave list.
- `HANDOFF-FROM-OVERNIGHT-EXECUTOR.md` mirroring this handoff: what the next role inherits, what they produce, constraints, authorities, and open questions.
- `RUNPOD-READINESS.md` with backend flags, GPU requirements, stub-swap evidence, and `httpx.MockTransport` invariance status.

The last action is `git push origin main`. The operator reviews GitHub and Hugging Face from a different machine.

## Open questions carried forward

These remain operator-level questions, not blockers:

1. Pipeline 4 of 6 mapping: what are pipelines 5 and 6? Drug Process Development is the explicit upcoming candidate; pipeline 6 remains unspecified.
2. First Phase 2 wet-lab activation partner/customer after CPU/GPU pipeline readiness.
3. Whether to cross-reference the Synthetic Biology HF artifacts from sibling workstream READMEs after all independent builds complete.
