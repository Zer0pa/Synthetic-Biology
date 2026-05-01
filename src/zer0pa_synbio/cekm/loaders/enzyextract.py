"""EnzyExtract loader.

Source: ``ChemBioHTP/EnzyExtract`` on GitHub, MIT license,
license_class=A per audit/source_manifests/enzyextract.yaml.

Provenance:
    Direct download:
        https://github.com/ChemBioHTP/EnzyExtract/raw/main/EnzyExtractDB/EnzyExtractDB_176463.parquet
    Format: Apache Parquet, 176,463 rows.

The upstream parquet schema (verified 2026-05) has 39 columns. The
loader reads the columns relevant to CEKM training:
    - ``uniprot``               → enzyme_uniprot_id
    - ``smiles``                → substrate_inchi_key (SMILES used as
                                  the canonical substrate identifier
                                  when InChIKey unavailable)
    - ``kcat_value``            → kcat (per second)
    - ``km_value``              → Km (molar; converted to mM ×1000)
    - ``temperature``, ``pH``   → conditions
    - ``brenda_id``             → presence flag for the
                                  survivorship-bias dark-matter check
    - ``flag.hallucination``,
      ``flag.scientific``       → quality filters; rows with hallucination
                                  flag set are skipped

EnzyExtract contributes 176,463 enzyme kinetic entries extracted from
the literature. Rows where ``brenda_id`` is null are the "dark
matter" partition that materially reduces survivorship bias per PRD
§12.1; the held-out split fully holds these out.

The loader retains the legacy entrypoint name
``load_enzyextract_tsv`` for backward compatibility with the
aggregator and tests; it now reads parquet under the hood.
"""

from __future__ import annotations

import math
from pathlib import Path

from zer0pa_synbio.cekm import CorpusSlice, KineticsRow


CITATION = (
    "EnzyExtract (ChemBioHTP/EnzyExtract, MIT). 176,463 enzyme kinetic "
    "entries extracted from literature."
)


def _to_optional_float(value) -> float | None:
    if value is None:
        return None
    try:
        f = float(value)
    except (TypeError, ValueError):
        return None
    if math.isnan(f):
        return None
    return f


def load_enzyextract_parquet(path: Path) -> CorpusSlice:
    """Parse EnzyExtract's parquet dump into a ``CorpusSlice``.

    Skips rows missing both kcat_value and km_value, and rows whose
    ``flag.hallucination`` is set.
    """
    if not path.exists():
        raise FileNotFoundError(
            f"EnzyExtract parquet not found at {path}. "
            "Provision via: curl -fsSL "
            "https://github.com/ChemBioHTP/EnzyExtract/raw/main/EnzyExtractDB/EnzyExtractDB_176463.parquet "
            f"-o {path}"
        )
    try:
        import pandas as pd  # type: ignore[import-not-found]
    except ImportError as exc:
        raise RuntimeError(
            "pandas is required to load the EnzyExtract parquet"
        ) from exc

    df = pd.read_parquet(path)
    rows: list[KineticsRow] = []
    for record in df.itertuples(index=False):
        # Quality filter: drop hallucinated entries.
        hallu = getattr(record, "_38", None)  # `flag.hallucination` lacks a clean attr name
        try:
            hallu_v = float(hallu) if hallu is not None else 0.0
            if not math.isnan(hallu_v) and hallu_v > 0:
                continue
        except (TypeError, ValueError):
            pass

        uniprot = (getattr(record, "uniprot", None) or "")
        smiles = (getattr(record, "smiles", None) or "")
        if not uniprot or not smiles:
            continue
        kcat = _to_optional_float(getattr(record, "kcat_value", None))
        km_M = _to_optional_float(getattr(record, "km_value", None))
        km_mM = km_M * 1000.0 if km_M is not None else None
        if kcat is None and km_mM is None:
            continue

        # Dark-matter detection: brenda_id null → not in BRENDA.
        brenda_id = getattr(record, "brenda_id", None)
        is_dark_matter = brenda_id is None or (
            isinstance(brenda_id, float) and math.isnan(brenda_id)
        )

        # PMID + DOI go in the citation; the upstream parquet exposes pmid only.
        pmid = getattr(record, "pmid", None) or ""
        citation = f"{CITATION} pmid={pmid}" if pmid else CITATION
        if is_dark_matter:
            citation += " [BRENDA-absent dark-matter partition]"

        # Organism taxonomy ID isn't in the upstream parquet — it has
        # an organism *name* string. Without an NCBI Taxonomy lookup,
        # we record 0 and let the ESM-2 / D-MPNN encoders rely on the
        # sequence + SMILES.
        organism = 0
        rows.append(
            KineticsRow(
                enzyme_uniprot_id=str(uniprot),
                substrate_inchi_key=str(smiles),
                organism_taxonomy_id=organism,
                temperature_c=_to_optional_float(getattr(record, "temperature", None)) or 25.0,
                ph=_to_optional_float(getattr(record, "pH", None)) or 7.0,
                kcat_per_s=kcat,
                km_mm=km_mM,
                source="enzyextract",
                citation=citation,
                license_class="A",
            )
        )
    return CorpusSlice(source="enzyextract", license_class="A", rows=rows)


