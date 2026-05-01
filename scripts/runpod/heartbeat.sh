#!/usr/bin/env bash
# Synbio autonomous heartbeat.
#
# Writes audit/runtime/runpod/heartbeat.txt every 60s with current
# phase / GPU util / disk / RAM. Pushes the heartbeat file to git
# every N seconds (per orchestrator.yaml: heartbeat_git_push_period_s,
# default 600s = 10 min). The operator can `git fetch && cat
# audit/runtime/runpod/heartbeat.txt` from any clone to see live
# state without SSH.

set -uo pipefail

REPO_DIR="${REPO_DIR:-$(cd "$(dirname "$0")/.." && pwd)}"
cd "$REPO_DIR"

CFG="configs/runpod/orchestrator.yaml"
RUNPOD_DIR="audit/runtime/runpod"
HEARTBEAT="$RUNPOD_DIR/heartbeat.txt"
mkdir -p "$RUNPOD_DIR"

read_top_attr() {
    local attr="$1"
    awk -v attr="$attr" '
        $0 ~ ("^" attr ":") {
            sub(".*" attr ":[[:space:]]*", "")
            sub(/[[:space:]]*#.*$/, "")
            gsub(/^[[:space:]]+|[[:space:]]+$/, "")
            print
            exit
        }
    ' "$CFG"
}

PERIOD_LOCAL=$(read_top_attr "heartbeat_local_period_s")
PERIOD_LOCAL=${PERIOD_LOCAL:-60}
PERIOD_GIT=$(read_top_attr "heartbeat_git_push_period_s")
PERIOD_GIT=${PERIOD_GIT:-600}

ts() { date -u +"%Y-%m-%dT%H:%M:%SZ"; }
log() { printf '[heartbeat %s] %s\n' "$(ts)" "$*"; }

log "Heartbeat starting (local=${PERIOD_LOCAL}s, git_push=${PERIOD_GIT}s)…"

last_git_push=0
START_TS=$(date -u +%s)

while true; do
    now=$(date -u +%s)
    elapsed=$(( now - START_TS ))
    elapsed_h=$(awk "BEGIN{printf \"%.2f\", $elapsed/3600.0}")

    cur_phase="(idle)"
    if [[ -f "$RUNPOD_DIR/CURRENT_PHASE.txt" ]]; then
        cur_phase=$(cat "$RUNPOD_DIR/CURRENT_PHASE.txt" 2>/dev/null || echo "?")
    fi

    gpu_line=""
    if command -v nvidia-smi >/dev/null 2>&1; then
        gpu_line=$(nvidia-smi --query-gpu=utilization.gpu,memory.used,memory.total,power.draw,temperature.gpu \
            --format=csv,noheader 2>/dev/null | head -1)
    fi
    disk_line=""
    if [[ -d /workspace ]]; then
        disk_line=$(df -h /workspace 2>/dev/null | awk 'NR==2 {print $4 " free of " $2 " (" $5 " used)"}')
    fi
    ram_line=$(free -h 2>/dev/null | awk '/^Mem/ {print $3 " used / " $2 " total"}')

    last_log=""
    cur_phase_log="$RUNPOD_DIR/phase_${cur_phase}.log"
    if [[ -f "$cur_phase_log" ]]; then
        last_log=$(tail -1 "$cur_phase_log" 2>/dev/null | head -c 200)
    fi

    {
        echo "TIMESTAMP_UTC: $(ts)"
        echo "WALLCLOCK_HOURS: $elapsed_h"
        echo "CURRENT_PHASE: $cur_phase"
        echo "GPU: $gpu_line"
        echo "DISK: $disk_line"
        echo "RAM: $ram_line"
        echo "LAST_PHASE_LOG_LINE: $last_log"
        echo "BOUNDARY: research artifact only; no clinical/regulatory/environmental claim."
    } > "$HEARTBEAT.tmp"
    mv "$HEARTBEAT.tmp" "$HEARTBEAT"

    if (( now - last_git_push >= PERIOD_GIT )); then
        # Push the heartbeat (and any other tracked runpod files) to git.
        if git -c user.email=architects@zer0pa.ai -c user.name="Zer0pa Pod Executor" add "$HEARTBEAT" "$RUNPOD_DIR/CURRENT_PHASE.txt" 2>/dev/null; then
            if ! git diff --cached --quiet; then
                git -c user.email=architects@zer0pa.ai -c user.name="Zer0pa Pod Executor" commit -m "Heartbeat $(ts)" >/dev/null 2>&1 || true
                if git push origin HEAD:main >/dev/null 2>&1; then
                    last_git_push=$now
                else
                    log "git push failed (will retry on next heartbeat tick)."
                fi
            fi
        fi
    fi

    sleep "$PERIOD_LOCAL"
done
