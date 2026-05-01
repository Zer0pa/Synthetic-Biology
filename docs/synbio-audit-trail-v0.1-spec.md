# Zer0pa Synbio Audit-Trail Specification v0.1

**Status:** Draft for review · v0.1.0 · 2026-05-01
**Publisher:** Zer0pa (architects@zer0pa.ai)
**License:** CC BY 4.0
**Canonical URL:** https://github.com/Zer0pa/Synthetic-Biology/blob/main/docs/synbio-audit-trail-v0.1-spec.md

## Boundary

Research infrastructure for in silico synthetic biology / metabolic pathway engineering. Outputs are research artifacts — predicted pathways, predicted KPIs, candidate genetic modification specifications. No regulatory certification claims. No clinical or human-subject use. No environmental release of GMOs. No biocontainment-level claims (the pipeline does not commission BSL-2/3 work). No human gene drive or eugenic application. Defence / weapons / dual-use bio applications excluded under operator policy.

This boundary appears verbatim in every artifact governed by this spec.

## 1. Why this exists

There is no synthetic-biology equivalent of pharma's ICH M15 audit-trail
framing or materials-science's RO-Crate / RDF-PROV-O export pattern. SBOL3
describes genetic designs but does not specify a reproducibility-grade audit
chain. PROV-O describes provenance but does not encode SBOL-level genetic
detail. SynBioHub publishes designs but does not record the full LDBT loop.
DBTL practitioners ship dossiers in ad-hoc PDF + Excel formats whose state
no future agent can reconstruct.

The Zer0pa Synbio Audit-Trail Specification v0.1 closes that gap. It is the
binding contract between any Zer0pa Synthetic Biology dossier and any
downstream consumer (CRO partner, research team, regulator, customer
analytics layer, future Zer0pa workstream). It composes:

- **SBOL3** for the genetic design surface.
- **PROV-O** for the provenance graph.
- **Pydantic v2** for typed schemas.
- **LangGraph DAG records** for the layer execution chain.
- **sha256 hash chain** anchoring envelope_id → pathway_candidate_id →
  scored_pathway_id → ranked_pathway_id → gms_id → cftxtl_observation_id →
  dossier_id.

Conformance means the dossier and every supporting envelope can be
re-derived bit-identical from the committed audit log plus the source
manifests, modulo runtime/provenance fields that are explicitly allowed to
differ between stub / CPU / Runpod backends.

## 2. Scope and conformance

A Zer0pa Synbio Dossier conforms to this spec if and only if:

1. **Boundary attestation.** Every envelope and the dossier itself carry the
   canonical boundary block sha256 and the literal text. (Falsifier
   `f000_boundary_violation`.)
2. **Envelope chain.** Every layer execution emits a
   `UniversalLayerEnvelope` whose `envelope_id` is `sha256:<canonical-JSON
   of the envelope with envelope_id zeroed>`. Adjacent envelopes are linked
   via `inputs.refs[].uri` matching upstream `envelope_id`.
3. **License attestation.** Every envelope's `backend.license_class` is set;
   class C/D/E require `backend.license_evidence_uri` pointing into
   `audit/license_grants/<name>.yaml`. (Falsifier `f018_license_drift`.)
4. **Falsifier coverage.** Every layer's envelope carries falsifier results
   for at least the falsifiers declared as applicable to that layer in
   `audit/falsifiers.yaml`. Failure-tier falsifiers block downstream
   emission; warn-tier falsifiers inflate uncertainty and annotate the
   dossier.
5. **SBOL3 attestation for L6.** Every L6 envelope's payload is a
   `GeneticModificationSpec` whose `sbol3_uri` points to a local SBOL3
   document that parses via `pysbol3` strict-mode validation. Falsifier
   `f019_valid_sbol_only`.
6. **Cross-model disagreement first-class.** Wherever the pipeline runs an
   ensemble (kinetics, FBA, retrosynthesis, surrogate), a
   `CrossModelDisagreementRecord` accompanies the envelope. `fail`-status
   records block downstream emission.
