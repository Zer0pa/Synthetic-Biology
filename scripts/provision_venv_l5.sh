#!/usr/bin/env bash
# Provision the Python 3.11 sub-venv used by L5MFMOAdapter for real
# BoTorch + GPyTorch + qLogNEHVI computation.
#
# Required because PyTorch dropped macOS x86_64 wheels at Python 3.13;
# the rest of the synbio repo runs on Python 3.13 / macOS x86_64.
#
# This venv is NOT tracked in git (.venv-l5/ is gitignored). Re-run on
# any new clone or worktree where you want the real BoTorch path
# instead of the scipy stub fallback.
#
# Per HANDOFF-CPU-CONTINUATION.md item A.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
VENV_DIR="${REPO_ROOT}/.venv-l5"
PY311=${PY311:-/usr/local/bin/python3.11}

if [[ ! -x "${PY311}" ]]; then
    echo "ERROR: Python 3.11 not found at ${PY311}." >&2
    echo "       Override with PY311=/path/to/python3.11" >&2
    exit 1
fi

if [[ -d "${VENV_DIR}" ]]; then
    echo "Reusing existing ${VENV_DIR}"
else
    echo "Creating ${VENV_DIR} with ${PY311}"
    "${PY311}" -m venv "${VENV_DIR}"
fi

# shellcheck disable=SC1091
source "${VENV_DIR}/bin/activate"

pip install --quiet --upgrade pip
pip install --quiet "torch==2.2.2"
pip install --quiet "numpy<2"
pip install --quiet "botorch==0.17.2" "gpytorch==1.15.2"

python - <<'PY'
import torch, numpy, botorch, gpytorch
print(f"torch    {torch.__version__}")
print(f"numpy    {numpy.__version__}")
print(f"botorch  {botorch.__version__}")
print(f"gpytorch {gpytorch.__version__}")
PY

echo "Done. .venv-l5 ready. L5MFMOAdapter will now take the real BoTorch path."
