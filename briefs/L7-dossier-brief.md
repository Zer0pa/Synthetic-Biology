# L7 — Output dossier generation brief

**Adapter:** `L7DossierAdapter`
**Layer:** L7 · v0.1 · references PRD §6.11
**Status:** complete; sha256 hash chain reconstructs cleanly through Pydantic round-trip; verified by `synbio audit verify`.

## Boundary

Research infrastructure for in silico synthetic biology / metabolic pathway engineering. Outputs are research artifacts — predicted pathways, predicted KPIs, candidate genetic modification specifications. No regulatory certification claims. No clinical or human-subject use. No environmental release of GMOs. No biocontainment-level claims (the pipeline does not commission BSL-2/3 work). No human gene drive or eugenic application. Defence / weapons / dual-use bio applications excluded under operator policy.

## Purpose

Emit the final research artifact: Pydantic v2-validated dossier; SBOL3-attested; PROV-O-anchored; sha256-hash-chained across the canonical fields. **Always carries `advisory_only=True` by default** for the HMO triple (PRD §3.2 DSLNT row requires it explicitly).

## Hash chain (Audit-Trail Spec v0.1 §6)

```
chain = []
chain.append(L1.envelope_id)
chain.append(L2.envelope_id)
chain.append(L3.envelope_id)
chain.append(L3_5.envelope_id)
chain.append(L4.envelope_id)
chain.append(L4_5.envelope_id) if novelty triggered it
chain.append(L5.envelope_id)
chain.append(L5_OED.envelope_id)
chain.append(L6.envelope_id)
chain.append(L6_BUILD.envelope_id)  # one per round
chain.append("sbol3:" + sha256(open(sbol3_uri).read()))
chain.append("prov:" + sha256(provenance.prov_o_jsonld))
chain.append("dossier:" + sha256(canonical_json(dossier_minus_self_hash)))
```

The verifier strips the last element, re-canonicalizes, and confirms the recomputed sha256 matches. All 3 HMO seed dossiers reconstruct cleanly under `synbio audit verify hmo_seed_<seed>`.

## Closed-loop variant (v1 default)

`dbtl_round > 0` triggers the round-N+1 emission:
1. `CellFreeTXTLObservation` envelopes (Phase 0 stub or Phase 2 wet-lab) post back to L5.
2. BoTorch surrogate updates with the new observation.
3. L5_OED re-runs to compute the new validation sequence.
4. Round-N+1 dossier emits with refined ranking + new experiments.
5. `sha256_hash_chain` includes both round-N's hash and the new envelopes.

## Tools

- Pydantic v2 (MIT, Class A) — typed validation
- LangGraph (MIT, Class A) — DAG record (skeleton)
- Chroma (MIT, Class A) — vector store for L7 RAG (skeleton)
- PubMed E-utilities + Wiley API — fair-use literature references; no full-text redistribution

## Falsifiers in scope

- Every dossier passes the full Tier-A/B/C falsifier sweep (PRD §5.4).
- Missing falsifier evidence fails the dossier closed.
- `f000_boundary_violation` on every envelope.

## Outputs

`Dossier` (synbio.dossier.v0.1):

```yaml
boundary: <verbatim block>
dossier_id: dossier_<seed>_round_0
dbtl_round: 0
target_compound_inchi_key: ...
host_organism: {taxonomy_id, refseq_genome_accession, gem_id}
ranked_pathway_set_envelope_id, gms_envelope_id, cftxtl_observation_envelope_ids: [...]
kpi_predictions: [{name, unit, distribution, p05, p50, p95, contributors: [layer ids]}]
validation_sequence: {schema_version, ordered_experiments, go_cbed_objective, posterior_uncertainty_kl_reduction_target}
falsifier_summary: [...]
cross_model_disagreement_summary: [...]
early_warning_summary: [...]
literature_refs: [{title, doi, pubmed_id, license_class, quote (≤15 words)}]
sbol_attestation_uri, prov_o_chain_uri
sha256_hash_chain: [...]   # ends with "dossier:<sha256>"
advisory_only: true
consumer_recommendation: human_cro | strateos_api | emerald_api | cellfree_txtl_stub | wetlab_phase2
```

## Plug-replaceability

The dossier is consumer-mode polymorphic:
- Single-shot human-readable: markdown + Pydantic JSON
- Cloud-lab API: REST endpoint shape
- Cell-free TX-TL (LDBT): queued-task graph

Same Pydantic schema; rendering shape varies.
