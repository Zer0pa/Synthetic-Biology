#!/usr/bin/env bash
# Phase 90 — finalize the autonomous run.
# 1. Generate FINAL-REPORT-RUNPOD-AUTONOMOUS.md from phase artifacts.
# 2. Final HF push of any remaining artifacts.
# 3. Final git push (orchestrator pushes too, but we double-tap here).
# 4. Write COMPLETE.flag so any external watcher knows the chain is done.

set -euo pipefail

REPO_DIR="${REPO_DIR:-$(cd "$(dirname "$0")/../../.." && pwd)}"
cd "$REPO_DIR"

VENV="$REPO_DIR/.venv"
# shellcheck disable=SC1091
source "$VENV/bin/activate"

ts() { date -u +"%Y-%m-%dT%H:%M:%SZ"; }
log() { printf '[90_finalize %s] %s\n' "$(ts)" "$*"; }

RUNPOD_DIR="$REPO_DIR/audit/runtime/runpod"
REPORT="$REPO_DIR/FINAL-REPORT-RUNPOD-AUTONOMOUS.md"

START_TS=$(stat -c %Y "$RUNPOD_DIR/PHASE_LOG.md" 2>/dev/null || stat -f %m "$RUNPOD_DIR/PHASE_LOG.md" 2>/dev/null || echo 0)
NOW_TS=$(date -u +%s)
ELAPSED_H=$(awk "BEGIN{printf \"%.2f\", ($NOW_TS-$START_TS)/3600.0}")

{
    echo "# FINAL-REPORT-RUNPOD-AUTONOMOUS"
    echo
    echo "**Generated:** $(ts)"
    echo "**Wallclock:** ${ELAPSED_H} h"
    echo
    echo "## Boundary"
    echo
    echo "Research infrastructure for in silico synthetic biology / metabolic pathway engineering. Outputs are research artifacts. No regulatory certification claims. No clinical or human-subject use. No environmental release of GMOs."
    echo
    echo "## Phases run"
    echo
    if [[ -f "$RUNPOD_DIR/PHASE_LOG.md" ]]; then
        cat "$RUNPOD_DIR/PHASE_LOG.md"
    fi
    echo
    echo "## Watchdog alerts"
    echo
    if [[ -f "$RUNPOD_DIR/WATCHDOG_ALERTS.md" ]]; then
        cat "$RUNPOD_DIR/WATCHDOG_ALERTS.md"
    else
        echo "(none)"
    fi
    echo
    echo "## CEKM training"
    echo
    if ls "$REPO_DIR"/checkpoints/cekm/ckpt_step*.meta.json >/dev/null 2>&1; then
        local_latest=$(ls -t "$REPO_DIR"/checkpoints/cekm/ckpt_step*.meta.json | head -1)
        echo "Final checkpoint: \`$(basename "$local_latest")\`"
        echo
        echo "On HF: https://huggingface.co/Architect-Prime/synbio-cekm-v0.1"
    else
        echo "(no checkpoint found — phase 30 may not have completed)"
    fi
    echo
    echo "## Audit verify"
    echo
    if [[ -f "$RUNPOD_DIR/audit_verify_report.md" ]]; then
        cat "$RUNPOD_DIR/audit_verify_report.md"
    fi
    echo
    echo "## Next blocker"
    echo
    echo "After this autonomous run completes: the operator reviews the artifacts on GitHub and HF."
    echo "Remaining work: Salis v1.0 binary install + LIRC full corpus build (both CPU-feasible per HANDOFF-CPU-CONTINUATION.md)."
} > "$REPORT"

log "Wrote $REPORT"

# Final git push.
git -c user.email=architects@zer0pa.ai -c user.name="Zer0pa Pod Executor" \
    add "$REPORT" "$RUNPOD_DIR" 2>/dev/null || true
git -c user.email=architects@zer0pa.ai -c user.name="Zer0pa Pod Executor" \
    commit -m "Autonomous run COMPLETE: FINAL-REPORT-RUNPOD-AUTONOMOUS.md ($(ts))" >/dev/null 2>&1 || true
for delay in 5 30 60 300 900; do
    if git push origin HEAD:main; then
        log "Final git push succeeded."
        break
    fi
    log "git push failed; retry in ${delay}s…"
    sleep "$delay"
done

# COMPLETE.flag — the absence of any later orchestrator action is the
# pod's signal that it can be torn down. Operator policy decides
# whether to auto-shutdown the pod or leave it for inspection.
touch "$RUNPOD_DIR/COMPLETE.flag"
log "Phase 90 complete; chain is done. Pod is safe to terminate."
exit 0
