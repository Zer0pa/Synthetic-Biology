# Research Agent Handover Note — Synthetic Biology Pipeline 4

**From:** Research agent (Architect Prime / Zer0pa Science Intelligence Platform)
**To:** Synthesis agent
**Date:** 2026-04-30
**Pipeline:** 4 of 6 — Synthetic Biology / Metabolic Pathway Engineering
**Source documents:**
- `01-full-technology-landscape.md` (Report 1, v1.0, 30 April 2026)
- `02-corrections-and-architecture.md` (Report 2, v2.0, 30 April 2026)

## Boundary

Research infrastructure for in silico synthetic biology / metabolic pathway engineering. Outputs are research artifacts (predicted pathways, predicted KPIs, candidate genetic modification specifications). No regulatory certification claims. No clinical or human-subject use. No environmental release of GMOs. No biocontainment-level claims (the pipeline does not commission BSL-2/3 work). No human gene drive or eugenic application.

## What the reports gave the synthesis agent

The two Synthetic Biology reports are the most architecturally mature in the Zer0pa Science Intelligence Platform series. **Report 2 introduced four things that prior pairs (Drug Process Dev report, Materials Science Report 2, the earlier landscape passes) did not have**:

1. **Four-column license decomposition audit** — every major resource decomposed into software/code, data/content, model weights, and API/service terms, each independently classified A/B/C/D/E.
2. **LDBT paradigm inversion** — Learn-Design-Build-Test (Clark-ElSayed et al., *Nature Communications* 2025) replaces canonical DBTL by front-loading the ML learning phase and using cell-free TX-TL platforms as the rapid Build-Test substrate, enabling megascale data generation.
3. **Causal OED node** — GO-CBED (Goal-Oriented Causal Bayesian Experimental Design, ICLR 2025) elevated to Tier 1 architecture-critical, sitting between the BoTorch optimisation layer and the Host Engineering layer to choose the next wet-lab experiment by maximum information gain.
4. **PathGym flywheel** — a Zer0pa-built DBTL benchmark equivalent to ProteinGym for pathway-level optimisation. Each pipeline run generates one annotated training point; the benchmark grows with use.

Each of these four contributions is retroactively applicable to the prior workstreams. The Drug Process Dev report and the Materials Science report were written without them.

## Five structural observations the research agent contributes

Beyond what the two source briefs encode, the research agent surfaces five cross-cutting observations for the synthesis agent's fresh-eyes pass.

### 1. The Shared Infrastructure Layer

No single report specifies it, but the same components recur across all four pipelines that have been researched (Drug Discovery, Drug Process Dev, Materials Science, Synthetic Biology):

- ZPE adapter (SELFIES interface)
- MFMO (multi-fidelity BoTorch acquisition)
- LangGraph + Prefect + Parsl orchestration substrate
- Pydantic v2 dossier factory
- GPT-4.1 Mini Phase 0 literature extraction
- MACE fine-tuning service (SE(3)-equivariant interatomic potentials)
- TxGemma 27B reasoning layer

If PRD agents write independently without this being named, Zer0pa builds four parallel implementations of the same components. **The research agent's recommendation: commission a Platform Core specification before dispatching any PRD.**

### 2. The Variational Principle as the Spine

VQE, CALPHAD Gibbs minimisation, MDF eQuilibrator, BoTorch acquisition function, PBPK objective function — all instances of one principle on different functional spaces. The Materials Science Report 2's information geometry observation (ESPEI MCMC navigates the Fisher information manifold) applies to every GP surrogate in every pipeline. **Natural gradient acquisition functions over ZPE-encoded design spaces are a genuine research contribution available from Zer0pa's existing information theory background.**

### 3. Active Inference as the Unifying Frame

The entire pipeline architecture is a hierarchical active inference agent:
- **ZPE** is the generative prior.
- **NOSES** (or its equivalent metabolic knowledge layer) is semantic memory.
- **Generative candidates** are predictions.
- **BoTorch** is the policy.
- **The dossier validation sequence** is the optimal epistemic action set.

This is not metaphor — it is the formal basis for why the pipeline is self-improving and why the validation sequence is necessary.

### 4. The Cross-Pipeline Gym Flywheel

PathGym (Synthetic Biology) should have counterparts:
- **CandidateGym** (Drug Discovery)
- **CompositionGym** (Materials Science)
- **FormulationGym** (Drug Process Development)
- **ElectrochemGym** (Energy)

Together they form the compounding data asset that trains ZPE at the platform level. Each client engagement generates a training point. **The moat is not any model — it is the annotated cross-domain corpus no competitor can replicate.**

### 5. The SE(3) Transfer Bridge Is Operational Now

One MACE fine-tuning service, typed as an API, serves Materials Science, Drug Discovery, and Synthetic Biology. 100–500 DFT configurations and 1–4 GPU-hours per system are sufficient. **The PRD for Materials Science should specify this as a shared service; the others reference it as a dependency.**

## Note for the synthesis agent

Observations 1, 4, and 5 propose explicit cross-workstream substrate sharing. The research agent recommends them as architectural improvements. The operator's parallel-exploration principle (`MODUS-OPERANDI.md` § Parallel-exploration principle) has previously rejected analogous proposals in the Materials and Energy synthesis passes. The synthesis agent is expected to capture these recommendations faithfully and apply the operator override per pattern. Observations 2 and 3 are within-workstream architectural framings and are permitted.

## Provenance

- Research agent: Perplexity / Zer0pa Architect Prime composite, 2026-04-30.
- This handover note: written by the research agent on 2026-04-30, transcribed verbatim into the synthesis agent's source-briefs by the synthesis agent on 2026-05-01.
- Source briefs: `01-full-technology-landscape.md` (1,663 lines), `02-corrections-and-architecture.md` (750 lines).
- Next role: synthesis agent (writes `synthesis/01-fresh-eyes-on-synbio-briefs.md` and `HANDOFF-TO-ORCHESTRATOR.md`).
