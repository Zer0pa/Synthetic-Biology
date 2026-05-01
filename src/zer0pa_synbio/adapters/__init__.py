"""Adapter base classes.

Every concrete adapter (L1 ZPE, L2 LIRC, L3 RetroPath3, etc.) emits a
`UniversalLayerEnvelope` and routes its raw tool output through the envelope
discipline. Tool-native objects must not cross layer boundaries; the
adapter is the boundary.

Hierarchy:

    Adapter (abstract)
    ├── LayerAdapter (binds to a Layer enum; sets backend metadata)
    │   ├── L1ZPEAdapter
    │   ├── L2LIRCAdapter
    │   ├── L3RetroPath3Adapter
    │   ├── L3NovoStoic2Adapter
    │   ├── L3BioNaviAdapter (gpu_rest_stub)
    │   ├── L3DeepRetroAdapter (gpu_rest_stub)
    │   ├── L3_5RankingGateAdapter
    │   ├── L4FBAAdapter
    │   ├── L4KineticsAdapter (gpu_rest_stub)
    │   ├── L4ThermoAdapter
    │   ├── L4_5RFdiffusion3Adapter (gpu_rest_stub)
    │   ├── L5MFMOAdapter
    │   ├── L5OEDAdapter
    │   ├── L6HostEngineeringAdapter
    │   ├── L6BuildCellFreeStubAdapter
    │   ├── L6BuildStrateosAdapter
    │   ├── L6BuildEmeraldAdapter
    │   └── L7DossierAdapter
"""

from __future__ import annotations

import hashlib
import uuid
from abc import ABC, abstractmethod
from typing import Any

from zer0pa_synbio.boundary import BOUNDARY_BLOCK
from zer0pa_synbio.envelope import (
    Backend,
    ContributorTag,
    Domain,
    ExecutionMode,
    Falsification,
    GateStatus,
    Inputs,
    Layer,
    LicenseClass,
    Outputs,
    Provenance,
    Reference,
    RunMode,
    Uncertainty,
    UncertaintyDistribution,
    UniversalLayerEnvelope,
    canonical_json,
    compute_envelope_id,
    now_iso,
)


def _hash(payload: Any) -> str:
    return hashlib.sha256(canonical_json(payload)).hexdigest()


