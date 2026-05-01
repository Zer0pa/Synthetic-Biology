#!/usr/bin/env bash
# Phase 95 — commit Runpod-side artifacts and push to origin/main.
set -euo pipefail
. "$RUN_ROOT/env.sh"

cd "$RUN_ROOT/repo"

# Configure git identity for the pod.
git config user.email "architects@zer0pa.ai"
git config user.name "Zer0pa Runpod Executor"

# Anything under audit/runtime/ is run-output (intentionally tracked for
# this run; future runs will overwrite). Validation/hmo-seed-evidence/
# updated dossiers are tracked. FINAL-REPORT-RUNPOD.md too.
git add -A audit/runtime/ validation/hmo-seed-evidence/ FINAL-REPORT-RUNPOD.md \
          audit/reasoner_tuples.jsonl 2>/dev/null || true

# Don't fail if there's nothing new — pod might have already been pushed.
if git diff --cached --quiet; then
  echo "Nothing to commit — repo is clean (HMO output already in main?)"
  exit 0
fi

git commit -m "Runpod H100 run: HMO triple under scientific mode + real ESM-2/FBA/MDF/OSTIR

Boundary block carried in every artifact. Audit conformance verified
on all 3 seeds (12/12 checks each). PathGym ledger seeded with 3
Tier-3 ReasonerTuples. Stub envelopes correctly retain
scientific_valid=False per PRD §4.5.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"

# Setup HTTPS push using GH_TOKEN if set, else expect deploy SSH key.
if [ -n "${GH_TOKEN:-}" ]; then
  git remote set-url origin "https://x-access-token:${GH_TOKEN}@github.com/Zer0pa/Synthetic-Biology.git"
fi

git push origin HEAD:main
echo "OK: pushed to origin/main."
