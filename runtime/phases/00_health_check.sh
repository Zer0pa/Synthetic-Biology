#!/usr/bin/env bash
# Phase 00 — pod + Python + GPU sanity
set -euo pipefail

. "$RUN_ROOT/env.sh"

echo "==== python ===="
python --version
python -c "from zer0pa_synbio.boundary import BOUNDARY_SHA256; print('boundary sha256:', BOUNDARY_SHA256)"

echo "==== torch + cuda ===="
python -c "
import torch
assert torch.cuda.is_available(), 'CUDA not available'
print(f'torch={torch.__version__}')
print(f'cuda_version={torch.version.cuda}')
print(f'device={torch.cuda.get_device_name(0)}')
print(f'vram={torch.cuda.get_device_properties(0).total_memory/1e9:.1f} GB')
print(f'capability={torch.cuda.get_device_capability(0)}')
"

echo "==== falsifier registry ===="
python -c "
from zer0pa_synbio.falsifiers import REGISTRY
from zer0pa_synbio.falsifiers.checks import CHECKS, assert_complete_coverage
assert_complete_coverage()
print(f'registry={len(REGISTRY)} falsifiers; checks={len(CHECKS)} implementations')
"

echo "==== iML1515 ===="
ls -lh "$RUN_ROOT/repo/fixtures/gem/iML1515.json"
python -c "
import cobra
m = cobra.io.load_json_model('$RUN_ROOT/repo/fixtures/gem/iML1515.json')
print(f'model={m.id}; reactions={len(m.reactions)}; metabolites={len(m.metabolites)}')
print(f'biomass FBA={m.optimize().objective_value:.4f} /h')
"

echo "==== eQuilibrator cache ===="
python -c "
import os
import equilibrator_api as eq
print('Initialising ComponentContribution (downloads ~1.3 GB cache on first use)...')
cc = eq.ComponentContribution()
r = cc.parse_reaction_formula('bigg.metabolite:g6p = bigg.metabolite:f6p')
print(f'PGI ΔrG\\' = {cc.standard_dg_prime(r)}')
"

echo "OK: health check passed."
