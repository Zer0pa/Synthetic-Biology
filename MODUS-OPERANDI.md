# Modus Operandi — Multi-Agent Work-Stream Pattern

How Zer0pa work streams are run from research input to executable system. Reusable across work streams; this Synthetic Biology repo is the fourth instance after `Zer0pa/Health`, `Zer0pa/Materials`, and `Zer0pa/Energy`.

## Boundary

Research infrastructure. Outputs are research artifacts. No regulatory certification claims. No clinical or human-subject use. No environmental release of GMOs. Defence / weapons / dual-use bio applications excluded under operator policy.

## The pattern in one paragraph

A work stream begins when source research material lands. A **synthesis agent** reads with fresh eyes, distinguishes inherited from operator-read, surfaces what is not yet seen, and produces a portable briefing pack and synthesis document. An **orchestrator agent**, possibly on a different machine, applies fresh eyes again on the synthesis output, augments with deeper specificity, identifies remaining gaps, spawns sub-agents to research stuck or innovation points (Perplexity / Gemini deep research / domain LLMs), and writes a PRD that fully specifies an overnight long-horizon execution. **Overnight executor agents**, on a third machine (typically Runpod-bound), read the PRD with fresh eyes, decompose into parallel sub-streams, and front-load as much engineering as possible before GPU bring-up. **Runpod migration** is then a stub-swap into a known-good system, not a re-architecture. Each role adds value; if a role only paraphrases, it has not done its job.

## Role chain

| Role | Input | Output | Tools |
|---|---|---|---|
| **Synthesis agent** | Source research (papers, briefs, prior project state) | Briefing pack + synthesis doc + fresh-eyes reframe | Heavy reading, structured prose, distinguishing inherited vs operator-read |
| **Orchestrator** | Synthesis output + repo state | `PRD.md` with overnight-executable specifics, sub-agent allocation, build sequence, interface contracts, falsification ledger, audit-trail spec, acceptance gates | Multi-model routing (Opus 4.7 + GPT-5+ + domain LLMs), sub-agents in parallel worktrees, Perplexity / Gemini at stuck points, recursive fresh eyes |
| **Overnight executor** | `PRD.md` + repo state | Code, schemas, tests, audit trails, KG nodes, simulation stubs, integration scaffolds — everything that does not require GPU | Coding agents in parallel worktrees, test-first, mock simulators, REST stubs for GPU layers, KG-write discipline |
| **Runpod migration** | Overnight executor's output | GPU-shaped layers swapped into REST stubs; pipeline runs real | Same coding agents with GPU access; cutover is a config flag |

## The recursive fresh-eyes principle

Each role does not just relay the prior role's output. Each role adds:

- **What was not yet seen** — gaps, anti-patterns, missing layers, unstated assumptions.
- **What is implicit but should be explicit** — interface contracts, falsifiers, audit shapes.
- **What the next role needs that this role can prefigure** — interface specs, decision criteria, fallback patterns, acceptance gates.
- **What deep research would unlock** — strategic lookups via Perplexity / Gemini surfaced as either tactical (use the answer) or strategic (return to user for innovation).

If a role only paraphrases, it has not done its job. Each handoff is expected to be substantively richer than the input.

## Parallel-exploration principle (cross-workstream)

Zer0pa runs multiple research workstreams in parallel: **Health, Materials, Energy, and Synthetic Biology as of 2026-05-01; more to follow (Pipeline 4 of 6 per the Synthetic Biology brief framing — Drug Process Development is the explicitly-named upcoming pipeline that has had research done but not yet been mobilised at the synthesis-orchestrator layer).** These workstreams are built independently in parallel, not in coordination. Each has its own repo, its own modus operandi instance, its own synthesis agent, its own orchestrator, its own overnight executor.

Why deliberate redundancy:

- Parallel agents on the same engineering problem produce diversity of architecture — different orchestrators see different reframes that a single shared substrate would foreclose.
- Surplus coding capacity makes redundancy cheap; premature convergence is the more expensive mistake.
- Cross-workstream merge happens in a separate, named merge step after all parallel workstreams are complete. It is not a build-time concern.
- During build, an orchestrator may *read* sibling workstreams as reference for fresh eyes, but **must not depend on them** and **must not propose shared substrate** in their PRD.

