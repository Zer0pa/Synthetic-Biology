"""PathGym — Zer0pa-built DBTL benchmark for pathway-level optimisation.

Per PRD §11 and source-briefs/02-corrections-and-architecture.md §2.4:
PathGym is the equivalent of ProteinGym for metabolic-pathway optimisation.
Each pipeline run emits one `ReasonerTuple`; the corpus grows per
engagement. The corpus is the moat; no model is.

The active-learning data loop (PRD §11) reoptimises three things nightly
against the latest PathGym corpus state:
  1. L3.5 ranking gate thresholds (audit/l3_5_thresholds.json)
  2. CEKM model weights (HF: Architect-Prime/synbio-cekm-v0.1)
  3. BoTorch surrogate prior (per-campaign state)

This module ships the writer and the corpus-loader; the nightly retrain
hook is a future work item gated on Runpod (see NEXT-WAVE-PLAN.md).
"""

from __future__ import annotations

import hashlib
import uuid
from pathlib import Path
from typing import Any

from zer0pa_synbio.boundary import BOUNDARY_BLOCK
from zer0pa_synbio.envelope import canonical_json
from zer0pa_synbio.types import ReasonerTuple


def _ledger_path(repo_root: Path) -> Path:
    return repo_root / "audit" / "reasoner_tuples.jsonl"


def append_reasoner_tuple(repo_root: Path, tuple_: ReasonerTuple) -> Path:
    """Append a ReasonerTuple to the PathGym ledger (Tier-3 + opted-in
    Tier-2 only). Returns the ledger path."""
    if tuple_.rights_label == "tier_1_customer":
        # Tier-1 stays customer-isolated; never write to the global ledger.
        raise ValueError(
            "tier_1_customer ReasonerTuples must be written to "
            "audit/runtime/<campaign_id>/reasoner_tuples.jsonl, "
            "not the global PathGym ledger."
        )
    p = _ledger_path(repo_root)
    p.parent.mkdir(parents=True, exist_ok=True)
    line = canonical_json(tuple_.model_dump(mode="json")).decode("utf-8")
    with open(p, "a", encoding="utf-8") as f:
        f.write(line + "\n")
    return p


def load_pathgym_corpus(repo_root: Path) -> list[ReasonerTuple]:
    """Read the public PathGym ledger; deserialise each line as a
    ReasonerTuple. Used by the nightly retrain hook to produce the
    training corpus state."""
    p = _ledger_path(repo_root)
    if not p.exists():
        return []
    out: list[ReasonerTuple] = []
    import json as _json

    for line in p.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        out.append(ReasonerTuple.model_validate(_json.loads(line)))
    return out


def make_reasoner_tuple(
    *,
    campaign_id: str,
    problem_context: str,
    input_spec_envelope_id: str,
    tool_plan: dict[str, Any],
    raw_result_envelope_id: str,
    falsifier_result_ids: list[str],
    disagreement_record_ids: list[str],
    outcome_label: str = "inconclusive",
    rights_label: str = "tier_3_public",
    next_action: str = "",
    ground_truth_envelope_id: str | None = None,
) -> ReasonerTuple:
    """Build a ReasonerTuple with stable, content-addressable tuple_id."""
    seed = f"{campaign_id}|{input_spec_envelope_id}|{raw_result_envelope_id}|{outcome_label}"
    tid = "tuple_" + hashlib.sha256(seed.encode("utf-8")).hexdigest()[:12]
    return ReasonerTuple(
        tuple_id=tid,
        campaign_id=campaign_id,
        problem_context=problem_context,
        input_spec_ref=input_spec_envelope_id,
        tool_plan=tool_plan,
        simulation_request_ref="",
        raw_result_ref=raw_result_envelope_id,
        reduced_observables_ref="",
        falsifier_results=falsifier_result_ids,
        disagreement_records=disagreement_record_ids,
        ground_truth_ref=ground_truth_envelope_id,
        outcome_label=outcome_label,  # type: ignore[arg-type]
        rights_label=rights_label,  # type: ignore[arg-type]
        next_action=next_action,
    )


__all__ = ["append_reasoner_tuple", "load_pathgym_corpus", "make_reasoner_tuple"]
