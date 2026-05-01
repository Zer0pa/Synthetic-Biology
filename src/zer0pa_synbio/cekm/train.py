"""CEKM training entry point — scaffolding for Wave 4 Runpod session.

BOUNDARY:
Research infrastructure for in silico synthetic biology / metabolic pathway
engineering. Outputs are research artifacts — predicted pathways, predicted
KPIs, candidate genetic modification specifications. No regulatory
certification claims. No clinical or human-subject use. No environmental
release of GMOs. No biocontainment-level claims (the pipeline does not
commission BSL-2/3 work). No human gene drive or eugenic application.
Defence / weapons / dual-use bio applications excluded under operator policy.

PRD §12 is the controlling spec for this module.

Usage (CLI):
    synbio cekm train --config path/to/config.yaml
    synbio cekm train --config path/to/config.yaml --resume
    synbio cekm smoke
    synbio cekm eval --config path/to/config.yaml --checkpoint path/to/ckpt.pt

Architecture:
    ESM-2 (650M, facebook/esm2_t33_650M_UR50D) — frozen by default; configurable
      to unfreeze last N transformer layers.
    D-MPNN substrate encoder — directed message-passing neural network over
      molecular graphs (atom + bond features from SMILES/InChI).
    Condition MLP — temperature_c + pH → latent condition vector.
    Adaptive gate — learnable combination (α, β, γ scalars) of the three
      representations.
    Output heads:
      kcat_head  — regression, predicts log10(kcat / s⁻¹)
      km_head    — regression, predicts log10(Km / mM)
      disc_head  — binary classification per adversarial-negative tier
                   (positives vs α/β/γ negatives; three separate classifiers).

Loss (PRD §12):
    L_total = w_sup  * L_supervised_regression
            + w_curr * L_curriculum_gotenzymes2
            + w_cont * L_contrastive_discrimination

    L_supervised_regression: MSE on log-kcat + log-Km for BRENDA +
      EnzyExtract + ProteinGym positives.
    L_curriculum_gotenzymes2: MSE against GotEnzymes2 soft pseudo-labels
      (lower weight; GotEnzymes2 treated as curriculum pre-training only).
    L_contrastive_discrimination: margin-based hinge (or NT-Xent) separating
      positives from each of the three adversarial-negative tiers.

Calibration gate (PRD §12.3 — load-bearing acceptance):
    At each checkpoint (and at end of training), report empirical 90% CI
    coverage on the held-out partition, broken down by:
      - Tier α adversarial negatives
      - Tier β adversarial negatives
      - Tier γ adversarial negatives
      - BRENDA 15% holdout
      - 100% EnzyExtract dark-matter holdout

Checkpoint / resume:
    Checkpoints saved to checkpoint_dir every checkpoint_every_steps steps.
    On --resume, loads the latest checkpoint (by step number).

Logging:
    TensorBoard: tb_log_dir (default: runs/cekm/<campaign>/).
    JSONL: audit/runtime/<campaign>/cekm_training.jsonl.

HF push (PRD §12.4):
    After training, push weights to Architect-Prime/synbio-cekm-v0.1 (HF
    private). Skipped silently if HF_TOKEN env var is absent.

License guard:
    assemble_corpus() in zer0pa_synbio.cekm already raises ValueError for
    Class C/D/E sources. train() enforces this at corpus-assembly time and
    aborts before any model is instantiated if the check fails.
"""

from __future__ import annotations

import dataclasses
import json
import logging
import os
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import click
import yaml

from zer0pa_synbio.boundary import BOUNDARY_BLOCK, BOUNDARY_SHA256
from zer0pa_synbio.cekm import (
    AdversarialNegative,
    CalibrationReport,
    CorpusSlice,
    HeldOutSplit,
    KineticsRow,
    assemble_corpus,
    held_out_split,
    sample_adversarial_negatives,
    smoke_test_pipeline,
)

log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Config dataclasses
# ---------------------------------------------------------------------------


@dataclass
class ESM2Config:
    """ESM-2 backbone configuration."""

    model_name: str = "facebook/esm2_t33_650M_UR50D"
    frozen: bool = True
    unfreeze_last_n_layers: int = 0  # 0 = fully frozen; >0 = unfreeze last N


@dataclass
class DMPNNConfig:
    """Directed Message-Passing Neural Network (substrate encoder) configuration."""

    atom_feature_dim: int = 72
    bond_feature_dim: int = 14
    hidden_dim: int = 300
    depth: int = 3
    dropout: float = 0.1
    aggregation: str = "mean"  # "mean" | "sum" | "norm"


@dataclass
class ConditionMLPConfig:
    """Condition MLP (temperature + pH → latent vector) configuration."""

    input_dim: int = 2  # [temperature_c, pH]
    hidden_dims: list[int] = field(default_factory=lambda: [64, 128])
    output_dim: int = 128
    dropout: float = 0.1