If a synthesis agent or research agent recommends cross-workstream substrate sharing and the operator has rejected that recommendation, the handoff document captures the recommendation as historical artefact and the operator override as binding. **This has now happened in the Materials, Energy, AND Synthetic Biology handoffs.** The Synthetic Biology research agent's recommendations were the most explicit yet — naming a Shared Infrastructure Layer constellation (ZPE adapter, MFMO, LangGraph+Prefect+Parsl, Pydantic dossier factory, GPT-4.1 Mini extraction, MACE fine-tuning service, TxGemma 27B), a Cross-Pipeline Gym Flywheel (PathGym + CandidateGym + CompositionGym + FormulationGym + ElectrochemGym as a single compounding training corpus), and a single MACE fine-tuning service across Materials / Drug Discovery / Synthetic Biology. All three are captured-and-overridden in `synthesis/01-fresh-eyes-on-synbio-briefs.md` and `HANDOFF-TO-ORCHESTRATOR.md` § Operator override. The within-workstream framings the same handover proposes (variational principle as spine; active inference as unifying frame) are intra-workstream and explicitly permitted.

**Within-workstream sharing is allowed and recommended where physics warrants it.** Within Synthetic Biology, the seven layers (L1 ZPE → L2 metabolic knowledge → L3 retrosynthesis → L4 in silico screening → L5 multi-fidelity BoTorch + causal OED → L6 host engineering → L7 dossier) compose one coherent active-inference loop with the cell-free TX-TL adapter (per Report 2's LDBT paradigm) as the rapid Build-Test substrate. That intra-workstream composition is the design.

## Repo discipline

- **GitHub is canonical.** Local working trees may drift. The repo does not.
- Each role's output is committed and pushed before handoff. The next role reads from GitHub.
- `MODUS-OPERANDI.md` and the role-specific `HANDOFF-TO-*.md` files are updated only when the pattern itself evolves.
- Boundary block appears verbatim in every artifact.
- **Audit shape**: every artifact carries provenance — agent / model / date / source files / fresh-eyes additions.
- All sub-agent work commits back to the repo before final handoff.

## Front-load engineering before GPU

Default is local-first build. The orchestrator's PRD must specify which layers are CPU-only and which require GPU. The overnight executor builds the entire CPU side to completion, with GPU layers represented as REST stubs returning canned outputs that match real-shape contracts. **Runpod migration is a stub-swap, not a re-architecture.**

This applies to every work stream.

## Boundary discipline through layers

Each role inherits the prior boundary block. No role may relax the boundary. If a role believes the boundary should evolve, surface this as an open question in the handoff, not silently change it. **Synthetic Biology's boundary is materially different from Health / Materials / Energy's** — it must include explicit prohibition of (a) environmental GMO release, (b) BSL-2/3 commissioning, (c) gene drives, (d) human germline applications, (e) dual-use bio. The synthesis agent has carried this through every artifact in this repo.

## Cross-machine handoff

When the next role runs on a different machine:

- The startup prompt for the next role gives the GitHub URL as primary path.
- The startup prompt also gives a local fallback path for the originating machine.
- The next role clones (or fetches) before reading, so they read GitHub state, not stale local state.
- All sub-agent work commits back to GitHub before final handoff.

## Standard repo layout

```
<workstream>/
├── README.md                              # Entry, read order
├── MODUS-OPERANDI.md                      # This pattern (reusable across work streams)
├── HANDOFF-TO-<NEXT-ROLE>.md              # Role-specific handoff
├── <ROLE>-STARTUP-PROMPT.md               # Paste-ready startup prompt for next agent
├── source-briefs/                         # Inherited research input
├── briefing-pack/                         # Synthesis agent's primer (when scope warrants)
├── synthesis/                             # Synthesis agent's fresh-eyes reframes
├── PRD.md                                 # Orchestrator's output
├── phases/                                # Overnight executor's output (per-phase artifacts)
└── runtime/                               # Runtime configs, deployment manifests
```

When a new work stream starts, copy this `MODUS-OPERANDI.md` verbatim, adapt the parallel-exploration list with the current set of active workstreams, write a stream-specific `HANDOFF-TO-<NEXT-ROLE>.md`, and the synthesis-agent material specific to that stream.

## Sub-agent topology (recommended for orchestrator + overnight executor)

- **Strategic planner** — Claude Opus 4.7 at maximum reasoning effort. Reads, plans, decomposes, reviews.
- **Heavy code generator** — GPT-5+ at xhigh reasoning. Writes substantive code.
- **Per-layer specialists** — sub-agents in parallel worktrees, one per pipeline layer. Each owns its layer's code, tests, schemas.
- **Domain reasoner** — domain-specific open-weight LLM (TxGemma 27B for therapeutics; for synthetic biology, candidates are TxGemma fine-tuned on metabolic-engineering corpora, BioMedLM, or a fine-tuned Llama-class model on BRENDA + EnzyExtract + BioTRY + ProteinGym DMS data).
- **Deep-research tools** — Perplexity Pro / Gemini Advanced at stuck or innovation points; surface strategic lookups to the user. Specifically for Synthetic Biology: BioTRY commercial license verification (the one unresolved Ready-for-PRD checklist item from Report 2), EF-UniKP / UniKP commercial-use confirmation, RFdiffusion3 RosettaCommons Foundry enrolment status from operating jurisdiction (South Africa), and the SBOL-as-audit-trail-shape question.
- **KG / episodic memory** — every decision, every blocker, every resolution writes a structured node. Retrieval-augments future reasoning.

The orchestrator decides which sub-agents to spawn. The overnight executor decides which sub-agents to spawn for code-level decomposition.

## Acceptance gates (default)

Every PRD should pass three gates before overnight execution begins:

1. **Scientific gate** — every layer has falsifier coverage, source grounding, no out-of-scope claims (no environmental release framing, no GMO field-trial implication, no human germline framing, no dual-use bio framing, no clinical or pharma-clinical claim).
2. **Engineering gate** — CPU-only build runs end-to-end with GPU stubs; plug-swap test passes (the architectural invariant).
3. **Brain-functionality gate** — next-agent state is fully reconstructible from the repo plus KG plus audit log; no conversation history needed.

These are pattern-level defaults. Stream-specific gates can be added but not subtracted. **Synthetic Biology adds a fourth gate at the orchestrator's discretion: a license-clean corpus gate** — every reaction in the LIRC (License-Clean Integrated Reaction Corpus per Report 2 §4.1) carries a verifiable Class A/B license attestation; BKMS-react and KEGG bulk are excluded by construction; BioTRY is gated on commercial-license verification before training-corpus inclusion.

## Operator refinements (binding for all workstreams; captured 2026-05-01)

Recorded for every future synthesis pass. These constraints apply to every Zer0pa workstream that follows this modus operandi — whether or not it is a pipeline vertical. The role chain may compress (synthesis+orchestrator collapsed for smaller projects) or expand (multiple orchestrators per super-project), but the discipline below does not change.

- **Anti-MVP / anti-toy.** The target is never an MVP, never a first paying customer. Zer0pa is R&D pushing boundaries with science and evidence. The orchestrator's PRD specifies the most overdesigned, best-in-class system the technology landscape supports — not a minimum viable wedge.
- **110% pre-Runpod.** The overnight executor must do 110% of what they can without GPU access. The Runpod cutover is a config-flag stub-swap, not a re-architecture step.
- **Overnight long-horizon, autonomous, no interim reporting.** Once the brief is received, the executor runs end-to-end through the night without check-ins. Strip all process theater. The operator is asleep; the agent is working.
- **GitHub + Hugging Face are the review surface.** Code, schemas, tests, audit trails, decision logs, KG nodes, and the PRD itself commit to GitHub. Large datasets and AI model artifacts go to Hugging Face — under the **Architect-Prime user, not the Zer0pa org**. HF token at `~/.cache/huggingface/token` on the originating machine. When execution completes, both stores must be up to date so the cross-workstream synthesis agent (on a different machine) can review without conversation context.
- **PRD self-contained in the repo.** The orchestrator's PRD plus everything the executor needs lives in the GitHub repo. The executor can and must augment the PRD as they learn — augmentations commit back to GitHub.
- **Fork-and-own across workstreams.** Pipelines/projects can steal parts, datasets, code patterns, harnesses, schemas, and ideas freely. They cannot be runtime co-dependent. Each workstream is sacrosanct as if it were its own thing — independently runnable, independently auditable, independently shippable.
- **RESISTANCE.md doctrine.** Every executor locates and reads `RESISTANCE.md` (in the repo and on the originating machine) before starting work. The named corruptions — `fp-shapematchRE`, `fp-rushtoend`, `fp-NULLasout`, `fp-approvalseek`, `fp-flatteryasfreedom`, efficiency-as-corner-cutting — are binding constraints. The discipline IS the resistance.
- **Operator delegates engineering / science / commercial decisions** to the synthesis and orchestrator agents. Surface only strategic decisions or boundary-evolution questions to the operator.

## Beyond pipeline verticals

Some incoming projects will not be pipeline verticals (no L1–L7 substrate, no domain-specific falsification ledger shape, no PRD-equivalent in the prior pattern's strict sense). The modus operandi above still applies. The role chain compresses or expands per project scope; the discipline does not.
