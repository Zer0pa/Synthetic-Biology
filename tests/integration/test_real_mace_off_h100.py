"""End-to-end GPU integration tests for RunpodMACEOFFRunner on H100.

Research infrastructure for in silico synthetic biology / metabolic
pathway engineering. Outputs are research artifacts — predicted
pathways, predicted KPIs, candidate genetic modification
specifications. No regulatory certification claims. No clinical or
human-subject use. No environmental release of GMOs. No
biocontainment-level claims (the pipeline does not commission BSL-2/3
work). No human gene drive or eugenic application. Defence / weapons
/ dual-use bio applications excluded under operator policy.

These tests are marked ``@pytest.mark.gpu`` and are **skipped
automatically** on machines that lack CUDA or the ``mace`` and ``ase``
packages.  They are designed to run on a Runpod H100 node.

Skip conditions (any of the following → test is skipped):
  - ``torch.cuda.is_available()`` returns False
  - ``mace`` is not importable
  - ``ase`` is not importable

Test structure:
  Minimal ASE ``Atoms`` objects (water molecule and small peptide PDB
  fragments) are used as inputs.  The tests assert that the calculator
  returns finite binding energies in kJ/mol without raising.

Unit conventions:
  ASE returns energies in eV.  The runner converts using:
    1 eV = 96.485 kJ/mol  (NIST 2018 CODATA)
  A finite (not NaN/Inf) result is required; sign depends on the
  structure.
"""

from __future__ import annotations

import math

import pytest

# ─── gpu marker ──────────────────────────────────────────────────────────────

pytestmark = pytest.mark.gpu

# ─── skip predicate ──────────────────────────────────────────────────────────

_SKIP_REASON: str = ""


def _gpu_and_deps_available() -> bool:
    """Return True only if CUDA + mace + ase are available."""
    global _SKIP_REASON

    try:
        import torch  # noqa: F401
    except ImportError:
        _SKIP_REASON = "torch not installed"
        return False

    import torch

    if not torch.cuda.is_available():
        _SKIP_REASON = "CUDA not available"
        return False

    try:
        from mace.calculators import mace_off  # noqa: F401
    except ImportError:
        _SKIP_REASON = "mace-torch not installed"
        return False

    try:
        import ase  # noqa: F401
    except ImportError:
        _SKIP_REASON = "ase not installed"
        return False

    return True


_HAVE_GPU_DEPS = _gpu_and_deps_available()

_SKIP_IF_NO_GPU = pytest.mark.skipif(
    not _HAVE_GPU_DEPS,
    reason=f"GPU test skipped: {_SKIP_REASON or 'CUDA + mace + ase required'}",
)

# ─── minimal test PDB strings ─────────────────────────────────────────────────
# Water molecule — simplest valid proteindatabank input for ASE.
# Used to verify calculator loads and returns a finite energy.

_WATER_PDB = """\
REMARK  Minimal water PDB for MACE-OFF test
HETATM    1  O   HOH A   1       0.000   0.000   0.000  1.00  0.00           O
HETATM    2  H   HOH A   1       0.757   0.586   0.000  1.00  0.00           H
HETATM    3  H   HOH A   1      -0.757   0.586   0.000  1.00  0.00           H
END
"""

# Short alanine dipeptide PDB — more realistic protein-like input.
_ALA_DIP_PDB = """\
REMARK  Alanine dipeptide (Ala-Ala) for MACE-OFF test
ATOM      1  N   ALA A   1       1.458   0.000   0.000  1.00  0.00           N
ATOM      2  CA  ALA A   1       2.912   0.000   0.000  1.00  0.00           C
ATOM      3  C   ALA A   1       3.453   1.420   0.000  1.00  0.00           C
ATOM      4  O   ALA A   1       2.634   2.340   0.000  1.00  0.00           O
ATOM      5  CB  ALA A   1       3.447  -0.770  -1.206  1.00  0.00           C
ATOM      6  N   ALA A   2       4.780   1.579   0.000  1.00  0.00           N
ATOM      7  CA  ALA A   2       5.427   2.892   0.000  1.00  0.00           C
ATOM      8  C   ALA A   2       6.945   2.779   0.000  1.00  0.00           C
ATOM      9  O   ALA A   2       7.543   1.690   0.000  1.00  0.00           O
ATOM     10  CB  ALA A   2       4.992   3.700   1.218  1.00  0.00           C
END
"""

# ─── fixture ──────────────────────────────────────────────────────────────────


@pytest.fixture(scope="module")
def mace_runner():
    """Module-scoped MACE-OFF runner loaded on CUDA."""
    from zer0pa_synbio.adapters.l4_5_unknown_enzyme.runpod_inference import (
        RunpodMACEOFFRunner,
    )

    runner = RunpodMACEOFFRunner(model="medium", device="cuda", default_dtype="float64")
    loaded = runner._ensure_loaded()
    assert loaded, (
        "MACE-OFF runner failed to load — check mace-torch install and VRAM"
    )
    return runner


# ─── single-complex tests ─────────────────────────────────────────────────────


@_SKIP_IF_NO_GPU
def test_mace_off_water_energy_is_finite(mace_runner):
    """Water molecule must return a finite binding energy in kJ/mol."""
    from zer0pa_synbio.adapters.l4_5_unknown_enzyme.runpod_inference import (
        ProteinLigandComplex,
    )

    complexes = [
        ProteinLigandComplex(
            protein_pdb=_WATER_PDB,
            ligand_smiles="O",
            complex_id="water_test",
        )
    ]
    energies = mace_runner.binding_energy_batch(complexes)
    assert len(energies) == 1
    assert isinstance(energies[0], float)
    assert math.isfinite(energies[0]), f"Water energy is not finite: {energies[0]}"


