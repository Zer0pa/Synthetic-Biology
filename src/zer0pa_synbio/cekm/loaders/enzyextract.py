"""EnzyExtract loader.

Source: HanselYu/EnzyExtract on GitHub, MIT license, license_class=A
per audit/source_manifests/enzyextract.yaml.

Provenance:
    git clone https://github.com/HanselYu/EnzyExtract
    Path of interest: ``data/parameters.tsv`` (or equivalent).

EnzyExtract contributes 218,095 enzyme kinetic entries extracted from
the literature, of which 89,544 are NOT present in BRENDA — this
"dark matter" partition is the survivorship-bias defence per PRD
§12.1 and is fully held out from training (see HeldOutSplit
``enzyextract_holdout_full=True``).

Schema (TSV; column names taken from the upstream README):
    ``protein_uniprot, substrate_smiles_or_inchikey, organism_taxon,
    temp_c, ph, kcat_s, km_mm, brenda_present, doi``

The ``brenda_present`` flag is captured in the citation string for
audit but is not used to gate inclusion — that gating happens in
``held_out_split``.
"""

from __future__ import annotations

import csv
from pathlib import Path

from zer0pa_synbio.cekm import CorpusSlice, KineticsRow


CITATION = (
    "EnzyExtract (HanselYu/EnzyExtract, MIT). 218,095 enzyme kinetic "
    "entries extracted from literature; 89,544 absent from BRENDA "
    "per source-briefs/02 §1.2."
)


def _parse_optional_float(s: str) -> float | None:
    s = s.strip()
    if not s or s.lower() in {"none", "null", "nan", "n/a"}:
        return None
    try:
        return float(s)
    except ValueError:
        return None


def load_enzyextract_tsv(path: Path) -> CorpusSlice:
    """Parse EnzyExtract's parameters.tsv into a ``CorpusSlice``.

    Recognised columns (case-insensitive; alternate names accepted):
      - protein_uniprot / uniprot_id
      - substrate_inchi_key / substrate_smiles
      - organism_taxon / organism_taxonomy_id
      - temp_c / temperature_c
      - ph
      - kcat_s / kcat_per_s
      - km_mm
      - brenda_present (optional; appended to citation if "False")
      - doi (optional; appended to citation)
    """
    if not path.exists():
        raise FileNotFoundError(
            f"EnzyExtract TSV not found at {path}. "
            "Provision via: git clone https://github.com/HanselYu/EnzyExtract"
        )
    rows: list[KineticsRow] = []
    with open(path, encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")
        # Build a case-insensitive column index.
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
            kcat = _parse_optional_float(col(record, "kcat_s", "kcat_per_s"))
            km = _parse_optional_float(col(record, "km_mm"))
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
                    temperature_c=_parse_optional_float(col(record, "temp_c", "temperature_c"))
                    or 25.0,
                    ph=_parse_optional_float(col(record, "ph")) or 7.0,
                    kcat_per_s=kcat,
                    km_mm=km,
                    source="enzyextract",
                    citation=citation,
                    license_class="A",
                )
            )
    return CorpusSlice(source="enzyextract", license_class="A", rows=rows)


__all__ = ["load_enzyextract_tsv"]
