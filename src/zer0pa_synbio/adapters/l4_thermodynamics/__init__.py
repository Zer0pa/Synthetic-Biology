"""L4B thermodynamics — eQuilibrator MDF + PyTFA.

Per PRD §6.5 L4B. CPU-side (no GPU needed).

Two execution paths:

1. **Real path** (when ``input_payload['eq_reactions']`` is provided AND
   the eQuilibrator cache loads): parse each reaction via
   ``ComponentContribution.parse_reaction_formula``, build a
   ``ThermodynamicModel``, run ``mdf_analysis()``. Returns the real
   MDF score (max-min driving force, kJ/mol) optimised over feasible
   concentration bounds (default 1 µM – 10 mM, eQuilibrator's standard
   physiological window), per-reaction ΔrG'°, and per-compound optimal
   concentrations. Sets ``stub_mode=False``.

2. **Stub path** (no ``eq_reactions`` or eQuilibrator unavailable):
   summarise the synthetic per-step ΔG values from the input payload.
   Sets ``stub_mode=True``.

The real path uses ``equilibrator_pathway.ThermodynamicModel`` (MIT
license; transitive dependency of ``equilibrator-api``). MDF is a
linear program (cvxpy / scs / clarabel) that maximises the smallest
driving force across the pathway, subject to box constraints on
metabolite concentrations and the standard ΔG'° estimates from the
component-contribution method.
"""

from __future__ import annotations

from typing import Any

from zer0pa_synbio.adapters import LayerAdapter
from zer0pa_synbio.envelope import Domain, Layer, LicenseClass, UniversalLayerEnvelope


