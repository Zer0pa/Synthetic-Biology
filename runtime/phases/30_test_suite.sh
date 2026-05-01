#!/usr/bin/env bash
# Phase 30 — full pytest suite
set -euo pipefail
. "$RUN_ROOT/env.sh"

python -m pytest tests/ -q --tb=line --maxfail=5
echo "OK: full suite passed."
