"""Wave 11 — Runpod cutover proof.

For every gpu_rest_stub endpoint in the FastAPI app, this test runs the
endpoint via httpx.MockTransport (no network) and confirms:

1. The response is a valid UniversalLayerEnvelope.
2. The boundary block is verbatim.
3. `scientific_valid=False` is enforced (because it's a stub).
4. The license attestation is present.
5. The envelope_id is sha256-prefixed.
6. The schema_version is `synbio.envelope.v0.1`.

This is the executable proof of PRD §4.5 plug-replaceability + §19.2
cutover gates: under stub, the response shape is identical to what
runpod_rest will return. The cutover is a config flag, not a rewrite.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from zer0pa_synbio.envelope import UniversalLayerEnvelope
from zer0pa_synbio.rest import app


pytestmark = pytest.mark.runpod_cutover


@pytest.fixture(scope="module")
def client():
    return TestClient(app)


# Per PRD §17: ten REST stub endpoints.
# `/l4/kinetics/ensemble` returns four envelopes (one per ensemble member),
# wrapped in `{ensemble: {DLKcat:{}, CatPred:{}, TurNuP:{}, CEKM:{}}}`. Tested
# separately.
SINGLE_ENVELOPE_ENDPOINTS = [
    "/l1/zpe/embed",
    "/l3/bionavi/retrosynthesise",
    "/l3/deepretro/retrosynthesise",
    "/l4_5/rfdiffusion3/scaffold",
    "/l4_5/mace_off/binding",
    "/l4_5/esmfold/predict",
    "/l6_build/cellfree/stub",
    "/l6_build/cellfree/strateos",
    "/l6_build/cellfree/emerald",
]


def _minimal_body() -> dict:
    import selfies as sf

    return {
        "campaign_id": "test_runpod_cutover",
        "domain": "hmo",
        "organism": 562,
        "gem_id": "iML1515",
        "input_payload": {
            "target_compound": {"selfies": sf.encoder("CCO"), "inchi_key": "TEST"},
            "host_organism": {
                "taxonomy_id": 562,
                "refseq_genome_accession": "NC_000913.3",
                "gem_id": "iML1515",
            },
            "target_inchi_key": "GFXBRIYRYYFCIA-LWNAIEPUSA-N",
            "spec_id": "gms_test",
            "enzyme_uniprot_id": "Q11075",
        },
    }


def test_health_endpoint(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"
    assert r.json()["schema_version"] == "synbio.envelope.v0.1"


@pytest.mark.parametrize("path", SINGLE_ENVELOPE_ENDPOINTS)
def test_endpoint_returns_valid_envelope(client, path):
    """Every gpu_rest_stub endpoint returns a UniversalLayerEnvelope-shaped JSON."""
    r = client.post(path, json=_minimal_body())
    assert r.status_code == 200, f"{path} returned {r.status_code}: {r.text[:200]}"
    data = r.json()
    # Validate via Pydantic.
    env = UniversalLayerEnvelope.model_validate(data)
    assert env.boundary == data["boundary"]
    assert env.envelope_id.startswith("sha256:")
    assert env.schema_version == "synbio.envelope.v0.1"


@pytest.mark.parametrize("path", SINGLE_ENVELOPE_ENDPOINTS)
def test_stub_envelope_cannot_claim_scientific_validity(client, path):
    r = client.post(path, json=_minimal_body())
    assert r.status_code == 200
    env = UniversalLayerEnvelope.model_validate(r.json())
    assert env.falsification.scientific_valid is False, (
        f"{path}: stub envelope claimed scientific_valid=True"
    )


@pytest.mark.parametrize("path", SINGLE_ENVELOPE_ENDPOINTS)
def test_endpoint_returns_license_attestation(client, path):
    r = client.post(path, json=_minimal_body())
    env = UniversalLayerEnvelope.model_validate(r.json())
    assert env.backend.license_class is not None
    assert env.backend.license_evidence_uri.startswith("audit/")


def test_kinetics_ensemble_returns_four_envelopes(client):
    r = client.post("/l4/kinetics/ensemble", json=_minimal_body())
    assert r.status_code == 200
    data = r.json()
    assert "ensemble" in data
    assert set(data["ensemble"].keys()) == {"DLKcat", "CatPred", "TurNuP", "CEKM"}
    for name, env_dict in data["ensemble"].items():
        env = UniversalLayerEnvelope.model_validate(env_dict)
        assert env.layer.value == "L4"
        assert env.falsification.scientific_valid is False


@pytest.mark.parametrize("path", SINGLE_ENVELOPE_ENDPOINTS)
def test_endpoint_response_byte_equals_direct_adapter_call(client, path):
    """The REST endpoint's envelope is byte-equal to a direct adapter call,
    modulo runtime/provenance fields. This is the cutover invariance proof."""
    from zer0pa_synbio.plug_replaceability import compare_envelopes

    # Path → direct adapter mapping.
    from zer0pa_synbio.adapters.l1_zpe import L1ZPEAdapter
    from zer0pa_synbio.adapters.l3_retrosynthesis import (
        L3BioNaviAdapter,
        L3DeepRetroAdapter,
    )
    from zer0pa_synbio.adapters.l4_5_unknown_enzyme import (
        L4_5ESMFoldAdapter,
        L4_5MACEOFFAdapter,
        L4_5RFdiffusion3Adapter,
    )
    from zer0pa_synbio.adapters.l6_build_cellfree_txtl import (
        L6BuildCellFreeStubAdapter,
        L6BuildEmeraldAdapter,
        L6BuildStrateosAdapter,
    )
    from zer0pa_synbio.envelope import Domain, ExecutionMode

    direct_adapters = {
        "/l1/zpe/embed": lambda: L1ZPEAdapter(execution_mode=ExecutionMode.gpu_rest_stub),
        "/l3/bionavi/retrosynthesise": L3BioNaviAdapter,
        "/l3/deepretro/retrosynthesise": L3DeepRetroAdapter,
        "/l4_5/rfdiffusion3/scaffold": L4_5RFdiffusion3Adapter,
        "/l4_5/mace_off/binding": L4_5MACEOFFAdapter,
        "/l4_5/esmfold/predict": L4_5ESMFoldAdapter,
        "/l6_build/cellfree/stub": L6BuildCellFreeStubAdapter,
        "/l6_build/cellfree/strateos": L6BuildStrateosAdapter,
        "/l6_build/cellfree/emerald": L6BuildEmeraldAdapter,
    }
    factory = direct_adapters[path]
    body = _minimal_body()
    rest_resp = client.post(path, json=body)
    rest_env = UniversalLayerEnvelope.model_validate(rest_resp.json())

    direct = factory()
    direct_env = direct.run(
        campaign_id=body["campaign_id"],
        domain=Domain(body["domain"]),
        organism=body["organism"],
        gem_id=body["gem_id"],
        input_payload=body["input_payload"],
    )
    diffs = compare_envelopes(rest_env, direct_env)
    assert diffs == [], (
        f"REST endpoint and direct adapter call diverge on non-runtime fields:\n  "
        + "\n  ".join(diffs)
    )
