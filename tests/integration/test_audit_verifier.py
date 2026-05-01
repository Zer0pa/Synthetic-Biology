"""Audit verifier (Audit-Trail Spec v0.1 §10) integration tests."""

from __future__ import annotations

from pathlib import Path

import pytest

from zer0pa_synbio.audit.verify import verify_campaign


pytestmark = pytest.mark.integration


REPO_ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.parametrize("seed", ["2pFL", "3pSL", "DSLNT"])
def test_hmo_seed_audit_conformance(seed):
    """Each HMO seed packet must pass all conformance checks once
    `validation/hmo-seed-evidence/run_seed.py --seed <X>` has been run."""
    campaign = f"hmo_seed_{seed}"
    runtime = REPO_ROOT / "audit" / "runtime" / campaign
    if not runtime.exists():
        pytest.skip(f"Campaign {campaign} not yet run; run validation/hmo-seed-evidence/run_seed.py --seed {seed}")
    report = verify_campaign(REPO_ROOT, campaign)
    assert report.passed, "\n" + report.summary()


def test_verify_unknown_campaign_fails():
    report = verify_campaign(REPO_ROOT, "no_such_campaign_2026")
    assert report.passed is False
    assert any(c.name == "runtime_dir_present" and not c.passed for c in report.checks)
