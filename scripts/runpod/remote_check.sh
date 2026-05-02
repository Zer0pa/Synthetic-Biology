#!/usr/bin/env bash
# Mac-side: 30-second pod-state probe used by the wake-up watcher.
#
# Reads the pod's git-pushed state surface (STATUS.md, heartbeat.txt,
# WATCHDOG_ALERTS.md, phase sentinels). Optionally tails the latest
# phase log via SSH if POD_SSH is exported.
#
# Usage:
#   POD_SSH="ssh root@<host> -p <port> -i ~/.ssh/<key>" \
#       bash scripts/runpod/remote_check.sh
#
# Exit codes:
#   0 = chain progressing or complete
#   1 = stuck (no heartbeat update for >20 min during a saturating phase)
#   2 = FATAL diagnostic in STATUS.md
#   3 = git pull failed (network/auth)

set -uo pipefail

REPO_DIR="${REPO_DIR:-$(cd "$(dirname "$0")/../.." && pwd)}"
cd "$REPO_DIR"

ts() { date -u +"%Y-%m-%dT%H:%M:%SZ"; }
log() { printf '[remote_check %s] %s\n' "$(ts)" "$*"; }

RUNPOD_DIR="audit/runtime/runpod"

# ─── pull latest pod-pushed state ────────────────────────────────────────
log "Pulling latest from origin/main…"
if ! git pull --ff-only origin main 2>&1 | tail -3; then
    log "git pull failed."
    exit 3
fi

# ─── completion check ────────────────────────────────────────────────────
if [[ -f "$RUNPOD_DIR/COMPLETE.flag" ]]; then
    log "✅ COMPLETE.flag present — autonomous run finished."
    if [[ -f FINAL-REPORT-RUNPOD-AUTONOMOUS.md ]]; then
        echo "Final report exists ($(wc -l < FINAL-REPORT-RUNPOD-AUTONOMOUS.md) lines)."
    fi
    exit 0
fi

# ─── status surface ──────────────────────────────────────────────────────
if [[ ! -f "$RUNPOD_DIR/STATUS.md" ]]; then
    log "No STATUS.md yet — pod has not pushed first heartbeat. Either bootstrap is still installing apt deps, or pod failed to start."
    exit 1
fi

echo "─── STATUS.md (head 30) ───"
head -30 "$RUNPOD_DIR/STATUS.md"
echo
echo "─── heartbeat.txt ───"
[[ -f "$RUNPOD_DIR/heartbeat.txt" ]] && cat "$RUNPOD_DIR/heartbeat.txt" || echo "(no heartbeat)"
echo
echo "─── done sentinels ───"
ls -1 "$RUNPOD_DIR"/phase_*.done 2>/dev/null | sed 's@.*/@  @' || echo "  (none yet)"
echo
echo "─── current phase ───"
[[ -f "$RUNPOD_DIR/CURRENT_PHASE.txt" ]] && cat "$RUNPOD_DIR/CURRENT_PHASE.txt" || echo "(unknown)"
echo

# ─── fatal-state detection ──────────────────────────────────────────────
if grep -qE "FATAL|WALLCLOCK_EXCEEDED" "$RUNPOD_DIR/STATUS.md"; then
    log "⚠️  FATAL or wallclock-exceeded state in STATUS.md."
    echo "─── PHASE_LOG.md (last 10) ───"
    tail -10 "$RUNPOD_DIR/PHASE_LOG.md" 2>/dev/null
    exit 2
fi

# ─── stuck-detection: heartbeat older than 20 min ───────────────────────
if [[ -f "$RUNPOD_DIR/heartbeat.txt" ]]; then
    HB_AGE=$(( $(date +%s) - $(stat -f %m "$RUNPOD_DIR/heartbeat.txt" 2>/dev/null || stat -c %Y "$RUNPOD_DIR/heartbeat.txt") ))
    log "Heartbeat age: ${HB_AGE}s"
    if (( HB_AGE > 1200 )); then
        log "⚠️  heartbeat is stale (>20 min) — pod may be stuck or pushed-but-not-pulled."
        exit 1
    fi
fi

# ─── watchdog alerts ─────────────────────────────────────────────────────
if [[ -f "$RUNPOD_DIR/WATCHDOG_ALERTS.md" ]] && grep -q "|" "$RUNPOD_DIR/WATCHDOG_ALERTS.md" 2>/dev/null; then
    ALERT_COUNT=$(grep -c '^| 2026' "$RUNPOD_DIR/WATCHDOG_ALERTS.md" || echo 0)
    if (( ALERT_COUNT > 0 )); then
        log "ℹ️  Watchdog has $ALERT_COUNT GPU-underutil alerts (informational; soft)."
    fi
fi

# ─── optional SSH probe (if POD_SSH set) ────────────────────────────────
if [[ -n "${POD_SSH:-}" ]]; then
    log "SSH probe (tmux session + GPU snapshot)…"
    $POD_SSH "tmux ls 2>/dev/null; nvidia-smi --query-gpu=utilization.gpu,memory.used,memory.total,power.draw,temperature.gpu --format=csv 2>/dev/null | head -2" 2>&1 | head -10
fi

log "Chain progressing."
exit 0
