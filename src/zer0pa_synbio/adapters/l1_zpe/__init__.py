"""L1 ZPE adapter — input encoding.

Per PRD §6.1:
- **Input:** `{target_compound: SELFIES + InChI_key, host_organism: ncbi_taxonomy_id + refseq_genome_accession + gem_id}`
- **Output:** `{zpe_word_envelope: 20-bit deterministic per-token, esm2_embedding: float[1280], gem_handle: string}`
- **Tools:** `selfies` (Apache 2.0), `RDKit` (BSD), `ESM-2` weights (MIT).
- **Falsifiers:** f001 (invalid SELFIES), f018 (license drift).

The ZPE word envelope is a deterministic 20-bit-per-token fingerprint of
the SELFIES string: `top20bits(sha256(token + context))`. This is the
Zer0pa-specific input encoding described in PRD §6.1; it is reproducible
under any backend (stub / local_cpu / runpod_rest) so the
`httpx.MockTransport` invariance test passes.

The ESM-2 embedding is a 1280-dimensional float vector. In `local_cpu`
mode (no torch installed), this falls back to a deterministic
hash-derived feature vector with `scientific_valid=False` enforced. In
`gpu_rest_stub` mode, the same canned vector is returned. In future
`runpod_rest` mode, the real ESM-2 inference runs; the envelope schema is
identical except for `provenance.created_at` and `provenance.git_sha`.
"""

from __future__ import annotations

import hashlib
import struct
import uuid
from typing import Any

from zer0pa_synbio.adapters import LayerAdapter
from zer0pa_synbio.envelope import (
    Domain,
    ExecutionMode,
    FalsifierFailure,
    Falsification,
    GateStatus,
    Layer,
    LicenseClass,
    RunMode,
    Reference,
    UniversalLayerEnvelope,
)
from zer0pa_synbio.falsifiers.checks import run as run_falsifier


_ZPE_VERSION = "zpe.v0.1"
_EMBEDDING_DIM = 1280  # ESM-2 dimensionality


def _zpe_word(token: str, context: bytes) -> int:
    """20-bit deterministic fingerprint per SELFIES token + context."""
    h = hashlib.sha256(context + token.encode("utf-8")).digest()
    # Top 20 bits.
    return (struct.unpack(">I", h[:4])[0]) >> 12


def _zpe_envelope(selfies_str: str) -> list[int]:
    """Tokenise SELFIES and emit one 20-bit word per token."""
    try:
        import selfies as sf  # type: ignore[import-not-found]

        tokens = list(sf.split_selfies(selfies_str))
    except Exception:
        # Fallback tokenisation: split on `]` to isolate brackets — reproducible
        # but not chemistry-aware.
        tokens = [tok + "]" for tok in selfies_str.split("]") if tok]
    context = hashlib.sha256(selfies_str.encode("utf-8")).digest()
    return [_zpe_word(tok, context) for tok in tokens]


def _hash_derived_embedding(seed: bytes, dim: int = _EMBEDDING_DIM) -> list[float]:
    """Reproducible deterministic 1280-d float vector derived from a seed.

    Used in stub mode (no real ESM-2 inference). The vector is unit-norm
    (L2) so that downstream code that expects a normalised embedding
    behaves consistently between stub and real backends.
    """
    out: list[float] = []
    counter = 0
    while len(out) < dim:
        h = hashlib.sha512(seed + counter.to_bytes(4, "big")).digest()
        for i in range(0, len(h), 4):
            if len(out) >= dim:
                break
            val = struct.unpack(">i", h[i : i + 4])[0]
            # Normalise to roughly [-1, 1].
            out.append(val / 2_147_483_648.0)
        counter += 1
    # L2-normalise.
    norm = sum(x * x for x in out) ** 0.5
    if norm > 0:
        out = [x / norm for x in out]
    return out