@dataclass
class AdaptiveGateConfig:
    """Adaptive gate combining ESM-2 + D-MPNN + condition representations."""

    esm2_dim: int = 1280  # ESM-2 650M CLS dim
    substrate_dim: int = 300  # must match DMPNNConfig.hidden_dim
    condition_dim: int = 128  # must match ConditionMLPConfig.output_dim
    gate_hidden_dim: int = 256
    output_dim: int = 512


@dataclass
class HeadsConfig:
    """Output head configuration."""

    kcat_hidden_dims: list[int] = field(default_factory=lambda: [256, 128])
    km_hidden_dims: list[int] = field(default_factory=lambda: [256, 128])
    discriminator_hidden_dims: list[int] = field(default_factory=lambda: [128, 64])
    # Three discriminators: one per adversarial tier (alpha, beta, gamma).
    n_discriminator_heads: int = 3


@dataclass
class LossConfig:
    """Loss weighting configuration (PRD §12)."""

    # Supervised regression (BRENDA + EnzyExtract + ProteinGym positives)
    w_supervised: float = 1.0
    # Curriculum pre-training on GotEnzymes2 soft pseudo-labels (lower weight)
    w_curriculum: float = 0.3
    # Contrastive discrimination of α/β/γ adversarial negatives
    w_contrastive: float = 0.5
    # Contrastive loss type: "hinge" (margin-based) | "ntxent"
    contrastive_type: str = "hinge"
    contrastive_margin: float = 1.0  # used when contrastive_type == "hinge"
    contrastive_temperature: float = 0.07  # used when contrastive_type == "ntxent"


@dataclass
class TrainingConfig:
    """Main training loop configuration."""

    campaign_id: str = "cekm_v0"
    seed: int = 42
    # Data
    max_corpus_rows: int | None = None  # None = use all rows
    holdout_fraction: float = 0.15
    enzyextract_holdout_full: bool = True
    # Decoy pool: InChIKey strings for adversarial-negative sampling
    decoy_pool_path: str | None = None  # path to a .txt file of InChIKeys; None = intra-corpus
    # Training loop
    batch_size: int = 64
    gradient_accumulation_steps: int = 4
    learning_rate: float = 3e-4
    weight_decay: float = 1e-2
    warmup_steps: int = 500
    max_steps: int = 20_000
    eval_every_steps: int = 500
    checkpoint_every_steps: int = 1000
    # Precision and hardware
    use_bf16: bool = True
    use_flash_attention_2: bool = False  # requires flash-attn >=2 installed on GPU
    # Directories
    checkpoint_dir: str = "checkpoints/cekm"
    tb_log_dir: str = "runs/cekm"
    # HF push (PRD §12.4)
    hf_repo_id: str = "Architect-Prime/synbio-cekm-v0.1"
    hf_private: bool = True
    # Submodule configs
    esm2: ESM2Config = field(default_factory=ESM2Config)
    dmpnn: DMPNNConfig = field(default_factory=DMPNNConfig)
    condition_mlp: ConditionMLPConfig = field(default_factory=ConditionMLPConfig)
    adaptive_gate: AdaptiveGateConfig = field(default_factory=AdaptiveGateConfig)
    heads: HeadsConfig = field(default_factory=HeadsConfig)
    loss: LossConfig = field(default_factory=LossConfig)


def load_config(path: Path) -> TrainingConfig:
    """Load a TrainingConfig from a YAML file.

    Handles nested dataclass fields by recursively applying the appropriate
    dataclass constructor. Unknown keys are silently ignored (forward
    compatibility). Sub-keys in YAML map onto named nested dataclasses.

    Uses typing.get_type_hints() to resolve string annotations produced by
    ``from __future__ import annotations`` (PEP 563), so nested dataclass
    fields are correctly detected even in Python 3.11+.
    """
    import typing

    raw: dict[str, Any] = yaml.safe_load(path.read_text(encoding="utf-8")) or {}

    # Map of known sub-config type names to their classes (for hint resolution).
    _KNOWN_TYPES: dict[str, type] = {
        "ESM2Config": ESM2Config,
        "DMPNNConfig": DMPNNConfig,
        "ConditionMLPConfig": ConditionMLPConfig,
        "AdaptiveGateConfig": AdaptiveGateConfig,
        "HeadsConfig": HeadsConfig,
        "LossConfig": LossConfig,
        "TrainingConfig": TrainingConfig,
    }

    def _resolve_hints(dc_type: type) -> dict[str, type]:
        """Return {field_name: resolved_type} for a dataclass, handling PEP-563."""
        try:
            return typing.get_type_hints(dc_type, localns=_KNOWN_TYPES)
        except Exception:
            # Fallback: return empty dict; fields won't be recursively applied.
            return {}

    def _apply(dc_type: type, data: dict) -> Any:
        if not dataclasses.is_dataclass(dc_type):
            return data
        hints = _resolve_hints(dc_type)
        # Build kwargs for the dataclass; recursively handle nested dataclasses.
        kwargs: dict[str, Any] = {}
        field_names = {f.name for f in dataclasses.fields(dc_type)}
        for key, val in data.items():
            if key not in field_names:
                continue  # ignore unknown keys
            ftype = hints.get(key)
            if ftype is not None and isinstance(ftype, type) and dataclasses.is_dataclass(ftype) and isinstance(val, dict):
                kwargs[key] = _apply(ftype, val)
            else:
                kwargs[key] = val
        return dc_type(**kwargs)

    return _apply(TrainingConfig, raw)


