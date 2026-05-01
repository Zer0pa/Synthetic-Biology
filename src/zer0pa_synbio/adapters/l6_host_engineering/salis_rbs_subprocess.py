"""Salis Lab RBS Calculator v1.0 — subprocess-isolated GPL wrapper.

Per PRD §22 + audit/license_grants/salis_v1.yaml +
audit/source_manifests/salis_rbs_v1_0_GPL_subprocess.yaml.

**License-isolation discipline (binding):**
This module MUST NOT ``import`` any GPL-licensed Python code from the
Salis RBS Calculator project. The Salis v1.0 codebase is GPL-3.0; the
synbio package is permissive (Apache 2.0). To prevent GPL infection
of the synbio codebase, the only permitted interaction is launching
the Salis binary as a separate OS process via ``subprocess.run`` and
parsing its stdout. The binary's source code is never linked, never
imported, and never executed in-process.

**Binary discovery:**
The wrapper looks for the Salis binary at, in order:

1. The ``SALIS_RBS_BIN`` environment variable (preferred for pod
   deployments).
2. A configured path passed to ``predict_initiation_rate(..., binary_path=...)``.
3. ``/usr/local/bin/salis_rbs`` (default install).

If no binary is found, ``predict_initiation_rate`` returns ``None``
and the caller falls back to OSTIR (the permissive alternative). This
is by design: the wrapper does not implement any GPL logic in Python.

**Expected binary contract:**
The Salis binary is invoked as:

    salis_rbs --rbs <RBS_SEQ> --cds <CDS_START_SEQ>

and is expected to write a single line of stdout::

    INITIATION_RATE_AU=<float> CONFIDENCE=<float>

The wrapper parses this line. Implementations of the binary that emit
a different format require a custom ``--output-format json`` flag,
not supported here in v0.1. Real Salis v1.0 ships as a Python 2
package; the operator wraps it with a small CLI shim that emits the
above format, e.g. ``audit/runtime/salis_v1/cli_shim.sh``.

**Source:** https://github.com/salislab/RBS_Calculator_v1
**Citation:** Salis, H. M. et al. Automated design of synthetic
ribosome binding sites to control protein expression. Nat. Biotechnol.
(2009).
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
from pathlib import Path
from typing import NamedTuple


class SalisRBSResult(NamedTuple):
    """Result of a Salis RBS subprocess invocation."""

    initiation_rate_au: float
    confidence: float
    binary_path: str
    stdout_line: str


def _locate_binary(binary_path: str | None = None) -> str | None:
    """Return the resolved Salis binary path, or None if not found.

    Resolution order: explicit binary_path → SALIS_RBS_BIN env →
    PATH lookup for ``salis_rbs`` → /usr/local/bin/salis_rbs default.
    """
    if binary_path:
        if Path(binary_path).is_file() and os.access(binary_path, os.X_OK):
            return binary_path
        return None
    env_path = os.environ.get("SALIS_RBS_BIN")
    if env_path and Path(env_path).is_file() and os.access(env_path, os.X_OK):
        return env_path
    which = shutil.which("salis_rbs")
    if which:
        return which
    default = "/usr/local/bin/salis_rbs"
    if Path(default).is_file() and os.access(default, os.X_OK):
        return default
    return None


_LINE_RE = re.compile(
    r"INITIATION_RATE_AU\s*=\s*([\-+]?[0-9]*\.?[0-9]+(?:[eE][-+]?\d+)?)"
    r"\s+CONFIDENCE\s*=\s*([\-+]?[0-9]*\.?[0-9]+(?:[eE][-+]?\d+)?)"
)


def predict_initiation_rate(
    rbs_sequence: str,
    cds_start_sequence: str,
    *,
    binary_path: str | None = None,
    timeout_s: int = 30,
) -> SalisRBSResult | None:
    """Invoke the Salis v1.0 binary via subprocess and parse the result.

    Returns a ``SalisRBSResult`` on success; ``None`` if the binary
    cannot be located, fails to execute, exits non-zero, or emits
    output that does not match the expected ``INITIATION_RATE_AU=…
    CONFIDENCE=…`` format. The caller is expected to fall back to
    OSTIR (or another permissive RBS predictor) on a None return.

    The subprocess is launched with ``shell=False``, an explicit
    ``timeout``, and ``check=False`` so the wrapper handles all
    failure modes itself rather than raising.
    """
    binary = _locate_binary(binary_path)
    if binary is None:
        return None
    cmd = [binary, "--rbs", rbs_sequence, "--cds", cds_start_sequence]
    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout_s,
            check=False,
            shell=False,
        )
    except (subprocess.TimeoutExpired, OSError):
        return None
    if proc.returncode != 0:
        return None
    out = proc.stdout.strip()
    # Find the first line that matches the contract (allows the binary
    # to emit log lines / banner before the result).
    for line in out.splitlines():
        m = _LINE_RE.search(line)
        if m:
            try:
                rate = float(m.group(1))
                confidence = float(m.group(2))
            except ValueError:
                return None
            return SalisRBSResult(
                initiation_rate_au=rate,
                confidence=confidence,
                binary_path=binary,
                stdout_line=line,
            )
    return None


__all__ = ["SalisRBSResult", "predict_initiation_rate"]
