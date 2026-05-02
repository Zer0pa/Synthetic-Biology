"""Runpod-side inference modules invoked by the autonomous chain.

Each module here is GPU-bound and called by phase scripts under
``scripts/runpod/phases/``. They produce real research artifacts
(PDBs, energies, designs) under ``audit/runtime/l45_real_inference/``.

Modules:
    mace_off_binding     — 3-run reference-state binding ΔG via MACE-OFF
    rfdiffusion2_design  — backbone diffusion + ProteinMPNN sequence design
"""
