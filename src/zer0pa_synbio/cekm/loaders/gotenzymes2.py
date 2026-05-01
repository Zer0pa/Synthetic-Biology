"""GotEnzymes2 loader.

Source: GotEnzymes2 (https://gotenzymes.io/), CC BY 4.0,
license_class=A per audit/source_manifests/gotenzymes2.yaml.

GotEnzymes2 contains 59.6M predicted enzyme-substrate-condition
entries with model-derived kcat / Km labels. Per PRD §12.1, these
are treated as **soft pseudo-labels** in CEKM training (curriculum
pre-training only); the loss weight on these rows is lower than on
BRENDA + EnzyExtract positives.

Provenance:
    Bulk pull from https://gotenzymes.io/ (per their access terms).
    Expected format: JSONL — one JSON record per line.

Schema (per record):
    ``{
       "uniprot_id": "...",
       "substrate_inchi_key": "...",
       "organism_taxonomy_id": 562,
       "temperature_c": 37.0,
       "ph": 7.0,
       "kcat_per_s": 12.3,
       "km_mm": 0.8,
       "model_confidence": 0.85
    }``

The loader marks all rows with citation prefix
``"[soft pseudo-label]"`` so downstream loss-weighting can be applied.
"""

from __future__ import annotations

import json
from pathlib import Path

from zer0pa_synbio.cekm import CorpusSlice, KineticsRow


CITATION = (
    "[soft pseudo-label] GotEnzymes2: 59.6M predicted enzyme-substrate-"
    "condition entries; CC BY 4.0. Used as curriculum pre-training only "
    "per PRD §12.1."
)


def load_gotenzymes2_jsonl(path: Path) -> CorpusSlice:
    """Parse a GotEnzymes2 JSONL bulk dump into a ``CorpusSlice``."""
    if not path.exists():
        raise FileNotFoundError(
            f"GotEnzymes2 JSONL not found at {path}. "
            "Provision via bulk pull from https://gotenzymes.io/."
        )
    rows: list[KineticsRow] = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            uniprot = (rec.get("uniprot_id") or "").strip()
            substrate = (rec.get("substrate_inchi_key") or "").strip()
            kcat = rec.get("kcat_per_s")
            km = rec.get("km_mm")
            if not uniprot or not substrate:
                continue
            if kcat is None and km is None:
                continue
            confidence = rec.get("model_confidence")
            citation = CITATION
            if confidence is not None:
                citation = f"{citation} confidence={confidence:.2f}"
            rows.append(
                KineticsRow(
                    enzyme_uniprot_id=uniprot,
                    substrate_inchi_key=substrate,
                    organism_taxonomy_id=int(rec.get("organism_taxonomy_id", 0) or 0),
                    temperature_c=float(rec.get("temperature_c", 25.0) or 25.0),
                    ph=float(rec.get("ph", 7.0) or 7.0),
                    kcat_per_s=float(kcat) if kcat is not None else None,
                    km_mm=float(km) if km is not None else None,
                    source="gotenzymes2",
                    citation=citation,
                    license_class="A",
                )
            )
    return CorpusSlice(source="gotenzymes2", license_class="A", rows=rows)


__all__ = ["load_gotenzymes2_jsonl"]
