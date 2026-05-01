"""LIRC corpus-build pipeline tests.

Per HANDOFF-CPU-CONTINUATION.md item C and PRD §6.2.

The full build hits public SPARQL/REST endpoints and takes ~4–8 h.
These tests use small synthetic inputs to exercise:

- Canonical-SMARTS computation via RDKit
- Cross-source merge via canonical-id hash
- Output round-trip through gzip JSON
- BLOCKED-source enforcement (excluded list is part of every output)
- ReactionRecord dataclass invariants

A network-touching slice test (``test_smoke_slice_runs_end_to_end``)
runs only when the env var ``LIRC_LIVE_NETWORK_TEST`` is set; it is
skipped by default to keep the suite hermetic.
"""

from __future__ import annotations

import gzip
import json
import os
from pathlib import Path

import pytest

from zer0pa_synbio.adapters.l2_lirc.build import (
    ReactionRecord,
    build_lirc_corpus,
    canonicalise_reaction_smarts,
    merge_records,
)


def test_canonicalise_reaction_smarts_round_trip():
    """Real RDKit reaction-SMARTS round-trip preserves the structure."""
    smarts = "[CH3:1][C:2](=[O:3])[OH:4]>>[CH3:1][C:2](=[O:3])[O-:4].[H+]"
    canonical = canonicalise_reaction_smarts(smarts)
    # RDKit may shuffle the SMARTS but must produce a valid canonical
    # form — re-canonicalising must be idempotent.
    assert canonical is not None
    assert canonicalise_reaction_smarts(canonical) == canonical


def test_canonicalise_returns_none_for_unparseable():
    assert canonicalise_reaction_smarts("not a real reaction") is None
    assert canonicalise_reaction_smarts("") is None


def test_merge_records_dedups_by_canonical_smarts():
    smarts = "[CH3:1][C:2](=[O:3])[OH:4]>>[CH3:1][C:2](=[O:3])[O-:4].[H+]"
    canonical = canonicalise_reaction_smarts(smarts)
    raw = [
        {
            "rhea_id": "RHEA:1",
            "equation": "acetate <=> deprotonated acetate",
            "canonical_smarts": canonical,
            "source_manifests": ["audit/source_manifests/rhea.yaml"],
            "license_class": "A",
            "brenda_ec_numbers": ["6.2.1.1"],
        },
        {
            "modelseed_id": "rxn00102",
            "equation": "(equivalent ModelSEED expression)",
            "canonical_smarts": canonical,
            "source_manifests": ["audit/source_manifests/modelseed.yaml"],
            "license_class": "A",
        },
    ]
    merged = merge_records(raw)
    assert len(merged) == 1
    rec = merged[0]
    assert rec.rhea_id == "RHEA:1"
    assert rec.modelseed_id == "rxn00102"
    assert "audit/source_manifests/rhea.yaml" in rec.source_manifests
    assert "audit/source_manifests/modelseed.yaml" in rec.source_manifests
    assert "6.2.1.1" in rec.brenda_ec_numbers


def test_merge_records_distinct_smarts_stay_separate():
    raw = [
        {
            "rhea_id": "RHEA:1",
            "equation": "A => B",
            "canonical_smarts": "[A]>>[B]",
        },
        {
            "rhea_id": "RHEA:2",
            "equation": "C => D",
            "canonical_smarts": "[C]>>[D]",
        },
    ]
    merged = merge_records(raw)
    assert len(merged) == 2