def config_to_dict(cfg: TrainingConfig) -> dict[str, Any]:
    """Serialize a TrainingConfig to a plain dict (for logging and audit)."""
    return dataclasses.asdict(cfg)


# ---------------------------------------------------------------------------
# Checkpoint utilities
# ---------------------------------------------------------------------------


@dataclass
class CheckpointState:
    """Serialisable checkpoint state.

    Only primitive types so the dict round-trips through json.dumps /
    json.loads without loss.
    """

    step: int
    epoch: int
    global_loss: float
    best_calib_coverage: float  # best empirical 90% CI coverage on held-out
    config_hash: str  # sha256 of the serialised config dict (hex)
    model_state_path: str  # path to the .pt file with model + optimiser state
    boundary_sha256: str = BOUNDARY_SHA256  # for tamper-check


def checkpoint_state_to_dict(state: CheckpointState) -> dict[str, Any]:
    return dataclasses.asdict(state)


def checkpoint_state_from_dict(d: dict[str, Any]) -> CheckpointState:
    """Reconstruct CheckpointState from a plain dict (loaded from JSON)."""
    return CheckpointState(**{k: v for k, v in d.items() if k in {f.name for f in dataclasses.fields(CheckpointState)}})


def _latest_checkpoint(checkpoint_dir: Path) -> Path | None:
    """Return the metadata JSON for the most recent checkpoint, or None."""
    meta_files = sorted(checkpoint_dir.glob("ckpt_step*.meta.json"))
    return meta_files[-1] if meta_files else None


def save_checkpoint(
    state: CheckpointState,
    checkpoint_dir: Path,
    model_obj: Any,  # torch.nn.Module at runtime; Any here to avoid import
    optimiser_obj: Any,  # torch.optim.Optimizer
) -> Path:
    """Write a checkpoint to disk.

    Creates two files:
      ckpt_step<N>.meta.json   — CheckpointState dict (text, human-readable)
      ckpt_step<N>.pt          — model + optimiser state_dicts (torch.save)

    Returns the path to the .meta.json file.

    NOTE: The actual torch.save call is inside the TODO block. The function
    signature and file-naming convention are load-bearing.
    """
    checkpoint_dir.mkdir(parents=True, exist_ok=True)
    base = checkpoint_dir / f"ckpt_step{state.step:08d}"
    pt_path = base.with_suffix(".pt")
    meta_path = base.with_suffix("").with_suffix(".meta.json")

    # TODO(wave4): replace with:
    #   import torch
    #   torch.save({"model": model_obj.state_dict(),
    #               "optimiser": optimiser_obj.state_dict()}, pt_path)
    _ = model_obj  # silence linter until implemented
    _ = optimiser_obj

    state = dataclasses.replace(state, model_state_path=str(pt_path))
    meta_path.write_text(
        json.dumps(checkpoint_state_to_dict(state), indent=2),
        encoding="utf-8",
    )
    log.info("Checkpoint saved: %s", meta_path)
    return meta_path


def load_checkpoint(meta_path: Path) -> CheckpointState:
    """Load a CheckpointState from a .meta.json file (boundary tamper-check included)."""
    d = json.loads(meta_path.read_text(encoding="utf-8"))
    state = checkpoint_state_from_dict(d)
    if state.boundary_sha256 != BOUNDARY_SHA256:
        raise ValueError(
            f"Checkpoint boundary SHA256 mismatch: stored={state.boundary_sha256!r}, "
            f"current={BOUNDARY_SHA256!r}. Reject."
        )
    return state


# ---------------------------------------------------------------------------
# Audit / logging helpers
# ---------------------------------------------------------------------------


def _audit_log_path(campaign_id: str, repo_root: Path) -> Path:
    """Return the JSONL audit log path for a training campaign."""
    p = repo_root / "audit" / "runtime" / campaign_id / "cekm_training.jsonl"
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


def _write_audit_event(log_path: Path, event: dict[str, Any]) -> None:
    """Append one JSON event line to the audit JSONL log."""
    event.setdefault("ts", time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))
    event.setdefault("boundary_sha256", BOUNDARY_SHA256)
    with log_path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(event, ensure_ascii=False) + "\n")


# ---------------------------------------------------------------------------
# Dataset / corpus factory
# ---------------------------------------------------------------------------


