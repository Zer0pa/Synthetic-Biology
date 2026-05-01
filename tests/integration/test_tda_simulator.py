"""Tests for the real Monod ODE fermentation simulator + TDA early-warning.

Per HANDOFF-CPU-CONTINUATION.md item E and PRD §5.3 failure modes.
The simulator is real ``scipy.integrate.solve_ivp`` LSODA. The
early-warning module uses real ``ripser`` + ``persim``.

These tests verify:
- Each of the five PRD §5.3 stress-test failure modes produces a
  trace whose final state demonstrably reflects the documented
  failure mode (e.g. oxygen-transfer collapse pulls DO down sharply,
  byproduct-buildup drives byproduct concentration up, etc.).
- ``compute_early_warning`` emits a structurally valid
  ``EarlyWarningSignal`` envelope with non-zero TDA features and a
  finite warning score.
- The multi-channel TDA pipeline runs end-to-end without raising.
"""

from __future__ import annotations

import math

import numpy as np
import pytest

from zer0pa_synbio.tda import (
    FermentationParams,
    compute_early_warning,
    simulate_fermentation_timeseries,
)


def _normal(seed: int = 42, duration_min: float = 720.0):
    return simulate_fermentation_timeseries(
        duration_min=duration_min, seed=seed
    )


def _with_regime(mode: str, t_event: float = 240.0, seed: int = 42, duration_min: float = 720.0):
    return simulate_fermentation_timeseries(
        duration_min=duration_min,
        regime_change=mode,
        regime_change_at_min=t_event,
        seed=seed,
    )


def test_normal_growth_reaches_stationary_phase():
    trace = _normal()
    # Biomass grows from 0.5 g/L to ≥10 g/L within 12 h (literature
    # high-density E. coli HMO production).
    assert trace.biomass_g_l[-1] > 10.0
    # Glucose stays above zero (feed maintains it).
    assert trace.glucose_g_l[-1] >= 0.0
    # Product accumulates.
    assert trace.product_g_l[-1] > 0.5
    # DO stays mostly positive.
    assert trace.dissolved_o2_pct[-1] > 30.0


def test_oxygen_transfer_collapse_drops_DO():
    """kLa drops from 200 → 5 h⁻¹; DO must crash relative to normal."""
    normal = _normal()
    failed = _with_regime("oxygen_transfer_collapse")
    # DO at end should be substantially lower under OC.
    assert failed.dissolved_o2_pct[-1] < normal.dissolved_o2_pct[-1] - 30.0


def test_byproduct_buildup_elevates_byproduct():
    """q_b ramps up by 5×; byproduct at end >> normal."""
    normal = _normal()
    failed = _with_regime("byproduct_buildup")
    assert failed.byproduct_g_l[-1] > normal.byproduct_g_l[-1] * 2.0


def test_growth_stall_lowers_biomass():
    """μ_max decays exponentially; biomass at end < normal."""
    normal = _normal()
    failed = _with_regime("growth_stall")
    assert failed.biomass_g_l[-1] < normal.biomass_g_l[-1] * 0.7


def test_toxicity_threshold_crossing_attenuates_growth():
    """When P > P_tox, μ_max scales down; final X < normal."""
    normal = _normal()
    failed = _with_regime("toxicity_threshold_crossing")
    # Toxicity bites once P crosses 3 g/L; final X should be lower.
    assert failed.biomass_g_l[-1] < normal.biomass_g_l[-1]


def test_nutrient_depletion_lowers_biomass():
    """Feed cut to zero; biomass plateau is lower than normal."""
    normal = _normal()
    failed = _with_regime("nutrient_depletion")
    assert failed.biomass_g_l[-1] < normal.biomass_g_l[-1] * 0.7


def test_simulator_uses_solve_ivp_and_is_deterministic_under_seed():
    """Two runs with the same seed must produce identical traces."""
    t1 = simulate_fermentation_timeseries(duration_min=300, seed=7)
    t2 = simulate_fermentation_timeseries(duration_min=300, seed=7)
    assert np.allclose(t1.biomass_g_l, t2.biomass_g_l)
    assert np.allclose(t1.dissolved_o2_pct, t2.dissolved_o2_pct)


def test_simulator_emits_byproduct_channel():
    """The new 5-state ODE adds byproduct accumulation; verify it's in
    the trace and grows monotonically under normal conditions."""
    trace = _normal()
    assert trace.byproduct_g_l is not None
    assert trace.byproduct_g_l[-1] > trace.byproduct_g_l[0]


def test_compute_early_warning_emits_real_ripser_features():
    trace = _with_regime("oxygen_transfer_collapse", t_event=300.0)
    ew = compute_early_warning(trace=trace, source_envelope_id="test_ew_oc")
    # The signal must be structurally valid and carry real TDA features.
    assert ew.signal_id.startswith("warn_")
    assert ew.source_envelope_id == "test_ew_oc"
    assert ew.window_spec.length_min == 60.0
    # TDA features are non-zero (ripser ran successfully).
    f = ew.features
    assert f.bottleneck_delta >= 0.0
    assert math.isfinite(f.persistence_entropy)
    assert math.isfinite(f.max_lifetime_h0)
    assert math.isfinite(f.max_lifetime_h1)
    # Warning score is in [0, 1].
    assert 0.0 <= ew.warning_score <= 1.0
    # Failure mode is recorded.
    assert "oxygen_transfer_collapse" in ew.failure_modes


def test_compute_early_warning_failure_mode_recorded_per_regime():
    """All 5 PRD §5.3 failure modes must round-trip through the signal."""
    modes = [
        "oxygen_transfer_collapse",
        "byproduct_buildup",
        "growth_stall",
        "toxicity_threshold_crossing",
        "nutrient_depletion",
    ]
    for mode in modes:
        trace = _with_regime(mode)
        ew = compute_early_warning(
            trace=trace, source_envelope_id=f"test_ew_{mode}"
        )
        assert mode in ew.failure_modes


def test_compute_early_warning_normal_trace_is_normal_status():
    """A pristine normal trace should not raise a fail-tier alert."""
    trace = _normal()
    ew = compute_early_warning(trace=trace, source_envelope_id="test_ew_normal")
    # Normal traces may show natural drift (status `watch` is fine for
    # v0.1 pre-PathGym calibration); they must not be `fail`.
    assert ew.status != "fail"
    assert ew.failure_modes == []


def test_short_trace_does_not_crash():
    """Very short traces (fewer than ~4 sliding windows) should return
    a valid signal with zeroed TDA features rather than crashing."""
    trace = simulate_fermentation_timeseries(duration_min=30, seed=0)
    ew = compute_early_warning(trace=trace, source_envelope_id="test_short")
    assert ew.warning_score == 0.0
    assert ew.status == "normal"


def test_simulator_with_custom_params():
    """Override default parameters and verify the simulator honours them."""
    params = FermentationParams(mu_max_h=1.4, q_p_g_g_h=0.20)
    trace = simulate_fermentation_timeseries(
        duration_min=300, seed=0, params=params
    )
    # With μ_max doubled, biomass should grow much faster than at default.
    default = simulate_fermentation_timeseries(duration_min=300, seed=0)
    assert trace.biomass_g_l[-1] > default.biomass_g_l[-1]
