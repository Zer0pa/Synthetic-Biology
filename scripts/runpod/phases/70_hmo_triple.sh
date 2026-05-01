#!/usr/bin/env bash
# Phase 70 — Wave 9 HMO triple full numerical run.
# Re-runs validation/hmo-seed-evidence/run_seed.py for each of the
# three seeds with all upstream layers now real (CEKM trained, ESMFold
# real, eQuilibrator MDF real, BoTorch real, etc.). Outputs
# scientific_valid envelopes where the underlying tools support it.

set -euo pipefail

REPO_DIR="${REPO_DIR:-$(cd "$(dirname "$0")/../../.." && pwd)}"
cd "$REPO_DIR"

VENV="$REPO_DIR/.venv"
# shellcheck disable=SC1091
source "$VENV/bin/activate"

ts() { date -u +"%Y-%m-%dT%H:%M:%SZ"; }
log() { printf '[70_hmo_triple %s] %s\n' "$(ts)" "$*"; }

OUT_LOG="$REPO_DIR/audit/runtime/runpod/hmo_triple.log"
: > "$OUT_LOG"

for SEED in 2pFL 3pSL DSLNT; do
    log "──── Running HMO seed $SEED ────"
    python validation/hmo-seed-evidence/run_seed.py --seed "$SEED" 2>&1 | tee -a "$OUT_LOG"
    log "Seed $SEED complete."
done

log "HMO triple phase complete; output at $OUT_LOG"
exit 0
