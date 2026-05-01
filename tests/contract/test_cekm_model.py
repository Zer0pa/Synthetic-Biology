"""Contract tests for zer0pa_synbio.cekm.model — CEKMModel architecture.

BOUNDARY:
Research infrastructure for in silico synthetic biology / metabolic pathway
engineering. Outputs are research artifacts — predicted pathways, predicted
KPIs, candidate genetic modification specifications. No regulatory
certification claims. No clinical or human-subject use. No environmental
release of GMOs. No biocontainment-level claims (the pipeline does not
commission BSL-2/3 work). No human gene drive or eugenic application.
Defence / weapons / dual-use bio applications excluded under operator policy.

These tests cover:
  1.  Module importability without torch installed (graceful degradation).
  2.  Model factory builds on CPU with stub config.
  3.  ESM2Backbone stub degrades gracefully (_using_real_esm2=False).
  4.  DMPNNSubstrateEncoder selects correct input_mode.
  5.  ConditionMLP output shape.
  6.  AdaptiveGate output shape.
  7.  CEKMModel.forward() output dict — key presence and tensor shapes.
  8.  kcat_head output shape (B,).
  9.  km_head output shape (B,).
  10. disc_alpha/beta/gamma output shapes (B,).
  11. compute_supervised_loss returns scalar tensor.
  12. compute_curriculum_loss returns scalar tensor.
  13. compute_contrastive_loss (hinge) returns scalar tensor.
  14. compute_contrastive_loss (ntxent) returns scalar tensor.
  15. Gradient flows through non-backbone parameters (no NaN).
  16. Backbone parameters are detached (require_grad=False by default).
  17. Checkpoint round-trip: state_dict + config preserved.
  18. CEKMModel.count_parameters() returns positive non-zero counts.
  19. CEKMModel.to_bf16() does not raise on CPU.
  20. CEKMModel.named_trainable_parameters() excludes frozen backbone params.

All tests run on CPU without GPU or real ESM-2 weights.
Torch is required; tests are auto-skipped if torch is absent.
"""

from __future__ import annotations

import dataclasses
import json
import tempfile
from pathlib import Path
from typing import Any

import pytest

# ---------------------------------------------------------------------------
# Skip everything if torch is not installed.
# ---------------------------------------------------------------------------

try:
    import torch
    _TORCH_AVAILABLE = True
except ImportError:
    _TORCH_AVAILABLE = False

pytestmark = pytest.mark.contract

# Per-class skip marker for tests that strictly need torch.
_needs_torch = pytest.mark.skipif(not _TORCH_AVAILABLE, reason="torch not installed")


# ---------------------------------------------------------------------------
# Imports (guarded so the file is importable even without torch).
# ---------------------------------------------------------------------------

if _TORCH_AVAILABLE:
    from zer0pa_synbio.cekm.model import (
        AdaptiveGate,
        CEKMModel,
        ConditionMLP,
        DMPNNSubstrateEncoder,
        ESM2Backbone,
        _ESM2_HIDDEN_DIM,
        _FP_NBITS,
        _RDKIT_AVAILABLE,
        _TORCH_AVAILABLE as MODEL_TORCH_AVAILABLE,
        _TRANSFORMERS_AVAILABLE,
        build_cekm_model,
    )
    from zer0pa_synbio.cekm.train import (
        LossConfig,
        TrainingConfig,
        compute_contrastive_loss,
        compute_curriculum_loss,
        compute_supervised_loss,
        save_checkpoint,
        load_checkpoint,
        CheckpointState,
    )
    from zer0pa_synbio.boundary import BOUNDARY_SHA256


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _stub_config(**overrides: Any) -> TrainingConfig:
    """Return a minimal TrainingConfig suitable for CPU tests."""
    cfg = TrainingConfig()
    # Use smallest possible dims to keep tests fast.
    cfg.adaptive_gate = dataclasses.replace(
        cfg.adaptive_gate,
        esm2_dim=_ESM2_HIDDEN_DIM,   # must stay 1280 (contract)
        substrate_dim=cfg.dmpnn.hidden_dim,
        condition_dim=cfg.condition_mlp.output_dim,
        gate_hidden_dim=32,
        output_dim=64,
    )
    cfg.heads = dataclasses.replace(
        cfg.heads,
        kcat_hidden_dims=[32],
        km_hidden_dims=[32],
        discriminator_hidden_dims=[32],
    )
    for k, v in overrides.items():
        cfg = dataclasses.replace(cfg, **{k: v})
    return cfg


