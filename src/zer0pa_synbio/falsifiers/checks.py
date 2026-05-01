"""Falsifier implementations.

One callable per registry entry. Each takes an `evidence` dict whose shape
matches the falsifier's `evidence_schema`, returns a `FalsifierResult`.

Implementations are CPU-only. Where a check requires GPU-bound model output
(cross-model kinetics disagreement, RFdiffusion3 motif RMSD, MACE-OFF binding
energy), the falsifier consumes pre-computed evidence emitted by the
upstream adapter — the falsifier itself does not run the GPU model. This
preserves the stub/CPU/Runpod-invariance: the falsifier's input shape is the
same regardless of where the upstream computation ran.
"""

from __future__ import annotations

import hashlib
from typing import Any, Callable

from zer0pa_synbio.boundary import BOUNDARY_BLOCK, BOUNDARY_SHA256
from zer0pa_synbio.falsifiers import REGISTRY, FalsifierResult


def _spec(falsifier_id: str):
    if falsifier_id not in REGISTRY:
        raise KeyError(f"Unknown falsifier: {falsifier_id}")
    return REGISTRY[falsifier_id]


def _result(falsifier_id: str, triggered: bool, message: str = "", evidence: dict[str, Any] | None = None) -> FalsifierResult:
    spec = _spec(falsifier_id)
    return FalsifierResult(
        falsifier_id=falsifier_id,
        triggered=triggered,
        severity=spec.severity,
        gate_action=spec.gate_action,
        message=message,
        evidence=evidence or {},
    )


# ─── Tier A ────────────────────────────────────────────────────────────────

def check_f000_boundary_violation(evidence: dict[str, Any]) -> FalsifierResult:
    """`evidence` carries `boundary_text: str`. Triggered if the text doesn't
    match BOUNDARY_BLOCK exactly (sha256 mismatch)."""
    text = evidence.get("boundary_text", "")
    actual = hashlib.sha256(text.encode("utf-8")).hexdigest()
    triggered = actual != BOUNDARY_SHA256
    return _result(
        "f000_boundary_violation",
        triggered,
        message=("Boundary block mutated" if triggered else "Boundary block matches"),
        evidence={"observed_sha256": actual, "expected_sha256": BOUNDARY_SHA256},
    )


def check_f001_invalid_selfies(evidence: dict[str, Any]) -> FalsifierResult:
    """`evidence` carries `selfies: str`. Triggered if selfies fails to decode
    or the resulting SMILES doesn't parse via RDKit. Both libraries are
    optional; if absent, the check is treated as a skip (triggered=False with
    a 'skipped' note)."""
    s = evidence.get("selfies", "")
    if not s:
        return _result("f001_invalid_selfies", True, "Empty SELFIES string", evidence={"offending_selfies": s})
    try:
        import selfies as sf  # type: ignore[import-not-found]
        from rdkit import Chem  # type: ignore[import-not-found]
    except ImportError:
        return _result(
            "f001_invalid_selfies",
            False,
            "SKIPPED: selfies/rdkit not installed; falsifier downgraded to no-op on this code path",
            evidence={"offending_selfies": s, "skipped": True},
        )
    try:
        smiles = sf.decoder(s)
        mol = Chem.MolFromSmiles(smiles) if smiles else None
        if mol is None:
            return _result(
                "f001_invalid_selfies",
                True,
                f"SELFIES decoded to SMILES={smiles!r} but RDKit could not parse",
                evidence={"offending_selfies": s, "decoded_smiles": smiles},
            )
        return _result("f001_invalid_selfies", False, "SELFIES parses cleanly")
    except Exception as exc:  # SELFIES decoder raises on malformed input
        return _result(
            "f001_invalid_selfies",
            True,
            f"SELFIES decoder raised: {exc}",
            evidence={"offending_selfies": s, "parse_error": str(exc)},
        )


