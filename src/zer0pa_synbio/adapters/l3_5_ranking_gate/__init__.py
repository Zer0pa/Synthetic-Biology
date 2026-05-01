"""L3.5 learnable pathway ranking gate.

Per PRD §6.4: thresholds are state, stored in `audit/l3_5_thresholds.json`.
Reject criteria: MDF, cofactor flux, toxic intermediate, retrosynthesis
disagreement.
"""

from __future__ import annotations

import json
import uuid
from pathlib import Path
from typing import Any

from zer0pa_synbio.adapters import LayerAdapter
from zer0pa_synbio.envelope import Domain, Layer, LicenseClass, UniversalLayerEnvelope


_DEFAULT_THRESHOLDS = {
    "tau_mdf_kj_mol": 1.0,
    "tau_cofactor_flux_ratio": 10.0,
    "tau_toxic_severity": 0.5,
    "tau_retrosynthesis_jaccard": 0.7,
}


def _load_thresholds(repo_root: Path) -> dict[str, float]:
    p = repo_root / "audit" / "l3_5_thresholds.json"
    if p.exists():
        try:
            return json.loads(p.read_text())
        except Exception:
            return dict(_DEFAULT_THRESHOLDS)
    return dict(_DEFAULT_THRESHOLDS)


class L3_5RankingGateAdapter(LayerAdapter):
    layer = Layer.L3_5
    adapter_name = "L3_5RankingGateAdapter"
    tool_name = "zer0pa_l3_5_thresholds"
    tool_version = "zer0pa.l3_5.v0.1"
    license_class = LicenseClass.A
    license_evidence_uri = "audit/source_manifests/metanetx.yaml"

    def run(
        self, *, campaign_id, domain, organism, gem_id, input_payload, run_id=None
    ) -> UniversalLayerEnvelope:
        repo_root = Path(__file__).resolve().parents[4]
        thresholds = _load_thresholds(repo_root)
        candidates = input_payload.get("candidates", [])
        # Annotate each with cheap-to-compute reject signals; do not actually
        # reject here — caller filters.
        annotated = []
        for c in candidates:
            steps = c.get("steps", [])
            min_dg = min((s.get("delta_g_kj_mol", 0.0) for s in steps), default=0.0)
            mdf_proxy = -min_dg if steps else 0.0
            annotated.append(
                {
                    **c,
                    "ranking_gate": {
                        "mdf_proxy_kj_mol": mdf_proxy,
                        "tau_mdf_kj_mol": thresholds["tau_mdf_kj_mol"],
                        "passes_mdf_gate": mdf_proxy >= thresholds["tau_mdf_kj_mol"],
                        "passes_disagreement_gate": c.get("cross_tool_disagreement_signal", 0.0)
                        <= thresholds["tau_retrosynthesis_jaccard"],
                    },
                }
            )
        out = {
            "schema_version": "synbio.pathway_candidate_set.v0.1",
            "candidates": annotated,
            "thresholds": thresholds,
            "thresholds_source": "audit/l3_5_thresholds.json (default)",
        }
        return self._make_envelope(
            campaign_id=campaign_id,
            domain=domain,
            organism=organism,
            gem_id=gem_id,
            input_payload=input_payload,
            output_payload=out,
            run_id=run_id,
        )


__all__ = ["L3_5RankingGateAdapter", "_DEFAULT_THRESHOLDS"]
