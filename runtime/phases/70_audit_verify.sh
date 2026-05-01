#!/usr/bin/env bash
# Phase 70 — audit conformance verifier on all 3 HMO seeds.
set -euo pipefail
. "$RUN_ROOT/env.sh"

for s in 2pFL 3pSL DSLNT; do
  echo "=== hmo_seed_$s ==="
  python -m zer0pa_synbio.cli audit verify "hmo_seed_$s"
done
echo "OK: all 3 HMO seeds pass conformance."
