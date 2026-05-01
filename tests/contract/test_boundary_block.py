"""Contract: the boundary block in `boundary.py` matches `BOUNDARY.md`."""

from __future__ import annotations

import hashlib

import pytest

from zer0pa_synbio.boundary import (
    BOUNDARY_BLOCK,
    BOUNDARY_SHA256,
    boundary_sha256,
    verify_against_disk,
)

pytestmark = pytest.mark.contract


def test_boundary_block_in_boundary_md(repo_root):
    boundary_md = (repo_root / "BOUNDARY.md").read_text(encoding="utf-8")
    assert BOUNDARY_BLOCK in boundary_md, (
        "BOUNDARY_BLOCK constant must appear verbatim in BOUNDARY.md"
    )


def test_boundary_block_in_prd(repo_root):
    prd = (repo_root / "PRD.md").read_text(encoding="utf-8")
    assert BOUNDARY_BLOCK in prd, "BOUNDARY_BLOCK constant must appear verbatim in PRD.md"


def test_verify_against_disk(repo_root):
    assert verify_against_disk(repo_root) is True


def test_boundary_sha256_is_stable():
    # Recomputing the hash must match the cached constant.
    assert boundary_sha256() == BOUNDARY_SHA256
    # And it must match a fresh hashlib computation.
    assert BOUNDARY_SHA256 == hashlib.sha256(BOUNDARY_BLOCK.encode("utf-8")).hexdigest()


def test_boundary_block_contains_all_prohibitions():
    """Every operator-imposed prohibition must be in the boundary block."""
    required_phrases = [
        "Research infrastructure",
        "predicted pathways",
        "predicted KPIs",
        "candidate genetic modification specifications",
        "No regulatory certification claims",
        "No clinical or human-subject use",
        "No environmental release of GMOs",
        "No biocontainment-level claims",
        "BSL-2/3 work",
        "No human gene drive",
        "Defence / weapons / dual-use bio",
    ]
    for phrase in required_phrases:
        assert phrase in BOUNDARY_BLOCK, f"Missing required phrase: {phrase!r}"
