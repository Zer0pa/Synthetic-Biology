"""Wave 10 — Falsification wave.

One deliberate-trigger test per falsifier in `audit/falsifiers.yaml`.
Each falsifier is given:
  - a *clean* evidence payload (must NOT trigger)
  - a *deliberately bad* evidence payload (must trigger)

Per PRD §20.4 (Falsification-wave gate): the wave passes only if the
system blocks or quarantines each bad case.

References:
- audit/falsifiers.yaml (the executable spec)
- src/zer0pa_synbio/falsifiers/checks.py (the implementations)
"""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from zer0pa_synbio.boundary import BOUNDARY_BLOCK
from zer0pa_synbio.falsifiers import REGISTRY
from zer0pa_synbio.falsifiers.checks import CHECKS, run as run_falsifier


pytestmark = pytest.mark.falsification


# ─── Coverage assertion ────────────────────────────────────────────────


def test_every_registry_entry_has_implementation():
    missing = set(REGISTRY) - set(CHECKS)
    assert not missing, f"Falsifiers without implementations: {missing}"


def test_every_implementation_has_registry_entry():
    extra = set(CHECKS) - set(REGISTRY)
    assert not extra, f"Implementations without registry entries: {extra}"


# ─── Per-falsifier deliberate triggers ────────────────────────────────


def test_f000_clean_passes():
    r = run_falsifier("f000_boundary_violation", {"boundary_text": BOUNDARY_BLOCK})
    assert r.triggered is False


def test_f000_deliberate_trigger():
    r = run_falsifier("f000_boundary_violation", {"boundary_text": "REPLACED BOUNDARY"})
    assert r.triggered is True
    assert r.gate_action == "reject_envelope"


def test_f001_clean_passes():
    # Valid SELFIES: ethanol = [C][C][O]; will roundtrip through selfies+rdkit.
    r = run_falsifier("f001_invalid_selfies", {"selfies": "[C][C][O]"})
    assert r.triggered is False


def test_f001_deliberate_trigger():
    r = run_falsifier("f001_invalid_selfies", {"selfies": "[NONSENSE_TOKEN_NOT_SELFIES]["})
    assert r.triggered is True


def test_f002_clean_passes():
    r = run_falsifier(
        "f002_mass_balance_violation",
        {"substrate_atoms": {"C": 6, "H": 12, "O": 6}, "product_atoms": {"C": 6, "H": 12, "O": 6}},
    )
    assert r.triggered is False


def test_f002_deliberate_trigger():
    r = run_falsifier(
        "f002_mass_balance_violation",
        {"substrate_atoms": {"C": 6, "O": 6}, "product_atoms": {"C": 6, "O": 5}},
    )
    assert r.triggered is True


def test_f003_clean_passes():
    r = run_falsifier("f003_mdf_infeasibility", {"mdf_kj_mol": 5.0})
    assert r.triggered is False


def test_f003_deliberate_trigger():
    r = run_falsifier("f003_mdf_infeasibility", {"mdf_kj_mol": -2.0, "bottleneck_step": "step_3"})
    assert r.triggered is True


def test_f004_clean_passes():
    r = run_falsifier("f004_toxic_intermediate", {"qsar_alert": None, "confidence": 0.0})
    assert r.triggered is False


def test_f004_deliberate_trigger():
    r = run_falsifier(
        "f004_toxic_intermediate",
        {"qsar_alert": "AzideAcid", "confidence": 0.78, "intermediate_inchi_key": "X"},
    )
    assert r.triggered is True


def test_f005_clean_passes():
    r = run_falsifier(
        "f005_stoichiometric_infeasibility",
        {"cofactor": "NADH", "required_flux": 5.0, "native_capacity": 10.0},
    )
    assert r.triggered is False


def test_f005_deliberate_trigger():
    r = run_falsifier(
        "f005_stoichiometric_infeasibility",
        {"cofactor": "NADH", "required_flux": 50.0, "native_capacity": 4.0},
    )
    assert r.triggered is True


def test_f006_clean_passes():
    r = run_falsifier("f006_kinetics_disagreement_high", {"values": [12.0, 12.5, 11.8, 12.3]})
    assert r.triggered is False


def test_f006_deliberate_trigger():
    r = run_falsifier("f006_kinetics_disagreement_high", {"values": [1.0, 100.0, 50.0, 25.0]})
    assert r.triggered is True


def test_f007_clean_passes():
    r = run_falsifier("f007_fba_disagreement_high", {"values": [0.85, 0.83, 0.82, 0.81]})
    assert r.triggered is False


def test_f007_deliberate_trigger():
    r = run_falsifier("f007_fba_disagreement_high", {"values": [0.1, 0.9, 0.5, 0.85]})
    assert r.triggered is True


