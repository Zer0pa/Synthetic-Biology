"""Contract tests for zer0pa_synbio.cekm.train — scaffolding validation.

BOUNDARY:
Research infrastructure for in silico synthetic biology / metabolic pathway
engineering. Outputs are research artifacts — predicted pathways, predicted
KPIs, candidate genetic modification specifications. No regulatory
certification claims. No clinical or human-subject use. No environmental
release of GMOs. No biocontainment-level claims (the pipeline does not
commission BSL-2/3 work). No human gene drive or eugenic application.
Defence / weapons / dual-use bio applications excluded under operator policy.

These tests cover:
  1. Config loader — YAML round-trip, defaults, unknown-key tolerance.
  2. Dataclass shapes — field presence, type guards, default values.
  3. Checkpoint state-dict round-trip — JSON serialise → deserialise →
     field equality, boundary tamper detection.
  4. Corpus + split wiring — build_corpus_and_split with a synthetic slice,
     decoy-pool fallback.
  5. train() skeleton — does NOT execute the real training loop (stub model);
     validates that all hooks (corpus, split, negatives, audit log, summary
     schema) fire correctly.
  6. CLI smoke-test subcommand — invoked via click's test runner.
  7. Calibration gate logic — calibration_passed() with None / float values.
  8. HF push skip — silently skips when HF_TOKEN is absent.

NOT covered here (Wave 4 responsibility):
  - Actual model forward pass (torch.nn.Module).
  - Real loss computation.
  - Real calibration metric values.
  - DataLoader integration.
  - TensorBoard SummaryWriter.
"""

from __future__ import annotations

import dataclasses
import json
import os
import tempfile
from pathlib import Path
from typing import Any

import pytest
import yaml
from click.testing import CliRunner

from zer0pa_synbio.boundary import BOUNDARY_SHA256
from zer0pa_synbio.cekm import CorpusSlice, KineticsRow
from zer0pa_synbio.cekm.train import (
    AdaptiveGateConfig,
    CalibrationReport,
    CheckpointState,
    ConditionMLPConfig,
    DMPNNConfig,
    ESM2Config,
    HeadsConfig,
    LossConfig,
    TrainingConfig,
    build_corpus_and_split,
    build_decoy_pool,
    calibration_audit,
    calibration_passed,
    cekm_group,
    checkpoint_state_from_dict,
    checkpoint_state_to_dict,
    config_to_dict,
    load_config,
    load_checkpoint,
    push_to_hf,
    save_checkpoint,
    train,
)

pytestmark = pytest.mark.contract


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _minimal_brenda_slice(n: int = 10) -> CorpusSlice:
    return CorpusSlice(
        source="brenda",
        license_class="A",
        rows=[
            KineticsRow(
                enzyme_uniprot_id=f"P{i:05d}",
                substrate_inchi_key=f"S{i:03d}",
                organism_taxonomy_id=562,
                temperature_c=37.0,
                ph=7.0,
                kcat_per_s=10.0 + i,
                km_mm=0.1 + i * 0.01,
                source="brenda",
            )
            for i in range(n)
        ],
    )


def _minimal_config(**overrides: Any) -> TrainingConfig:
    return dataclasses.replace(TrainingConfig(), **overrides)


# ---------------------------------------------------------------------------
# 1. Config dataclass shapes
# ---------------------------------------------------------------------------


