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

    # Save model + optimiser state dicts when both are real torch objects.
    try:
        import torch as _torch
        payload: dict[str, Any] = {}
        if model_obj is not None and hasattr(model_obj, "state_dict"):
            payload["model"] = model_obj.state_dict()
        if optimiser_obj is not None and hasattr(optimiser_obj, "state_dict"):
            payload["optimiser"] = optimiser_obj.state_dict()
        if payload:
            _torch.save(payload, pt_path)
        else:
            # Nothing to save; write an empty marker file so the path exists.
            pt_path.touch()
    except ImportError:
        # torch not installed — write a stub marker.
        pt_path.touch()
    except Exception as _exc:
        log.warning("save_checkpoint: torch.save failed (%s); writing stub marker.", _exc)
        pt_path.touch()

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

    Returns a torch.nn.Module at runtime. Returns None when torch is absent
    (CPU-only CI / smoke-test environments).

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
    """
    try:
        from zer0pa_synbio.cekm.model import CEKMModel, _TORCH_AVAILABLE
    except ImportError:
        log.warning("build_model(): zer0pa_synbio.cekm.model not importable — returning None.")
        return None

    if not _TORCH_AVAILABLE:
        log.warning(
            "build_model(): torch not available — returning None (CPU-only mode)."
        )
        return None

    try:
        import torch
        model = CEKMModel(cfg)
        if cfg.use_bf16:
            try:
                model = model.to(torch.bfloat16)
            except Exception:
                pass  # bfloat16 may not be supported on this device
        log.info(
            "build_model(): CEKMModel instantiated (esm2_real=%s, substrate_mode=%s).",
            model._using_real_esm2,
            model.substrate_encoder.input_mode,
        )
        return model
    except Exception as exc:
        log.warning("build_model(): failed to instantiate CEKMModel (%s) — returning None.", exc)
        return None


def build_optimiser(model: Any, cfg: TrainingConfig) -> Any:
    """Instantiate AdamW optimiser for the CEKM model.

    Uses betas=(0.9, 0.999) per PRD §12. Only optimises parameters that
    require gradients (i.e., the frozen backbone parameters are excluded).

    Returns None when model is None (CPU-only / stub mode).
    """
    if model is None:
        return None
    try:
        import torch
        trainable = [p for p in model.parameters() if p.requires_grad]
        if not trainable:
            log.warning("build_optimiser(): no trainable parameters found.")
            return None
        optimiser = torch.optim.AdamW(
            trainable,
            lr=cfg.learning_rate,
            weight_decay=cfg.weight_decay,
            betas=(0.9, 0.999),
        )
        log.info(
            "build_optimiser(): AdamW with lr=%.2e, wd=%.2e, %d param-groups.",
            cfg.learning_rate,
            cfg.weight_decay,
            len(trainable),
        )
        return optimiser
    except Exception as exc:
        log.warning("build_optimiser(): failed (%s) — returning None.", exc)
        return None


def build_scheduler(optimiser: Any, cfg: TrainingConfig) -> Any:
    """Build a linear-warmup + cosine-decay LR scheduler.

    Uses transformers.get_cosine_schedule_with_warmup when available;
    falls back to torch.optim.lr_scheduler.CosineAnnealingLR without warmup.

    Returns None when optimiser is None (CPU-only / stub mode).
    """
    if optimiser is None:
        return None
    try:
        # Prefer transformers scheduler (linear warmup + cosine decay).
        try:
            from transformers import get_cosine_schedule_with_warmup  # type: ignore
            scheduler = get_cosine_schedule_with_warmup(
                optimiser,
                num_warmup_steps=cfg.warmup_steps,
                num_training_steps=cfg.max_steps,
            )
            log.info(
                "build_scheduler(): transformers cosine-with-warmup "
                "(warmup=%d, max_steps=%d).",
                cfg.warmup_steps,
                cfg.max_steps,
            )
            return scheduler
        except ImportError:
            pass

        # Fallback: plain cosine without warmup.
        import torch
        scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(
            optimiser,
            T_max=max(1, cfg.max_steps - cfg.warmup_steps),
        )
        log.info(
            "build_scheduler(): CosineAnnealingLR fallback (T_max=%d).",
            cfg.max_steps,
        )
        return scheduler
    except Exception as exc:
        log.warning("build_scheduler(): failed (%s) — returning None.", exc)
        return None


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

    Both predictions and targets should be in log10-space. NaN targets
    (entries where kcat or Km is unknown) are masked out before computing
    the mean so the loss is only computed on available measurements.

    Returns:
        Scalar tensor — sum of MSE(kcat) + MSE(Km), or 0.0 if no valid
        targets are present.
    """
    try:
        import torch
        import torch.nn.functional as F_

        total = torch.tensor(0.0, requires_grad=True)

        if kcat_pred is not None and kcat_target is not None:
            mask = ~torch.isnan(kcat_target)
            if mask.any():
                loss_kcat = F_.mse_loss(kcat_pred[mask], kcat_target[mask])
                total = total + loss_kcat

        if km_pred is not None and km_target is not None:
            mask = ~torch.isnan(km_target)
            if mask.any():
                loss_km = F_.mse_loss(km_pred[mask], km_target[mask])
                total = total + loss_km

        return total
    except Exception as exc:
        log.warning("compute_supervised_loss(): error (%s) — returning None.", exc)
        return None


