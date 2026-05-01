#!/usr/bin/env bash
# Phase 50 — Real ESM-2 batched embedding sanity check (L1).
set -euo pipefail
. "$RUN_ROOT/env.sh"

python <<'PY'
"""Smoke test the real ESM-2 path before HMO seed runs depend on it."""
from zer0pa_synbio.adapters.l1_zpe.esm2_real import encode_real, is_available, _MODEL_NAME, _EMBEDDING_DIM

assert is_available(), "ESM-2 + CUDA must be available for L1 real-embedding phase"
print(f"Model: {_MODEL_NAME}; expected dim: {_EMBEDDING_DIM}")

# Three sequences relevant to the HMO triple — FutC (2'-FL), α-2,3-Lst (3'-SL), α-2,6-Lst (DSLNT).
fragments = [
    "MFQPLLDAFIESCESYTKQVNRYAEDLQRSRTNNILDISKHENILYLPSPETKRGAGFCN",
    "MAITEFQDIVHRWDLKLAEALKAAYGYDDRENGAEKGRRESPRYVENGEFAESCKAKLERPYF",
    "MIRSWFRDPGFGLAVLPLDIWGSCQAEPVRTAEEKKKQILEHFGISIGTGTKVHASFVVDDD",
]
embeddings = encode_real(fragments, batch_size=8)
print(f"  embeddings shape: ({len(embeddings)}, {len(embeddings[0])})")
print(f"  unit-norm check: {[round(sum(x*x for x in e)**0.5, 4) for e in embeddings]}")
print(f"  not all zero: {[any(abs(x)>1e-3 for x in e) for e in embeddings]}")
PY
echo "OK: real ESM-2 batched inference works on H100."
