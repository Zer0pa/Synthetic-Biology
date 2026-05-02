#!/usr/bin/env bash
# Phase 20 — stage CEKM corpora + model weights to local pod disk.
#
# Strategy: prefer HF dataset (Architect-Prime/synbio-cekm-corpus-v0.1)
# when available, fall back to public direct sources. BRENDA bulk
# requires registration; if neither HF dataset nor pre-downloaded TSV
# is present, we log a warning and continue without BRENDA (CEKM still
# trains on EnzyExtract + GotEnzymes2 + ProteinGym).

set -euo pipefail

REPO_DIR="${REPO_DIR:-$(cd "$(dirname "$0")/../../.." && pwd)}"
cd "$REPO_DIR"

VENV="$REPO_DIR/.venv"
# shellcheck disable=SC1091
source "$VENV/bin/activate"

ts() { date -u +"%Y-%m-%dT%H:%M:%SZ"; }
log() { printf '[20_stage_data %s] %s\n' "$(ts)" "$*"; }

DATA_ROOT="${DATA_ROOT:-/workspace/data}"
mkdir -p "$DATA_ROOT"/{brenda,enzyextract,gotenzymes2,proteingym}

# ─── HF dataset stager ──────────────────────────────────────────────────
HF_CORPUS_REPO="Architect-Prime/synbio-cekm-corpus-v0.1"
hf_dataset_exists=$(python -c "
from huggingface_hub import HfApi
import sys
try:
    HfApi().repo_info('$HF_CORPUS_REPO', repo_type='dataset')
    sys.stdout.write('1')
except Exception:
    sys.stdout.write('0')
")
if [[ "$hf_dataset_exists" == "1" ]]; then
    log "HF corpus dataset $HF_CORPUS_REPO found."
else
    log "HF corpus dataset $HF_CORPUS_REPO not found; will fall back to direct sources."
fi

download_from_hf_or_direct() {
    local source="$1" hf_path="$2" direct_url="$3" out_path="$4"
    if [[ -f "$out_path" ]]; then
        log "$source already at $out_path; skipping."
        return 0
    fi
    if [[ "$hf_dataset_exists" == "1" ]]; then
        log "Pulling $source from HF dataset…"
        # hf download places file at <local-dir>/<path-in-repo>; the
        # caller's $out_path already includes the source subdir, so we
        # must point --local-dir at $DATA_ROOT (one level up) so the
        # path-in-repo subdir lands as $out_path.
        if hf download "$HF_CORPUS_REPO" "$hf_path" --repo-type dataset \
            --local-dir "$DATA_ROOT" >/dev/null 2>&1; then
            [[ -f "$out_path" ]] && return 0
        fi
        log "HF dataset pull failed for $source; trying direct."
    fi
    if [[ -n "$direct_url" ]]; then
        log "Downloading $source from $direct_url…"
        curl -fsSL "$direct_url" -o "$out_path" || {
            log "Direct download failed for $source ($direct_url)."
            return 1
        }
    else
        log "No direct URL for $source; cannot stage."
        return 1
    fi
}

# ─── BRENDA (Class A; CC BY 4.0; bulk requires registration) ─────────────
BRENDA_TSV="$DATA_ROOT/brenda/brenda_data.tsv"
if [[ -f "$BRENDA_TSV" ]]; then
    log "BRENDA already present."
elif [[ "$hf_dataset_exists" == "1" ]]; then
    log "Pulling BRENDA from HF dataset…"
    hf download "$HF_CORPUS_REPO" "brenda/brenda_data.tsv" --repo-type dataset \
        --local-dir "$DATA_ROOT" >/dev/null 2>&1 || \
        log "WARNING: BRENDA not on HF dataset. CEKM will train without BRENDA core (EnzyExtract + GotEnzymes2 + ProteinGym only)."
else
    log "WARNING: BRENDA not pre-staged. Operator must run scripts/runpod/stage_corpora_to_hf.sh before next pod."
fi

# ─── EnzyExtract (Class A; MIT; ChemBioHTP/EnzyExtract; parquet) ─────────
ENZYEXTRACT_PARQUET="$DATA_ROOT/enzyextract/EnzyExtractDB_176463.parquet"
if [[ ! -f "$ENZYEXTRACT_PARQUET" ]]; then
    if [[ "$hf_dataset_exists" == "1" ]]; then
        log "Pulling EnzyExtract parquet from HF dataset…"
        hf download "$HF_CORPUS_REPO" "enzyextract/EnzyExtractDB_176463.parquet" --repo-type dataset \
            --local-dir "$DATA_ROOT" >/dev/null 2>&1
    fi
    if [[ ! -f "$ENZYEXTRACT_PARQUET" ]]; then
        log "Direct download EnzyExtract parquet from ChemBioHTP/EnzyExtract…"
        curl -fsSL "https://github.com/ChemBioHTP/EnzyExtract/raw/main/EnzyExtractDB/EnzyExtractDB_176463.parquet" \
            -o "$ENZYEXTRACT_PARQUET" || log "EnzyExtract parquet download failed."
    fi
fi
[[ -f "$ENZYEXTRACT_PARQUET" ]] || log "WARNING: EnzyExtract parquet not present at $ENZYEXTRACT_PARQUET"

# ─── GotEnzymes2 (Class A; CC BY 4.0; bulk pull) ────────────────────────
GOTENZYMES2_JSONL="$DATA_ROOT/gotenzymes2/gotenzymes2_bulk.jsonl"
if [[ ! -f "$GOTENZYMES2_JSONL" ]]; then
    if [[ "$hf_dataset_exists" == "1" ]]; then
        hf download "$HF_CORPUS_REPO" "gotenzymes2/gotenzymes2_bulk.jsonl" --repo-type dataset \
            --local-dir "$DATA_ROOT" >/dev/null 2>&1 || \
            log "WARNING: GotEnzymes2 not on HF dataset; bulk pull from gotenzymes.io would go here."
    else
        log "WARNING: GotEnzymes2 not pre-staged."
    fi
fi

# ─── ProteinGym (Class A; MIT; OATML-Markslab/ProteinGym) ──────────────
PROTEINGYM_CSV="$DATA_ROOT/proteingym/DMS_substitutions.csv"
if [[ ! -f "$PROTEINGYM_CSV" ]]; then
    if [[ "$hf_dataset_exists" == "1" ]]; then
        hf download "$HF_CORPUS_REPO" "proteingym/DMS_substitutions.csv" --repo-type dataset \
            --local-dir "$DATA_ROOT" >/dev/null 2>&1
    fi
    if [[ ! -f "$PROTEINGYM_CSV" ]]; then
        log "Direct download ProteinGym DMS_substitutions.csv from OATML-Markslab/ProteinGym…"
        curl -fsSL "https://github.com/OATML-Markslab/ProteinGym/raw/main/reference_files/DMS_substitutions.csv" \
            -o "$PROTEINGYM_CSV" || log "ProteinGym CSV download failed."
    fi
fi
[[ -f "$PROTEINGYM_CSV" ]] || log "WARNING: ProteinGym DMS_substitutions.csv not present."

# ─── eQuilibrator cache pre-warm ─────────────────────────────────────────
log "Pre-warming eQuilibrator ComponentContribution cache…"
python -c "
import equilibrator_api as eq
cc = eq.ComponentContribution()
print('eQuilibrator cache loaded; example: ΔG\\'°(g6p→f6p) =', cc.standard_dg_prime(cc.parse_reaction_formula('bigg.metabolite:g6p = bigg.metabolite:f6p')).value.magnitude, 'kJ/mol')
" || log "WARNING: eQuilibrator cache load failed."

# ─── ESM-2 + ESMFold weight pre-cache ────────────────────────────────────
log "Pre-caching ESM-2 (650M) + ESMFold weights from HF…"
python - <<'PY'
import os
os.environ.setdefault("HF_HUB_DISABLE_TELEMETRY", "1")
from huggingface_hub import snapshot_download
for repo in ("facebook/esm2_t33_650M_UR50D", "facebook/esmfold_v1"):
    try:
        path = snapshot_download(repo)
        print(f"cached {repo} -> {path}")
    except Exception as e:
        print(f"WARNING: failed to cache {repo}: {e}")
PY

# ─── Update wave4 config to point at pod data paths ─────────────────────
WAVE4_CFG="$REPO_DIR/configs/cekm/wave4_real_corpus.yaml"
PHASE_CFG="$REPO_DIR/audit/runtime/runpod/wave4_active_corpus.yaml"
log "Materialising active config at $PHASE_CFG (rewriting paths to pod data dir)…"
sed \
    -e "s|/workspace/data/brenda/brenda_data.tsv|$BRENDA_TSV|g" \
    -e "s|/workspace/data/enzyextract/parameters.tsv|$ENZYEXTRACT_PARQUET|g" \
    -e "s|/workspace/data/gotenzymes2/gotenzymes2_bulk.jsonl|$GOTENZYMES2_JSONL|g" \
    -e "s|/workspace/data/proteingym/DMS_substitutions.csv|$PROTEINGYM_CSV|g" \
    "$WAVE4_CFG" > "$PHASE_CFG"

# Drop missing-source paths to None so loaders skip them gracefully.
python - <<PY
import yaml, pathlib
p = pathlib.Path("$PHASE_CFG")
cfg = yaml.safe_load(p.read_text())
for key, path in (
    ("brenda_tsv_path", "$BRENDA_TSV"),
    ("enzyextract_tsv_path", "$ENZYEXTRACT_PARQUET"),
    ("gotenzymes2_jsonl_path", "$GOTENZYMES2_JSONL"),
    ("proteingym_csv_path", "$PROTEINGYM_CSV"),
):
    if path and not pathlib.Path(path).exists():
        cfg[key] = None
        print(f"NOTE: {key} -> None (file not found)")
p.write_text(yaml.safe_dump(cfg, sort_keys=False))
PY

log "Data staging complete. Active config: $PHASE_CFG"
exit 0