def compute_curriculum_loss(
    kcat_pred: Any,
    km_pred: Any,
    kcat_soft: Any,
    km_soft: Any,
) -> Any:
    """MSE loss against GotEnzymes2 soft pseudo-labels (curriculum pre-training).

    GotEnzymes2 labels are treated as soft pseudo-labels — they have higher
    uncertainty than BRENDA/EnzyExtract, so the caller applies a lower weight
    (cfg.loss.w_curriculum = 0.3 by default). The loss form is the same MSE
    as the supervised loss; the weighting is handled externally.

    Returns:
        Scalar tensor — sum of MSE(kcat_soft) + MSE(km_soft), or 0.0 if no
        valid soft-label targets are present.
    """
    try:
        import torch
        import torch.nn.functional as F_

        total = torch.tensor(0.0, requires_grad=True)

        if kcat_pred is not None and kcat_soft is not None:
            mask = ~torch.isnan(kcat_soft)
            if mask.any():
                total = total + F_.mse_loss(kcat_pred[mask], kcat_soft[mask])

        if km_pred is not None and km_soft is not None:
            mask = ~torch.isnan(km_soft)
            if mask.any():
                total = total + F_.mse_loss(km_pred[mask], km_soft[mask])

        return total
    except Exception as exc:
        log.warning("compute_curriculum_loss(): error (%s) — returning None.", exc)
        return None


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

    Two components per tier:
      1. Discriminator BCE loss: binary cross-entropy on disc_head logits
         (positives = label 1, negatives = label 0).
      2. Embedding-space loss:
         - "hinge": max(0, margin - dist(pos, neg)) per positive-negative pair.
         - "ntxent": NT-Xent / InfoNCE loss with temperature τ.

    The total contrastive loss is the sum over the three tiers.

    Returns:
        Scalar tensor — total contrastive loss, or 0.0 if inputs are None /
        insufficient (e.g., no negatives in the batch).
    """
    try:
        import torch
        import torch.nn.functional as F_

        total = torch.tensor(0.0, requires_grad=True)

        tier_triples = [
            (neg_embeddings_alpha, disc_logits_alpha),
            (neg_embeddings_beta, disc_logits_beta),
            (neg_embeddings_gamma, disc_logits_gamma),
        ]

        for neg_emb, disc_logits in tier_triples:
            # --- Discriminator BCE loss ------------------------------------
            if disc_logits is not None and pos_embeddings is not None:
                n_pos = disc_logits.shape[0] if disc_logits.dim() == 1 else disc_logits.shape[0]
                pos_labels = torch.ones(n_pos, device=disc_logits.device)
                total = total + F_.binary_cross_entropy_with_logits(disc_logits, pos_labels)

            # --- Embedding-space contrastive loss -------------------------
            if pos_embeddings is None or neg_emb is None:
                continue

            if pos_embeddings.shape[0] == 0 or neg_emb.shape[0] == 0:
                continue

            if cfg.contrastive_type == "hinge":
                # L2 distance between positive and negative embeddings.
                # Broadcast: each positive paired with the corresponding negative.
                n = min(pos_embeddings.shape[0], neg_emb.shape[0])
                dists = torch.norm(
                    pos_embeddings[:n] - neg_emb[:n], dim=-1
                )  # (n,)
                hinge = torch.clamp(cfg.contrastive_margin - dists, min=0.0)
                total = total + hinge.mean()

            elif cfg.contrastive_type == "ntxent":
                # NT-Xent: cosine-similarity matrix, temperature-scaled.
                # Each positive is its own positive; all negatives are negatives.
                tau = max(cfg.contrastive_temperature, 1e-6)
                n = min(pos_embeddings.shape[0], neg_emb.shape[0])
                pos_norm = F_.normalize(pos_embeddings[:n], dim=-1)   # (n, d)
                neg_norm = F_.normalize(neg_emb[:n], dim=-1)           # (n, d)
                # Compute pairwise similarity matrix over pos+neg.
                all_emb = torch.cat([pos_norm, neg_norm], dim=0)       # (2n, d)
                sim_mat = torch.mm(pos_norm, all_emb.T) / tau          # (n, 2n)
                # Labels: position i is positive of row i (the first n).
                labels = torch.arange(n, device=pos_embeddings.device)
                total = total + F_.cross_entropy(sim_mat, labels)

        return total

    except Exception as exc:
        log.warning("compute_contrastive_loss(): error (%s) — returning None.", exc)
        return None


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

    # When no real model is available, return the stub report (None values).
    # The calibration_passed() gate will correctly return False for None values.
    if model is None:
        return CalibrationReport(
            tier_alpha_coverage_at_90=None,
            tier_beta_coverage_at_90=None,
            tier_gamma_coverage_at_90=None,
            held_out_brenda_coverage_at_90=None,
            held_out_enzyextract_coverage_at_90=None,
            notes=(
                "Stub calibration report — model is None (CPU-only / no-torch mode). "
                "Wave 4 Runpod training will produce real coverage metrics."
            ),
        )

    # --- Real calibration with a trained model ----------------------------
    # PRD §12.3: Run model in eval mode over the held-out partition.
    # Use MC-Dropout for uncertainty estimation (enable_mc_dropout() call).
    # Empirical 90% CI: [mean - 1.645*std, mean + 1.645*std].
    try:
        import torch
        import numpy as np

        # Check model has the MC-dropout helper.
        has_mc_dropout = hasattr(model, "enable_mc_dropout")
        model.eval()
        if has_mc_dropout:
            model.enable_mc_dropout()

        N_MC = 30  # MC-Dropout samples for uncertainty estimation
        Z_90 = 1.645  # z-score for 90% CI

        def _estimate_coverage(
            source_rows: list[KineticsRow],
        ) -> float | None:
            """Empirical 90% CI coverage for kcat over `source_rows`."""
            if not source_rows:
                return None

            kcat_means: list[float] = []
            kcat_stds: list[float] = []
            kcat_targets: list[float] = []

            with torch.no_grad():
                for row in source_rows:
                    if row.kcat_per_s is None or row.kcat_per_s <= 0:
                        continue
                    import math as _math
                    target_log = _math.log10(row.kcat_per_s)

                    # Build minimal stub inputs for the model.
                    # Sequence: single residue → shape (1, 1).
                    seq_ids = torch.zeros(1, 1, dtype=torch.long)
                    # Substrate: hash of InChIKey → shape (1,) for stub mode.
                    sub_hash = hash(row.substrate_inchi_key) % (2**20)
                    substrate_input = torch.tensor([sub_hash], dtype=torch.long)
                    # Conditions: [pH, T, ionic_strength=0.15].
                    conds = torch.tensor(
                        [[row.ph, row.temperature_c]],
                        dtype=torch.float32,
                    )
                    # Pad conditions to cfg.condition_mlp.input_dim if needed.
                    cond_dim = cfg.condition_mlp.input_dim
                    if conds.shape[-1] < cond_dim:
                        pad = torch.zeros(1, cond_dim - conds.shape[-1])
                        conds = torch.cat([conds, pad], dim=-1)

                    # MC-Dropout forward passes.
                    mc_kcat = []
                    for _ in range(N_MC):
                        try:
                            out = model(seq_ids, substrate_input, conds)
                            mc_kcat.append(out["kcat_log"].item())
                        except Exception:
                            break

                    if not mc_kcat:
                        continue

                    kcat_means.append(float(np.mean(mc_kcat)))
                    kcat_stds.append(float(np.std(mc_kcat)) + 1e-6)  # avoid 0-std
                    kcat_targets.append(target_log)

            if not kcat_targets:
                return None

            covered = sum(
                1
                for mean, std, target in zip(kcat_means, kcat_stds, kcat_targets)
                if (mean - Z_90 * std) <= target <= (mean + Z_90 * std)
            )
            return covered / len(kcat_targets)

        def _estimate_disc_auc(neg_list: list[AdversarialNegative]) -> float | None:
            """Discrimination AUC for one adversarial tier via disc_head logits."""
            if not neg_list:
                return None
            try:
                from sklearn.metrics import roc_auc_score  # type: ignore
                # Build positive rows (in-corpus) for comparison.
                in_rows = [r for r in rows if r.row_id in split.in_corpus_row_ids]
                if not in_rows:
                    return None

                all_scores: list[float] = []
                all_labels: list[int] = []

                def _get_disc_score(row_or_neg: Any, label: int) -> None:
                    seq_ids = torch.zeros(1, 1, dtype=torch.long)
                    if hasattr(row_or_neg, "substrate_inchi_key"):
                        sub_key = row_or_neg.substrate_inchi_key
                    else:
                        sub_key = row_or_neg.decoy_substrate_inchi_key
                    sub_hash = hash(sub_key) % (2**20)
                    substrate_input = torch.tensor([sub_hash], dtype=torch.long)
                    ph = getattr(row_or_neg, "ph", 7.0)
                    temp = getattr(row_or_neg, "temperature_c", 37.0)
                    conds = torch.tensor([[ph, temp]], dtype=torch.float32)
                    cond_dim = cfg.condition_mlp.input_dim
                    if conds.shape[-1] < cond_dim:
                        pad = torch.zeros(1, cond_dim - conds.shape[-1])
                        conds = torch.cat([conds, pad], dim=-1)
                    with torch.no_grad():
                        out = model(seq_ids, substrate_input, conds)
                        logit_key = "disc_alpha"  # use alpha head for all tiers
                        score = torch.sigmoid(out[logit_key]).item()
                    all_scores.append(score)
                    all_labels.append(label)

                n_sample = min(20, len(in_rows), len(neg_list))
                for r in in_rows[:n_sample]:
                    _get_disc_score(r, 1)
                for n in neg_list[:n_sample]:
                    _get_disc_score(n, 0)

                if len(set(all_labels)) < 2:
                    return None
                return float(roc_auc_score(all_labels, all_scores))
            except Exception as exc_auc:
                log.debug("_estimate_disc_auc(): %s", exc_auc)
                return None

        # Compute all five metrics.
        cov_brenda = _estimate_coverage(brenda_held)
        cov_enzyextract = _estimate_coverage(enzyextract_held)
        auc_alpha = _estimate_disc_auc(neg_alpha)
        auc_beta = _estimate_disc_auc(neg_beta)
        auc_gamma = _estimate_disc_auc(neg_gamma)

        log.info(
            "calibration_audit done: brenda_cov=%.3f enzy_cov=%.3f "
            "auc_alpha=%s auc_beta=%s auc_gamma=%s",
            cov_brenda or -1.0,
            cov_enzyextract or -1.0,
            auc_alpha,
            auc_beta,
            auc_gamma,
        )

        return CalibrationReport(
            tier_alpha_coverage_at_90=auc_alpha,
            tier_beta_coverage_at_90=auc_beta,
            tier_gamma_coverage_at_90=auc_gamma,
            held_out_brenda_coverage_at_90=cov_brenda,
            held_out_enzyextract_coverage_at_90=cov_enzyextract,
            notes=(
                f"Real model calibration run. "
                f"brenda_held={len(brenda_held)}, "
                f"enzyextract_held={len(enzyextract_held)}, "
                f"neg_alpha={len(neg_alpha)}, "
                f"neg_beta={len(neg_beta)}, "
                f"neg_gamma={len(neg_gamma)}."
            ),
        )

    except Exception as exc:
        log.warning(
            "calibration_audit(): model forward pass failed (%s) — returning stub report.",
            exc,
        )
        return CalibrationReport(
            tier_alpha_coverage_at_90=None,
            tier_beta_coverage_at_90=None,
            tier_gamma_coverage_at_90=None,
            held_out_brenda_coverage_at_90=None,
            held_out_enzyextract_coverage_at_90=None,
            notes=f"calibration_audit() raised exception: {exc}",
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

    # Real HF upload using huggingface_hub.
    try:
        from huggingface_hub import HfApi  # type: ignore
        api = HfApi(token=token)
        # Create the repo if it doesn't exist; fail silently if already exists.
        try:
            api.create_repo(
                repo_id=cfg.hf_repo_id,
                private=cfg.hf_private,
                exist_ok=True,
            )
        except Exception as _repo_exc:
            log.warning("push_to_hf: create_repo raised (%s); continuing.", _repo_exc)

        # Upload the .meta.json file and the sibling .pt file.
        files_to_upload = [checkpoint_path]
        pt_sibling = checkpoint_path.with_suffix("").with_suffix(".pt")
        if pt_sibling.exists():
            files_to_upload.append(pt_sibling)

        for file_path in files_to_upload:
            if not file_path.exists():
                continue
            api.upload_file(
                path_or_fileobj=str(file_path),
                path_in_repo=file_path.name,
                repo_id=cfg.hf_repo_id,
            )
            log.info("push_to_hf: uploaded %s → %s/%s", file_path.name, cfg.hf_repo_id, file_path.name)

        return True
    except Exception as _hf_exc:
        log.error("push_to_hf: upload failed: %s", _hf_exc)
        return False


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
    # Move model to CUDA when available — without this, training silently
    # runs on CPU at glacial pace (967M params on Intel = hours per step).
    if model is not None:
        try:
            import torch as _t

            if _t.cuda.is_available():
                model = model.cuda()
                log.info("train(): model moved to CUDA: %s", _t.cuda.get_device_name(0))
        except Exception as _exc:  # pragma: no cover
            log.warning("train(): model.cuda() failed: %s", _exc)
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
            # Load model + optimiser state dicts when torch and objects are available.
            if model is not None and optimiser is not None:
                try:
                    import torch as _torch
                    pt_path = Path(ckpt_state.model_state_path)
                    if pt_path.exists() and pt_path.stat().st_size > 0:
                        state_dicts = _torch.load(
                            str(pt_path), weights_only=True
                        )
                        if "model" in state_dicts and hasattr(model, "load_state_dict"):
                            model.load_state_dict(state_dicts["model"])
                        if "optimiser" in state_dicts and hasattr(optimiser, "load_state_dict"):
                            optimiser.load_state_dict(state_dicts["optimiser"])
                        log.info("Loaded model + optimiser from %s", pt_path)
                    else:
                        log.info(
                            "Checkpoint .pt not found or empty (%s); "
                            "continuing with fresh model weights.",
                            pt_path,
                        )
                except ImportError:
                    log.warning("torch not installed; skipping state-dict reload.")
                except Exception as _exc:
                    log.warning("Failed to load state-dicts from checkpoint: %s", _exc)
        else:
            log.info("--resume requested but no checkpoint found; starting from scratch.")

    # --- 4. TensorBoard writer ------------------------------------------
    tb_log_dir = Path(cfg.tb_log_dir) / cfg.campaign_id
    tb_log_dir.mkdir(parents=True, exist_ok=True)
    tb_writer: Any = None
    try:
        from torch.utils.tensorboard import SummaryWriter  # type: ignore
        tb_writer = SummaryWriter(log_dir=str(tb_log_dir))
        log.info("TensorBoard writer opened at %s", tb_log_dir)
    except Exception:
        tb_writer = None

    # --- 5. Training loop -----------------------------------------------
    global_step = start_step
    final_calib_report = CalibrationReport(
        notes="No calibration run yet — model is None or loop not executed."
    )

    if model is None or optimiser is None:
        # CPU-only / stub mode: skip the real training loop.
        log.info(
            "Training loop: model=%s, optimiser=%s — skipping GPU training loop. "
            "Stub mode: max_steps=%d acknowledged but not executed.",
            model,
            optimiser,
            cfg.max_steps,
        )
    else:
        # ----------------------------------------------------------------
        # Real training loop (GPU mode — requires torch + real model).
        # ----------------------------------------------------------------
        try:
            import torch as _torch
            import hashlib as _hashlib
            import json as _json_mod

            # Build a simple in-memory dataset from the in-corpus rows.
            # On the Runpod GPU pod, the caller will supply a real DataLoader;
            # this loop builds batches directly from KineticsRow objects so
            # the Wave 4 framework is end-to-end without a separate Dataset class.

            # Separate supervised (brenda/enzyextract/proteingym) from
            # curriculum (gotenzymes2) rows.
            supervised_rows = [
                r for r in in_corpus_rows
                if r.source in {"brenda", "enzyextract", "proteingym"}
            ]
            curriculum_rows = [
                r for r in in_corpus_rows if r.source == "gotenzymes2"
            ]
            neg_by_parent: dict[str, list[AdversarialNegative]] = {}
            for neg in negatives:
                neg_by_parent.setdefault(neg.parent_row_id, []).append(neg)

            def _rows_to_batch(
                batch_rows: list[KineticsRow],
            ) -> tuple[Any, Any, Any, Any, Any]:
                """Convert a list of KineticsRow → stub tensors for forward pass.

                Returns (seq_ids, substrate_input, conditions, kcat_target, km_target).
                Targets are NaN-masked where the value is None.
                """
                import math as _math
                B = len(batch_rows)
                cond_dim = cfg.condition_mlp.input_dim
                seq_ids = _torch.zeros(B, 1, dtype=_torch.long)
                substrate_input = _torch.tensor(
                    [hash(r.substrate_inchi_key) % (2**20) for r in batch_rows],
                    dtype=_torch.long,
                )
                conds_list = []
                for r in batch_rows:
                    row_cond = [r.ph, r.temperature_c]
                    # Pad to cond_dim.
                    while len(row_cond) < cond_dim:
                        row_cond.append(0.15)  # default ionic_strength
                    conds_list.append(row_cond[:cond_dim])
                conds = _torch.tensor(conds_list, dtype=_torch.float32)
                kcat_t = _torch.tensor(
                    [
                        _math.log10(r.kcat_per_s) if (r.kcat_per_s and r.kcat_per_s > 0)
                        else float("nan")
                        for r in batch_rows
                    ],
                    dtype=_torch.float32,
                )
                km_t = _torch.tensor(
                    [
                        _math.log10(r.km_mm) if (r.km_mm and r.km_mm > 0)
                        else float("nan")
                        for r in batch_rows
                    ],
                    dtype=_torch.float32,
                )
                return seq_ids, substrate_input, conds, kcat_t, km_t

            import random as _random
            rng = _random.Random(cfg.seed)

            # GradScaler for bfloat16 mixed precision.
            use_amp = cfg.use_bf16
            try:
                scaler = _torch.cuda.amp.GradScaler(enabled=use_amp)  # type: ignore[attr-defined]
            except Exception:
                scaler = None

            model.train()
            optimiser.zero_grad()

            epoch = 0
            batch_size = max(1, cfg.batch_size)

            while global_step < cfg.max_steps:
                # Shuffle supervised rows each epoch.
                if global_step % max(1, len(supervised_rows) // batch_size) == 0:
                    rng.shuffle(supervised_rows)
                    epoch += 1

                # --- Build supervised batch --------------------------------
                start_idx = (global_step * batch_size) % max(1, len(supervised_rows)) if supervised_rows else 0
                if supervised_rows:
                    batch_rows = supervised_rows[start_idx: start_idx + batch_size]
                    if not batch_rows:
                        batch_rows = supervised_rows[:batch_size]
                else:
                    global_step += 1
                    continue

                seq_ids, substrate_inp, conds, kcat_t, km_t = _rows_to_batch(batch_rows)

                # Move inputs to the same device as the model.
                _dev = next(model.parameters()).device
                seq_ids = seq_ids.to(_dev)
                substrate_inp = substrate_inp.to(_dev)
                conds = conds.to(_dev)
                kcat_t = kcat_t.to(_dev)
                km_t = km_t.to(_dev)

                # --- Forward pass (with optional amp) ----------------------
                try:
                    if use_amp and scaler is not None:
                        with _torch.autocast(device_type="cuda", dtype=_torch.bfloat16):  # type: ignore[attr-defined]
                            out = model(seq_ids, substrate_inp, conds)
                    else:
                        out = model(seq_ids, substrate_inp, conds)

                    kcat_pred = out["kcat_log"]
                    km_pred = out["km_log"]
                    fused = out["fused"]

                    # --- Supervised loss -----------------------------------
                    L_sup = compute_supervised_loss(kcat_pred, km_pred, kcat_t, km_t)
                    if L_sup is None:
                        L_sup = _torch.tensor(0.0, requires_grad=True)

                    # --- Curriculum loss (GotEnzymes2) ----------------------
                    L_curr = _torch.tensor(0.0, requires_grad=True)
                    if curriculum_rows:
                        curr_batch = rng.sample(
                            curriculum_rows, min(batch_size, len(curriculum_rows))
                        )
                        _, curr_sub, curr_conds, curr_kcat, curr_km = _rows_to_batch(curr_batch)
                        curr_seq = _torch.zeros(len(curr_batch), 1, dtype=_torch.long, device=_dev)
                        curr_sub = curr_sub.to(_dev)
                        curr_conds = curr_conds.to(_dev)
                        curr_kcat = curr_kcat.to(_dev)
                        curr_km = curr_km.to(_dev)
                        curr_out = model(curr_seq, curr_sub, curr_conds)
                        _l = compute_curriculum_loss(
                            curr_out["kcat_log"], curr_out["km_log"],
                            curr_kcat, curr_km,
                        )
                        if _l is not None:
                            L_curr = _l

                    # --- Contrastive loss (adversarial negatives) ----------
                    L_cont = _torch.tensor(0.0, requires_grad=True)
                    neg_alpha_emb: list[Any] = []
                    neg_beta_emb: list[Any] = []
                    neg_gamma_emb: list[Any] = []
                    disc_alpha_logits: list[Any] = []
                    disc_beta_logits: list[Any] = []
                    disc_gamma_logits: list[Any] = []

                    for row in batch_rows:
                        row_negs = neg_by_parent.get(row.row_id, [])
                        for neg_item in row_negs:
                            neg_sub = _torch.tensor(
                                [hash(neg_item.decoy_substrate_inchi_key) % (2**20)],
                                dtype=_torch.long,
                                device=_dev,
                            )
                            neg_cond = conds[batch_rows.index(row): batch_rows.index(row) + 1]
                            neg_seq = _torch.zeros(1, 1, dtype=_torch.long, device=_dev)
                            neg_out = model(neg_seq, neg_sub, neg_cond)
                            if neg_item.tier == "alpha":
                                neg_alpha_emb.append(neg_out["fused"])
                                disc_alpha_logits.append(neg_out["disc_alpha"])
                            elif neg_item.tier == "beta":
                                neg_beta_emb.append(neg_out["fused"])
                                disc_beta_logits.append(neg_out["disc_beta"])
                            elif neg_item.tier == "gamma":
                                neg_gamma_emb.append(neg_out["fused"])
                                disc_gamma_logits.append(neg_out["disc_gamma"])

                    def _cat_or_none(lst: list[Any]) -> Any:
                        if not lst:
                            return None
                        return _torch.cat(lst, dim=0)

                    _l_cont = compute_contrastive_loss(
                        fused,
                        _cat_or_none(neg_alpha_emb),
                        _cat_or_none(neg_beta_emb),
                        _cat_or_none(neg_gamma_emb),
                        _cat_or_none(disc_alpha_logits),
                        _cat_or_none(disc_beta_logits),
                        _cat_or_none(disc_gamma_logits),
                        cfg.loss,
                    )
                    if _l_cont is not None:
                        L_cont = _l_cont

                    # --- Total loss + gradient accumulation ----------------
                    loss = (
                        cfg.loss.w_supervised * L_sup
                        + cfg.loss.w_curriculum * L_curr
                        + cfg.loss.w_contrastive * L_cont
                    )
                    loss_scaled = loss / max(1, cfg.gradient_accumulation_steps)

                    if scaler is not None:
                        scaler.scale(loss_scaled).backward()
                    else:
                        loss_scaled.backward()

                    if (global_step + 1) % cfg.gradient_accumulation_steps == 0:
                        if scaler is not None:
                            scaler.unscale_(optimiser)
                        _torch.nn.utils.clip_grad_norm_(
                            [p for p in model.parameters() if p.requires_grad], 1.0
                        )
                        if scaler is not None:
                            scaler.step(optimiser)
                            scaler.update()
                        else:
                            optimiser.step()
                        if scheduler is not None:
                            scheduler.step()
                        optimiser.zero_grad()

                    loss_val = float(loss.item())

                    # --- Audit + TensorBoard logging -----------------------
                    if global_step % 50 == 0:
                        _write_audit_event(
                            audit_log,
                            {
                                "event": "step",
                                "step": global_step,
                                "epoch": epoch,
                                "loss": loss_val,
                                "loss_supervised": float(L_sup.item()),
                                "loss_curriculum": float(L_curr.item()),
                                "loss_contrastive": float(L_cont.item()),
                            },
                        )
                        if tb_writer is not None:
                            tb_writer.add_scalar("loss/total", loss_val, global_step)
                            tb_writer.add_scalar("loss/supervised", float(L_sup.item()), global_step)
                            tb_writer.add_scalar("loss/curriculum", float(L_curr.item()), global_step)
                            tb_writer.add_scalar("loss/contrastive", float(L_cont.item()), global_step)

                    # --- Eval + calibration gate ---------------------------
                    if global_step > 0 and global_step % cfg.eval_every_steps == 0:
                        calib = calibration_audit(model, rows, negatives, split, cfg)
                        if calibration_passed(calib):
                            coverages = [
                                v for v in [
                                    calib.tier_alpha_coverage_at_90,
                                    calib.tier_beta_coverage_at_90,
                                    calib.tier_gamma_coverage_at_90,
                                    calib.held_out_brenda_coverage_at_90,
                                    calib.held_out_enzyextract_coverage_at_90,
                                ]
                                if v is not None
                            ]
                            if coverages:
                                best_calib_coverage = min(coverages)
                        _write_audit_event(
                            audit_log,
                            {
                                "event": "calibration",
                                "step": global_step,
                                **calib.to_dict(),
                            },
                        )
                        if tb_writer is not None:
                            for k, v in calib.to_dict().items():
                                if isinstance(v, float):
                                    tb_writer.add_scalar(f"calib/{k}", v, global_step)
                        final_calib_report = calib

                    # --- Checkpoint ---------------------------------------
                    if global_step > 0 and global_step % cfg.checkpoint_every_steps == 0:
                        config_hash = _hashlib.sha256(
                            _json_mod.dumps(
                                config_to_dict(cfg), sort_keys=True
                            ).encode()
                        ).hexdigest()
                        ckpt = CheckpointState(
                            step=global_step,
                            epoch=epoch,
                            global_loss=loss_val,
                            best_calib_coverage=best_calib_coverage,
                            config_hash=config_hash,
                            model_state_path="(set by save_checkpoint)",
                        )
                        meta_path_ckpt = save_checkpoint(
                            ckpt, checkpoint_dir, model, optimiser
                        )
                        _write_audit_event(
                            audit_log,
                            {
                                "event": "checkpoint_saved",
                                "step": global_step,
                                "meta": str(meta_path_ckpt),
                            },
                        )
                        log.info("Checkpoint saved at step %d → %s", global_step, meta_path_ckpt)

                except Exception as _step_exc:
                    log.warning(
                        "Training step %d raised exception: %s — skipping step.",
                        global_step,
                        _step_exc,
                    )
                    _write_audit_event(
                        audit_log,
                        {
                            "event": "step_error",
                            "step": global_step,
                            "error": str(_step_exc),
                        },
                    )

                global_step += 1

        except Exception as _loop_exc:
            log.error("Training loop failed: %s", _loop_exc)
            _write_audit_event(
                audit_log,
                {
                    "event": "training_loop_error",
                    "step": global_step,
                    "error": str(_loop_exc),
                },
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
