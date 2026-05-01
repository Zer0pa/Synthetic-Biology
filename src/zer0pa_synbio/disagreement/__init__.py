"""CrossModelDisagreementRecord builder + ensemble aggregator.

Per PRD §5.2 — disagreement is a first-class quantity, not an
explanation after the fact. Never average away a failed disagreement.

Helpers:
- `build_kinetics_disagreement(...)` — DLKcat / CatPred / TurNuP / CEKM
  on the same enzyme-substrate-condition tuple.
- `build_fba_disagreement(...)` — COBRApy / GECKO / ECMpy / ETFL on the
  same pathway flux through a load-bearing reaction.
- `build_retrosynthesis_disagreement(...)` — RetroPath3 / novoStoic2 /
  BioNavi / DeepRetro Jaccard distance on candidate routes.

All three write `CrossModelDisagreementRecord` with status (pass/warn/
fail/quarantine) and `resolution_action` (rerun / add_reference_model /
block_handoff / escalate_to_unknown_enzyme / escalate_to_blind_eval).
"""

from __future__ import annotations

import hashlib
import statistics
from typing import Iterable

from zer0pa_synbio.types import CrossModelDisagreementRecord


def _record_id(envelope_id: str, layer: str, quantity: str) -> str:
    seed = f"{envelope_id}|{layer}|{quantity}".encode()
    return "disagree_" + hashlib.sha256(seed).hexdigest()[:16]


def _sigma_normalised(values: list[float]) -> float:
    """Sigma-normalised dispersion (≈ relative std)."""
    if not values or len(values) < 2:
        return 0.0
    mean = statistics.fmean(values)
    if abs(mean) < 1e-12:
        return float(max(values) - min(values))
    sd = statistics.pstdev(values)
    return abs(sd / mean)


def _status_and_action(
    score: float,
    warn_threshold: float,
    fail_threshold: float,
    layer: str,
) -> tuple[str, str]:
    if score >= fail_threshold:
        if "kinetics" in layer or "L4_kinetics" in layer:
            return "fail", "escalate_to_blind_eval"
        if "L3" in layer:
            return "fail", "escalate_to_unknown_enzyme"
        return "fail", "block_handoff"
    if score >= warn_threshold:
        return "warn", "add_reference_model"
    return "pass", "rerun"


def build_kinetics_disagreement(
    *,
    envelope_id: str,
    enzyme_uniprot_id: str,
    quantity: str,  # e.g., "kcat_per_s" or "Km_mM"
    values_by_model: dict[str, float],
    uncertainties_by_model: dict[str, float] | None = None,
    warn_threshold: float = 0.3,  # 30% relative spread
    fail_threshold: float = 0.6,  # 60% relative spread
) -> CrossModelDisagreementRecord:
    models = list(values_by_model.keys())
    values = [float(values_by_model[m]) for m in models]
    uncertainties = (
        [float((uncertainties_by_model or {}).get(m, 0.0)) for m in models]
        if uncertainties_by_model is not None
        else [0.0] * len(models)
    )
    score = _sigma_normalised(values)
    layer = "L4_kinetics"
    status, action = _status_and_action(score, warn_threshold, fail_threshold, layer)
    return CrossModelDisagreementRecord(
        record_id=_record_id(envelope_id, layer, quantity + ":" + enzyme_uniprot_id),
        envelope_id=envelope_id,
        layer=layer,
        quantity=quantity + ":" + enzyme_uniprot_id,
        unit="per_s" if quantity.startswith("kcat") else "mM",
        models_compared=models,
        values=values,
        uncertainties=uncertainties,
        metric="sigma_normalized",
        pass_threshold=0.0,
        warn_threshold=warn_threshold,
        fail_threshold=fail_threshold,
        status=status,  # type: ignore[arg-type]
        resolution_action=action,  # type: ignore[arg-type]
    )


def build_fba_disagreement(
    *,
    envelope_id: str,
    reaction_id: str,
    values_by_model: dict[str, float],
    warn_threshold: float = 0.4,
    fail_threshold: float = 0.7,
) -> CrossModelDisagreementRecord:
    models = list(values_by_model.keys())
    values = [float(values_by_model[m]) for m in models]
    score = _sigma_normalised(values)
    layer = "L4_fba"
    status, action = _status_and_action(score, warn_threshold, fail_threshold, layer)
    return CrossModelDisagreementRecord(
        record_id=_record_id(envelope_id, layer, reaction_id),
        envelope_id=envelope_id,
        layer=layer,
        quantity="flux_through_" + reaction_id,
        unit="mmol/(gDW.h)",
        models_compared=models,
        values=values,
        uncertainties=[0.0] * len(models),
        metric="sigma_normalized",
        pass_threshold=0.0,
        warn_threshold=warn_threshold,
        fail_threshold=fail_threshold,
        status=status,  # type: ignore[arg-type]
        resolution_action=action,  # type: ignore[arg-type]
    )


def build_retrosynthesis_disagreement(
    *,
    envelope_id: str,
    target_inchi_key: str,
    routes_by_tool: dict[str, set[str] | list[str]],
    warn_threshold: float = 0.5,
    fail_threshold: float = 0.85,
) -> CrossModelDisagreementRecord:
    """Pairwise Jaccard distance over candidate-route ID sets per tool."""
    tools = list(routes_by_tool.keys())
    if len(tools) < 2:
        max_jd = 0.0
    else:
        max_jd = 0.0
        sets = {t: set(routes_by_tool[t]) for t in tools}
        for i in range(len(tools)):
            for j in range(i + 1, len(tools)):
                a, b = sets[tools[i]], sets[tools[j]]
                u = a | b
                inter = a & b
                jd = 1.0 - (len(inter) / len(u) if u else 1.0)
                if jd > max_jd:
                    max_jd = jd
    score = max_jd
    layer = "L3"
    status, action = _status_and_action(score, warn_threshold, fail_threshold, layer)
    return CrossModelDisagreementRecord(
        record_id=_record_id(envelope_id, layer, "retrosynthesis:" + target_inchi_key),
        envelope_id=envelope_id,
        layer=layer,
        quantity="route_set:" + target_inchi_key,
        unit="jaccard",
        models_compared=tools,
        values=[float(len(routes_by_tool[t])) for t in tools],
        uncertainties=[0.0] * len(tools),
        metric="jaccard",
        pass_threshold=0.0,
        warn_threshold=warn_threshold,
        fail_threshold=fail_threshold,
        status=status,  # type: ignore[arg-type]
        resolution_action=action,  # type: ignore[arg-type]
    )


__all__ = [
    "build_kinetics_disagreement",
    "build_fba_disagreement",
    "build_retrosynthesis_disagreement",
]