class TestConfigDataclassShapes:
    def test_training_config_has_required_fields(self) -> None:
        cfg = TrainingConfig()
        # Core training fields
        assert hasattr(cfg, "campaign_id")
        assert hasattr(cfg, "seed")
        assert hasattr(cfg, "batch_size")
        assert hasattr(cfg, "gradient_accumulation_steps")
        assert hasattr(cfg, "learning_rate")
        assert hasattr(cfg, "weight_decay")
        assert hasattr(cfg, "warmup_steps")
        assert hasattr(cfg, "max_steps")
        assert hasattr(cfg, "eval_every_steps")
        assert hasattr(cfg, "checkpoint_every_steps")
        # Precision flags
        assert hasattr(cfg, "use_bf16")
        assert hasattr(cfg, "use_flash_attention_2")
        # Directories
        assert hasattr(cfg, "checkpoint_dir")
        assert hasattr(cfg, "tb_log_dir")
        # HF
        assert hasattr(cfg, "hf_repo_id")
        assert hasattr(cfg, "hf_private")
        # Sub-configs
        assert hasattr(cfg, "esm2")
        assert hasattr(cfg, "dmpnn")
        assert hasattr(cfg, "condition_mlp")
        assert hasattr(cfg, "adaptive_gate")
        assert hasattr(cfg, "heads")
        assert hasattr(cfg, "loss")

    def test_esm2_config_defaults(self) -> None:
        c = ESM2Config()
        assert c.model_name == "facebook/esm2_t33_650M_UR50D"
        assert c.frozen is True
        assert c.unfreeze_last_n_layers == 0

    def test_dmpnn_config_defaults(self) -> None:
        c = DMPNNConfig()
        assert c.hidden_dim == 300
        assert c.depth == 3
        assert c.aggregation == "mean"

    def test_condition_mlp_config_defaults(self) -> None:
        c = ConditionMLPConfig()
        assert c.input_dim == 2
        assert c.output_dim == 128

    def test_adaptive_gate_config_defaults(self) -> None:
        c = AdaptiveGateConfig()
        # ESM-2 650M CLS dim must be 1280
        assert c.esm2_dim == 1280
        # substrate_dim must match DMPNN hidden_dim default
        assert c.substrate_dim == DMPNNConfig().hidden_dim
        # condition_dim must match ConditionMLP output_dim default
        assert c.condition_dim == ConditionMLPConfig().output_dim

    def test_heads_config_defaults(self) -> None:
        c = HeadsConfig()
        assert c.n_discriminator_heads == 3  # one per tier α/β/γ

    def test_loss_config_defaults(self) -> None:
        c = LossConfig()
        assert c.w_supervised > c.w_curriculum  # supervised has higher weight
        assert c.w_contrastive > 0
        assert c.contrastive_type in {"hinge", "ntxent"}

    def test_training_config_defaults_hf_repo(self) -> None:
        cfg = TrainingConfig()
        assert cfg.hf_repo_id == "Architect-Prime/synbio-cekm-v0.1"
        assert cfg.hf_private is True

    def test_training_config_holdout_defaults(self) -> None:
        cfg = TrainingConfig()
        assert 0.10 <= cfg.holdout_fraction <= 0.20  # PRD §12.3: 10-20%
        assert cfg.enzyextract_holdout_full is True


# ---------------------------------------------------------------------------
# 2. Config loader (YAML round-trip)
# ---------------------------------------------------------------------------


class TestConfigLoader:
    def test_load_minimal_yaml(self, tmp_path: Path) -> None:
        data = {
            "campaign_id": "test_campaign",
            "max_steps": 100,
            "batch_size": 16,
        }
        cfg_path = tmp_path / "config.yaml"
        cfg_path.write_text(yaml.dump(data), encoding="utf-8")
        cfg = load_config(cfg_path)
        assert cfg.campaign_id == "test_campaign"
        assert cfg.max_steps == 100
        assert cfg.batch_size == 16
        # Defaults preserved for unspecified fields.
        assert cfg.seed == TrainingConfig().seed

    def test_load_nested_yaml(self, tmp_path: Path) -> None:
        data = {
            "esm2": {
                "frozen": False,
                "unfreeze_last_n_layers": 4,
            },
            "loss": {
                "w_supervised": 2.0,
                "contrastive_type": "ntxent",
            },
        }
        cfg_path = tmp_path / "config.yaml"
        cfg_path.write_text(yaml.dump(data), encoding="utf-8")
        cfg = load_config(cfg_path)
        assert cfg.esm2.frozen is False
        assert cfg.esm2.unfreeze_last_n_layers == 4
        assert cfg.loss.w_supervised == 2.0
        assert cfg.loss.contrastive_type == "ntxent"

    def test_load_unknown_keys_ignored(self, tmp_path: Path) -> None:
        data = {
            "campaign_id": "forward_compat",
            "some_future_key_not_in_dataclass": "should_be_silently_ignored",
        }
        cfg_path = tmp_path / "config.yaml"
        cfg_path.write_text(yaml.dump(data), encoding="utf-8")
        # Must not raise.
        cfg = load_config(cfg_path)
        assert cfg.campaign_id == "forward_compat"

    def test_empty_yaml_loads_defaults(self, tmp_path: Path) -> None:
        cfg_path = tmp_path / "empty.yaml"
        cfg_path.write_text("", encoding="utf-8")
        cfg = load_config(cfg_path)
        assert cfg == TrainingConfig()

    def test_config_to_dict_round_trips(self) -> None:
        cfg = TrainingConfig(campaign_id="roundtrip_test", max_steps=42)
        d = config_to_dict(cfg)
        assert d["campaign_id"] == "roundtrip_test"
        assert d["max_steps"] == 42
        # Nested sub-configs serialised as dicts.
        assert isinstance(d["esm2"], dict)
        assert "model_name" in d["esm2"]
        assert isinstance(d["loss"], dict)
        assert "w_supervised" in d["loss"]

    def test_config_to_dict_is_json_serialisable(self) -> None:
        cfg = TrainingConfig()
        d = config_to_dict(cfg)
        # Must not raise.
        serialised = json.dumps(d)
        assert len(serialised) > 0


