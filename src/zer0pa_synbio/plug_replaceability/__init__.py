"""Plug-replaceability harness.

Per PRD §4.5 (plug-replaceability invariant): any layer backend may be
replaced only if it preserves:
- Same UniversalLayerEnvelope.
- Same domain-payload schema version.
- Same REST endpoint shape and request/response surface.
- Same artifact manifest format.
- Same audit/KG writes.
- Same falsifier IDs.

Runpod cutover (PRD §4.5 final paragraph): accepted only when changing
a config flag from `gpu_rest_stub` to `runpod_rest` preserves golden
fixture behaviour except for runtime/provenance fields. The
`httpx.MockTransport` golden-fixture invariance test (Wave 11) is the
executable proof.

This module exposes:

- `compare_envelopes(a, b)`: return a list of structural differences,
  excluding runtime/provenance fields that are explicitly allowed to
  differ.
- `RUNTIME_VARIABLE_FIELDS`: the set of dotted paths within the envelope
  whose values may differ across backends.
"""

from __future__ import annotations

from typing import Any

from zer0pa_synbio.envelope import UniversalLayerEnvelope


# Dotted paths that are explicitly allowed to differ between backends.
RUNTIME_VARIABLE_FIELDS: frozenset[str] = frozenset(
    {
        "envelope_id",  # depends on contents (acceptable for runtime)
        "run_id",  # one per call
        "provenance.created_at",
        "provenance.git_sha",
        "provenance.prov_o_jsonld",  # may have a different timestamp
        "backend.execution_mode",  # the cutover changes this
        "backend.tool_version",  # may include backend tag
    }
)


def _flatten(d: Any, prefix: str = "") -> dict[str, Any]:
    """Recursively flatten a dict to dotted-path leaves. Lists are kept as-is."""
    out: dict[str, Any] = {}
    if isinstance(d, dict):
        for k, v in d.items():
            key = f"{prefix}.{k}" if prefix else k
            if isinstance(v, dict):
                out.update(_flatten(v, key))
            else:
                out[key] = v
    return out


def compare_envelopes(a: UniversalLayerEnvelope, b: UniversalLayerEnvelope) -> list[str]:
    """Return dotted paths where two envelopes differ (excluding runtime fields)."""
    da = _flatten(a.model_dump(mode="json"))
    db = _flatten(b.model_dump(mode="json"))
    keys = set(da) | set(db)
    diffs: list[str] = []
    for k in sorted(keys):
        if k in RUNTIME_VARIABLE_FIELDS:
            continue
        if da.get(k) != db.get(k):
            diffs.append(f"{k}: a={da.get(k)!r} b={db.get(k)!r}")
    return diffs


def assert_plug_replaceable(a: UniversalLayerEnvelope, b: UniversalLayerEnvelope) -> None:
    diffs = compare_envelopes(a, b)
    if diffs:
        raise AssertionError(
            "Envelopes differ on non-runtime fields; plug-replaceability fails:\n  "
            + "\n  ".join(diffs)
        )


__all__ = ["RUNTIME_VARIABLE_FIELDS", "compare_envelopes", "assert_plug_replaceable"]