def check_f002_mass_balance_violation(evidence: dict[str, Any]) -> FalsifierResult:
    """`evidence` carries `substrate_atoms: dict[str,int]`, `product_atoms:
    dict[str,int]`, `ignore_elements: list[str]` (default ['H'] for proton
    balancing). Triggered if any non-ignored element has nonzero delta."""
    sub = evidence.get("substrate_atoms", {})
    pro = evidence.get("product_atoms", {})
    ignore = set(evidence.get("ignore_elements", ["H"]))
    keys = (set(sub) | set(pro)) - ignore
    delta = {k: pro.get(k, 0) - sub.get(k, 0) for k in keys}
    bad = {k: v for k, v in delta.items() if v != 0}
    return _result(
        "f002_mass_balance_violation",
        bool(bad),
        message=("Atom balance violated" if bad else "Atom balance OK"),
        evidence={"substrate_atoms": sub, "product_atoms": pro, "delta": delta},
    )


def check_f003_mdf_infeasibility(evidence: dict[str, Any]) -> FalsifierResult:
    """`evidence` carries `mdf_kj_mol: float` (MDF score in kJ/mol).
    Triggered if mdf_kj_mol < 0 (no concentration assignment makes the
    pathway thermodynamically feasible)."""
    mdf = float(evidence.get("mdf_kj_mol", 0.0))
    triggered = mdf < 0.0
    return _result(
        "f003_mdf_infeasibility",
        triggered,
        message=f"MDF = {mdf} kJ/mol",
        evidence={"mdf_kj_mol": mdf, "bottleneck_step": evidence.get("bottleneck_step", "")},
    )


def check_f004_toxic_intermediate(evidence: dict[str, Any]) -> FalsifierResult:
    """`evidence` carries `qsar_alert: str | None`, `confidence: float`.
    Triggered if a structural alert is present at >0 confidence."""
    alert = evidence.get("qsar_alert")
    conf = float(evidence.get("confidence", 0.0))
    triggered = bool(alert) and conf > 0.0
    return _result(
        "f004_toxic_intermediate",
        triggered,
        message=(f"QSAR alert: {alert} (confidence={conf})" if triggered else "No QSAR alert"),
        evidence={"qsar_alert": alert, "confidence": conf},
    )


def check_f005_stoichiometric_infeasibility(evidence: dict[str, Any]) -> FalsifierResult:
    """`evidence` carries `cofactor: str`, `required_flux: float`,
    `native_capacity: float`. Triggered if required/native > 10×."""
    req = float(evidence.get("required_flux", 0.0))
    cap = float(evidence.get("native_capacity", 1.0))
    if cap <= 0:
        return _result(
            "f005_stoichiometric_infeasibility",
            True,
            "Native cofactor regeneration capacity <= 0; pathway infeasible",
            evidence=evidence,
        )
    ratio = req / cap
    triggered = ratio > 10.0
    return _result(
        "f005_stoichiometric_infeasibility",
        triggered,
        message=f"Cofactor flux ratio = {ratio:.2f} (threshold 10×)",
        evidence={"cofactor": evidence.get("cofactor"), "required_flux": req, "native_capacity": cap, "ratio": ratio},
    )


# ─── Tier B ────────────────────────────────────────────────────────────────

def _disagreement(values: list[float]) -> float:
    """Sigma-normalised dispersion: range / mean, fallback to range alone if mean ~ 0."""
    if not values:
        return 0.0
    lo, hi = min(values), max(values)
    mean = sum(values) / len(values)
    if abs(mean) < 1e-12:
        return float(hi - lo)
    return float((hi - lo) / abs(mean))


