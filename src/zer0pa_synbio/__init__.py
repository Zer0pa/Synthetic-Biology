"""Zer0pa Synthetic Biology Pipeline 4.

Research infrastructure for in silico synthetic biology / metabolic pathway
engineering. Outputs are research artifacts. See `BOUNDARY.md` for the binding
boundary block.
"""

from zer0pa_synbio import boundary
from zer0pa_synbio.envelope import UniversalLayerEnvelope, BoundaryGateError, Layer, ExecutionMode, LicenseClass

__all__ = [
    "boundary",
    "UniversalLayerEnvelope",
    "BoundaryGateError",
    "Layer",
    "ExecutionMode",
    "LicenseClass",
]

__version__ = "0.1.0"