def build_corpus_and_split(
    cfg: TrainingConfig,
    slices: list[CorpusSlice],
) -> tuple[list[KineticsRow], HeldOutSplit]:
    """Assemble corpus (with license guard) and produce held-out split.

    License enforcement: assemble_corpus() raises ValueError if any slice has
    license_class in {D, E}. Class C is blocked only if no grant is recorded
    in audit/license_grants/ — that check is enforced at corpus-slice
    construction time by the caller supplying pre-vetted CorpusSlice objects.

    The pipeline never calls torch or transformers in this function — it is
    safe on CPU-only machines and in test environments.
    """
    rows = assemble_corpus(slices)
    if cfg.max_corpus_rows is not None:
        rows = rows[: cfg.max_corpus_rows]
    split = held_out_split(
        rows,
        holdout_fraction=cfg.holdout_fraction,
        seed=cfg.seed,
        enzyextract_holdout_full=cfg.enzyextract_holdout_full,
    )
    return rows, split


def build_decoy_pool(
    cfg: TrainingConfig,
    rows: list[KineticsRow],
) -> list[str]:
    """Build or load the InChIKey decoy pool for adversarial-negative sampling.

    If cfg.decoy_pool_path is set, load from that file (one InChIKey per line).
    Otherwise fall back to intra-corpus substrates (the original behaviour of
    smoke_test_pipeline and the CPU prototype).
    """
    if cfg.decoy_pool_path:
        p = Path(cfg.decoy_pool_path)
        if not p.exists():
            raise FileNotFoundError(f"decoy_pool_path not found: {p}")
        keys = [ln.strip() for ln in p.read_text(encoding="utf-8").splitlines() if ln.strip()]
        log.info("Loaded %d decoy InChIKeys from %s", len(keys), p)
        return keys
    # Intra-corpus fallback: all substrate InChIKeys in the corpus.
    pool = list({r.substrate_inchi_key for r in rows})
    log.info("Built intra-corpus decoy pool: %d unique substrates", len(pool))
    return pool


# ---------------------------------------------------------------------------
# Model factory (GPU-bound; stubs here for structure)
# ---------------------------------------------------------------------------


def build_model(cfg: TrainingConfig) -> Any:
    """Instantiate and return the CEKM model.

    Returns a torch.nn.Module at runtime. Returns None in stub / CPU mode.

    Architecture (per PRD §12 and module docstring):
      ESM2Backbone(cfg.esm2) → enzyme representation (1280-dim CLS embedding)
      DMPNN(cfg.dmpnn)       → substrate representation (hidden_dim-dim)
      ConditionMLP(cfg.condition_mlp) → condition vector (output_dim-dim)
      AdaptiveGate(cfg.adaptive_gate) → fused representation (output_dim-dim)
      KcatHead(cfg.heads)    → scalar log10(kcat)
      KmHead(cfg.heads)      → scalar log10(Km)
      DiscHead × 3(cfg.heads) → binary logits for α/β/γ discrimination

    Optional: use_flash_attention_2=True patches ESM-2's attention with
    Flash Attention 2 (requires flash-attn >=2 installed).

    TODO(wave4): implement this function by importing:
        from zer0pa_synbio.cekm.model import CEKMModel
        model = CEKMModel(cfg)
        if cfg.training.use_flash_attention_2:
            model.esm2 = patch_flash_attention(model.esm2)
        if cfg.training.use_bf16:
            model = model.bfloat16()
        return model
    """
    # TODO(wave4): implement model construction.
    log.warning(
        "build_model(): stub — no torch model instantiated. "
        "Wave 4 agent should implement zer0pa_synbio.cekm.model.CEKMModel."
    )
    return None  # placeholder


def build_optimiser(model: Any, cfg: TrainingConfig) -> Any:
    """Instantiate AdamW optimiser.

    TODO(wave4): implement with:
        import torch
        return torch.optim.AdamW(
            [p for p in model.parameters() if p.requires_grad],
            lr=cfg.learning_rate,
            weight_decay=cfg.weight_decay,
        )
    """
    # TODO(wave4): implement.
    _ = model
    return None  # placeholder


def build_scheduler(optimiser: Any, cfg: TrainingConfig) -> Any:
    """Build a linear-warmup + cosine-decay LR scheduler.

    TODO(wave4): implement with torch.optim.lr_scheduler.OneCycleLR or
    transformers.get_cosine_schedule_with_warmup.
    """
    # TODO(wave4): implement.
    _ = optimiser
    return None  # placeholder


# ---------------------------------------------------------------------------
# Loss computation (stubs)
# ---------------------------------------------------------------------------


def compute_supervised_loss(
    kcat_pred: Any,
    km_pred: Any,
    kcat_target: Any,
    km_target: Any,
) -> Any:
    """MSE regression loss on log10(kcat) + log10(Km) for positives.

    Sources: BRENDA, EnzyExtract, ProteinGym.

    TODO(wave4): implement with:
        import torch.nn.functional as F
        loss_kcat = F.mse_loss(kcat_pred, kcat_target)
        loss_km   = F.mse_loss(km_pred, km_target)
        return loss_kcat + loss_km
    """
    # TODO(wave4): implement.
    return None  # placeholder


def compute_curriculum_loss(
    kcat_pred: Any,
    km_pred: Any,
    kcat_soft: Any,
    km_soft: Any,
) -> Any:
    """MSE loss against GotEnzymes2 soft pseudo-labels (curriculum pre-training).

    Lower weight (cfg.loss.w_curriculum) applied at call site.

    TODO(wave4): implement similarly to compute_supervised_loss.
    """
    # TODO(wave4): implement.
    return None  # placeholder


