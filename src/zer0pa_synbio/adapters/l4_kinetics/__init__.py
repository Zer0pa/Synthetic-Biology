"""L4C kinetics ensemble adapters (gpu_rest_stub by default).

Per PRD §6.5 L4C: DLKcat + CatPred + TurNuP + CEKM. UniKP/EF-UniKP
excluded from v1 ensemble until LICENSE verified per audit/source_manifests/unikp_PARKED.yaml.
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


def _stub_kinetics_payload(model_name: str, enzyme_uniprot: str | None) -> dict[str, Any]:
    """Canned shape-correct kinetics output."""
    base = {"DLKcat": 12.4, "CatPred": 11.7, "TurNuP": 13.1, "CEKM": 12.9}
    base_km = {"DLKcat": 0.42, "CatPred": 0.38, "TurNuP": 0.47, "CEKM": 0.41}
    return {
        "schema_version": "synbio.kinetics_prediction.v0.1",
        "enzyme_uniprot_id": enzyme_uniprot,
        "kcat_per_s": base.get(model_name, 12.5),
        "km_mM": base_km.get(model_name, 0.4),
        "ci90_kcat_lower": base.get(model_name, 12.5) * 0.85,
        "ci90_kcat_upper": base.get(model_name, 12.5) * 1.15,
        "model": model_name,
        "stub_mode": True,
    }


class L4DLKcatAdapter(LayerAdapter):
    layer = Layer.L4
    adapter_name = "L4DLKcatAdapter"
    tool_name = "dlkcat"
    tool_version = "dlkcat==1.0.0-stub"
    license_class = LicenseClass.A
    license_evidence_uri = "audit/source_manifests/brenda.yaml"

    def __init__(self, **kwargs):
        kwargs.setdefault("execution_mode", ExecutionMode.gpu_rest_stub)
        super().__init__(**kwargs)

    def run(
        self, *, campaign_id, domain, organism, gem_id, input_payload, run_id=None
    ) -> UniversalLayerEnvelope:
        enzyme = input_payload.get("enzyme_uniprot_id")
        return self._make_envelope(
            campaign_id=campaign_id,
            domain=domain,
            organism=organism,
            gem_id=gem_id,
            input_payload=input_payload,
            output_payload=_stub_kinetics_payload("DLKcat", enzyme),
            run_id=run_id,
        )


class L4CatPredAdapter(LayerAdapter):
    layer = Layer.L4
    adapter_name = "L4CatPredAdapter"
    tool_name = "catpred"
    tool_version = "catpred==1.0.0-stub"
    license_class = LicenseClass.A
    license_evidence_uri = "audit/source_manifests/brenda.yaml"

    def __init__(self, **kwargs):
        kwargs.setdefault("execution_mode", ExecutionMode.gpu_rest_stub)
        super().__init__(**kwargs)

    def run(
        self, *, campaign_id, domain, organism, gem_id, input_payload, run_id=None
    ) -> UniversalLayerEnvelope:
        enzyme = input_payload.get("enzyme_uniprot_id")
        return self._make_envelope(
            campaign_id=campaign_id,
            domain=domain,
            organism=organism,
            gem_id=gem_id,
            input_payload=input_payload,
            output_payload=_stub_kinetics_payload("CatPred", enzyme),
            run_id=run_id,
        )


class L4TurNuPAdapter(LayerAdapter):
    layer = Layer.L4
    adapter_name = "L4TurNuPAdapter"
    tool_name = "turnup"
    tool_version = "turnup==1.0.0-stub"
    license_class = LicenseClass.A
    license_evidence_uri = "audit/source_manifests/brenda.yaml"

    def __init__(self, **kwargs):
        kwargs.setdefault("execution_mode", ExecutionMode.gpu_rest_stub)
        super().__init__(**kwargs)

    def run(
        self, *, campaign_id, domain, organism, gem_id, input_payload, run_id=None
    ) -> UniversalLayerEnvelope:
        enzyme = input_payload.get("enzyme_uniprot_id")
        return self._make_envelope(
            campaign_id=campaign_id,
            domain=domain,
            organism=organism,
            gem_id=gem_id,
            input_payload=input_payload,
            output_payload=_stub_kinetics_payload("TurNuP", enzyme),
            run_id=run_id,
        )


class L4CEKMAdapter(LayerAdapter):
    """Zer0pa-owned Conditional Enzyme Kinetics Model.

    CPU-side prototype here; full Runpod-trained weights gated under
    `Architect-Prime/synbio-cekm-v0.1` per PRD §12.
    """

    layer = Layer.L4
    adapter_name = "L4CEKMAdapter"
    tool_name = "cekm_zer0pa"
    tool_version = "cekm==0.1.0-cpu-prototype"
    license_class = LicenseClass.A
    license_evidence_uri = "audit/source_manifests/brenda.yaml"

    def __init__(self, **kwargs):
        kwargs.setdefault("execution_mode", ExecutionMode.gpu_rest_stub)
        super().__init__(**kwargs)

    def run(
        self, *, campaign_id, domain, organism, gem_id, input_payload, run_id=None
    ) -> UniversalLayerEnvelope:
        enzyme = input_payload.get("enzyme_uniprot_id")
        payload = _stub_kinetics_payload("CEKM", enzyme)
        payload["calibration"] = {
            "held_out_partition_coverage": None,  # populated post-Runpod training
            "tier_alpha_calibration": None,
            "tier_beta_calibration": None,
            "tier_gamma_calibration": None,
        }
        return self._make_envelope(
            campaign_id=campaign_id,
            domain=domain,
            organism=organism,
            gem_id=gem_id,
            input_payload=input_payload,
            output_payload=payload,
            run_id=run_id,
        )


__all__ = ["L4DLKcatAdapter", "L4CatPredAdapter", "L4TurNuPAdapter", "L4CEKMAdapter"]