def check_f006_kinetics_disagreement_high(evidence: dict[str, Any]) -> FalsifierResult:
    """`evidence` carries `values: list[float]` (per-model kcat or Km),
    `threshold: float` (default 0.5 = 50% relative spread)."""
    values = list(evidence.get("values", []))
    threshold = float(evidence.get("threshold", 0.5))
    score = _disagreement(values)
    triggered = score > threshold
    return _result(
        "f006_kinetics_disagreement_high",
        triggered,
        message=f"Kinetics ensemble dispersion = {score:.3f} (threshold {threshold})",
        evidence={**evidence, "sigma_normalised_disagreement": score},
    )


def check_f007_fba_disagreement_high(evidence: dict[str, Any]) -> FalsifierResult:
    """Same dispersion logic as f006 but for FBA flux predictions."""
    values = list(evidence.get("values", []))
    threshold = float(evidence.get("threshold", 0.4))
    score = _disagreement(values)
    triggered = score > threshold
    return _result(
        "f007_fba_disagreement_high",
        triggered,
        message=f"FBA ensemble dispersion = {score:.3f} (threshold {threshold})",
        evidence={**evidence, "sigma_normalised_disagreement": score},
    )


def check_f008_retrosynthesis_disagreement_high(evidence: dict[str, Any]) -> FalsifierResult:
    """`evidence` carries `tool_route_sets: dict[str, list[str]]` mapping
    each retrosynthesis tool to the route IDs it proposed for the target.
    Computes pairwise Jaccard distance and triggers if max > threshold."""
    sets: dict[str, list[str]] = evidence.get("tool_route_sets", {})
    threshold = float(evidence.get("threshold", 0.7))
    if len(sets) < 2:
        return _result(
            "f008_retrosynthesis_disagreement_high",
            False,
            "Fewer than two retrosynthesis tools reporting; no disagreement to compute",
            evidence=evidence,
        )
    items = list(sets.values())
    max_jaccard_distance = 0.0
    for i in range(len(items)):
        for j in range(i + 1, len(items)):
            a = set(items[i])
            b = set(items[j])
            union = a | b
            inter = a & b
            j_sim = (len(inter) / len(union)) if union else 1.0
            j_dist = 1.0 - j_sim
            if j_dist > max_jaccard_distance:
                max_jaccard_distance = j_dist
    triggered = max_jaccard_distance > threshold
    return _result(
        "f008_retrosynthesis_disagreement_high",
        triggered,
        message=f"Max pairwise Jaccard distance = {max_jaccard_distance:.3f} (threshold {threshold})",
        evidence={**evidence, "jaccard_distance": max_jaccard_distance},
    )


def check_f009_novelty_without_retrosynthesis(evidence: dict[str, Any]) -> FalsifierResult:
    """`evidence` carries `novelty_class: str`, `retrosynthesis_proposing_count: int`."""
    nc = evidence.get("novelty_class", "")
    count = int(evidence.get("retrosynthesis_proposing_count", 0))
    triggered = nc == "fully_novel" and count == 0
    return _result(
        "f009_novelty_without_retrosynthesis",
        triggered,
        message=(
            "Fully novel pathway with zero retrosynthesis tool support; routing to L4.5 unknown-enzyme"
            if triggered else "OK"
        ),
        evidence=evidence,
    )


def check_f010_novelty_without_ts_analog(evidence: dict[str, Any]) -> FalsifierResult:
    """`evidence` carries `novelty_class: str`, `ts_analog_search_result: dict` with
    `found: bool`."""
    nc = evidence.get("novelty_class", "")
    found = bool(evidence.get("ts_analog_search_result", {}).get("found", False))
    triggered = nc == "fully_novel" and not found
    return _result(
        "f010_novelty_without_ts_analog",
        triggered,
        message=(
            "Fully novel reaction class with no TS analog in LIRC; Tier-3 advisory only"
            if triggered else "OK"
        ),
        evidence=evidence,
    )