# ---------------------------------------------------------------------------
# 3. CheckpointState round-trip
# ---------------------------------------------------------------------------


class TestCheckpointStateRoundTrip:
    def _make_state(self, step: int = 500) -> CheckpointState:
        return CheckpointState(
            step=step,
            epoch=1,
            global_loss=0.42,
            best_calib_coverage=0.91,
            config_hash="a" * 64,
            model_state_path="/tmp/ckpt_step500.pt",
        )

    def test_to_dict_has_boundary_sha256(self) -> None:
        state = self._make_state()
        d = checkpoint_state_to_dict(state)
        assert d["boundary_sha256"] == BOUNDARY_SHA256

    def test_from_dict_round_trip(self) -> None:
        state = self._make_state(step=999)
        d = checkpoint_state_to_dict(state)
        restored = checkpoint_state_from_dict(d)
        assert restored.step == 999
        assert restored.epoch == 1
        assert abs(restored.global_loss - 0.42) < 1e-9
        assert abs(restored.best_calib_coverage - 0.91) < 1e-9
        assert restored.config_hash == "a" * 64
        assert restored.boundary_sha256 == BOUNDARY_SHA256

    def test_from_dict_json_round_trip(self) -> None:
        state = self._make_state()
        d = checkpoint_state_to_dict(state)
        # Serialise to JSON string and back.
        json_str = json.dumps(d)
        d2 = json.loads(json_str)
        restored = checkpoint_state_from_dict(d2)
        assert restored.step == state.step
        assert restored.boundary_sha256 == BOUNDARY_SHA256

    def test_save_and_load_checkpoint(self, tmp_path: Path) -> None:
        state = self._make_state(step=1000)
        meta_path = save_checkpoint(state, tmp_path, model_obj=None, optimiser_obj=None)
        assert meta_path.exists()
        # Verify the meta JSON is parseable.
        loaded_d = json.loads(meta_path.read_text(encoding="utf-8"))
        assert loaded_d["step"] == 1000
        assert loaded_d["boundary_sha256"] == BOUNDARY_SHA256

    def test_load_checkpoint_boundary_tamper_fails(self, tmp_path: Path) -> None:
        state = self._make_state(step=50)
        meta_path = save_checkpoint(state, tmp_path, model_obj=None, optimiser_obj=None)
        # Tamper: overwrite boundary_sha256 with garbage.
        d = json.loads(meta_path.read_text(encoding="utf-8"))
        d["boundary_sha256"] = "0" * 64
        meta_path.write_text(json.dumps(d), encoding="utf-8")
        with pytest.raises(ValueError, match="boundary SHA256 mismatch"):
            load_checkpoint(meta_path)

    def test_load_checkpoint_clean(self, tmp_path: Path) -> None:
        state = self._make_state(step=200)
        meta_path = save_checkpoint(state, tmp_path, model_obj=None, optimiser_obj=None)
        loaded = load_checkpoint(meta_path)
        assert loaded.step == 200
        assert loaded.boundary_sha256 == BOUNDARY_SHA256

    def test_checkpoint_filename_contains_step(self, tmp_path: Path) -> None:
        state = self._make_state(step=12345)
        meta_path = save_checkpoint(state, tmp_path, model_obj=None, optimiser_obj=None)
        assert "12345" in meta_path.name


# ---------------------------------------------------------------------------
# 4. Corpus + split wiring
# ---------------------------------------------------------------------------


