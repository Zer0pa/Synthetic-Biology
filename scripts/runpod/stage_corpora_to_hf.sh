#!/usr/bin/env bash
# Mac-side: pre-stage CEKM corpora to a private HF dataset so the
# pod's phase 20 downloads in ~10 min instead of cloning + bulk-pulling
# from public sources (~45–60 min).
#
# Run this on the originating Mac BEFORE booting the H100 pod:
#
#   bash scripts/runpod/stage_corpora_to_hf.sh
#
# The script:
#   1. Ensures HF login (HF_TOKEN env or ~/.cache/huggingface/token).
#   2. Creates the private HF dataset Architect-Prime/synbio-cekm-corpus-v0.1
#      if it doesn't exist.
#   3. For each corpus, locates a local copy (or auto-clones public
#      repos), uploads to the dataset under the canonical layout.
#   4. Computes + records sha256 of every uploaded file.
#
# BRENDA bulk requires registration at https://www.brenda-enzymes.org/
# and a manual download. If brenda_data.tsv isn't found at
# data/raw/brenda/, the script prints download instructions and
# continues without it. The pod's CEKM training will then run
# without BRENDA core (EnzyExtract + GotEnzymes2 + ProteinGym only).

# Don't use -e: we want to continue past missing/failed sources rather
# than abort the whole staging run.
set -uo pipefail

REPO_DIR="${REPO_DIR:-$(cd "$(dirname "$0")/../.." && pwd)}"
cd "$REPO_DIR"

ts() { date -u +"%Y-%m-%dT%H:%M:%SZ"; }
log() { printf '[stage_corpora %s] %s\n' "$(ts)" "$*"; }

VENV="$REPO_DIR/.venv"
if [[ -d "$VENV" ]]; then
    # shellcheck disable=SC1091
    source "$VENV/bin/activate"
fi

# ─── HF auth ────────────────────────────────────────────────────────────
if [[ -z "${HF_TOKEN:-}" ]]; then
    if [[ -f "${HOME}/.cache/huggingface/token" ]]; then
        export HF_TOKEN=$(cat "${HOME}/.cache/huggingface/token")
        log "HF_TOKEN read from ~/.cache/huggingface/token"
    else
        log "FATAL: HF_TOKEN not set and ~/.cache/huggingface/token not found."
        exit 60
    fi
fi

python -c "import huggingface_hub" 2>/dev/null || pip install --quiet "huggingface_hub[cli]"

HF_REPO="Architect-Prime/synbio-cekm-corpus-v0.1"

# ─── ensure dataset exists ─────────────────────────────────────────────
log "Ensuring HF dataset $HF_REPO exists (private)…"
hf repos create "$HF_REPO" --type dataset --private 2>&1 | tail -3 || true

# ─── source paths (local) ──────────────────────────────────────────────
RAW_DIR="${RAW_DATA_DIR:-data/raw}"
mkdir -p "$RAW_DIR"/{brenda,enzyextract,gotenzymes2,proteingym}

stage_file() {
    local local_path="$1" hf_path="$2" source_label="$3"
    if [[ ! -f "$local_path" ]]; then
        log "WARNING: $source_label local file missing at $local_path; skipping HF push for this source."
        return 1
    fi
    local size=$(stat -c %s "$local_path" 2>/dev/null || stat -f %z "$local_path" 2>/dev/null || echo 0)
    log "Uploading $source_label ($((size/1024/1024)) MB) → $HF_REPO/$hf_path …"
    hf upload "$HF_REPO" "$local_path" "$hf_path" --repo-type dataset \
        --commit-message "Stage $source_label at $(ts)" 2>&1 | tail -3
    # Record SHA256.
    local sha
    if command -v sha256sum >/dev/null 2>&1; then
        sha=$(sha256sum "$local_path" | awk '{print $1}')
    else
        sha=$(shasum -a 256 "$local_path" | awk '{print $1}')
    fi
    echo "$hf_path  sha256=$sha  size=$size  staged=$(ts)" >> "$RAW_DIR/STAGED_MANIFEST.txt"
    log "  sha256: $sha"
}

