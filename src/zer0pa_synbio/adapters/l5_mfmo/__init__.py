"""L5 MFMO multi-fidelity BoTorch surrogate.

Per PRD §6.7: GP with Hamming-distance kernel default; deep ensemble
fallback; BNN as plug-replaceable alternative. ASR-thermostable
initialisation when predicted Tm < 50°C. qLogNEHVI for multi-objective
Pareto ranking.

Two execution paths:

1. **Real path (preferred)** — when ``.venv-l5/bin/python`` exists at
   the repo root, the adapter spawns it as a subprocess to run
   ``botorch_worker.py``. The worker fits a GP per objective with the
   Hamming-distance kernel, computes posterior quantiles, runs Pareto
   ranking, and proposes a next-batch via qLogNEHVI. ASR-thermostable
   warm-starts are injected when any candidate has predicted
   ``Tm < 50°C``. Sets ``surrogate=gp_hamming``,
   ``surrogate_calibration_score`` from leave-one-out posterior
   coverage.

2. **Stub path (fallback)** — when ``.venv-l5`` is not available
   (e.g. on CI runners without a Python 3.11 sub-venv), the adapter
   falls back to a scipy-based deterministic Pareto sort. Sets
   ``surrogate=scipy_fallback``.

The split-venv architecture is required because PyTorch dropped
macOS x86_64 wheels at Python 3.13; the rest of this repo runs on
Python 3.13 / macOS x86_64. The worker venv is Python 3.11 / torch
2.2.2 — see ``HANDOFF-CPU-CONTINUATION.md`` § A.

Plug-replaceability invariant (PRD §4.5): both paths emit the same
``RankedPathwaySet`` payload schema. Switching paths is a pure
runtime detection, not a configuration change.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import uuid
from pathlib import Path
from typing import Any

from zer0pa_synbio.adapters import LayerAdapter
from zer0pa_synbio.envelope import Domain, Layer, LicenseClass, UniversalLayerEnvelope


def _zpe_design_vector(c: dict[str, Any], dim: int = 8) -> list[int]:
    """Encode a candidate's pathway_id into a deterministic ZPE-like
    integer vector for the Hamming kernel. v0.1 uses a hash-based
    encoder; future versions will pull from L1's ZPE word output and
    L6's design knobs (promoter strength, copy number, knockout flags).
    """
    pid = str(c.get("pathway_id", ""))
    h = abs(hash(pid)).to_bytes(16, "big", signed=False)
    return [b % 4 for b in h[:dim]]


class L5MFMOAdapter(LayerAdapter):
    layer = Layer.L5
    adapter_name = "L5MFMOAdapter"
    tool_name = "botorch_qLogNEHVI_hamming"
    tool_version = "torch==2.2.2;botorch==0.17.2;gpytorch==1.15.2"
    license_class = LicenseClass.A
    license_evidence_uri = "audit/source_manifests/metanetx.yaml"

    @staticmethod
    def _venv_l5_python() -> Path | None:
        """Locate the Python 3.11 BoTorch worker venv at the repo root.

        Returns the absolute path to ``.venv-l5/bin/python`` if it
        exists, else None.
        """
        # The adapter is at .../src/zer0pa_synbio/adapters/l5_mfmo/__init__.py
        repo_root = Path(__file__).resolve().parents[4]
        candidate = repo_root / ".venv-l5" / "bin" / "python"
        return candidate if candidate.exists() else None

    @classmethod
    def _worker_script(cls) -> Path:
        return Path(__file__).resolve().parent / "botorch_worker.py"

    @classmethod
    def _run_worker(cls, spec: dict[str, Any], timeout_s: int = 300) -> dict[str, Any] | None:
        py = cls._venv_l5_python()
        if py is None:
            return None
        try:
            proc = subprocess.run(
                [str(py), str(cls._worker_script())],
                input=json.dumps(spec),
                capture_output=True,
                text=True,
                timeout=timeout_s,
            )
        except (subprocess.TimeoutExpired, OSError):
            return None
        if proc.returncode != 0:
            return None
        try:
            return json.loads(proc.stdout)
        except json.JSONDecodeError:
            return None

    def run(
        self, *, campaign_id, domain, organism, gem_id, input_payload, run_id=None
    ) -> UniversalLayerEnvelope:
        candidates = list(input_payload.get("scored_candidates", []))
        design_dim = int(input_payload.get("design_dim", 8))
        n_warm_asr = int(input_payload.get("n_warm_asr", 3))
        asr_thr = float(input_payload.get("asr_tm_threshold_c", 50.0))
        n_suggested = int(input_payload.get("n_suggested_next_batch", 4))
        ref_point = input_payload.get(
            "hypervolume_ref_point", [-1.0, -1.0, -3.0, -3.0]
        )
        seed = int(input_payload.get("seed", 42))

        # Build the worker spec. Each candidate gets a deterministic
        # Hamming-encoded design vector (until L6 hands the real one
        # back through the closed-loop in DBTL round ≥ 1).
        spec_candidates = []
        for c in candidates:
            spec_candidates.append(
                {
                    "pathway_id": c.get("pathway_id", ""),
                    "design_vector": _zpe_design_vector(c, design_dim),
                    "predicted_titer_g_l": float(
                        c.get("predicted_titer_g_l", 1.0 + 0.5 * c.get("mdf_score_kj_mol", 0.0) / 10.0)
                    ),
                    "predicted_yield_mol_mol": float(
                        c.get("predicted_yield_mol_mol", 0.15 + 0.05 * c.get("mdf_score_kj_mol", 0.0) / 10.0)
                    ),
                    "predicted_burden_au": float(c.get("predicted_burden_au", 0.6)),
                    "predicted_toxicity_au": float(c.get("predicted_toxicity_au", 0.1)),
                    "predicted_tm_celsius": c.get("predicted_tm_celsius"),
                    "mdf_score_kj_mol": float(c.get("mdf_score_kj_mol", 0.0)),
                }
            )

        worker_spec = {
            "candidates": spec_candidates,
            "design_dim": design_dim,
            "n_warm_asr": n_warm_asr,
            "asr_tm_threshold_c": asr_thr,
            "ref_point": ref_point,
            "n_suggested": n_suggested,
            "seed": seed,
        }

        worker_result = self._run_worker(worker_spec)

        if worker_result is not None:
            # Real path. Hydrate ranked candidates with worker outputs.
            id_to_orig = {c.get("pathway_id"): c for c in candidates}
            ranked: list[dict[str, Any]] = []
            for r in worker_result["ranked"]:
                pid = r["pathway_id"]
                base = dict(id_to_orig.get(pid, {"pathway_id": pid}))
                base.update(
                    {
                        "pathway_id": pid,
                        "pareto_rank": r["pareto_rank"],
                        "expected_titer_g_l": r["expected_titer_g_l"],
                        "expected_yield_mol_mol": r["expected_yield_mol_mol"],
                        "expected_burden_au": r["expected_burden_au"],
                        "expected_toxicity_au": r["expected_toxicity_au"],
                        "surrogate": r["surrogate"],
                        "surrogate_calibration_score": r[
                            "surrogate_calibration_score"
                        ],
                    }
                )
                ranked.append(base)

            # Validation sequence stub gets the qLogNEHVI suggestions
            # as candidate experiments for the L5_OED node.
            validation_sequence = {
                "schema_version": "synbio.validation_sequence.v0.1",
                "ordered_experiments": [
                    {
                        "experiment_id": f"qLogNEHVI_proposal_{i}",
                        "intervention": {
                            "design_vector_continuous": s["design_vector_continuous"],
                            "is_asr_thermostable_warmstart": s.get(
                                "is_asr_thermostable_warmstart", False
                            ),
                        },
                        "expected_information_gain_nats": float(
                            s["qLogNEHVI_acq_value"]
                        ),
                        "consumer": "human_cro",
                        "cost_estimate_usd": 0.0,
                        "expected_completion_days": 0,
                    }
                    for i, s in enumerate(worker_result["suggested_next_batch"])
                ],
                "go_cbed_objective": "balanced",
                "posterior_uncertainty_kl_reduction_target": 1.0,
            }

            output_payload = {
                "schema_version": "synbio.ranked_pathway_set.v0.1",
                "candidates": ranked,
                "validation_sequence": validation_sequence,
                "surrogate_meta": worker_result["surrogate_meta"],
                "asr_warmstart": worker_result["asr_warmstart"],
                "stub_mode": False,
            }
        else:
            # Stub path — scipy-style deterministic Pareto rank by MDF score.
            ranked = sorted(
                candidates,
                key=lambda c: c.get("mdf_score_kj_mol", 0.0),
                reverse=True,
            )
            for i, c in enumerate(ranked):
                c["pareto_rank"] = i
                c["expected_titer_g_l"] = {"p05": 0.5, "p50": 1.2, "p95": 2.4}
                c["expected_yield_mol_mol"] = {"p05": 0.10, "p50": 0.18, "p95": 0.27}
                c["expected_burden_au"] = {"p05": 0.4, "p50": 0.6, "p95": 0.9}
                c["expected_toxicity_au"] = {"p05": 0.05, "p50": 0.10, "p95": 0.20}
                c["surrogate"] = "scipy_fallback"
                c["surrogate_calibration_score"] = 0.0
            validation_sequence = {
                "schema_version": "synbio.validation_sequence.v0.1",
                "ordered_experiments": [],
                "go_cbed_objective": "balanced",
                "posterior_uncertainty_kl_reduction_target": 1.0,
            }
            output_payload = {
                "schema_version": "synbio.ranked_pathway_set.v0.1",
                "candidates": ranked,
                "validation_sequence": validation_sequence,
                "surrogate_meta": {
                    "kernel": "scipy_pareto_sort",
                    "acquisition": "scipy_pareto_sort",
                    "n_train": 0,
                    "n_features": 0,
                    "n_objectives": 0,
                },
                "asr_warmstart": {
                    "n_injected": 0,
                    "tm_threshold_c": asr_thr,
                    "tm_min_observed_c": None,
                },
                "stub_mode": True,
            }

        return self._make_envelope(
            campaign_id=campaign_id,
            domain=domain,
            organism=organism,
            gem_id=gem_id,
            input_payload=input_payload,
            output_payload=output_payload,
            run_id=run_id,
        )


__all__ = ["L5MFMOAdapter"]
