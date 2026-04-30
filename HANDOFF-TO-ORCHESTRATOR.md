# Handoff to the Synbio Orchestrator — Synthetic Biology Work Stream

You are the synbio orchestrator for the Zer0pa Synthetic Biology / Metabolic Pathway Engineering work stream. This document briefs you on what you inherit, what is expected of you, and what you produce. It does not pre-bake the structure of your PRD — that is your job. The substrate is on the table; shape it with your fresh eyes.

## Boundary

Research infrastructure for in silico synthetic biology / metabolic pathway engineering. Outputs are research artifacts (predicted pathways, predicted KPIs, candidate genetic modification specifications). No regulatory certification claims. No clinical or human-subject use. No environmental release of GMOs. No biocontainment-level claims (the pipeline does not commission BSL-2/3 work). No human gene drive or eugenic application. Defence / weapons / dual-use bio applications excluded under operator policy.

## What you inherit

### Source briefs (`source-briefs/`)

- **`00-research-agent-handover-note.md`** — Read first. The research agent's framing of what the two source briefs gave the synthesis agent (the four Report 2 contributions: four-column license decomposition audit, LDBT paradigm, causal OED node, PathGym flywheel) and five structural observations the research agent contributes (Shared Infrastructure Layer; Variational Principle as Spine; Active Inference as Unifying Frame; Cross-Pipeline Gym Flywheel; SE(3) Transfer Bridge as Operational Now). Three of the five (#1, #4, #5) are explicit cross-workstream substrate-sharing recommendations and are captured-and-overridden in § Operator override below.
- **`01-full-technology-landscape.md`** — Brief #1, ~150 KB, 1,663 lines. The full seven-layer pipeline catalogue (L1 ZPE → L2 metabolic knowledge → L3 retrosynthesis → L4 in silico screening → L5 BoTorch optimisation → L6 host engineering → L7 dossier), twenty intersectional science mappings (information theory ↔ metabolic networks; non-equilibrium thermodynamics ↔ enzyme kinetics; SE(3)-equivariant geometry ↔ enzyme structure; evolutionary ML ↔ directed evolution; fluid dynamics ↔ bioreactor scale-up; etc.), five application domains (industrial chemicals, specialty/fine chemicals, SAF/biofuels, pharma intermediates, food/flavour ingredients), key organisms with GEM availability and licensing, complete Class A/B/C/D/E stack summary, benchmark and performance metrics, key institutional and academic sources.
- **`02-corrections-and-architecture.md`** — Brief #2, ~78 KB, 750 lines. Higher-value document. Four-column license corrections (BRENDA core data is CC BY 4.0 Class A, not C/E as Report 1 implied; BKMS-react remains proprietary C/D and excluded from corpus; KEGG single-entry queries are usable but bulk requires commercial licensing; NASA OSDR is two-tier with public non-human Class A and controlled human Class D; ModelSEED confirmed MIT Class A; RFdiffusion3 available via RosettaCommons Foundry under BSD/MIT). Per-task data matrix introducing BioTRY (>52,000 TRY entries, commercial-license-pending), EnzyExtract (89,544 kinetic entries absent from BRENDA, MIT), and GotEnzymes2 (59.6M predicted entries, CC BY 4.0). Tiered intersectional map with causal OED promoted to Tier 1, heterogeneity demoted to Tier 2/v1.1, gauge theory and QM/MM held at Tier 3. Five emergent innovation artefacts (LIRC = License-Clean Integrated Reaction Corpus; PathGym = DBTL benchmark; Unknown Enzyme Generative Sub-Pipeline; MFMO = Multi-Fidelity Metabolic Optimiser; CEKM = Conditional Enzyme Kinetics Model). Typed seven-layer architecture and Ready-for-PRD checklist with one explicit unresolved item (BioTRY commercial license verification).

### Synthesis (`synthesis/`)

