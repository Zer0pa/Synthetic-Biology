"""UniversalLayerEnvelope (synbio-shaped) — every adapter, simulator, MCP
server, and LLM-assisted tool emits one of these. Tool-native objects must not
cross layer boundaries.

Reference: `PRD.md` § 4.1.

Invariants enforced here:

- The `boundary` field must contain the binding boundary block exactly
  (BoundaryGate; sha256-checked against `boundary.BOUNDARY_SHA256`).
- An envelope in `mode=engineering_stub`, `mode=replay`, or whose backend
  `execution_mode` is `gpu_rest_stub` MUST NOT set
  `falsification.scientific_valid=True`. Stubs satisfy engineering acceptance
  only.
- License classes `C`, `D`, `E` may not appear in product paths without an
  explicit `license_evidence_uri` pointing into `audit/license_grants/`.
- L6 envelopes (`layer=L6`) require `falsification.sbol_attestation_present=True`.
- `envelope_id` is the sha256 of the canonical-JSON serialisation of the
  envelope with `envelope_id` itself blanked. Hash discipline:
  `compute_envelope_id(model)` is deterministic.
"""

from __future__ import annotations

import hashlib
import json
import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)

from zer0pa_synbio.boundary import BOUNDARY_BLOCK, BOUNDARY_SHA256


SCHEMA_VERSION: str = "synbio.envelope.v0.1"


class BoundaryGateError(ValueError):
    """Raised when an envelope fails the boundary gate."""


class Layer(str, Enum):
    L1 = "L1"
    L2 = "L2"
    L3 = "L3"
    L3_5 = "L3_5"
    L4 = "L4"
    L4_5 = "L4_5"
    L5 = "L5"
    L5_OED = "L5_OED"
    L6 = "L6"
    L6_BUILD = "L6_BUILD"
    L7 = "L7"


class Domain(str, Enum):
    industrial_chemical = "industrial_chemical"
    specialty_chemical = "specialty_chemical"
    saf = "saf"
    pharma_intermediate = "pharma_intermediate"
    hmo = "hmo"
    other = "other"


class RunMode(str, Enum):
    scientific = "scientific"
    engineering_stub = "engineering_stub"
    replay = "replay"
    validation = "validation"


class ExecutionMode(str, Enum):
    local_cpu = "local_cpu"
    isolated_cpu = "isolated_cpu"
    gpu_rest_stub = "gpu_rest_stub"
    runpod_rest = "runpod_rest"
    external_service = "external_service"
    cloud_lab_dry_run = "cloud_lab_dry_run"
    cloud_lab_wet = "cloud_lab_wet"


class LicenseClass(str, Enum):
    A = "A"
    B = "B"
    C = "C"
    D = "D"
    E = "E"


class GateStatus(str, Enum):
    pass_ = "pass"
    warn = "warn"
    fail = "fail"
    quarantine = "quarantine"


class UncertaintyDistribution(str, Enum):
    none = "none"
    normal = "normal"
    lognormal = "lognormal"
    empirical = "empirical"
    ensemble = "ensemble"
    posterior = "posterior"


class ContributorTag(str, Enum):
    L1 = "L1"
    L2 = "L2"
    L3 = "L3"
    L3_5 = "L3_5"
    L4 = "L4"
    L4_5 = "L4_5"
    L5 = "L5"
    data = "data"
    surrogate = "surrogate"
    cross_model = "cross_model"


class Reference(BaseModel):
    """A reference to an external artifact (input or output)."""

    model_config = ConfigDict(extra="forbid")

    type: str
    uri: str
    sha256: str
    schema_version: str


class Backend(BaseModel):
    """Identity of the backend that produced the envelope."""

    model_config = ConfigDict(extra="forbid")

    adapter: str
    tool: str
    tool_version: str
    execution_mode: ExecutionMode
    license_class: LicenseClass
    license_evidence_uri: str

    @model_validator(mode="after")
    def license_grant_required_for_cde(self) -> "Backend":
        if self.license_class in (LicenseClass.C, LicenseClass.D, LicenseClass.E):
            if not self.license_evidence_uri or not self.license_evidence_uri.strip():
                raise ValueError(
                    f"License class {self.license_class.value} requires non-empty "
                    "license_evidence_uri pointing into audit/license_grants/"
                )
            if "audit/license_grants/" not in self.license_evidence_uri:
                raise ValueError(
                    f"License class {self.license_class.value} requires "
                    "license_evidence_uri to reference audit/license_grants/<name>.yaml"
                )
        return self


class Inputs(BaseModel):
    model_config = ConfigDict(extra="forbid")
    refs: list[Reference] = Field(default_factory=list)
    payload: dict[str, Any] = Field(default_factory=dict)


class Outputs(BaseModel):
    model_config = ConfigDict(extra="forbid")
    refs: list[Reference] = Field(default_factory=list)
    payload: dict[str, Any] = Field(default_factory=dict)


class Uncertainty(BaseModel):
    model_config = ConfigDict(extra="forbid")
    distribution: UncertaintyDistribution = UncertaintyDistribution.none
    p05: dict[str, Any] = Field(default_factory=dict)
    p50: dict[str, Any] = Field(default_factory=dict)
    p95: dict[str, Any] = Field(default_factory=dict)
    contributors: list[ContributorTag] = Field(default_factory=list)


class FalsifierFailure(BaseModel):
    model_config = ConfigDict(extra="forbid")
    gate_id: str
    severity: Literal["warn", "fail"]
    message: str
    evidence_uri: str = ""


