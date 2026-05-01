#!/usr/bin/env bash
# Phase 200 — CEKM data-pipeline + model-construction smoke (no training).
# Confirms the model builds on H100 and a single forward pass succeeds
# before committing to a multi-hour training run (Murphy's law).
set -euo pipefail
. "$RUN_ROOT/env.sh"

python <<'PY'
import torch
from zer0pa_synbio.cekm.train import (
    TrainingConfig, ESM2Config, DMPNNConfig, ConditionMLPConfig,
    AdaptiveGateConfig, HeadsConfig, LossConfig, build_model,
)
from zer0pa_synbio.cekm import smoke_test_pipeline

# 1. Data-pipeline smoke (CPU; no model).
print("=== data pipeline smoke ===")
result = smoke_test_pipeline()
print(f"  positives: {result['positives']} negatives: {result['negatives']}")

# 2. Model build + single forward pass on H100.
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
    max_steps=10,  # tiny — just to confirm forward+backward works
    eval_every_steps=10,
    checkpoint_every_steps=10,
    seed=42,
)
model = build_model(cfg)
model = model.cuda()
print(f"  param count: {sum(p.numel() for p in model.parameters())/1e6:.1f} M")
print(f"  trainable param count: {sum(p.numel() for p in model.parameters() if p.requires_grad)/1e6:.1f} M")

# 3. Tiny forward pass.
print("=== forward pass on dummy batch ===")
seq = "MFKVAIIGAGAVGNALLLDLLEKHKVELQGI"  # FutC fragment, 30 residues
from transformers import AutoTokenizer
tok = AutoTokenizer.from_pretrained("facebook/esm2_t33_650M_UR50D")
batch = tok([seq] * 4, return_tensors="pt", padding=True).to("cuda")

# Substrate fingerprint — random 64-d vector for smoke test.
substrate_fp = torch.randn(4, 128, device="cuda", dtype=torch.bfloat16)
condition = torch.randn(4, 3, device="cuda", dtype=torch.bfloat16)  # pH, T, ionic

with torch.no_grad():
    out = model(
        sequence_ids=batch["input_ids"],
        substrate_input=substrate_fp,
        conditions=condition,
    )
print(f"  forward keys: {list(out.keys())}")
expected_keys = {"kcat_log", "km_log", "disc_alpha", "disc_beta", "disc_gamma", "fused"}
assert expected_keys.issubset(out.keys()), f"missing keys: {expected_keys - set(out.keys())}"
for k, v in out.items():
    if torch.is_tensor(v):
        print(f"    {k}: shape={tuple(v.shape)} dtype={v.dtype}")
        assert not torch.isnan(v).any(), f"NaN in {k}"
print("OK: CEKM model builds and forward-passes on H100; all 6 output keys present.")
PY
echo "OK: CEKM smoke passed."
