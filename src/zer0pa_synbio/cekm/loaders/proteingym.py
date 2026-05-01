"""ProteinGym DMS loader.

Source: OATML-Markslab/ProteinGym, MIT license, license_class=A per
audit/source_manifests/proteingym.yaml.

ProteinGym aggregates ~2.7M missense variants across 217 deep
mutational scanning (DMS) assays. Per PRD §12.1, ProteinGym
contributes the *protein-fitness* arm of the CEKM corpus — not direct
kcat/Km records. The loader emits ``KineticsRow`` records with
``kcat=None, km=None`` and the variant identity encoded in
``substrate_inchi_key`` (a synthetic key of the form
``"DMS|<assay_id>|<variant>"``). The downstream training loop
recognises ProteinGym rows by ``source=="proteingym"`` and feeds them
through the protein-fitness loss head.

Provenance:
    git clone https://github.com/OATML-Markslab/ProteinGym
    Path of interest: ``ProteinGym_substitutions/`` (one CSV per
    assay) or the ``DMS_substitutions.csv`` reference summary file.

Reference: Notin, P. et al. ProteinGym: large-scale benchmarks for
protein design and fitness prediction. NeurIPS (2023).
"""

from __future__ import annotations

import csv
from pathlib import Path

from zer0pa_synbio.cekm import CorpusSlice, KineticsRow


CITATION = (
    "Notin, P. et al. ProteinGym: large-scale benchmarks for protein "
    "design and fitness prediction. NeurIPS (2023). MIT."
)


def _parse_optional_float(s: str) -> float | None:
    s = s.strip()
    if not s or s.lower() in {"none", "null", "nan", "n/a"}:
        return None
    try:
        return float(s)
    except ValueError:
        return None


def load_proteingym_csv(path: Path) -> CorpusSlice:
    """Parse a ProteinGym substitutions reference CSV.

    Recognised columns (case-insensitive):
      - DMS_id / assay_id
      - target_seq / sequence
      - mutant / mutation_code
      - DMS_score / fitness_score
      - target_organism / organism_taxonomy_id (optional)
      - uniprot_id (optional; falls back to DMS_id)
    """
    if not path.exists():
        raise FileNotFoundError(
            f"ProteinGym CSV not found at {path}. "
            "Provision via: git clone https://github.com/OATML-Markslab/ProteinGym"
        )
    rows: list[KineticsRow] = []
    with open(path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames is None:
            return CorpusSlice(source="proteingym", license_class="A", rows=[])
        norm = {k.lower(): k for k in reader.fieldnames}

        def col(record: dict, *names: str) -> str:
            for n in names:
                key = norm.get(n.lower())
                if key is not None and record.get(key) is not None:
                    return record[key]
            return ""

        for record in reader:
            assay = col(record, "DMS_id", "assay_id").strip()
            mutant = col(record, "mutant", "mutation_code").strip()
            uniprot = col(record, "uniprot_id").strip() or assay
            score = _parse_optional_float(col(record, "DMS_score", "fitness_score"))
            if not assay or not mutant:
                continue
            substrate_key = f"DMS|{assay}|{mutant}"
            try:
                organism = int(col(record, "organism_taxonomy_id") or "0")
            except ValueError:
                organism = 0
            citation = CITATION
            if score is not None:
                citation = f"{citation} dms_score={score:.3f}"
            rows.append(
                KineticsRow(
                    enzyme_uniprot_id=uniprot,
                    substrate_inchi_key=substrate_key,
                    organism_taxonomy_id=organism,
                    temperature_c=25.0,
                    ph=7.0,
                    kcat_per_s=None,
                    km_mm=None,
                    source="proteingym",
                    citation=citation,
                    license_class="A",
                )
            )
    return CorpusSlice(source="proteingym", license_class="A", rows=rows)


__all__ = ["load_proteingym_csv"]
