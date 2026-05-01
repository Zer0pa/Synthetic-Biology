#!/usr/bin/env bash
# Phase 210 — CEKM REAL training on H100 (synthetic corpus from smoke pipeline).
#
# The shipped CLI passes empty slices; here we assemble the synthetic corpus
# inline (100 positives + 207 negatives) and call train() directly so the
# H100 actually does forward+backward passes for 2000 steps.
set -euo pipefail
. "$RUN_ROOT/env.sh"

mkdir -p "$RUN_ROOT/audit/runtime/cekm_train_h100/checkpoints"

python <<'PY'
"""Real CEKM training on H100 — synthetic corpus + real model."""
import sys
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)

from zer0pa_synbio.cekm import KineticsRow, CorpusSlice
from zer0pa_synbio.cekm.train import TrainingConfig, train

print("=== assembling synthetic corpus ===")
brenda = CorpusSlice(
    source="brenda",
    license_class="A",
    rows=[
        KineticsRow(
            enzyme_uniprot_id=f"P{i:05d}",
            substrate_inchi_key=f"SUBSTRATE-{i:03d}",
            organism_taxonomy_id=562,
            temperature_c=37.0,
            ph=7.0,
            kcat_per_s=10.0 + i * 0.3,
            km_mm=0.1 + i * 0.05,
            source="brenda",
            citation="(synthetic for H100 training)",
        )
        for i in range(50)
    ],
)
enzyextract = CorpusSlice(
    source="enzyextract",
    license_class="A",
    rows=[
        KineticsRow(
            enzyme_uniprot_id=f"E{i:05d}",
            substrate_inchi_key=f"DARK-MATTER-{i:03d}",
            organism_taxonomy_id=83333,
            temperature_c=30.0,
            ph=6.5,
            kcat_per_s=5.0 + i * 0.2,
            km_mm=0.5 + i * 0.1,
            source="enzyextract",
            citation="(synthetic enzyextract dark-matter for H100 training)",
        )
        for i in range(50)
    ],
)
slices = [brenda, enzyextract]
print(f"  brenda rows: {len(brenda.rows)}, enzyextract rows: {len(enzyextract.rows)}")

print("=== train() — 2000 steps on H100 ===")
cfg = TrainingConfig(
    campaign_id="cekm_train_h100",
    seed=42,
    use_bf16=False,
    batch_size=4,
    gradient_accumulation_steps=2,
    learning_rate=1e-4,
    warmup_steps=50,
    max_steps=2000,
    eval_every_steps=200,
    checkpoint_every_steps=500,
    checkpoint_dir="/workspace/synbio-run/repo/audit/runtime/cekm_train_h100/checkpoints",
    holdout_fraction=0.20,
    enzyextract_holdout_full=False,
)
summary = train(cfg, slices, resume=False)

import json
print("=== summary ===")
print(json.dumps(summary, indent=2))

assert summary["steps_completed"] >= 100, f"too few steps: {summary['steps_completed']}"
assert summary["corpus_total"] > 0, f"empty corpus"
assert summary["in_corpus"] > 0, f"no in-corpus rows"
print(
    f"OK: real CEKM training ran {summary['steps_completed']} steps on "
    f"{summary['in_corpus']} positives + {summary['negatives']} adversarial negatives."
)
PY
echo "OK: CEKM training phase finished."
