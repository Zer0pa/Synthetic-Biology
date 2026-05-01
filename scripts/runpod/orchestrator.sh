#!/usr/bin/env bash
# Synbio autonomous orchestrator — runs the phase chain on the H100 pod.
#
# Reads configs/runpod/orchestrator.yaml. For each phase: skips if the
# sentinel exists, runs otherwise, retries on failure, writes the
# sentinel + commits + pushes git on success. Maintains STATUS.md and
# PHASE_LOG.md so the operator can monitor progress without SSH.
#
# Resume safety: the chain is idempotent — re-running this orchestrator
# from a freshly-restarted pod picks up at the next unfinished phase.
# CEKM training within phase 30 has its own --resume flag that loads
# the latest checkpoint; phases that download data are no-op when the
# data already exists.
#
# Operator emergency stop: a `PAUSE_ORCHESTRATOR.flag` file at the repo
# root (committed from anywhere via git) causes the orchestrator to
# finish the current phase and exit gracefully.

set -uo pipefail

REPO_DIR="${REPO_DIR:-$(cd "$(dirname "$0")/../.." && pwd)}"
cd "$REPO_DIR"

CFG="configs/runpod/orchestrator.yaml"
RUNPOD_DIR="audit/runtime/runpod"
PHASES_DIR="scripts/runpod/phases"
mkdir -p "$RUNPOD_DIR"

STATUS_MD="$RUNPOD_DIR/STATUS.md"
PHASE_LOG="$RUNPOD_DIR/PHASE_LOG.md"
CURRENT_PHASE_FILE="$RUNPOD_DIR/CURRENT_PHASE.txt"
PAUSE_FLAG="PAUSE_ORCHESTRATOR.flag"
COMPLETE_FLAG="$RUNPOD_DIR/COMPLETE.flag"

START_TS=$(date -u +%s)
START_HUMAN=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

# ─── helpers ─────────────────────────────────────────────────────────────────
ts() { date -u +"%Y-%m-%dT%H:%M:%SZ"; }
log() { printf '[orchestrator %s] %s\n' "$(ts)" "$*"; }

write_status() {
    local current_phase="$1" state="$2" detail="${3:-}"
    local elapsed=$(( $(date -u +%s) - START_TS ))
    local elapsed_h=$(awk "BEGIN{printf \"%.2f\", $elapsed/3600.0}")
    {
        echo "# Synbio autonomous H100 SXM run — STATUS"
        echo
        echo "_Generated $(ts) by orchestrator. Pushed to git on every phase boundary; heartbeat updates separately every 60s._"
        echo
        echo "| Field | Value |"
        echo "|---|---|"
        echo "| Started (UTC) | $START_HUMAN |"
        echo "| Now (UTC)     | $(ts) |"
        echo "| Wallclock (h) | $elapsed_h |"
        echo "| Current phase | \`$current_phase\` |"
        echo "| State         | $state |"
        if [[ -n "$detail" ]]; then echo "| Detail        | $detail |"; fi
        if command -v nvidia-smi >/dev/null 2>&1; then
            local gpu=$(nvidia-smi --query-gpu=utilization.gpu,memory.used,memory.total --format=csv,noheader 2>/dev/null | head -1)
            echo "| GPU           | $gpu |"
        fi
        if [[ -d /workspace ]]; then
            local disk=$(df -h /workspace 2>/dev/null | awk 'NR==2 {print $4 " free of " $2}')
            echo "| Disk          | $disk |"
        fi
        local mem=$(free -h 2>/dev/null | awk '/^Mem/ {print $3 " used of " $2}')
        echo "| RAM           | $mem |"
        echo
        echo "## Phases"
        echo
        echo "| Phase | Status |"
        echo "|---|---|"
        for sentinel in "$RUNPOD_DIR"/phase_*.done; do
            [[ -e "$sentinel" ]] || continue
            local name=$(basename "$sentinel" .done)
            echo "| $name | DONE ($(stat -c %y "$sentinel" 2>/dev/null || stat -f %Sm "$sentinel" 2>/dev/null)) |"
        done
        if [[ -n "${PHASE_LIST:-}" ]]; then
            for ph in $PHASE_LIST; do
                [[ -e "$RUNPOD_DIR/phase_${ph}.done" ]] && continue
                if [[ "$ph" == "$current_phase" ]]; then
                    echo "| $ph | **RUNNING** |"
                else
                    echo "| $ph | pending |"
                fi
            done
        fi
        echo
        echo "## Boundary"
        echo "Research infrastructure for in silico synthetic biology / metabolic pathway engineering. Outputs are research artifacts. No regulatory certification claims. No clinical or human-subject use. No environmental release of GMOs."
    } > "$STATUS_MD.tmp"
    mv "$STATUS_MD.tmp" "$STATUS_MD"
    echo "$current_phase" > "$CURRENT_PHASE_FILE"
}

