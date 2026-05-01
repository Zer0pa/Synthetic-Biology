"""Boundary block for the Zer0pa Synthetic Biology pipeline.

Single source of truth for the boundary paragraph that every artifact must
carry verbatim. Derived from `BOUNDARY.md`. The hash exposed here is the gate
used by `BoundaryGate` in `envelope.py`.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

# The boundary block is duplicated here for performance (no disk read on every
# import) and verified against `BOUNDARY.md` by `verify_against_disk()` and by
# `tests/contract/test_boundary_block.py`.
BOUNDARY_BLOCK: str = (
    "Research infrastructure for in silico synthetic biology / metabolic "
    "pathway engineering. Outputs are research artifacts — predicted "
    "pathways, predicted KPIs, candidate genetic modification "
    "specifications. No regulatory certification claims. No clinical or "
    "human-subject use. No environmental release of GMOs. No "
    "biocontainment-level claims (the pipeline does not commission BSL-2/3 "
    "work). No human gene drive or eugenic application. Defence / weapons "
    "/ dual-use bio applications excluded under operator policy."
)


def boundary_sha256() -> str:
    """sha256 of the canonical UTF-8-encoded boundary block."""
    return hashlib.sha256(BOUNDARY_BLOCK.encode("utf-8")).hexdigest()


BOUNDARY_SHA256: str = boundary_sha256()
"""Hash gate value. Envelopes whose `boundary` field doesn't hash to this value fail closed."""


def verify_against_disk(repo_root: Path | None = None) -> bool:
    """Verify the in-memory boundary block matches `BOUNDARY.md` on disk.

    Returns True if `BOUNDARY.md` contains `BOUNDARY_BLOCK` exactly. Tests
    use this to detect drift between the markdown source-of-truth and the
    Python constant.
    """
    if repo_root is None:
        # Walk up from this file to find the repo root (the first dir
        # containing BOUNDARY.md).
        current = Path(__file__).resolve().parent
        while current != current.parent:
            if (current / "BOUNDARY.md").exists():
                repo_root = current
                break
            current = current.parent
        else:
            return False
    boundary_md = repo_root / "BOUNDARY.md"
    if not boundary_md.exists():
        return False
    text = boundary_md.read_text(encoding="utf-8")
    return BOUNDARY_BLOCK in text


__all__ = ["BOUNDARY_BLOCK", "BOUNDARY_SHA256", "boundary_sha256", "verify_against_disk"]
