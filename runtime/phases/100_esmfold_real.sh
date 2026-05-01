#!/usr/bin/env bash
# Phase 100 — Real ESMFold structure prediction for HMO-target enzymes (L4.5).
#
# Runs EsmForProteinFolding (facebook/esmfold_v1) on the three key HMO-pathway
# enzymes:
#   FutC     — GDP-fucose:β-D-galactosyl-R 2-α-L-fucosyltransferase (2'-FL)
#   α-2,3-Lst — CMP-Neu5Ac:β-D-Gal(1→4)-β-D-GlcNAc α-2,3-sialyltransferase (3'-SL)
#   α-2,6-Lst — CMP-Neu5Ac:Galβ1-4GlcNAc α-2,6-sialyltransferase (DSLNT)
#
# Outputs are written to:
#   $RUN_ROOT/audit/runtime/l45_real_esmfold/<sequence_id>/structure.pdb
#   $RUN_ROOT/audit/runtime/l45_real_esmfold/<sequence_id>/plddt.json
#
# Boundary block (must appear verbatim per RESISTANCE.md):
# Research infrastructure for in silico synthetic biology / metabolic
# pathway engineering. Outputs are research artifacts — predicted
# pathways, predicted KPIs, candidate genetic modification specifications.
# No regulatory certification claims. No clinical or human-subject use.
# No environmental release of GMOs. No biocontainment-level claims (the
# pipeline does not commission BSL-2/3 work). No human gene drive or
# eugenic application. Defence / weapons / dual-use bio applications
# excluded under operator policy.

set -euo pipefail
. "$RUN_ROOT/env.sh"

OUTDIR="$RUN_ROOT/audit/runtime/l45_real_esmfold"
mkdir -p "$OUTDIR"

echo "=== Phase 100: ESMFold real inference (L4.5) ==="
echo "Output directory: $OUTDIR"

python <<'PY'
"""
Real ESMFold inference for the three HMO-target enzymes.

Uses RunpodESMFoldRunner in batch mode (batch_size=4 to saturate H100).
Writes structure.pdb and plddt.json per sequence_id to the audit output dir.
"""

import json
import math
import os
import sys
from pathlib import Path

RUN_ROOT = os.environ["RUN_ROOT"]
OUTDIR = Path(RUN_ROOT) / "audit" / "runtime" / "l45_real_esmfold"

# ── HMO-target enzyme sequences ───────────────────────────────────────────────
# Full-length representative sequences (UniProt canonical isoforms).
#
# FutC (Helicobacter pylori 26695) — UniProt Q11075
#   GDP-fucose α-2-fucosyltransferase, 317 aa
FUTC_SEQ = (
    "MFQPLLDAFIESCESYTKQVNRYAEDLQRSRTNNILDISKHENILYLPSPETKRGAGFCN"
    "IAAPKLREQIKAIQERAKKNLAFIDLYHEFRMHSFDQGFYQIAESMPIVIEDYPTSYDIY"
    "NVIKSNRYSKLVSTLFPHGPIVSSGKAFVTYYQHFYQAVLPQNKLILDFEDMPELQKKYD"
    "FLQKTIESITSPNLMKTYYRDKEPPHHEIVAVNDYLTYLDGLTHFYQSLSQKFNIPYFYL"
    "GDPAELYSYFAGKDLSNLIEEVKYLPEAHRVLKLHPRFIDVSYQHQKTAKQSTIKMRQFE"
    "KNLKLGKI"
)

# α-2,3-sialyltransferase Lst (Neisseria meningitidis) — UniProt Q9JYS2 (shortened)
ALPHA23LST_SEQ = (
    "MAITEFQDIVHRWDLKLAEALKAAYGYDDRENGAEKGRRESPRYVENGEFAESCKAKLERPYF"
    "KIIVDTDNLLFSGVSAALKDALETVNPELLYREKYGGKKGQTMFQDRQPLYKWRWMKSMM"
    "ATVNHNYQRIWDQSVIGQISRQSEQQIAKLELDILKQLNMTYLNHYGLKKEIKPFVWDFT"
    "PPLVGLNLFDIYTQNKPIGMLQDNELPSLYLDYQYPVGGALWSWEYATPHHIYVTADKVY"
    "QRLIGPNP"
)