def check_f011_cekm_survivorship_bias_check(evidence: dict[str, Any]) -> FalsifierResult:
    """`evidence` carries `cekm_value: float`, `ensemble_value: float`,
    `threshold: float` (relative gap)."""
    cekm = float(evidence.get("cekm_value", 0.0))
    ens = float(evidence.get("ensemble_value", 0.0))
    threshold = float(evidence.get("threshold", 1.0))  # 1.0 = 100% relative diff
    if abs(ens) < 1e-12:
        rel = float("inf") if abs(cekm) > 1e-12 else 0.0
    else:
        rel = abs(cekm - ens) / abs(ens)
    triggered = rel > threshold
    return _result(
        "f011_cekm_survivorship_bias_check",
        triggered,
        message=f"CEKM-vs-ensemble relative gap = {rel:.3f} (threshold {threshold})",
        evidence={**evidence, "relative_gap": rel},
    )


def check_f012_codec_as_mechanism_analog(evidence: dict[str, Any]) -> FalsifierResult:
    """`evidence` carries `mechanism_chain: list[str]`. Triggered if empty —
    a KPI prediction must have a mechanistic chain to a genotype-level
    intervention."""
    chain = list(evidence.get("mechanism_chain", []))
    triggered = len(chain) == 0
    return _result(
        "f012_codec_as_mechanism_analog",
        triggered,
        message="No mechanism chain; KPI prediction has no genotype-level grounding" if triggered else "OK",
        evidence={**evidence, "missing_mechanism_chain": triggered},
    )


# ─── Tier C ────────────────────────────────────────────────────────────────


def check_f013_rfdiffusion3_motif_infeasible(evidence: dict[str, Any]) -> FalsifierResult:
    """`evidence` carries `motif_rmsd: float`, `threshold: float` (default 2.0 Å)."""
    rmsd = float(evidence.get("motif_rmsd", 0.0))
    threshold = float(evidence.get("threshold", 2.0))
    triggered = rmsd > threshold
    return _result(
        "f013_rfdiffusion3_motif_infeasible",
        triggered,
        message=f"Motif RMSD = {rmsd:.2f} Å (threshold {threshold})",
        evidence={**evidence},
    )


def check_f014_mace_off_binding_implausible(evidence: dict[str, Any]) -> FalsifierResult:
    """`evidence` carries `binding_energy_kj_mol: float`, `reference_range:
    dict[str,float]` with `lo` and `hi`."""
    be = float(evidence.get("binding_energy_kj_mol", 0.0))
    ref = evidence.get("reference_range", {})
    lo = float(ref.get("lo", -200.0))
    hi = float(ref.get("hi", 0.0))
    triggered = be < lo or be > hi
    return _result(
        "f014_mace_off_binding_implausible",
        triggered,
        message=f"Binding energy {be} kJ/mol outside [{lo}, {hi}]" if triggered else "OK",
        evidence={**evidence},
    )


def check_f015_prody_nma_misaligned(evidence: dict[str, Any]) -> FalsifierResult:
    """`evidence` carries `catalytic_coordinate_alignment: float` (cosine
    similarity in [0,1]), `threshold: float`."""
    align = float(evidence.get("catalytic_coordinate_alignment", 0.0))
    threshold = float(evidence.get("threshold", 0.5))
    triggered = align < threshold
    return _result(
        "f015_prody_nma_misaligned",
        triggered,
        message=f"NMA alignment = {align:.3f} (threshold {threshold})",
        evidence={**evidence},
    )


def check_f016_tda_regime_change(evidence: dict[str, Any]) -> FalsifierResult:
    """`evidence` carries `warning_score: float`, `threshold: float`,
    `failure_mode: str`."""
    score = float(evidence.get("warning_score", 0.0))
    threshold = float(evidence.get("threshold", 0.6))
    triggered = score > threshold
    return _result(
        "f016_tda_regime_change",
        triggered,
        message=f"TDA warning score = {score:.3f} (threshold {threshold})",
        evidence={**evidence},
    )


_CLASS_A_OR_B = {"A", "B"}