class TestCorpusAndSplit:
    def test_build_corpus_and_split_counts(self) -> None:
        cfg = _minimal_config(holdout_fraction=0.15, enzyextract_holdout_full=False, seed=42)
        slices = [_minimal_brenda_slice(n=50)]
        rows, split = build_corpus_and_split(cfg, slices)
        assert len(rows) == 50
        assert len(split.in_corpus_row_ids) + len(split.held_out_row_ids) == 50

    def test_build_corpus_enzyextract_fully_held_out(self) -> None:
        enz_slice = CorpusSlice(
            source="enzyextract",
            license_class="A",
            rows=[
                KineticsRow(
                    enzyme_uniprot_id=f"Q{i:05d}",
                    substrate_inchi_key=f"DM{i:03d}",
                    organism_taxonomy_id=562,
                    temperature_c=30.0,
                    ph=6.5,
                    kcat_per_s=5.0,
                    km_mm=0.2,
                    source="enzyextract",
                )
                for i in range(15)
            ],
        )
        cfg = _minimal_config(enzyextract_holdout_full=True, seed=0)
        rows, split = build_corpus_and_split(cfg, [enz_slice])
        assert len(split.held_out_row_ids) == 15
        assert len(split.in_corpus_row_ids) == 0

    def test_build_corpus_class_d_rejected(self) -> None:
        bad_slice = CorpusSlice(source="brenda", license_class="D", rows=[])
        cfg = _minimal_config()
        with pytest.raises(ValueError, match="Class D/E"):
            build_corpus_and_split(cfg, [bad_slice])

    def test_build_corpus_class_e_rejected(self) -> None:
        bad_slice = CorpusSlice(source="brenda", license_class="E", rows=[])
        cfg = _minimal_config()
        with pytest.raises(ValueError, match="Class D/E"):
            build_corpus_and_split(cfg, [bad_slice])

    def test_build_corpus_max_rows_truncates(self) -> None:
        cfg = _minimal_config(max_corpus_rows=5)
        slices = [_minimal_brenda_slice(n=20)]
        rows, _ = build_corpus_and_split(cfg, slices)
        assert len(rows) == 5

    def test_build_decoy_pool_intra_corpus_fallback(self) -> None:
        cfg = _minimal_config(decoy_pool_path=None)
        slices = [_minimal_brenda_slice(n=10)]
        rows, _ = build_corpus_and_split(cfg, slices)
        pool = build_decoy_pool(cfg, rows)
        assert len(pool) == 10  # 10 unique substrates
        assert all(isinstance(k, str) for k in pool)

    def test_build_decoy_pool_from_file(self, tmp_path: Path) -> None:
        decoy_file = tmp_path / "decoys.txt"
        keys = [f"INCHI{i}" for i in range(25)]
        decoy_file.write_text("\n".join(keys), encoding="utf-8")
        cfg = _minimal_config(decoy_pool_path=str(decoy_file))
        rows, _ = build_corpus_and_split(cfg, [_minimal_brenda_slice()])
        pool = build_decoy_pool(cfg, rows)
        assert len(pool) == 25

    def test_build_decoy_pool_missing_file_raises(self, tmp_path: Path) -> None:
        cfg = _minimal_config(decoy_pool_path=str(tmp_path / "missing.txt"))
        rows, _ = build_corpus_and_split(cfg, [_minimal_brenda_slice()])
        with pytest.raises(FileNotFoundError):
            build_decoy_pool(cfg, rows)


# ---------------------------------------------------------------------------
# 5. train() skeleton (stub model — no GPU, no real loop)
# ---------------------------------------------------------------------------