class L1ZPEAdapter(LayerAdapter):
    layer = Layer.L1
    adapter_name = "L1ZPEAdapter"
    tool_name = "selfies+rdkit+esm2"
    tool_version = "selfies==2.2.0+rdkit==2025.9.3+esm2==v0.1-stub"
    license_class = LicenseClass.A
    license_evidence_uri = "audit/source_manifests/selfies.yaml"

    def run(
        self,
        *,
        campaign_id: str,
        domain: Domain,
        organism: int,
        gem_id: str,
        input_payload: dict[str, Any],
        run_id: uuid.UUID | None = None,
    ) -> UniversalLayerEnvelope:
        """Execute L1 encoding.

        `input_payload` must carry:
            target_compound: {selfies: str, inchi_key: str}
            host_organism: {taxonomy_id: int, refseq_genome_accession: str, gem_id: str}
        """
        target = input_payload.get("target_compound", {})
        selfies_str = target.get("selfies", "")
        inchi_key = target.get("inchi_key", "")

        # Pre-flight falsifier f001.
        f001 = run_falsifier("f001_invalid_selfies", {"selfies": selfies_str})
        failures: list[FalsifierFailure] = []
        if f001.triggered:
            failures.append(
                FalsifierFailure(
                    gate_id="f001_invalid_selfies",
                    severity=f001.severity,
                    message=f001.message,
                    evidence_uri="",
                )
            )
            gate_status = GateStatus.fail
        else:
            gate_status = GateStatus.pass_

        # Build outputs (zpe_word_envelope + esm2_embedding + gem_handle).
        zpe_words = _zpe_envelope(selfies_str) if not f001.triggered else []
        host = input_payload.get("host_organism", {})
        gem_handle = host.get("gem_id", gem_id)
        seed = (selfies_str + "|" + inchi_key + "|" + gem_handle).encode("utf-8")

        # Real ESM-2 batched embedding when on Runpod backend with a
        # protein sequence supplied; fall back to deterministic hash-derived
        # stub otherwise. The cutover invariance test (Wave 11) is preserved
        # because: in stub-mode without protein_sequence, the output is
        # identical to before; in runpod-mode WITH protein_sequence, the
        # output_payload structure stays the same, only the embedding
        # values differ — which is captured under provenance.method.
        protein_seq = input_payload.get("protein_sequence", "")
        used_real_esm2 = False
        if self.execution_mode == ExecutionMode.runpod_rest and protein_seq:
            try:
                from zer0pa_synbio.adapters.l1_zpe.esm2_real import (
                    encode_real,
                    is_available,
                )
                if is_available():
                    esm2_embedding = encode_real([protein_seq])[0]
                    used_real_esm2 = True
                else:
                    esm2_embedding = _hash_derived_embedding(seed)
            except Exception:
                esm2_embedding = _hash_derived_embedding(seed)
        else:
            esm2_embedding = _hash_derived_embedding(seed)

        output_payload = {
            "zpe_version": _ZPE_VERSION,
            "zpe_word_envelope": zpe_words,
            "esm2_embedding": esm2_embedding,
            "gem_handle": gem_handle,
            "embedding_provenance": {
                "method": "esm2_runpod" if used_real_esm2 else "hash_derived_stub",
                "scientific_valid": used_real_esm2,
                "dim": _EMBEDDING_DIM,
            },
        }

        # Falsification block.
        falsification = Falsification(
            gate_status=gate_status,
            scientific_valid=False,  # CPU/stub embedding — never SV
            failures=failures,
            boundary_check_passed=True,
        )

        return self._make_envelope(
            campaign_id=campaign_id,
            domain=domain,
            organism=organism,
            gem_id=gem_id,
            input_payload=input_payload,
            output_payload=output_payload,
            falsification=falsification,
            run_id=run_id,
            scientific_valid_override=False,
        )


__all__ = ["L1ZPEAdapter", "_zpe_envelope", "_hash_derived_embedding"]
