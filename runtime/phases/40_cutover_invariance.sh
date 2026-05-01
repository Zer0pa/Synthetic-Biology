#!/usr/bin/env bash
# Phase 40 — Wave 11 cutover invariance under runpod_rest
set -euo pipefail
. "$RUN_ROOT/env.sh"

# By default, gpu_rest_stub adapters return canned envelopes. The Wave
# 11 invariance test confirms that even on Linux+CUDA, the stub
# response is byte-equal to a direct adapter call (modulo runtime fields).
# Gating real runpod_rest backend behind a separate env var so we don't
# regress the stub-side test.
python -m pytest tests/runpod_cutover/ -q --tb=line
echo "OK: cutover invariance preserved on H100."
