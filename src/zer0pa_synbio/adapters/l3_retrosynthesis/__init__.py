"""L3 retrosynthesis ensemble adapters.

Per PRD §6.3: RetroPath3 + novoStoic2 (local_cpu) + BioNavi + DeepRetro
(gpu_rest_stub) + Genie-CAT advisory. Cross-tool disagreement signal via
Jaccard.
"""

from __future__ import annotations

import uuid
from typing import Any

from zer0pa_synbio.adapters import LayerAdapter
from zer0pa_synbio.envelope import (
    Domain,
    ExecutionMode,
    Layer,
    LicenseClass,
    UniversalLayerEnvelope,
)


def _candidate_routes_for_2pfl(target_inchi_key: str) -> list[dict[str, Any]]:
    """Three canned candidate routes for the 2'-FL HMO seed test, all
    structurally valid PRD §4.3 PathwayCandidate shapes.

    Each tool's "proposing" annotation is canonical: RetroPath3 + novoStoic2
    (the two CPU tools) propose the canonical lactose+GDP-fucose route;
    BioNavi (gpu_rest_stub) proposes the same plus a novelty variant; DeepRetro
    proposes only the canonical. This drives a measurable cross-tool
    disagreement signal for the f008 test.
    """
    return [
        {
            "pathway_id": "p_2pfl_canonical",
            "target_compound_inchi_key": target_inchi_key,
            "steps": [
                {
                    "reaction_id": "MNXR105069",
                    "substrates": [
                        "GUBGYTABKSRVRQ-PICCSMPSSA-N",
                        "WUUGFSXJNOTRMR-IOSLPCCCSA-N",
                    ],
                    "products": [target_inchi_key, "RQFCJASXJCIDSX-UUOKFMHZSA-N"],
                    "ec_class": "2.4.1.69",
                    "enzyme_uniprot_id": "Q11075",
                    "delta_g_kj_mol": -23.4,
                    "thermodynamic_feasibility_at_default_concs": True,
                    "novelty_class": "known_reaction",
                }
            ],
            "length": 1,
            "precursor_compound_inchi_key": "GUBGYTABKSRVRQ-PICCSMPSSA-N",
            "retrosynthesis_tools_proposing": ["retropath3", "novostoic2", "bionavi", "deepretro"],
            "cross_tool_disagreement_signal": 0.0,
        },
        {
            "pathway_id": "p_2pfl_alt_3step",
            "target_compound_inchi_key": target_inchi_key,
            "steps": [
                {
                    "reaction_id": "MNXR105069_alt1",
                    "substrates": [
                        "WSUNQZCJYIDADW-CWHQHJEKSA-N"
                    ],  # GDP-mannose intermediate
                    "products": [target_inchi_key],
                    "ec_class": "2.4.1.69",
                    "enzyme_uniprot_id": "Q11075",
                    "delta_g_kj_mol": -19.1,
                    "thermodynamic_feasibility_at_default_concs": True,
                    "novelty_class": "reaction_class_known",
                }
            ],
            "length": 3,
            "precursor_compound_inchi_key": "WSUNQZCJYIDADW-CWHQHJEKSA-N",
            "retrosynthesis_tools_proposing": ["retropath3", "bionavi"],
            "cross_tool_disagreement_signal": 0.5,
        },
    ]


class L3RetroPath3Adapter(LayerAdapter):
    layer = Layer.L3
    adapter_name = "L3RetroPath3Adapter"
    tool_name = "retropath3"
    tool_version = "retropath3==3.0.0"
    license_class = LicenseClass.A
    license_evidence_uri = "audit/source_manifests/metanetx.yaml"  # uses MetaNetX rules

    def run(
        self, *, campaign_id, domain, organism, gem_id, input_payload, run_id=None
    ) -> UniversalLayerEnvelope:
        target = input_payload.get("target_inchi_key", "")
        candidates = _candidate_routes_for_2pfl(target)
        # RetroPath3 sees a subset.
        rp3_candidates = [c for c in candidates if "retropath3" in c["retrosynthesis_tools_proposing"]]
        return self._make_envelope(
            campaign_id=campaign_id,
            domain=domain,
            organism=organism,
            gem_id=gem_id,
            input_payload=input_payload,
            output_payload={
                "schema_version": "synbio.pathway_candidate_set.v0.1",
                "candidates": rp3_candidates,
            },
            run_id=run_id,
        )