7. **PROV-O JSON-LD.** Every envelope carries a `provenance.prov_o_jsonld`
   block linking `prov:Activity` (the layer execution) → `prov:Agent` (the
   adapter) → `prov:Entity` (the input/output payloads).
8. **Hash chain.** The dossier's `sha256_hash_chain` is the ordered list of
   envelope_ids and SBOL3 document hashes that contributed to it; verifying
   the chain reconstructs the dossier deterministically.
9. **No tool-native objects across layer boundaries.** Tool outputs are
   wrapped in envelopes; raw tool-native shapes never propagate.

Non-conformance is detectable by running `synbio audit verify <campaign_id>`
(CLI) or `zer0pa_synbio.audit.verify_chain(campaign_id)` (Python).

## 3. Schemas

The following Pydantic v2 schemas are normative. YAML mirrors live under
`schemas/`. Schema versions are pinned at v0.1 and bump only on breaking
change.

### 3.1 UniversalLayerEnvelope (`synbio.envelope.v0.1`)

See `src/zer0pa_synbio/envelope.py`. Required fields: `boundary`,
`envelope_id`, `campaign_id`, `run_id`, `layer`, `domain`, `organism`,
`gem_id`, `mode`, `backend`, `inputs`, `outputs`, `uncertainty`,
`falsification`, `provenance`. Cross-field invariants enforced at
construction time (BoundaryGate, stub-no-scientific-validity,
L6-requires-SBOL, license-class-grant).

### 3.2 GeneticModificationSpec (`synbio.gms.v0.1`)

See `src/zer0pa_synbio/types.py` `GeneticModificationSpec`. Structurally an
SBOL3 document; pysbol3 round-trips it through validate.

### 3.3 PathwayCandidateSet / ScoredPathwaySet / RankedPathwaySet / ValidationSequence

See `src/zer0pa_synbio/types.py`. The L3 → L4 → L5 → L5_OED data flow.

### 3.4 CellFreeTXTLObservation (`synbio.cftxtl.v0.1`)

The L6_BUILD output for the cell-free TX-TL Build-Test substrate
(LDBT paradigm).

### 3.5 CrossModelDisagreementRecord (`synbio.disagreement.v0.1`)

Forked from Energy. First-class quantity, not an after-the-fact annotation.
Never average away a failed disagreement.

### 3.6 EarlyWarningSignal (`synbio.early_warning.v0.1`)

Forked from Energy. Persistent-homology-derived; no scalar-classifier-only
warnings accepted.

### 3.7 Dossier (`synbio.dossier.v0.1`)

The L7 output. Every dossier carries the boundary verbatim, advisory_only
flag (default True), consumer_recommendation, and the hash chain.

### 3.8 ReasonerTuple (`synbio.reasoner_tuple.v0.1`)

The PathGym training point. One per pipeline run; the corpus grows per
engagement.

### 3.9 SourceManifest (`synbio.source_manifest.v0.1`)

One YAML per external source. License class A/B/C/D/E and
excluded_from_training_corpus are load-bearing fields used by falsifier
`f018_license_drift`.

## 4. PROV-O extension

The Zer0pa extension to PROV-O adds:

- `synbio:Layer` — subclass of `prov:Activity`; values L1, L2, L3, L3_5,
  L4, L4_5, L5, L5_OED, L6, L6_BUILD, L7.
- `synbio:Adapter` — subclass of `prov:Agent`; identifies the concrete
  adapter (e.g., `RetroPath3Adapter`, `CEKMAdapter`).
- `synbio:Envelope` — subclass of `prov:Entity`; links to a
  `UniversalLayerEnvelope` via `synbio:envelopeId` (sha256-prefixed hash).
- `synbio:Falsifier` — subclass of `prov:Entity`; one per falsifier result.
- `synbio:DisagreementRecord` — subclass of `prov:Entity`; one per
  cross-model disagreement record.
