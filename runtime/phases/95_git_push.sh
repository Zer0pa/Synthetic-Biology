#!/usr/bin/env bash
# Phase 95 — produce artifact tarball for the Mac to rsync back + git push.
#
# The pod was bootstrapped via rsync (no .git/) because the Synthetic-Biology
# repo is INTERNAL on GitHub and the pod can't anonymously authenticate.
# Instead of duplicating auth on the pod, we tarball the run-output paths
# here; the Mac side rsyncs the tarball back and does the git commit + push
# under the operator's already-verified credentials.
set -euo pipefail
. "$RUN_ROOT/env.sh"

OUT_DIR="$RUN_ROOT/state"
TARBALL="$OUT_DIR/artifacts-$(date +%Y%m%dT%H%M%SZ).tar.gz"

cd "$RUN_ROOT/repo"
tar -czf "$TARBALL" \
    audit/runtime/ \
    audit/reasoner_tuples.jsonl \
    validation/hmo-seed-evidence/ \
    FINAL-REPORT-RUNPOD.md \
    2>/dev/null || true

ls -lh "$TARBALL"
echo "  paths included:"
tar -tzf "$TARBALL" | head -10
echo "  ..."
tar -tzf "$TARBALL" | wc -l
echo "  total entries"

# Symlink for predictable rsync target.
ln -snf "$TARBALL" "$OUT_DIR/artifacts-latest.tar.gz"

echo "OK: artifacts tarball at $TARBALL"
echo "    Mac-side rsync: rsync -avz -e 'ssh -i ~/.ssh/id_ed25519 -p 31031' \\"
echo "                    root@38.80.152.148:$OUT_DIR/artifacts-latest.tar.gz ./"
