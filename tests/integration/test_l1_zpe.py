"""L1 ZPE adapter integration tests."""

from __future__ import annotations

import pytest

from zer0pa_synbio.adapters.l1_zpe import (
    L1ZPEAdapter,
    _hash_derived_embedding,
    _zpe_envelope,
)
from zer0pa_synbio.envelope import (
    Domain,
    ExecutionMode,
    GateStatus,
    Layer,
    LicenseClass,
    RunMode,
)


pytestmark = pytest.mark.integration


# 2'-FL canonical input: lactose + GDP-fucose → 2'-fucosyllactose.
# 2'-FL InChIKey: GFXBRIYRYYFCIA-LWNAIEPUSA-N (canonical)
# Lactose SMILES: OC[C@H]1O[C@@H](OC[C@H]2O[C@H](O)[C@H](O)[C@@H](O)[C@@H]2O)[C@H](O)[C@@H](O)[C@@H]1O
# Lactose SELFIES (one of many valid encodings): use RDKit + selfies on the fly.

LACTOSE_SMILES = (
    "OC[C@H]1O[C@@H](OC[C@H]2O[C@H](O)[C@H](O)[C@@H](O)[C@@H]2O)[C@H](O)[C@@H](O)[C@@H]1O"
)


def _lactose_selfies() -> str:
    import selfies as sf  # type: ignore[import-not-found]

    return sf.encoder(LACTOSE_SMILES)


@pytest.fixture
def lactose_input():
    return {
        "target_compound": {
            "selfies": _lactose_selfies(),
            "inchi_key": "GUBGYTABKSRVRQ-PICCSMPSSA-N",  # lactose InChIKey
        },
        "host_organism": {
            "taxonomy_id": 562,
            "refseq_genome_accession": "NC_000913.3",
            "gem_id": "iML1515",
        },
    }


def test_l1_runs_in_local_cpu_and_returns_envelope(lactose_input):
    adapter = L1ZPEAdapter(execution_mode=ExecutionMode.local_cpu, run_mode=RunMode.engineering_stub)
    env = adapter.run(
        campaign_id="test_l1_local_cpu",
        domain=Domain.hmo,
        organism=562,
        gem_id="iML1515",
        input_payload=lactose_input,
    )
    assert env.layer == Layer.L1
    assert env.backend.adapter == "L1ZPEAdapter"
    assert env.backend.license_class == LicenseClass.A
    assert env.falsification.scientific_valid is False  # stub backend
    assert env.outputs.payload["zpe_version"] == "zpe.v0.1"
    assert isinstance(env.outputs.payload["zpe_word_envelope"], list)
    assert len(env.outputs.payload["zpe_word_envelope"]) > 0
    assert all(0 <= w < 2**20 for w in env.outputs.payload["zpe_word_envelope"])
    assert len(env.outputs.payload["esm2_embedding"]) == 1280


def test_l1_invalid_selfies_triggers_f001(lactose_input):
    bad_input = dict(lactose_input)
    bad_input["target_compound"] = {"selfies": "[NOT_VALID_SELFIES_TOKEN][", "inchi_key": "X"}
    adapter = L1ZPEAdapter(execution_mode=ExecutionMode.local_cpu)
    env = adapter.run(
        campaign_id="test_l1_bad_selfies",
        domain=Domain.hmo,
        organism=562,
        gem_id="iML1515",
        input_payload=bad_input,
    )
    assert env.falsification.gate_status == GateStatus.fail
    assert any(f.gate_id == "f001_invalid_selfies" for f in env.falsification.failures)


def test_zpe_word_envelope_is_deterministic(lactose_input):
    s = _lactose_selfies()
    a = _zpe_envelope(s)
    b = _zpe_envelope(s)
    assert a == b


def test_hash_derived_embedding_is_unit_norm():
    e = _hash_derived_embedding(b"any seed")
    assert len(e) == 1280
    norm = sum(x * x for x in e) ** 0.5
    assert abs(norm - 1.0) < 1e-9


def test_l1_envelope_id_is_stable_for_same_inputs(lactose_input):
    """The same logical inputs should produce the same envelope_id (modulo
    runtime fields). This is the structural invariant for the
    plug-replaceability and Runpod cutover proof tests in Wave 11."""
    adapter1 = L1ZPEAdapter(execution_mode=ExecutionMode.local_cpu)
    adapter2 = L1ZPEAdapter(execution_mode=ExecutionMode.local_cpu)
    # Use a fixed run_id so the only differences are timing-related.
    import uuid

    rid = uuid.UUID("00000000-0000-0000-0000-000000000123")
    env1 = adapter1.run(
        campaign_id="stable_test",
        domain=Domain.hmo,
        organism=562,
        gem_id="iML1515",
        input_payload=lactose_input,
        run_id=rid,
    )
    env2 = adapter2.run(
        campaign_id="stable_test",
        domain=Domain.hmo,
        organism=562,
        gem_id="iML1515",
        input_payload=lactose_input,
        run_id=rid,
    )
    # Output payload hash is stable; full envelope_id differs only on
    # provenance.created_at.
    assert env1.outputs.payload == env2.outputs.payload
    assert env1.provenance.input_hash == env2.provenance.input_hash
    assert env1.provenance.output_hash == env2.provenance.output_hash
    assert env1.provenance.config_hash == env2.provenance.config_hash