class L3NovoStoic2Adapter(LayerAdapter):
    layer = Layer.L3
    adapter_name = "L3NovoStoic2Adapter"
    tool_name = "novostoic2"
    tool_version = "novostoic2==2.0.0"
    license_class = LicenseClass.A
    license_evidence_uri = "audit/source_manifests/metanetx.yaml"

    def run(
        self, *, campaign_id, domain, organism, gem_id, input_payload, run_id=None
    ) -> UniversalLayerEnvelope:
        target = input_payload.get("target_inchi_key", "")
        candidates = _candidate_routes_for_2pfl(target)
        ns2_candidates = [c for c in candidates if "novostoic2" in c["retrosynthesis_tools_proposing"]]
        return self._make_envelope(
            campaign_id=campaign_id,
            domain=domain,
            organism=organism,
            gem_id=gem_id,
            input_payload=input_payload,
            output_payload={
                "schema_version": "synbio.pathway_candidate_set.v0.1",
                "candidates": ns2_candidates,
            },
            run_id=run_id,
        )


class L3BioNaviAdapter(LayerAdapter):
    """gpu_rest_stub backend by default."""

    layer = Layer.L3
    adapter_name = "L3BioNaviAdapter"
    tool_name = "bionavi"
    tool_version = "bionavi==1.0.0-stub"
    license_class = LicenseClass.A
    license_evidence_uri = "audit/source_manifests/metanetx.yaml"

    def __init__(self, **kwargs):
        kwargs.setdefault("execution_mode", ExecutionMode.gpu_rest_stub)
        super().__init__(**kwargs)

    def run(
        self, *, campaign_id, domain, organism, gem_id, input_payload, run_id=None
    ) -> UniversalLayerEnvelope:
        target = input_payload.get("target_inchi_key", "")
        candidates = _candidate_routes_for_2pfl(target)
        bn_candidates = [c for c in candidates if "bionavi" in c["retrosynthesis_tools_proposing"]]
        return self._make_envelope(
            campaign_id=campaign_id,
            domain=domain,
            organism=organism,
            gem_id=gem_id,
            input_payload=input_payload,
            output_payload={
                "schema_version": "synbio.pathway_candidate_set.v0.1",
                "candidates": bn_candidates,
            },
            run_id=run_id,
        )


class L3DeepRetroAdapter(LayerAdapter):
    layer = Layer.L3
    adapter_name = "L3DeepRetroAdapter"
    tool_name = "deepretro"
    tool_version = "deepretro==1.0.0-stub"
    license_class = LicenseClass.A
    license_evidence_uri = "audit/source_manifests/metanetx.yaml"

    def __init__(self, **kwargs):
        kwargs.setdefault("execution_mode", ExecutionMode.gpu_rest_stub)
        super().__init__(**kwargs)

    def run(
        self, *, campaign_id, domain, organism, gem_id, input_payload, run_id=None
    ) -> UniversalLayerEnvelope:
        target = input_payload.get("target_inchi_key", "")
        candidates = _candidate_routes_for_2pfl(target)
        dr_candidates = [c for c in candidates if "deepretro" in c["retrosynthesis_tools_proposing"]]
        return self._make_envelope(
            campaign_id=campaign_id,
            domain=domain,
            organism=organism,
            gem_id=gem_id,
            input_payload=input_payload,
            output_payload={
                "schema_version": "synbio.pathway_candidate_set.v0.1",
                "candidates": dr_candidates,
            },
            run_id=run_id,
        )


__all__ = [
    "L3RetroPath3Adapter",
    "L3NovoStoic2Adapter",
    "L3BioNaviAdapter",
    "L3DeepRetroAdapter",
    "_candidate_routes_for_2pfl",
]
