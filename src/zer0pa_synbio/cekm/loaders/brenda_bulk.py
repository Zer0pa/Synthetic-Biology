"""BRENDA bulk-dump loader.

Source: BRENDA (https://www.brenda-enzymes.org/), CC BY 4.0,
license_class=A per audit/source_manifests/brenda.yaml.

Bulk download:
    https://www.brenda-enzymes.org/download.php (registration required;
    file ``brenda_data.txt.gz``).

Schema (TSV, gzipped or plain):
    Each row: ``ec_number\tuniprot_id\torganism_taxonomy_id\tsubstrate_inchi_key
    \ttemperature_c\tph\tkcat_per_s\tkm_mm\tcitation``

Real BRENDA exports use a richer record format (per-enzyme blocks of
KCAT/KM/PH/TEMPERATURE entries); this loader expects the *flattened*
TSV that downstream tooling produces. Pre-process with the BRENDA-API
``brenda-textmining`` Python package or equivalent to flatten before
feeding here.

Reference: Chang, A. et al. BRENDA, the ELIXIR core data resource in
2021: new developments and updates. Nucleic Acids Res. (2021).
"""

from __future__ import annotations

import csv
import gzip
import io
from pathlib import Path

from zer0pa_synbio.cekm import CorpusSlice, KineticsRow


CITATION = (
    "Chang, A. et al. BRENDA, the ELIXIR core data resource in 2021: "
    "new developments and updates. Nucleic Acids Res. (2021). CC BY 4.0."
)


def _open(path: Path):
    """Open ``path`` whether gzipped or plain text."""
    if str(path).endswith(".gz"):
        return io.TextIOWrapper(gzip.open(path, "rb"), encoding="utf-8")
    return open(path, encoding="utf-8")


def _parse_optional_float(s: str) -> float | None:
    s = s.strip()
    if not s or s.lower() in {"none", "null", "nan", "n/a"}:
        return None
    try:
        return float(s)
    except ValueError:
        return None


def load_brenda_tsv(path: Path) -> CorpusSlice:
    """Parse a flattened BRENDA TSV into a ``CorpusSlice``.

    Expected columns (case-insensitive header match):
      ``ec_number, uniprot_id, organism_taxonomy_id, substrate_inchi_key,
      temperature_c, ph, kcat_per_s, km_mm, citation``

    Rows missing both ``kcat_per_s`` and ``km_mm`` are skipped (no
    measurement to learn from).
    """
    if not path.exists():
        raise FileNotFoundError(
            f"BRENDA TSV not found at {path}. "
            "Download via https://www.brenda-enzymes.org/download.php "
            "(requires registration)."
        )
    rows: list[KineticsRow] = []
    with _open(path) as f:
        reader = csv.DictReader(f, delimiter="\t")
        for record in reader:
            uniprot = (record.get("uniprot_id") or "").strip()
            substrate = (record.get("substrate_inchi_key") or "").strip()
            if not uniprot or not substrate:
                continue
            kcat = _parse_optional_float(record.get("kcat_per_s", ""))
            km = _parse_optional_float(record.get("km_mm", ""))
            if kcat is None and km is None:
                continue
            try:
                organism = int(record.get("organism_taxonomy_id", "0"))
            except ValueError:
                organism = 0
            rows.append(
                KineticsRow(
                    enzyme_uniprot_id=uniprot,
                    substrate_inchi_key=substrate,
                    organism_taxonomy_id=organism,
                    temperature_c=_parse_optional_float(record.get("temperature_c", ""))
                    or 25.0,
                    ph=_parse_optional_float(record.get("ph", "")) or 7.0,
                    kcat_per_s=kcat,
                    km_mm=km,
                    source="brenda",
                    citation=record.get("citation") or CITATION,
                    license_class="A",
                )
            )
    return CorpusSlice(source="brenda", license_class="A", rows=rows)


__all__ = ["load_brenda_tsv"]