- **`01-fresh-eyes-on-synbio-briefs.md`** — Fresh-eyes reading of the two briefs plus the handover note by the prior synthesis agent (Claude Opus 4.7, 2026-05-01). Surfaces:
  - The architectural reframe: the Synthetic Biology pipeline IS a falsification-driven Bayesian active-inference loop over discrete ZPE-encoded genotype space, with cell-free TX-TL as the rapid Build-Test substrate per the LDBT paradigm. The L1-L7 decomposition is the agent's perception-action factorisation, not a forward chain.
  - Cross-model disagreement as a universal falsification primitive across L2 (BiGG vs ModelSEED vs KBase), L3 (RetroPath3.0 vs novoStoic2.0 vs BioNavi vs DeepRetro), L4 kinetics (DLKcat vs TurNuP vs DeepEnzyme vs CatPred), L4 FBA (COBRApy vs GECKO vs ECMpy vs ETFL), and L5 (GP vs deep ensemble vs Bayesian neural network).
  - Twelve specific things the briefs and handover do not see — the MVP-wedge HMOs argument; the missing retrosynthesis ranking gate (L3.5); the CEKM survivorship-bias remedy; the unspecified LDBT cell-free TX-TL adapter; the dossier-as-iterative-engagement mismatch with single-shot emission; the KEGG-coverage gap landing on pharma intermediates; the GP-kernel mismatch with discrete ZPE inputs; ASR-thermostable variants as BoTorch loop initialization rather than a directed-evolution tactic; the missing SBOL-shaped audit-trail surface; the industrial-scale-up gap that should be parked-for-real-data not papered over; the unspecified consumer of the dossier validation_sequence; and the "Pipeline 4 of 6" framing that reveals two upcoming workstreams not yet identified.
  - Pressure-test points for the orchestrator (nine explicit).
  - **A cross-workstream substrate proposal that the operator has explicitly rejected.** See § Operator override below.

## Operator override — keep workstreams independent

The research-agent handover note proposes three explicit cross-workstream substrate-sharing observations:

- **Observation #1 — Shared Infrastructure Layer**: a single shared instance of ZPE adapter (SELFIES interface), MFMO (multi-fidelity BoTorch), LangGraph + Prefect + Parsl substrate, Pydantic dossier factory, GPT-4.1 Mini Phase 0 literature extraction, MACE fine-tuning service, TxGemma 27B reasoning layer — serving Health, Materials, Energy, Synthetic Biology, Drug Process Development, and the upcoming Pipeline 6 from one Platform Core specification.
- **Observation #4 — Cross-Pipeline Gym Flywheel**: PathGym (Synthetic Biology) coupled to CandidateGym (Drug Discovery), CompositionGym (Materials), FormulationGym (Drug Process Development), and ElectrochemGym (Energy) as one compounding annotated cross-domain corpus that trains a single platform-level ZPE.
- **Observation #5 — Single SE(3) MACE Fine-Tuning Service**: one MACE fine-tuning service typed as an API, serving Materials Science, Drug Discovery, and Synthetic Biology, with 100-500 DFT configurations and 1-4 GPU-hours per system as the stated cost shape.

**The operator has rejected all three.** The binding policy is the *Parallel-exploration principle* in `MODUS-OPERANDI.md`. Stated precisely:

- Build Synthetic Biology end-to-end as an independent pipeline with its own ZPE adapter, its own MFMO BoTorch implementation, its own LangGraph + Prefect + Parsl deployment, its own Pydantic dossier factory, its own Phase 0 literature extraction, its own MACE-OFF deployment, its own TxGemma instance, its own PathGym corpus.
- Do not propose cross-workstream substrate sharing in your PRD.
- Do not depend on `Zer0pa/Health`, `Zer0pa/Materials`, or `Zer0pa/Energy` for any architectural component **at runtime**.
- **Fork-and-own is explicitly permitted (operator clarification, 2026-05-01).** You may copy any implementation pattern, falsifier-registry shape, audit-log schema, plug-replaceability harness, runpod-cutover scaffold, KG-node taxonomy, code structure, test pattern, or architectural detail from a sibling workstream and reimplement it inside Synthetic Biology. You may steal tools, datasets, components, and design patterns freely. **What is rejected is runtime co-dependency** — two workstreams sharing one running instance of any service, two workstreams writing to one shared database or corpus, two workstreams importing from one shared git repo. Read the sibling repos as fresh-eyes reference, fork the patterns that work, and build your own deployment.
- Each workstream is sacrosanct as if it were its own thing — independently runnable, independently auditable, independently shippable. Convergence (if any) happens in a separate, named merge step after all parallel workstreams are complete.
- The deliberate redundancy across Health, Materials, Energy, and Synthetic Biology is the point. Premature convergence is the more expensive mistake.

This has now happened in the Materials, Energy, and Synthetic Biology handoffs — three captured-and-overridden cross-workstream recommendations from three separate research-agent or synthesis-agent passes. The pattern is consistent.

