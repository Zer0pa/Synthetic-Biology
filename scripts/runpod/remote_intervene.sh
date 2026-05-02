#!/usr/bin/env bash
# Mac-side: SSH-driven intervention helpers for the autonomous pod chain.
#
# Used by the wake-up watcher when remote_check.sh returns non-zero
# (FATAL or stuck). Each subcommand is one bounded operation.
#
# Usage:
#   export POD_SSH="ssh root@<host> -p <port> -i ~/.ssh/<key>"
#   bash scripts/runpod/remote_intervene.sh <command> [args]
#
# Commands:
#   tail-current             Tail the current phase's log (last 100 lines).
#   tail-phase <NN_name>     Tail a specific phase's log.
#   gpu                      Show nvidia-smi output.
#   tmux-attach              Print the command to attach to the synbio session.
#   restart-orchestrator     Kill the orchestrator pane and re-launch it (resumes from sentinels).
#   force-skip <NN_name>     Touch a phase sentinel to skip it (use carefully).
#   pull-latest              Pull origin/main on the pod (re-syncs after Mac-side commits).
#   ssh                      Open an interactive SSH session.

set -uo pipefail

REPO_DIR="${REPO_DIR:-$(cd "$(dirname "$0")/../.." && pwd)}"
cd "$REPO_DIR"

ts() { date -u +"%Y-%m-%dT%H:%M:%SZ"; }
log() { printf '[intervene %s] %s\n' "$(ts)" "$*"; }

if [[ -z "${POD_SSH:-}" ]]; then
    log "FATAL: POD_SSH not set. Export e.g.:"
    log "  export POD_SSH=\"ssh root@<host> -p <port> -i ~/.ssh/id_pod\""
    exit 10
fi

POD_REPO="${POD_REPO:-/workspace/Synthetic-Biology}"
RUNPOD_DIR="audit/runtime/runpod"

CMD="${1:-help}"

case "$CMD" in
    tail-current)
        # Pull current phase from heartbeat (Mac-side after git pull).
        git pull --ff-only origin main >/dev/null 2>&1 || true
        PHASE=$(cat "$RUNPOD_DIR/CURRENT_PHASE.txt" 2>/dev/null || echo "?")
        log "Tailing pod's $PHASE phase log…"
        $POD_SSH "tail -100 $POD_REPO/$RUNPOD_DIR/phase_${PHASE}.log 2>&1"
        ;;
    tail-phase)
        PHASE="${2:?missing phase name e.g. 30_cekm_train}"
        $POD_SSH "tail -200 $POD_REPO/$RUNPOD_DIR/phase_${PHASE}.log"
        ;;
    gpu)
        $POD_SSH "nvidia-smi"
        ;;
    tmux-attach)
        echo "Run interactively:"
        echo "  $POD_SSH -t 'tmux attach -t synbio'"
        ;;
    restart-orchestrator)
        log "Killing tmux pane 0 and relaunching orchestrator (resumes from sentinels)…"
        $POD_SSH "cd $POD_REPO && \
            tmux kill-window -t synbio:0 2>/dev/null; \
            tmux new-window -t synbio: -n main -c $POD_REPO 'bash scripts/runpod/orchestrator.sh 2>&1 | tee -a $RUNPOD_DIR/orchestrator.log'"
        ;;
    force-skip)
        PHASE="${2:?missing phase}"
        log "WARNING: marking phase $PHASE as done (skipping it)."
        $POD_SSH "touch $POD_REPO/$RUNPOD_DIR/phase_${PHASE}.done && \
                  cd $POD_REPO && git add $RUNPOD_DIR/phase_${PHASE}.done && \
                  git commit -m 'Operator force-skip: $PHASE' && git push origin HEAD:main"
        ;;
    pull-latest)
        log "Pulling origin/main on the pod…"
        $POD_SSH "cd $POD_REPO && git pull --ff-only origin main"
        ;;
    ssh)
        exec $POD_SSH
        ;;
    *)
        cat <<USAGE
Usage: $0 <command> [args]
  tail-current
  tail-phase <NN_name>
  gpu
  tmux-attach
  restart-orchestrator
  force-skip <NN_name>
  pull-latest
  ssh
USAGE
        exit 1
        ;;
esac
