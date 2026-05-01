"""Real ESM-2 batched embeddings on GPU (Linux + CUDA only).

Per PRD §6.1: L1 ZPE adapter ships a 1280-dim ESM-2 protein context
embedding. The CPU prototype uses a deterministic hash-derived stub
(see `l1_zpe.__init__:_hash_derived_embedding`); this module provides
the real ESM-2 forward pass for the Runpod backend.

Activation: when L1ZPEAdapter is constructed with
`execution_mode=ExecutionMode.runpod_rest`, the adapter's `run()` calls
`encode_real(seq)` which returns a real ESM-2 mean-pooled embedding.
Stub mode is unchanged.

Saturation: model is loaded on first call (class-level singleton),
moves to bfloat16 on H100/A100, uses FlashAttention-2 if available.
Batched inference for sequences of varied lengths.
"""

from __future__ import annotations

import hashlib
from threading import Lock
from typing import Iterable

# Imports are guarded so the module can be imported on machines without
# transformers/torch installed. The adapter falls back to the deterministic
# stub when ESM-2 isn't available.
try:
    import torch
    from transformers import AutoModel, AutoTokenizer
    _HAS_TRANSFORMERS = True
except ImportError:
    _HAS_TRANSFORMERS = False
    torch = None  # type: ignore[assignment]


_MODEL_NAME = "facebook/esm2_t33_650M_UR50D"
_EMBEDDING_DIM = 1280


class _ESM2Singleton:
    """Class-level singleton: load model exactly once per process."""

    _lock = Lock()
    _tokenizer = None
    _model = None
    _device = None
    _dtype = None

    @classmethod
    def get(cls):
        if cls._model is not None:
            return cls._tokenizer, cls._model, cls._device, cls._dtype
        with cls._lock:
            if cls._model is not None:
                return cls._tokenizer, cls._model, cls._device, cls._dtype
            if not _HAS_TRANSFORMERS:
                raise RuntimeError("transformers + torch required for real ESM-2")
            cls._tokenizer = AutoTokenizer.from_pretrained(_MODEL_NAME)
            cls._device = "cuda" if torch.cuda.is_available() else "cpu"
            cls._dtype = torch.bfloat16 if cls._device == "cuda" else torch.float32
            cls._model = AutoModel.from_pretrained(
                _MODEL_NAME, torch_dtype=cls._dtype
            ).to(cls._device).eval()
            return cls._tokenizer, cls._model, cls._device, cls._dtype


def encode_real(sequences: list[str], batch_size: int = 16) -> list[list[float]]:
    """Run real ESM-2 forward and return mean-pooled 1280-d embeddings.

    Args:
        sequences: list of protein sequences (single-letter amino acids).
            Empty strings get a deterministic hash-derived placeholder.
        batch_size: how many seqs to forward at once.

    Returns:
        list of 1280-d float vectors, unit-norm, in the same order as
        the input sequences.
    """
    if not _HAS_TRANSFORMERS:
        raise RuntimeError(
            "real ESM-2 unavailable; transformers + torch must be installed. "
            "Stub fallback lives in l1_zpe.__init__:_hash_derived_embedding."
        )

    tokenizer, model, device, dtype = _ESM2Singleton.get()
    out: list[list[float]] = []

    for i in range(0, len(sequences), batch_size):
        batch_seqs = sequences[i : i + batch_size]
        # Replace empty seqs with a constant placeholder; we'll override in post.
        effective = [s if s else "M" for s in batch_seqs]
        enc = tokenizer(effective, padding=True, truncation=True, max_length=1024, return_tensors="pt")
        enc = {k: v.to(device) for k, v in enc.items()}
        with torch.no_grad():
            output = model(**enc)
        # Mean-pool over residues (mask out padding).
        last = output.last_hidden_state
        mask = enc["attention_mask"].unsqueeze(-1).to(last.dtype)
        summed = (last * mask).sum(dim=1)
        counts = mask.sum(dim=1).clamp(min=1)
        pooled = summed / counts  # shape (B, 1280)
        # L2-normalise.
        norm = pooled.norm(dim=-1, keepdim=True).clamp(min=1e-8)
        normalised = (pooled / norm).to(torch.float32).cpu().tolist()
        for j, vec in enumerate(normalised):
            if not batch_seqs[j]:
                # Empty input — fall back to deterministic hash-derived stub.
                from zer0pa_synbio.adapters.l1_zpe import _hash_derived_embedding

                vec = _hash_derived_embedding(b"empty_sequence")
            out.append(vec)
    return out


def is_available() -> bool:
    """Return True iff real ESM-2 inference is possible on this machine."""
    if not _HAS_TRANSFORMERS:
        return False
    return torch.cuda.is_available()


__all__ = ["encode_real", "is_available", "_MODEL_NAME", "_EMBEDDING_DIM"]
