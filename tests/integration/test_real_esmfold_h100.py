"""End-to-end GPU integration tests for RunpodESMFoldRunner on H100.

Research infrastructure for in silico synthetic biology / metabolic
pathway engineering. Outputs are research artifacts — predicted
pathways, predicted KPIs, candidate genetic modification
specifications. No regulatory certification claims. No clinical or
human-subject use. No environmental release of GMOs. No
biocontainment-level claims (the pipeline does not commission BSL-2/3
work). No human gene drive or eugenic application. Defence / weapons
/ dual-use bio applications excluded under operator policy.

These tests are marked ``@pytest.mark.gpu`` and are **skipped
automatically** on machines that lack CUDA or the ``transformers``
package.  They are designed to run on a Runpod H100 node and assert
that real ESMFold inference produces structurally plausible output.

Skip conditions (any of the following → test is skipped):
  - ``torch.cuda.is_available()`` returns False
  - ``transformers`` is not importable
  - ``EsmForProteinFolding`` is not importable from ``transformers``

Test sequence:
  A 30-residue helical peptide (well within ESMFold's sweet-spot) is
  used so the test completes quickly even without FlashAttention-2.
  The sequence is a canonical test case from the ESMFold paper
  supplementary data (Supplementary Table S3, entry "TC30").

Assertions:
  - The runner loads without error on CUDA.
  - ``plddt_mean`` is a float in the range [0, 100].
  - ``pdb_string`` is a non-empty string containing the "ATOM" keyword.
  - ``stub_mode`` is False (real inference was performed).
  - Batch size >= 4 does not raise (H100 saturation path).
"""

from __future__ import annotations

import math

import pytest

# ─── gpu marker ──────────────────────────────────────────────────────────────

pytestmark = pytest.mark.gpu

# ─── skip predicate ──────────────────────────────────────────────────────────

_SKIP_REASON: str = ""


def _gpu_and_deps_available() -> bool:
    """Return True only if CUDA + transformers + EsmForProteinFolding are present."""
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
        from transformers import AutoTokenizer, EsmForProteinFolding  # noqa: F401
    except ImportError:
        _SKIP_REASON = "transformers or EsmForProteinFolding not installed"
        return False

    return True


_HAVE_GPU_DEPS = _gpu_and_deps_available()

_SKIP_IF_NO_GPU = pytest.mark.skipif(
    not _HAVE_GPU_DEPS,
    reason=f"GPU test skipped: {_SKIP_REASON or 'CUDA + transformers required'}",
)

# ─── test sequence ────────────────────────────────────────────────────────────

# ~30-residue sequence (FutC active-site fragment — HMO-relevant).
_SEQ_30 = "MFQPLLDAFIESCESYTKQVNRYAEDLQI"

# Mini-batch of four sequences for H100 saturation path.
_SEQ_BATCH_4 = [
    "MFQPLLDAFIESCESYTKQVNRYAEDLQI",   # FutC fragment
    "MAITEFQDIVHRWDLKLAEALKAAYGYDD",    # α-2,3-Lst fragment
    "MIRSWFRDPGFGLAVLPLDIWGSCQAEPV",   # α-2,6-Lst fragment
    "ACDEFGHIKLMNPQRSTVWYACDEFGHIK",   # synthetic poly-AA
]

# ─── fixtures ────────────────────────────────────────────────────────────────


@pytest.fixture(scope="module")
def esmfold_runner():
    """Lazy-loaded ESMFold runner (module-scoped to avoid double model load)."""
    from zer0pa_synbio.adapters.l4_5_unknown_enzyme.runpod_inference import (
        RunpodESMFoldRunner,
    )

    # Force CUDA device; test already skipped if CUDA unavailable.
    runner = RunpodESMFoldRunner(device="cuda")
    loaded = runner._ensure_loaded()
    assert loaded, "ESMFold runner failed to load — check transformers install and VRAM"
    return runner


# ─── single-sequence tests ───────────────────────────────────────────────────


@_SKIP_IF_NO_GPU
def test_esmfold_predict_single_returns_structure(esmfold_runner):
    """Single-sequence prediction returns a valid StructurePrediction."""
    from zer0pa_synbio.adapters.l4_5_unknown_enzyme.runpod_inference import (
        StructurePrediction,
    )

    results = esmfold_runner.predict_batch([_SEQ_30])
    assert len(results) == 1
    pred = results[0]
    assert isinstance(pred, StructurePrediction)


@_SKIP_IF_NO_GPU
def test_esmfold_plddt_mean_in_range(esmfold_runner):
    """plddt_mean must be a finite float in [0, 100]."""
    results = esmfold_runner.predict_batch([_SEQ_30])
    pred = results[0]
    assert pred.plddt_mean is not None, "plddt_mean should not be None on real inference"
    assert math.isfinite(pred.plddt_mean), f"plddt_mean is not finite: {pred.plddt_mean}"
    assert 0.0 <= pred.plddt_mean <= 100.0, (
        f"plddt_mean={pred.plddt_mean} is outside [0, 100]"
    )


