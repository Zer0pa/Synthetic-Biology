#!/usr/bin/env bash
# Phase 60 — HMO seed in scientific mode (real layers where adapters support them).
set -euo pipefail
. "$RUN_ROOT/env.sh"

# NB: do NOT use ${1:?usage...{...}} — bash matches the FIRST `}` to close
# the parameter expansion, leaving the second `}` appended to the value.
SEED="${1:-}"
if [ -z "$SEED" ]; then
  echo "usage: 60_hmo_seed.sh 2pFL|3pSL|DSLNT" >&2
  exit 2
fi
echo "Running HMO seed: $SEED (scientific mode)"
python validation/hmo-seed-evidence/run_seed.py --seed "$SEED" 2>&1 | tail -10
echo "OK: $SEED dossier emitted."
