# Zer0pa Synthetic Biology — Pipeline 4 of 6

Canonical home for the Zer0pa Synthetic Biology / Metabolic Pathway
Engineering work stream. Multi-agent handoff: synthesis → orchestrator
→ overnight executor → Runpod migration. **GitHub is the source of truth
across machines; HF (Architect-Prime) is the bulk-artifact mirror.**

## Boundary

Research infrastructure for in silico synthetic biology / metabolic pathway engineering. Outputs are research artifacts — predicted pathways, predicted KPIs, candidate genetic modification specifications. No regulatory certification claims. No clinical or human-subject use. No environmental release of GMOs. No biocontainment-level claims (the pipeline does not commission BSL-2/3 work). No human gene drive or eugenic application. Defence / weapons / dual-use bio applications excluded under operator policy.

## Status

| Stage | Status | Author |
|---|---|---|
| Synthesis (fresh-eyes pass on the briefs) | done | Synthesis agent (Claude Opus 4.7, 2026-05-01) |
| Orchestrator PRD v1.0 | done | Synbio orchestrator (Claude Opus 4.7, 2026-05-01) |
| Overnight executor (CPU/Mac structural waves) | **done — see [FINAL-REPORT.md](FINAL-REPORT.md)** | Overnight executor (Claude Opus 4.7, 2026-05-01) |
| Runpod cutover | pending | See [RUNPOD-READINESS.md](RUNPOD-READINESS.md) |

## What got built

The overnight executor produced:

- **Boundary discipline.** [BOUNDARY.md](BOUNDARY.md), [src/zer0pa_synbio/boundary.py](src/zer0pa_synbio/boundary.py), and a `f000_boundary_violation` falsifier check the boundary block hash on every envelope.
- **UniversalLayerEnvelope (synbio v0.1).** [src/zer0pa_synbio/envelope.py](src/zer0pa_synbio/envelope.py) — Pydantic v2 model with canonical-JSON sha256, BoundaryGate, stub-cannot-claim-scientific-validity, L6-requires-SBOL3-attestation, Class C/D/E require `audit/license_grants/` URI.
- **23 falsifiers** ([audit/falsifiers.yaml](audit/falsifiers.yaml)) with 23 working CPU implementations ([src/zer0pa_synbio/falsifiers/checks.py](src/zer0pa_synbio/falsifiers/checks.py)) and import-time coverage assertion. Three-tier hierarchy (A=fast, B=medium, C=heavy) per PRD §5.1.
- **30 source manifests** under [audit/source_manifests/](audit/source_manifests/) — Class A/B/C/D/E breakdown including hard exclusions (BKMS-react, KEGG bulk, ATLAS), parked items (BioTRY, UniKP, DeNovoDNA v2), and three quantum-slot BlockedSourceManifest entries. License-class enforcement is wired into the envelope validator.
- **Knowledge graph schema.** [kg/schema.cypher](kg/schema.cypher) (constraints + indexes), [kg/nodes.csv](kg/nodes.csv) (34 node labels), [kg/edges.csv](kg/edges.csv) (30 edge types), and [src/zer0pa_synbio/kg/__init__.py](src/zer0pa_synbio/kg/__init__.py) (GraphML + Cypher + RDF/Turtle export).
- **Synbio Audit-Trail Spec v0.1.** [docs/synbio-audit-trail-v0.1-spec.md](docs/synbio-audit-trail-v0.1-spec.md) — Zer0pa-published standard (CC BY 4.0): SBOL3 + PROV-O extension + Pydantic schemas + LangGraph DAG + sha256 hash chain + closed-loop semantics + tier-based sovereignty + GPL subprocess isolation pattern.
- **26 layer adapters L1→L7.** All envelope-correct, all stubs honour `scientific_valid=False`, license-class enforced. L1 ZPE adapter does real SELFIES parsing + 20-bit deterministic ZPE words + 1280-d hash-derived (unit-norm) ESM-2 placeholder embedding. L6 produces SBOL3-attested GMS via `pysbol3`. L6_BUILD ships three cell-free TX-TL adapters (Stub / Strateos myTXTL dry-run / Emerald PURExpress dry-run). L7 dossier with sha256 hash chain.
- **REST stubs (PRD §17): 10 FastAPI endpoints + /health.** Each instantiates the corresponding adapter in `gpu_rest_stub` mode and returns the envelope JSON.
- **Plug-replaceability harness** ([src/zer0pa_synbio/plug_replaceability/__init__.py](src/zer0pa_synbio/plug_replaceability/__init__.py)) with documented `RUNTIME_VARIABLE_FIELDS` (`envelope_id`, `run_id`, `provenance.created_at`, `provenance.git_sha`, `provenance.prov_o_jsonld`, `backend.execution_mode`, `backend.tool_version`).
- **HMO seed evidence triple.** [validation/hmo-seed-evidence/](validation/hmo-seed-evidence/) — 2'-FL (10-envelope chain), 3'-SL (11-envelope chain with L4.5), DSLNT (11-envelope chain with L4.5 fully_novel). Each seed has `acceptance.yaml` (pre-registered thresholds), `dossier.json`, `envelope_chain.json`, `kg.graphml`, `threshold_check.yaml`, `RESULT.md`.
- **PathGym scaffold** ([src/zer0pa_synbio/pathgym/__init__.py](src/zer0pa_synbio/pathgym/__init__.py)) with deterministic `tuple_id` and Tier-1/2/3 sovereignty enforcement.
- **Audit writer** ([src/zer0pa_synbio/audit/__init__.py](src/zer0pa_synbio/audit/__init__.py)) — JSONL append + DuckDB query layer per campaign.
- **CLI** ([src/zer0pa_synbio/cli/__main__.py](src/zer0pa_synbio/cli/__main__.py)) — `synbio status`, `synbio falsifiers list/run`, `synbio hmo run <seed>`, `synbio audit verify`.
- **Test suite — 117 tests, all green.**
  - 21 contract tests (boundary block, envelope invariants, license-class enforcement)
  - 5 L1 ZPE integration tests
  - 38 Wave 11 cutover-invariance tests (httpx.MockTransport)
  - 53 Wave 10 falsification-wave tests (one clean-pass + one deliberate-trigger per falsifier)

