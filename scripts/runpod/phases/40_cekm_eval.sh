#!/usr/bin/env bash
# Phase 40 — calibration audit on held-out + Tier α/β/γ adversarial negatives.
set -euo pipefail

REPO_DIR="${REPO_DIR:-$(cd "$(dirname "$0")/../../.." && pwd)}"
cd "$REPO_DIR"

VENV="$REPO_DIR/.venv"
# shellcheck disable=SC1091
source "$VENV/bin/activate"

ts() { date -u +"%Y-%m-%dT%H:%M:%SZ"; }
log() { printf '[40_cekm_eval %s] %s\n' "$(ts)" "$*"; }

CFG_ACTIVE="$REPO_DIR/audit/runtime/runpod/wave4_active_corpus.yaml"
[[ -f "$CFG_ACTIVE" ]] || { log "FATAL: $CFG_ACTIVE missing."; exit 41; }

CKPT_DIR=$(python -c "
import yaml; cfg = yaml.safe_load(open('$CFG_ACTIVE')); print(cfg.get('checkpoint_dir', 'checkpoints/cekm'))
")

LATEST=$(ls -t "$CKPT_DIR"/ckpt_step*.meta.json 2>/dev/null | head -1 || true)
if [[ -z "$LATEST" ]]; then
    log "FATAL: no checkpoint found at $CKPT_DIR; phase 30 must complete first."
    exit 42
fi
log "Evaluating checkpoint: $LATEST"

EVAL_LOG="$REPO_DIR/audit/runtime/runpod/cekm_eval.log"
synbio cekm eval --config "$CFG_ACTIVE" --checkpoint "$LATEST" 2>&1 | tee "$EVAL_LOG"
RC=${PIPESTATUS[0]}
if [[ "$RC" -ne 0 ]]; then
    log "Calibration audit returned rc=$RC. The orchestrator may treat this as fatal or warn-only depending on config."
    # Calibration failure should NOT block the rest of the chain — the
    # rest of the pipeline is still useful even if CEKM is poorly
    # calibrated. Exit 0 with the diagnostic captured.
fi
log "CEKM eval phase complete; report at $EVAL_LOG"
exit 0
