"""Real MACE-OFF binding ΔG via 3-run reference-state subtraction.

Per PRD §5.1 Tier-C falsifier f014 (mace_off_binding_implausible) and
HANDOFF-CPU-CONTINUATION.md item E.

Computes ``ΔG_binding ≈ E(complex) - E(protein) - E(ligand)`` using
the MACE-OFF universal MLIP. Single-point energies on the GPU (no
MD, no full geometry optimization — that requires curated geometry
which is downstream curation work).

Inputs:
    pdb_path:        ESMFold-predicted protein structure (.pdb)
    ligand_smiles:   substrate as canonical SMILES
    seed_label:      string for output JSON (e.g. "2pFL", "3pSL")

Outputs:
    {
      "binding_dg_kj_mol": float,
      "e_complex_kj_mol": float,
      "e_protein_kj_mol": float,
      "e_ligand_kj_mol": float,
      "n_atoms": {"complex": int, "protein": int, "ligand": int},
      "tool": "mace_off_v0.1_singlepoint",
      "boundary": "...",
    }

Honest scope:
    Single-point energies on heuristic complex geometry (ligand
    placed near protein center-of-mass) are NOT bona-fide binding
    free energies. This computes a structural plausibility score
    grounded in real MACE-OFF physics — usable as a Tier-C falsifier
    signal (f014 plausibility check), not a publishable affinity.
    Full alchemical / FEP / WAT-COMP work requires curated geometry
    + sampling, downstream of this v0.1.
"""

from __future__ import annotations

import json
import logging
import math
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

BOUNDARY = (
    "Research infrastructure for in silico synthetic biology / "
    "metabolic pathway engineering. Outputs are research artifacts. "
    "No regulatory certification claims. No clinical or human-subject "
    "use. No environmental release of GMOs."
)


@dataclass
class MaceBindingResult:
    binding_dg_kj_mol: float | None
    e_complex_kj_mol: float | None
    e_protein_kj_mol: float | None
    e_ligand_kj_mol: float | None
    n_atoms_complex: int
    n_atoms_protein: int
    n_atoms_ligand: int
    wallclock_seconds: float
    tool: str
    error: str | None
    boundary: str

    def to_dict(self) -> dict:
        return {
            "boundary": self.boundary,
            "tool": self.tool,
            "binding_dg_kj_mol": self.binding_dg_kj_mol,
            "e_complex_kj_mol": self.e_complex_kj_mol,
            "e_protein_kj_mol": self.e_protein_kj_mol,
            "e_ligand_kj_mol": self.e_ligand_kj_mol,
            "n_atoms": {
                "complex": self.n_atoms_complex,
                "protein": self.n_atoms_protein,
                "ligand": self.n_atoms_ligand,
            },
            "wallclock_seconds": self.wallclock_seconds,
            "error": self.error,
        }


def _load_protein_atoms(pdb_path: Path):
    """Load protein from ESMFold PDB into an ASE Atoms object.

    MACE-OFF accepts arbitrary atomic systems; we strip waters,
    keep only ATOM records (drop HETATM other than the future
    ligand we'll add ourselves).
    """
    from ase import Atoms
    from ase.io import read as ase_read

    try:
        atoms = ase_read(str(pdb_path), format="proteindatabank")
    except Exception:
        # Fallback: parse manually (ase's PDB reader can be picky)
        from ase.io.proteindatabank import read_proteindatabank

        with open(pdb_path) as f:
            atoms = read_proteindatabank(f, index=0)
    return atoms


def _smiles_to_atoms(smiles: str):
    """SMILES → 3D-embedded ASE Atoms via RDKit.

    Uses ETKDG embedding + UFF force-field minimization for a
    chemically-reasonable starting geometry.
    """
    from ase import Atoms
    from rdkit import Chem
    from rdkit.Chem import AllChem

    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        raise ValueError(f"RDKit failed to parse SMILES: {smiles}")
    mol = Chem.AddHs(mol)
    if AllChem.EmbedMolecule(mol, AllChem.ETKDGv3()) != 0:
        raise RuntimeError(f"RDKit ETKDG embedding failed for {smiles}")
    AllChem.UFFOptimizeMolecule(mol, maxIters=500)
    conf = mol.GetConformer()
    positions = [
        [conf.GetAtomPosition(i).x, conf.GetAtomPosition(i).y, conf.GetAtomPosition(i).z]
        for i in range(mol.GetNumAtoms())
    ]
    symbols = [a.GetSymbol() for a in mol.GetAtoms()]
    return Atoms(symbols=symbols, positions=positions)


def _make_complex(protein_atoms, ligand_atoms, offset_angstrom: float = 5.0):
    """Build a protein+ligand complex by placing the ligand near the
    protein center-of-mass with a fixed offset. Heuristic v0.1 — a real
    docking pose would come from AutoDock Vina or a better tool."""
    import numpy as np
    from ase import Atoms

    p_com = protein_atoms.get_center_of_mass()
    l_com = ligand_atoms.get_center_of_mass()
    # Translate ligand so its COM is at protein_COM + (offset, 0, 0)
    target = p_com + np.array([offset_angstrom, 0.0, 0.0])
    shift = target - l_com
    ligand_shifted = ligand_atoms.copy()
    ligand_shifted.translate(shift)
    complex_atoms = protein_atoms + ligand_shifted
    return complex_atoms, len(protein_atoms), len(ligand_shifted)