def compute_contrastive_loss(
    pos_embeddings: Any,
    neg_embeddings_alpha: Any,
    neg_embeddings_beta: Any,
    neg_embeddings_gamma: Any,
    disc_logits_alpha: Any,
    disc_logits_beta: Any,
    disc_logits_gamma: Any,
    cfg: LossConfig,
) -> Any:
    """Contrastive discrimination loss for adversarial-negative tiers.

    Supports:
      "hinge": margin-based hinge loss — pushes positives and negatives apart
        by at least cfg.contrastive_margin in embedding space.
      "ntxent": NT-Xent (InfoNCE) loss with temperature cfg.contrastive_temperature.

    Three separate discriminator heads (one per tier α/β/γ) each get a
    binary cross-entropy loss; the tier-level hinge/NT-Xent is computed on the
    fused embeddings.

    TODO(wave4): implement.
    """
    # TODO(wave4): implement.
    return None  # placeholder


# ---------------------------------------------------------------------------
# Calibration audit (PRD §12.3 — load-bearing acceptance gate)
# ---------------------------------------------------------------------------


def calibration_audit(
    model: Any,
    rows: list[KineticsRow],
    negatives: list[AdversarialNegative],
    split: HeldOutSplit,
    cfg: TrainingConfig,
) -> CalibrationReport:
    """Empirical 90% CI coverage audit on the held-out partition.

    Runs model in eval mode over the held-out rows (no gradients). Computes:
      - Fraction of true kcat values falling within the predicted 90% CI.
      - Reported separately for:
          * Tier α adversarial negatives (discrimination accuracy)
          * Tier β adversarial negatives
          * Tier γ adversarial negatives
          * BRENDA 15% holdout (regression calibration)
          * 100% EnzyExtract dark-matter holdout (out-of-distribution calibration)

    PRD §12.3 acceptance gate: all five coverage values must be >= 0.85 to
    set calibration_passed=True in the training summary. This gate is checked
    at every eval checkpoint and at end of training.

    TODO(wave4): implement by:
      1. Filtering rows by split.held_out_row_ids.
      2. Partitioning into BRENDA holdout / EnzyExtract holdout.
      3. Running batched model forward pass with dropout disabled.
      4. Collecting predicted (mean, std) — model must output uncertainty
         (use MC-dropout or an ensemble head).
      5. Computing empirical 90% CI: [mean - 1.645*std, mean + 1.645*std].
      6. Fraction of true values within CI = coverage.
      7. For adversarial tiers: report discrimination AUC (not CI coverage)
         using disc_head logits vs true labels.
    """
    # TODO(wave4): implement.
    _ = model
    held_out_rows = [r for r in rows if r.row_id in split.held_out_row_ids]
    brenda_held = [r for r in held_out_rows if r.source == "brenda"]
    enzyextract_held = [r for r in held_out_rows if r.source == "enzyextract"]
    neg_alpha = [n for n in negatives if n.tier == "alpha"]
    neg_beta = [n for n in negatives if n.tier == "beta"]
    neg_gamma = [n for n in negatives if n.tier == "gamma"]

    log.info(
        "calibration_audit: held_out=%d (brenda=%d enzyextract=%d), "
        "negatives: α=%d β=%d γ=%d",
        len(held_out_rows),
        len(brenda_held),
        len(enzyextract_held),
        len(neg_alpha),
        len(neg_beta),
        len(neg_gamma),
    )

    return CalibrationReport(
        tier_alpha_coverage_at_90=None,  # TODO(wave4): fill from model predictions
        tier_beta_coverage_at_90=None,
        tier_gamma_coverage_at_90=None,
        held_out_brenda_coverage_at_90=None,
        held_out_enzyextract_coverage_at_90=None,
        notes=(
            "Stub calibration report. Wave 4 agent must implement "
            "calibration_audit() with model forward passes and CI computation."
        ),
    )


def calibration_passed(report: CalibrationReport, threshold: float = 0.85) -> bool:
    """Return True iff all five coverage metrics meet the acceptance threshold.

    PRD §12.3: this is a load-bearing gate — training is not considered
    complete until all five values are >= threshold.
    """
    values = [
        report.tier_alpha_coverage_at_90,
        report.tier_beta_coverage_at_90,
        report.tier_gamma_coverage_at_90,
        report.held_out_brenda_coverage_at_90,
        report.held_out_enzyextract_coverage_at_90,
    ]
    if any(v is None for v in values):
        return False
    return all(v >= threshold for v in values)  # type: ignore[operator]


# ---------------------------------------------------------------------------
# HF push (PRD §12.4)
# ---------------------------------------------------------------------------


