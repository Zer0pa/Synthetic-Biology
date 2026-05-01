#!/usr/bin/env bash
# Phase 200 — CEKM data-pipeline + model-construction smoke.
set -euo pipefail
. "$RUN_ROOT/env.sh"

python <<'PY'
"""1. Data pipeline runs end-to-end (CPU).
2. Model factory builds CEKM on CUDA via TrainingConfig defaults.
3. One forward pass with the same shape train.py uses.
"""
import torch
from zer0pa_synbio.cekm import smoke_test_pipeline
from zer0pa_synbio.cekm.train import TrainingConfig, build_model

print("=== data pipeline smoke ===")
result = smoke_test_pipeline()
print(f"  corpus_size={result['corpus_size']} held_out_size={result['held_out_size']}")
print(f"  adversarial: α={result['tier_alpha_count']} β={result['tier_beta_count']} γ={result['tier_gamma_count']}")

print("=== build model (CUDA, fp32 for smoke; train.py uses bf16) ===")
cfg = TrainingConfig(campaign_id="cekm_smoke_h100", seed=42, use_bf16=False)
model = build_model(cfg)
assert model is not None, "build_model returned None — torch missing?"
model = model.cuda()
total = sum(p.numel() for p in model.parameters())
trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
print(f"  param count: {total/1e6:.1f} M ({trainable/1e6:.1f} M trainable)")
print(f"  esm2_real={model._using_real_esm2}  substrate_mode={model.substrate_encoder.input_mode}")

print("=== forward pass on dummy batch (training-loop shape) ===")
from transformers import AutoTokenizer
tok = AutoTokenizer.from_pretrained("facebook/esm2_t33_650M_UR50D")
seq = "MFKVAIIGAGAVGNALLLDLLEKHKVELQGI"
batch = tok([seq] * 4, return_tensors="pt", padding=True).to("cuda")
substrate_input = torch.tensor([0, 1, 2, 3], dtype=torch.long, device="cuda")
conditions = torch.tensor([[7.0, 37.0]] * 4, dtype=torch.float32, device="cuda")
with torch.no_grad():
    out = model(
        sequence_ids=batch["input_ids"],
        substrate_input=substrate_input,
        conditions=conditions,
    )
expected = {"kcat_log", "km_log", "disc_alpha", "disc_beta", "disc_gamma", "fused"}
assert expected.issubset(out.keys()), f"missing keys: {expected - set(out.keys())}"
for k, v in out.items():
    if torch.is_tensor(v):
        assert not torch.isnan(v).any(), f"NaN in {k}"
        print(f"    {k}: shape={tuple(v.shape)} dtype={v.dtype}")
print("OK: CEKM model builds + forward-passes on H100; all 6 output keys present.")
PY
echo "OK: CEKM smoke passed."