class TestTrainSkeleton:
    def test_train_returns_valid_summary(self, tmp_path: Path) -> None:
        cfg = _minimal_config(
            campaign_id="test_train_stub",
            checkpoint_dir=str(tmp_path / "ckpts"),
            tb_log_dir=str(tmp_path / "tb"),
            max_steps=10,
        )
        summary = train(cfg, slices=[], resume=False)
        # Schema version present.
        assert summary["schema_version"] == "synbio.cekm_training.v0.1"
        # Boundary SHA256 present.
        assert summary["boundary_sha256"] == BOUNDARY_SHA256
        # Campaign ID matches.
        assert summary["campaign_id"] == "test_train_stub"
        # Required top-level keys.
        for key in (
            "steps_completed",
            "corpus_total",
            "in_corpus",
            "held_out",
            "negatives",
            "calibration_report",
            "calibration_gate_passed",
            "checkpoint_dir",
            "audit_log",
        ):
            assert key in summary, f"Missing key in summary: {key!r}"

    def test_train_audit_log_written(self, tmp_path: Path) -> None:
        cfg = _minimal_config(
            campaign_id="test_audit_log",
            checkpoint_dir=str(tmp_path / "ckpts"),
            tb_log_dir=str(tmp_path / "tb"),
        )
        summary = train(cfg, slices=[], resume=False)
        audit_log_path = Path(summary["audit_log"])
        assert audit_log_path.exists()
        lines = [json.loads(ln) for ln in audit_log_path.read_text(encoding="utf-8").splitlines()]
        events = [ln["event"] for ln in lines]
        assert "training_start" in events
        assert "corpus_assembled" in events
        assert "final_calibration" in events
        assert "training_complete" in events

    def test_train_summary_is_json_serialisable(self, tmp_path: Path) -> None:
        cfg = _minimal_config(
            campaign_id="test_json_serial",
            checkpoint_dir=str(tmp_path / "ckpts"),
            tb_log_dir=str(tmp_path / "tb"),
        )
        summary = train(cfg, slices=[], resume=False)
        # Must not raise.
        serialised = json.dumps(summary)
        assert len(serialised) > 0

    def test_train_calibration_report_in_summary(self, tmp_path: Path) -> None:
        cfg = _minimal_config(
            campaign_id="test_calib_in_summary",
            checkpoint_dir=str(tmp_path / "ckpts"),
            tb_log_dir=str(tmp_path / "tb"),
        )
        summary = train(cfg, slices=[], resume=False)
        cal = summary["calibration_report"]
        assert cal["schema_version"] == "synbio.cekm_calibration.v0.1"

    def test_train_with_synthetic_slice(self, tmp_path: Path) -> None:
        cfg = _minimal_config(
            campaign_id="test_synthetic_slice",
            checkpoint_dir=str(tmp_path / "ckpts"),
            tb_log_dir=str(tmp_path / "tb"),
            enzyextract_holdout_full=False,
            seed=0,
        )
        slices = [_minimal_brenda_slice(n=20)]
        summary = train(cfg, slices=slices, resume=False)
        assert summary["corpus_total"] == 20
        assert summary["negatives"] == summary["in_corpus"] * 3

    def test_train_resume_no_checkpoint_starts_fresh(self, tmp_path: Path) -> None:
        cfg = _minimal_config(
            campaign_id="test_resume_fresh",
            checkpoint_dir=str(tmp_path / "ckpts"),
            tb_log_dir=str(tmp_path / "tb"),
        )
        # Should not raise even though there is no checkpoint yet.
        summary = train(cfg, slices=[], resume=True)
        assert summary["steps_completed"] == 0  # stub loop runs 0 steps


# ---------------------------------------------------------------------------
# 6. Calibration gate logic
# ---------------------------------------------------------------------------


class TestCalibrationGate:
    def test_calibration_passed_with_all_above_threshold(self) -> None:
        report = CalibrationReport(
            tier_alpha_coverage_at_90=0.92,
            tier_beta_coverage_at_90=0.88,
            tier_gamma_coverage_at_90=0.90,
            held_out_brenda_coverage_at_90=0.87,
            held_out_enzyextract_coverage_at_90=0.91,
        )
        assert calibration_passed(report) is True

    def test_calibration_passed_fails_if_one_below_threshold(self) -> None:
        report = CalibrationReport(
            tier_alpha_coverage_at_90=0.92,
            tier_beta_coverage_at_90=0.88,
            tier_gamma_coverage_at_90=0.84,  # below 0.85
            held_out_brenda_coverage_at_90=0.87,
            held_out_enzyextract_coverage_at_90=0.91,
        )
        assert calibration_passed(report) is False

    def test_calibration_passed_fails_if_any_is_none(self) -> None:
        report = CalibrationReport(
            tier_alpha_coverage_at_90=0.92,
            tier_beta_coverage_at_90=None,  # stub / not yet computed
            tier_gamma_coverage_at_90=0.90,
            held_out_brenda_coverage_at_90=0.87,
            held_out_enzyextract_coverage_at_90=0.91,
        )
        assert calibration_passed(report) is False

    def test_calibration_passed_all_none_fails(self) -> None:
        report = CalibrationReport()  # all None by default
        assert calibration_passed(report) is False

    def test_calibration_passed_custom_threshold(self) -> None:
        report = CalibrationReport(
            tier_alpha_coverage_at_90=0.80,
            tier_beta_coverage_at_90=0.80,
            tier_gamma_coverage_at_90=0.80,
            held_out_brenda_coverage_at_90=0.80,
            held_out_enzyextract_coverage_at_90=0.80,
        )
        assert calibration_passed(report, threshold=0.80) is True
        assert calibration_passed(report, threshold=0.85) is False

    def test_calibration_audit_returns_report_stub(self) -> None:
        cfg = _minimal_config()
        rows, split = build_corpus_and_split(cfg, [_minimal_brenda_slice(n=10)])
        report = calibration_audit(
            model=None,
            rows=rows,
            negatives=[],
            split=split,
            cfg=cfg,
        )
        assert isinstance(report, CalibrationReport)
        # Stub values must be None (not yet implemented).
        assert report.tier_alpha_coverage_at_90 is None
        assert report.tier_beta_coverage_at_90 is None
        assert report.tier_gamma_coverage_at_90 is None
        assert report.held_out_brenda_coverage_at_90 is None
        assert report.held_out_enzyextract_coverage_at_90 is None

    def test_calibration_report_to_dict_has_schema_version(self) -> None:
        report = CalibrationReport()
        d = report.to_dict()
        assert d["schema_version"] == "synbio.cekm_calibration.v0.1"


