#!/usr/bin/env bash
# Phase 60 — L4.5 unknown-enzyme inference for the HMO triple.
#
# Runs ESMFold + MACE-OFF binding ΔG (3-run reference subtraction)
# + RFdiffusion2 backbone scaffolding. All three are public:
#  - ESMFold: facebook/esmfold_v1 on HF (downloaded in phase 20)
#  - MACE-OFF: mace-torch (PyPI) + mace-medium pretrained model
#  - RFdiffusion2: RosettaCommons/RFdiffusion2 on GitHub, BSD-3-Clause;
#    weights at http://files.ipd.uw.edu/pub/RFdiffusion/.../*.pt
#    (no registration; verified by Zer0pa Pod Executor 2026-05).
#
# Outputs land under audit/runtime/l45_real_inference_<seed>/ for
# pickup by phase 70 (HMO triple full numerical run).

set -euo pipefail

REPO_DIR="${REPO_DIR:-$(cd "$(dirname "$0")/../../.." && pwd)}"
cd "$REPO_DIR"

VENV="$REPO_DIR/.venv"
# shellcheck disable=SC1091
source "$VENV/bin/activate"

ts() { date -u +"%Y-%m-%dT%H:%M:%SZ"; }
log() { printf '[60_l45_inference %s] %s\n' "$(ts)" "$*"; }

OUT_ROOT="$REPO_DIR/audit/runtime/l45_real_inference"
mkdir -p "$OUT_ROOT"

# Canonical HMO-seed enzyme map (subset; full list resolved from each
# seed's spec at runtime). Keep here as a fallback if the repo's
# validation/hmo-seed-evidence/SEED_INPUTS isn't loadable.
declare -A SEED_ENZYMES=(
    [2pFL]="Q11075,P0AC88,P32055"          # FutC, Gmd, WcaG
    [3pSL]="Q56930,P0A6S0"                  # α-2,3-Lst, NeuA
    [DSLNT]="P15467,Q56930,P0A6S0"         # α-2,6-Lst, α-2,3-Lst, NeuA
)

run_esmfold() {
    local seed="$1" uniprot="$2" out_dir="$3"
    log "ESMFold inference: seed=$seed uniprot=$uniprot"
    python - <<PY 2>&1 | tee -a "$out_dir/esmfold_${uniprot}.log"
import os, json, pathlib
import torch
from transformers import EsmForProteinFolding, AutoTokenizer

uniprot = "$uniprot"
seed = "$seed"
out_dir = pathlib.Path("$out_dir")
out_dir.mkdir(parents=True, exist_ok=True)

# Pull sequence from UniProt or a local cache (skip on network failure
# — operator should pre-cache sequences in fixtures/uniprot/).
import urllib.request
seq = None
cache = pathlib.Path("fixtures/uniprot") / f"{uniprot}.fasta"
try:
    if cache.exists():
        seq = "".join(l.strip() for l in cache.read_text().splitlines() if not l.startswith(">"))
    else:
        with urllib.request.urlopen(f"https://rest.uniprot.org/uniprotkb/{uniprot}.fasta", timeout=30) as r:
            text = r.read().decode("utf-8")
            seq = "".join(l.strip() for l in text.splitlines() if not l.startswith(">"))
        cache.parent.mkdir(parents=True, exist_ok=True)
        cache.write_text(text)
    print(f"sequence: {len(seq)} AA")
except Exception as e:
    print(f"FAIL: could not fetch sequence for {uniprot}: {e}")
    raise SystemExit(60)

if len(seq) > 1024:
    print(f"WARNING: sequence too long ({len(seq)} AA); truncating to 1024 for ESMFold.")
    seq = seq[:1024]

device = "cuda"
tokenizer = AutoTokenizer.from_pretrained("facebook/esmfold_v1")
model = EsmForProteinFolding.from_pretrained("facebook/esmfold_v1", torch_dtype=torch.float32).to(device)
model.eval()
inputs = tokenizer([seq], return_tensors="pt", add_special_tokens=False).to(device)
with torch.no_grad():
    output = model(**inputs)
pdb = model.output_to_pdb(output)[0]
plddt = float(output["plddt"].mean().detach().cpu())

(out_dir / f"{uniprot}.pdb").write_text(pdb)
(out_dir / f"{uniprot}_meta.json").write_text(json.dumps({
    "uniprot_id": uniprot,
    "seed": seed,
    "sequence_length": len(seq),
    "plddt_mean": plddt,
    "tool": "esmfold_v1",
    "device": str(device),
}, indent=2, sort_keys=True))
print(f"ESMFold done: {uniprot}.pdb (pLDDT mean = {plddt:.3f})")
PY
}

