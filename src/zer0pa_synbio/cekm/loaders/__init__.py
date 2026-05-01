"""CEKM corpus loaders.

Per HANDOFF-CPU-CONTINUATION.md item D and PRD §12.1.

Each loader parses a locally-resident copy of a permissively-licensed
kinetics dataset and emits a ``CorpusSlice`` of ``KineticsRow`` records.
The loader functions are pure parsers — they do NOT download data;
the operator pre-downloads (via wget / git clone) on the GPU pod
before invoking ``synbio cekm train``.

Sources:

- ``brenda_bulk.load_brenda_tsv(path)`` — BRENDA core (CC BY 4.0,
  Class A). Bulk download requires registration at
  https://www.brenda-enzymes.org/download.php; the file is a gzipped
  TSV with one row per ``(enzyme, substrate, organism, condition)``
  measurement.
- ``enzyextract.load_enzyextract_tsv(path)`` — EnzyExtract (MIT,
  Class A). Direct download from https://github.com/ChemBioHTP/EnzyExtract
  (file ``EnzyExtractDB/EnzyExtractDB_176463.parquet``, ~10 MB,
  176,463 rows). The function name retains the ``_tsv`` suffix for
  backward compatibility but auto-dispatches to the parquet reader
  by extension.
- ``gotenzymes2.load_gotenzymes2_jsonl(path)`` — GotEnzymes2 (CC BY 4.0,
  Class A). Bulk pull from https://gotenzymes.io/. Marked as
  curriculum / soft-pseudo-label per PRD §12.1.
- ``proteingym.load_proteingym_csv(path)`` — ProteinGym DMS dataset
  (MIT, Class A). git clone https://github.com/OATML-Markslab/ProteinGym;
  parse the substitution-DMS reference CSV. ProteinGym contributes the
  protein-fitness arm of CEKM, not direct kcat/Km records — the loader
  emits placeholder ``kcat=None, Km=None`` rows tagged with
  ``source="proteingym"`` whose substrate/condition fields encode the
  variant identity for the ESM-2 / D-MPNN encoders.

Aggregator:

- ``load_corpus_slices_from_config(cfg)`` — read ``cfg.brenda_tsv_path``
  etc. from a ``TrainingConfig`` and return a list of ``CorpusSlice``.
  Missing-path slices are skipped silently so a config can opt into
  any subset of sources.

License-class enforcement: each loader hardcodes ``license_class``
matching ``audit/source_manifests/<source>.yaml``. Class C/D/E sources
are not supported here — by construction the four supported sources
are all Class A.
"""

from __future__ import annotations

from pathlib import Path

from zer0pa_synbio.cekm import CorpusSlice
from zer0pa_synbio.cekm.loaders import (
    brenda_bulk,
    enzyextract,
    gotenzymes2,
    proteingym,
)


def load_corpus_slices_from_config(cfg) -> list[CorpusSlice]:
    """Return CorpusSlice list per the four loader paths on cfg.

    Recognised attributes (any may be ``None`` to skip that source):
    - ``brenda_tsv_path``
    - ``enzyextract_tsv_path``
    - ``gotenzymes2_jsonl_path``
    - ``proteingym_csv_path``
    """
    out: list[CorpusSlice] = []
    brenda_path = getattr(cfg, "brenda_tsv_path", None)
    if brenda_path:
        out.append(brenda_bulk.load_brenda_tsv(Path(brenda_path)))
    enzyextract_path = getattr(cfg, "enzyextract_tsv_path", None)
    if enzyextract_path:
        out.append(enzyextract.load_enzyextract_tsv(Path(enzyextract_path)))
    gotenzymes2_path = getattr(cfg, "gotenzymes2_jsonl_path", None)
    if gotenzymes2_path:
        out.append(gotenzymes2.load_gotenzymes2_jsonl(Path(gotenzymes2_path)))
    proteingym_path = getattr(cfg, "proteingym_csv_path", None)
    if proteingym_path:
        out.append(proteingym.load_proteingym_csv(Path(proteingym_path)))
    return out


__all__ = [
    "brenda_bulk",
    "enzyextract",
    "gotenzymes2",
    "proteingym",
    "load_corpus_slices_from_config",
]
