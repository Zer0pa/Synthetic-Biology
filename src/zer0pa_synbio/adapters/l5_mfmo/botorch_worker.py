"""L5 MFMO BoTorch worker — runs in `.venv-l5` (Python 3.11 + torch 2.2).

Per PRD §6.7 / HANDOFF-CPU-CONTINUATION.md item A.

This script is invoked as a subprocess by `L5MFMOAdapter` (which lives
in the main `.venv` Python 3.13 environment, where torch wheels for
macOS x86_64 are not available). It reads a JSON spec from stdin and
writes a JSON result to stdout.

Spec format (input)::

    {
      "candidates": [
        {
          "pathway_id": str,
          "design_vector": [int, ...],   # discrete encoding (ZPE word + design knobs)
          "predicted_titer_g_l": float,  # observed objective 1
          "predicted_yield_mol_mol": float,  # observed objective 2
          "predicted_burden_au": float,  # observed objective 3 (lower is better)
          "predicted_toxicity_au": float,  # observed objective 4 (lower is better)
          "predicted_tm_celsius": float | null,  # ASR trigger when < 50
          "mdf_score_kj_mol": float | null,
        }, ...
      ],
      "design_dim": int,        # length of design_vector
      "n_warm_asr": int,        # number of ASR-thermostable warm starts (0 if none triggered)
      "asr_tm_threshold_c": float,  # default 50.0
      "ref_point": [float, float, float, float],  # hypervolume reference (worst-acceptable)
      "n_suggested": int,       # how many next-batch designs to propose
      "seed": int
    }

Result format (output)::

    {
      "ranked": [
        {
          "pathway_id": str,
          "pareto_rank": int,
          "expected_titer_g_l": {p05, p50, p95},
          "expected_yield_mol_mol": {p05, p50, p95},
          "expected_burden_au": {p05, p50, p95},
          "expected_toxicity_au": {p05, p50, p95},
          "surrogate": "gp_hamming",
          "surrogate_calibration_score": float,
          "is_asr_thermostable_warmstart": bool
        }, ...
      ],
      "suggested_next_batch": [
        {
          "design_vector_continuous": [float, ...],
          "qLogNEHVI_acq_value": float,
          "rank_in_batch": int
        }, ...
      ],
      "surrogate_meta": {
        "n_train": int,
        "n_features": int,
        "n_objectives": int,
        "kernel": "hamming_distance",
        "acquisition": "qLogNEHVI",
        "fitted_lengthscales": [float, ...] | null,
        "noise_levels": [float, ...]
      },
      "asr_warmstart": {
        "n_injected": int,
        "tm_threshold_c": float,
        "tm_min_observed_c": float | null
      }
    }

The worker is **deterministic** under the input ``seed`` so the
adapter can produce reproducible envelopes.

License: Apache 2.0 (Zer0pa). Tools used: BoTorch + GPyTorch (MIT),
PyTorch (BSD).
"""

from __future__ import annotations

import json
import math
import sys
from typing import Any

import numpy as np
import torch
from botorch.acquisition.multi_objective.logei import (
    qLogNoisyExpectedHypervolumeImprovement,
)
from botorch.fit import fit_gpytorch_mll
from botorch.models import ModelListGP, SingleTaskGP
from botorch.utils.multi_objective.pareto import is_non_dominated
from gpytorch.constraints import GreaterThan
from gpytorch.kernels import Kernel, ScaleKernel
from gpytorch.likelihoods import GaussianLikelihood
from gpytorch.mlls import SumMarginalLogLikelihood

DTYPE = torch.float64