class Adapter(ABC):
    """Abstract base for all adapters."""

    layer: Layer
    adapter_name: str
    tool_name: str
    tool_version: str
    license_class: LicenseClass
    license_evidence_uri: str

    def __init__(
        self,
        execution_mode: ExecutionMode = ExecutionMode.local_cpu,
        run_mode: RunMode = RunMode.engineering_stub,
        agent_id: str = "zer0pa_overnight_executor",
        model_id: str = "claude-opus-4-7",
        git_sha: str = "0" * 40,
    ):
        self.execution_mode = execution_mode
        self.run_mode = run_mode
        self.agent_id = agent_id
        self.model_id = model_id
        self.git_sha = git_sha

    @abstractmethod
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
        """Execute the layer's logic and return a UniversalLayerEnvelope."""
        raise NotImplementedError

    # ─── helpers ───────────────────────────────────────────────────────

    def _make_envelope(
        self,
        *,
        campaign_id: str,
        domain: Domain,
        organism: int,
        gem_id: str,
        input_payload: dict[str, Any],
        output_payload: dict[str, Any],
        uncertainty: Uncertainty | None = None,
        falsification: Falsification | None = None,
        run_id: uuid.UUID | None = None,
        input_refs: list[Reference] | None = None,
        output_refs: list[Reference] | None = None,
        sbol_uri: str | None = None,
        prov_o_jsonld: str | None = None,
        scientific_valid_override: bool | None = None,
    ) -> UniversalLayerEnvelope:
        rid = run_id or uuid.uuid4()
        backend = Backend(
            adapter=self.adapter_name,
            tool=self.tool_name,
            tool_version=self.tool_version,
            execution_mode=self.execution_mode,
            license_class=self.license_class,
            license_evidence_uri=self.license_evidence_uri,
        )

        # Default scientific_valid: True only for `scientific` mode + non-stub backend.
        is_stub = (
            self.run_mode in (RunMode.engineering_stub, RunMode.replay)
            or self.execution_mode == ExecutionMode.gpu_rest_stub
        )
        default_sv = self.run_mode == RunMode.scientific and not is_stub
        sv = scientific_valid_override if scientific_valid_override is not None else default_sv
        # Stubs cannot claim SV — Pydantic will enforce, but we honour here too.
        if is_stub:
            sv = False

        falsification = falsification or Falsification(
            gate_status=GateStatus.pass_,
            scientific_valid=sv,
            boundary_check_passed=True,
        )

        provenance = Provenance(
            agent_id=self.agent_id,
            model_id=self.model_id,
            git_sha=self.git_sha,
            created_at=now_iso(),
            input_hash=_hash(input_payload),
            output_hash=_hash(output_payload),
            config_hash=_hash(
                {
                    "adapter": self.adapter_name,
                    "tool": self.tool_name,
                    "tool_version": self.tool_version,
                    "execution_mode": self.execution_mode.value,
                    "license_class": self.license_class.value,
                }
            ),
            artifact_hashes=[],
            source_refs=[self.license_evidence_uri],
            sbol_uri=sbol_uri,
            prov_o_jsonld=prov_o_jsonld
            or self._build_prov_o(rid, input_payload, output_payload),
        )

        env = UniversalLayerEnvelope(
            boundary=BOUNDARY_BLOCK,
            envelope_id="sha256:placeholder",
            campaign_id=campaign_id,
            run_id=rid,
            layer=self.layer,
            domain=domain,
            organism=organism,
            gem_id=gem_id,
            mode=self.run_mode,
            backend=backend,
            inputs=Inputs(refs=input_refs or [], payload=input_payload),
            outputs=Outputs(refs=output_refs or [], payload=output_payload),
            uncertainty=uncertainty or Uncertainty(distribution=UncertaintyDistribution.none),
            falsification=falsification,
            provenance=provenance,
        )
        return env.model_copy(update={"envelope_id": compute_envelope_id(env)})

    def _build_prov_o(
        self,
        run_id: uuid.UUID,
        input_payload: dict[str, Any],
        output_payload: dict[str, Any],
    ) -> str:
        """Minimal PROV-O JSON-LD block. Conformant to the Zer0pa Synbio
        Audit-Trail Spec v0.1 § PROV-O extension."""
        import json

        return json.dumps(
            {
                "@context": {
                    "prov": "http://www.w3.org/ns/prov#",
                    "synbio": "https://zer0pa.ai/synbio/audit-trail/v0.1/",
                },
                "@graph": [
                    {
                        "@id": f"synbio:activity/{run_id}",
                        "@type": ["prov:Activity", "synbio:Layer"],
                        "synbio:layer": self.layer.value,
                    },
                    {
                        "@id": f"synbio:agent/{self.adapter_name}",
                        "@type": ["prov:Agent", "synbio:Adapter"],
                        "synbio:adapterName": self.adapter_name,
                        "synbio:tool": self.tool_name,
                        "synbio:toolVersion": self.tool_version,
                    },
                    {
                        "@id": f"synbio:input/{_hash(input_payload)[:12]}",
                        "@type": ["prov:Entity", "synbio:Envelope"],
                    },
                    {
                        "@id": f"synbio:output/{_hash(output_payload)[:12]}",
                        "@type": ["prov:Entity", "synbio:Envelope"],
                    },
                    {
                        "@id": f"synbio:activity/{run_id}",
                        "prov:wasAssociatedWith": {"@id": f"synbio:agent/{self.adapter_name}"},
                        "prov:used": {"@id": f"synbio:input/{_hash(input_payload)[:12]}"},
                        "synbio:layerOutputsFrom": {
                            "@id": f"synbio:output/{_hash(output_payload)[:12]}"
                        },
                    },
                ],
            },
            sort_keys=True,
            separators=(",", ":"),
        )


class LayerAdapter(Adapter):
    """Adapter bound to a layer. Subclasses must set class attributes:
    `layer`, `adapter_name`, `tool_name`, `tool_version`, `license_class`,
    `license_evidence_uri`."""


__all__ = ["Adapter", "LayerAdapter", "_hash"]
