"""L2 LIRC corpus adapter — local CPU only.

Per PRD §6.2: Rhea + MetaNetX + BiGG + ModelSEED + BRENDA core CC BY 4.0.
ATLAS, BKMS-react, KEGG bulk are excluded (per source manifests).

This adapter operates on the LIRC slice fixtures committed under
`fixtures/lirc/`. The full LIRC build (Wave 2) pulls SPARQL endpoints +
HF mirrors and is hours-long; here the adapter runs against the small
local slice and emits a `ReactionGraph` envelope.
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


class L2LIRCAdapter(LayerAdapter):
    layer = Layer.L2
    adapter_name = "L2LIRCAdapter"
    tool_name = "rhea+metanetx+bigg+modelseed+brenda"
    tool_version = "lirc-slice-v0.1"
    license_class = LicenseClass.A  # majority CC BY 4.0 / CC0 / MIT
    license_evidence_uri = "audit/source_manifests/metanetx.yaml"

    def run(
        self,
        *,
        campaign_id: str,
        domain: Domain,
        organism: int,
        gem_id: str,
        input_payload: dict[str, Any],
        run_id: uuid.UUID | None = None,
    ) -> UniversalLayerEnvelope:
        """Stub LIRC query.

        Returns a ReactionGraph payload shaped per PRD §6.2 with placeholder
        nodes and edges. The full implementation queries Rhea SPARQL +
        MetaNetX MNXref reconciliation + BiGG + ModelSEED + BRENDA core
        bulk slices.
        """
        target_inchi_key = input_payload.get("target_inchi_key", "")
        organism_gem_id = input_payload.get("organism_gem_id", gem_id)

        # Tiny canned ReactionGraph for the HMO seed test.
        # 2'-FL = lactose + GDP-fucose → 2'-FL + GDP (one-step from precursors).
        reaction_graph = {
            "schema_version": "synbio.reaction_graph.v0.1",
            "nodes": [
                {"type": "Compound", "id": "GUBGYTABKSRVRQ-PICCSMPSSA-N", "name": "lactose"},
                {"type": "Compound", "id": "WUUGFSXJNOTRMR-IOSLPCCCSA-N", "name": "GDP-fucose"},
                {"type": "Compound", "id": "GFXBRIYRYYFCIA-LWNAIEPUSA-N", "name": "2-fucosyllactose"},
                {"type": "Compound", "id": "RQFCJASXJCIDSX-UUOKFMHZSA-N", "name": "GDP"},
                {"type": "Reaction", "id": "MNXR105069", "name": "alpha-1,2-fucosyltransferase"},
                {"type": "Enzyme", "id": "Q11075", "name": "FutC alpha-1,2-fucosyltransferase"},
            ],
            "edges": [
                {"from": "MNXR105069", "to": "GFXBRIYRYYFCIA-LWNAIEPUSA-N", "type": "produces"},
                {"from": "MNXR105069", "to": "GUBGYTABKSRVRQ-PICCSMPSSA-N", "type": "consumes"},
                {"from": "MNXR105069", "to": "WUUGFSXJNOTRMR-IOSLPCCCSA-N", "type": "consumes"},
                {"from": "Q11075", "to": "MNXR105069", "type": "catalyses"},
            ],
            "provenance": {
                "rhea_uri": "https://www.rhea-db.org/rhea/52608",
                "metanetx_reconciliation": "MNXR105069",
                "bigg_reaction": None,
                "modelseed_reaction": None,
                "brenda_ec": "2.4.1.69",
                "lirc_slice_uri": "fixtures/lirc/2pfl_canonical.json",
                "license_class": "A",
                "excluded_sources_for_this_query": [
                    "atlas_of_biochemistry_BLOCKED",
                    "bkms_react_BLOCKED",
                    "kegg_bulk_BLOCKED",
                ],
            },
            "target_inchi_key": target_inchi_key,
            "organism_gem_id": organism_gem_id,
        }

        output_payload = {"reaction_graph": reaction_graph}

        return self._make_envelope(
            campaign_id=campaign_id,
            domain=domain,
            organism=organism,
            gem_id=gem_id,
            input_payload=input_payload,
            output_payload=output_payload,
            run_id=run_id,
        )


__all__ = ["L2LIRCAdapter"]
