#!/usr/bin/env bash
# Phase 110 — Real MACE-OFF binding energy for HMO protein-ligand complexes (L4.5).
#
# Computes SE(3)-equivariant binding energies for three protein-ligand complexes
# relevant to HMO biosynthesis:
#   FutC + GDP-fucose      (key donor substrate for 2'-FL synthesis)
#   α-2,3-Lst + CMP-Neu5Ac (key donor substrate for 3'-SL synthesis)
#   α-2,6-Lst + CMP-Neu5Ac (key donor substrate for DSLNT synthesis)
#
# Input PDB files are read from the ESMFold phase outputs (phase 100):
#   $RUN_ROOT/audit/runtime/l45_real_esmfold/<sequence_id>/structure.pdb
#
# Outputs are written to:
#   $RUN_ROOT/audit/runtime/l45_real_mace_off/<complex_id>/binding_energy.json
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

ESMFOLD_DIR="$RUN_ROOT/audit/runtime/l45_real_esmfold"
OUTDIR="$RUN_ROOT/audit/runtime/l45_real_mace_off"
mkdir -p "$OUTDIR"

echo "=== Phase 110: MACE-OFF real binding energy (L4.5) ==="
echo "ESMFold input dir: $ESMFOLD_DIR"
echo "Output directory:  $OUTDIR"

python <<'PY'
"""
Real MACE-OFF (MACE-OFF23 medium) binding energy for HMO protein-ligand complexes.

Reads ESMFold PDB outputs from phase 100, builds ASE Atoms objects,
computes total energies with MACE-OFF (eV → kJ/mol), and writes JSON
audit artifacts per complex_id.

Note on total vs binding energy:
  MACE-OFF calculates the total potential energy of the complex.
  True binding energy (ΔE_bind) requires separate protein and ligand
  calculations: ΔE = E(complex) − E(protein) − E(ligand).
  Phase 110 writes the total energy; the audit verifier (phase 70) will
  compute ΔE from the individual components when they are available.
  For now, total energy is the primary output annotated as
  "energy_type": "total_kj_mol".
"""

import json
import math
import os
import sys
from pathlib import Path

RUN_ROOT = os.environ["RUN_ROOT"]
ESMFOLD_DIR = Path(RUN_ROOT) / "audit" / "runtime" / "l45_real_esmfold"
OUTDIR = Path(RUN_ROOT) / "audit" / "runtime" / "l45_real_mace_off"

# ── complex definitions ───────────────────────────────────────────────────────
# Each entry: (complex_id, esmfold_seq_id, ligand_smiles, ligand_name)
COMPLEXES = [
    (
        "futc_gdp_fucose",
        "futc_helicobacter",
        "OC[C@H]1O[C@@H](OP(=O)(O)OP(=O)(O)OC[C@H]2O[C@@H](n3cnc4c(N)ncnc43)"
        "[C@@H](O)[C@H]2O)[C@@H](O)[C@H](O)[C@@H]1O",  # GDP-fucose
        "GDP-fucose",
    ),
    (
        "alpha23lst_cmp_neu5ac",
        "alpha23lst_neisseria",
        "OC[C@H]1O[C@@](O)(C(=O)O)C[C@@H]1NC(C)=O",  # CMP-Neu5Ac (simplified)
        "CMP-Neu5Ac",
    ),
    (
        "alpha26lst_cmp_neu5ac",
        "alpha26lst_pasteurella",
        "OC[C@H]1O[C@@](O)(C(=O)O)C[C@@H]1NC(C)=O",  # CMP-Neu5Ac (simplified)
        "CMP-Neu5Ac",
    ),
]

# ── load runner ───────────────────────────────────────────────────────────────

from zer0pa_synbio.adapters.l4_5_unknown_enzyme.runpod_inference import (
    ProteinLigandComplex,
    RunpodMACEOFFRunner,
    mace_off_runner_available,
)

assert mace_off_runner_available(), (
    "MACE-OFF deps (mace-torch + ase + torch + CUDA) must be available for phase 110"
)

runner = RunpodMACEOFFRunner(model="medium", device="cuda", default_dtype="float64")
loaded = runner._ensure_loaded()
assert loaded, "RunpodMACEOFFRunner failed to load — check mace-torch install and VRAM"

print(f"  MACE-OFF runner loaded on {runner._device} (model={runner.model})")

# ── build complex inputs ──────────────────────────────────────────────────────

cpx_inputs: list[ProteinLigandComplex] = []
cpx_meta: list[tuple[str, str, str]] = []  # (complex_id, seq_id, ligand_name)

for complex_id, seq_id, ligand_smiles, ligand_name in COMPLEXES:
    pdb_path = ESMFOLD_DIR / seq_id / "structure.pdb"
    if not pdb_path.exists():
        print(
            f"  WARN: PDB not found for {seq_id} at {pdb_path} "
            f"— skipping complex {complex_id}",
            file=sys.stderr,
        )
        continue
    protein_pdb = pdb_path.read_text(encoding="utf-8")
    cpx_inputs.append(
        ProteinLigandComplex(
            protein_pdb=protein_pdb,
            ligand_smiles=ligand_smiles,
            complex_id=complex_id,
        )
    )
    cpx_meta.append((complex_id, seq_id, ligand_name))
    print(f"  Loaded PDB for {seq_id} ({len(protein_pdb)} bytes)")

if not cpx_inputs:
    print("ERROR: No valid complex inputs found — did phase 100 complete?", file=sys.stderr)
    sys.exit(1)

# ── batch inference ───────────────────────────────────────────────────────────

print(f"  Running MACE-OFF on {len(cpx_inputs)} complexes ...")
energies = runner.binding_energy_batch(cpx_inputs)

# ── write outputs ─────────────────────────────────────────────────────────────

success_count = 0
for (complex_id, seq_id, ligand_name), energy in zip(cpx_meta, energies):
    cpx_outdir = OUTDIR / complex_id
    cpx_outdir.mkdir(parents=True, exist_ok=True)

    is_stub = (energy == runner._STUB_ENERGY_KJ_MOL)
    if is_stub:
        print(
            f"  WARN: {complex_id} — stub sentinel returned ({energy} kJ/mol)",
            file=sys.stderr,
        )

    payload = {
        "complex_id": complex_id,
        "sequence_id": seq_id,
        "ligand_name": ligand_name,
        "energy_kj_mol": energy,
        "energy_type": "total_kj_mol",
        "ev_to_kj_mol_factor": runner._EV_TO_KJ_MOL,
        "model": runner.model,
        "default_dtype": runner.default_dtype,
        "device": runner._device,
        "is_finite": math.isfinite(energy),
        "stub_mode": is_stub,
    }
    out_path = cpx_outdir / "binding_energy.json"
    out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    if not is_stub and math.isfinite(energy):
        success_count += 1
        print(f"  OK: {complex_id} — energy={energy:.2f} kJ/mol → {out_path}")
    else:
        print(f"  WARN: {complex_id} — non-finite or stub energy: {energy}")

# ── sanity check ──────────────────────────────────────────────────────────────

total = len(cpx_inputs)
print(f"\nPhase 110 summary: {success_count}/{total} complexes with real finite energies.")
if success_count < total:
    print("WARN: Some complexes returned stub/non-finite energies — check logs.", file=sys.stderr)
    sys.exit(1)
PY

echo "OK: Phase 110 (MACE-OFF real binding energy) complete."
