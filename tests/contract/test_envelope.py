"""Contract: UniversalLayerEnvelope construction, validation, and hash discipline."""

from __future__ import annotations

import json

import pytest
from pydantic import ValidationError

from zer0pa_synbio.boundary import BOUNDARY_BLOCK
from zer0pa_synbio.envelope import (
    BoundaryGateError,
    ExecutionMode,
    Layer,
    LicenseClass,
    RunMode,
    UniversalLayerEnvelope,
    canonical_json,
    compute_envelope_id,
)


# Pydantic v2 wraps validator-raised exceptions in ValidationError.
# Cross-field invariants raised by `model_validator(mode="after")` may also
# come through as ValidationError. Either is a valid rejection signal.
RejectError = (BoundaryGateError, ValidationError, ValueError)

pytestmark = pytest.mark.contract


def test_envelope_constructs_valid(make_envelope):
    env = make_envelope()
    assert env.boundary == BOUNDARY_BLOCK
    assert env.schema_version == "synbio.envelope.v0.1"
    assert env.envelope_id.startswith("sha256:")


def test_boundary_mutation_fails_closed(make_envelope):
    env = make_envelope()
    bad_dump = env.model_dump(mode="json")
    bad_dump["boundary"] = "REPLACED"
    with pytest.raises(RejectError, match="Boundary block does not match"):
        UniversalLayerEnvelope.model_validate(bad_dump)


def test_boundary_silent_truncation_fails_closed(make_envelope):
    """Even a tiny mutation (one missing word) must fail closed."""
    env = make_envelope()
    bad_dump = env.model_dump(mode="json")
    bad_dump["boundary"] = BOUNDARY_BLOCK.replace("Defence / weapons / dual-use bio applications excluded under operator policy.", "")
    with pytest.raises(RejectError):
        UniversalLayerEnvelope.model_validate(bad_dump)


def test_canonical_json_is_byte_stable(make_envelope):
    """An envelope's canonical JSON is byte-stable across re-serialisation."""
    env = make_envelope()
    blob1 = canonical_json(env.model_dump(mode="json"))
    blob2 = canonical_json(env.model_dump(mode="json"))
    assert blob1 == blob2


def test_canonical_json_round_trip_byte_equal(make_envelope):
    """Dump → canonical → parse → validate → dump → canonical is byte-stable."""
    env = make_envelope()
    blob1 = canonical_json(env.model_dump(mode="json"))
    parsed = json.loads(blob1)
    rebuilt = UniversalLayerEnvelope.model_validate(parsed)
    blob2 = canonical_json(rebuilt.model_dump(mode="json"))
    assert blob1 == blob2


def test_envelope_id_is_deterministic(make_envelope):
    env = make_envelope()
    eid1 = compute_envelope_id(env)
    eid2 = compute_envelope_id(env)
    assert eid1 == eid2
    assert eid1.startswith("sha256:")
    assert len(eid1) == len("sha256:") + 64


def test_envelope_id_changes_on_payload_change(make_envelope):
    env = make_envelope()
    e1 = compute_envelope_id(env)
    bumped = env.model_copy(update={"campaign_id": "DIFFERENT_CAMPAIGN"})
    e2 = compute_envelope_id(bumped)
    assert e1 != e2


def test_canonical_json_roundtrip(make_envelope):
    env = make_envelope()
    blob = canonical_json(env.model_dump(mode="json"))
    parsed = json.loads(blob)
    rebuilt = UniversalLayerEnvelope.model_validate(parsed)
    assert rebuilt == env


def test_stub_cannot_claim_scientific_validity(make_envelope):
    with pytest.raises(RejectError, match="scientific_valid=True"):
        make_envelope(mode=RunMode.engineering_stub, scientific_valid=True)


def test_gpu_rest_stub_cannot_claim_scientific_validity(make_envelope):
    with pytest.raises(RejectError, match="scientific_valid=True"):
        make_envelope(
            mode=RunMode.scientific,
            execution_mode=ExecutionMode.gpu_rest_stub,
            scientific_valid=True,
        )


def test_l6_requires_sbol_attestation(make_envelope):
    with pytest.raises(RejectError, match="sbol_attestation_present"):
        make_envelope(layer=Layer.L6, sbol_attestation_present=False)


def test_l6_with_sbol_attestation_passes(make_envelope):
    env = make_envelope(layer=Layer.L6, sbol_attestation_present=True)
    assert env.layer == Layer.L6
    assert env.falsification.sbol_attestation_present is True


def test_class_c_requires_license_grant_path(make_envelope):
    with pytest.raises(RejectError, match="license_evidence_uri"):
        make_envelope(license_class=LicenseClass.C, license_evidence_uri="")


def test_class_c_requires_license_grant_dir(make_envelope):
    with pytest.raises(RejectError, match="audit/license_grants/"):
        make_envelope(
            license_class=LicenseClass.C,
            license_evidence_uri="https://some.elsewhere/license.txt",
        )


def test_class_c_with_proper_grant_uri_passes(make_envelope):
    env = make_envelope(
        license_class=LicenseClass.C,
        license_evidence_uri="audit/license_grants/example_class_c.yaml",
    )
    assert env.backend.license_class == LicenseClass.C


def test_class_a_does_not_require_license_grant(make_envelope):
    env = make_envelope(
        license_class=LicenseClass.A,
        license_evidence_uri="audit/source_manifests/cc_by_4_0.yaml",
    )
    assert env.backend.license_class == LicenseClass.A