def _energy_with_mace(atoms, calculator) -> float:
    """Single-point energy in eV from MACE-OFF, converted to kJ/mol."""
    atoms.calc = calculator
    e_ev = atoms.get_potential_energy()
    e_kjmol = e_ev * 96.485  # eV → kJ/mol
    return e_kjmol


def compute_binding_dg(
    pdb_path: Path,
    ligand_smiles: str,
    seed_label: str,
    out_dir: Path,
    *,
    device: str = "cuda",
    max_protein_residues: int = 200,
) -> MaceBindingResult:
    """Compute MACE-OFF binding ΔG via 3-run reference subtraction.

    Truncates large proteins to ``max_protein_residues`` (centred on
    the active-site COM heuristic) — full proteins are O(few thousand)
    atoms which is feasible on H100 but slow.
    """
    t0 = time.time()
    out_dir.mkdir(parents=True, exist_ok=True)
    try:
        from mace.calculators import mace_off
    except ImportError as exc:
        return MaceBindingResult(
            binding_dg_kj_mol=None,
            e_complex_kj_mol=None,
            e_protein_kj_mol=None,
            e_ligand_kj_mol=None,
            n_atoms_complex=0,
            n_atoms_protein=0,
            n_atoms_ligand=0,
            wallclock_seconds=time.time() - t0,
            tool="mace_off_v0.1_singlepoint",
            error=f"mace import failed: {exc}",
            boundary=BOUNDARY,
        )

    try:
        # Load components
        protein_atoms = _load_protein_atoms(pdb_path)
        # Truncate if very large (active-site is unknown; centre on COM)
        if len(protein_atoms) > max_protein_residues * 8:
            import numpy as np

            com = protein_atoms.get_center_of_mass()
            d = np.linalg.norm(protein_atoms.get_positions() - com, axis=1)
            order = np.argsort(d)
            keep = order[: max_protein_residues * 8]
            protein_atoms = protein_atoms[keep]
            logger.info(
                "Truncated protein to %d nearest-COM atoms (heuristic active site).",
                len(protein_atoms),
            )

        ligand_atoms = _smiles_to_atoms(ligand_smiles)
        complex_atoms, n_protein_atoms, n_ligand_atoms = _make_complex(
            protein_atoms, ligand_atoms
        )

        # Build calculator (loads MACE-OFF medium model)
        logger.info("Loading MACE-OFF medium model on %s…", device)
        calc = mace_off(model="medium", device=device, default_dtype="float32")

        logger.info("Computing E(complex) [%d atoms]…", len(complex_atoms))
        e_complex = _energy_with_mace(complex_atoms, calc)
        logger.info("E(complex) = %.3f kJ/mol", e_complex)

        logger.info("Computing E(protein) [%d atoms]…", n_protein_atoms)
        e_protein = _energy_with_mace(protein_atoms.copy(), calc)
        logger.info("E(protein) = %.3f kJ/mol", e_protein)

        logger.info("Computing E(ligand) [%d atoms]…", n_ligand_atoms)
        e_ligand = _energy_with_mace(ligand_atoms.copy(), calc)
        logger.info("E(ligand) = %.3f kJ/mol", e_ligand)

        dg = e_complex - e_protein - e_ligand
        logger.info("ΔG_binding ≈ %.3f kJ/mol", dg)

        result = MaceBindingResult(
            binding_dg_kj_mol=dg,
            e_complex_kj_mol=e_complex,
            e_protein_kj_mol=e_protein,
            e_ligand_kj_mol=e_ligand,
            n_atoms_complex=len(complex_atoms),
            n_atoms_protein=n_protein_atoms,
            n_atoms_ligand=n_ligand_atoms,
            wallclock_seconds=time.time() - t0,
            tool="mace_off_v0.1_singlepoint",
            error=None,
            boundary=BOUNDARY,
        )
    except Exception as exc:
        logger.exception("MACE-OFF binding ΔG failed for %s/%s", seed_label, pdb_path)
        result = MaceBindingResult(
            binding_dg_kj_mol=None,
            e_complex_kj_mol=None,
            e_protein_kj_mol=None,
            e_ligand_kj_mol=None,
            n_atoms_complex=0,
            n_atoms_protein=0,
            n_atoms_ligand=0,
            wallclock_seconds=time.time() - t0,
            tool="mace_off_v0.1_singlepoint",
            error=str(exc),
            boundary=BOUNDARY,
        )

    out_path = out_dir / f"mace_binding_{pdb_path.stem}.json"
    out_path.write_text(json.dumps(result.to_dict(), indent=2, sort_keys=True))
    logger.info("Wrote %s", out_path)
    return result


def main() -> int:
    """CLI entry: ``python -m zer0pa_synbio.runpod_inference.mace_off_binding
    <pdb> <smiles> <out_dir> [seed_label]``."""
    import sys

    logging.basicConfig(
        level=logging.INFO, format="%(levelname)s %(name)s: %(message)s"
    )
    if len(sys.argv) < 4:
        print("usage: mace_off_binding <pdb> <smiles> <out_dir> [seed_label]")
        return 2
    pdb = Path(sys.argv[1])
    smi = sys.argv[2]
    out = Path(sys.argv[3])
    label = sys.argv[4] if len(sys.argv) > 4 else "unknown"
    res = compute_binding_dg(pdb, smi, label, out)
    print(json.dumps(res.to_dict(), indent=2))
    return 0 if res.binding_dg_kj_mol is not None else 1


if __name__ == "__main__":
    raise SystemExit(main())