- `synbio:SBOLDocument` — subclass of `prov:Entity`; required for L6
  envelopes.
- `synbio:LicenseFinding` — subclass of `prov:Entity`; one per license
  decision recorded in `audit/license_grants/`.

Relations:

- `synbio:layerInputsTo` (Envelope → Layer; the envelope was input to the
  layer execution).
- `synbio:layerOutputsFrom` (Layer → Envelope; the envelope was emitted by
  the layer execution).
- `synbio:falsifiedBy` (Envelope → Falsifier).
- `synbio:disagreesWith` (Envelope → DisagreementRecord).
- `synbio:attestedBySBOL` (Envelope → SBOLDocument). Required for L6.

Triple representation: every envelope's
`provenance.prov_o_jsonld` is a JSON-LD document conforming to the
Zer0pa context (`https://zer0pa.ai/synbio/audit-trail/v0.1/context.jsonld`,
to be published with the spec).

## 5. SBOL3 attestation

Every `GeneticModificationSpec` (L6 envelope payload) is serialised as an
SBOL3 document and placed under
`audit/sbol/<spec_id>.<gms_schema_version>.sbol3.xml`. The document
includes:

- `sbol3:Component` for the host strain (taxonomy + RefSeq accession).
- `sbol3:Component` for each `Knockout`, `Knockin`, `Upregulation`,
  `Downregulation`, `CofactorBalancing`.
- `sbol3:SubComponent` for promoters, RBSes, terminators, integration
  sites, codon-optimised CDSs.
- `sbol3:Sequence` for nucleotide sequences (only when explicitly
  authorised by the customer; otherwise, sequences are referenced by
  external accession).
- `sbol3:Interaction` for each cofactor balancing or regulatory link.
- A top-level `sbol3:Description` carrying the boundary block verbatim.

The SBOL3 document is validated via `sbol3.Document.validate()` at strict
mode; if validation messages are non-empty, falsifier `f019_valid_sbol_only`
fires and the envelope is rejected.

## 6. Hash chain

The dossier's `sha256_hash_chain` is constructed as follows:

```
chain = []
for envelope_id in [
    L1.envelope_id,
    L2.envelope_id,
    L3.envelope_id,
    L3_5.envelope_id,
    L4.envelope_id,
    L4_5.envelope_id,  # optional, present only if novelty_class triggered it
    L5.envelope_id,
    L5_OED.envelope_id,
    L6.envelope_id,
    L6_BUILD.envelope_id,  # one per dry-run / wet-lab observation in the round
    L7.envelope_id,
]:
    chain.append(envelope_id)
chain.append("sbol3:" + sha256(open(sbol3_uri).read()))
chain.append("prov:" + sha256(provenance.prov_o_jsonld))
chain.append("dossier:" + sha256(canonical_json(dossier without hash_chain)))
dossier.sha256_hash_chain = chain
```

A consumer verifies a dossier by walking the chain in order, fetching each
envelope from `audit/runtime/<campaign_id>/envelopes/<envelope_id>.json`,
recomputing each envelope's canonical-JSON sha256, and confirming the chain
reconstructs.

## 7. Closed-loop semantics

In closed-loop dossier mode (`SYNBIO_CLOSED_LOOP_DEFAULT=true`, the v1
default), the dossier carries `dbtl_round: int >= 0`. Round 0 is the
initial emission. For round N > 0:

- The L6_BUILD envelope's `outputs.payload.observation_id` is appended to
  `cftxtl_observation_envelope_ids` in the round-N+1 dossier.
- The L5 BoTorch surrogate is updated in place; its envelope_id changes;
  the new ranking flows through L5_OED → L7.
- The round-N+1 dossier's `sha256_hash_chain` includes both the round-N
  dossier's hash (as an external reference) and the new L5/L5_OED/L7
  envelopes.
- The validation_sequence in the round-N+1 dossier reflects the updated
  posterior; experiments that already returned observations are removed
  from the sequence; new high-information-gain experiments are added.