def test_build_lirc_corpus_writes_gzip_with_blocked_list(tmp_path, monkeypatch):
    """End-to-end build with all four pulls monkeypatched to return
    fixed synthetic rows. Verifies output structure and BLOCKED-source
    audit list is present in the corpus header."""
    fake_rhea = [
        {"rhea_id": "RHEA:1", "equation": "A => B"},
        {"rhea_id": "RHEA:2", "equation": "C => D"},
    ]
    fake_mnx = [
        {"source_id": "rheaR:1", "mnx_id": "MNXR1"},
        {"source_id": "rheaR:2", "mnx_id": "MNXR2"},
    ]
    fake_bigg = [{"bigg_id": "R_PFK", "name": "Phosphofructokinase"}]
    fake_modelseed = [
        {"id": "rxn00001", "equation": "X <=> Y"},
    ]

    monkeypatch.setattr(
        "zer0pa_synbio.adapters.l2_lirc.build.query_rhea_sparql",
        lambda **kw: fake_rhea,
    )
    monkeypatch.setattr(
        "zer0pa_synbio.adapters.l2_lirc.build.query_metanetx_xref",
        lambda **kw: fake_mnx,
    )
    monkeypatch.setattr(
        "zer0pa_synbio.adapters.l2_lirc.build.query_bigg_reactions",
        lambda **kw: fake_bigg,
    )
    monkeypatch.setattr(
        "zer0pa_synbio.adapters.l2_lirc.build.query_modelseed_reactions",
        lambda **kw: fake_modelseed,
    )

    out_path = tmp_path / "lirc_test.json.gz"
    summary = build_lirc_corpus(output_path=out_path)
    assert summary["rhea_pulled"] == 2
    assert summary["bigg_pulled"] == 1
    assert summary["modelseed_pulled"] == 1
    assert summary["metanetx_pulled"] == 2
    # Check the file exists and is gzipped JSON.
    assert out_path.exists()
    with gzip.open(out_path, "rt", encoding="utf-8") as f:
        payload = json.load(f)
    assert payload["schema_version"] == "synbio.lirc_corpus.v0.1"
    assert payload["license_class"] == "A"
    # BLOCKED sources are present in every output (audit transparency).
    blocked = payload["excluded_blocked"]
    assert any("atlas" in b.lower() for b in blocked)
    assert any("bkms" in b.lower() for b in blocked)
    assert any("kegg" in b.lower() for b in blocked)


def test_metanetx_xref_attaches_mnx_id_to_rhea_records(tmp_path, monkeypatch):
    """Cross-ref join: a Rhea record whose MNXref ID is in the MNXref
    pull should have ``metanetx_id`` populated."""
    fake_rhea = [{"rhea_id": "RHEA:14457", "equation": "GDP-Fuc + lactose => 2'-FL + GDP"}]
    fake_mnx = [{"source_id": "rheaR:14457", "mnx_id": "MNXR144857"}]
    monkeypatch.setattr(
        "zer0pa_synbio.adapters.l2_lirc.build.query_rhea_sparql",
        lambda **kw: fake_rhea,
    )
    monkeypatch.setattr(
        "zer0pa_synbio.adapters.l2_lirc.build.query_metanetx_xref",
        lambda **kw: fake_mnx,
    )
    monkeypatch.setattr(
        "zer0pa_synbio.adapters.l2_lirc.build.query_bigg_reactions",
        lambda **kw: [],
    )
    monkeypatch.setattr(
        "zer0pa_synbio.adapters.l2_lirc.build.query_modelseed_reactions",
        lambda **kw: [],
    )

    out_path = tmp_path / "lirc_test.json.gz"
    build_lirc_corpus(output_path=out_path)
    with gzip.open(out_path, "rt", encoding="utf-8") as f:
        payload = json.load(f)
    futc = next(r for r in payload["reactions"] if r["rhea_id"] == "RHEA:14457")
    assert futc["metanetx_id"] == "MNXR144857"


def test_reaction_record_dataclass_round_trips_through_dict():
    rec = ReactionRecord(
        canonical_id="abc123",
        rhea_id="RHEA:14457",
        bigg_id=None,
        brenda_ec_numbers=["2.4.1.69"],
        equation="A => B",
    )
    from dataclasses import asdict

    d = asdict(rec)
    rec2 = ReactionRecord(**d)
    assert rec2 == rec


@pytest.mark.skipif(
    "LIRC_LIVE_NETWORK_TEST" not in os.environ,
    reason="Network-touching test; set LIRC_LIVE_NETWORK_TEST=1 to enable.",
)
def test_smoke_slice_runs_end_to_end(tmp_path):
    """Live-network: pull a tiny slice from real Rhea/BiGG/ModelSEED."""
    out_path = tmp_path / "lirc_smoke.json.gz"
    summary = build_lirc_corpus(
        cap_rhea=10,
        cap_metanetx=10,
        cap_bigg=10,
        cap_modelseed=10,
        output_path=out_path,
    )
    assert summary["rhea_pulled"] >= 1
    assert summary["bigg_pulled"] >= 1
    assert summary["modelseed_pulled"] >= 1
    assert summary["unique_canonical_reactions"] >= 1
    assert out_path.exists()
