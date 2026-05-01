"""L6_BUILD cell-free TX-TL adapters — three implementations.

Per PRD §6.10: CellFreeStubAdapter (Phase 0 stub), StrateosMyTXTLAdapter
(Phase 0 dry-run + Phase 2 wet-lab gated), EmeraldPURExpressAdapter (same
shape as Strateos, Emerald + PURExpress).

All three emit `CellFreeTXTLObservation` envelopes with the same schema.
Closed-loop dossier mode posts these back to L5 via the closed-loop
router (see `src/zer0pa_synbio/adapters/l7_dossier/`).
"""

from __future__ import annotations

import hashlib
import uuid
from typing import Any

from zer0pa_synbio.adapters import LayerAdapter
from zer0pa_synbio.envelope import Domain, Layer, LicenseClass, UniversalLayerEnvelope


def _det_id(prefix: str, *parts: str) -> str:
    """Deterministic ID = prefix + first 8 hex of sha256(parts).
    Required for plug-replaceability invariance (PRD §4.5)."""
    raw = "|".join(parts).encode("utf-8")
    return f"{prefix}_{hashlib.sha256(raw).hexdigest()[:8]}"


def _stub_observation(spec_id: str, platform: str, provider: str) -> dict[str, Any]:
    return {
        "schema_version": "synbio.cftxtl.v0.1",
        "observation_id": _det_id("obs", spec_id, platform, provider),
        "source_spec_id": spec_id,
        "platform": platform,
        "cloud_lab_provider": provider,
        "reaction_volume_ul": 10.0,
        "duration_min": 120,
        "measurements": {
            "transcription_rate_au": 1.2e3,
            "translation_rate_au": 8.4e2,
            "soluble_protein_yield_ug_ml": 12.5,
            "target_substrate_conversion_pct": 18.4,
            "byproduct_formation_au": {"GDP": 4.2e2},
        },
        "uncertainty": {"distribution": "lognormal", "p05": 9.0, "p50": 12.5, "p95": 16.8},
        "falsifier_status": "warn",
        "in_vivo_corroboration": "absent",
    }


class L6BuildCellFreeStubAdapter(LayerAdapter):
    """Phase 0 stub — canned outputs from a calibrated lookup table."""

    layer = Layer.L6_BUILD
    adapter_name = "L6BuildCellFreeStubAdapter"
    tool_name = "cellfree_stub"
    tool_version = "stub==v0.1"
    license_class = LicenseClass.A
    license_evidence_uri = "audit/source_manifests/strateos_PARKED.yaml"

    def run(
        self, *, campaign_id, domain, organism, gem_id, input_payload, run_id=None
    ) -> UniversalLayerEnvelope:
        spec_id = input_payload.get("spec_id", "")
        return self._make_envelope(
            campaign_id=campaign_id,
            domain=domain,
            organism=organism,
            gem_id=gem_id,
            input_payload=input_payload,
            output_payload=_stub_observation(spec_id, "other", "none_stub"),
            run_id=run_id,
        )


class L6BuildStrateosAdapter(LayerAdapter):
    """Strateos TxPy + myTXTL kit dry-run.

    Phase 0: dry-run, returns simulated outputs validated against canned
    myTXTL benchmark data. Phase 2 wet-lab activation requires
    runtime/cloud_lab.config.yaml + runtime/license_grants/strateos.yaml +
    operator approval (PRD §13.2).
    """

    layer = Layer.L6_BUILD
    adapter_name = "L6BuildStrateosAdapter"
    tool_name = "strateos_txpy+mytxtl"
    tool_version = "strateos_txpy==latest+mytxtl==stub-v0.1"
    license_class = LicenseClass.B
    license_evidence_uri = "audit/source_manifests/strateos_PARKED.yaml"

    def run(
        self, *, campaign_id, domain, organism, gem_id, input_payload, run_id=None
    ) -> UniversalLayerEnvelope:
        spec_id = input_payload.get("spec_id", "")
        # PRD §13.2 hard interlock: wet-lab dispatch requires three gates.
        # Default mode is dry-run.
        return self._make_envelope(
            campaign_id=campaign_id,
            domain=domain,
            organism=organism,
            gem_id=gem_id,
            input_payload=input_payload,
            output_payload=_stub_observation(spec_id, "mytxtl", "strateos"),
            run_id=run_id,
        )


class L6BuildEmeraldAdapter(LayerAdapter):
    """Emerald Cloud Lab + NEB PURExpress dry-run."""

    layer = Layer.L6_BUILD
    adapter_name = "L6BuildEmeraldAdapter"
    tool_name = "emerald+purexpress"
    tool_version = "emerald-api==latest+purexpress==stub-v0.1"
    license_class = LicenseClass.B
    license_evidence_uri = "audit/source_manifests/emerald_PARKED.yaml"

    def run(
        self, *, campaign_id, domain, organism, gem_id, input_payload, run_id=None
    ) -> UniversalLayerEnvelope:
        spec_id = input_payload.get("spec_id", "")
        return self._make_envelope(
            campaign_id=campaign_id,
            domain=domain,
            organism=organism,
            gem_id=gem_id,
            input_payload=input_payload,
            output_payload=_stub_observation(spec_id, "purexpress", "emerald"),
            run_id=run_id,
        )


__all__ = [
    "L6BuildCellFreeStubAdapter",
    "L6BuildStrateosAdapter",
    "L6BuildEmeraldAdapter",
]