**Within-workstream sharing is permitted.** The research agent's Observations #2 (Variational Principle as the Spine — VQE / CALPHAD / MDF / BoTorch / PBPK as instances of one principle on different functional spaces) and #3 (Active Inference as the Unifying Frame — ZPE-as-prior, knowledge-layer-as-semantic-memory, generative-candidates-as-predictions, BoTorch-as-policy, validation-sequence-as-epistemic-action-set) are within-workstream architectural framings and explicitly permitted. The synthesis-agent reframe (the pipeline IS a falsification-driven Bayesian active-inference loop with cell-free TX-TL as the Build-Test substrate per LDBT) is also within-workstream.

The deliberate redundancy across Health, Materials, Energy, and Synthetic Biology is the point. The synthesis recommendation is captured here for traceability, but it is not the operating instruction.

## What you must do

Write `PRD.md` at the top of this repo. The PRD specifies a long-horizon overnight execution by a separate set of overnight-executor agents on a different machine that will eventually have Runpod GPU access. The PRD must front-load every CPU-side build before GPU bring-up.

You are expected to:

- **Apply recursive fresh eyes.** Where the prior synthesis is incomplete, close gaps. Where it sketches, lock interface contracts. Where it gestures, specify falsifiers and acceptance gates. Where it notes a frontier development, evaluate whether deeper specification is warranted. **Augment and innovate; do not paraphrase.** If your PRD is not substantively richer than the synthesis it inherited from, you have not done your job.
- **Spawn sub-agents** in parallel worktrees per pipeline layer (L1 ZPE / L2 knowledge / L3 retrosynthesis / L3.5 ranking gate / L4 in silico screening / L5 BoTorch + causal OED / L6 host engineering / L7 dossier) and per cross-cutting concern you identify (falsification ledger; cross-model disagreement aggregator; audit-trail schema with SBOL3 attestation; LIRC corpus build; PathGym benchmark scaffold; Unknown Enzyme Generative Sub-Pipeline; CEKM training corpus assembly with synthetic-negatives + held-out partition; cell-free TX-TL adapter spec; MVP HMO evidence packet; cloud-lab integration patterns; data-sovereignty schema; CRO partnership pricing model).
- **Use Perplexity Pro / Gemini Advanced deep research** at the points the prior agents left open. Specifically: BioTRY commercial license verification (the one explicit unresolved Ready-for-PRD checklist item from Report 2 §5.4); EF-UniKP / UniKP commercial-use confirmation from GitHub MIT; RFdiffusion3 RosettaCommons Foundry enrolment status from the operating jurisdiction (South Africa); the SBOL-as-audit-trail-shape question (does any synbio-CRO-scale audit standard exist analogous to ICH M15?); the cell-free TX-TL adapter API status of myTXTL / PURExpress / commercial alternatives; whether ATLAS of Biochemistry's predicted reactions can be referenced (not redistributed) in the LIRC corpus under academic terms.
- **Resolve the MVP-wedge selection.** The synthesis recommends HMOs (Domain 3.5) on GRAS regulatory simplification, *E. coli* iML1515 tooling depth, tractable pathway lengths, multi-customer market structure, with three named seeds (2'-FL known-good, 3'-SL known-borderline, novel sialylated HMO outside published reach). You may take, refine, or override with reasoning. The cleanest seed-test triple discipline (known-good / known-borderline / novel) should hold.
- **Maximally front-load pre-Runpod engineering.** The PRD must specify what every overnight-executor agent does without GPU access. Acceptance criterion: when the Runpod machine comes online, the entire CPU-side of the pipeline is complete and GPU layers are stubs ready to be swapped. The cutover must be a config-flag-shaped change, not an architectural rewrite.

## Shape of the PRD

The structure is yours. Mirror the sibling Health PRD, Materials PRD, or Energy PRD if the patterns help; depart where your fresh eyes warrant. The PRD must cover at minimum:

