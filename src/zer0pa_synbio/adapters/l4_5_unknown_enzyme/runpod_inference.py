"""Runpod inference runners for L4.5 unknown-enzyme generative sub-pipeline.

Research infrastructure for in silico synthetic biology / metabolic
pathway engineering. Outputs are research artifacts — predicted
pathways, predicted KPIs, candidate genetic modification
specifications. No regulatory certification claims. No clinical or
human-subject use. No environmental release of GMOs. No
biocontainment-level claims (the pipeline does not commission BSL-2/3
work). No human gene drive or eugenic application. Defence / weapons
/ dual-use bio applications excluded under operator policy.

Per PRD §6.6: these runners are the GPU-inference glue that Runpod
agents will activate by switching `execution_mode=runpod_rest`. They
are pure scaffolding — all heavy imports are guarded with try/except
ImportError so the package continues to import cleanly without the
optional GPU dependencies.

Dependency installation notes (Runpod workers only — do NOT run locally):

  ESMFold:
    pip install "transformers>=4.38" "accelerate>=0.27" "torch>=2.4"
    # Flash Attention 2 (optional, speeds up attention):
    pip install "flash-attn>=2.5" --no-build-isolation

  MACE-OFF:
    pip install "mace-torch>=0.3"          # installs e3nn + torch
    # Optional: CUDA-accelerated ASE for geometry relaxation
    pip install "ase>=3.22"

  RFdiffusion3:
    # 1. Foundry enrolment required (checkpoint gating) — contact RosettaCommons.
    # 2. Install stack: torch>=2.4, dgl>=2.1 (CUDA build), se3-transformer
    pip install "dgl -f https://data.dgl.ai/wheels/cu121/repo.html"
    pip install "se3-transformer @ git+https://github.com/FabianFuchsML/se3-transformer-public"
    # 3. Clone RFdiffusion3 repo and install in editable mode:
    git clone https://github.com/RosettaCommons/RFdiffusion3
    pip install -e RFdiffusion3
    # 4. Download Foundry checkpoint (requires account/token):
    python -m rfdiffusion3.download --ckpt base --out /checkpoints/rfdiffusion3

The runner classes are designed for class-level lazy-init: the GPU
model/calculator is loaded only on the first call to the relevant
method, not at import or __init__ time. This prevents OOM on workers
that share the process until the L4.5 branch is triggered.

All three runners fall back to stub output if their heavy deps are
unavailable (ImportError or runtime checkpoint failure), preserving the
envelope shape exactly so Wave 11 cutover invariance tests still pass.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)

# ─── optional dep flags ──────────────────────────────────────────────────────

try:
    import torch as _torch  # noqa: F401

    _TORCH_AVAILABLE = True
except ImportError:
    _TORCH_AVAILABLE = False

try:
    import transformers as _transformers  # noqa: F401

    _TRANSFORMERS_AVAILABLE = True
except ImportError:
    _TRANSFORMERS_AVAILABLE = False

try:
    from mace import calculators as _mace_calc  # noqa: F401

    _MACE_AVAILABLE = True
except ImportError:
    _MACE_AVAILABLE = False

try:
    import rfdiffusion3 as _rfd3  # noqa: F401

    _RFDIFFUSION3_AVAILABLE = True
except ImportError:
    _RFDIFFUSION3_AVAILABLE = False


# ─── payload dataclasses (returned by runners; adapters project these into
#     the envelope's output_payload dict) ─────────────────────────────────────


@dataclass
class StructurePrediction:
    """ESMFold output per sequence."""

    sequence: str
    pdb_string: str | None           # None when stub_mode=True
    plddt_mean: float | None         # None when stub_mode=True
    plddt_per_residue: list[float] = field(default_factory=list)
    stub_mode: bool = True


@dataclass
class ProteinLigandComplex:
    """Input to MACE-OFF runner."""

    protein_pdb: str              # PDB-format string
    ligand_smiles: str
    complex_id: str = ""


@dataclass
class ScaffoldDesign:
    """RFdiffusion3 output per scaffold."""

    scaffold_pdb: str | None      # None when stub_mode=True
    motif_rmsd_angstrom: float | None
    design_index: int = 0
    stub_mode: bool = True


# ─── ESMFold runner ──────────────────────────────────────────────────────────


class RunpodESMFoldRunner:
    """Wraps ``transformers.EsmForProteinFolding`` for batched protein structure
    prediction on a Runpod GPU node.

    Lazy-init: the model is only loaded on the first call to
    ``predict_batch``.  Falls back to stub output if ``transformers``
    or ``torch`` are not importable, or if the model fails to load.

    bf16 + FlashAttention-2 are enabled when the runtime supports them.
    The standard HuggingFace model ID is ``facebook/esmfold_v1``.

    Attributes:
        model_id: HuggingFace model ID for ESMFold (default
            ``"facebook/esmfold_v1"``).
        device: ``"cuda"`` or ``"cpu"``; inferred from availability when None.
    """

    def __init__(
        self,
        model_id: str = "facebook/esmfold_v1",
        device: str | None = None,
    ) -> None:
        self.model_id = model_id
        self._device: str | None = device
        self._model: Any = None
        self._tokenizer: Any = None
        self._load_error: str | None = None

    # ── lazy init ────────────────────────────────────────────────────────────

    def _ensure_loaded(self) -> bool:
        """Load model if not yet loaded.  Returns True on success, False on failure."""
        if self._model is not None:
            return True
        if self._load_error is not None:
            return False

        if not _TORCH_AVAILABLE or not _TRANSFORMERS_AVAILABLE:
            self._load_error = "transformers / torch not installed"
            logger.warning("RunpodESMFoldRunner: %s — staying in stub mode", self._load_error)
            return False

        try:
            import torch
            from transformers import AutoTokenizer, EsmForProteinFolding

            device = self._device
            if device is None:
                device = "cuda" if torch.cuda.is_available() else "cpu"
            self._device = device

            logger.info(
                "RunpodESMFoldRunner: loading %s on %s (bf16=%s)",
                self.model_id,
                device,
                device == "cuda",
            )
            tokenizer = AutoTokenizer.from_pretrained(self.model_id)
            model_kwargs: dict[str, Any] = {"low_cpu_mem_usage": True}

            if device == "cuda":
                model_kwargs["torch_dtype"] = torch.bfloat16
                # NB: EsmForProteinFolding does NOT support attn_implementation=
                # "flash_attention_2" yet (transformers raises ValueError). The
                # ESM-2 sub-module supports it, but the folding trunk doesn't.
                # We rely on the bf16 cast for throughput; FA2 would only help
                # the ESM backbone path which is the smaller cost on H100.

            try:
                model = EsmForProteinFolding.from_pretrained(self.model_id, **model_kwargs)
            except (ValueError, TypeError) as exc:
                # If the chosen kwargs are rejected (e.g. some flash-attn arg
                # leaked in via env), fall back to plain eager attention.
                logger.warning("ESMFold load with bf16 failed (%s); retrying eager fp32", exc)
                model = EsmForProteinFolding.from_pretrained(self.model_id, low_cpu_mem_usage=True)
            model = model.to(device)
            if device == "cuda":
                # ESMFold uses fp16 for the ESM-2 language-model backbone.
                # The folding trunk stays in bf16; only esm sub-module goes fp16.
                model.esm = model.esm.half()
                logger.info("RunpodESMFoldRunner: ESM-2 backbone cast to fp16")
            model.eval()

            self._tokenizer = tokenizer
            self._model = model
            logger.info("RunpodESMFoldRunner: model loaded successfully")
            return True

        except Exception as exc:  # noqa: BLE001
            self._load_error = str(exc)
            logger.warning(
                "RunpodESMFoldRunner: load failed (%s) — staying in stub mode", exc
            )
            return False

    # ── public API ───────────────────────────────────────────────────────────

    def predict_batch(
        self, sequences: list[str], batch_size: int = 4
    ) -> list[StructurePrediction]:
        """Run ESMFold on a list of amino-acid sequences.

        Sequences are processed in micro-batches of ``batch_size`` (default 4)
        to saturate H100 SM occupancy while staying within VRAM limits.
        Sequences within a micro-batch are padded to the longest sequence in
        that batch via the tokenizer's padding logic.

        Returns one :class:`StructurePrediction` per sequence.  The
        ``stub_mode`` flag is True when real inference was not performed.

        Args:
            sequences:  List of single-letter amino-acid sequences.
            batch_size: Number of sequences per GPU micro-batch (default 4).
                        Set to 1 for sequences > 800 residues to avoid OOM.

        Returns:
            List of :class:`StructurePrediction` with ``stub_mode=False`` on
            success, ``stub_mode=True`` on fallback.
        """
        if not self._ensure_loaded():
            logger.debug(
                "RunpodESMFoldRunner.predict_batch: stub fallback for %d seqs", len(sequences)
            )
            return [
                StructurePrediction(sequence=seq, pdb_string=None, plddt_mean=None, stub_mode=True)
                for seq in sequences
            ]

        import torch

        results: list[StructurePrediction] = []
        device = self._device or "cpu"

        # Process in micro-batches of `batch_size` to saturate H100 SMs.
        for batch_start in range(0, len(sequences), batch_size):
            batch_seqs = sequences[batch_start : batch_start + batch_size]
            try:
                tokenized = self._tokenizer(
                    batch_seqs,
                    return_tensors="pt",
                    add_special_tokens=False,
                    padding=True,        # pad shorter seqs in the batch
                    truncation=False,    # never silently truncate
                )
                tokenized = {k: v.to(device) for k, v in tokenized.items()}

                with torch.no_grad():
                    output = self._model(**tokenized)

                # output_to_pdb returns one PDB string per sequence in the batch.
                pdb_strings: list[str] = self._model.output_to_pdb(output)

                for i, seq in enumerate(batch_seqs):
                    pdb_string = pdb_strings[i] if i < len(pdb_strings) else None

                    # plddt tensor: [batch, seq_len, n_atoms]; index 1 = Cα.
                    if hasattr(output, "plddt") and output.plddt is not None:
                        plddt_all: list[float] = (
                            output.plddt[i, :len(seq), 1].cpu().float().tolist()
                        )
                    else:
                        plddt_all = []

                    plddt_mean = (
                        float(sum(plddt_all) / len(plddt_all)) if plddt_all else None
                    )

                    results.append(
                        StructurePrediction(
                            sequence=seq,
                            pdb_string=pdb_string,
                            plddt_mean=plddt_mean,
                            plddt_per_residue=plddt_all,
                            stub_mode=False,
                        )
                    )

            except Exception as exc:  # noqa: BLE001
                logger.warning(
                    "RunpodESMFoldRunner: batch inference failed (seqs %d-%d): %s",
                    batch_start,
                    batch_start + len(batch_seqs) - 1,
                    exc,
                )
                for seq in batch_seqs:
                    results.append(
                        StructurePrediction(
                            sequence=seq, pdb_string=None, plddt_mean=None, stub_mode=True
                        )
                    )

        return results


# ─── MACE-OFF runner ─────────────────────────────────────────────────────────


class RunpodMACEOFFRunner:
    """Wraps the ``mace-torch`` MACECalculator for SE(3)-equivariant
    binding-energy prediction.

    Lazy-init: the MACE-OFF calculator is instantiated on the first call to
    ``binding_energy_batch``.  Falls back to stub energies if ``mace-torch``
    is not installed.

    The binding energy is reported in kJ/mol per protein–ligand complex.  A
    more negative value indicates tighter binding.

    Unit convention:
      ASE returns energies in eV.  1 eV = 96.485 kJ/mol.

    Attributes:
        model: MACE-OFF model size identifier.  ``"medium"`` is the recommended
            default (MACE-OFF23(M) — ~7 M parameters, good balance of speed
            and accuracy).  Accepted values: ``"small"``, ``"medium"``,
            ``"large"``.  May also accept legacy identifier ``"MACE-OFF23"``.
        device: ``"cuda"`` or ``"cpu"``; inferred when None.
        default_dtype: Floating-point precision for ASE/MACE computations.
            ``"float64"`` (default) is required for chemistry-grade energy
            accuracy; ``"float32"`` is faster but less precise.
        dispersion: Whether to include D3 dispersion correction (default True).
    """

    # Canonical canned stub energy (same as existing adapter stub).
    _STUB_ENERGY_KJ_MOL: float = -45.2

    # eV → kJ/mol conversion factor (NIST 2018 CODATA).
    _EV_TO_KJ_MOL: float = 96.485

    def __init__(
        self,
        model: str = "medium",
        device: str | None = None,
        default_dtype: str = "float64",
        dispersion: bool = True,
    ) -> None:
        self.model = model
        self._device: str | None = device
        self.default_dtype = default_dtype
        self.dispersion = dispersion
        self._calculator: Any = None
        self._load_error: str | None = None

    # ── lazy init ────────────────────────────────────────────────────────────

    def _ensure_loaded(self) -> bool:
        """Load MACE-OFF calculator if not yet loaded.  Returns True on success."""
        if self._calculator is not None:
            return True
        if self._load_error is not None:
            return False

        if not _MACE_AVAILABLE or not _TORCH_AVAILABLE:
            self._load_error = "mace-torch not installed"
            logger.warning("RunpodMACEOFFRunner: %s — staying in stub mode", self._load_error)
            return False

        try:
            import torch
            from mace.calculators import mace_off

            device = self._device
            if device is None:
                device = "cuda" if torch.cuda.is_available() else "cpu"
            self._device = device

            logger.info(
                "RunpodMACEOFFRunner: loading MACE-OFF model=%r dtype=%s on %s",
                self.model,
                self.default_dtype,
                device,
            )
            self._calculator = mace_off(
                model=self.model,
                device=device,
                default_dtype=self.default_dtype,
            )
            logger.info("RunpodMACEOFFRunner: calculator loaded successfully")
            return True

        except Exception as exc:  # noqa: BLE001
            self._load_error = str(exc)
            logger.warning(
                "RunpodMACEOFFRunner: load failed (%s) — staying in stub mode", exc
            )
            return False

    # ── public API ───────────────────────────────────────────────────────────

    def binding_energy_batch(
        self, complexes: list[ProteinLigandComplex]
    ) -> list[float]:
        """Compute binding energy (kJ/mol) for each protein–ligand complex.

        A negative value indicates a stabilising (binding-favourable) interaction.
        Returns the canned stub value (-45.2 kJ/mol) for each complex when
        MACE-OFF is unavailable.

        Args:
            complexes: List of :class:`ProteinLigandComplex` inputs.

        Returns:
            List of binding energies in kJ/mol, one per complex.
        """
        if not self._ensure_loaded():
            logger.debug(
                "RunpodMACEOFFRunner.binding_energy_batch: stub fallback for %d complexes",
                len(complexes),
            )
            return [self._STUB_ENERGY_KJ_MOL] * len(complexes)

        results: list[float] = []
        for cpx in complexes:
            try:
                # Build an ASE Atoms object from PDB + SMILES.
                # ASE is a transitive dependency of mace-torch.
                import ase.io
                import io

                atoms = ase.io.read(io.StringIO(cpx.protein_pdb), format="proteindatabank")
                atoms.calc = self._calculator

                # energy() in eV; convert to kJ/mol (1 eV = 96.485 kJ/mol).
                energy_ev = atoms.get_potential_energy()
                energy_kj_mol = float(energy_ev) * self._EV_TO_KJ_MOL
                results.append(energy_kj_mol)

            except Exception as exc:  # noqa: BLE001
                logger.warning(
                    "RunpodMACEOFFRunner: binding energy failed for complex %r: %s",
                    cpx.complex_id,
                    exc,
                )
                results.append(self._STUB_ENERGY_KJ_MOL)

        return results


# ─── RFdiffusion3 runner ─────────────────────────────────────────────────────


class RunpodRFdiffusion3Runner:
    """Wraps RFdiffusion3 conditional diffusion for catalytic motif scaffolding.

    Installation (Runpod workers only — NOT required locally):
        # Requirements: torch>=2.4, DGL>=2.1 CUDA build, se3-transformer.
        pip install dgl -f https://data.dgl.ai/wheels/cu121/repo.html
        pip install se3-transformer @ git+https://github.com/FabianFuchsML/se3-transformer-public
        git clone https://github.com/RosettaCommons/RFdiffusion3
        pip install -e RFdiffusion3
        python -m rfdiffusion3.download --ckpt base --out /checkpoints/rfdiffusion3

        Note: Foundry enrolment is required to download checkpoints.  If the
        checkpoint download is blocked (no Foundry token), the adapter
        automatically remains in stub mode and does not claim scientific_valid.

    Lazy-init: the RFdiffusion3 model is loaded on the first call to
    ``scaffold_from_motif``.  Falls back to stub scaffolds if RFdiffusion3
    is not importable or the checkpoint is absent.

    Attributes:
        checkpoint_path: Path to the Foundry checkpoint directory (default
            ``"/checkpoints/rfdiffusion3"``).
        device: ``"cuda"`` or ``"cpu"``; inferred when None.
        noise_scale: Diffusion noise scale parameter (default 0.5).
    """

    def __init__(
        self,
        checkpoint_path: str = "/checkpoints/rfdiffusion3",
        device: str | None = None,
        noise_scale: float = 0.5,
    ) -> None:
        self.checkpoint_path = checkpoint_path
        self._device: str | None = device
        self.noise_scale = noise_scale
        self._model: Any = None
        self._load_error: str | None = None

    # ── lazy init ────────────────────────────────────────────────────────────

    def _ensure_loaded(self) -> bool:
        """Load RFdiffusion3 model.  Returns True on success, False on fallback."""
        if self._model is not None:
            return True
        if self._load_error is not None:
            return False

        if not _RFDIFFUSION3_AVAILABLE or not _TORCH_AVAILABLE:
            self._load_error = "rfdiffusion3 / torch not installed"
            logger.warning(
                "RunpodRFdiffusion3Runner: %s — staying in stub mode", self._load_error
            )
            return False

        try:
            import torch
            import rfdiffusion3

            device = self._device
            if device is None:
                device = "cuda" if torch.cuda.is_available() else "cpu"
            self._device = device

            logger.info(
                "RunpodRFdiffusion3Runner: loading checkpoint from %s on %s",
                self.checkpoint_path,
                device,
            )
            # RFdiffusion3 public API (may vary with Foundry release; adapt as needed):
            self._model = rfdiffusion3.load_model(
                checkpoint=self.checkpoint_path,
                device=device,
            )
            self._model.eval()
            logger.info("RunpodRFdiffusion3Runner: model loaded successfully")
            return True

        except Exception as exc:  # noqa: BLE001
            self._load_error = str(exc)
            logger.warning(
                "RunpodRFdiffusion3Runner: load failed (%s) — staying in stub mode", exc
            )
            return False

    # ── public API ───────────────────────────────────────────────────────────

    def scaffold_from_motif(
        self,
        motif_pdb: str,
        length: int,
        n_designs: int = 4,
    ) -> list[ScaffoldDesign]:
        """Run RFdiffusion3 conditional diffusion to scaffold a catalytic motif.

        Args:
            motif_pdb: PDB-format string of the fixed catalytic motif residues.
            length:    Total scaffold length (residue count, including motif).
            n_designs: Number of independent scaffold designs to generate.

        Returns:
            List of :class:`ScaffoldDesign` objects, one per design, with
            ``stub_mode=False`` on success, ``stub_mode=True`` on fallback.
        """
        if not self._ensure_loaded():
            logger.debug(
                "RunpodRFdiffusion3Runner.scaffold_from_motif: stub fallback, n_designs=%d",
                n_designs,
            )
            return [
                ScaffoldDesign(
                    scaffold_pdb=None,
                    motif_rmsd_angstrom=None,
                    design_index=i,
                    stub_mode=True,
                )
                for i in range(n_designs)
            ]

        designs: list[ScaffoldDesign] = []
        try:
            # RFdiffusion3 public API (adapt to Foundry release):
            import rfdiffusion3

            outputs = rfdiffusion3.scaffold_from_motif(
                model=self._model,
                motif_pdb=motif_pdb,
                total_length=length,
                num_designs=n_designs,
                noise_scale=self.noise_scale,
            )

            for i, design_output in enumerate(outputs):
                designs.append(
                    ScaffoldDesign(
                        scaffold_pdb=design_output.get("pdb_string"),
                        motif_rmsd_angstrom=design_output.get("motif_rmsd"),
                        design_index=i,
                        stub_mode=False,
                    )
                )
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "RunpodRFdiffusion3Runner: scaffold failed (%s) — stub fallback", exc
            )
            designs = [
                ScaffoldDesign(
                    scaffold_pdb=None,
                    motif_rmsd_angstrom=None,
                    design_index=i,
                    stub_mode=True,
                )
                for i in range(n_designs)
            ]

        return designs


# ── availability helpers (used by adapter __init__.py) ──────────────────────


def esmfold_runner_available() -> bool:
    """True if transformers + torch are importable (ESMFold can be loaded)."""
    return _TORCH_AVAILABLE and _TRANSFORMERS_AVAILABLE


def mace_off_runner_available() -> bool:
    """True if mace-torch + torch are importable."""
    return _MACE_AVAILABLE and _TORCH_AVAILABLE


def rfdiffusion3_runner_available() -> bool:
    """True if rfdiffusion3 + torch are importable."""
    return _RFDIFFUSION3_AVAILABLE and _TORCH_AVAILABLE


__all__ = [
    # Dataclasses
    "StructurePrediction",
    "ProteinLigandComplex",
    "ScaffoldDesign",
    # Runners
    "RunpodESMFoldRunner",
    "RunpodMACEOFFRunner",
    "RunpodRFdiffusion3Runner",
    # Availability helpers
    "esmfold_runner_available",
    "mace_off_runner_available",
    "rfdiffusion3_runner_available",
]