class L4EQuilibratorAdapter(LayerAdapter):
    layer = Layer.L4
    adapter_name = "L4EQuilibratorAdapter"
    tool_name = "equilibrator-api+equilibrator-pathway"
    tool_version = "equilibrator-api==0.7.0;equilibrator-pathway==0.7.0"
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

    @staticmethod
    def _build_thermo_model(cc: Any, eq_reactions: list[str]):
        """Parse reactions and construct a ThermodynamicModel.

        Returns ``(model, parsed)`` where ``model`` is a
        ``ThermodynamicModel`` (or None on failure) and ``parsed`` is a
        list of ``(rxn_id, reaction_obj, error_or_None)`` entries.
        """
        import numpy as np
        import pandas as pd
        import equilibrator_api as eq
        from equilibrator_pathway import ThermodynamicModel

        parsed: list[tuple[str, Any, str | None]] = []
        rxn_objs: dict[str, Any] = {}
        compounds: list[Any] = []
        compound_keys: list[str] = []

        for i, rxn_str in enumerate(eq_reactions):
            rid = f"rxn{i+1}"
            try:
                r = cc.parse_reaction_formula(rxn_str)
                rxn_objs[rid] = r
                parsed.append((rid, r, None))
                for cmpd, _coeff in r.sparse.items():
                    key = cmpd.get_common_name() or cmpd.id
                    if key not in compound_keys:
                        compound_keys.append(key)
                        compounds.append(cmpd)
            except Exception as exc:
                parsed.append((rid, None, str(exc)))

        if not rxn_objs:
            return None, parsed

        # Stoichiometric matrix (rows = compounds, cols = reactions).
        compound_dict: dict[str, Any] = {}
        for c in compounds:
            key = c.get_common_name() or c.id
            compound_dict[key] = c
        S_data: dict[str, dict[str, float]] = {}
        for rid, r in rxn_objs.items():
            S_data[rid] = {}
            for c in compounds:
                key = c.get_common_name() or c.id
                S_data[rid][key] = float(r.sparse.get(c, 0))
        S = pd.DataFrame(S_data)

        # Default unit fluxes (mM/s); MDF score is invariant under
        # positive scaling of fluxes.
        fluxes = eq.Q_(np.ones(len(rxn_objs)), "mM/s")

        try:
            model = ThermodynamicModel(
                S=S,
                compound_dict=compound_dict,
                reaction_dict=rxn_objs,
                fluxes=fluxes,
                comp_contrib=cc,
            )
        except Exception:
            return None, parsed
        return model, parsed

    def run(
        self, *, campaign_id, domain, organism, gem_id, input_payload, run_id=None
    ) -> UniversalLayerEnvelope:
        steps = input_payload.get("steps", [])
        eq_reactions: list[str] = input_payload.get("eq_reactions", [])

        delta_g_per_step: list[dict[str, Any]] = []
        delta_g_total = 0.0
        delta_g_var_total = 0.0
        used_real_eq = False
        mdf_score = 0.0
        compound_concentrations: list[dict[str, Any]] = []
        mdf_solver_status: str = "not_attempted"

        cc = self._component_contribution() if eq_reactions else None
        if cc is not None and eq_reactions:
            # Per-reaction ΔrG'° (always available even if MDF LP fails).
            for rxn_str in eq_reactions:
                try:
                    r = cc.parse_reaction_formula(rxn_str)
                    balanced = bool(r.is_balanced())
                    dgm = cc.standard_dg_prime(r)
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
                    delta_g_var_total += e * e
                    used_real_eq = True
                except Exception as exc:
                    delta_g_per_step.append(
                        {"reaction": rxn_str, "error": str(exc)}
                    )

            # Real MDF LP — needs ≥ 2 successfully parsed reactions.
            # equilibrator-pathway 0.7.0 has an upstream IndexError on
            # single-reaction pathways (cvxpy returns a 0-d scalar that
            # the solution constructor tries to index by [0]). For 1-rxn
            # cases we fall back to the worst-case ΔrG'° proxy.
            successful_parsed = sum(
                1 for s in delta_g_per_step if "delta_g_prime_kj_mol" in s
            )
            if successful_parsed < 2:
                mdf_solver_status = "skipped_lt_2_reactions"
                model = None
            else:
                model = None
            try:
                if successful_parsed >= 2:
                    model, _parsed = self._build_thermo_model(cc, eq_reactions)
                if model is not None:
                    sol = model.mdf_analysis()
                    mdf_score = float(sol.score)
                    mdf_solver_status = "ok"
                    # Per-compound optimal concentration (mM).
                    try:
                        # ln_conc is a numpy array (natural log of M).
                        # eQuilibrator's pathway model uses molar; convert to mM.
                        import numpy as np

                        ln_conc = np.asarray(sol.ln_conc).flatten()
                        for j, key in enumerate(model.compound_ids):
                            if j >= len(ln_conc):
                                break
                            conc_M = float(np.exp(ln_conc[j]))
                            compound_concentrations.append(
                                {
                                    "compound_id": str(key),
                                    "optimal_concentration_mM": conc_M * 1000.0,
                                    "log10_concentration_M": float(np.log10(conc_M)),
                                }
                            )
                    except Exception:
                        pass
                elif mdf_solver_status == "not_attempted":
                    mdf_solver_status = "model_construction_failed"
            except Exception as exc:
                mdf_solver_status = f"mdf_lp_error: {exc}"

        # Synthetic fallback summary (always computed for cross-check).
        synthetic_delta_g = sum(s.get("delta_g_kj_mol", 0.0) for s in steps)

        if used_real_eq and delta_g_per_step:
            # If the LP didn't run, fall back to the worst-case
            # standard-ΔG' summary as the MDF proxy.
            if mdf_solver_status != "ok":
                real_dgs = [
                    s.get("delta_g_prime_kj_mol", 0.0)
                    for s in delta_g_per_step
                    if "delta_g_prime_kj_mol" in s
                ]
                mdf_score = -max(real_dgs) if real_dgs else 0.0
            output_payload = {
                "schema_version": "synbio.thermo_mdf.v0.1",
                "mdf_score_kj_mol": mdf_score,
                "delta_g_total_kj_mol": delta_g_total,
                "delta_g_uncertainty_kj_mol": delta_g_var_total ** 0.5,
                "delta_g_per_step": delta_g_per_step,
                "compound_concentrations": compound_concentrations,
                "concentration_bounds_used": "1 uM – 10 mM (eQuilibrator default)",
                "mdf_solver_status": mdf_solver_status,
                "stub_mode": False,
                "tool": (
                    "equilibrator_pathway.ThermodynamicModel.mdf_analysis"
                    if mdf_solver_status == "ok"
                    else "equilibrator_api.ComponentContribution.standard_dg_prime"
                ),
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