def _load_enzyextract_tsv_legacy(path: Path) -> CorpusSlice:
    """Read the legacy hand-curated TSV format (used by mini fixtures
    + early prototype data). Kept for backward compatibility with
    existing test fixtures and any operator-flattened BRENDA-style
    TSVs that follow the same column layout.
    """
    import csv

    if not path.exists():
        raise FileNotFoundError(
            f"EnzyExtract TSV not found at {path}."
        )
    rows: list[KineticsRow] = []
    with open(path, encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")
        if reader.fieldnames is None:
            return CorpusSlice(source="enzyextract", license_class="A", rows=[])
        norm = {k.lower(): k for k in reader.fieldnames}

        def col(record: dict, *names: str) -> str:
            for n in names:
                key = norm.get(n.lower())
                if key is not None and record.get(key) is not None:
                    return record[key]
            return ""

        for record in reader:
            uniprot = col(record, "protein_uniprot", "uniprot_id").strip()
            substrate = col(record, "substrate_inchi_key", "substrate_smiles").strip()
            if not uniprot or not substrate:
                continue
            kcat = _to_optional_float(col(record, "kcat_s", "kcat_per_s"))
            km = _to_optional_float(col(record, "km_mm"))
            if kcat is None and km is None:
                continue
            try:
                organism = int(col(record, "organism_taxon", "organism_taxonomy_id") or "0")
            except ValueError:
                organism = 0
            brenda_flag = col(record, "brenda_present").strip().lower()
            doi = col(record, "doi").strip()
            citation = CITATION
            if doi:
                citation = f"{citation} doi={doi}"
            if brenda_flag in {"false", "0", "no"}:
                citation += " [BRENDA-absent dark-matter partition]"
            rows.append(
                KineticsRow(
                    enzyme_uniprot_id=uniprot,
                    substrate_inchi_key=substrate,
                    organism_taxonomy_id=organism,
                    temperature_c=_to_optional_float(col(record, "temp_c", "temperature_c")) or 25.0,
                    ph=_to_optional_float(col(record, "ph")) or 7.0,
                    kcat_per_s=kcat,
                    km_mm=km,
                    source="enzyextract",
                    citation=citation,
                    license_class="A",
                )
            )
    return CorpusSlice(source="enzyextract", license_class="A", rows=rows)


def load_enzyextract_tsv(path: Path) -> CorpusSlice:
    """Auto-dispatching entrypoint: parquet for the upstream
    ``EnzyExtractDB_*.parquet`` shape, legacy TSV otherwise.

    The aggregator's ``cfg.enzyextract_tsv_path`` field name is kept
    for backward compatibility with existing configs and tests; the
    actual format is detected from the file extension.
    """
    p = Path(path)
    if str(p).endswith(".parquet"):
        return load_enzyextract_parquet(p)
    return _load_enzyextract_tsv_legacy(p)


__all__ = [
    "load_enzyextract_parquet",
    "load_enzyextract_tsv",
]
