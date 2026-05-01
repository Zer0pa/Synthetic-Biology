"""L5 MFMO BoTorch adapter integration tests.

Two paths:

- **Real path** when ``.venv-l5/bin/python`` exists (Python 3.11 +
  torch 2.2.2 + botorch 0.17.2). The adapter shells out to the
  worker, fits a real GP per objective with the Hamming kernel, runs
  qLogNEHVI for next-batch suggestions, and triggers ASR-thermostable
  warm-starts when any candidate has predicted Tm < 50°C.
- **Stub path** when ``.venv-l5`` is absent. Adapter falls back to
  scipy-style Pareto sort. Plug-replaceability invariant (PRD §4.5)
  asserts the same output schema in both paths.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from zer0pa_synbio.adapters.l5_mfmo import L5MFMOAdapter
from zer0pa_synbio.envelope import Domain, RunMode


REPO_ROOT = Path(__file__).resolve().parents[2]
VENV_L5_PYTHON = REPO_ROOT / ".venv-l5" / "bin" / "python"


def _make_candidates(n: int = 6) -> list[dict]:
    """Synthetic candidate set with diverse Pareto-trade-off shape and
    a low-Tm member to trigger ASR warm-start."""
    return [
        {
            "pathway_id": f"p{i}",
            "mdf_score_kj_mol": 5.0 + i * 1.5,
            # Mix Tm values so at least one is < 50 °C.
            "predicted_tm_celsius": 40 + i * 3,
            "predicted_titer_g_l": 1.0 + 0.3 * i,
            "predicted_yield_mol_mol": 0.15 + 0.02 * i,
            "predicted_burden_au": 0.6 - 0.05 * i,
            "predicted_toxicity_au": 0.1 + 0.02 * i,
        }
        for i in range(n)
    ]


def _run(input_payload, run_mode=RunMode.scientific):
    return L5MFMOAdapter(run_mode=run_mode).run(
        campaign_id="test_l5",
        domain=Domain.hmo,
        organism=562,
        gem_id="iML1515",
        input_payload=input_payload,
    )


def test_envelope_schema_invariant_in_both_paths():
    """Both real and stub paths must emit ``synbio.ranked_pathway_set.v0.1``
    with the same top-level keys (PRD §4.5 plug-replaceability)."""
    cands = _make_candidates(4)
    env = _run({"scored_candidates": cands, "n_suggested_next_batch": 2})
    p = env.outputs.payload
    assert p["schema_version"] == "synbio.ranked_pathway_set.v0.1"
    for key in (
        "candidates",
        "validation_sequence",
        "surrogate_meta",
        "asr_warmstart",
        "stub_mode",
    ):
        assert key in p
    # Each candidate carries the four expected-* quantile dicts.
    for c in p["candidates"]:
        for k in (
            "expected_titer_g_l",
            "expected_yield_mol_mol",
            "expected_burden_au",
            "expected_toxicity_au",
        ):
            assert "p50" in c[k]


@pytest.mark.skipif(
    not VENV_L5_PYTHON.exists(),
    reason=".venv-l5 (Python 3.11 + torch + botorch) not provisioned",
)
def test_real_botorch_path_fits_gp_and_proposes_suggestions():
    cands = _make_candidates(6)
    env = _run({"scored_candidates": cands, "n_suggested_next_batch": 3})
    p = env.outputs.payload
    assert p["stub_mode"] is False
    meta = p["surrogate_meta"]
    assert meta["kernel"] == "hamming_distance"
    assert meta["acquisition"] == "qLogNEHVI"
    assert meta["n_train"] == 6
    assert meta["n_objectives"] == 4
    assert meta["fitted_lengthscales"] is not None
    assert len(meta["fitted_lengthscales"]) == 4
    # qLogNEHVI suggestions land in the validation_sequence as
    # ordered_experiments. We requested 3.
    assert len(p["validation_sequence"]["ordered_experiments"]) == 3


@pytest.mark.skipif(
    not VENV_L5_PYTHON.exists(),
    reason=".venv-l5 not provisioned",
)
def test_real_botorch_path_triggers_asr_warmstart_below_50c():
    cands = _make_candidates(6)  # min Tm = 40 °C → triggers
    env = _run(
        {
            "scored_candidates": cands,
            "n_suggested_next_batch": 2,
            "n_warm_asr": 4,
            "asr_tm_threshold_c": 50.0,
        }
    )
    asr = env.outputs.payload["asr_warmstart"]
    assert asr["n_injected"] == 4
    assert asr["tm_min_observed_c"] == 40
    assert asr["tm_threshold_c"] == 50.0


@pytest.mark.skipif(
    not VENV_L5_PYTHON.exists(),
    reason=".venv-l5 not provisioned",
)
def test_real_botorch_path_no_asr_when_all_above_50c():
    cands = [
        {
            "pathway_id": f"p{i}",
            "mdf_score_kj_mol": 8.0,
            "predicted_tm_celsius": 60 + i,  # all > 50
            "predicted_titer_g_l": 1.0 + 0.3 * i,
            "predicted_yield_mol_mol": 0.15 + 0.02 * i,
            "predicted_burden_au": 0.6,
            "predicted_toxicity_au": 0.1,
        }
        for i in range(5)
    ]
    env = _run(
        {
            "scored_candidates": cands,
            "n_suggested_next_batch": 1,
            "n_warm_asr": 4,
            "asr_tm_threshold_c": 50.0,
        }
    )
    asr = env.outputs.payload["asr_warmstart"]
    assert asr["n_injected"] == 0


def test_stub_fallback_when_venv_l5_absent(monkeypatch):
    """Force the adapter to take the stub path by patching the locator."""
    monkeypatch.setattr(L5MFMOAdapter, "_venv_l5_python", staticmethod(lambda: None))
    cands = _make_candidates(4)
    env = _run({"scored_candidates": cands, "n_suggested_next_batch": 2})
    p = env.outputs.payload
    assert p["stub_mode"] is True
    assert p["surrogate_meta"]["kernel"] == "scipy_pareto_sort"
    # Stub still preserves the schema.
    assert len(p["candidates"]) == len(cands)
    for c in p["candidates"]:
        assert c["surrogate"] == "scipy_fallback"
        assert "p50" in c["expected_titer_g_l"]


def test_empty_candidates_does_not_crash():
    env = _run({"scored_candidates": [], "n_suggested_next_batch": 0})
    assert env.outputs.payload["candidates"] == []
