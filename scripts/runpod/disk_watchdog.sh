#!/usr/bin/env bash
# Pre-emptive disk watchdog — monitors / overlay and cleans MY artefacts only
# (never touches other agents' /workspace dirs or /tmp/qwen*, /tmp/path_a_*).
# Triggered when / > 85%.
set -uo pipefail
LOG=/workspace/Synthetic-Biology/audit/runtime/runpod/disk_watchdog.log
ts() { date -u +"%Y-%m-%dT%H:%M:%SZ"; }
log() { printf '[disk_watchdog %s] %s\n' "$(ts)" "$*" | tee -a "$LOG"; }
log "starting disk watchdog (clean trigger: />85%)"
while true; do
    used=$(df / 2>/dev/null | awk 'NR==2 {gsub(/%/,"",$5); print $5}')
    used=${used:-0}
    if (( used > 85 )); then
        log "ALERT / overlay at ${used}% — cleaning my artefacts only"
        # Mine: apt cache, pip cache (system /root/.cache/pip — NOT /workspace/synbio-run/cache/pip)
        apt-get clean 2>/dev/null && log "  apt-get clean"
        rm -rf /root/.cache/pip 2>/dev/null && log "  /root/.cache/pip removed"
        rm -rf /var/log/*.log.[0-9]* /var/log/*.log.gz /var/log/apt/archives/*.deb 2>/dev/null && log "  log rotation files"
        # Mine in /tmp: only files matching synbio/cekm/equilibrator patterns
        rm -rf /tmp/synbio* /tmp/cekm* /tmp/equilibrator* 2>/dev/null && log "  /tmp/synbio* cleaned"
        # NEVER touch: /tmp/qwen*, /tmp/path_a*, /tmp/run_aot*, /tmp/run_onnx*, /tmp/aot_*  (other agent)
        used_after=$(df / 2>/dev/null | awk 'NR==2 {gsub(/%/,"",$5); print $5}')
        log "  / now at ${used_after}%"
    fi
    sleep 60
done