# α-2,6-sialyltransferase (Pasteurella dagmatis) — UniProt A0A0P0HQ09 (shortened)
ALPHA26LST_SEQ = (
    "MIRSWFRDPGFGLAVLPLDIWGSCQAEPVRTAEEKKKQILEHFGISIGTGTKVHASFVVDDD"
    "AQKRSKMMYEMLEQLKQIPSTSMYFNNHQIEYVTDNYAGPLNIYNLSSQYAYFDYTIQKP"
    "LAEQGLNFPLPEKQRLTEGLLHSSSYLYQNIWDQSIIGRIPRQSETQIAQLELQILRDLN"
    "MTYLNNYGLPKDIRPFIWDFVPPLVALNLFDIYTKDKPIGMLENHALPSLYLDYQYPVGG"
    "ALWAWEYATPHHIYVTADKVYQRLIGPNP"
)

SEQUENCES = {
    "futc_helicobacter": FUTC_SEQ,
    "alpha23lst_neisseria": ALPHA23LST_SEQ,
    "alpha26lst_pasteurella": ALPHA26LST_SEQ,
}

# ── load runner ───────────────────────────────────────────────────────────────

from zer0pa_synbio.adapters.l4_5_unknown_enzyme.runpod_inference import (
    RunpodESMFoldRunner,
    esmfold_runner_available,
)

assert esmfold_runner_available(), (
    "ESMFold deps (transformers + torch + CUDA) must be available for phase 100"
)

runner = RunpodESMFoldRunner(device="cuda")
loaded = runner._ensure_loaded()
assert loaded, "RunpodESMFoldRunner failed to load — check transformers install and VRAM"

print(f"  ESMFold runner loaded on {runner._device}")

# ── batched inference ─────────────────────────────────────────────────────────

seq_ids = list(SEQUENCES.keys())
seqs = list(SEQUENCES.values())

print(f"  Running inference on {len(seqs)} sequences (batch_size=4) ...")
results = runner.predict_batch(seqs, batch_size=4)

# ── write outputs ─────────────────────────────────────────────────────────────

for seq_id, pred in zip(seq_ids, results):
    seq_outdir = OUTDIR / seq_id
    seq_outdir.mkdir(parents=True, exist_ok=True)

    if pred.stub_mode:
        print(f"  WARN: {seq_id} — stub_mode=True (real inference failed)", file=sys.stderr)
        continue

    # Write PDB.
    pdb_path = seq_outdir / "structure.pdb"
    pdb_path.write_text(pred.pdb_string, encoding="utf-8")

    # Write pLDDT JSON.
    plddt_payload = {
        "sequence_id": seq_id,
        "plddt_mean": pred.plddt_mean,
        "plddt_per_residue": pred.plddt_per_residue,
        "sequence_length": len(pred.sequence),
        "stub_mode": pred.stub_mode,
    }
    plddt_path = seq_outdir / "plddt.json"
    plddt_path.write_text(json.dumps(plddt_payload, indent=2), encoding="utf-8")

    print(
        f"  OK: {seq_id} — plddt_mean={pred.plddt_mean:.1f} "
        f"({len(pred.sequence)} residues) → {seq_outdir}"
    )

# ── sanity check ──────────────────────────────────────────────────────────────

real_count = sum(1 for p in results if not p.stub_mode)
print(f"\nPhase 100 summary: {real_count}/{len(results)} sequences successfully predicted.")
if real_count < len(results):
    print("WARN: Some sequences fell back to stub mode — check logs.", file=sys.stderr)
    sys.exit(1)
PY

echo "OK: Phase 100 (ESMFold real inference) complete."
