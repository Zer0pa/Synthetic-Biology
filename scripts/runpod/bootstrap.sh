#!/usr/bin/env bash
# Synbio autonomous H100 SXM bootstrap.
#
# Single entry point. Pod startup command (or first-shell command) is:
#
#   curl -fsSL https://raw.githubusercontent.com/Zer0pa/Synthetic-Biology/main/scripts/runpod/bootstrap.sh | bash
#
# OR (after first manual SSH):
#
#   git clone https://github.com/Zer0pa/Synthetic-Biology /workspace/Synthetic-Biology
#   cd /workspace/Synthetic-Biology
#   bash scripts/runpod/bootstrap.sh
#
# Required env vars (set in Runpod UI):
#   HF_TOKEN          — Hugging Face token with write access to Architect-Prime
#   GH_TOKEN          — GitHub PAT with `repo` scope on Zer0pa/Synthetic-Biology
#   FOUNDRY_TOKEN     — (optional) RosettaCommons Foundry token for RFdiffusion3
#
# What this does:
#   1. Configures the workspace + git auth
#   2. Clones (or updates) the repo at /workspace/Synthetic-Biology
#   3. Installs apt-level deps (tmux, jq, etc.)
#   4. Launches the orchestrator + heartbeat + watchdog inside a tmux
#      session named `synbio` so SSH disconnect cannot kill the run
#   5. Returns immediately. Detached chain continues.
#
# After this script returns:
#   - tmux ls   shows the synbio session
#   - tmux attach -t synbio   to view live (split panes)
#   - git pull && cat audit/runtime/runpod/STATUS.md   to see status from anywhere

set -euo pipefail

# ─── colours / logging ────────────────────────────────────────────────────────
RED=$'\033[0;31m'; GREEN=$'\033[0;32m'; YELLOW=$'\033[1;33m'; NC=$'\033[0m'
log() { printf '%s[bootstrap]%s %s\n' "$GREEN" "$NC" "$*"; }
warn() { printf '%s[bootstrap]%s %s\n' "$YELLOW" "$NC" "$*" >&2; }
fatal() { printf '%s[bootstrap]%s %s\n' "$RED" "$NC" "$*" >&2; exit 1; }

# ─── env validation ───────────────────────────────────────────────────────────
: "${HF_TOKEN:?HF_TOKEN must be set in pod env (HuggingFace write token)}"
: "${GH_TOKEN:?GH_TOKEN must be set in pod env (GitHub PAT, repo scope)}"
# FOUNDRY_TOKEN is optional; phases that need it will skip if missing.

# ─── workspace ────────────────────────────────────────────────────────────────
WORKSPACE="${WORKSPACE:-/workspace}"
REPO_DIR="$WORKSPACE/Synthetic-Biology"
mkdir -p "$WORKSPACE"
cd "$WORKSPACE"

# ─── apt deps (tmux is essential for detachment) ─────────────────────────────
if ! command -v tmux >/dev/null 2>&1; then
    log "Installing apt deps (tmux jq curl ca-certificates git build-essential)…"
    if command -v apt-get >/dev/null 2>&1; then
        DEBIAN_FRONTEND=noninteractive apt-get update -y
        DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
            tmux jq curl ca-certificates git build-essential
    else
        warn "apt-get not found; assuming tmux/jq/git already installed."
    fi
fi
for bin in tmux jq git; do
    command -v "$bin" >/dev/null 2>&1 || fatal "$bin not on PATH after apt install."
done

# ─── git auth ─────────────────────────────────────────────────────────────────
log "Configuring git for autonomous push…"
git config --global user.email "architects@zer0pa.ai"
git config --global user.name "Zer0pa Pod Executor"
git config --global credential.helper store
# Persist GH_TOKEN to ~/.git-credentials so push works without prompts.
echo "https://x-access-token:${GH_TOKEN}@github.com" > "${HOME}/.git-credentials"
chmod 600 "${HOME}/.git-credentials"

# ─── clone or update repo ─────────────────────────────────────────────────────
if [[ -d "$REPO_DIR/.git" ]]; then
    log "Repo already at $REPO_DIR; fetching latest main…"
    cd "$REPO_DIR"
    git fetch origin main
    # Don't blow away local state — fast-forward only.
    git checkout main 2>/dev/null || git checkout -B main origin/main
    git pull --ff-only origin main || warn "git pull --ff-only failed; continuing with current state."
else
    log "Cloning Zer0pa/Synthetic-Biology to $REPO_DIR…"
    git clone https://github.com/Zer0pa/Synthetic-Biology "$REPO_DIR"
    cd "$REPO_DIR"
fi

# ─── HF auth ──────────────────────────────────────────────────────────────────
log "Persisting HF_TOKEN to ~/.cache/huggingface/token (read by huggingface_hub)…"
mkdir -p "${HOME}/.cache/huggingface"
echo -n "$HF_TOKEN" > "${HOME}/.cache/huggingface/token"
chmod 600 "${HOME}/.cache/huggingface/token"

# ─── make scripts executable ──────────────────────────────────────────────────
chmod +x scripts/runpod/*.sh scripts/runpod/phases/*.sh 2>/dev/null || true

# ─── prepare runpod runtime dir ───────────────────────────────────────────────
RUNPOD_DIR="$REPO_DIR/audit/runtime/runpod"
mkdir -p "$RUNPOD_DIR"

# ─── kill any stale tmux session of the same name ────────────────────────────
if tmux has-session -t synbio 2>/dev/null; then
    warn "Existing tmux session 'synbio' found; killing it (use --keep to override)."
    if [[ "${1:-}" != "--keep" ]]; then
        tmux kill-session -t synbio
    fi
fi

# ─── launch tmux with three panes: orchestrator | heartbeat | watchdog ───────
log "Launching tmux session 'synbio' with orchestrator + heartbeat + watchdog…"
tmux new-session -d -s synbio -n main -c "$REPO_DIR" \
    "bash scripts/runpod/orchestrator.sh 2>&1 | tee -a $RUNPOD_DIR/orchestrator.log"
tmux split-window -t synbio:0 -h -c "$REPO_DIR" \
    "bash scripts/runpod/heartbeat.sh 2>&1 | tee -a $RUNPOD_DIR/heartbeat.log"
tmux split-window -t synbio:0 -v -c "$REPO_DIR" \
    "bash scripts/runpod/watchdog.sh 2>&1 | tee -a $RUNPOD_DIR/watchdog.log"
tmux select-pane -t synbio:0.0

# ─── confirmation ─────────────────────────────────────────────────────────────
log "Bootstrap complete. The autonomous chain is now running detached in tmux."
log ""
log "  Inspect live:    tmux attach -t synbio    (Ctrl-b d to detach)"
log "  Inspect from anywhere:"
log "                   git pull --ff-only && cat audit/runtime/runpod/STATUS.md"
log "  Pause gracefully (from any clone):"
log "                   touch PAUSE_ORCHESTRATOR.flag && git add PAUSE_ORCHESTRATOR.flag &&"
log "                   git commit -m 'Pause autonomous run' && git push origin main"
log ""
log "Estimated total wallclock: 16–24 h. The pod is independent of the originating Mac."
exit 0