def push_to_hf(
    checkpoint_path: Path,
    cfg: TrainingConfig,
    *,
    dry_run: bool = False,
) -> bool:
    """Push trained weights to Hugging Face Hub (Architect-Prime/synbio-cekm-v0.1).

    Skips silently if HF_TOKEN is absent (per PRD §12.4). Returns True if
    push succeeded or was skipped, False if an error occurred.

    TODO(wave4): implement with:
        from huggingface_hub import HfApi
        api = HfApi(token=token)
        api.create_repo(cfg.hf_repo_id, private=cfg.hf_private, exist_ok=True)
        api.upload_file(
            path_or_fileobj=str(checkpoint_path),
            path_in_repo=checkpoint_path.name,
            repo_id=cfg.hf_repo_id,
        )
    """
    token = os.environ.get("HF_TOKEN")
    if not token:
        log.info("HF_TOKEN not set — skipping HF push (non-fatal per PRD §12.4).")
        return True

    if dry_run:
        log.info("push_to_hf: dry_run=True — skipping actual upload.")
        return True

    log.info(
        "push_to_hf: TODO(wave4) — implement upload of %s to %s",
        checkpoint_path,
        cfg.hf_repo_id,
    )
    # TODO(wave4): implement huggingface_hub upload here.
    return True


# ---------------------------------------------------------------------------
# Main training loop skeleton
# ---------------------------------------------------------------------------