append_phase_log() {
    local event="$1" phase="$2" detail="$3"
    {
        printf '| %s | %s | %s | %s |\n' "$(ts)" "$phase" "$event" "$detail"
    } >> "$PHASE_LOG"
}

ensure_phase_log_header() {
    if [[ ! -f "$PHASE_LOG" ]]; then
        {
            echo "# Phase log"
            echo
            echo "Append-only log of phase events. The orchestrator writes here; do not edit."
            echo
            echo "| Timestamp (UTC) | Phase | Event | Detail |"
            echo "|---|---|---|---|"
        } > "$PHASE_LOG"
    fi
}

git_push_with_retry() {
    local commit_msg="$1"
    local backoffs=(10 30 60 180 600)
    git add "$RUNPOD_DIR" PAUSE_ORCHESTRATOR.flag 2>/dev/null || true
    if ! git diff --cached --quiet; then
        git -c user.email=architects@zer0pa.ai -c user.name="Zer0pa Pod Executor" \
            commit -m "$commit_msg" >/dev/null 2>&1 || true
    fi
    for delay in "${backoffs[@]}"; do
        if git push origin HEAD:main >/dev/null 2>&1; then
            return 0
        fi
        log "git push failed; retrying in ${delay}s…"
        sleep "$delay"
    done
    log "git push failed after all retries; will retry on next phase boundary."
    return 1
}

check_pause_flag() {
    # Refresh from origin; if PAUSE_ORCHESTRATOR.flag committed, exit gracefully.
    git fetch origin main >/dev/null 2>&1 || true
    if git ls-tree origin/main "$PAUSE_FLAG" 2>/dev/null | grep -q .; then
        log "PAUSE_ORCHESTRATOR.flag detected on origin/main; exiting gracefully."
        write_status "(paused)" "PAUSED_BY_OPERATOR" "PAUSE flag committed"
        git_push_with_retry "Orchestrator paused by operator at $(ts)"
        exit 42
    fi
}

# ─── parse YAML config (minimal jq-free YAML reader) ────────────────────────
# We only need: phase names, max_retries per phase, max_wallclock_hours.
# Uses POSIX-compatible awk/sed (works on Linux pod and macOS Mac).
read_phase_list() {
    # Extract the quoted phase names from `  - name: "<name>"` lines.
    grep -E '^[[:space:]]*-[[:space:]]+name:' "$CFG" \
        | sed -E 's/.*"([^"]+)".*/\1/'
}

