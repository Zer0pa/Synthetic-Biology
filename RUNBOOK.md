# RUNBOOK — Synthetic Biology Pipeline 4

> Operator-facing runbook for the Zer0pa Synbio repo. The file is short by
> design — most procedural content lives in `docs/`, `EXECUTION-STATE.md`,
> and `HANDOFF-FROM-OVERNIGHT-EXECUTOR.md`.

## Boundary

Research infrastructure for in silico synthetic biology / metabolic pathway engineering. Outputs are research artifacts — predicted pathways, predicted KPIs, candidate genetic modification specifications. No regulatory certification claims. No clinical or human-subject use. No environmental release of GMOs. No biocontainment-level claims (the pipeline does not commission BSL-2/3 work). No human gene drive or eugenic application. Defence / weapons / dual-use bio applications excluded under operator policy.

## Quick start (local Mac CPU)

```bash
git clone https://github.com/Zer0pa/Synthetic-Biology
cd Synthetic-Biology
python3.13 -m venv .venv
source .venv/bin/activate
pip install -e .[chem,fba,sbol,tda,ml,dev]
pytest -q
synbio status
synbio falsifiers list
python validation/hmo-seed-evidence/run_seed.py --seed 2pFL
```

The CLI subcommands are listed in [src/zer0pa_synbio/cli/__main__.py](src/zer0pa_synbio/cli/__main__.py).

## Environment configuration

Per `PRD.md` §16, the canonical config flags are env vars; defaults ship
in `runtime/` (skeleton). The currently-load-bearing flags:

```bash
SYNBIO_BOUNDARY_GATE=strict         # always strict; never override
SYNBIO_AUDIT_REQUIRED=true
SYNBIO_LICENSE_GATE=strict
SYNBIO_EXECUTION_PROFILE=local_cpu_first
SYNBIO_ARTIFACT_MODE=manifest_only
SYNBIO_ALLOW_BULK_LOCAL=false
SYNBIO_HF_USER=Architect-Prime
SYNBIO_CLOSED_LOOP_DEFAULT=true     # closed-loop is v1 default
SYNBIO_BIOTRY_INCLUDED=false
SYNBIO_DENOVODNA_RBS_V2=false
SYNBIO_UNIKP_INCLUDED=false
SYNBIO_KEGG_BULK=false              # never on
SYNBIO_BKMS_REACT=false             # never on
SYNBIO_ATLAS_OF_BIOCHEMISTRY=false  # never on for training; URL refs only
```

## License-gated activations (off by default)

Activate one of these only with the corresponding `audit/license_grants/<name>.yaml`:

| Component | Off-state | On-state requires |
|---|---|---|
| BioTRY corpus inclusion (CEKM v2+) | excluded from training | `runtime/license_grants/biotry.yaml` + commercial license |
| De Novo DNA RBS v2 commercial | OSTIR fallback | `runtime/license_grants/denovodna.yaml` + API credentials |
| Strateos myTXTL **wet-lab** | dry-run only | `runtime/cloud_lab.config.yaml` + `runtime/license_grants/strateos.yaml` + operator approval |
| Emerald PURExpress **wet-lab** | dry-run only | `runtime/cloud_lab.config.yaml` + `runtime/license_grants/emerald.yaml` + operator approval |
| UniKP / EF-UniKP kinetics member | excluded from ensemble | LICENSE verified + `audit/source_manifests/unikp.yaml` updated with SPDX |

## Wet-lab activation gate (PRD §6.10, §13)

The L6_BUILD adapters (`L6BuildStrateosAdapter`, `L6BuildEmeraldAdapter`)
default to **dry-run** and never dispatch real wet-lab without the
triple gate:

1. `runtime/cloud_lab.config.yaml` populated with provider credentials.
2. `runtime/license_grants/<provider>.yaml` present.
3. Explicit operator approval (signed off in the same file).

The hard interlock is enforced in the adapter before any external API
call. Falsifier `f020_txtl_observation_without_in_vivo` flags every
dry-run output that drives a host-engineering decision.

## HMO scientific validation triple

The validation triple is the engine's correctness probe. Pre-registered
acceptance thresholds are committed under
`validation/hmo-seed-evidence/<seed>/acceptance.yaml`:

| Seed | Status | Pre-registered acceptance |
|---|---|---|
| 2'-FL | known-good | predicted titer within ±25% of literature median (~5 g/L); CEKM kcat within ±0.5 log of BRENDA; MDF ≥ 1 kJ/mol |
| 3'-SL | known-borderline | 90% CI covers literature; CMP-Neu5Ac identified as dominant uncertainty; CMP-Neu5Ac regeneration proposed as highest-IG intervention |
| DSLNT | novel | ≥ 3 distinct retrosynthesis routes; ≥ 1 Tier-2 unknown-enzyme classification; advisory_only=True; calibrated uncertainty band |

Stub-mode runs produce structurally complete envelope chains; full
numerical evaluation gated on Runpod (Wave 4 CEKM training + Wave 5
RFdiffusion3/MACE-OFF/ESMFold inference). See `RUNPOD-READINESS.md`.

## Audit verification

```bash
synbio audit verify <campaign_id>
```

Currently a stub that confirms envelopes.jsonl exists and counts entries.
Full conformance per `docs/synbio-audit-trail-v0.1-spec.md` §10 is wired
in v0.2.

## Test suite layout

- `tests/contract/` — schema / envelope / boundary / license-class tests
- `tests/integration/` — L1 ZPE adapter end-to-end tests
- `tests/falsification/` — Wave 10 deliberate-trigger tests (one per falsifier)
- `tests/runpod_cutover/` — Wave 11 httpx.MockTransport invariance tests
- `tests/plug_replaceability/` — backend-swap invariance (extends Wave 11)
- `tests/golden/` — golden fixtures (added per future engagement)
- `tests/hmo_seed/` — HMO seed-specific tests (extends Wave 9)

## Hugging Face mirror

Bulk artifacts go to private Hugging Face under user `Architect-Prime`
per PRD §14. Token: `~/.cache/huggingface/token` on the originating Mac;
`HF_TOKEN` env var on Runpod.

Manifests for HF artifacts live in `audit/source_manifests/<id>.yaml`
with `hf_mirror_uri` populated; the manifest is the source of truth
even if the HF push hasn't completed yet.

## Reporting blockers

Per PRD §1.3 + §15: log blockers in `EXECUTION-STATE.md` as
`BLOCKED:<component>:<reason>:<workaround>`. Surface them in
`FINAL-REPORT.md` and `HANDOFF-FROM-OVERNIGHT-EXECUTOR.md`. Never stop
the pipeline mid-wave for a recoverable blocker.
