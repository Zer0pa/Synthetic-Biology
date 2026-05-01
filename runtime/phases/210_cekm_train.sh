#!/usr/bin/env bash
# Phase 210 — CEKM mini training run (H100 saturation).
#
# Trains for max_steps=2000 against an in-memory synthetic corpus seeded
# from BRENDA-style positives + adversarial three-tier negatives. Real
# corpus assembly + full training (≥50K steps) is gated behind a
# `runtime/cekm.config.yaml` for a future operator-driven run; this
# phase is the saturation+plumbing test.
set -euo pipefail
. "$RUN_ROOT/env.sh"

CONFIG="$RUN_ROOT/repo/runtime/cekm-train-h100.yaml"
mkdir -p "$RUN_ROOT/repo/audit/runtime/cekm_train_h100" \
         "$RUN_ROOT/repo/audit/runtime/cekm_train_h100/checkpoints"

# Generate a config on the fly — campaign-scoped under audit/runtime/.
cat > "$CONFIG" <<EOF
campaign_id: cekm_train_h100
esm2:
  pretrained_name: facebook/esm2_t33_650M_UR50D
  use_real_esm2: true
  unfreeze_last_n_layers: 2
  dtype: bfloat16
dmpnn:
  hidden_dim: 128
  num_layers: 3
condition_mlp:
  hidden_dim: 64
adaptive_gate:
  gate_type: cross_attention
heads:
  num_disc_classes: 4
loss:
  supervised_weight: 1.0
  curriculum_weight: 0.3
  contrastive_weight: 0.5
batch_size: 8
gradient_accumulation_steps: 4
learning_rate: 1.0e-4
warmup_steps: 100
max_steps: 2000
eval_every_steps: 200
checkpoint_every_steps: 500
checkpoint_dir: $RUN_ROOT/repo/audit/runtime/cekm_train_h100/checkpoints
seed: 42
hf_repo: Architect-Prime/synbio-cekm-v0.1
push_to_hf: false   # smoke; full push gated on real-corpus run
EOF

cat "$CONFIG"

cd "$RUN_ROOT/repo"
python -m zer0pa_synbio.cli cekm train --config "$CONFIG" 2>&1 | tail -40
echo "OK: CEKM training phase finished."
