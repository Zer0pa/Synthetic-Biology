# Zer0pa Synthetic Biology — Workstream Repository

Canonical home for the Zer0pa Synthetic Biology / Metabolic Pathway Engineering work stream. Multi-agent handoff: synthesis → orchestrator → overnight executor → Runpod migration. Repo is the source of truth across machines.

## Boundary

Research infrastructure for in silico synthetic biology / metabolic pathway engineering. Outputs are research artifacts (predicted pathways, predicted KPIs, candidate genetic modification specifications). No regulatory certification claims. No clinical or human-subject use. No environmental release of GMOs. No biocontainment-level claims (the pipeline does not commission BSL-2/3 work). No human gene drive or eugenic application. Defence / weapons / dual-use bio applications excluded under operator policy.

## What is in here

| Path | Purpose | Author role |
|---|---|---|
| `MODUS-OPERANDI.md` | Reusable multi-agent pattern + parallel-exploration principle (Health, Materials, Energy, Synthetic Biology run independently in parallel; convergence happens after all complete, not during) | Synthesis agent |
| `HANDOFF-TO-ORCHESTRATOR.md` | Synthetic Biology-specific brief for the next agent (the synbio orchestrator) — defines what they inherit, what they must produce, and the operator override on the research agent's three cross-workstream substrate-sharing recommendations | Synthesis agent |
| `ORCHESTRATOR-STARTUP-PROMPT.md` | The exact prompt the user pastes into a fresh agent session to spin up the synbio orchestrator | Synthesis agent |
| `source-briefs/` | Inherited research input — the research-agent handover note plus two technology-landscape briefs (full landscape; corrections-and-architecture brief introducing the four-column license decomposition, LDBT paradigm, causal OED node, and PathGym flywheel) | External (consumer of synthesis) |
| `synthesis/` | Fresh-eyes reading of the briefs and handover note — what is not yet seen, the falsification-driven Bayesian-active-inference reframe, the cell-free TX-TL Build-Test substrate, twelve specific things the briefs do not see, and the operator override section | Synthesis agent |
| `PRD.md` (to be written) | The PRD that drives the overnight long-horizon execution on a Runpod-bound machine | Synbio orchestrator |

## Read order for the next agent

1. `MODUS-OPERANDI.md` — how the role chain works and why these workstreams stay independent.
2. `HANDOFF-TO-ORCHESTRATOR.md` — what you (synbio orchestrator) inherit and produce. Includes the operator override on the research agent's three cross-workstream proposals.
3. `source-briefs/00-research-agent-handover-note.md` — the research agent's five structural observations, the four Report 2 contributions (license decomposition, LDBT, causal OED, PathGym), and the explicit acknowledgement that observations #1, #4, #5 are cross-workstream and will be overridden per operator policy.
4. `source-briefs/01-full-technology-landscape.md` — Brief #1 — full seven-layer pipeline catalogue, twenty intersectional science mappings, five application domains (industrial chemicals, specialty/fine chemicals, SAF/biofuels, pharmaceutical intermediates, food/flavour ingredients).
5. `source-briefs/02-corrections-and-architecture.md` — Brief #2 — four-column license audit (BRENDA core data corrected to CC BY 4.0 Class A, BKMS-react held at C/D, KEGG single-entry queries usable, NASA OSDR two-tier access), per-task data matrix (BioTRY, EnzyExtract, GotEnzymes2 added; BioTRY commercial license is the one explicit unresolved blocker), tiered intersectional map promoting causal OED to Tier 1 and demoting heterogeneity to Tier 2/v1.1, and five emergent innovation artefacts (LIRC, PathGym, Unknown Enzyme Generative Sub-Pipeline, MFMO, CEKM).
6. `synthesis/01-fresh-eyes-on-synbio-briefs.md` — synthesis-agent reframe; this is the substrate for your own fresh-eyes augmentation.

## Provenance

- Initial commit: 2026-05-01.
- Research agent: Perplexity / Zer0pa Architect Prime composite (Briefs #1 and #2 plus handover note), 2026-04-30.
- Synthesis agent: Claude Opus 4.7 (1M context), 2026-05-01.
- Next agent: synbio orchestrator (writes `PRD.md`).
- Following: overnight executor on a Runpod-bound machine.

## Cross-workstream principle (deliberate)

This workstream runs in parallel with `Zer0pa/Health`, `Zer0pa/Materials`, and `Zer0pa/Energy`. Each workstream is built end-to-end as an independent pipeline. **No substrate is shared during build.** Redundancy across workstreams is a deliberate asset — surplus coding capacity buys diversity of architecture, not duplicated cost. Convergence (if any) happens in a separate merge step after all parallel workstreams complete. See `MODUS-OPERANDI.md` § Parallel-exploration principle.

The research-agent handover note for this workstream explicitly proposes a Shared Infrastructure Layer (Observation #1), a Cross-Pipeline Gym Flywheel coupling PathGym to CandidateGym / CompositionGym / FormulationGym / ElectrochemGym (Observation #4), and a single SE(3)-equivariant MACE fine-tuning service serving Materials / Drug Discovery / Synthetic Biology (Observation #5). Those three recommendations are captured verbatim in `synthesis/01-fresh-eyes-on-synbio-briefs.md` and explicitly overridden in `HANDOFF-TO-ORCHESTRATOR.md` § Operator override. Observations #2 (variational principle as spine) and #3 (active inference as unifying frame) are within-workstream architectural framings and are permitted.

The MVP-wedge debate (HMOs as the cleanest first deliverable on GRAS regulatory grounds; vs terpenoids, syngas, BIAs, SAF) is the synthesis agent's pressure-test for the orchestrator. Three named seeds are proposed (2'-FL known-good, 3'-SL known-borderline, novel sialylated HMO outside published reach) mirroring the dofetilide/verapamil/ranolazine and LLZO/Li6PS5Cl/quaternary patterns. The orchestrator may take, refine, or override.
