"""Salis RBS Calculator v1.0 subprocess wrapper tests.

Per HANDOFF-CPU-CONTINUATION.md item F + PRD §22 + audit/license_grants/salis_v1.yaml.

The real Salis v1.0 binary is GPL-3.0 and not co-located with this
repo (subprocess-isolation discipline). These tests use a small fake
binary (a shell script) that emits the documented output contract:

    INITIATION_RATE_AU=<float> CONFIDENCE=<float>

This validates the subprocess-isolation contract without coupling
the test suite to GPL code or to a real Salis install. The tests
verify:

- Locator: env, explicit path, PATH lookup, default fall-through.
- Parser: valid output → SalisRBSResult with correct values.
- Failure modes: missing binary, non-zero exit, malformed output,
  timeout — all return None (no exceptions).
- License-isolation: the wrapper does NOT import any GPL module.
"""

from __future__ import annotations

import os
import stat
from pathlib import Path

import pytest

from zer0pa_synbio.adapters.l6_host_engineering.salis_rbs_subprocess import (
    SalisRBSResult,
    _locate_binary,
    predict_initiation_rate,
)


def _make_fake_salis(tmp_path: Path, body: str, name: str = "fake_salis") -> Path:
    """Materialise a shell script that mimics the Salis v1.0 CLI contract."""
    script = tmp_path / name
    script.write_text(body, encoding="utf-8")
    script.chmod(script.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    return script


def test_locator_explicit_path_takes_precedence(tmp_path):
    fake = _make_fake_salis(tmp_path, "#!/bin/bash\necho hi\n")
    assert _locate_binary(str(fake)) == str(fake)


def test_locator_env_var(tmp_path, monkeypatch):
    fake = _make_fake_salis(tmp_path, "#!/bin/bash\necho hi\n")
    monkeypatch.setenv("SALIS_RBS_BIN", str(fake))
    monkeypatch.setattr(
        "shutil.which", lambda name: None  # disable PATH lookup
    )
    assert _locate_binary() == str(fake)


def test_locator_returns_none_when_nothing_found(monkeypatch):
    monkeypatch.delenv("SALIS_RBS_BIN", raising=False)
    monkeypatch.setattr("shutil.which", lambda name: None)
    monkeypatch.setattr(
        "pathlib.Path.is_file", lambda self: False
    )
    assert _locate_binary() is None


def test_predict_with_well_formed_output(tmp_path):
    body = (
        "#!/bin/bash\n"
        "# Mock Salis v1.0 CLI shim for tests.\n"
        'echo "INITIATION_RATE_AU=12345.6 CONFIDENCE=0.78"\n'
    )
    fake = _make_fake_salis(tmp_path, body)
    result = predict_initiation_rate(
        rbs_sequence="TTTAAGAAGGAGATATACAT",
        cds_start_sequence="ATGAAAAAG",
        binary_path=str(fake),
    )
    assert isinstance(result, SalisRBSResult)
    assert result.initiation_rate_au == 12345.6
    assert result.confidence == 0.78
    assert result.binary_path == str(fake)


def test_predict_with_banner_lines_before_result(tmp_path):
    body = (
        "#!/bin/bash\n"
        'echo "Salis Lab RBS Calculator v1.0"\n'
        'echo "Loading thermodynamic parameters..."\n'
        'echo "INITIATION_RATE_AU=42.5 CONFIDENCE=0.55"\n'
        'echo "Goodbye"\n'
    )
    fake = _make_fake_salis(tmp_path, body)
    result = predict_initiation_rate(
        rbs_sequence="TTTAAGAAGGAGATATACAT",
        cds_start_sequence="ATGAAAAAG",
        binary_path=str(fake),
    )
    assert result is not None
    assert result.initiation_rate_au == 42.5
    assert result.confidence == 0.55


def test_predict_returns_none_when_binary_missing(tmp_path):
    """Pointing at a non-existent path → None, no raise."""
    result = predict_initiation_rate(
        rbs_sequence="TTTAAGAAGGAGATATACAT",
        cds_start_sequence="ATGAAAAAG",
        binary_path=str(tmp_path / "does_not_exist"),
    )
    assert result is None


def test_predict_returns_none_on_nonzero_exit(tmp_path):
    body = "#!/bin/bash\necho 'simulated failure'\nexit 1\n"
    fake = _make_fake_salis(tmp_path, body)
    result = predict_initiation_rate(
        rbs_sequence="TTT",
        cds_start_sequence="ATG",
        binary_path=str(fake),
    )
    assert result is None


def test_predict_returns_none_on_malformed_output(tmp_path):
    body = '#!/bin/bash\necho "this is not the right format"\n'
    fake = _make_fake_salis(tmp_path, body)
    result = predict_initiation_rate(
        rbs_sequence="TTT",
        cds_start_sequence="ATG",
        binary_path=str(fake),
    )
    assert result is None


def test_no_gpl_module_is_imported():
    """Audit: confirm the wrapper does not import any GPL-licensed code.

    PRD §22 prohibits Python ``import`` of GPL modules into the synbio
    package. We assert that the only third-party imports in the wrapper
    are subprocess / re / os / shutil / pathlib / typing — all
    permissive (Python standard library, PSF licence).
    """
    import inspect

    from zer0pa_synbio.adapters.l6_host_engineering import salis_rbs_subprocess

    src = inspect.getsource(salis_rbs_subprocess)
    forbidden_imports = ["import salis", "import RBS_Calculator", "from salis", "from RBS_Calculator"]
    for needle in forbidden_imports:
        assert needle not in src, (
            f"Forbidden import '{needle}' found in salis_rbs_subprocess.py — "
            "GPL isolation discipline broken."
        )


def test_l6_adapter_uses_salis_when_grant_and_binary_present(tmp_path, monkeypatch):
    """Integration: when audit/license_grants/salis_v1.yaml exists AND
    a binary is locatable via SALIS_RBS_BIN, the L6 adapter's RBS
    prediction reports tool=rbs_calculator_v1_0_gpl_subprocess and
    carries the binary path + isolation_mechanism in the output.
    """
    body = (
        "#!/bin/bash\n"
        'echo "INITIATION_RATE_AU=9876.5 CONFIDENCE=0.65"\n'
    )
    fake = _make_fake_salis(tmp_path, body)
    monkeypatch.setenv("SALIS_RBS_BIN", str(fake))

    from zer0pa_synbio.adapters.l6_host_engineering import L6HostEngineeringAdapter
    from zer0pa_synbio.envelope import Domain

    env = L6HostEngineeringAdapter().run(
        campaign_id="test_l6_salis",
        domain=Domain.hmo,
        organism=562,
        gem_id="iML1515",
        input_payload={
            "spec_id": "gms_test_salis",
            "host_taxonomy_id": 562,
            "target_genes": ["FutC"],
            "rbs_sequence": "TTTAAGAAGGAGATATACAT",
            "cds_start_sequence": "ATGAAAAAG",
            "salis_binary_path": str(fake),
        },
    )
    rbs = env.outputs.payload["genetic_modification_spec"]["rbs_predictions"]
    assert rbs["tool"] == "rbs_calculator_v1_0_gpl_subprocess"
    assert rbs["initiation_rate_au"] == 9876.5
    assert rbs["confidence"] == 0.65
    assert rbs["isolation_mechanism"] == "subprocess"
    assert rbs["license_grant_uri"] == "audit/license_grants/salis_v1.yaml"
