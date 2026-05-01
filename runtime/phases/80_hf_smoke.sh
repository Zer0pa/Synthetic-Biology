#!/usr/bin/env bash
# Phase 80 — HF smoke push (proves token still works on this pod).
set -euo pipefail
. "$RUN_ROOT/env.sh"

python <<'PY'
import io, sys
from pathlib import Path
from huggingface_hub import HfApi, whoami

token_path = Path.home() / ".cache" / "huggingface" / "token"
hf_home_token = Path("/workspace/synbio-run/cache/huggingface/token")
token = None
for p in (token_path, hf_home_token):
    if p.exists():
        token = p.read_text().strip(); break
import os
if not token:
    token = os.environ.get("HF_TOKEN")
if not token:
    print("NO HF TOKEN — skip push (not a hard fail)"); sys.exit(0)

api = HfApi(token=token)
me = whoami(token=token)
print(f"Authenticated as: {me['name']}")
if me['name'] != 'Architect-Prime':
    print(f"Token belongs to {me['name']}, not Architect-Prime; skipping per PRD §14.4")
    sys.exit(0)

repo_id = "Architect-Prime/synbio-runpod-bootstrap-v0.1"
api.create_repo(repo_id=repo_id, repo_type="dataset", private=True, exist_ok=True)
readme = b"""# synbio-runpod-bootstrap-v0.1

Smoke from the Runpod H100 pod confirming HF Architect-Prime auth still works.
Canonical: https://github.com/Zer0pa/Synthetic-Biology
"""
api.upload_file(path_or_fileobj=io.BytesIO(readme), path_in_repo="README.md",
                repo_id=repo_id, repo_type="dataset",
                commit_message="Runpod bootstrap smoke")
print(f"OK: smoke-pushed to {repo_id}")
PY
echo "OK: HF smoke done."
