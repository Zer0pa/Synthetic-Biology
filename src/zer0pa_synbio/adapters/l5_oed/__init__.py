"""L5_OED — Goal-Oriented Causal Bayesian Experimental Design.

Per PRD §6.8: GO-CBED + CausalBench. CPU-only.
"""

from __future__ import annotations

import uuid
from typing import Any

from zer0pa_synbio.adapters import LayerAdapter
from zer0pa_synbio.envelope import Domain, Layer, LicenseClass, UniversalLayerEnvelope


class L5OEDAdapter(LayerAdapter):
    layer = Layer.L5_OED
    adapter_name = "L5OEDAdapter"
    tool_name = "go_cbed"
    tool_version = "go_cbed-stub-v0.1"
    license_class = LicenseClass.A
    license_evidence_uri = "audit/source_manifests/metanetx.yaml"

    def run(
        self, *, campaign_id, domain, organism, gem_id, input_payload, run_id=None
    ) -> UniversalLayerEnvelope:
        ranked = input_payload.get("ranked_candidates", [])
        # Top-3 candidates → propose three experiments (one each), with
        # decreasing expected information gain.
        experiments = []
        for i, c in enumerate(ranked[:3]):
            experiments.append(
                {
                    "experiment_id": f"exp_{i:03d}",
                    "intervention": {
                        "pathway_id": c.get("pathway_id", f"p_{i}"),
                        "knockin_genes": ["FutC"],
                        "promoter": "Ptrc",
                    },
                    "expected_information_gain_nats": 2.5 - 0.6 * i,
                    "consumer": "human_cro",
                    "cost_estimate_usd": 5000.0,
                    "expected_completion_days": 21,
                }
            )
        validation_sequence = {
            "schema_version": "synbio.validation_sequence.v0.1",
            "ordered_experiments": experiments,
            "go_cbed_objective": "max_information_gain_about_top_pareto_candidate",
            "posterior_uncertainty_kl_reduction_target": 1.5,
        }
        return self._make_envelope(
            campaign_id=campaign_id,
            domain=domain,
            organism=organism,
            gem_id=gem_id,
            input_payload=input_payload,
            output_payload={"validation_sequence": validation_sequence},
            run_id=run_id,
        )


__all__ = ["L5OEDAdapter"]
