"""ETL: GotEnzymes2 prediction CSVs (LiLabTsinghua/GotEnzymes2/Data/) →
JSONL matching the schema expected by zer0pa_synbio.cekm.loaders.gotenzymes2.

The upstream repo provides 19 model-prediction CSVs across kcat, Km,
kcat/Km, Topt, Tm. v0.1 corpus uses UniKP_KCAT × UniKP_KM (the
README-recommended best-performer combination) merged on
(Sequence, Smiles, EC, Organism).

Output: data/raw/gotenzymes2/gotenzymes2_bulk.jsonl
        ~16,890 rows × ~12 MB.

Re-run after refreshing data/raw/gotenzymes2/raw_csvs/ from the
upstream GitHub repo.
"""

from __future__ import annotations

import json
import math
import pathlib
import sys


def main() -> int:
    try:
        import pandas as pd
    except ImportError:
        print("pandas required for GotEnzymes2 ETL", file=sys.stderr)
        return 2

    repo_root = pathlib.Path(__file__).resolve().parents[2]
    raw = repo_root / "data" / "raw" / "gotenzymes2" / "raw_csvs"
    out_path = repo_root / "data" / "raw" / "gotenzymes2" / "gotenzymes2_bulk.jsonl"

    kcat_csv = raw / "UniKP_KCAT_prediction_new.csv"
    km_csv = raw / "UniKP_KM_prediction_new.csv"
    if not kcat_csv.exists() or not km_csv.exists():
        print(
            f"Missing upstream CSVs at {raw}. "
            "Download from "
            "https://github.com/LiLabTsinghua/GotEnzymes2/tree/main/Data first.",
            file=sys.stderr,
        )
        return 3

    print(f"Loading {kcat_csv.name}…")
    kcat = pd.read_csv(kcat_csv)
    print(f"Loading {km_csv.name}…")
    km = pd.read_csv(km_csv)

    merge_keys = ["Sequence", "Smiles", "ECNumber", "Organism"]
    merged = kcat.merge(km, on=merge_keys, how="inner", suffixes=("_kcat", "_km"))
    print(f"Merged: {len(merged):,} rows")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    n_written = 0
    with out_path.open("w", encoding="utf-8") as out:
        for r in merged.itertuples(index=False):
            try:
                kcat_log = float(r.Prediction_kcat)
                km_log = float(r.Prediction_km)
                if not (math.isfinite(kcat_log) and math.isfinite(km_log)):
                    continue
                seq = (r.Sequence or "").strip()
                smiles = (r.Smiles or "").strip()
                if not seq or not smiles:
                    continue
                rec = {
                    "uniprot_id": "GE2_" + str(hash(seq) & 0xFFFFFFFF),
                    "substrate_inchi_key": smiles,
                    "organism_taxonomy_id": 0,
                    "temperature_c": 25.0,
                    "ph": 7.0,
                    "kcat_per_s": 10.0 ** kcat_log,
                    "km_mm": 10.0 ** km_log,
                    "model_confidence": 0.7,
                    "ec_number": str(r.ECNumber) if r.ECNumber is not None else "",
                    "organism_name": str(r.Organism) if r.Organism is not None else "",
                    "sequence_aa": seq,
                }
                out.write(json.dumps(rec) + "\n")
                n_written += 1
            except Exception:
                pass
    size_mb = out_path.stat().st_size / 1024 / 1024
    print(f"Wrote {n_written:,} rows to {out_path} ({size_mb:.1f} MB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
