#!/usr/bin/env bash
# Synbio GPU watchdog.
#
# Monitors GPU utilization during phases that *should* saturate the
# H100 (CEKM training, calibration eval, ESMFold/MACE-OFF inference).
# If GPU util stays below the threshold for the watchdog window, an
# alert is appended to STATUS.md and pushed to git so the operator
# sees the underutilization in their next `git pull`.
#
# This is a soft alert — it does not kill any phase. The orchestrator
# decides whether to retry on phase timeout.

set -uo pipefail

REPO_DIR="${REPO_DIR:-$(cd "$(dirname "$0")/.." && pwd)}"
cd "$REPO_DIR"

RUNPOD_DIR="audit/runtime/runpod"
mkdir -p "$RUNPOD_DIR"
ALERT_FILE="$RUNPOD_DIR/WATCHDOG_ALERTS.md"

# Phases we expect to saturate the GPU (>=20% util sustained).
SATURATING_PHASES=(
    "30_cekm_train"
    "40_cekm_eval"
    "50_hf_push_cekm"
    "60_l45_inference"
    "70_hmo_triple"
)

UTIL_THRESHOLD_PCT=10        # below this counts as "underutilized"
UNDERUTIL_WINDOW_S=600       # 10 minutes of underutilization triggers alert
SAMPLE_PERIOD_S=60

ts() { date -u +"%Y-%m-%dT%H:%M:%SZ"; }
log() { printf '[watchdog %s] %s\n' "$(ts)" "$*"; }

is_saturating_phase() {
    local p="$1"
    for sp in "${SATURATING_PHASES[@]}"; do
        [[ "$p" == "$sp" ]] && return 0
    done
    return 1
}

if ! command -v nvidia-smi >/dev/null 2>&1; then
    log "nvidia-smi not on PATH; watchdog is no-op."
    while true; do sleep 3600; done
fi

log "Watchdog starting (threshold=${UTIL_THRESHOLD_PCT}%, window=${UNDERUTIL_WINDOW_S}s)…"

if [[ ! -f "$ALERT_FILE" ]]; then
    {
        echo "# Watchdog alerts"
        echo
        echo "Append-only log of GPU underutilization windows during saturating phases. Pushed to git on every alert."
        echo
        echo "| Timestamp (UTC) | Phase | Util % | Window (s) | Note |"
        echo "|---|---|---|---|---|"
    } > "$ALERT_FILE"
fi

last_alert_phase=""
last_alert_ts=0
underutil_start=0
last_util=100

while true; do
    cur_phase="(idle)"
    if [[ -f "$RUNPOD_DIR/CURRENT_PHASE.txt" ]]; then
        cur_phase=$(cat "$RUNPOD_DIR/CURRENT_PHASE.txt" 2>/dev/null || echo "?")
    fi

    if ! is_saturating_phase "$cur_phase"; then
        underutil_start=0
        sleep "$SAMPLE_PERIOD_S"
        continue
    fi

    util=$(nvidia-smi --query-gpu=utilization.gpu --format=csv,noheader,nounits 2>/dev/null | head -1 | tr -d '[:space:]')
    util=${util:-0}
    last_util=$util

    if (( util < UTIL_THRESHOLD_PCT )); then
        if (( underutil_start == 0 )); then
            underutil_start=$(date -u +%s)
        fi
        elapsed=$(( $(date -u +%s) - underutil_start ))
        if (( elapsed >= UNDERUTIL_WINDOW_S )); then
            now=$(date -u +%s)
            # Don't spam: at most one alert per 30 min per phase.
            if [[ "$cur_phase" != "$last_alert_phase" ]] || (( now - last_alert_ts > 1800 )); then
                printf '| %s | %s | %d | %d | sustained < %d%% util |\n' \
                    "$(ts)" "$cur_phase" "$util" "$elapsed" "$UTIL_THRESHOLD_PCT" >> "$ALERT_FILE"
                log "ALERT: phase=$cur_phase util=${util}%% sustained ${elapsed}s; pushing to git."
                git -c user.email=architects@zer0pa.ai -c user.name="Zer0pa Pod Executor" \
                    add "$ALERT_FILE" 2>/dev/null || true
                if ! git diff --cached --quiet; then
                    git -c user.email=architects@zer0pa.ai -c user.name="Zer0pa Pod Executor" \
                        commit -m "Watchdog alert: $cur_phase underutilized" >/dev/null 2>&1 || true
                    git push origin HEAD:main >/dev/null 2>&1 || true
                fi
                last_alert_phase="$cur_phase"
                last_alert_ts=$now
                # Reset window so we don't immediately re-fire.
                underutil_start=0
            fi
        fi
    else
        underutil_start=0
    fi

    sleep "$SAMPLE_PERIOD_S"
done