read_phase_attr() {
    local phase="$1" attr="$2"
    awk -v phase="$phase" -v attr="$attr" '
        BEGIN { in_phase = 0 }
        /^[[:space:]]*-[[:space:]]+name:/ {
            in_phase = (index($0, "\"" phase "\"") > 0)
        }
        in_phase && $0 ~ ("^[[:space:]]+" attr ":") {
            sub(".*" attr ":[[:space:]]*", "")
            sub(/[[:space:]]*#.*$/, "")
            gsub(/^[[:space:]]+|[[:space:]]+$/, "")
            print
            exit
        }
    ' "$CFG"
}

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

# ─── main loop ───────────────────────────────────────────────────────────────
ensure_phase_log_header

PHASE_LIST=$(read_phase_list | tr '\n' ' ')
MAX_WALLCLOCK_HOURS=$(read_top_attr "max_wallclock_hours")
MAX_WALLCLOCK_HOURS=${MAX_WALLCLOCK_HOURS:-26.0}
MAX_WALLCLOCK_S=$(awk "BEGIN{printf \"%d\", $MAX_WALLCLOCK_HOURS * 3600}")

log "Orchestrator starting. Phases: $PHASE_LIST"
log "Max wallclock: ${MAX_WALLCLOCK_HOURS}h"
write_status "(starting)" "STARTING" "phases=${PHASE_LIST}"
append_phase_log "START" "(orchestrator)" "max_wallclock_hours=${MAX_WALLCLOCK_HOURS}"
git_push_with_retry "Autonomous orchestrator started at $(ts)" || true

for PHASE in $PHASE_LIST; do
    elapsed=$(( $(date -u +%s) - START_TS ))
    if (( MAX_WALLCLOCK_S > 0 && elapsed > MAX_WALLCLOCK_S )); then
        log "Max wallclock (${MAX_WALLCLOCK_HOURS}h) exceeded; aborting before $PHASE."
        write_status "$PHASE" "WALLCLOCK_EXCEEDED" "elapsed=$(($elapsed/3600))h"
        append_phase_log "WALLCLOCK_EXCEEDED" "$PHASE" ""
        git_push_with_retry "Wallclock cap reached; orchestrator stopping" || true
        exit 3
    fi

    SENTINEL="$RUNPOD_DIR/phase_${PHASE}.done"
    if [[ -f "$SENTINEL" ]]; then
        log "Phase $PHASE already done (sentinel exists); skipping."
        append_phase_log "SKIP" "$PHASE" "sentinel present"
        continue
    fi

    check_pause_flag

    SCRIPT="$PHASES_DIR/${PHASE}.sh"
    if [[ ! -x "$SCRIPT" ]]; then
        log "Phase script $SCRIPT missing or not executable; aborting."
        write_status "$PHASE" "FATAL" "script missing"
        append_phase_log "FATAL" "$PHASE" "script missing"
        git_push_with_retry "Phase $PHASE script missing; orchestrator halting" || true
        exit 4
    fi

    MAX_RETRIES=$(read_phase_attr "$PHASE" "max_retries")
    MAX_RETRIES=${MAX_RETRIES:-2}
    TIMEOUT_MIN=$(read_phase_attr "$PHASE" "timeout_minutes")
    TIMEOUT_MIN=${TIMEOUT_MIN:-60}
    OPTIONAL=$(read_phase_attr "$PHASE" "optional")
    OPTIONAL=${OPTIONAL:-false}

    log "─── Phase $PHASE start (timeout=${TIMEOUT_MIN}m, max_retries=$MAX_RETRIES, optional=$OPTIONAL) ───"
    write_status "$PHASE" "RUNNING" "timeout=${TIMEOUT_MIN}m retries=$MAX_RETRIES"
    append_phase_log "START" "$PHASE" "timeout=${TIMEOUT_MIN}m"
    git_push_with_retry "Phase $PHASE starting at $(ts)" || true

    PHASE_LOG_FILE="$RUNPOD_DIR/phase_${PHASE}.log"
    success=0
    for attempt in $(seq 0 "$MAX_RETRIES"); do
        log "Phase $PHASE attempt $((attempt+1))/$((MAX_RETRIES+1))…"
        # Run with hard timeout; capture exit code without aborting the orchestrator.
        if timeout "${TIMEOUT_MIN}m" "$SCRIPT" >>"$PHASE_LOG_FILE" 2>&1; then
            success=1
            log "Phase $PHASE succeeded on attempt $((attempt+1))."
            break
        else
            rc=$?
            log "Phase $PHASE failed on attempt $((attempt+1)) (rc=$rc); see phase_${PHASE}.log"
            append_phase_log "RETRY" "$PHASE" "attempt=$((attempt+1)) rc=$rc"
            sleep $(( 30 * (attempt + 1) ))
        fi
        check_pause_flag
    done

    if [[ "$success" -eq 1 ]]; then
        touch "$SENTINEL"
        append_phase_log "DONE" "$PHASE" ""
        write_status "$PHASE" "DONE" ""
        log "Phase $PHASE done; pushing to git."
        git_push_with_retry "Phase $PHASE complete at $(ts)" || true
    else
        if [[ "$OPTIONAL" == "true" ]]; then
            log "Phase $PHASE failed but is optional; recording skip and continuing."
            append_phase_log "SKIP_OPTIONAL_FAIL" "$PHASE" "all retries exhausted"
            write_status "$PHASE" "SKIPPED_OPTIONAL" "all retries failed"
            git_push_with_retry "Phase $PHASE optional-skip at $(ts)" || true
        else
            log "Phase $PHASE failed after $((MAX_RETRIES+1)) attempts; halting."
            write_status "$PHASE" "FATAL" "all retries exhausted"
            append_phase_log "FATAL" "$PHASE" "all retries exhausted"
            git_push_with_retry "Phase $PHASE FATAL at $(ts)" || true
            exit 5
        fi
    fi
done

# ─── all phases completed ────────────────────────────────────────────────────
touch "$COMPLETE_FLAG"
elapsed=$(( $(date -u +%s) - START_TS ))
elapsed_h=$(awk "BEGIN{printf \"%.2f\", $elapsed/3600.0}")
log "All phases complete in ${elapsed_h}h."
write_status "(complete)" "COMPLETE" "wallclock=${elapsed_h}h"
append_phase_log "ALL_DONE" "(orchestrator)" "wallclock=${elapsed_h}h"
git_push_with_retry "Autonomous run COMPLETE at $(ts) (${elapsed_h}h)" || true

log "Pod is now safe to shut down. The Mac can pick up artifacts via git pull + huggingface_hub download."
exit 0
