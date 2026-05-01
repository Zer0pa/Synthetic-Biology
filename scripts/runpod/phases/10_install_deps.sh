#!/usr/bin/env bash
# Phase 10 — install GPU dependency stack. Idempotent: re-running is a no-op.
set -euo pipefail

REPO_DIR="${REPO_DIR:-$(cd "$(dirname "$0")/../../.." && pwd)}"
cd "$REPO_DIR"

ts() { date -u +"%Y-%m-%dT%H:%M:%SZ"; }
log() { printf '[10_install_deps %s] %s\n' "$(ts)" "$*"; }

VENV="$REPO_DIR/.venv"
if [[ ! -d "$VENV" ]]; then
    log "Creating .venv with system Python…"
    python3 -m venv "$VENV"
fi
# shellcheck disable=SC1091
source "$VENV/bin/activate"
log "Active Python: $(which python) ($(python --version))"

pip install --quiet --upgrade pip wheel setuptools

# ─── Editable install of synbio + its declared extras ─────────────────────
log "Installing zer0pa-synbio editable + extras…"
pip install --quiet -e ".[all,mfmo,dev]" 2>&1 | tail -5 || {
    log "Editable install with extras failed; falling back to base install."
    pip install --quiet -e .
}

# ─── Torch + CUDA (must match pod's CUDA driver) ─────────────────────────
if ! python -c "import torch; assert torch.cuda.is_available()" 2>/dev/null; then
    log "torch with CUDA not yet usable; installing torch wheel for CUDA 12.1…"
    # Pin a known-good wheel for stability; bump on next pod cycle if needed.
    pip install --quiet torch==2.4.1 --index-url https://download.pytorch.org/whl/cu121 || {
        log "CUDA 12.1 wheel install failed; trying default torch wheel…"
        pip install --quiet torch
    }
fi
python -c "import torch; print('torch:', torch.__version__, 'cuda:', torch.cuda.is_available(), 'device:', torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'NONE')"

# ─── Transformers + ESMFold deps ─────────────────────────────────────────
pip install --quiet "transformers>=4.42" accelerate safetensors

# ─── flash-attn-2 (optional — speeds up attention; build can take 5–10 min) ─
if ! python -c "import flash_attn" 2>/dev/null; then
    log "Installing flash-attn 2 (build, ~5–10 min on H100)…"
    pip install --quiet flash-attn --no-build-isolation 2>&1 | tail -5 || {
        log "flash-attn install failed; will run without it (slower but functional)."
    }
fi

# ─── MACE-OFF for L4.5 binding ΔG ────────────────────────────────────────
if ! python -c "import mace" 2>/dev/null; then
    log "Installing mace-torch…"
    pip install --quiet mace-torch 2>&1 | tail -3 || log "mace-torch install failed; phase 60 may degrade."
fi

# ─── eQuilibrator-pathway (CEKM training references it; cache pre-warmed) ─
pip install --quiet equilibrator-pathway

# ─── ripser + persim for TDA ─────────────────────────────────────────────
pip install --quiet ripser persim

# ─── BoTorch (training side may not need; runtime L5 worker uses .venv-l5) ─
# We do NOT install botorch in this venv; the .venv-l5 split-venv pattern
# (Python 3.11) handles it. On the pod we have Python 3.10/3.11/3.12, so
# we *could* install it here — but keeping the split discipline lets the
# same code run on Mac and pod identically.

# ─── HF CLI ──────────────────────────────────────────────────────────────
pip install --quiet "huggingface_hub[cli]"

# ─── Verify all critical imports ─────────────────────────────────────────
python - <<'PY'
import importlib, sys
need = [
    "torch", "numpy", "scipy", "pandas",
    "transformers", "huggingface_hub",
    "rdkit", "selfies", "cobra",
    "equilibrator_api", "equilibrator_pathway",
    "ripser", "persim",
    "zer0pa_synbio",
]
fail = []
for m in need:
    try:
        importlib.import_module(m)
        print(f"  ok: {m}")
    except Exception as e:
        print(f"  FAIL: {m}: {e}")
        fail.append(m)
if fail:
    print(f"FATAL: {len(fail)} modules failed to import: {fail}", file=sys.stderr)
    sys.exit(20)
PY

log "Dependency install complete."
exit 0
