# L1 — ZPE / Input encoding brief

**Adapter:** `zer0pa_synbio.adapters.l1_zpe.L1ZPEAdapter`
**Layer:** L1 · v0.1 · references PRD §6.1
**Status:** structural complete; ESM-2 CPU stub; full GPU embedding deferred (Wave 5).

## Boundary

Research infrastructure for in silico synthetic biology / metabolic pathway engineering. Outputs are research artifacts — predicted pathways, predicted KPIs, candidate genetic modification specifications. No regulatory certification claims. No clinical or human-subject use. No environmental release of GMOs. No biocontainment-level claims (the pipeline does not commission BSL-2/3 work). No human gene drive or eugenic application. Defence / weapons / dual-use bio applications excluded under operator policy.

## Purpose

Encode the (target compound, host organism) input pair into:

- A 20-bit-per-token deterministic ZPE word envelope over the SELFIES tokens of the target.
- A 1280-dimensional ESM-2 protein context embedding (host CDS-derived; in stub mode, hash-derived deterministic + L2-normalised).
- A `gem_handle` string referring to the host organism's GEM (default: `iML1515` for *E. coli*).

## Inputs

```yaml
input_payload:
  target_compound:
    selfies: str        # SELFIES encoding (Apache-2.0 selfies>=2.1)
    inchi_key: str      # canonical InChIKey
  host_organism:
    taxonomy_id: int
    refseq_genome_accession: str
    gem_id: str
```

## Outputs

```yaml
output_payload:
  zpe_version: "zpe.v0.1"
  zpe_word_envelope: list[int]       # 20-bit values, one per SELFIES token
  esm2_embedding: list[float]        # length 1280; unit-norm
  gem_handle: str
  embedding_provenance:
    method: hash_derived_stub | esm2_runpod
    scientific_valid: bool           # True only on Runpod backend
    dim: 1280
```

## Tools

- `selfies` (Apache 2.0) — SELFIES tokenisation; `audit/source_manifests/selfies.yaml`
- `RDKit` (BSD 3-Clause) — SMILES validation; `audit/source_manifests/rdkit.yaml`
- ESM-2 weights (MIT) — protein context embedding; `audit/source_manifests/esm2.yaml`. Hash-derived deterministic vector in stub mode.

## Falsifiers in scope

- `f001_invalid_selfies` (Tier A, fail) — invalid SELFIES rejected at L1 entry.
- `f018_license_drift` (Tier C, fail) — fires if the embedding falls back to a non-permissive source.

## Plug-replaceability

The 20-bit ZPE word envelope is deterministic across `local_cpu`, `gpu_rest_stub`, `runpod_rest`. The hash-derived stub embedding is also deterministic, ensuring `compare_envelopes()` (PRD §4.5) finds zero non-runtime differences between stub and (eventual) real ESM-2 backend output for the SAME input.

## Open questions

- Should the ZPE word width be 20 bits or larger? PRD §6.1 spec is 20-bit deterministic per token; alternative 24-bit or 32-bit may reduce collisions on long SELFIES strings (>10⁵ tokens). Defer until ZPE collision analysis is run on a corpus slice.

## Tests

- `tests/integration/test_l1_zpe.py` — 5 tests (real lactose SELFIES + 20-bit word generation + 1280-d unit-norm embedding + deterministic envelope_id).
