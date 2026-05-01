"""FastAPI REST stubs for every GPU-bound endpoint.

Per PRD §17, the gpu_rest_stub backend is one FastAPI app exposing the
following endpoints. Each endpoint instantiates the corresponding adapter
in `gpu_rest_stub` execution mode, runs it, and returns the
`UniversalLayerEnvelope` JSON. The same schema validates stub, local_cpu,
and runpod_rest responses; the `httpx.MockTransport` invariance test
(Wave 11) is the executable proof.

Endpoints (PRD §17):

    POST /l1/zpe/embed                     → L1ZPEAdapter (gpu_rest_stub)
    POST /l3/bionavi/retrosynthesise       → L3BioNaviAdapter
    POST /l3/deepretro/retrosynthesise     → L3DeepRetroAdapter
    POST /l4/kinetics/ensemble             → L4 kinetics ensemble call
    POST /l4_5/rfdiffusion3/scaffold       → L4_5RFdiffusion3Adapter
    POST /l4_5/mace_off/binding            → L4_5MACEOFFAdapter
    POST /l4_5/esmfold/predict             → L4_5ESMFoldAdapter
    POST /l6_build/cellfree/stub           → L6BuildCellFreeStubAdapter
    POST /l6_build/cellfree/strateos       → L6BuildStrateosAdapter
    POST /l6_build/cellfree/emerald        → L6BuildEmeraldAdapter
"""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI, HTTPException

from zer0pa_synbio.adapters.l1_zpe import L1ZPEAdapter
from zer0pa_synbio.adapters.l3_retrosynthesis import (
    L3BioNaviAdapter,
    L3DeepRetroAdapter,
)
from zer0pa_synbio.adapters.l4_5_unknown_enzyme import (
    L4_5ESMFoldAdapter,
    L4_5MACEOFFAdapter,
    L4_5RFdiffusion3Adapter,
)
from zer0pa_synbio.adapters.l4_kinetics import (
    L4CatPredAdapter,
    L4CEKMAdapter,
    L4DLKcatAdapter,
    L4TurNuPAdapter,
)
from zer0pa_synbio.adapters.l6_build_cellfree_txtl import (
    L6BuildCellFreeStubAdapter,
    L6BuildEmeraldAdapter,
    L6BuildStrateosAdapter,
)
from zer0pa_synbio.envelope import Domain, ExecutionMode


def create_app() -> FastAPI:
    app = FastAPI(
        title="Zer0pa Synbio REST Stubs",
        description=(
            "GPU-bound endpoints in stub mode. Same envelope schema as local_cpu "
            "and runpod_rest; cutover is a config flag."
        ),
        version="0.1.0",
    )

    @app.get("/health")
    def health() -> dict[str, Any]:
        return {"status": "ok", "schema_version": "synbio.envelope.v0.1"}

    def _run_adapter_endpoint(adapter, body: dict[str, Any]) -> dict[str, Any]:
        try:
            campaign_id = body.get("campaign_id", "rest_stub")
            domain = Domain(body.get("domain", "hmo"))
            organism = int(body.get("organism", 562))
            gem_id = body.get("gem_id", "iML1515")
            input_payload = body.get("input_payload", {})
            env = adapter.run(
                campaign_id=campaign_id,
                domain=domain,
                organism=organism,
                gem_id=gem_id,
                input_payload=input_payload,
            )
            return env.model_dump(mode="json")
        except Exception as exc:
            raise HTTPException(status_code=400, detail=str(exc))

    @app.post("/l1/zpe/embed")
    def l1_zpe_embed(body: dict[str, Any]) -> dict[str, Any]:
        return _run_adapter_endpoint(
            L1ZPEAdapter(execution_mode=ExecutionMode.gpu_rest_stub), body
        )

    @app.post("/l3/bionavi/retrosynthesise")
    def l3_bionavi(body: dict[str, Any]) -> dict[str, Any]:
        return _run_adapter_endpoint(L3BioNaviAdapter(), body)

    @app.post("/l3/deepretro/retrosynthesise")
    def l3_deepretro(body: dict[str, Any]) -> dict[str, Any]:
        return _run_adapter_endpoint(L3DeepRetroAdapter(), body)

    @app.post("/l4/kinetics/ensemble")
    def l4_kinetics_ensemble(body: dict[str, Any]) -> dict[str, Any]:
        # Run the four-way kinetics ensemble; emit one envelope per model
        # plus a top-level disagreement record.
        envs = {}
        for cls, name in (
            (L4DLKcatAdapter, "DLKcat"),
            (L4CatPredAdapter, "CatPred"),
            (L4TurNuPAdapter, "TurNuP"),
            (L4CEKMAdapter, "CEKM"),
        ):
            adapter = cls()
            campaign_id = body.get("campaign_id", "rest_stub")
            domain = Domain(body.get("domain", "hmo"))
            organism = int(body.get("organism", 562))
            gem_id = body.get("gem_id", "iML1515")
            input_payload = body.get("input_payload", {})
            env = adapter.run(
                campaign_id=campaign_id,
                domain=domain,
                organism=organism,
                gem_id=gem_id,
                input_payload=input_payload,
            )
            envs[name] = env.model_dump(mode="json")
        return {
            "ensemble": envs,
            "schema_version": "synbio.kinetics_ensemble.v0.1",
        }

    @app.post("/l4_5/rfdiffusion3/scaffold")
    def l4_5_rfdiffusion3(body: dict[str, Any]) -> dict[str, Any]:
        return _run_adapter_endpoint(L4_5RFdiffusion3Adapter(), body)

    @app.post("/l4_5/mace_off/binding")
    def l4_5_mace_off(body: dict[str, Any]) -> dict[str, Any]:
        return _run_adapter_endpoint(L4_5MACEOFFAdapter(), body)

    @app.post("/l4_5/esmfold/predict")
    def l4_5_esmfold(body: dict[str, Any]) -> dict[str, Any]:
        return _run_adapter_endpoint(L4_5ESMFoldAdapter(), body)

    @app.post("/l6_build/cellfree/stub")
    def l6_build_stub(body: dict[str, Any]) -> dict[str, Any]:
        return _run_adapter_endpoint(L6BuildCellFreeStubAdapter(), body)

    @app.post("/l6_build/cellfree/strateos")
    def l6_build_strateos(body: dict[str, Any]) -> dict[str, Any]:
        return _run_adapter_endpoint(L6BuildStrateosAdapter(), body)

    @app.post("/l6_build/cellfree/emerald")
    def l6_build_emerald(body: dict[str, Any]) -> dict[str, Any]:
        return _run_adapter_endpoint(L6BuildEmeraldAdapter(), body)

    return app


app = create_app()


__all__ = ["app", "create_app"]