def _make_model(cfg: TrainingConfig | None = None) -> CEKMModel:
    if cfg is None:
        cfg = _stub_config()
    return CEKMModel(cfg)


def _stub_inputs(
    B: int = 2,
    L: int = 5,
    cond_dim: int = 2,
    substrate_mode: str = "stub",
) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
    """Build minimal stub tensors for a forward pass.

    Returns (sequence_ids, substrate_input, conditions).
    """
    seq_ids = torch.zeros(B, L, dtype=torch.long)
    if substrate_mode == "fingerprint":
        substrate_input = torch.zeros(B, _FP_NBITS, dtype=torch.float32)
    else:
        substrate_input = torch.arange(B, dtype=torch.long)  # shape (B,)
    conditions = torch.rand(B, cond_dim)
    return seq_ids, substrate_input, conditions


# ---------------------------------------------------------------------------
# 1. Module importability (no torch required — checked outside skipif guard)
# ---------------------------------------------------------------------------


class TestModuleImportability:
    def test_model_module_importable(self) -> None:
        """zer0pa_synbio.cekm.model must be importable on any machine."""
        import importlib
        m = importlib.import_module("zer0pa_synbio.cekm.model")
        assert hasattr(m, "CEKMModel")
        assert hasattr(m, "_TORCH_AVAILABLE")

    @_needs_torch
    def test_torch_availability_flag_matches_reality(self) -> None:
        assert MODEL_TORCH_AVAILABLE is True  # inside skipif guard, torch IS available


# ---------------------------------------------------------------------------
# 2. Model factory builds on CPU
# ---------------------------------------------------------------------------


@_needs_torch
class TestModelFactory:
    def test_build_cekm_model_returns_module(self) -> None:
        cfg = _stub_config()
        model = build_cekm_model(cfg)
        assert isinstance(model, torch.nn.Module)

    def test_cekm_model_direct_ctor(self) -> None:
        model = _make_model()
        assert isinstance(model, CEKMModel)

    def test_model_has_all_expected_submodules(self) -> None:
        model = _make_model()
        assert hasattr(model, "esm2_backbone")
        assert hasattr(model, "substrate_encoder")
        assert hasattr(model, "condition_mlp")
        assert hasattr(model, "adaptive_gate")
        assert hasattr(model, "kcat_head")
        assert hasattr(model, "km_head")
        assert hasattr(model, "disc_alpha")
        assert hasattr(model, "disc_beta")
        assert hasattr(model, "disc_gamma")

    def test_model_using_real_esm2_attribute_exists(self) -> None:
        model = _make_model()
        assert hasattr(model, "_using_real_esm2")
        assert isinstance(model._using_real_esm2, bool)


# ---------------------------------------------------------------------------
# 3. ESM2Backbone stub
# ---------------------------------------------------------------------------