This is the active-inference completion across the customer / cell-free
TX-TL boundary.

## 8. Tier-based data sovereignty

Each artifact carries a `RightsPolicy` linkage:

- **Tier-1 Customer-Confidential** — customer pathway designs, customer
  assay observations, customer-fine-tuned CEKM weights. Customer-owned,
  customer-isolated. Zer0pa keeps redacted operational provenance only.
- **Tier-2 Aggregated-Insights** — de-identified DBTL telemetry, model
  calibration deltas, cross-model disagreement aggregates. Zer0pa-shared
  pool with customer opt-out. HF private under
  `Architect-Prime/synbio-aggregated-insights-v0.1`.
- **Tier-3 Public** — LIRC corpus contributions, PathGym benchmark splits,
  Synbio Audit-Trail Spec, scientific validation triple results.
  Zer0pa-published. CC BY 4.0.

Default for new fine-tuned weights: Tier-1 customer-isolated unless
customer opts into Tier-2 sharing. Default for novel falsifier discoveries:
Tier-3 public (the field benefits; Zer0pa's moat is the corpus, not the
falsifier list). Default for cross-model disagreement aggregates: Tier-2
with customer opt-out.

A dossier's RightsPolicy is the most-restrictive tier across its
contributing envelopes.

## 9. Subprocess isolation (GPL containment)

Class C tools (GPL) are invoked via subprocess; the synbio package does not
`import` GPL modules. The standard pattern:

```python
import subprocess
out = subprocess.run(
    ["/path/to/gpl_binary", "--input", input_path, "--output", output_path],
    capture_output=True, text=True, check=True,
)
# Parse stdout/output_path; only numeric / structural results cross back.
```

The corresponding `audit/license_grants/<name>.yaml` records the
subprocess-isolation evidence (file path, isolation mechanism, granted-for
scope). The Salis Lab RBS Calculator v1.0 (GPLv3) is the canonical
reference: `audit/license_grants/salis_v1.yaml`.

## 10. Conformance test

A conforming Zer0pa Synbio Dossier passes:

```bash
synbio audit verify --campaign-id <id> --dossier <path>
```

which runs:

1. Boundary block sha256 check on dossier and every contributing envelope.
2. Envelope-chain reconstruction (every `inputs.refs[].uri` matches an
   upstream `envelope_id`).
3. License-class enforcement for every envelope.
4. Falsifier-coverage check (every layer's required falsifiers ran).
5. SBOL3 strict-mode validate on every L6 envelope.
6. Cross-model disagreement records present where ensembles ran.
7. PROV-O JSON-LD parse + Zer0pa-extension term presence.
8. Hash chain reconstruction.

The reference test runner is `tests/integration/test_audit_chain.py` (to be
added in Wave 12 once the full HMO seed evidence packet is wired).

## 11. Versioning and stability

- v0.1 is **draft for review**. Breaking changes during the v0.1 lifetime
  require ADR + changelog entry. After v0.1 freezes, subsequent versions
  follow semver (v0.2 = additive, v1.0 = first stable).
- This spec is Zer0pa's operating standard. External adopters may use it
  freely under CC BY 4.0; attribution = "Zer0pa Synbio Audit-Trail
  Specification v0.1, https://github.com/Zer0pa/Synthetic-Biology, 2026."

## 12. Provenance

- **Drafted by:** Zer0pa Overnight Executor (Claude Opus 4.7, 1M context),
  2026-05-01, from `PRD.md` § 9 (Audit trail and KG) and the synthesis
  agent's recommendation in `synthesis/01-fresh-eyes-on-synbio-briefs.md`
  § 9 (no SBOL-shaped audit-trail surface).
- **Operator policy authority:** `MODUS-OPERANDI.md` § Operator
  refinements (2026-05-01); `RESISTANCE.md`.
- **Research-agent input:** `source-briefs/02-corrections-and-architecture.md`
  § 5.1 (typed seven-layer architecture) and § 5.4 (twelve canonical
  dossier fields).