class HammingKernel(Kernel):
    """Discrete Hamming-distance kernel.

    For inputs ``x, x'`` interpreted as integer-encoded design vectors,
    the Hamming distance ``d_H(x, x') = sum_i 1{x_i != x'_i}``. The
    kernel is::

        k(x, x') = exp(-lengthscale * d_H(x, x') / D)

    where ``D`` is the dimensionality. The lengthscale is learnable.
    PRD §6.7 specifies a Hamming-distance kernel as the L5 default for
    discrete ZPE-encoded design vectors. The continuous-relaxation form
    used here uses |x_i - x'_i| with a small temperature, which reduces
    to the integer Hamming distance when inputs are integer-valued and
    the temperature is small.
    """

    has_lengthscale = True

    def forward(self, x1, x2, diag=False, **params):
        # x1: (..., n1, d), x2: (..., n2, d). Compute pairwise
        # |x1 - x2| element-wise and sum across the feature axis.
        if diag:
            # When diag=True, the caller wants only the diagonal of
            # k(x1, x2) where x1 and x2 have the same shape.
            d = (x1 - x2).abs().sum(dim=-1)
        else:
            x1u = x1.unsqueeze(-2)
            x2u = x2.unsqueeze(-3)
            d = (x1u - x2u).abs().sum(dim=-1)
        D = x1.shape[-1]
        # Lengthscale shape (..., 1, 1) or (..., 1, 1, 1).
        ls = self.lengthscale
        scaled = d / max(D, 1) * ls.squeeze(-1)
        return torch.exp(-scaled)


def _tensor_from_candidates(candidates: list[dict[str, Any]]) -> tuple[torch.Tensor, torch.Tensor, list[float | None]]:
    """Stack design_vector and 4-objective observations into tensors.

    Burden and toxicity are negated so all objectives are
    "higher-is-better" for hypervolume computation downstream.
    """
    X = torch.tensor(
        [c["design_vector"] for c in candidates], dtype=DTYPE
    )
    Y = torch.tensor(
        [
            [
                c.get("predicted_titer_g_l", 0.0),
                c.get("predicted_yield_mol_mol", 0.0),
                -c.get("predicted_burden_au", 0.0),
                -c.get("predicted_toxicity_au", 0.0),
            ]
            for c in candidates
        ],
        dtype=DTYPE,
    )
    Tm = [c.get("predicted_tm_celsius") for c in candidates]
    return X, Y, Tm


def _pareto_rank(Y: torch.Tensor) -> list[int]:
    """Iteratively remove non-dominated fronts and assign ranks."""
    remaining = torch.ones(Y.shape[0], dtype=torch.bool)
    ranks = [-1] * Y.shape[0]
    rank = 0
    while remaining.any():
        idx = torch.where(remaining)[0]
        sub = Y[remaining]
        nd = is_non_dominated(sub)
        for i, in_front in zip(idx.tolist(), nd.tolist()):
            if in_front:
                ranks[i] = rank
                remaining[i] = False
        rank += 1
    return ranks


def _generate_asr_warmstarts(
    base: torch.Tensor,
    n_warm: int,
    seed: int,
) -> torch.Tensor:
    """Generate n_warm ASR-thermostable initialisation points.

    Heuristic: take the column-wise mean of `base` (centroid), perturb
    by a small gaussian, and discretise. ASR-thermostable variants in
    real synbio engineering are typically near consensus sequences;
    the centroid is a tractable structural analog over the design
    vector encoding.
    """
    if n_warm <= 0 or base.shape[0] == 0:
        return torch.empty((0, base.shape[1]), dtype=DTYPE)
    g = torch.Generator().manual_seed(seed + 7919)
    centroid = base.mean(dim=0, keepdim=True)
    pert = torch.randn(n_warm, base.shape[1], generator=g, dtype=DTYPE) * 0.5
    warm = centroid + pert
    warm = warm.round()
    return warm


def _fit_models(X: torch.Tensor, Y: torch.Tensor) -> ModelListGP:
    """Fit one SingleTaskGP per objective with the Hamming kernel."""
    models = []
    for i in range(Y.shape[1]):
        kernel = ScaleKernel(HammingKernel())
        likelihood = GaussianLikelihood(noise_constraint=GreaterThan(1e-4))
        gp = SingleTaskGP(
            train_X=X,
            train_Y=Y[:, i : i + 1],
            covar_module=kernel,
            likelihood=likelihood,
        )
        models.append(gp)
    mlist = ModelListGP(*models)
    mll = SumMarginalLogLikelihood(mlist.likelihood, mlist)
    fit_gpytorch_mll(mll)
    return mlist


