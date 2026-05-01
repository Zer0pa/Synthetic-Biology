#!/usr/bin/env bash
# Zer0pa Synbio — Pod Orchestrator (Murphy's-law resilient)
#
# Runs every phase in sequence. Phase markers under $RUN_ROOT/state/ make
# it idempotent on restart: re-running this script picks up exactly where
# it left off. Heartbeat at $RUN_ROOT/state/heartbeat.txt is updated every
# 30 s by a background loop. STATUS.txt is the live ledger.
#
# This script is designed to be run inside `tmux` so SSH disconnects
# don't kill it. Suggested launch:
#
#   tmux new-session -d -s synbio "bash /workspace/synbio-run/repo/runtime/orchestrator.sh"
#
# Re-run policy: `tmux attach -t synbio` to monitor, or `bash <script>`
# from a fresh shell to resume from last checkpoint.

set -uo pipefail

# Boundary block (must appear verbatim per RESISTANCE.md):
# Research infrastructure for in silico synthetic biology / metabolic
# pathway engineering. Outputs are research artifacts — predicted
# pathways, predicted KPIs, candidate genetic modification specifications.
# No regulatory certification claims. No clinical or human-subject use.
# No environmental release of GMOs. No biocontainment-level claims (the
# pipeline does not commission BSL-2/3 work). No human gene drive or
# eugenic application. Defence / weapons / dual-use bio applications
# excluded under operator policy.

RUN_ROOT="${RUN_ROOT:-/workspace/synbio-run}"
REPO="$RUN_ROOT/repo"
STATE="$RUN_ROOT/state"
LOGS="$RUN_ROOT/logs"
PHASES="$REPO/runtime/phases"

mkdir -p "$STATE" "$LOGS"

STATUS="$STATE/STATUS.txt"
HEARTBEAT="$STATE/heartbeat.txt"

ts() { date -Iseconds 2>/dev/null || date '+%Y-%m-%dT%H:%M:%S%z'; }

log_status() {
  local line="[$(ts)] $*"
  echo "$line"
  echo "$line" >> "$STATUS"
}

# Heartbeat in background — updated every 30s. Killed on script exit.
heartbeat_loop() {
  while true; do
    date +%s > "$HEARTBEAT"
    sleep 30
  done
}

# Source env.sh if present (sets venv, HF_HOME, etc.)
if [ -f "$RUN_ROOT/env.sh" ]; then
  # shellcheck disable=SC1090
  . "$RUN_ROOT/env.sh"
fi

# Phase guard: skip if marker exists; run otherwise.
phase() {
  local id="$1" desc="$2"
  shift 2
  local marker="$STATE/${id}.done"
  local logfile="$LOGS/${id}.log"

  if [ -f "$marker" ]; then
    log_status "SKIP  $id: $desc (already done; marker $marker)"
    return 0
  fi

  log_status "START $id: $desc"
  if "$@" > "$logfile" 2>&1; then
    touch "$marker"
    log_status "DONE  $id: $desc (log: $logfile)"
    return 0
  else
    local rc=$?
    log_status "FAIL  $id: $desc (rc=$rc; log: $logfile)"
    log_status "       Last 20 lines of log:"
    tail -20 "$logfile" | sed 's/^/         /' | tee -a "$STATUS" >/dev/null
    return $rc
  fi
}

# Main.
log_status "==== Zer0pa Synbio Pod Orchestrator ===="
log_status "RUN_ROOT=$RUN_ROOT"
log_status "REPO=$REPO ($(cd "$REPO" && git log -1 --oneline 2>/dev/null || echo 'no git'))"
log_status "GPU: $(nvidia-smi --query-gpu=name,memory.total --format=csv,noheader 2>/dev/null || echo none)"

# Start heartbeat in background.
heartbeat_loop &
HEARTBEAT_PID=$!
trap "kill $HEARTBEAT_PID 2>/dev/null; log_status 'orchestrator exit'" EXIT INT TERM

# ─── Phases ────────────────────────────────────────────────────────────
# Each phase script is idempotent and exits 0 on success.

phase 00_health_check          "Pod + Python + GPU sanity"            bash "$PHASES/00_health_check.sh" || exit 1
phase 10_pull_models           "HF model pulls (ESM-2-650M)"           bash "$PHASES/10_pull_models.sh"
phase 20_lirc_slice            "LIRC slice (real Rhea metadata)"       bash "$PHASES/20_lirc_slice.sh"
phase 30_test_suite            "pytest -q (full suite)"                bash "$PHASES/30_test_suite.sh"
phase 40_cutover_invariance    "Wave 11 invariance under runpod_rest"  bash "$PHASES/40_cutover_invariance.sh"
phase 50_esm2_real_l1          "Real ESM-2 batched embeddings (L1)"    bash "$PHASES/50_esm2_real_l1.sh"
phase 60_hmo_2pfl              "HMO seed: 2'-FL (scientific mode)"     bash "$PHASES/60_hmo_seed.sh" 2pFL
phase 60_hmo_3psl              "HMO seed: 3'-SL (scientific mode)"     bash "$PHASES/60_hmo_seed.sh" 3pSL
phase 60_hmo_dslnt             "HMO seed: DSLNT (scientific mode)"     bash "$PHASES/60_hmo_seed.sh" DSLNT
phase 70_audit_verify          "Audit conformance verify all 3 seeds"  bash "$PHASES/70_audit_verify.sh"
phase 80_hf_smoke              "HF Architect-Prime smoke push"         bash "$PHASES/80_hf_smoke.sh"
phase 90_final_report          "Write FINAL-REPORT-RUNPOD.md"          bash "$PHASES/90_final_report.sh"
phase 95_git_push              "git push origin main"                  bash "$PHASES/95_git_push.sh"

log_status "==== ALL PHASES COMPLETE ===="
log_status "See $STATUS for the full ledger; $LOGS/*.log for per-phase output."