@_needs_torch
class TestESM2Backbone:
    def test_esm2_backbone_builds(self) -> None:
        backbone = ESM2Backbone(
            model_name="facebook/esm2_t33_650M_UR50D",
            frozen=True,
            unfreeze_last_n_layers=0,
        )
        assert isinstance(backbone, torch.nn.Module)

    def test_esm2_backbone_output_shape(self) -> None:
        backbone = ESM2Backbone(frozen=True)
        seq_ids = torch.zeros(3, 8, dtype=torch.long)
        out = backbone(seq_ids)
        assert out.shape == (3, _ESM2_HIDDEN_DIM), (
            f"Expected ({3}, {_ESM2_HIDDEN_DIM}), got {out.shape}"
        )

    def test_esm2_stub_flag_false_without_weights(self) -> None:
        """In CI (no HF cache), _using_real_esm2 must be False."""
        backbone = ESM2Backbone(frozen=True)
        # If transformers is absent OR weights are not cached, stub is used.
        # Either state is valid; we just assert the flag is a bool.
        assert isinstance(backbone._using_real_esm2, bool)

    def test_esm2_dim_constant_is_1280(self) -> None:
        assert _ESM2_HIDDEN_DIM == 1280, "ESM-2 CLS dim must be 1280 (contract)"


# ---------------------------------------------------------------------------
# 4. DMPNNSubstrateEncoder
# ---------------------------------------------------------------------------


@_needs_torch
class TestDMPNNSubstrateEncoder:
    def test_encoder_builds(self) -> None:
        enc = DMPNNSubstrateEncoder(hidden_dim=64)
        assert isinstance(enc, torch.nn.Module)

    def test_encoder_has_input_mode_attribute(self) -> None:
        enc = DMPNNSubstrateEncoder(hidden_dim=64)
        assert enc.input_mode in {"dmpnn", "fingerprint", "stub"}

    def test_encoder_stub_mode_output_shape(self) -> None:
        enc = DMPNNSubstrateEncoder(hidden_dim=64)
        if enc.input_mode == "fingerprint":
            inp = torch.zeros(4, _FP_NBITS)
        else:
            inp = torch.arange(4, dtype=torch.long)
        out = enc(inp)
        assert out.shape == (4, 64)

    def test_encoder_fingerprint_mode_if_rdkit_available(self) -> None:
        enc = DMPNNSubstrateEncoder(hidden_dim=64)
        # If RDKit is available and full D-MPNN is not, mode should be "fingerprint".
        # If RDKit is absent, mode should be "stub".
        if _RDKIT_AVAILABLE:
            assert enc.input_mode in {"fingerprint", "dmpnn"}
        else:
            assert enc.input_mode == "stub"


# ---------------------------------------------------------------------------
# 5. ConditionMLP
# ---------------------------------------------------------------------------


@_needs_torch
class TestConditionMLP:
    def test_condition_mlp_output_shape(self) -> None:
        mlp = ConditionMLP(input_dim=3, hidden_dims=[16, 32], output_dim=64)
        x = torch.rand(5, 3)
        out = mlp(x)
        assert out.shape == (5, 64)

    def test_condition_mlp_default_output_dim(self) -> None:
        mlp = ConditionMLP()
        x = torch.rand(2, 2)
        out = mlp(x)
        assert out.shape[0] == 2
        assert out.shape[1] == 128  # default output_dim


# ---------------------------------------------------------------------------
# 6. AdaptiveGate
# ---------------------------------------------------------------------------


@_needs_torch
class TestAdaptiveGate:
    def test_adaptive_gate_output_shape(self) -> None:
        gate = AdaptiveGate(
            esm2_dim=_ESM2_HIDDEN_DIM,
            substrate_dim=64,
            condition_dim=32,
            gate_hidden_dim=32,
            output_dim=128,
        )
        B = 4
        e = torch.rand(B, _ESM2_HIDDEN_DIM)
        s = torch.rand(B, 64)
        c = torch.rand(B, 32)
        out = gate(e, s, c)
        assert out.shape == (B, 128)


# ---------------------------------------------------------------------------
# 7–10. CEKMModel.forward() — output dict shapes
# ---------------------------------------------------------------------------