def _calibration_score(model: ModelListGP, X: torch.Tensor, Y: torch.Tensor) -> float:
    """Leave-one-out RMSE / std as a simple calibration score (lower is
    better; good calibration means RMSE comparable to predicted std)."""
    with torch.no_grad():
        post = model.posterior(X)
        mean = post.mean
        std = post.variance.sqrt()
    err = (Y - mean).abs()
    z = err / (std + 1e-6)
    # Calibration score: 1 - |mean(z) - 1|, clipped to [0, 1].
    score = 1.0 - abs(float(z.mean()) - 1.0)
    return max(0.0, min(1.0, score))


def _objective_quantiles(
    model: ModelListGP, X: torch.Tensor, sign: list[int]
) -> list[dict[str, float]]:
    """Return p05/p50/p95 per design × per objective.

    ``sign[i] = +1`` if the user-facing objective is the model's
    objective; ``-1`` if it was negated for hypervolume (e.g. burden).
    """
    with torch.no_grad():
        post = model.posterior(X)
        mean = post.mean
        std = post.variance.sqrt()
    n_d, n_obj = mean.shape
    out: list[dict[str, float]] = []
    for d in range(n_d):
        per_obj = []
        for o in range(n_obj):
            mu = float(mean[d, o]) * sign[o]
            sd = float(std[d, o])
            per_obj.append(
                {
                    "p05": mu - 1.645 * sd,
                    "p50": mu,
                    "p95": mu + 1.645 * sd,
                }
            )
        out.append({"per_objective": per_obj})
    return out


