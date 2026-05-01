#!/usr/bin/env bash
# Phase 60 — HMO seed in scientific mode (real layers where adapters support them).
set -euo pipefail
. "$RUN_ROOT/env.sh"

SEED="${1:?usage: 60_hmo_seed.sh {2pFL|3pSL|DSLNT}}"
echo "Running HMO seed: $SEED (scientific mode)"
python validation/hmo-seed-evidence/run_seed.py --seed "$SEED" 2>&1 | tail -10
echo "OK: $SEED dossier emitted."
