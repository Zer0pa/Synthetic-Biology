"""CEKM corpus loader integration tests.

Per HANDOFF-CPU-CONTINUATION.md item D and PRD §12.1.

Each loader is a pure parser over a locally-resident dataset file.
The tests use small fixtures under ``fixtures/cekm_loaders/`` that
match the upstream schema. A pod-side tar of real BRENDA / EnzyExtract
/ GotEnzymes2 / ProteinGym is the operational data source on Wave 4.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from zer0pa_synbio.cekm import (
    CorpusSlice,
    KineticsRow,
    assemble_corpus,
    held_out_split,
)
from zer0pa_synbio.cekm.loaders import (
    brenda_bulk,
    enzyextract,
    gotenzymes2,
    proteingym,
    load_corpus_slices_from_config,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
FIX = REPO_ROOT / "fixtures" / "cekm_loaders"


def test_load_brenda_tsv():
    slice_ = brenda_bulk.load_brenda_tsv(FIX / "brenda_mini.tsv")
    assert slice_.source == "brenda"
    assert slice_.license_class == "A"
    assert len(slice_.rows) == 7
    # FutC entry maps to known UniProt + InChI key.
    futc = next(r for r in slice_.rows if r.enzyme_uniprot_id == "Q11075")
    assert futc.substrate_inchi_key == "GUBGYTABKSRVRQ-PICCSMPSSA-N"
    assert futc.kcat_per_s == 125.0
    assert futc.km_mm == 0.45
    assert futc.organism_taxonomy_id == 562
    assert futc.source == "brenda"


def test_brenda_loader_skips_empty_kinetics_rows(tmp_path):
    tsv = tmp_path / "brenda.tsv"
    tsv.write_text(
        "uniprot_id\tsubstrate_inchi_key\torganism_taxonomy_id\ttemperature_c\tph\t"
        "kcat_per_s\tkm_mm\tcitation\n"
        "Q11075\tGUBGYTABKSRVRQ-PICCSMPSSA-N\t562\t37.0\t7.0\t100.0\t0.5\tref1\n"
        # Empty kinetic measurements → skip
        "P12345\tABCDE-FGHIJ-K\t9606\t37.0\t7.0\t\t\tref2\n",
        encoding="utf-8",
    )
    slice_ = brenda_bulk.load_brenda_tsv(tsv)
    assert len(slice_.rows) == 1


def test_brenda_loader_raises_on_missing_file(tmp_path):
    with pytest.raises(FileNotFoundError, match="BRENDA TSV not found"):
        brenda_bulk.load_brenda_tsv(tmp_path / "nope.tsv")


def test_load_enzyextract_tsv():
    slice_ = enzyextract.load_enzyextract_tsv(FIX / "enzyextract_mini.tsv")
    assert slice_.source == "enzyextract"
    assert slice_.license_class == "A"
    assert len(slice_.rows) == 5
    # Dark-matter entries (brenda_present=False) should be tagged in citation.
    dark = [r for r in slice_.rows if "BRENDA-absent dark-matter" in r.citation]
    assert len(dark) == 2


def test_load_gotenzymes2_jsonl():
    slice_ = gotenzymes2.load_gotenzymes2_jsonl(FIX / "gotenzymes2_mini.jsonl")
    assert slice_.source == "gotenzymes2"
    assert slice_.license_class == "A"
    assert len(slice_.rows) == 4
    # All rows should be tagged as soft pseudo-labels.
    for r in slice_.rows:
        assert "soft pseudo-label" in r.citation


def test_load_proteingym_csv():
    slice_ = proteingym.load_proteingym_csv(FIX / "proteingym_mini.csv")
    assert slice_.source == "proteingym"
    assert slice_.license_class == "A"
    assert len(slice_.rows) == 5
    # ProteinGym rows carry no kcat / km — only fitness scores in the citation.
    for r in slice_.rows:
        assert r.kcat_per_s is None
        assert r.km_mm is None
        assert r.substrate_inchi_key.startswith("DMS|")


def test_aggregator_assembles_all_four_sources():
    """End-to-end: all four loaders → assemble_corpus → held_out_split.
    Verifies the data shape feeds into existing CEKM CPU pipeline."""

    class _Cfg:
        brenda_tsv_path = str(FIX / "brenda_mini.tsv")
        enzyextract_tsv_path = str(FIX / "enzyextract_mini.tsv")
        gotenzymes2_jsonl_path = str(FIX / "gotenzymes2_mini.jsonl")
        proteingym_csv_path = str(FIX / "proteingym_mini.csv")

    slices = load_corpus_slices_from_config(_Cfg())
    assert len(slices) == 4
    rows = assemble_corpus(slices)
    # 7 BRENDA + 5 EnzyExtract + 4 GotEnzymes2 + 5 ProteinGym = 21
    assert len(rows) == 21
    # Held-out split honours enzyextract_holdout_full=True (5 EnzyExtract
    # rows must all be in held_out).
    split = held_out_split(rows, seed=0, enzyextract_holdout_full=True)
    enzyextract_rows = [r for r in rows if r.source == "enzyextract"]
    for r in enzyextract_rows:
        assert r.row_id in split.held_out_row_ids


def test_aggregator_skips_missing_paths():
    """If only some paths are configured, only those slices are returned."""

    class _Cfg:
        brenda_tsv_path = str(FIX / "brenda_mini.tsv")
        enzyextract_tsv_path = None
        gotenzymes2_jsonl_path = None
        proteingym_csv_path = None

    slices = load_corpus_slices_from_config(_Cfg())
    assert len(slices) == 1
    assert slices[0].source == "brenda"
