#!/usr/bin/env bash
# Phase 200 — CEKM data-pipeline + model-construction smoke (no training).
# Confirms the model builds on H100 before committing to phase 210.
set -euo pipefail
. "$RUN_ROOT/env.sh"

python <<'PY'
"""Smoke test:
1. Data pipeline runs end-to-end (CPU).
2. Model factory builds CEKM on CUDA in bf16.
3. One forward pass on the same input shape that train.py uses
   (substrate as a LongTensor (B,) hash, not fingerprint).
"""
import torch
from zer0pa_synbio.cekm import smoke_test_pipeline
from zer0pa_synbio.cekm.train import (
    TrainingConfig, ESM2Config, DMPNNConfig, ConditionMLPConfig,
    AdaptiveGateConfig, HeadsConfig, LossConfig, build_model,
)

# 1. Data-pipeline smoke (CPU; no model).
print("=== data pipeline smoke ===")
result = smoke_test_pipeline()
print(f"  corpus_size={result['corpus_size']} in_corpus_size={result['in_corpus_size']}")
print(f"  held_out_size={result['held_out_size']}")
print(f"  adversarial_negative_count={result['adversarial_negative_count']}")
print(f"  tier_alpha={result['tier_alpha_count']} beta={result['tier_beta_count']} gamma={result['tier_gamma_count']}")

# 2. Model build on CUDA.
print("=== model build (bf16, CUDA) ===")
cfg = TrainingConfig(
    campaign_id="cekm_smoke_h100",
    esm2=ESM2Config(unfreeze_last_n_layers=0, use_real_esm2=True, dtype="bfloat16"),
    dmpnn=DMPNNConfig(hidden_dim=128, num_layers=3),
    condition_mlp=ConditionMLPConfig(hidden_dim=64),
    adaptive_gate=AdaptiveGateConfig(gate_type="cross_attention"),
    heads=HeadsConfig(num_disc_classes=4),
    loss=LossConfig(supervised_weight=1.0, curriculum_weight=0.3, contrastive_weight=0.5),
    batch_size=4,
    learning_rate=1e-4,
    max_steps=10,
    eval_every_steps=10,
    checkpoint_every_steps=10,
    seed=42,
)
model = build_model(cfg)
model = model.cuda()
total = sum(p.numel() for p in model.parameters())
trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
print(f"  param count: {total/1e6:.1f} M ({trainable/1e6:.1f} M trainable)")

# 3. Forward pass — same shape as the training loop uses (substrate as hash).
print("=== forward pass on dummy batch (training-loop shape) ===")
from transformers import AutoTokenizer
tok = AutoTokenizer.from_pretrained("facebook/esm2_t33_650M_UR50D")
seq = "MFKVAIIGAGAVGNALLLDLLEKHKVELQGI"  # FutC fragment (30 residues)
batch = tok([seq] * 4, return_tensors="pt", padding=True).to("cuda")
substrate_input = torch.tensor([0, 1, 2, 3], dtype=torch.long, device="cuda")
conditions = torch.tensor([[7.0, 37.0, 0.15]] * 4, dtype=torch.float32, device="cuda")

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