# ─── BRENDA (registration-required; user pre-downloads) ────────────────
BRENDA_TSV="$RAW_DIR/brenda/brenda_data.tsv"
if [[ ! -f "$BRENDA_TSV" ]]; then
    log "BRENDA bulk not found at $BRENDA_TSV."
    log "  To stage BRENDA: register at https://www.brenda-enzymes.org/, download the bulk TSV,"
    log "  flatten with the brenda_textmining package or your preferred parser, place at"
    log "  $BRENDA_TSV, and re-run this script."
fi
stage_file "$BRENDA_TSV" "brenda/brenda_data.tsv" "BRENDA" || true

# ─── EnzyExtract (public; ChemBioHTP/EnzyExtract; parquet format) ─────
ENZY_PARQUET="$RAW_DIR/enzyextract/EnzyExtractDB_176463.parquet"
if [[ ! -f "$ENZY_PARQUET" ]]; then
    log "Downloading EnzyExtract parquet (~10 MB) from ChemBioHTP/EnzyExtract…"
    curl -fsSL "https://github.com/ChemBioHTP/EnzyExtract/raw/main/EnzyExtractDB/EnzyExtractDB_176463.parquet" \
        -o "$ENZY_PARQUET" || log "EnzyExtract parquet download failed."
fi
stage_file "$ENZY_PARQUET" "enzyextract/EnzyExtractDB_176463.parquet" "EnzyExtract" || true

# ─── GotEnzymes2 (bulk pull) ───────────────────────────────────────────
GOT_JSONL="$RAW_DIR/gotenzymes2/gotenzymes2_bulk.jsonl"
if [[ ! -f "$GOT_JSONL" ]]; then
    log "GotEnzymes2 bulk not found at $GOT_JSONL."
    log "  Bulk pull URL is gated by gotenzymes.io's access terms; consult"
    log "  audit/source_manifests/gotenzymes2.yaml for the canonical URI."
fi
stage_file "$GOT_JSONL" "gotenzymes2/gotenzymes2_bulk.jsonl" "GotEnzymes2" || true

# ─── ProteinGym (public; OATML-Markslab/ProteinGym) ───────────────────
PG_CSV="$RAW_DIR/proteingym/DMS_substitutions.csv"
if [[ ! -f "$PG_CSV" ]]; then
    log "Downloading ProteinGym DMS_substitutions.csv (~209 KB) from OATML-Markslab/ProteinGym…"
    curl -fsSL "https://github.com/OATML-Markslab/ProteinGym/raw/main/reference_files/DMS_substitutions.csv" \
        -o "$PG_CSV" || log "ProteinGym CSV download failed."
fi
stage_file "$PG_CSV" "proteingym/DMS_substitutions.csv" "ProteinGym" || true

# ─── README upload ─────────────────────────────────────────────────────
README="$RAW_DIR/HF_README.md"
{
    echo "# CEKM corpus (Architect-Prime/synbio-cekm-corpus-v0.1)"
    echo
    echo "Pre-staged corpora for the synbio CEKM training pipeline. Pulled by the"
    echo "H100 pod's phase 20 staging step (\`scripts/runpod/phases/20_stage_data.sh\`)."
    echo
    echo "## Sources (all Class A, permissive)"
    echo
    echo "| File | Source | License |"
    echo "|---|---|---|"
    echo "| brenda/brenda_data.tsv | https://www.brenda-enzymes.org/ | CC BY 4.0 |"
    echo "| enzyextract/EnzyExtractDB_176463.parquet | https://github.com/ChemBioHTP/EnzyExtract | MIT |"
    echo "| gotenzymes2/gotenzymes2_bulk.jsonl | https://gotenzymes.io/ | CC BY 4.0 |"
    echo "| proteingym/DMS_substitutions.csv | https://github.com/OATML-Markslab/ProteinGym | MIT |"
    echo
    echo "## Boundary"
    echo
    echo "Research artifact only. No regulatory certification claim. No clinical or human-subject use."
    echo
    echo "## SHA256 manifest"
    echo
    echo '```'
    cat "$RAW_DIR/STAGED_MANIFEST.txt" 2>/dev/null || echo "(none)"
    echo '```'
} > "$README"
hf upload "$HF_REPO" "$README" "README.md" --repo-type dataset \
    --commit-message "Update README at $(ts)" 2>&1 | tail -3 || true

log "Staging complete. Pod's phase 20 will pull from $HF_REPO."
exit 0