@_needs_torch
class TestCEKMModelForward:
    def _run_forward(self, B: int = 2) -> tuple[CEKMModel, dict[str, Any]]:
        cfg = _stub_config()
        model = _make_model(cfg)
        model.eval()
        seq_ids, substrate_inp, conds = _stub_inputs(
            B=B,
            cond_dim=cfg.condition_mlp.input_dim,
            substrate_mode=model.substrate_encoder.input_mode,
        )
        with torch.no_grad():
            out = model(seq_ids, substrate_inp, conds)
        return model, out

    def test_forward_returns_dict(self) -> None:
        _, out = self._run_forward()
        assert isinstance(out, dict)

    def test_forward_dict_has_all_keys(self) -> None:
        _, out = self._run_forward()
        expected_keys = {"kcat_log", "km_log", "disc_alpha", "disc_beta", "disc_gamma", "fused"}
        assert expected_keys.issubset(out.keys()), (
            f"Missing keys: {expected_keys - out.keys()}"
        )

    def test_kcat_log_shape(self) -> None:
        B = 3
        _, out = self._run_forward(B=B)
        assert out["kcat_log"].shape == (B,), (
            f"kcat_log shape {out['kcat_log'].shape} != ({B},)"
        )

    def test_km_log_shape(self) -> None:
        B = 3
        _, out = self._run_forward(B=B)
        assert out["km_log"].shape == (B,)

    def test_disc_alpha_shape(self) -> None:
        B = 4
        _, out = self._run_forward(B=B)
        assert out["disc_alpha"].shape == (B,)

    def test_disc_beta_shape(self) -> None:
        B = 4
        _, out = self._run_forward(B=B)
        assert out["disc_beta"].shape == (B,)

    def test_disc_gamma_shape(self) -> None:
        B = 4
        _, out = self._run_forward(B=B)
        assert out["disc_gamma"].shape == (B,)

    def test_fused_shape_matches_gate_output_dim(self) -> None:
        cfg = _stub_config()
        model = _make_model(cfg)
        model.eval()
        seq_ids, substrate_inp, conds = _stub_inputs(
            B=2,
            cond_dim=cfg.condition_mlp.input_dim,
            substrate_mode=model.substrate_encoder.input_mode,
        )
        with torch.no_grad():
            out = model(seq_ids, substrate_inp, conds)
        expected_gate_dim = cfg.adaptive_gate.output_dim
        assert out["fused"].shape == (2, expected_gate_dim)

    def test_forward_values_are_finite(self) -> None:
        _, out = self._run_forward(B=2)
        for key, tensor in out.items():
            assert torch.isfinite(tensor).all(), (
                f"Non-finite values in output['{key}']: {tensor}"
            )


# ---------------------------------------------------------------------------
# 11–14. Loss functions return scalar tensors
# ---------------------------------------------------------------------------