def check_f017_industrial_scale_uncalibrated(evidence: dict[str, Any]) -> FalsifierResult:
    """`evidence` carries `claimed_scale: str`, `cited_corpus_uri: str`,
    `corpus_license_class: str`. Triggered if scale=='industrial' and
    license_class is not Class A or B with a manifest URI."""
    scale = evidence.get("claimed_scale", "")
    uri = evidence.get("cited_corpus_uri", "")
    cls = evidence.get("corpus_license_class", "")
    triggered = scale == "industrial" and (cls not in _CLASS_A_OR_B or not uri)
    return _result(
        "f017_industrial_scale_uncalibrated",
        triggered,
        message=(
            f"Industrial-scale KPI claim with corpus={uri!r} class={cls!r}"
            if triggered else "OK"
        ),
        evidence=evidence,
    )


_FORBIDDEN_SOURCES = {
    "bkms-react",
    "bkms_react",
    "bkmsreact",
    "kegg-bulk",
    "kegg_bulk",
    "atlas-of-biochemistry",
    "atlas_of_biochemistry",
}


def check_f018_license_drift(evidence: dict[str, Any]) -> FalsifierResult:
    """`evidence` carries `offending_source_uri: str`, `license_class: str`,
    `license_grant_present: bool`. Triggered if the source is forbidden, OR
    license class C/D/E and no grant is present."""
    uri = evidence.get("offending_source_uri", "").lower()
    cls = evidence.get("license_class", "")
    grant_present = bool(evidence.get("license_grant_present", False))
    if any(forbidden in uri for forbidden in _FORBIDDEN_SOURCES):
        return _result(
            "f018_license_drift",
            True,
            f"Forbidden source cited: {uri}",
            evidence=evidence,
        )
    if cls in {"C", "D", "E"} and not grant_present:
        return _result(
            "f018_license_drift",
            True,
            f"Class {cls} source without license grant",
            evidence=evidence,
        )
    return _result("f018_license_drift", False, "OK", evidence=evidence)


def check_f019_valid_sbol_only(evidence: dict[str, Any]) -> FalsifierResult:
    """`evidence` carries `sbol3_uri: str` (path to a local SBOL3 file).
    Validates via the `sbol3` Python package; triggered on parse/validation
    failure."""
    uri = evidence.get("sbol3_uri", "")
    if not uri:
        return _result("f019_valid_sbol_only", True, "Missing sbol3_uri", evidence=evidence)
    try:
        import sbol3  # type: ignore[import-not-found]
    except ImportError:
        return _result(
            "f019_valid_sbol_only",
            False,
            "SKIPPED: sbol3 package not installed",
            evidence={**evidence, "skipped": True},
        )
    try:
        doc = sbol3.Document()
        doc.read(uri)
        # Validate strictly.
        report = doc.validate()
        if report and len(report) > 0:
            return _result(
                "f019_valid_sbol_only",
                True,
                f"SBOL3 validator messages: {len(report)}",
                evidence={**evidence, "libsbolj3_validator_messages": [str(m) for m in report]},
            )
        return _result("f019_valid_sbol_only", False, "SBOL3 valid", evidence=evidence)
    except Exception as exc:
        return _result(
            "f019_valid_sbol_only",
            True,
            f"SBOL3 read/validate failed: {exc}",
            evidence={**evidence, "error": str(exc)},
        )


def check_f020_txtl_observation_without_in_vivo(evidence: dict[str, Any]) -> FalsifierResult:
    """`evidence` carries `consumer_decision: str`, `in_vivo_corroboration_present: bool`."""
    decision = evidence.get("consumer_decision", "")
    in_vivo = bool(evidence.get("in_vivo_corroboration_present", False))
    triggered = bool(decision) and not in_vivo
    return _result(
        "f020_txtl_observation_without_in_vivo",
        triggered,
        message=(
            f"Cell-free observation drives decision={decision!r} without in-vivo corroboration"
            if triggered else "OK"
        ),
        evidence=evidence,
    )