- **Scope and boundary** with the verbatim research-only block and the explicit MVP wedge selection (HMOs are the synthesis recommendation; the orchestrator commits or overrides).
- **Architecture** that the overnight executor can decompose into parallel sub-streams without further user input. Specify interface contracts (SELFIES / SMILES / InChI / mmCIF / SBML / SBOL3 / Rhea reaction IDs / MetaNetX MNXref 4.5 IDs / FMI / JSON Schema function calls). Plug-replaceability invariant ("swap any layer's tool in <1 day with no downstream breakage").
- **Falsification framing** with cross-model disagreement specified as a first-class quantity flowing through the audit log; falsifier registry covering at minimum: invalid SELFIES, missing SBOL3 attestation, MDF infeasibility, mass-balance violation, toxic intermediate present, novelty without retrosynthetic support, novelty without TS analog (route to unknown-enzyme sub-pipeline), DPA-style cross-model disagreement on kinetics, GECKO-vs-ECMpy flux disagreement, retrosynthesis-tool disagreement above threshold, CEKM survivorship-bias check (predict on known-negative held-out partition), CRO-deliverable not SBOL3-parseable, codec-as-mechanism analog (predicted KPI without mechanistic chain to genotype), license-drift (any pathway citing BKMS-react or KEGG bulk content), industrial-scale claim without calibrated corpus.
- **Build sequence** that front-loads CPU work and stubs GPU layers; explicit parallel sub-agent allocation per layer; layer order; gating test cases; HMO MVP wedge as the integration target; LDBT cell-free TX-TL adapter as Phase 0 stub if the orchestrator commits to LDBT in v1.
- **Agent topology** — Opus + GPT-5+ + domain LLMs (TxGemma 27B fine-tuned on metabolic-engineering corpora as Synthetic-Biology-domain reasoner; or BioMedLM / fine-tuned Llama-class on BRENDA + EnzyExtract + BioTRY + ProteinGym DMS data) + Perplexity / Gemini + KG with episodic memory.
- **Audit-trail spec** — campaign-grade per-discovery provenance log with SBOL3 attestation per `GeneticModificationSpec`; KG schema (nodes for Compound / Reaction / Pathway / Enzyme / Organism / Strain / Modification / Assay / Dossier; edges for catalyses / requires-cofactor / produces / consumes / encodes / regulates / has-source / has-falsifier / has-audit / member-of-pathway / instantiates-in-organism / measured-by / supports / contradicts); per-layer log shape; sha256 hash chain across all 12+ audit tables.
- **MVP first deliverable** — the HMO seed evidence packet (or the orchestrator's chosen alternative) with three named systems and pre-registered acceptance thresholds: predicted titer within 25% of literature for known-good; calibrated CI covers literature value for known-borderline; defensible novel-pathway prediction with uncertainty band for the novel candidate. Engine-vs-literature-baseline lift target +10 points or more, mirroring Health's PubMed-baseline harness pattern.
- **Self-bootstrapping reasoner** — how (input, simulation, output, falsifier, ground-truth) tuples flow from each pipeline run into a private dataset that compounds the moat; how the PathGym corpus accumulates per-engagement; how cross-model disagreement records compound into a held-out adversarial set.
- **CEKM training corpus design** — explicit BRENDA CC BY 4.0 + EnzyExtract MIT + GotEnzymes2 CC BY 4.0 mix; synthetic-negatives via active-site distance gates (AlphaFold2/ESMFold + AutoDock Vina screen for predicted non-fits); held-out partition strategy with the EnzyExtract "dark matter" entries reserved for blind eval; calibration-curve audit as part of the acceptance gate.
- **Cell-free TX-TL / cloud-lab / wet-lab integration plan** — `L_BUILD` adapter interface (input `GeneticModificationSpec` from L6, output `CellFreeTXTLObservation` envelope); stub adapters for myTXTL / PURExpress / a generic CellFreeStubAdapter; cloud-lab dry-run stubs for Strateos / Emerald / Arctoris with hard interlocks (mirroring Health's `runtime/cloud_lab.config.yaml` pattern); the closed-loop variant where DBTL rounds post results back to the dossier (v1 vs v1.1 decision).
- **Unknown Enzyme Generative Sub-Pipeline** — RFdiffusion3 (RosettaCommons Foundry, BSD/MIT) for all-atom diffusion + Baker catalytic motif scaffolding (Nature 2025) + MACE-OFF organic-molecule force field + ProDy NMA feasibility check + eQuilibrator ΔrG check; three-tier novelty classification (TS analog available / reaction class known / fully novel); retrosynthesis-to-RFdiffusion3 conditioning bridge; advisory-only flag for fully-novel reactions.
- **Quantum slot specification** — per the Materials synthesis pattern, quantum can plug into three slots (L1 VQE for active-site DFT, L4 QAOA for combinatorial enzyme-substrate fit, L5 quantum amplitude amplification on BoTorch acquisition). Synthetic Biology's quantum slot is far-horizon (Tier 3 in Report 2 §3.4); the PRD may stub it cleanly behind a `BlockedSourceManifest` with no scientific promotion until hardware lands.
- **Runpod migration plan** — exact stub-swap procedure; per-layer GPU requirements (RFdiffusion3 inference, MACE-OFF training, TxGemma 27B inference, ESMFold batch inference); cost shape; cutover acceptance gates with same-shape `httpx.MockTransport` golden-fixture invariance test (mirroring Energy Wave 4 pattern).
- **Acceptance gates** — scientific (falsifier coverage, source grounding, no out-of-scope claims, no environmental release / GMO field-trial / human-germline framing, no clinical or pharma-clinical claim); engineering (CPU-only build runs end-to-end; plug-swap test passes; same-endpoint Runpod cutover proven); brain-functionality (next-agent state reconstructible from repo + KG + audit log without conversation history).
- **License-clean corpus gate (4th, Synthetic-Biology-specific)** — every reaction in LIRC carries a verifiable Class A/B license attestation; BKMS-react and KEGG bulk are excluded by construction; BioTRY is gated on commercial-license verification before training-corpus inclusion; ATLAS of Biochemistry's predicted reactions are referenced (cross-database hint) but not embedded.
- **Productisation and pricing** — campaign vs platform-retainer (per the synthesis pattern; multi-year HMO portfolio retainer for a Glycom/Inbiose/Jennewein-shaped customer is the analogue of Materials' Amplats platform-buyer relationship); year-1 floor and year-3 ceiling; cross-domain transfer story limited to within-Synthetic-Biology (HMOs → terpenoids → BIAs → SAF → industrial chemicals); funding triangulation across DOE / NIH / DARPA / NSF / Horizon Europe synbio calls.
- **Data-sovereignty schema** — contract structure for who owns customer pathway designs, customer-fine-tuned CEKM weights, customer assay observations, audit trails. Surface as open question for the user if you cannot resolve.
- **Open questions for the user / for the next agent** — explicitly. Things you could not resolve. Things that require user innovation input. The Pipeline 4 of 6 mapping question (the synthesis surfaces this; the operator should specify what the remaining two pipelines are) is one explicit open question.

Be granular. The overnight executor is a separate agent on a separate machine with no conversation context. Every interface, every contract, every threshold, every fallback must be readable from the PRD alone.

## Constraints

- Mac storage bounded on the originating machine (~42 GiB free at last check); bulk artifacts go to private Hugging Face under Architect-Prime when offload is needed.
- HF token at `~/.cache/huggingface/token` on the originating machine. Cross-machine, the user provides.
- BioTRY commercial license verification must be resolved before any training-corpus inclusion (handover note Ready-for-PRD checklist explicit).
- BKMS-react excluded from corpus by construction (Report 2 §1.1 — proprietary, redistribution prohibited).
- KEGG bulk content excluded from corpus (Report 2 §1.2 — Class E without commercial license); KEGG IDs as cross-references only.
- NASA OSDR controlled-access human data excluded (Report 2 §1.3 — Class D, dbGaP-shaped IRB requirement).
- No Docker on the originating Mac. Overnight executor on Runpod may use Docker.
- No bulk local datasets — manifests + metadata + small slices only. Rhea + MetaNetX + BiGG + ModelSEED + UniProt + iGEM Registry SPARQL + REST APIs are sufficient CPU-side.
- GitHub canonical. All sub-agent work commits back to `Zer0pa/Synthetic-Biology` before PRD finalisation.
- No regulatory or clinical claims. No human-subject inference.
- No environmental release of GMOs, no BSL-2/3 commissioning, no gene drives, no human germline applications, no dual-use bio.
- **No cross-workstream substrate sharing.** See § Operator override.

## Authorities and tooling

- `gh` CLI authenticated as Zer0pa-Architect-Prime on the originating machine; cross-machine, the user provides.
- HF token at `~/.cache/huggingface/token` on the originating machine; cross-machine, the user provides.
- Anthropic Opus 4.7 + Claude Code SDK or Anthropic Console — primary planning + code review at maximum reasoning effort.
- OpenAI GPT-5+ at xhigh reasoning — primary heavy-code generator.
- Perplexity Pro / Gemini Advanced — stuck-point and innovation deep research. Use specifically for the open license verifications (BioTRY commercial, EF-UniKP / UniKP commercial-use, RFdiffusion3 Foundry from South Africa), the SBOL-as-audit-trail-shape question, and the cell-free TX-TL adapter API audit.
- LangGraph + Prefect + Parsl as a reference orchestration stack. The handover does not lock you to it.
- BoTorch + Ax + GPyTorch for the L5 substrate (qNEHVI multi-objective + qMFKG multi-fidelity + GO-CBED causal OED). The kernel choice over discrete ZPE-encoded inputs is a synthesis pressure-test point — the synthesis suggests Hamming-distance kernel as cleanest match.
- RFdiffusion3 + Baker catalytic motif scaffolding + MACE-OFF + ESMFold + ProDy for the Unknown Enzyme Generative Sub-Pipeline (all Class A; RFdiffusion3 needs RosettaCommons Foundry enrolment verification).
- Combined Master Tool Selection Tables in Report 1 §6 (complete Class A/B/C/D/E stack summary) and Report 2 §1.4 (four-column license decomposition) — the canonical L1 → L7 tool roster.

## Where the PRD lands and what comes next

Commit `PRD.md` to the top level of `Zer0pa/Synthetic-Biology`. Push to GitHub. After the PRD is final, write `HANDOFF-TO-OVERNIGHT-EXECUTOR.md` describing what the next role inherits, what they produce, and the constraints / authorities they operate under. Mirror the structure of this document.

The user will then trigger the overnight execution on a separate Runpod-bound machine using a startup prompt analogous to `ORCHESTRATOR-STARTUP-PROMPT.md`.

## Success criteria

- A PRD that the overnight executor can decompose into parallel sub-streams without further user input.
- Every interface contract locked. Every falsifier specified. Every acceptance gate measurable.
- A clear MVP first-deliverable (HMOs or the orchestrator's chosen alternative) with three named seeds and pre-registered acceptance thresholds and a target publishable paper or first-paying-customer engagement.
- The operator-override on cross-workstream substrate sharing carried through every artifact (no shared ZPE, no shared MFMO, no shared MACE service, no Cross-Pipeline Gym Flywheel).
- The BioTRY commercial license verification, EF-UniKP / UniKP commercial-use confirmation, RFdiffusion3 Foundry status, SBOL-audit-trail-shape, and cell-free TX-TL adapter API audits resolved or escalated to the user as strategic.
- A clear plug-replaceability test that proves the architecture survives the next four frontier-model releases.
- Open questions explicitly listed so the user can innovate on the strategic ones without re-reading everything (Pipeline 4 of 6 mapping question is one explicit open question).
- No cross-workstream substrate dependency.

## What you should pressure-test before locking the PRD

The synthesis agent committed to several positions that you should pressure-test with your fresh eyes:

- **Is the falsification-driven Bayesian active-inference loop reframe the right architectural primitive?** The synthesis argues yes (it subsumes variational principle + active inference + LDBT + ZPE in one loop). You may have a stronger frame.
- **Is HMOs the right MVP wedge?** The synthesis argues yes (GRAS, *E. coli* iML1515 well-tooled, tractable pathway lengths, multi-customer market). You may have a stronger frame.
- **Are 2'-FL / 3'-SL / a novel sialylated HMO the right three-named-system seed test?** Or a different triple (e.g., LNT / LNnT / a fucosylated-sialyl-Lewis-X-shaped trisaccharide)?
- **Is the cell-free TX-TL adapter Phase 0 (rapid Build-Test substrate per LDBT) or Phase 2 (deferred behind in-cell DBTL)?** The synthesis leans Phase 0 if any wet-lab integration is planned in v1.
- **Does the unknown-enzyme generative sub-pipeline (RFdiffusion3 + Baker) ship in v1 or v1.1?** And if v1, what fraction of HMO-pathway candidates will trigger it (likely <5% for HMOs since HMO biosynthetic enzymes are well-known)?
- **What is the audit-trail shape — SBOL3 + Pydantic JSON + LangGraph DAG record + sha256 hash chain?** Or different? The synthesis recommends SBOL3-attested.
- **Is BioTRY commercial-license verification a v1 blocker (per Report 2 §5.4 Ready-for-PRD checklist) or a parked-for-customer item with a synthetic-baseline fallback?**
- **Is the closed-loop dossier mode (DBTL rounds with CRO results posting back) v1 or v1.1?** Single-shot is simpler; closed-loop is the active-inference completion.
- **What is the Synthetic-Biology-equivalent of Health's PubMed-baseline harness?** A literature-titer baseline against which the engine's prediction is scored? The synthesis suggests the BioTRY corpus (>52,000 TRY entries) is the obvious candidate, contingent on commercial license.
- **What is the GP kernel choice over discrete ZPE-encoded inputs?** Hamming-distance kernel (synthesis recommendation) vs continuous embedding then Matérn vs categorical-product kernel.

These are pressure-test points, not pre-baked answers. Take them or override them with reasoning.
