#!/usr/bin/env bash
# Phase 00 — preflight checks. Bail early on anything missing.
set -euo pipefail

REPO_DIR="${REPO_DIR:-$(cd "$(dirname "$0")/../../.." && pwd)}"
cd "$REPO_DIR"

ts() { date -u +"%Y-%m-%dT%H:%M:%SZ"; }
log() { printf '[00_preflight %s] %s\n' "$(ts)" "$*"; }

log "Working dir: $(pwd)"
log "Hostname: $(hostname)"
log "Date: $(date -u)"

# ─── CUDA / GPU ───────────────────────────────────────────────────────────
if ! command -v nvidia-smi >/dev/null 2>&1; then
    log "FATAL: nvidia-smi not found. Pod is not GPU-equipped."
    exit 10
fi
nvidia-smi
GPU_NAME=$(nvidia-smi --query-gpu=name --format=csv,noheader | head -1)
GPU_MEM_TOTAL_MIB=$(nvidia-smi --query-gpu=memory.total --format=csv,noheader,nounits | head -1)
log "GPU: $GPU_NAME ($GPU_MEM_TOTAL_MIB MiB total)"
if (( GPU_MEM_TOTAL_MIB < 60000 )); then
    log "WARNING: GPU memory < 60 GiB. CEKM training may need batch_size reduction."
fi

# ─── Disk ─────────────────────────────────────────────────────────────────
DISK_FREE_GB=$(df -BG /workspace 2>/dev/null | awk 'NR==2 {gsub(/G/,"",$4); print $4}')
DISK_FREE_GB=${DISK_FREE_GB:-0}
log "Disk free on /workspace: ${DISK_FREE_GB} GiB"
if (( DISK_FREE_GB < 100 )); then
    log "FATAL: less than 100 GiB free on /workspace. Need ~150 GiB for CEKM corpora + checkpoints."
    exit 11
fi

# ─── Tokens ───────────────────────────────────────────────────────────────
: "${HF_TOKEN:?HF_TOKEN unset}"
: "${GH_TOKEN:?GH_TOKEN unset}"
log "HF_TOKEN: present (${#HF_TOKEN} chars)"
log "GH_TOKEN: present (${#GH_TOKEN} chars)"

# ─── Python ───────────────────────────────────────────────────────────────
log "Python: $(python3 --version)"
log "Pip: $(pip --version 2>/dev/null || echo 'pip not yet installed')"

# ─── Git ──────────────────────────────────────────────────────────────────
log "Git remote: $(git remote get-url origin)"
log "Git HEAD: $(git rev-parse HEAD)"
log "Git branch: $(git rev-parse --abbrev-ref HEAD)"

# ─── Acknowledge boundary ────────────────────────────────────────────────
log "Boundary block: research artifact only; no clinical / regulatory / environmental claim."

log "Preflight OK."
exit 0