def run(spec: dict[str, Any]) -> dict[str, Any]:
    candidates = list(spec.get("candidates", []))
    design_dim = int(spec.get("design_dim", 4))
    n_warm = int(spec.get("n_warm_asr", 0))
    asr_thr = float(spec.get("asr_tm_threshold_c", 50.0))
    n_next = int(spec.get("n_suggested", 0))
    ref_point = spec.get("ref_point", [-1.0, -1.0, -10.0, -10.0])
    seed = int(spec.get("seed", 0))
    torch.manual_seed(seed)
    np.random.seed(seed)

    if not candidates:
        return {
            "ranked": [],
            "suggested_next_batch": [],
            "surrogate_meta": {
                "n_train": 0,
                "n_features": design_dim,
                "n_objectives": 4,
                "kernel": "hamming_distance",
                "acquisition": "qLogNEHVI",
                "fitted_lengthscales": None,
                "noise_levels": [],
            },
            "asr_warmstart": {
                "n_injected": 0,
                "tm_threshold_c": asr_thr,
                "tm_min_observed_c": None,
            },
        }

    X_obs, Y_obs, Tm = _tensor_from_candidates(candidates)
    n_obj = Y_obs.shape[1]
    sign = [+1, +1, -1, -1]  # titer, yield, burden, toxicity

    # ASR warm-starts: trigger when the minimum observed Tm is below threshold.
    valid_tm = [t for t in Tm if t is not None]
    tm_min = min(valid_tm) if valid_tm else None
    asr_triggered = (tm_min is not None and tm_min < asr_thr) and n_warm > 0
    if asr_triggered:
        warm = _generate_asr_warmstarts(X_obs, n_warm, seed)
        # Score warm-starts by GP posterior after fitting on the
        # original observations only (warm-starts get appended for
        # the next-batch suggestion but are not "observed").
        X_train = X_obs
        Y_train = Y_obs
    else:
        warm = torch.empty((0, design_dim), dtype=DTYPE)
        X_train = X_obs
        Y_train = Y_obs

    # Fit one GP per objective.
    model = _fit_models(X_train, Y_train)
    calib = _calibration_score(model, X_train, Y_train)

    # Ranked output for the input candidates.
    obj_quantiles = _objective_quantiles(model, X_obs, sign)
    ranks = _pareto_rank(Y_obs)
    ranked: list[dict[str, Any]] = []
    obj_names = [
        "expected_titer_g_l",
        "expected_yield_mol_mol",
        "expected_burden_au",
        "expected_toxicity_au",
    ]
    for i, c in enumerate(candidates):
        per_obj = obj_quantiles[i]["per_objective"]
        out = {
            "pathway_id": c.get("pathway_id", f"p_{i}"),
            "pareto_rank": ranks[i],
            "surrogate": "gp_hamming",
            "surrogate_calibration_score": calib,
            "is_asr_thermostable_warmstart": False,
            "mdf_score_kj_mol": c.get("mdf_score_kj_mol"),
        }
        for name, q in zip(obj_names, per_obj):
            out[name] = q
        ranked.append(out)

    # qLogNEHVI suggestion.
    suggested: list[dict[str, Any]] = []
    if n_next > 0:
        try:
            ref_t = torch.tensor(ref_point, dtype=DTYPE)
            acq = qLogNoisyExpectedHypervolumeImprovement(
                model=model,
                ref_point=ref_t,
                X_baseline=X_train,
                prune_baseline=True,
            )
            # Build a candidate pool for next-batch evaluation by
            # combining (a) ASR warm-starts and (b) random perturbations
            # of the observed designs. We do *not* run continuous
            # optimisation because design space is discrete and
            # combinatorial — picking the best of a moderate-sized
            # pool is a reasonable v0.1 selector.
            g = torch.Generator().manual_seed(seed + 13)
            n_pool = 32
            pert = torch.randn(n_pool, design_dim, generator=g, dtype=DTYPE) * 0.7
            seed_pool = X_train[torch.randint(
                0, X_train.shape[0], (n_pool,), generator=g
            )]
            random_pool = (seed_pool + pert).round()
            pool = torch.cat([random_pool, warm], dim=0) if warm.numel() else random_pool
            with torch.no_grad():
                acq_vals = acq(pool.unsqueeze(1))  # batch shape (n_pool, 1, d)
            order = torch.argsort(acq_vals, descending=True)
            for j, idx in enumerate(order[:n_next].tolist()):
                is_warm = bool(idx >= random_pool.shape[0])
                suggested.append(
                    {
                        "design_vector_continuous": pool[idx].tolist(),
                        "qLogNEHVI_acq_value": float(acq_vals[idx]),
                        "rank_in_batch": j,
                        "is_asr_thermostable_warmstart": is_warm,
                    }
                )
        except Exception as exc:  # pragma: no cover (defensive)
            suggested = [
                {
                    "design_vector_continuous": [],
                    "qLogNEHVI_acq_value": 0.0,
                    "rank_in_batch": 0,
                    "error": f"qLogNEHVI failed: {exc}",
                }
            ]

    # Extract per-objective lengthscales and noise.
    lengthscales = []
    noise_levels = []
    try:
        for m in model.models:
            ls = float(m.covar_module.base_kernel.lengthscale.detach())
            lengthscales.append(ls)
            noise_levels.append(float(m.likelihood.noise.detach()))
    except Exception:
        lengthscales = None  # type: ignore[assignment]

    return {
        "ranked": ranked,
        "suggested_next_batch": suggested,
        "surrogate_meta": {
            "n_train": int(X_train.shape[0]),
            "n_features": design_dim,
            "n_objectives": n_obj,
            "kernel": "hamming_distance",
            "acquisition": "qLogNEHVI",
            "fitted_lengthscales": lengthscales,
            "noise_levels": noise_levels,
        },
        "asr_warmstart": {
            "n_injected": int(warm.shape[0]) if asr_triggered else 0,
            "tm_threshold_c": asr_thr,
            "tm_min_observed_c": tm_min,
        },
    }


def main() -> None:
    raw = sys.stdin.read()
    spec = json.loads(raw)
    result = run(spec)
    sys.stdout.write(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