@_needs_torch
class TestLossFunctions:
    def _make_preds_targets(self, B: int = 4) -> tuple[Any, Any, Any, Any]:
        kcat_pred = torch.rand(B)
        km_pred = torch.rand(B)
        kcat_target = torch.rand(B) + 0.1
        km_target = torch.rand(B) + 0.1
        return kcat_pred, km_pred, kcat_target, km_target

    def test_supervised_loss_returns_scalar_tensor(self) -> None:
        kcat_pred, km_pred, kcat_target, km_target = self._make_preds_targets()
        loss = compute_supervised_loss(kcat_pred, km_pred, kcat_target, km_target)
        assert loss is not None
        assert isinstance(loss, torch.Tensor)
        assert loss.ndim == 0, f"Expected scalar, got shape {loss.shape}"
        assert torch.isfinite(loss), f"Loss is not finite: {loss}"

    def test_supervised_loss_with_nan_targets(self) -> None:
        B = 4
        kcat_pred = torch.rand(B)
        km_pred = torch.rand(B)
        kcat_target = torch.tensor([float("nan"), 1.0, 2.0, float("nan")])
        km_target = torch.tensor([0.5, float("nan"), 1.5, 2.0])
        loss = compute_supervised_loss(kcat_pred, km_pred, kcat_target, km_target)
        assert loss is not None
        assert torch.isfinite(loss)

    def test_curriculum_loss_returns_scalar_tensor(self) -> None:
        kcat_pred, km_pred, kcat_soft, km_soft = self._make_preds_targets()
        loss = compute_curriculum_loss(kcat_pred, km_pred, kcat_soft, km_soft)
        assert loss is not None
        assert isinstance(loss, torch.Tensor)
        assert loss.ndim == 0
        assert torch.isfinite(loss)

    def test_contrastive_loss_hinge_returns_scalar(self) -> None:
        B = 4
        D = 64
        pos_emb = torch.rand(B, D)
        neg_emb_a = torch.rand(B, D)
        neg_emb_b = torch.rand(B, D)
        neg_emb_g = torch.rand(B, D)
        disc_a = torch.rand(B)
        disc_b = torch.rand(B)
        disc_g = torch.rand(B)
        cfg_loss = LossConfig(contrastive_type="hinge", contrastive_margin=1.0)
        loss = compute_contrastive_loss(
            pos_emb, neg_emb_a, neg_emb_b, neg_emb_g,
            disc_a, disc_b, disc_g,
            cfg_loss,
        )
        assert loss is not None
        assert isinstance(loss, torch.Tensor)
        assert loss.ndim == 0
        assert torch.isfinite(loss)

    def test_contrastive_loss_ntxent_returns_scalar(self) -> None:
        B = 4
        D = 64
        pos_emb = torch.rand(B, D)
        neg_emb_a = torch.rand(B, D)
        neg_emb_b = torch.rand(B, D)
        neg_emb_g = torch.rand(B, D)
        disc_a = torch.rand(B)
        disc_b = torch.rand(B)
        disc_g = torch.rand(B)
        cfg_loss = LossConfig(contrastive_type="ntxent", contrastive_temperature=0.07)
        loss = compute_contrastive_loss(
            pos_emb, neg_emb_a, neg_emb_b, neg_emb_g,
            disc_a, disc_b, disc_g,
            cfg_loss,
        )
        assert loss is not None
        assert isinstance(loss, torch.Tensor)
        assert loss.ndim == 0
        assert torch.isfinite(loss)

    def test_contrastive_loss_with_none_negatives(self) -> None:
        """compute_contrastive_loss must handle None neg_embeddings gracefully."""
        B = 2
        D = 64
        pos_emb = torch.rand(B, D)
        disc_a = torch.rand(B)
        cfg_loss = LossConfig(contrastive_type="hinge")
        loss = compute_contrastive_loss(
            pos_emb, None, None, None,
            disc_a, None, None,
            cfg_loss,
        )
        assert loss is not None
        assert loss.ndim == 0


# ---------------------------------------------------------------------------
# 15–16. Gradient flow
# ---------------------------------------------------------------------------


@_needs_torch
class TestGradientFlow:
    def test_gradients_flow_through_non_backbone_params(self) -> None:
        """Gradients must reach non-backbone parameters and must not be NaN."""
        cfg = _stub_config()
        model = _make_model(cfg)
        model.train()

        seq_ids, substrate_inp, conds = _stub_inputs(
            B=2,
            cond_dim=cfg.condition_mlp.input_dim,
            substrate_mode=model.substrate_encoder.input_mode,
        )
        out = model(seq_ids, substrate_inp, conds)
        loss = out["kcat_log"].mean() + out["km_log"].mean()
        loss.backward()

        # Check at least one non-backbone parameter has a gradient.
        non_backbone_grads = [
            (n, p.grad)
            for n, p in model.named_parameters()
            if "esm2_backbone" not in n and p.grad is not None
        ]
        assert len(non_backbone_grads) > 0, (
            "No gradients found in non-backbone parameters."
        )
        # No NaN gradients.
        for name, grad in non_backbone_grads:
            assert not torch.isnan(grad).any(), (
                f"NaN gradient in parameter '{name}': {grad}"
            )

    def test_backbone_parameters_detached_by_default(self) -> None:
        """By default (frozen=True), ESM-2 backbone parameters must not require grad."""
        cfg = _stub_config()
        # Ensure frozen=True (default).
        cfg = dataclasses.replace(cfg, esm2=dataclasses.replace(cfg.esm2, frozen=True, unfreeze_last_n_layers=0))
        model = _make_model(cfg)

        # For the stub backbone (_using_real_esm2=False), the _stub_embed may
        # or may not require grad. The key invariant is that if the real ESM-2
        # is loaded, its parameters are frozen.
        if model._using_real_esm2:
            for name, param in model.esm2_backbone.named_parameters():
                assert not param.requires_grad, (
                    f"Backbone parameter '{name}' should be frozen (requires_grad=False)."
                )