@_SKIP_IF_NO_GPU
def test_mace_off_ala_dip_energy_is_finite(mace_runner):
    """Alanine dipeptide PDB returns a finite energy in kJ/mol."""
    from zer0pa_synbio.adapters.l4_5_unknown_enzyme.runpod_inference import (
        ProteinLigandComplex,
    )

    complexes = [
        ProteinLigandComplex(
            protein_pdb=_ALA_DIP_PDB,
            ligand_smiles="CC(N)C(=O)NC(C)C(=O)O",  # Ala-Ala SMILES
            complex_id="ala_dip_test",
        )
    ]
    energies = mace_runner.binding_energy_batch(complexes)
    assert len(energies) == 1
    assert isinstance(energies[0], float)
    assert math.isfinite(energies[0]), f"Ala-dip energy is not finite: {energies[0]}"


@_SKIP_IF_NO_GPU
def test_mace_off_energy_not_stub_sentinel(mace_runner):
    """Real inference must not return the stub sentinel value -45.2 kJ/mol exactly."""
    from zer0pa_synbio.adapters.l4_5_unknown_enzyme.runpod_inference import (
        ProteinLigandComplex,
    )

    complexes = [
        ProteinLigandComplex(
            protein_pdb=_WATER_PDB,
            ligand_smiles="O",
            complex_id="stub_check",
        )
    ]
    energies = mace_runner.binding_energy_batch(complexes)
    # Stub sentinel is exactly -45.2; real water energy will differ.
    assert energies[0] != -45.2, (
        "Energy equals stub sentinel -45.2 — runner may have fallen back to stub mode"
    )


# ─── batch tests ──────────────────────────────────────────────────────────────


@_SKIP_IF_NO_GPU
def test_mace_off_batch_returns_correct_count(mace_runner):
    """Batch of complexes returns the same number of energy values."""
    from zer0pa_synbio.adapters.l4_5_unknown_enzyme.runpod_inference import (
        ProteinLigandComplex,
    )

    complexes = [
        ProteinLigandComplex(
            protein_pdb=_WATER_PDB, ligand_smiles="O", complex_id=f"c{i}"
        )
        for i in range(4)
    ]
    energies = mace_runner.binding_energy_batch(complexes)
    assert len(energies) == 4, f"Expected 4 energies, got {len(energies)}"


@_SKIP_IF_NO_GPU
def test_mace_off_batch_all_finite(mace_runner):
    """All energies in a batch must be finite floats."""
    from zer0pa_synbio.adapters.l4_5_unknown_enzyme.runpod_inference import (
        ProteinLigandComplex,
    )

    complexes = [
        ProteinLigandComplex(
            protein_pdb=pdb,
            ligand_smiles=smiles,
            complex_id=f"batch_{i}",
        )
        for i, (pdb, smiles) in enumerate(
            [
                (_WATER_PDB, "O"),
                (_WATER_PDB, "O"),
                (_ALA_DIP_PDB, "CC(N)C(=O)NC(C)C(=O)O"),
                (_ALA_DIP_PDB, "CC(N)C(=O)NC(C)C(=O)O"),
            ]
        )
    ]
    energies = mace_runner.binding_energy_batch(complexes)
    assert len(energies) == 4
    for i, e in enumerate(energies):
        assert isinstance(e, float), f"Energy {i} is not a float: {type(e)}"
        assert math.isfinite(e), f"Energy {i} is not finite: {e}"


# ─── eV → kJ/mol conversion sanity ───────────────────────────────────────────


@_SKIP_IF_NO_GPU
def test_mace_off_ev_to_kj_mol_conversion_factor(mace_runner):
    """Verify the class-level conversion constant matches NIST 2018 CODATA."""
    from zer0pa_synbio.adapters.l4_5_unknown_enzyme.runpod_inference import (
        RunpodMACEOFFRunner,
    )

    # NIST 2018 CODATA: 1 eV = 96.48530749925793 kJ/mol (rounded to 96.485).
    assert abs(RunpodMACEOFFRunner._EV_TO_KJ_MOL - 96.485) < 1e-3, (
        f"Unexpected conversion factor: {RunpodMACEOFFRunner._EV_TO_KJ_MOL}"
    )


# ─── scientific_valid propagation (adapter-level) ─────────────────────────────


@_SKIP_IF_NO_GPU
def test_mace_off_adapter_scientific_valid_when_runpod_rest(mace_runner):
    """L4_5MACEOFFAdapter must emit scientific_valid=True in runpod_rest + scientific mode
    when real inference succeeds on GPU.
    """
    from zer0pa_synbio.adapters.l4_5_unknown_enzyme import L4_5MACEOFFAdapter
    from zer0pa_synbio.envelope import Domain, ExecutionMode, RunMode

    # Inject the already-loaded runner to avoid reloading.
    L4_5MACEOFFAdapter._runner = mace_runner

    adapter = L4_5MACEOFFAdapter(
        execution_mode=ExecutionMode.runpod_rest,
        run_mode=RunMode.scientific,
    )
    env = adapter.run(
        campaign_id="test_gpu_mace",
        domain=Domain.hmo,
        organism=562,
        gem_id="iML1515",
        input_payload={
            "protein_pdb": _WATER_PDB,
            "ligand_smiles": "O",
            "complex_id": "water_adapter_test",
        },
    )
    if not env.outputs.payload.get("stub_mode", True):
        assert env.falsification.scientific_valid is True, (
            "scientific_valid must be True when runpod_rest + scientific mode + real inference"
        )
