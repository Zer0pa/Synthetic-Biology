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

    # Class-level cache so repeated runs share the (heavy) ComponentContribution.
    _cc: Any = None

    @classmethod
    def _component_contribution(cls):
        if cls._cc is not None:
            return cls._cc
        try:
            import equilibrator_api as eq  # type: ignore[import-not-found]
        except ImportError:
            return None
        try:
            cls._cc = eq.ComponentContribution()
        except Exception:
            cls._cc = None
        return cls._cc

    def run(
        self, *, campaign_id, domain, organism, gem_id, input_payload, run_id=None
    ) -> UniversalLayerEnvelope:
        steps = input_payload.get("steps", [])
        # Optional: BiGG-style reaction strings (e.g. "bigg.metabolite:g6p = bigg.metabolite:f6p")
        eq_reactions: list[str] = input_payload.get("eq_reactions", [])

        delta_g_per_step: list[dict[str, Any]] = []
        delta_g_total = 0.0
        delta_g_uncertainty_total = 0.0
        used_real_eq = False

        cc = self._component_contribution() if eq_reactions else None
        if cc is not None and eq_reactions:
            try:
                for rxn_str in eq_reactions:
                    try:
                        r = cc.parse_reaction_formula(rxn_str)
                        balanced = bool(r.is_balanced())
                        dgm = cc.standard_dg_prime(r)
                        # dgm is a Pint Measurement: .value (kJ/mol) and .error.
                        v = float(getattr(dgm.value, "magnitude", dgm.value))
                        e = float(getattr(dgm.error, "magnitude", dgm.error))
                        delta_g_per_step.append(
                            {
                                "reaction": rxn_str,
                                "delta_g_prime_kj_mol": v,
                                "uncertainty_kj_mol": e,
                                "balanced": balanced,
                            }
                        )
                        delta_g_total += v
                        delta_g_uncertainty_total += e * e
                    except Exception as exc:
                        delta_g_per_step.append(
                            {"reaction": rxn_str, "error": str(exc)}
                        )
                used_real_eq = True
            except Exception:
                used_real_eq = False
        # Fall back to synthetic delta_g from the input steps.
        synthetic_delta_g = sum(s.get("delta_g_kj_mol", 0.0) for s in steps)

        if used_real_eq and delta_g_per_step:
            # Real MDF proxy: largest single-step ΔrG' (worst-case) — full
            # MDF requires concentration optimisation; we report the
            # standard ΔrG' summary for now.
            real_dgs = [s.get("delta_g_prime_kj_mol", 0.0) for s in delta_g_per_step if "delta_g_prime_kj_mol" in s]
            mdf = -max(real_dgs) if real_dgs else 0.0
            output_payload = {
                "schema_version": "synbio.thermo_mdf.v0.1",
                "mdf_score_kj_mol": mdf,
                "delta_g_total_kj_mol": delta_g_total,
                "delta_g_uncertainty_kj_mol": delta_g_uncertainty_total ** 0.5,
                "delta_g_per_step": delta_g_per_step,
                "concentration_bounds_used": "standard (1 mM)",
                "stub_mode": False,
                "tool": "equilibrator_api.ComponentContribution.standard_dg_prime",
            }
        else:
            mdf = abs(synthetic_delta_g) / max(1, len(steps))
            output_payload = {
                "schema_version": "synbio.thermo_mdf.v0.1",
                "mdf_score_kj_mol": mdf,
                "delta_g_total_kj_mol": synthetic_delta_g,
                "concentration_bounds_used": "(synthetic)",
                "stub_mode": True,
            }

        return self._make_envelope(
            campaign_id=campaign_id,
            domain=domain,
            organism=organism,
            gem_id=gem_id,
            input_payload=input_payload,
            output_payload=output_payload,
            run_id=run_id,
        )


__all__ = ["L4EQuilibratorAdapter"]
