"""Falsifier registry — the executable spec.

Reads `audit/falsifiers.yaml` at module load and exposes:

- `REGISTRY`: dict[str, FalsifierSpec] keyed by falsifier id.
- `FalsifierSpec`: typed view of a single falsifier entry.
- `apply_falsifier(falsifier_id, evidence) -> FalsifierResult`: runs the
  falsifier's check against the evidence payload (or returns a "skip" result
  if the implementation isn't on this code path).
- `iter_layer(layer)`: yields falsifier specs that apply to a given layer.

References: PRD §5, audit/falsifiers.yaml, RESISTANCE.md.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Iterator, Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field

from zer0pa_synbio.boundary import BOUNDARY_BLOCK


REGISTRY_PATH: Path = (
    Path(__file__).resolve().parent.parent.parent.parent / "audit" / "falsifiers.yaml"
)


Tier = Literal["A", "B", "C"]
Severity = Literal["warn", "fail"]
GateAction = Literal[
    "reject_candidate",
    "flag_in_dossier",
    "inflate_uncertainty",
    "rank_lower",
    "route_to_unknown_enzyme",
    "tier_3_advisory",
    "route_to_blind_eval",
    "reject_l6_envelope",
    "route_to_phase_2",
    "reject_claim",
    "reject_candidate_and_alert",
    "reject_envelope",
]


class FalsifierSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str
    tier: Tier
    description: str
    severity: Severity
    gate_action: GateAction
    layers: list[str]
    evidence_schema: dict[str, Any] = Field(default_factory=dict)


class FalsifierResult(BaseModel):
    """Outcome of a falsifier check."""

    model_config = ConfigDict(extra="forbid")
    falsifier_id: str
    triggered: bool
    severity: Severity
    gate_action: GateAction
    message: str = ""
    evidence: dict[str, Any] = Field(default_factory=dict)


def _load_registry() -> dict[str, FalsifierSpec]:
    if not REGISTRY_PATH.exists():
        raise FileNotFoundError(f"Falsifier registry not found at {REGISTRY_PATH}")
    raw = yaml.safe_load(REGISTRY_PATH.read_text(encoding="utf-8"))
    if raw.get("schema_version") != "synbio.falsifiers.v0.1":
        raise ValueError(
            f"Unexpected falsifier registry schema_version: {raw.get('schema_version')!r}"
        )
    if raw.get("boundary") != BOUNDARY_BLOCK:
        raise ValueError(
            "Falsifier registry boundary block does not match BOUNDARY_BLOCK; "
            "f000_boundary_violation would fire on every envelope. Re-sync."
        )
    out: dict[str, FalsifierSpec] = {}
    for entry in raw.get("falsifiers", []):
        spec = FalsifierSpec.model_validate(entry)
        if spec.id in out:
            raise ValueError(f"Duplicate falsifier id in registry: {spec.id}")
        out[spec.id] = spec
    return out


REGISTRY: dict[str, FalsifierSpec] = _load_registry()
"""Module-level registry — loaded once at import."""


def iter_layer(layer: str) -> Iterator[FalsifierSpec]:
    """Yield falsifier specs that apply to a given layer label.

    Layer labels match the registry's `layers` list (e.g., "L4", "L4_kinetics",
    "L4_fba"). Substring match on layer names registered with finer-grained
    sub-layer tags (`L4_kinetics`, `L4_fba`) is intentional — a `layer="L4"`
    query yields all sub-layers.
    """
    for spec in REGISTRY.values():
        if layer in spec.layers or any(layer in lab for lab in spec.layers):
            yield spec


__all__ = [
    "REGISTRY",
    "FalsifierSpec",
    "FalsifierResult",
    "Tier",
    "Severity",
    "GateAction",
    "iter_layer",
]
