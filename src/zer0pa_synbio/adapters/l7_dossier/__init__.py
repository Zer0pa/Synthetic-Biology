"""L7 dossier factory + closed-loop router.

Per PRD §6.11: Pydantic v2 dossier; SBOL3-attested; PROV-O-anchored;
sha256-hash-chained across the canonical dossier fields. Closed-loop
mode (dbtl_round > 0) is the v1 default.
"""

from __future__ import annotations

import hashlib
import uuid
from typing import Any

from zer0pa_synbio.adapters import LayerAdapter
from zer0pa_synbio.boundary import BOUNDARY_BLOCK
from zer0pa_synbio.envelope import (
    Domain,
    Layer,
    LicenseClass,
    UniversalLayerEnvelope,
    canonical_json,
)


def _build_hash_chain(envelope_ids: list[str], sbol_sha: str | None, prov_o: str) -> list[str]:
    chain = list(envelope_ids)
    if sbol_sha:
        chain.append(f"sbol3:{sbol_sha}")
    chain.append(f"prov:{hashlib.sha256(prov_o.encode('utf-8')).hexdigest()}")
    return chain


class L7DossierAdapter(LayerAdapter):
    layer = Layer.L7
    adapter_name = "L7DossierAdapter"
    tool_name = "pydantic+langgraph+chroma"
    tool_version = "pydantic==2.13+langgraph-stub+chroma-stub"
    license_class = LicenseClass.A
    license_evidence_uri = "audit/source_manifests/metanetx.yaml"

    def run(
        self, *, campaign_id, domain, organism, gem_id, input_payload, run_id=None
    ) -> UniversalLayerEnvelope:
        ranked_envelope_id = input_payload.get("ranked_pathway_set_envelope_id", "sha256:placeholder")
        gms_envelope_id = input_payload.get("gms_envelope_id", "sha256:placeholder")
        cftxtl_ids = input_payload.get("cftxtl_observation_envelope_ids", [])
        kpi_predictions = input_payload.get("kpi_predictions", [
            {
                "name": "predicted_titer_g_l",
                "unit": "g/L",
                "distribution": "lognormal",
                "p05": 0.5, "p50": 1.2, "p95": 2.4,
                "contributors": ["L1", "L2", "L3", "L4_kinetics", "L4_fba", "L5"],
            }
        ])
        validation_sequence = input_payload.get("validation_sequence", {
            "schema_version": "synbio.validation_sequence.v0.1",
            "ordered_experiments": [],
            "go_cbed_objective": "balanced",
            "posterior_uncertainty_kl_reduction_target": 1.0,
        })
        sbol_attestation_uri = input_payload.get("sbol_attestation_uri", "")
        sbol_sha = input_payload.get("sbol_sha256", "")
        prov_o = input_payload.get("prov_o_jsonld", "{}")

        envelope_ids = [
            input_payload.get("l1_envelope_id", "sha256:l1"),
            input_payload.get("l2_envelope_id", "sha256:l2"),
            input_payload.get("l3_envelope_id", "sha256:l3"),
            input_payload.get("l3_5_envelope_id", "sha256:l3_5"),
            input_payload.get("l4_envelope_id", "sha256:l4"),
            input_payload.get("l4_5_envelope_id", "sha256:l4_5") if input_payload.get("l4_5_envelope_id") else None,
            input_payload.get("l5_envelope_id", "sha256:l5"),
            input_payload.get("l5_oed_envelope_id", "sha256:l5_oed"),
            gms_envelope_id,
            *cftxtl_ids,
        ]
        envelope_ids = [e for e in envelope_ids if e]
        chain = _build_hash_chain(envelope_ids, sbol_sha or None, prov_o)

        # Deterministic dossier_id derived from inputs — required for plug-replaceability.
        provided_id = input_payload.get("dossier_id")
        if provided_id:
            dossier_id = provided_id
        else:
            seed = f"{campaign_id}|{ranked_envelope_id}|{gms_envelope_id}|{input_payload.get('dbtl_round', 0)}"
            dossier_id = "dossier_" + hashlib.sha256(seed.encode("utf-8")).hexdigest()[:12]
        dossier = {
            "schema_version": "synbio.dossier.v0.1",
            "boundary": BOUNDARY_BLOCK,
            "dossier_id": dossier_id,
            "campaign_id": campaign_id,
            "dbtl_round": input_payload.get("dbtl_round", 0),
            "target_compound_inchi_key": input_payload.get("target_compound_inchi_key", ""),
            "host_organism": input_payload.get("host_organism", {
                "taxonomy_id": organism,
                "refseq_genome_accession": "NC_000913.3",
                "gem_id": gem_id,
            }),
            "domain": domain.value,
            "ranked_pathway_set_envelope_id": ranked_envelope_id,
            "gms_envelope_id": gms_envelope_id,
            "cftxtl_observation_envelope_ids": cftxtl_ids,
            "kpi_predictions": kpi_predictions,
            "validation_sequence": validation_sequence,
            "falsifier_summary": input_payload.get("falsifier_summary", []),
            "cross_model_disagreement_summary": input_payload.get("cross_model_disagreement_summary", []),
            "early_warning_summary": input_payload.get("early_warning_summary", []),
            "literature_refs": input_payload.get("literature_refs", []),
            "sbol_attestation_uri": sbol_attestation_uri,
            "prov_o_chain_uri": input_payload.get("prov_o_chain_uri", ""),
            "sha256_hash_chain": chain,
            "advisory_only": input_payload.get("advisory_only", True),
            "consumer_recommendation": input_payload.get("consumer_recommendation", "human_cro"),
        }
        # Self-anchor the chain. Validate the dossier dict through the
        # Pydantic Dossier model first so the on-disk shape matches what
        # the verifier reconstructs. Hash the canonical JSON of the
        # serialised model with the chain *without* the self-hash, then
        # append.
        from zer0pa_synbio.types import Dossier

        validated = Dossier.model_validate(dossier)
        canonical_pre_self = canonical_json(validated.model_dump(mode="json"))
        dossier_self_hash = hashlib.sha256(canonical_pre_self).hexdigest()
        chain.append(f"dossier:{dossier_self_hash}")
        validated = validated.model_copy(update={"sha256_hash_chain": chain})
        # Replace the dict copy that gets embedded in the envelope output
        # with the validated dump for byte-stable reconstruction.
        dossier = validated.model_dump(mode="json")

        return self._make_envelope(
            campaign_id=campaign_id,
            domain=domain,
            organism=organism,
            gem_id=gem_id,
            input_payload=input_payload,
            output_payload={"dossier": dossier},
            run_id=run_id,
            sbol_uri=sbol_attestation_uri or None,
        )


__all__ = ["L7DossierAdapter", "_build_hash_chain"]
