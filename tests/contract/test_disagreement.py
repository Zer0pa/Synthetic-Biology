"""Contract tests for the cross-model disagreement record builders."""

from __future__ import annotations

import pytest

from zer0pa_synbio.disagreement import (
    build_fba_disagreement,
    build_kinetics_disagreement,
    build_retrosynthesis_disagreement,
)
from zer0pa_synbio.types import CrossModelDisagreementRecord

pytestmark = pytest.mark.contract


def test_kinetics_disagreement_pass():
    rec = build_kinetics_disagreement(
        envelope_id="sha256:test",
        enzyme_uniprot_id="Q11075",
        quantity="kcat_per_s",
        values_by_model={"DLKcat": 12.5, "CatPred": 12.2, "TurNuP": 13.1, "CEKM": 12.8},
    )
    assert rec.status == "pass"
    assert rec.metric == "sigma_normalized"
    assert rec.unit == "per_s"


def test_kinetics_disagreement_fail_routes_to_blind_eval():
    rec = build_kinetics_disagreement(
        envelope_id="sha256:test",
        enzyme_uniprot_id="Q11075",
        quantity="kcat_per_s",
        values_by_model={"DLKcat": 1.0, "CatPred": 100.0, "TurNuP": 50.0, "CEKM": 200.0},
    )
    assert rec.status == "fail"
    assert rec.resolution_action == "escalate_to_blind_eval"


def test_fba_disagreement():
    rec = build_fba_disagreement(
        envelope_id="sha256:test",
        reaction_id="BIOMASS_Ec_iML1515",
        values_by_model={"COBRApy": 0.876, "GECKO": 0.821, "ECMpy": 0.853, "ETFL": 0.812},
    )
    assert rec.layer == "L4_fba"
    assert rec.status in ("pass", "warn")
    assert rec.unit == "mmol/(gDW.h)"


def test_retrosynthesis_jaccard_disagreement():
    """Three tools propose distinct route sets — high Jaccard distance."""
    rec = build_retrosynthesis_disagreement(
        envelope_id="sha256:test",
        target_inchi_key="GFXBRIYRYYFCIA-LWNAIEPUSA-N",
        routes_by_tool={
            "retropath3": ["r1", "r2"],
            "novostoic2": ["r3", "r4"],
            "bionavi": ["r5"],
            "deepretro": ["r6"],
        },
    )
    assert rec.metric == "jaccard"
    # All tools propose disjoint routes → Jaccard distance = 1.0 → fail.
    assert rec.status == "fail"
    assert rec.resolution_action == "escalate_to_unknown_enzyme"


def test_retrosynthesis_consensus_passes():
    rec = build_retrosynthesis_disagreement(
        envelope_id="sha256:test",
        target_inchi_key="X",
        routes_by_tool={
            "retropath3": ["r1", "r2", "r3"],
            "novostoic2": ["r1", "r2", "r3"],
            "bionavi": ["r1", "r2", "r3"],
            "deepretro": ["r1", "r2", "r3"],
        },
    )
    assert rec.status == "pass"


def test_disagreement_record_validates_against_pydantic_schema():
    rec = build_kinetics_disagreement(
        envelope_id="sha256:t",
        enzyme_uniprot_id="X",
        quantity="kcat_per_s",
        values_by_model={"DLKcat": 1.0, "CatPred": 1.5},
    )
    # Round-trip via dump/parse to ensure schema invariance.
    data = rec.model_dump(mode="json")
    rebuilt = CrossModelDisagreementRecord.model_validate(data)
    assert rebuilt.record_id == rec.record_id