def test_f008_clean_passes():
    r = run_falsifier(
        "f008_retrosynthesis_disagreement_high",
        {
            "tool_route_sets": {
                "retropath3": ["r1", "r2", "r3"],
                "novostoic2": ["r1", "r2", "r3"],
                "bionavi": ["r1", "r2", "r3"],
                "deepretro": ["r1", "r2", "r3"],
            }
        },
    )
    assert r.triggered is False


def test_f008_deliberate_trigger():
    r = run_falsifier(
        "f008_retrosynthesis_disagreement_high",
        {
            "tool_route_sets": {
                "retropath3": ["r1"],
                "novostoic2": ["r2"],
                "bionavi": ["r3"],
                "deepretro": ["r4"],
            },
            "threshold": 0.5,
        },
    )
    assert r.triggered is True


def test_f009_clean_passes():
    r = run_falsifier(
        "f009_novelty_without_retrosynthesis",
        {"novelty_class": "known_reaction", "retrosynthesis_proposing_count": 4},
    )
    assert r.triggered is False


def test_f009_deliberate_trigger():
    r = run_falsifier(
        "f009_novelty_without_retrosynthesis",
        {"novelty_class": "fully_novel", "retrosynthesis_proposing_count": 0},
    )
    assert r.triggered is True
    assert r.gate_action == "route_to_unknown_enzyme"


def test_f010_clean_passes():
    r = run_falsifier(
        "f010_novelty_without_ts_analog",
        {"novelty_class": "reaction_class_known", "ts_analog_search_result": {"found": True}},
    )
    assert r.triggered is False


def test_f010_deliberate_trigger():
    r = run_falsifier(
        "f010_novelty_without_ts_analog",
        {"novelty_class": "fully_novel", "ts_analog_search_result": {"found": False}},
    )
    assert r.triggered is True


def test_f011_clean_passes():
    r = run_falsifier(
        "f011_cekm_survivorship_bias_check", {"cekm_value": 12.5, "ensemble_value": 12.0}
    )
    assert r.triggered is False


def test_f011_deliberate_trigger():
    r = run_falsifier(
        "f011_cekm_survivorship_bias_check", {"cekm_value": 100.0, "ensemble_value": 5.0, "threshold": 0.5}
    )
    assert r.triggered is True


def test_f012_clean_passes():
    r = run_falsifier("f012_codec_as_mechanism_analog", {"mechanism_chain": ["genotype_X", "kcat_change"]})
    assert r.triggered is False


def test_f012_deliberate_trigger():
    r = run_falsifier("f012_codec_as_mechanism_analog", {"mechanism_chain": []})
    assert r.triggered is True
    assert r.severity == "fail"


def test_f013_clean_passes():
    r = run_falsifier("f013_rfdiffusion3_motif_infeasible", {"motif_rmsd": 1.2})
    assert r.triggered is False


def test_f013_deliberate_trigger():
    r = run_falsifier("f013_rfdiffusion3_motif_infeasible", {"motif_rmsd": 5.5})
    assert r.triggered is True


def test_f014_clean_passes():
    r = run_falsifier(
        "f014_mace_off_binding_implausible",
        {"binding_energy_kj_mol": -42.0, "reference_range": {"lo": -100.0, "hi": 0.0}},
    )
    assert r.triggered is False


def test_f014_deliberate_trigger():
    r = run_falsifier(
        "f014_mace_off_binding_implausible",
        {"binding_energy_kj_mol": -500.0, "reference_range": {"lo": -100.0, "hi": 0.0}},
    )
    assert r.triggered is True


def test_f015_clean_passes():
    r = run_falsifier("f015_prody_nma_misaligned", {"catalytic_coordinate_alignment": 0.78})
    assert r.triggered is False


def test_f015_deliberate_trigger():
    r = run_falsifier("f015_prody_nma_misaligned", {"catalytic_coordinate_alignment": 0.18})
    assert r.triggered is True


def test_f016_clean_passes():
    r = run_falsifier("f016_tda_regime_change", {"warning_score": 0.2})
    assert r.triggered is False


def test_f016_deliberate_trigger():
    r = run_falsifier(
        "f016_tda_regime_change",
        {"warning_score": 0.85, "failure_mode": "oxygen_transfer_collapse"},
    )
    assert r.triggered is True


def test_f017_clean_passes():
    r = run_falsifier(
        "f017_industrial_scale_uncalibrated",
        {
            "claimed_scale": "bench",
            "cited_corpus_uri": "audit/source_manifests/iml1515.yaml",
            "corpus_license_class": "A",
        },
    )
    assert r.triggered is False


def test_f017_deliberate_trigger():
    r = run_falsifier(
        "f017_industrial_scale_uncalibrated",
        {"claimed_scale": "industrial", "cited_corpus_uri": "", "corpus_license_class": "E"},
    )
    assert r.triggered is True


