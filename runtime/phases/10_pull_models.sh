#!/usr/bin/env bash
# Phase 10 — HF model pulls
set -euo pipefail
. "$RUN_ROOT/env.sh"

echo "==== HF auth ===="
if [ -f ~/.cache/huggingface/token ] || [ -f "$HF_HOME/token" ]; then
  python -c "from huggingface_hub import whoami; me = whoami(); print(f'authenticated as {me[\"name\"]}')"
elif [ -n "${HF_TOKEN:-}" ]; then
  echo "$HF_TOKEN" > "$HF_HOME/token"
  python -c "from huggingface_hub import whoami; me = whoami(); print(f'authenticated as {me[\"name\"]}')"
else
  echo "NO HF TOKEN — anonymous pulls only (still works for public models)"
fi

echo "==== Pull ESM-2-650M (load-bearing for L1) ===="
python -c "
from transformers import AutoTokenizer, AutoModel
import torch
print('Downloading facebook/esm2_t33_650M_UR50D ...')
tok = AutoTokenizer.from_pretrained('facebook/esm2_t33_650M_UR50D')
model = AutoModel.from_pretrained('facebook/esm2_t33_650M_UR50D', torch_dtype=torch.bfloat16)
print(f'  param count: {sum(p.numel() for p in model.parameters())/1e6:.1f} M')
model = model.to('cuda').eval()
# Smoke test: encode lactose-related FutC fragment.
seq = 'MFKVAIIGAGAVGNALLLDLLEKHKVELQGI'  # truncated FutC start
batch = tok(seq, return_tensors='pt').to('cuda')
with torch.no_grad():
    out = model(**batch)
emb = out.last_hidden_state.mean(dim=1)
print(f'  ESM-2 forward OK: shape={emb.shape} dtype={emb.dtype}')
"

echo "OK: model pulls done."