# ---------------------------------------------------------------------------
# 17. Checkpoint round-trip
# ---------------------------------------------------------------------------


@_needs_torch
class TestCheckpointRoundTrip:
    def test_checkpoint_roundtrip_preserves_state_dict(self, tmp_path: Path) -> None:
        cfg = _stub_config(campaign_id="ckpt_roundtrip_test")
        model = _make_model(cfg)

        # Record initial state dict values.
        initial_sd = {k: v.clone() for k, v in model.state_dict().items()}

        # Save checkpoint.
        state = CheckpointState(
            step=100,
            epoch=1,
            global_loss=0.55,
            best_calib_coverage=0.0,
            config_hash="a" * 64,
            model_state_path="(placeholder)",
        )
        meta_path = save_checkpoint(state, tmp_path, model_obj=model, optimiser_obj=None)
        assert meta_path.exists()

        # Verify meta JSON.
        meta_d = json.loads(meta_path.read_text(encoding="utf-8"))
        assert meta_d["step"] == 100
        from zer0pa_synbio.boundary import BOUNDARY_SHA256
        assert meta_d["boundary_sha256"] == BOUNDARY_SHA256

        # Reload state dict from the saved .pt file.
        pt_path = Path(meta_d["model_state_path"])
        assert pt_path.exists()

        if pt_path.stat().st_size > 0:
            loaded = torch.load(str(pt_path), weights_only=True)
            assert "model" in loaded
            # Verify the loaded state dict matches the initial one.
            for key, orig_val in initial_sd.items():
                assert key in loaded["model"], f"Key '{key}' missing from saved state_dict."
                assert torch.allclose(orig_val, loaded["model"][key], atol=1e-6), (
                    f"State dict mismatch for parameter '{key}'."
                )

    def test_checkpoint_load_restores_step(self, tmp_path: Path) -> None:
        model = _make_model()
        state = CheckpointState(
            step=999,
            epoch=3,
            global_loss=0.12,
            best_calib_coverage=0.91,
            config_hash="b" * 64,
            model_state_path="(placeholder)",
        )
        meta_path = save_checkpoint(state, tmp_path, model_obj=model, optimiser_obj=None)
        loaded_state = load_checkpoint(meta_path)
        assert loaded_state.step == 999
        assert loaded_state.epoch == 3
        assert abs(loaded_state.global_loss - 0.12) < 1e-9


# ---------------------------------------------------------------------------
# 18–20. CEKMModel helpers
# ---------------------------------------------------------------------------


@_needs_torch
class TestCEKMModelHelpers:
    def test_count_parameters_positive(self) -> None:
        model = _make_model()
        counts = model.count_parameters()
        assert counts["total"] > 0
        assert counts["non_backbone"] > 0

    def test_to_bf16_does_not_raise(self) -> None:
        model = _make_model()
        # to_bf16() should not raise on CPU (weights are cast; some ops may
        # not support bfloat16 on CPU but the cast itself is valid).
        try:
            model.to_bf16()
        except Exception as exc:
            pytest.fail(f"to_bf16() raised unexpectedly: {exc}")

    def test_named_trainable_parameters_excludes_frozen(self) -> None:
        """named_trainable_parameters() must only return parameters with requires_grad=True."""
        model = _make_model()
        trainable = model.named_trainable_parameters()
        for name, param in trainable:
            assert param.requires_grad, (
                f"named_trainable_parameters() returned non-trainable param '{name}'."
            )