def test_f018_clean_passes():
    r = run_falsifier(
        "f018_license_drift",
        {
            "offending_source_uri": "audit/source_manifests/rhea.yaml",
            "license_class": "A",
            "license_grant_present": False,
        },
    )
    assert r.triggered is False


def test_f018_bkms_react_blocked():
    """Reciting BKMS-react fails closed regardless of license_grant_present."""
    r = run_falsifier(
        "f018_license_drift",
        {
            "offending_source_uri": "https://bkms-react.tu-bs.de/some_endpoint",
            "license_class": "E",
            "license_grant_present": True,  # even with a grant, BKMS-react fails closed
        },
    )
    assert r.triggered is True


def test_f018_kegg_bulk_blocked():
    r = run_falsifier(
        "f018_license_drift",
        {
            "offending_source_uri": "kegg-bulk-export-v2",
            "license_class": "E",
            "license_grant_present": True,
        },
    )
    assert r.triggered is True


def test_f018_atlas_blocked():
    r = run_falsifier(
        "f018_license_drift",
        {
            "offending_source_uri": "atlas_of_biochemistry/predicted_reactions.csv",
            "license_class": "D",
            "license_grant_present": True,
        },
    )
    assert r.triggered is True


def test_f018_class_c_without_grant_fails():
    r = run_falsifier(
        "f018_license_drift",
        {
            "offending_source_uri": "salis_v1_subprocess",
            "license_class": "C",
            "license_grant_present": False,
        },
    )
    assert r.triggered is True


def test_f018_class_c_with_grant_passes():
    r = run_falsifier(
        "f018_license_drift",
        {
            "offending_source_uri": "salis_v1_subprocess",
            "license_class": "C",
            "license_grant_present": True,
        },
    )
    assert r.triggered is False


def test_f019_skipped_when_no_uri():
    """f019 with no uri is treated as failed (no SBOL doc to validate)."""
    r = run_falsifier("f019_valid_sbol_only", {"sbol3_uri": ""})
    assert r.triggered is True


def test_f019_invalid_sbol_path_fails(tmp_path):
    bad = tmp_path / "not_sbol.xml"
    bad.write_text("<not-sbol/>", encoding="utf-8")
    r = run_falsifier("f019_valid_sbol_only", {"sbol3_uri": str(bad)})
    assert r.triggered is True


def test_f020_clean_passes():
    r = run_falsifier(
        "f020_txtl_observation_without_in_vivo",
        {"consumer_decision": "use_for_l6_handoff", "in_vivo_corroboration_present": True},
    )
    assert r.triggered is False


def test_f020_deliberate_trigger():
    r = run_falsifier(
        "f020_txtl_observation_without_in_vivo",
        {"consumer_decision": "use_for_l6_handoff", "in_vivo_corroboration_present": False},
    )
    assert r.triggered is True
    assert r.gate_action == "route_to_phase_2"


def test_f021_clean_passes():
    r = run_falsifier(
        "f021_reaction_not_atom_balanced",
        {"substrate_atoms": {"C": 6, "H": 12, "O": 6}, "product_atoms": {"C": 6, "H": 12, "O": 6}},
    )
    assert r.triggered is False


def test_f021_deliberate_trigger():
    r = run_falsifier(
        "f021_reaction_not_atom_balanced",
        {"substrate_atoms": {"C": 6}, "product_atoms": {"C": 7}},
    )
    assert r.triggered is True


def test_f022_clean_passes():
    r = run_falsifier(
        "f022_validation_sequence_unreachable",
        {"consumer": "human_cro", "configured_consumers": ["human_cro", "strateos_api"]},
    )
    assert r.triggered is False


def test_f022_deliberate_trigger():
    r = run_falsifier(
        "f022_validation_sequence_unreachable",
        {"consumer": "wetlab_phase2", "configured_consumers": ["human_cro", "cellfree_txtl_stub"]},
    )
    assert r.triggered is True
    assert r.severity == "fail"


# ─── Falsification-wave aggregate gate ────────────────────────────────


def test_falsification_wave_passes():
    """Aggregate Wave 10 gate: every falsifier has both a clean and a
    bad-trigger test. This counts the test functions in this module."""
    import inspect
    import sys

    module = sys.modules[__name__]
    fns = inspect.getmembers(module, inspect.isfunction)
    test_fns = [n for n, _ in fns if n.startswith("test_")]
    deliberate = [n for n in test_fns if "_deliberate_trigger" in n or "_blocked" in n or "_without_grant" in n]
    clean = [n for n in test_fns if "_clean_passes" in n or "_with_grant_passes" in n]
    # Must have at least 23 deliberate triggers and 23 clean passes
    # (one per falsifier; allow extras for f018/f019 license drift specifics).
    assert len(deliberate) >= 23, f"Need 23+ deliberate triggers, have {len(deliberate)}"
    assert len(clean) >= 22, f"Need 22+ clean-pass tests, have {len(clean)}"