class Falsification(BaseModel):
    model_config = ConfigDict(extra="forbid")
    gate_status: GateStatus = GateStatus.pass_
    scientific_valid: bool = False
    cross_model_disagreement: dict[str, Any] = Field(default_factory=dict)
    unit_check_passed: bool = True
    mass_balance_check_passed: bool = True
    boundary_check_passed: bool = True
    sbol_attestation_present: bool = False
    failures: list[FalsifierFailure] = Field(default_factory=list)


class Provenance(BaseModel):
    model_config = ConfigDict(extra="forbid")
    agent_id: str
    model_id: str
    git_sha: str
    created_at: str  # ISO-8601
    input_hash: str
    output_hash: str
    config_hash: str
    artifact_hashes: list[str] = Field(default_factory=list)
    source_refs: list[str] = Field(default_factory=list)
    sbol_uri: str | None = None
    prov_o_jsonld: str = ""

    @field_validator("created_at")
    @classmethod
    def created_at_is_iso8601(cls, v: str) -> str:
        # Round-trip parse to ensure ISO-8601.
        try:
            datetime.fromisoformat(v.replace("Z", "+00:00"))
        except ValueError as exc:  # pragma: no cover
            raise ValueError(f"created_at must be ISO-8601: {v}") from exc
        return v


class UniversalLayerEnvelope(BaseModel):
    """The synbio universal layer envelope.

    Every adapter emits one. Field-level validation is in the per-field
    classes; cross-field invariants are enforced in `_check_invariants`.
    """

    model_config = ConfigDict(extra="forbid", validate_assignment=True)

    schema_version: Literal["synbio.envelope.v0.1"] = SCHEMA_VERSION  # type: ignore[assignment]
    boundary: str
    envelope_id: str  # sha256 with envelope_id field zeroed during canonicalisation
    campaign_id: str
    run_id: uuid.UUID
    layer: Layer
    domain: Domain
    organism: int  # NCBI taxonomy id
    gem_id: str
    mode: RunMode
    backend: Backend
    inputs: Inputs
    outputs: Outputs
    uncertainty: Uncertainty
    falsification: Falsification
    provenance: Provenance

    @field_validator("boundary")
    @classmethod
    def boundary_must_match(cls, v: str) -> str:
        if v != BOUNDARY_BLOCK:
            actual_hash = hashlib.sha256(v.encode("utf-8")).hexdigest()
            raise BoundaryGateError(
                "Boundary block does not match canonical text "
                f"(expected sha256 {BOUNDARY_SHA256}, got {actual_hash})"
            )
        return v

    @model_validator(mode="after")
    def _check_invariants(self) -> "UniversalLayerEnvelope":
        # Stubs cannot claim scientific validity.
        is_stub_mode = (
            self.mode in (RunMode.engineering_stub, RunMode.replay)
            or self.backend.execution_mode == ExecutionMode.gpu_rest_stub
        )
        if is_stub_mode and self.falsification.scientific_valid:
            raise BoundaryGateError(
                "Stub envelopes (mode in {engineering_stub,replay} or "
                "execution_mode=gpu_rest_stub) MUST NOT set "
                "falsification.scientific_valid=True. Stubs satisfy engineering "
                "acceptance only."
            )

        # L6 envelopes require an SBOL3 attestation flag.
        if self.layer == Layer.L6 and not self.falsification.sbol_attestation_present:
            raise BoundaryGateError(
                "L6 envelopes must set falsification.sbol_attestation_present=True; "
                "every GeneticModificationSpec is SBOL3-attested per PRD §4.2 and §9.5."
            )

        # boundary_check_passed must be True iff boundary text is canonical.
        # (boundary_must_match validator already enforced text equality, so
        # boundary_check_passed must reflect it.)
        if not self.falsification.boundary_check_passed:
            raise BoundaryGateError(
                "boundary_check_passed must be True; boundary text is canonical."
            )
        return self


def canonical_json(obj: Any) -> bytes:
    """Canonical JSON serialisation: keys sorted, no whitespace, UTF-8."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def _stable_dump(model: BaseModel) -> dict[str, Any]:
    """Pydantic dump with stable ordering of all dict fields and string-coerced UUIDs."""
    raw = model.model_dump(mode="json")
    return raw  # mode=json already coerces UUIDs/datetimes to strings


def compute_envelope_id(envelope: UniversalLayerEnvelope) -> str:
    """Compute the canonical envelope_id sha256.

    The envelope_id field is replaced with a placeholder before hashing so
    that the hash is stable across (re)constructions.
    """
    dump = _stable_dump(envelope)
    dump["envelope_id"] = ""
    blob = canonical_json(dump)
    return "sha256:" + hashlib.sha256(blob).hexdigest()


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def empty_provenance(agent_id: str, model_id: str, git_sha: str) -> Provenance:
    """Build a Provenance block with empty hashes for envelope construction.

    Hashes are set by the adapter once inputs/outputs are determined.
    """
    return Provenance(
        agent_id=agent_id,
        model_id=model_id,
        git_sha=git_sha,
        created_at=now_iso(),
        input_hash="",
        output_hash="",
        config_hash="",
        artifact_hashes=[],
        source_refs=[],
        sbol_uri=None,
        prov_o_jsonld="",
    )


__all__ = [
    "SCHEMA_VERSION",
    "BoundaryGateError",
    "Layer",
    "Domain",
    "RunMode",
    "ExecutionMode",
    "LicenseClass",
    "GateStatus",
    "UncertaintyDistribution",
    "ContributorTag",
    "Reference",
    "Backend",
    "Inputs",
    "Outputs",
    "Uncertainty",
    "FalsifierFailure",
    "Falsification",
    "Provenance",
    "UniversalLayerEnvelope",
    "canonical_json",
    "compute_envelope_id",
    "now_iso",
    "empty_provenance",
]
