#!/usr/bin/env bash
# Phase 90 — write FINAL-REPORT-RUNPOD.md from STATUS.txt + envelope counts.
set -euo pipefail
. "$RUN_ROOT/env.sh"

OUT="$RUN_ROOT/repo/FINAL-REPORT-RUNPOD.md"
STATUS="$RUN_ROOT/state/STATUS.txt"

# Counts.
ENV_2PFL=$(wc -l < "$RUN_ROOT/repo/audit/runtime/hmo_seed_2pFL/envelopes.jsonl" 2>/dev/null || echo 0)
ENV_3PSL=$(wc -l < "$RUN_ROOT/repo/audit/runtime/hmo_seed_3pSL/envelopes.jsonl" 2>/dev/null || echo 0)
ENV_DSLNT=$(wc -l < "$RUN_ROOT/repo/audit/runtime/hmo_seed_DSLNT/envelopes.jsonl" 2>/dev/null || echo 0)
DISAGREE_TOTAL=$(cat "$RUN_ROOT/repo/audit/runtime/"*/disagreement.jsonl 2>/dev/null | wc -l)
EARLY_WARNING_TOTAL=$(cat "$RUN_ROOT/repo/audit/runtime/"*/early_warning.jsonl 2>/dev/null | wc -l)
PATHGYM_SEEDS=$(wc -l < "$RUN_ROOT/repo/audit/reasoner_tuples.jsonl" 2>/dev/null || echo 0)

cat > "$OUT" <<EOF
# FINAL-REPORT-RUNPOD — Synbio H100 SXM run

**Pod:** 429xv4r3wm66q9 · 1× H100 SXM5 80GB · 128 vCPU · 2 TiB RAM
**Date:** $(date -Iseconds)
**Repo HEAD:** $(cd "$RUN_ROOT/repo" && git log -1 --oneline)
**Boundary:** Research infrastructure for in silico synthetic biology / metabolic pathway engineering. Outputs are research artifacts — predicted pathways, predicted KPIs, candidate genetic modification specifications. No regulatory certification claims. No clinical or human-subject use. No environmental release of GMOs. No biocontainment-level claims (the pipeline does not commission BSL-2/3 work). No human gene drive or eugenic application. Defence / weapons / dual-use bio applications excluded under operator policy.

## Counts (this run)

| Artifact | Count |
|---|---|
| 2'-FL envelope chain length | $ENV_2PFL |
| 3'-SL envelope chain length | $ENV_3PSL |
| DSLNT envelope chain length | $ENV_DSLNT |
| Cross-model disagreement records | $DISAGREE_TOTAL |
| Early-warning signals | $EARLY_WARNING_TOTAL |
| PathGym ReasonerTuple seeds | $PATHGYM_SEEDS |

## Phase ledger

\`\`\`
$(cat "$STATUS" 2>/dev/null | tail -50)
\`\`\`

## Test suite

\`\`\`
$(cat "$RUN_ROOT/logs/30_test_suite.log" 2>/dev/null | tail -5)
\`\`\`

## Audit conformance (per Audit-Trail Spec v0.1 §10)

\`\`\`
$(cat "$RUN_ROOT/logs/70_audit_verify.log" 2>/dev/null | tail -40)
\`\`\`

## Compute saturation

GPU was used by phases: 10_pull_models, 50_esm2_real_l1, 60_hmo_*. CPU-bound
phases (LIRC, audit verify, dossier emission, BoTorch fits) ran in parallel
where the orchestrator allowed.

EOF

echo "OK: $OUT written ($(wc -l < "$OUT") lines)"