# ---------------------------------------------------------------------------
# 7. HF push skip when HF_TOKEN absent
# ---------------------------------------------------------------------------


class TestHFPush:
    def test_push_skipped_when_no_hf_token(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("HF_TOKEN", raising=False)
        cfg = _minimal_config()
        # Create a dummy checkpoint file to pass to push_to_hf.
        dummy_ckpt = tmp_path / "ckpt_step00000100.meta.json"
        dummy_ckpt.write_text("{}", encoding="utf-8")
        result = push_to_hf(dummy_ckpt, cfg)
        assert result is True  # skipped silently → True

    def test_push_dry_run_returns_true(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("HF_TOKEN", "fake_token_for_testing")
        cfg = _minimal_config()
        dummy_ckpt = tmp_path / "ckpt_step00000100.meta.json"
        dummy_ckpt.write_text("{}", encoding="utf-8")
        result = push_to_hf(dummy_ckpt, cfg, dry_run=True)
        assert result is True


# ---------------------------------------------------------------------------
# 8. CLI smoke subcommand (click test runner)
# ---------------------------------------------------------------------------


class TestCLISmoke:
    def test_smoke_subcommand_passes(self) -> None:
        runner = CliRunner()
        result = runner.invoke(cekm_group, ["smoke"])
        assert result.exit_code == 0, f"Smoke CLI failed:\n{result.output}"
        assert "PASSED" in result.output

    def test_smoke_subcommand_emits_json(self) -> None:
        runner = CliRunner()
        result = runner.invoke(cekm_group, ["smoke"])
        assert result.exit_code == 0
        # Output must contain valid JSON (the summary dict) before "Smoke test PASSED."
        json_block = result.output.split("Smoke test")[0].strip()
        parsed = json.loads(json_block)
        assert parsed["schema_version"] == "synbio.cekm_smoke.v0.1"

    def test_train_subcommand_requires_config(self) -> None:
        runner = CliRunner()
        result = runner.invoke(cekm_group, ["train"])
        # Missing required option --config → non-zero exit.
        assert result.exit_code != 0

    def test_train_subcommand_with_minimal_config(self, tmp_path: Path) -> None:
        cfg_path = tmp_path / "test_config.yaml"
        cfg_path.write_text(
            yaml.dump({
                "campaign_id": "cli_test",
                "checkpoint_dir": str(tmp_path / "ckpts"),
                "tb_log_dir": str(tmp_path / "tb"),
                "max_steps": 5,
            }),
            encoding="utf-8",
        )
        runner = CliRunner()
        result = runner.invoke(cekm_group, ["train", "--config", str(cfg_path)])
        assert result.exit_code == 0, f"CLI train failed:\n{result.output}"
        # Output should contain campaign_id in the JSON summary.
        assert "cli_test" in result.output

    def test_eval_subcommand_requires_config_and_checkpoint(self) -> None:
        runner = CliRunner()
        # Missing both options → non-zero exit.
        result = runner.invoke(cekm_group, ["eval"])
        assert result.exit_code != 0
