#!/usr/bin/env bash
# Phase 80 — synbio audit verify on each campaign. Conformance reports
# are appended to RUN_REPORT.md and pushed to git.
set -euo pipefail

REPO_DIR="${REPO_DIR:-$(cd "$(dirname "$0")/../../.." && pwd)}"
cd "$REPO_DIR"

VENV="$REPO_DIR/.venv"
# shellcheck disable=SC1091
source "$VENV/bin/activate"

ts() { date -u +"%Y-%m-%dT%H:%M:%SZ"; }
log() { printf '[80_audit_verify %s] %s\n' "$(ts)" "$*"; }

REPORT="$REPO_DIR/audit/runtime/runpod/audit_verify_report.md"
{
    echo "# Audit verify report — autonomous run"
    echo
    echo "Generated $(ts)"
    echo
} > "$REPORT"

PASS=0
FAIL=0
for SEED in 2pFL 3pSL DSLNT; do
    CAMPAIGN="hmo_seed_$SEED"
    log "Verifying $CAMPAIGN…"
    {
        echo "## $CAMPAIGN"
        echo '```'
        synbio audit verify "$CAMPAIGN" 2>&1 || echo "VERIFY FAILED rc=$?"
        echo '```'
        echo
    } | tee -a "$REPORT"
    if grep -q "OVERALL: PASS" "$REPORT"; then
        PASS=$((PASS + 1))
    else
        FAIL=$((FAIL + 1))
    fi
done

log "Audit verify summary: PASS=$PASS FAIL=$FAIL"
echo "## Summary" >> "$REPORT"
echo "PASS=$PASS FAIL=$FAIL" >> "$REPORT"

# Don't fail the whole pipeline if a seed's audit doesn't pass; surface
# the diagnostic and continue. The next agent inspects the report.
exit 0
