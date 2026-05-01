"""CEKM CPU prototype data-pipeline contract tests."""

from __future__ import annotations

import pytest

from zer0pa_synbio.cekm import (
    CorpusSlice,
    KineticsRow,
    assemble_corpus,
    held_out_split,
    sample_adversarial_negatives,
    smoke_test_pipeline,
)

pytestmark = pytest.mark.contract


def test_class_d_source_rejected_in_assemble():
    bad_slice = CorpusSlice(
        source="brenda",
        license_class="D",  # not allowed
        rows=[],
    )
    with pytest.raises(ValueError, match="Class D/E"):
        assemble_corpus([bad_slice])


def test_assemble_dedupes_by_row_id():
    row = KineticsRow(
        enzyme_uniprot_id="X",
        substrate_inchi_key="Y",
        organism_taxonomy_id=562,
        temperature_c=37.0,
        ph=7.0,
        kcat_per_s=10.0,
        km_mm=0.1,
        source="brenda",
    )
    s1 = CorpusSlice(source="brenda", license_class="A", rows=[row, row])
    s2 = CorpusSlice(source="brenda", license_class="A", rows=[row])
    out = assemble_corpus([s1, s2])
    assert len(out) == 1


def test_held_out_split_full_enzyextract_holdout():
    rows = [
        KineticsRow(
            enzyme_uniprot_id=f"X{i}",
            substrate_inchi_key=f"S{i}",
            organism_taxonomy_id=562,
            temperature_c=37.0,
            ph=7.0,
            kcat_per_s=10.0,
            km_mm=0.1,
            source="enzyextract",
        )
        for i in range(20)
    ]
    split = held_out_split(rows, holdout_fraction=0.15, seed=42)
    # All EnzyExtract rows are held out per PRD §12.3.
    assert len(split.held_out_row_ids) == 20
    assert len(split.in_corpus_row_ids) == 0


def test_adversarial_sampler_emits_three_tiers_per_positive():
    positives = [
        KineticsRow(
            enzyme_uniprot_id=f"X{i}",
            substrate_inchi_key=f"S{i}",
            organism_taxonomy_id=562,
            temperature_c=37.0,
            ph=7.0,
            kcat_per_s=10.0,
            km_mm=0.1,
            source="brenda",
        )
        for i in range(5)
    ]
    decoys = [f"D{i}" for i in range(20)]
    negs = sample_adversarial_negatives(positives, decoys, seed=42)
    assert len(negs) == 5 * 3
    assert sum(1 for n in negs if n.tier == "alpha") == 5
    assert sum(1 for n in negs if n.tier == "beta") == 5
    assert sum(1 for n in negs if n.tier == "gamma") == 5
    # Tier-distance-factor invariant.
    factors = {n.tier: n.active_site_distance_factor for n in negs}
    assert factors["alpha"] == 0.5
    assert factors["beta"] == 1.0
    assert factors["gamma"] == 2.0


def test_smoke_test_pipeline_runs_end_to_end():
    summary = smoke_test_pipeline()
    assert summary["schema_version"] == "synbio.cekm_smoke.v0.1"
    assert summary["corpus_size"] == 100  # 50 + 20 + 30
    assert summary["held_out_size"] >= 20  # all enzyextract + ~15% brenda
    # Three tiers of negatives per in-corpus positive.
    assert summary["adversarial_negative_count"] == summary["in_corpus_size"] * 3
    assert summary["tier_alpha_count"] == summary["in_corpus_size"]
    assert summary["tier_beta_count"] == summary["in_corpus_size"]
    assert summary["tier_gamma_count"] == summary["in_corpus_size"]
