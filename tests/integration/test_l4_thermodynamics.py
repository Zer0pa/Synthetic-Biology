"""L4B thermodynamics integration tests — real eQuilibrator MDF.

These tests exercise the real ``equilibrator-api`` +
``equilibrator-pathway`` code path. They require:

1. ``equilibrator-api`` and ``equilibrator-pathway`` installed.
2. The eQuilibrator compound cache resolved on disk (~1.3 GB pulled
   on first ``ComponentContribution()`` call).

If the cache is not resolvable in the test environment the real-path
tests skip cleanly. The stub-path test never skips.
"""

from __future__ import annotations

import math

import pytest

from zer0pa_synbio.adapters.l4_thermodynamics import L4EQuilibratorAdapter
from zer0pa_synbio.envelope import Domain, RunMode


@pytest.fixture(scope="module")
def cc():
    """Load eQuilibrator's ComponentContribution once per module.

    Skips the real-path tests if the cache cannot be resolved.
    """
    try:
        cc = L4EQuilibratorAdapter._component_contribution()
    except Exception as exc:  # pragma: no cover
        pytest.skip(f"eQuilibrator cache not resolvable: {exc}")
    if cc is None:
        pytest.skip("eQuilibrator cache not resolvable in this environment")
    return cc


def _run(payload, run_mode=RunMode.scientific):
    return L4EQuilibratorAdapter(run_mode=run_mode).run(
        campaign_id="test_l4_thermo",
        domain=Domain.hmo,
        organism=562,
        gem_id="iML1515",
        input_payload=payload,
    )


def test_stub_mode_when_no_eq_reactions():
    """No eq_reactions → stub mode with synthetic ΔG summary."""
    env = _run({"steps": [{"delta_g_kj_mol": -10.0}, {"delta_g_kj_mol": -5.0}]})
    assert env.layer.value == "L4"
    payload = env.outputs.payload
    assert payload["stub_mode"] is True
    assert payload["delta_g_total_kj_mol"] == -15.0


def test_real_dg_prime_pgi(cc):
    """Single-reaction PGI (g6p ↔ f6p) — known ΔG'° ≈ +2.6 kJ/mol.

    Single-reaction MDF LP triggers an upstream cvxpy/pint indexing bug
    in equilibrator-pathway 0.7.0; the adapter detects this and falls
    back to the worst-case ΔrG'° proxy. ΔrG'° itself is computed via
    the component-contribution method and is the canonical literature
    value (~+2.6 kJ/mol for PGI).
    """
    env = _run({"eq_reactions": ["bigg.metabolite:g6p = bigg.metabolite:f6p"]})
    payload = env.outputs.payload
    assert payload["stub_mode"] is False
    assert payload["mdf_solver_status"] == "skipped_lt_2_reactions"
    step = payload["delta_g_per_step"][0]
    assert step["balanced"] is True
    assert math.isclose(step["delta_g_prime_kj_mol"], 2.64, abs_tol=0.5)
    # Worst-case proxy for 1-rxn: MDF = -ΔG'° = -2.64.
    assert math.isclose(payload["mdf_score_kj_mol"], -2.64, abs_tol=0.5)


def test_real_mdf_two_step_pathway(cc):
    """Two-reaction pathway (PGI then PMI) — both balanced with positive
    standard ΔG'°. MDF LP runs on ≥ 2 reactions and produces a real
    score plus per-compound optimal concentrations."""
    env = _run(
        {
            "eq_reactions": [
                "bigg.metabolite:g6p = bigg.metabolite:f6p",
                "bigg.metabolite:f6p = bigg.metabolite:man6p",
            ]
        }
    )
    payload = env.outputs.payload
    assert payload["stub_mode"] is False
    assert payload["mdf_solver_status"] == "ok"
    assert len(payload["delta_g_per_step"]) == 2
    for step in payload["delta_g_per_step"]:
        assert step["balanced"] is True
    # MDF should be finite (not +/-inf, not NaN).
    s = payload["mdf_score_kj_mol"]
    assert math.isfinite(s)
    # Per-compound concentrations should be reported.
    assert len(payload["compound_concentrations"]) >= 2
    cmpd_ids = {c["compound_id"] for c in payload["compound_concentrations"]}
    assert any("Glucose" in cid for cid in cmpd_ids)


def test_real_mdf_unparseable_reaction(cc):
    """A reaction string that fails to parse should not crash the
    adapter; it should be reported in delta_g_per_step with an error
    field, and the rest of the pathway should still be analysed."""
    env = _run(
        {
            "eq_reactions": [
                "bigg.metabolite:g6p = bigg.metabolite:f6p",
                "bigg.metabolite:NOT_A_REAL_COMPOUND = bigg.metabolite:f6p",
            ]
        }
    )
    payload = env.outputs.payload
    # At least one step should have a real ΔG'° value.
    have_value = [s for s in payload["delta_g_per_step"] if "delta_g_prime_kj_mol" in s]
    assert len(have_value) >= 1
    # And one should report an error.
    have_error = [s for s in payload["delta_g_per_step"] if "error" in s]
    assert len(have_error) >= 1
    assert payload["stub_mode"] is False  # used_real_eq because at least one parsed
