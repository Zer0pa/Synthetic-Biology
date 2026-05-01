#!/usr/bin/env bash
# Phase 30 — CEKM real-corpus training. Load-bearing 6–8h block.
#
# Resume-safe: invokes `synbio cekm train --resume` so a mid-phase pod
# restart picks up at the latest checkpoint. On NaN-loss / divergence:
# the underlying train.py is responsible for rolling back; this phase
# script wraps the call and surfaces failures via exit code.
#
# OOM strategy: starts at the configured batch_size; on CUDA OOM, the
# next attempt drops batch_size to half (and grad_accum doubles to
# preserve effective batch).

set -euo pipefail

REPO_DIR="${REPO_DIR:-$(cd "$(dirname "$0")/../../.." && pwd)}"
cd "$REPO_DIR"

VENV="$REPO_DIR/.venv"
# shellcheck disable=SC1091
source "$VENV/bin/activate"

ts() { date -u +"%Y-%m-%dT%H:%M:%SZ"; }
log() { printf '[30_cekm_train %s] %s\n' "$(ts)" "$*"; }

CFG_ACTIVE="$REPO_DIR/audit/runtime/runpod/wave4_active_corpus.yaml"
[[ -f "$CFG_ACTIVE" ]] || { log "FATAL: active config $CFG_ACTIVE missing (run phase 20 first)."; exit 31; }

CKPT_DIR=$(python -c "
import yaml, sys
cfg = yaml.safe_load(open('$CFG_ACTIVE'))
print(cfg.get('checkpoint_dir', 'checkpoints/cekm'))
")
mkdir -p "$CKPT_DIR"

# Detect whether to resume.
RESUME_FLAG=""
LATEST=$(ls -t "$CKPT_DIR"/ckpt_step*.meta.json 2>/dev/null | head -1 || true)
if [[ -n "$LATEST" ]]; then
    log "Found existing checkpoint: $LATEST — running with --resume."
    RESUME_FLAG="--resume"
else
    log "No prior checkpoint; starting fresh CEKM training."
fi

# Materialise active config with current OOM-recovery batch size.
ATTEMPT_FILE="$REPO_DIR/audit/runtime/runpod/cekm_attempt.txt"
ATTEMPT=$(cat "$ATTEMPT_FILE" 2>/dev/null || echo 0)
ATTEMPT=$((ATTEMPT + 1))
echo "$ATTEMPT" > "$ATTEMPT_FILE"

case "$ATTEMPT" in
    1) BS=64; GA=4 ;;
    2) BS=32; GA=8 ;;
    *) BS=16; GA=16 ;;
esac
log "Attempt #$ATTEMPT — using batch_size=$BS gradient_accumulation_steps=$GA"

CFG_THIS_ATTEMPT="$REPO_DIR/audit/runtime/runpod/wave4_attempt_${ATTEMPT}.yaml"
python - <<PY
import yaml
cfg = yaml.safe_load(open('$CFG_ACTIVE'))
cfg['batch_size'] = $BS
cfg['gradient_accumulation_steps'] = $GA
yaml.safe_dump(cfg, open('$CFG_THIS_ATTEMPT', 'w'), sort_keys=False)
print('wrote', '$CFG_THIS_ATTEMPT')
PY

log "Launching synbio cekm train…"
log "GPU snapshot before training:"
nvidia-smi --query-gpu=name,memory.used,memory.total,temperature.gpu --format=csv

# Run; tee output. Time. Exit code propagates via pipefail.
TRAIN_LOG="$REPO_DIR/audit/runtime/runpod/cekm_train_attempt_${ATTEMPT}.log"
START=$(date -u +%s)
synbio cekm train --config "$CFG_THIS_ATTEMPT" $RESUME_FLAG 2>&1 | tee -a "$TRAIN_LOG"
RC=${PIPESTATUS[0]}
END=$(date -u +%s)
log "synbio cekm train exited rc=$RC after $(( (END-START)/60 )) min."

if [[ "$RC" -ne 0 ]]; then
    if grep -qE "CUDA out of memory|cuda.OutOfMemoryError|RuntimeError: CUDA" "$TRAIN_LOG"; then
        log "CUDA OOM detected; orchestrator will retry with smaller batch."
        exit 32
    fi
    if grep -qE "loss=nan|loss=NaN|nan loss|Loss is NaN" "$TRAIN_LOG"; then
        log "NaN loss detected; rolling back to previous checkpoint."
        # Train.py is expected to handle rollback internally on NaN; if not,
        # the orchestrator retry will re-resume from the last good checkpoint.
        exit 33
    fi
    log "Training failed with unhandled error (rc=$RC); see $TRAIN_LOG"
    exit "$RC"
fi

# Verify a final checkpoint exists.
LATEST_AFTER=$(ls -t "$CKPT_DIR"/ckpt_step*.meta.json 2>/dev/null | head -1 || true)
if [[ -z "$LATEST_AFTER" ]]; then
    log "FATAL: no checkpoint produced. Training may have hit max_steps=0 or config error."
    exit 34
fi
log "Final checkpoint: $LATEST_AFTER"
log "GPU snapshot after training:"
nvidia-smi --query-gpu=name,memory.used,memory.total --format=csv

log "CEKM training phase complete."
exit 0