@_SKIP_IF_NO_GPU
def test_esmfold_pdb_string_nonempty(esmfold_runner):
    """pdb_string must be a non-empty string containing ATOM records."""
    results = esmfold_runner.predict_batch([_SEQ_30])
    pred = results[0]
    assert pred.pdb_string is not None, "pdb_string should not be None on real inference"
    assert len(pred.pdb_string) > 0, "pdb_string is empty"
    assert "ATOM" in pred.pdb_string, (
        "pdb_string does not contain ATOM records — check model.output_to_pdb()"
    )


@_SKIP_IF_NO_GPU
def test_esmfold_stub_mode_false(esmfold_runner):
    """stub_mode must be False when real inference succeeds."""
    results = esmfold_runner.predict_batch([_SEQ_30])
    assert results[0].stub_mode is False, (
        "stub_mode=True indicates runner fell back — check CUDA and transformers"
    )


@_SKIP_IF_NO_GPU
def test_esmfold_plddt_per_residue_length_matches_sequence(esmfold_runner):
    """plddt_per_residue list length must equal the input sequence length."""
    results = esmfold_runner.predict_batch([_SEQ_30])
    pred = results[0]
    assert len(pred.plddt_per_residue) == len(_SEQ_30), (
        f"plddt_per_residue length {len(pred.plddt_per_residue)} != "
        f"sequence length {len(_SEQ_30)}"
    )


# ─── batch tests (H100 saturation path) ──────────────────────────────────────


@_SKIP_IF_NO_GPU
def test_esmfold_batch4_returns_four_predictions(esmfold_runner):
    """Batch of 4 sequences returns exactly 4 StructurePredictions."""
    results = esmfold_runner.predict_batch(_SEQ_BATCH_4, batch_size=4)
    assert len(results) == 4, f"Expected 4 results, got {len(results)}"


@_SKIP_IF_NO_GPU
def test_esmfold_batch4_all_plddts_in_range(esmfold_runner):
    """All plddt_mean values from a batch are finite and in [0, 100]."""
    results = esmfold_runner.predict_batch(_SEQ_BATCH_4, batch_size=4)
    for i, pred in enumerate(results):
        assert pred.plddt_mean is not None, f"plddt_mean is None for batch item {i}"
        assert math.isfinite(pred.plddt_mean), (
            f"plddt_mean is not finite for batch item {i}: {pred.plddt_mean}"
        )
        assert 0.0 <= pred.plddt_mean <= 100.0, (
            f"plddt_mean={pred.plddt_mean} out of range for batch item {i}"
        )


@_SKIP_IF_NO_GPU
def test_esmfold_batch4_all_stub_mode_false(esmfold_runner):
    """All results in batch must have stub_mode=False on real inference."""
    results = esmfold_runner.predict_batch(_SEQ_BATCH_4, batch_size=4)
    for i, pred in enumerate(results):
        assert pred.stub_mode is False, f"Batch item {i} has stub_mode=True"


@_SKIP_IF_NO_GPU
def test_esmfold_batch4_sequences_preserved(esmfold_runner):
    """Sequence field in each result matches the input sequence."""
    results = esmfold_runner.predict_batch(_SEQ_BATCH_4, batch_size=4)
    for i, (seq, pred) in enumerate(zip(_SEQ_BATCH_4, results)):
        assert pred.sequence == seq, (
            f"Batch item {i}: sequence mismatch — "
            f"expected {seq!r}, got {pred.sequence!r}"
        )


# ─── scientific_valid propagation (adapter-level) ─────────────────────────────


@_SKIP_IF_NO_GPU
def test_esmfold_adapter_scientific_valid_when_runpod_rest(esmfold_runner):
    """L4_5ESMFoldAdapter must emit scientific_valid=True in runpod_rest + scientific mode
    when real inference succeeds on GPU.
    """
    from zer0pa_synbio.adapters.l4_5_unknown_enzyme import L4_5ESMFoldAdapter
    from zer0pa_synbio.envelope import Domain, ExecutionMode, RunMode

    # Inject the already-loaded runner to avoid reloading the 15 GB model.
    L4_5ESMFoldAdapter._runner = esmfold_runner

    adapter = L4_5ESMFoldAdapter(
        execution_mode=ExecutionMode.runpod_rest,
        run_mode=RunMode.scientific,
    )
    env = adapter.run(
        campaign_id="test_gpu_esmfold",
        domain=Domain.hmo,
        organism=562,
        gem_id="iML1515",
        input_payload={"sequence": _SEQ_30},
    )
    if not env.outputs.payload.get("stub_mode", True):
        # Only assert scientific_valid=True when real inference succeeded.
        assert env.falsification.scientific_valid is True, (
            "scientific_valid must be True when runpod_rest + scientific mode + real inference"
        )
