"""Shared pytest fixtures for the synbio test suite."""

from __future__ import annotations

import uuid
from pathlib import Path

import pytest

from zer0pa_synbio.boundary import BOUNDARY_BLOCK
from zer0pa_synbio.envelope import (
    Backend,
    Domain,
    ExecutionMode,
    Falsification,
    Inputs,
    Layer,
    LicenseClass,
    Outputs,
    Provenance,
    RunMode,
    Uncertainty,
    UncertaintyDistribution,
    UniversalLayerEnvelope,
    compute_envelope_id,
    empty_provenance,
    now_iso,
)


REPO_ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture(scope="session")
def repo_root() -> Path:
    return REPO_ROOT


def _make_envelope(
    *,
    layer: Layer = Layer.L1,
    mode: RunMode = RunMode.engineering_stub,
    execution_mode: ExecutionMode = ExecutionMode.local_cpu,
    license_class: LicenseClass = LicenseClass.A,
    license_evidence_uri: str = "audit/source_manifests/builtin.yaml",
    sbol_attestation_present: bool = False,
    scientific_valid: bool = False,
) -> UniversalLayerEnvelope:
    """Construct a minimal valid envelope for tests."""
    backend = Backend(
        adapter="test_adapter",
        tool="test_tool",
        tool_version="0.1.0",
        execution_mode=execution_mode,
        license_class=license_class,
        license_evidence_uri=license_evidence_uri,
    )
    falsification = Falsification(
        sbol_attestation_present=sbol_attestation_present,
        scientific_valid=scientific_valid,
    )
    env = UniversalLayerEnvelope(
        boundary=BOUNDARY_BLOCK,
        envelope_id="sha256:placeholder",  # replaced below
        campaign_id="test_campaign",
        run_id=uuid.UUID("00000000-0000-0000-0000-000000000001"),
        layer=layer,
        domain=Domain.hmo,
        organism=562,  # E. coli
        gem_id="iML1515",
        mode=mode,
        backend=backend,
        inputs=Inputs(refs=[], payload={}),
        outputs=Outputs(refs=[], payload={}),
        uncertainty=Uncertainty(distribution=UncertaintyDistribution.none),
        falsification=falsification,
        provenance=Provenance(
            agent_id="test_agent",
            model_id="test_model",
            git_sha="0000000",
            created_at=now_iso(),
            input_hash="0" * 64,
            output_hash="0" * 64,
            config_hash="0" * 64,
        ),
    )
    # Re-create with a stable envelope_id (test convenience).
    eid = compute_envelope_id(env)
    return env.model_copy(update={"envelope_id": eid})


@pytest.fixture
def make_envelope():
    """Factory fixture for tests that need to construct minimal valid envelopes."""
    return _make_envelope