def train(cfg: TrainingConfig, slices: list[CorpusSlice], *, resume: bool = False) -> dict[str, Any]:
    """Training loop skeleton for CEKM (PRD §12).

    This function is the single entry point for the Wave 4 Runpod session.
    All hooks (checkpoint, resume, logging, calibration, HF push) are wired
    in the correct sequence; the inner loop and model calls are TODO stubs.

    Returns a summary dict with training outcome, calibration report, and
    checkpoint path.

    License guard:
        assemble_corpus() will raise ValueError if any slice has
        license_class in {D, E}. This propagates here as a hard failure —
        training never starts with a disallowed source.
    """
    repo_root = Path(__file__).resolve().parents[4]  # src/zer0pa_synbio/cekm/train.py → repo
    audit_log = _audit_log_path(cfg.campaign_id, repo_root)
    checkpoint_dir = Path(cfg.checkpoint_dir)
    checkpoint_dir.mkdir(parents=True, exist_ok=True)

    _write_audit_event(
        audit_log,
        {
            "event": "training_start",
            "campaign_id": cfg.campaign_id,
            "resume": resume,
            "config": config_to_dict(cfg),
        },
    )

    # --- 1. Corpus assembly (license gate enforced by assemble_corpus) -----
    rows, split = build_corpus_and_split(cfg, slices)
    decoy_pool = build_decoy_pool(cfg, rows)
    in_corpus_rows = [r for r in rows if r.row_id in split.in_corpus_row_ids]
    negatives = sample_adversarial_negatives(in_corpus_rows, decoy_pool, seed=cfg.seed)

    log.info(
        "Corpus assembled: total=%d, in_corpus=%d, held_out=%d, negatives=%d",
        len(rows),
        len(split.in_corpus_row_ids),
        len(split.held_out_row_ids),
        len(negatives),
    )
    _write_audit_event(
        audit_log,
        {
            "event": "corpus_assembled",
            "total_rows": len(rows),
            "in_corpus_rows": len(in_corpus_rows),
            "held_out_rows": len(split.held_out_row_ids),
            "adversarial_negatives": len(negatives),
        },
    )

    # --- 2. Model + optimiser factory ------------------------------------
    model = build_model(cfg)
    optimiser = build_optimiser(model, cfg)
    scheduler = build_scheduler(optimiser, cfg)

    # --- 3. Resume from checkpoint (if requested) -----------------------
    start_step = 0
    best_calib_coverage = 0.0
    if resume:
        meta_path = _latest_checkpoint(checkpoint_dir)
        if meta_path is not None:
            ckpt_state = load_checkpoint(meta_path)
            start_step = ckpt_state.step
            best_calib_coverage = ckpt_state.best_calib_coverage
            log.info("Resuming from step %d (checkpoint: %s)", start_step, meta_path)
            _write_audit_event(
                audit_log,
                {
                    "event": "checkpoint_resumed",
                    "step": start_step,
                    "best_calib_coverage": best_calib_coverage,
                    "checkpoint": str(meta_path),
                },
            )
            # TODO(wave4): load model + optimiser state:
            #   import torch
            #   state_dict = torch.load(ckpt_state.model_state_path, weights_only=True)
            #   model.load_state_dict(state_dict["model"])
            #   optimiser.load_state_dict(state_dict["optimiser"])
        else:
            log.info("--resume requested but no checkpoint found; starting from scratch.")

    # --- 4. TensorBoard writer ------------------------------------------
    tb_log_dir = Path(cfg.tb_log_dir) / cfg.campaign_id
    tb_log_dir.mkdir(parents=True, exist_ok=True)
    tb_writer: Any = None
    # TODO(wave4): instantiate SummaryWriter:
    #   from torch.utils.tensorboard import SummaryWriter
    #   tb_writer = SummaryWriter(log_dir=str(tb_log_dir))

    # --- 5. Training loop -----------------------------------------------
    global_step = start_step
    final_calib_report = CalibrationReport(notes="No calibration run yet — training loop is a stub.")

    # TODO(wave4): replace the block below with a real DataLoader + training loop:
    #
    # for epoch in range(cfg.max_steps // steps_per_epoch):
    #     for batch in dataloader:
    #         # --- forward pass ---
    #         outputs = model(batch)
    #
    #         # --- loss computation ---
    #         L_sup  = compute_supervised_loss(...)
    #         L_curr = compute_curriculum_loss(...)
    #         L_cont = compute_contrastive_loss(...)
    #         loss   = (cfg.loss.w_supervised  * L_sup
    #                 + cfg.loss.w_curriculum  * L_curr
    #                 + cfg.loss.w_contrastive * L_cont)
    #         loss = loss / cfg.gradient_accumulation_steps
    #
    #         # --- bf16 mixed-precision backward ---
    #         scaler.scale(loss).backward()
    #
    #         if (global_step + 1) % cfg.gradient_accumulation_steps == 0:
    #             scaler.unscale_(optimiser)
    #             torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
    #             scaler.step(optimiser)
    #             scaler.update()
    #             scheduler.step()
    #             optimiser.zero_grad()
    #
    #         # --- logging ---
    #         if tb_writer and global_step % 50 == 0:
    #             tb_writer.add_scalar("loss/total",      loss.item(),  global_step)
    #             tb_writer.add_scalar("loss/supervised", L_sup.item(), global_step)
    #             tb_writer.add_scalar("loss/curriculum", L_curr.item(), global_step)
    #             tb_writer.add_scalar("loss/contrastive",L_cont.item(),global_step)
    #         _write_audit_event(audit_log, {"event": "step", "step": global_step,
    #                                         "loss": loss.item()})
    #
    #         # --- eval + calibration audit ---
    #         if global_step % cfg.eval_every_steps == 0:
    #             calib = calibration_audit(model, rows, negatives, split, cfg)
    #             if calibration_passed(calib):
    #                 best_calib_coverage = min(filter(None, [
    #                     calib.tier_alpha_coverage_at_90,
    #                     calib.tier_beta_coverage_at_90,
    #                     calib.tier_gamma_coverage_at_90,
    #                     calib.held_out_brenda_coverage_at_90,
    #                     calib.held_out_enzyextract_coverage_at_90,
    #                 ]))
    #             _write_audit_event(audit_log, {"event": "calibration",
    #                                            "step": global_step,
    #                                            **calib.to_dict()})
    #             if tb_writer:
    #                 for k, v in calib.to_dict().items():
    #                     if isinstance(v, float):
    #                         tb_writer.add_scalar(f"calib/{k}", v, global_step)
    #
    #         # --- checkpoint ---
    #         if global_step % cfg.checkpoint_every_steps == 0:
    #             import hashlib, json as _json
    #             config_hash = hashlib.sha256(
    #                 _json.dumps(config_to_dict(cfg), sort_keys=True).encode()
    #             ).hexdigest()
    #             ckpt = CheckpointState(
    #                 step=global_step, epoch=epoch, global_loss=loss.item(),
    #                 best_calib_coverage=best_calib_coverage,
    #                 config_hash=config_hash,
    #                 model_state_path="(set by save_checkpoint)",
    #             )
    #             meta_path = save_checkpoint(ckpt, checkpoint_dir, model, optimiser)
    #             _write_audit_event(audit_log, {"event": "checkpoint_saved",
    #                                            "step": global_step,
    #                                            "meta": str(meta_path)})
    #
    #         global_step += 1
    #         if global_step >= cfg.max_steps:
    #             break

    log.info(
        "Training loop stub: max_steps=%d not executed. "
        "Wave 4 agent must replace this TODO block with the real loop.",
        cfg.max_steps,
    )

    # --- 6. Final calibration audit -------------------------------------
    final_calib_report = calibration_audit(model, rows, negatives, split, cfg)
    _write_audit_event(
        audit_log,
        {
            "event": "final_calibration",
            "step": global_step,
            **final_calib_report.to_dict(),
        },
    )
    gate_passed = calibration_passed(final_calib_report)
    log.info("Calibration gate passed: %s", gate_passed)

    # --- 7. HF push ------------------------------------------------------
    last_ckpt_meta = _latest_checkpoint(checkpoint_dir)
    hf_pushed = False
    if last_ckpt_meta is not None:
        hf_pushed = push_to_hf(last_ckpt_meta, cfg)

    if tb_writer is not None:
        tb_writer.close()  # type: ignore[union-attr]

    summary = {
        "schema_version": "synbio.cekm_training.v0.1",
        "boundary_sha256": BOUNDARY_SHA256,
        "campaign_id": cfg.campaign_id,
        "steps_completed": global_step,
        "corpus_total": len(rows),
        "in_corpus": len(in_corpus_rows),
        "held_out": len(split.held_out_row_ids),
        "negatives": len(negatives),
        "calibration_report": final_calib_report.to_dict(),
        "calibration_gate_passed": gate_passed,
        "hf_push_attempted": last_ckpt_meta is not None,
        "hf_pushed": hf_pushed,
        "checkpoint_dir": str(checkpoint_dir),
        "audit_log": str(audit_log),
    }
    _write_audit_event(audit_log, {"event": "training_complete", **summary})
    return summary