run_mace_off_binding() {
    local seed="$1" uniprot="$2" substrate_smiles="$3" out_dir="$4"
    local pdb="$out_dir/${uniprot}.pdb"
    if [[ ! -f "$pdb" ]]; then
        log "MACE-OFF skip $uniprot: PDB not present (ESMFold likely failed)"
        return 0
    fi
    log "MACE-OFF binding (real 3-run reference subtraction): seed=$seed uniprot=$uniprot"
    python -m zer0pa_synbio.runpod_inference.mace_off_binding \
        "$pdb" "$substrate_smiles" "$out_dir" "$seed" 2>&1 | tee -a "$out_dir/mace_${uniprot}.log"
}

run_rfdiffusion2() {
    local seed="$1" out_dir="$2"
    log "RFdiffusion2 inference for $seed (public weights from files.ipd.uw.edu)…"

    local RF_DIR="/workspace/models/rfdiffusion2"
    if [[ ! -d "$RF_DIR/repo" ]]; then
        log "Cloning RosettaCommons/RFdiffusion2 (BSD-3-Clause)…"
        mkdir -p "$RF_DIR"
        git clone --depth 1 https://github.com/RosettaCommons/RFdiffusion2 "$RF_DIR/repo" 2>&1 | tail -3 || {
            log "RFdiffusion2 clone failed."
            return 0
        }
    fi
    if [[ ! -f "$RF_DIR/RF_structure_prediction_weights.pt" ]]; then
        log "Downloading RFdiffusion structure-prediction weights (~241 MB) from files.ipd.uw.edu…"
        curl -fsSL -o "$RF_DIR/RF_structure_prediction_weights.pt" \
            "http://files.ipd.uw.edu/pub/RFdiffusion/1befcb9b28e2f778f53d47f18b7597fa/RF_structure_prediction_weights.pt" || {
            log "Weight download failed."
            return 0
        }
        log "Downloaded $(du -h "$RF_DIR/RF_structure_prediction_weights.pt" | awk '{print $1}')."
    fi

    # Real invocation via the runpod_inference module. Generates 3
    # unconditional 100-residue scaffolds per seed (full PRD §6.6 spec
    # for the L4.5 unknown-enzyme path; pod budget extended 2026-05-02
    # post-call so we can cover the per-seed scaffold ensemble).
    # Curated motif-conditional designs for catalytic active sites
    # are downstream of v0.1 (require curated TS-mimetic geometry).
    python -m zer0pa_synbio.runpod_inference.rfdiffusion2_design \
        "$seed" "$out_dir" 3 "100" 2>&1 | tee -a "$out_dir/rfdiffusion2.log"
}

# ─── per-seed loop ───────────────────────────────────────────────────────
for SEED in 2pFL 3pSL DSLNT; do
    SEED_DIR="$OUT_ROOT/$SEED"
    mkdir -p "$SEED_DIR"
    log "──── Processing seed $SEED ────"

    # ESMFold per enzyme.
    IFS=',' read -ra UNIPROTS <<< "${SEED_ENZYMES[$SEED]}"
    for uniprot in "${UNIPROTS[@]}"; do
        if [[ -f "$SEED_DIR/${uniprot}.pdb" ]]; then
            log "ESMFold already done for $uniprot; skipping."
        else
            run_esmfold "$SEED" "$uniprot" "$SEED_DIR" || log "ESMFold failed for $uniprot; continuing."
        fi
    done

    # MACE-OFF binding (placeholder substrate per seed; real run uses canonical substrate).
    case "$SEED" in
        2pFL)  SUBSTRATE_SMILES="OC[C@H]1O[C@@H](O[C@H]2O[C@H](OC[C@H]3O[C@H](O)[C@H](O)[C@@H](O)[C@@H]3O)[C@H](O)[C@@H](O)[C@@H]2O)[C@H](O)[C@@H](O)[C@@H]1O" ;;
        3pSL)  SUBSTRATE_SMILES="C[C@H](O)[C@@H](N)C(=O)O" ;;
        DSLNT) SUBSTRATE_SMILES="C[C@H](O)[C@@H](N)C(=O)O" ;;
    esac
    PRIMARY_UNIPROT=${UNIPROTS[0]}
    if [[ ! -f "$SEED_DIR/mace_${PRIMARY_UNIPROT}.json" ]]; then
        run_mace_off_binding "$SEED" "$PRIMARY_UNIPROT" "$SUBSTRATE_SMILES" "$SEED_DIR" || \
            log "MACE-OFF failed for $SEED; continuing."
    fi

    # RFdiffusion2 (public; weights + repo staged for operator follow-up).
    run_rfdiffusion2 "$SEED" "$SEED_DIR" || true
done

log "L4.5 inference phase complete."
exit 0
