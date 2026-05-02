#!/usr/bin/env bash
# Phase 50 — push CEKM checkpoints + audit JSONL + meta to HF
# Architect-Prime/synbio-cekm-v0.1. Idempotent (HF dedups by content).
set -euo pipefail

REPO_DIR="${REPO_DIR:-$(cd "$(dirname "$0")/../../.." && pwd)}"
cd "$REPO_DIR"

VENV="$REPO_DIR/.venv"
# shellcheck disable=SC1091
source "$VENV/bin/activate"

ts() { date -u +"%Y-%m-%dT%H:%M:%SZ"; }
log() { printf '[50_hf_push_cekm %s] %s\n' "$(ts)" "$*"; }

CFG_ACTIVE="$REPO_DIR/audit/runtime/runpod/wave4_active_corpus.yaml"
HF_REPO=$(python -c "
import yaml; cfg = yaml.safe_load(open('$CFG_ACTIVE')); print(cfg.get('hf_repo_id', 'Architect-Prime/synbio-cekm-v0.1'))
")
CKPT_DIR=$(python -c "
import yaml; cfg = yaml.safe_load(open('$CFG_ACTIVE')); print(cfg.get('checkpoint_dir', 'checkpoints/cekm'))
")

log "Pushing CEKM artifacts to HF repo: $HF_REPO"

# Push the directory; HF CLI handles deltas + retries internally.
# `hf upload --include` accepts ONE pattern per flag — pass each
# pattern as its own --include rather than space-separated args
# (which the CLI rejects as "unexpected extra arguments").
hf upload "$HF_REPO" "$CKPT_DIR" "." \
    --commit-message "Pod-autonomous CEKM checkpoint push at $(ts)" \
    --include "ckpt_step*" \
    --include "*.meta.json" \
    --include "cekm_training_audit.jsonl" \
    --include "README.md" \
    2>&1 | tee "$REPO_DIR/audit/runtime/runpod/cekm_hf_push.log"

# Verify by querying HF that the latest checkpoint is present.
LATEST_LOCAL=$(ls -t "$CKPT_DIR"/ckpt_step*.meta.json 2>/dev/null | head -1 | xargs -I{} basename {} .meta.json)
if [[ -n "$LATEST_LOCAL" ]]; then
    log "Verifying $LATEST_LOCAL is on HF…"
    if hf download "$HF_REPO" "${LATEST_LOCAL}.meta.json" -q >/dev/null 2>&1; then
        log "Verified: $LATEST_LOCAL is on HF."
    else
        log "WARNING: could not verify $LATEST_LOCAL on HF; manual check recommended."
    fi
fi

log "HF push phase complete."
exit 0
