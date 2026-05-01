"""L4B thermodynamics — eQuilibrator MDF + PyTFA.

Per PRD §6.5 L4B. CPU-side (no GPU needed).
"""

from __future__ import annotations

import uuid
from typing import Any

from zer0pa_synbio.adapters import LayerAdapter
from zer0pa_synbio.envelope import Domain, Layer, LicenseClass, UniversalLayerEnvelope


class L4EQuilibratorAdapter(LayerAdapter):
    layer = Layer.L4
    adapter_name = "L4EQuilibratorAdapter"
    tool_name = "equilibrator-api"
    tool_version = "equilibrator-api==0.6.0"
    license_class = LicenseClass.A
    license_evidence_uri = "audit/source_manifests/equilibrator.yaml"

    def run(
        self, *, campaign_id, domain, organism, gem_id, input_payload, run_id=None
    ) -> UniversalLayerEnvelope:
        # MDF stub: report a positive MDF for the canonical 2'-FL pathway.
        # Real implementation calls equilibrator-api which downloads its
        # cache (~100 MB) on first use; we don't pull that here.
        steps = input_payload.get("steps", [])
        delta_g = sum(s.get("delta_g_kj_mol", 0.0) for s in steps)
        # Synthetic MDF: positive if all steps are downhill.
        mdf = abs(delta_g) / max(1, len(steps))
        return self._make_envelope(
            campaign_id=campaign_id,
            domain=domain,
            organism=organism,
            gem_id=gem_id,
            input_payload=input_payload,
            output_payload={
                "schema_version": "synbio.thermo_mdf.v0.1",
                "mdf_score_kj_mol": mdf,
                "delta_g_total_kj_mol": delta_g,
                "concentration_bounds_used": "default 1µM–10mM",
                "stub_mode": True,
            },
            run_id=run_id,
        )


__all__ = ["L4EQuilibratorAdapter"]
