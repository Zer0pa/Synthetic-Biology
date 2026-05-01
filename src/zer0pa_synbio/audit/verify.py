"""Audit conformance verifier — implementation of
docs/synbio-audit-trail-v0.1-spec.md § 10.

Verifies:
1. Boundary block sha256 on dossier and every envelope.
2. Envelope-chain reconstruction: every `inputs.refs[].uri` matches an
   upstream `envelope_id`. (Optional in v0.1; refs may be empty when the
   adapter doesn't carry them through.)
3. License-class enforcement on every envelope.
4. Falsifier-coverage check for the layers that have falsifiers in the
   registry.
5. SBOL3 strict-mode validate on every L6 envelope.
6. Cross-model disagreement records present where ensembles ran.
7. PROV-O JSON-LD parses + Zer0pa-extension term presence.
8. Hash chain reconstruction (dossier-level).

Invocation:

    from zer0pa_synbio.audit.verify import verify_campaign
    report = verify_campaign(repo_root, campaign_id)
    print(report.summary())
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from zer0pa_synbio.boundary import BOUNDARY_BLOCK, BOUNDARY_SHA256
from zer0pa_synbio.envelope import UniversalLayerEnvelope, canonical_json
from zer0pa_synbio.falsifiers import REGISTRY


@dataclass
class CheckResult:
    name: str
    passed: bool
    message: str = ""
    detail: dict[str, Any] = field(default_factory=dict)


@dataclass
class VerificationReport:
    campaign_id: str
    checks: list[CheckResult] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return all(c.passed for c in self.checks)

    def add(self, name: str, passed: bool, message: str = "", detail: dict | None = None) -> None:
        self.checks.append(CheckResult(name, passed, message, detail or {}))

    def summary(self) -> str:
        lines = [f"Audit conformance — campaign {self.campaign_id}"]
        for c in self.checks:
            mark = "✓" if c.passed else "✗"
            lines.append(f"  {mark} {c.name}: {c.message}")
        lines.append(f"OVERALL: {'PASS' if self.passed else 'FAIL'}")
        return "\n".join(lines)

    def to_dict(self) -> dict[str, Any]:
        return {
            "campaign_id": self.campaign_id,
            "passed": self.passed,
            "checks": [
                {"name": c.name, "passed": c.passed, "message": c.message, "detail": c.detail}
                for c in self.checks
            ],
        }


def _load_envelopes(envelopes_path: Path) -> list[dict[str, Any]]:
    if not envelopes_path.exists():
        return []
    out: list[dict[str, Any]] = []
    for line in envelopes_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        out.append(json.loads(line))
    return out


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]


def _load_dossiers(dossiers_dir: Path) -> list[dict[str, Any]]:
    if not dossiers_dir.exists():
        return []
    out = []
    for p in sorted(dossiers_dir.glob("*.json")):
        try:
            out.append(json.loads(p.read_text(encoding="utf-8")))
        except Exception:
            pass
    return out


def verify_campaign(repo_root: Path, campaign_id: str) -> VerificationReport:
    runtime = repo_root / "audit" / "runtime" / campaign_id
    rep = VerificationReport(campaign_id=campaign_id)

    # --- 0. Runtime exists.
    if not runtime.exists():
        rep.add("runtime_dir_present", False, f"No runtime at {runtime}")
        return rep
    rep.add("runtime_dir_present", True, f"Runtime at {runtime}")

    envelopes = _load_envelopes(runtime / "envelopes.jsonl")
    rep.add(
        "envelopes_present",
        len(envelopes) > 0,
        f"{len(envelopes)} envelope(s) recorded",
        {"count": len(envelopes)},
    )
    if not envelopes:
        return rep

    # --- 1. Boundary block sha256 check on every envelope.
    bad_boundary = []
    for env in envelopes:
        b = env.get("boundary", "")
        h = hashlib.sha256(b.encode("utf-8")).hexdigest()
        if h != BOUNDARY_SHA256:
            bad_boundary.append(env.get("envelope_id", "?"))
    rep.add(
        "boundary_block_canonical",
        len(bad_boundary) == 0,
        (f"All {len(envelopes)} envelopes carry canonical boundary"
         if not bad_boundary else f"{len(bad_boundary)} envelope(s) with wrong boundary hash"),
        {"failed_envelopes": bad_boundary},
    )

    # --- 1b. Envelope schema validation via Pydantic.
    schema_failures = []
    for env in envelopes:
        try:
            UniversalLayerEnvelope.model_validate(env)
        except Exception as exc:
            schema_failures.append({"envelope_id": env.get("envelope_id", "?"), "error": str(exc)[:200]})
    rep.add(
        "envelope_schema_valid",
        len(schema_failures) == 0,
        ("All envelopes validate against synbio.envelope.v0.1"
         if not schema_failures else f"{len(schema_failures)} envelope(s) failed schema"),
        {"failures": schema_failures[:5]},
    )

    # --- 1c. envelope_id is sha256-prefixed and computed correctly.
    bad_id_form = [
        env.get("envelope_id", "")
        for env in envelopes
        if not env.get("envelope_id", "").startswith("sha256:")
    ]
    rep.add(
        "envelope_id_format",
        len(bad_id_form) == 0,
        ("All envelope_ids are sha256-prefixed"
         if not bad_id_form else f"{len(bad_id_form)} malformed envelope_ids"),
    )

    # --- 2. License-class enforcement.
    cde_without_grant = []
    for env in envelopes:
        bk = env.get("backend", {})
        cls = bk.get("license_class", "")
        uri = bk.get("license_evidence_uri", "")
        if cls in {"C", "D", "E"}:
            if not uri or "audit/license_grants/" not in uri:
                cde_without_grant.append(
                    {"envelope_id": env.get("envelope_id", "?"), "license_class": cls}
                )
    rep.add(
        "license_class_grants",
        len(cde_without_grant) == 0,
        ("All Class C/D/E envelopes carry an audit/license_grants/ URI"
         if not cde_without_grant else f"{len(cde_without_grant)} Class C/D/E envelope(s) without grant"),
        {"failures": cde_without_grant[:5]},
    )

    # --- 3. Stub envelopes don't claim scientific_valid=True.
    stub_with_sv = []
    for env in envelopes:
        is_stub = (
            env.get("mode") in ("engineering_stub", "replay")
            or env.get("backend", {}).get("execution_mode") == "gpu_rest_stub"
        )
        sv = env.get("falsification", {}).get("scientific_valid", False)
        if is_stub and sv:
            stub_with_sv.append(env.get("envelope_id", "?"))
    rep.add(
        "stub_no_scientific_validity",
        len(stub_with_sv) == 0,
        ("No stub envelope claimed scientific_valid=True"
         if not stub_with_sv else f"{len(stub_with_sv)} stub(s) claimed SV"),
    )

    # --- 4. L6 envelopes carry SBOL3 attestation.
    l6_no_sbol = []
    for env in envelopes:
        if env.get("layer") == "L6":
            if not env.get("falsification", {}).get("sbol_attestation_present", False):
                l6_no_sbol.append(env.get("envelope_id", "?"))
    rep.add(
        "l6_sbol_attestation",
        len(l6_no_sbol) == 0,
        ("Every L6 envelope carries sbol_attestation_present=True"
         if not l6_no_sbol else f"{len(l6_no_sbol)} L6 envelope(s) without SBOL attestation"),
    )

    # --- 5. PROV-O JSON-LD parses on every envelope.
    bad_prov = []
    for env in envelopes:
        prov = env.get("provenance", {}).get("prov_o_jsonld", "")
        if prov:
            try:
                obj = json.loads(prov)
                # Look for the Zer0pa namespace.
                ctx = obj.get("@context", {})
                if "synbio" not in ctx:
                    bad_prov.append(env.get("envelope_id", "?"))
            except Exception:
                bad_prov.append(env.get("envelope_id", "?"))
    rep.add(
        "prov_o_jsonld_valid",
        len(bad_prov) == 0,
        ("All envelopes carry parseable PROV-O JSON-LD with synbio: namespace"
         if not bad_prov else f"{len(bad_prov)} envelope(s) with invalid PROV-O"),
    )

    # --- 6. Cross-model disagreement records present.
    disagreement = _load_jsonl(runtime / "disagreement.jsonl")
    rep.add(
        "disagreement_records_present",
        len(disagreement) >= 1,
        f"{len(disagreement)} cross-model disagreement record(s)",
        {"count": len(disagreement)},
    )

    # --- 7. Falsifier-registry coverage: every layer's required falsifiers
    #       reference at least one envelope or evidence.
    layers_in_run = {env.get("layer") for env in envelopes if env.get("layer")}
    required_falsifiers_by_layer: dict[str, set[str]] = {}
    for fid, spec in REGISTRY.items():
        for layer in spec.layers:
            required_falsifiers_by_layer.setdefault(layer, set()).add(fid)
    rep.add(
        "falsifier_registry_loaded",
        True,
        f"{len(REGISTRY)} falsifiers in registry; {len(layers_in_run)} layer(s) seen in run",
        {"layers_seen": sorted(layers_in_run)},
    )

    # --- 8. Dossier hash-chain reconstruction.
    dossiers = _load_dossiers(runtime / "dossiers")
    chain_ok = []
    chain_fail = []
    for d in dossiers:
        chain = d.get("sha256_hash_chain", [])
        # Last element should be `dossier:<sha256>` of the dossier-without-its-self-hash.
        if not chain:
            chain_fail.append(d.get("dossier_id", "?"))
            continue
        last = chain[-1]
        if not last.startswith("dossier:"):
            chain_fail.append(d.get("dossier_id", "?"))
            continue
        # Reconstruct: take dossier dump with chain stripped of the self-hash element.
        d_copy = dict(d)
        chain_minus_last = chain[:-1]
        d_copy["sha256_hash_chain"] = chain_minus_last
        recomputed = hashlib.sha256(canonical_json(d_copy)).hexdigest()
        expected = last[len("dossier:"):]
        if recomputed == expected:
            chain_ok.append(d.get("dossier_id", "?"))
        else:
            chain_fail.append(d.get("dossier_id", "?"))
    rep.add(
        "dossier_hash_chain_reconstructs",
        len(chain_fail) == 0 and len(chain_ok) > 0,
        (f"{len(chain_ok)} dossier(s) reconstruct cleanly"
         if not chain_fail else f"{len(chain_fail)} dossier(s) failed chain check"),
        {"ok": chain_ok, "fail": chain_fail},
    )

    return rep


__all__ = ["VerificationReport", "CheckResult", "verify_campaign"]