# ---------------------------------------------------------------------------
# CLI (wired via cli/__main__.py)
# ---------------------------------------------------------------------------


@click.group("cekm")
def cekm_group() -> None:
    """CEKM (Conditional Enzyme Kinetics Model) commands."""


@cekm_group.command("train")
@click.option(
    "--config",
    "config_path",
    required=True,
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    help="Path to YAML training config.",
)
@click.option(
    "--resume",
    is_flag=True,
    default=False,
    help="Resume from the latest checkpoint in checkpoint_dir.",
)
def cekm_train(config_path: Path, resume: bool) -> None:
    """Train CEKM from a YAML config.

    Corpus slices must be wired in the config (or overridden here once the
    Wave 4 data-ingestion pipeline is complete). For now, a smoke-test corpus
    is used to validate the orchestration end-to-end.
    """
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    cfg = load_config(config_path)
    click.echo(f"Loaded config: campaign={cfg.campaign_id}, max_steps={cfg.max_steps}")

    # TODO(wave4): replace synthetic slices with real data loaders that
    # construct CorpusSlice objects from BRENDA, EnzyExtract, GotEnzymes2,
    # ProteinGym. These slices must have license_class vetted against
    # audit/source_manifests/*.yaml before being passed here.
    click.echo(
        "WARNING: Using synthetic stub corpus. "
        "Wave 4 agent must wire real CorpusSlice objects."
    )
    slices: list[CorpusSlice] = []

    summary = train(cfg, slices, resume=resume)
    click.echo(json.dumps(summary, indent=2))


@cekm_group.command("smoke")
def cekm_smoke() -> None:
    """Run the CPU-side data-pipeline smoke test (no GPU required)."""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    summary = smoke_test_pipeline()
    click.echo(json.dumps(summary, indent=2))
    passed = (
        summary.get("corpus_size", 0) == 100
        and summary.get("adversarial_negative_count", 0) == summary.get("in_corpus_size", 0) * 3
    )
    if not passed:
        raise click.ClickException("Smoke test assertion failed — check the output above.")
    click.echo("Smoke test PASSED.")


@cekm_group.command("eval")
@click.option(
    "--config",
    "config_path",
    required=True,
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    help="Path to YAML training config.",
)
@click.option(
    "--checkpoint",
    "checkpoint_path",
    required=True,
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    help="Path to a .meta.json checkpoint file.",
)
def cekm_eval(config_path: Path, checkpoint_path: Path) -> None:
    """Run calibration audit on a saved checkpoint.

    Loads the checkpoint, runs calibration_audit() on the held-out partition,
    and prints the CalibrationReport as JSON. Exits 1 if the acceptance gate
    is not met.
    """
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    cfg = load_config(config_path)
    ckpt_state = load_checkpoint(Path(checkpoint_path))
    click.echo(f"Loaded checkpoint at step {ckpt_state.step}")

    # TODO(wave4): load real model, build real corpus, run calibration_audit().
    slices: list[CorpusSlice] = []
    rows, split = build_corpus_and_split(cfg, slices)
    decoy_pool = build_decoy_pool(cfg, rows)
    in_corpus_rows = [r for r in rows if r.row_id in split.in_corpus_row_ids]
    negatives = sample_adversarial_negatives(in_corpus_rows, decoy_pool, seed=cfg.seed)

    model = None  # TODO(wave4): load from ckpt_state.model_state_path
    report = calibration_audit(model, rows, negatives, split, cfg)
    click.echo(json.dumps(report.to_dict(), indent=2))
    if not calibration_passed(report):
        raise click.ClickException(
            "Calibration gate NOT passed. "
            "One or more coverage metrics are below 0.85 or are None (stub). "
            "Wave 4 agent must implement calibration_audit()."
        )
    click.echo("Calibration gate PASSED.")


__all__ = [
    # Config dataclasses
    "ESM2Config",
    "DMPNNConfig",
    "ConditionMLPConfig",
    "AdaptiveGateConfig",
    "HeadsConfig",
    "LossConfig",
    "TrainingConfig",
    # Config I/O
    "load_config",
    "config_to_dict",
    # Checkpoint
    "CheckpointState",
    "checkpoint_state_to_dict",
    "checkpoint_state_from_dict",
    "save_checkpoint",
    "load_checkpoint",
    # Dataset / corpus
    "build_corpus_and_split",
    "build_decoy_pool",
    # Model factory
    "build_model",
    "build_optimiser",
    "build_scheduler",
    # Loss
    "compute_supervised_loss",
    "compute_curriculum_loss",
    "compute_contrastive_loss",
    # Calibration
    "calibration_audit",
    "calibration_passed",
    # HF push
    "push_to_hf",
    # Main entry point
    "train",
    # CLI group
    "cekm_group",
]