def check_f021_reaction_not_atom_balanced(evidence: dict[str, Any]) -> FalsifierResult:
    """LIRC import-time atom balance. Same shape as f002 but invoked on raw
    imports rather than on per-pathway-step composition."""
    return check_f002_mass_balance_violation(evidence).model_copy(
        update={"falsifier_id": "f021_reaction_not_atom_balanced"}
    )


def check_f022_validation_sequence_unreachable(evidence: dict[str, Any]) -> FalsifierResult:
    """`evidence` carries `consumer: str`, `configured_consumers: list[str]`."""
    consumer = evidence.get("consumer", "")
    configured = list(evidence.get("configured_consumers", []))
    triggered = consumer not in configured
    return _result(
        "f022_validation_sequence_unreachable",
        triggered,
        message=(
            f"Consumer {consumer!r} not in configured set {configured}"
            if triggered else "OK"
        ),
        evidence=evidence,
    )


# ─── dispatch table ────────────────────────────────────────────────────────


CHECKS: dict[str, Callable[[dict[str, Any]], FalsifierResult]] = {
    "f000_boundary_violation": check_f000_boundary_violation,
    "f001_invalid_selfies": check_f001_invalid_selfies,
    "f002_mass_balance_violation": check_f002_mass_balance_violation,
    "f003_mdf_infeasibility": check_f003_mdf_infeasibility,
    "f004_toxic_intermediate": check_f004_toxic_intermediate,
    "f005_stoichiometric_infeasibility": check_f005_stoichiometric_infeasibility,
    "f006_kinetics_disagreement_high": check_f006_kinetics_disagreement_high,
    "f007_fba_disagreement_high": check_f007_fba_disagreement_high,
    "f008_retrosynthesis_disagreement_high": check_f008_retrosynthesis_disagreement_high,
    "f009_novelty_without_retrosynthesis": check_f009_novelty_without_retrosynthesis,
    "f010_novelty_without_ts_analog": check_f010_novelty_without_ts_analog,
    "f011_cekm_survivorship_bias_check": check_f011_cekm_survivorship_bias_check,
    "f012_codec_as_mechanism_analog": check_f012_codec_as_mechanism_analog,
    "f013_rfdiffusion3_motif_infeasible": check_f013_rfdiffusion3_motif_infeasible,
    "f014_mace_off_binding_implausible": check_f014_mace_off_binding_implausible,
    "f015_prody_nma_misaligned": check_f015_prody_nma_misaligned,
    "f016_tda_regime_change": check_f016_tda_regime_change,
    "f017_industrial_scale_uncalibrated": check_f017_industrial_scale_uncalibrated,
    "f018_license_drift": check_f018_license_drift,
    "f019_valid_sbol_only": check_f019_valid_sbol_only,
    "f020_txtl_observation_without_in_vivo": check_f020_txtl_observation_without_in_vivo,
    "f021_reaction_not_atom_balanced": check_f021_reaction_not_atom_balanced,
    "f022_validation_sequence_unreachable": check_f022_validation_sequence_unreachable,
}


def run(falsifier_id: str, evidence: dict[str, Any]) -> FalsifierResult:
    """Dispatch entrypoint."""
    if falsifier_id not in CHECKS:
        raise KeyError(f"No implementation for falsifier {falsifier_id}")
    return CHECKS[falsifier_id](evidence)


def assert_complete_coverage() -> None:
    """Sanity check: every registry entry has a matching implementation."""
    missing = set(REGISTRY) - set(CHECKS)
    extra = set(CHECKS) - set(REGISTRY)
    if missing:
        raise RuntimeError(f"Falsifier registry has entries without implementations: {missing}")
    if extra:
        raise RuntimeError(f"Falsifier implementations without registry entries: {extra}")


# Run coverage assertion at import time.
assert_complete_coverage()


__all__ = ["CHECKS", "run", "assert_complete_coverage"]