## What is NOT yet built (deferred to Runpod / next-wave)

See [NEXT-WAVE-PLAN.md](NEXT-WAVE-PLAN.md) and [RUNPOD-READINESS.md](RUNPOD-READINESS.md).

- Wave 4 — CEKM training (10-20 GPU-hours, A100/H100 80 GB).
- Wave 5 — RFdiffusion3 + MACE-OFF + ESMFold real inference.
- Wave 5 — L1 ESM-2 batched real embeddings.
- Wave 5 — L3 BioNavi / DeepRetro real inference.
- Wave 9 — full numerical HMO triple under `scientific_valid=True`.
- Wave 2 — full LIRC corpus build via SPARQL (Rhea + MetaNetX + BiGG + ModelSEED + BRENDA bulk core).
- Real BoTorch + qNEHVI + qMFKG with Hamming-distance kernel (currently a scipy-backed deterministic Pareto sort).
- Real eQuilibrator MDF (CPU-feasible; needs ~100 MB cache download).
- Wet-lab Phase 2 dispatch (triple-gated; never on the cutover path).

## Quick start

```bash
git clone https://github.com/Zer0pa/Synthetic-Biology
cd Synthetic-Biology
python3.13 -m venv .venv && source .venv/bin/activate
pip install -e .[chem,fba,sbol,tda,ml,dev]
pytest -q
synbio status
synbio falsifiers list
python validation/hmo-seed-evidence/run_seed.py --seed 2pFL
```

## Read order for the next agent

1. [BOUNDARY.md](BOUNDARY.md) — the binding boundary block.
2. [PRD.md](PRD.md) — the controlling spec (orchestrator's output, locked decisions).
3. [FINAL-REPORT.md](FINAL-REPORT.md) — what the overnight executor built and what failed.
4. [HANDOFF-FROM-OVERNIGHT-EXECUTOR.md](HANDOFF-FROM-OVERNIGHT-EXECUTOR.md) — what the next role inherits.
5. [RUNPOD-READINESS.md](RUNPOD-READINESS.md) — the Runpod cutover procedure + invariance proof.
6. [NEXT-WAVE-PLAN.md](NEXT-WAVE-PLAN.md) — open work, ordered by priority.
7. [docs/synbio-audit-trail-v0.1-spec.md](docs/synbio-audit-trail-v0.1-spec.md) — the published Zer0pa standard.
8. [RESISTANCE.md](RESISTANCE.md) — anti-corruption discipline; binding meta-protocol.
9. [MODUS-OPERANDI.md](MODUS-OPERANDI.md) — the multi-agent role chain.

## Cross-workstream principle (deliberate)

This workstream runs in parallel with `Zer0pa/Health`, `Zer0pa/Materials`,
and `Zer0pa/Energy`. Each workstream is built end-to-end as an
independent pipeline. **No substrate is shared at runtime.** Fork-and-own
is required: copy the pattern, reimplement inside Synthetic Biology.
The research-agent's three cross-workstream substrate-sharing
recommendations (Shared Infrastructure Layer, Cross-Pipeline Gym
Flywheel, single SE(3) MACE service) are captured-and-overridden per
operator policy. See [MODUS-OPERANDI.md](MODUS-OPERANDI.md) § Operator
refinements.

## Provenance

- Initial commit: 2026-05-01.
- Synthesis agent: Claude Opus 4.7 (1M context), 2026-05-01.
- Synbio orchestrator (PRD v1.0 author): Claude Opus 4.7, 2026-05-01.
- Overnight executor (this commit set): Claude Opus 4.7 (1M context), 2026-05-01.
- Next agent: Runpod-bound CEKM trainer + L4.5 inference + full HMO triple numerical run.
