#!/usr/bin/env bash
# Phase 20 — confirm LIRC slice present
set -euo pipefail
. "$RUN_ROOT/env.sh"

if [ -f fixtures/lirc/2pfl_canonical.json ]; then
  echo "LIRC slice present: $(wc -l < fixtures/lirc/2pfl_canonical.json) lines"
else
  python -m zer0pa_synbio.adapters.l2_lirc.rhea_slice 2>&1 | tail -5 || \
    python -c "from zer0pa_synbio.adapters.l2_lirc.rhea_slice import build_2pfl_slice; build_2pfl_slice()"
fi
echo "OK: LIRC slice ready."
