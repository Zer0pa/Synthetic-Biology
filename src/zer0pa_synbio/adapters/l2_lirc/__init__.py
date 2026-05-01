"""L2 LIRC corpus adapter — local CPU only.

Per PRD §6.2: Rhea + MetaNetX + BiGG + ModelSEED + BRENDA core CC BY 4.0.
ATLAS, BKMS-react, KEGG bulk are excluded (per source manifests).

This adapter operates on the LIRC slice fixtures committed under
`fixtures/lirc/`. The full LIRC build (Wave 2) pulls SPARQL endpoints +
HF mirrors and is hours-long; here the adapter runs against the small
local slice and emits a `ReactionGraph` envelope.
"""

from __future__ import annotations

import json
import uuid
from pathlib import Path
from typing import Any

from zer0pa_synbio.adapters import LayerAdapter
from zer0pa_synbio.envelope import (
    Domain,
    ExecutionMode,
    Layer,
    LicenseClass,
    UniversalLayerEnvelope,
)


def _load_slice() -> dict[str, Any] | None:
    """Load the canonical 2'-FL/3'-SL LIRC slice from disk if present."""
    repo_root = Path(__file__).resolve().parents[4]
    slice_path = repo_root / "fixtures" / "lirc" / "2pfl_canonical.json"
    if not slice_path.exists():
        return None
    try:
        return json.loads(slice_path.read_text(encoding="utf-8"))
    except Exception:
        return None


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

        # Try the real Rhea-derived slice first; fall back to a tiny canned
        # one only if the slice file is absent.
        slice_data = _load_slice()
        if slice_data is not None:
            nodes: list[dict[str, Any]] = []
            edges: list[dict[str, Any]] = []
            seen_compounds: set[str] = set()
            for r in slice_data.get("reactions", []):
                rid = r.get("rhea_id", "")
                ec = r.get("ec", "")
                uniprot = r.get("enzyme_uniprot")
                nodes.append({"type": "Reaction", "id": rid, "ec": ec, "label": r.get("label", "")})
                if uniprot:
                    nodes.append({"type": "Enzyme", "id": uniprot, "ec": ec})
                    edges.append({"from": uniprot, "to": rid, "type": "catalyses"})
                for ck in r.get("substrate_inchi_keys", []) or []:
                    if ck not in seen_compounds:
                        nodes.append({"type": "Compound", "id": ck})
                        seen_compounds.add(ck)
                    edges.append({"from": rid, "to": ck, "type": "consumes"})
                for ck in r.get("product_inchi_keys", []) or []:
                    if ck not in seen_compounds:
                        nodes.append({"type": "Compound", "id": ck})
                        seen_compounds.add(ck)
                    edges.append({"from": rid, "to": ck, "type": "produces"})
            reaction_graph = {
                "schema_version": "synbio.reaction_graph.v0.1",
                "nodes": nodes,
                "edges": edges,
                "provenance": {
                    "lirc_slice_uri": "fixtures/lirc/2pfl_canonical.json",
                    "license_class": slice_data.get("license_class", "A"),
                    "source_manifests": slice_data.get("source_manifests", []),
                    "rhea_fetch_errors": slice_data.get("fetch_errors", []),
                    "excluded_sources_for_this_query": [
                        "atlas_of_biochemistry_BLOCKED",
                        "bkms_react_BLOCKED",
                        "kegg_bulk_BLOCKED",
                    ],
                },
                "target_inchi_key": target_inchi_key,
                "organism_gem_id": organism_gem_id,
            }
        else:
            reaction_graph = {
                "schema_version": "synbio.reaction_graph.v0.1",
                "nodes": [
                    {"type": "Compound", "id": "GUBGYTABKSRVRQ-PICCSMPSSA-N", "name": "lactose"},
                    {"type": "Compound", "id": "GFXBRIYRYYFCIA-LWNAIEPUSA-N", "name": "2-fucosyllactose"},
                    {"type": "Reaction", "id": "RHEA:14457", "ec": "2.4.1.69"},
                    {"type": "Enzyme", "id": "Q11075"},
                ],
                "edges": [
                    {"from": "RHEA:14457", "to": "GFXBRIYRYYFCIA-LWNAIEPUSA-N", "type": "produces"},
                    {"from": "RHEA:14457", "to": "GUBGYTABKSRVRQ-PICCSMPSSA-N", "type": "consumes"},
                    {"from": "Q11075", "to": "RHEA:14457", "type": "catalyses"},
                ],
                "provenance": {"lirc_slice_uri": "(canned fallback; slice file not found)"},
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
