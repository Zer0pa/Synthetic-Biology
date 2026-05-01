"""L4.5 unknown-enzyme generative sub-pipeline.

Per PRD §6.6: triggered only when f009 or f010 fires. Three-tier novelty
classification with RFdiffusion3 + Baker catalytic motif scaffolding +
MACE-OFF + ESMFold + ProDy + eQuilibrator + Genie-CAT.

All four GPU-bound tools are stubbed here; ProDy + eQuilibrator are
CPU-runnable and will be live once equilibrator-api cache is pulled
(deferred per PRD §15 Wave 5).
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


class L4_5RFdiffusion3Adapter(LayerAdapter):
    layer = Layer.L4_5
    adapter_name = "L4_5RFdiffusion3Adapter"
    tool_name = "rfdiffusion3"
    tool_version = "rfdiffusion3==v0.1-foundry"
    license_class = LicenseClass.A
    license_evidence_uri = "audit/source_manifests/rfdiffusion3.yaml"

    def __init__(self, **kwargs):
        kwargs.setdefault("execution_mode", ExecutionMode.gpu_rest_stub)
        super().__init__(**kwargs)

    def run(
        self, *, campaign_id, domain, organism, gem_id, input_payload, run_id=None
    ) -> UniversalLayerEnvelope:
        return self._make_envelope(
            campaign_id=campaign_id,
            domain=domain,
            organism=organism,
            gem_id=gem_id,
            input_payload=input_payload,
            output_payload={
                "schema_version": "synbio.rfdiffusion3_scaffold.v0.1",
                "structures": [],
                "motif_rmsd_angstrom": None,
                "tier": input_payload.get("tier", "tier_2"),
                "stub_mode": True,
            },
            run_id=run_id,
        )


class L4_5MACEOFFAdapter(LayerAdapter):
    layer = Layer.L4_5
    adapter_name = "L4_5MACEOFFAdapter"
    tool_name = "mace-off"
    tool_version = "mace-off==v0.1-stub"
    license_class = LicenseClass.A
    license_evidence_uri = "audit/source_manifests/rfdiffusion3.yaml"

    def __init__(self, **kwargs):
        kwargs.setdefault("execution_mode", ExecutionMode.gpu_rest_stub)
        super().__init__(**kwargs)

    def run(
        self, *, campaign_id, domain, organism, gem_id, input_payload, run_id=None
    ) -> UniversalLayerEnvelope:
        return self._make_envelope(
            campaign_id=campaign_id,
            domain=domain,
            organism=organism,
            gem_id=gem_id,
            input_payload=input_payload,
            output_payload={
                "schema_version": "synbio.mace_off_binding.v0.1",
                "binding_energy_kj_mol": -45.2,
                "reference_range_kj_mol": {"lo": -200.0, "hi": 0.0},
                "stub_mode": True,
            },
            run_id=run_id,
        )


class L4_5ESMFoldAdapter(LayerAdapter):
    layer = Layer.L4_5
    adapter_name = "L4_5ESMFoldAdapter"
    tool_name = "esmfold"
    tool_version = "esmfold==v1-stub"
    license_class = LicenseClass.A
    license_evidence_uri = "audit/source_manifests/esm2.yaml"

    def __init__(self, **kwargs):
        kwargs.setdefault("execution_mode", ExecutionMode.gpu_rest_stub)
        super().__init__(**kwargs)

    def run(
        self, *, campaign_id, domain, organism, gem_id, input_payload, run_id=None
    ) -> UniversalLayerEnvelope:
        return self._make_envelope(
            campaign_id=campaign_id,
            domain=domain,
            organism=organism,
            gem_id=gem_id,
            input_payload=input_payload,
            output_payload={
                "schema_version": "synbio.esmfold_prediction.v0.1",
                "structure_pdb": None,
                "plddt_mean": None,
                "stub_mode": True,
            },
            run_id=run_id,
        )


__all__ = ["L4_5RFdiffusion3Adapter", "L4_5MACEOFFAdapter", "L4_5ESMFoldAdapter"]
