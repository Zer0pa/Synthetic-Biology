#!/usr/bin/env bash
# Proactive disk + ckpt watchdog. Runs every 60s.
# - / overlay > 85%: clean my cache/log artefacts
# - /workspace mfs probe: if EDQUOT, rotate ckpts AND clean caches
# - PROACTIVE: keep only latest 2 ckpts always (prevents EDQUOT during save)
set -uo pipefail
LOG=/workspace/Synthetic-Biology/audit/runtime/runpod/disk_watchdog.log
CKPT_DIR=/workspace/checkpoints/cekm_wave4
ts() { date -u +"%Y-%m-%dT%H:%M:%SZ"; }
log() { printf '[disk_watchdog %s] %s\n' "$(ts)" "$*" | tee -a "$LOG"; }
log "starting (proactive ckpt rotation: keep latest 2 + step 1500 baseline)"
while true; do
    # /overlay cleanup
    used_root=$(df / 2>/dev/null | awk 'NR==2 {gsub(/%/,"",$5); print $5}')
    used_root=${used_root:-0}
    if (( used_root > 85 )); then
        log "/ overlay ${used_root}% — cleaning my caches"
        apt-get clean 2>/dev/null || true
        rm -rf /root/.cache/pip /root/.cache/equilibrator 2>/dev/null
        rm -rf /var/log/*.log.[0-9]* /var/log/*.log.gz 2>/dev/null
        used_after=$(df / 2>/dev/null | awk 'NR==2 {gsub(/%/,"",$5); print $5}')
        log "  / now ${used_after}%"
    fi
    # PROACTIVE ckpt rotation: keep latest 2 + step 1500 (proven baseline)
    if [[ -d "$CKPT_DIR" ]]; then
        # All ckpts sorted by mtime (newest first)
        all_pts=( $(ls -t "$CKPT_DIR"/ckpt_step*.pt 2>/dev/null) )
        n=${#all_pts[@]}
        if (( n > 3 )); then
            # Keep newest 2; explicitly preserve step 1500 baseline if present
            for ((i=2; i<n; i++)); do
                f="${all_pts[$i]}"
                base=$(basename "$f" .pt)
                # Preserve step 1500 (the proven-good baseline ckpt)
                if [[ "$base" == "ckpt_step00001500" ]]; then
                    continue
                fi
                rm -f "$f" "${f%.pt}.meta.json"
                log "rotated out $base"
            done
        fi
    fi
    # /workspace quota probe
    PROBE=/workspace/Synthetic-Biology/audit/runtime/runpod/.quota_probe
    if ! echo q > "$PROBE" 2>/dev/null; then
        log "ALERT /workspace mfs EDQUOT — emergency cleanup"
        rm -rf /workspace/Synthetic-Biology/audit/runtime/runpod/cekm_train_attempt_*.log 2>/dev/null
        rm -f /workspace/Synthetic-Biology/audit/runtime/runpod/wave4_attempt_[2-9]*.yaml 2>/dev/null
        # Even more aggressive: keep only 1 ckpt
        ls -t "$CKPT_DIR"/ckpt_step*.pt 2>/dev/null | tail -n +2 | xargs -r rm -f
        ls -t "$CKPT_DIR"/ckpt_step*.meta.json 2>/dev/null | tail -n +2 | xargs -r rm -f
        if echo q > "$PROBE" 2>/dev/null; then log "  /workspace recovered"; else log "  STILL EDQUOT after cleanup"; fi
    fi
    rm -f "$PROBE" 2>/dev/null
    sleep 60
done
