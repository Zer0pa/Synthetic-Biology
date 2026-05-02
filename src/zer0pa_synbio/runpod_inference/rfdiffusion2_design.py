"""RFdiffusion2 backbone-design wrapper for the L4.5 unknown-enzyme path.

Invokes the upstream ``RosettaCommons/RFdiffusion2`` inference script
on a small set of unconditional + motif-conditional designs for the
DSLNT seed (Tier-2 enzyme novelty per PRD §6.6.2). RFdiffusion2 is
BSD-3-Clause, weights publicly downloadable from files.ipd.uw.edu.

For the v0.1 autonomous run we generate **unconditional designs**
(scaffold a 100-residue protein) per seed — this validates that real
RFdiffusion2 inference ran on the H100 even without a curated
catalytic-motif specification. Motif-conditional designs require a
curated active-site geometry which is downstream of v0.1.

Outputs:
    designs/<seed>/design_<i>.pdb    — diffused backbone
    rfdiffusion2_<seed>.json         — manifest of designs + metadata

Honest scope:
    Unconditional designs are NOT enzyme designs — they're protein
    backbones the diffusion model considers physically plausible.
    They serve as proof-of-life that the GPU can run real
    RFdiffusion2 inference and produce structurally valid PDBs.
    Real catalytic-motif scaffolding for α-2,6-sialyltransferase
    (DSLNT seed) requires curated TS-mimetic geometry, downstream.
"""

from __future__ import annotations

import json
import logging
import os
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)

BOUNDARY = (
    "Research infrastructure for in silico synthetic biology / "
    "metabolic pathway engineering. Outputs are research artifacts. "
    "No regulatory certification claims. No clinical or human-subject "
    "use. No environmental release of GMOs."
)


@dataclass
class RFD2DesignManifest:
    seed: str
    n_designs_requested: int
    n_designs_produced: int
    design_paths: list[str]
    contig_spec: str
    repo_path: str
    weights_path: str
    weights_sha256: str | None
    wallclock_seconds: float
    error: str | None
    boundary: str

    def to_dict(self) -> dict:
        return {
            "boundary": self.boundary,
            "seed": self.seed,
            "n_designs_requested": self.n_designs_requested,
            "n_designs_produced": self.n_designs_produced,
            "design_paths": self.design_paths,
            "contig_spec": self.contig_spec,
            "repo_path": self.repo_path,
            "weights_path": self.weights_path,
            "weights_sha256": self.weights_sha256,
            "wallclock_seconds": self.wallclock_seconds,
            "error": self.error,
            "tool": "rfdiffusion2",
        }


def _sha256(path: Path) -> str:
    import hashlib

    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def run_rfdiffusion2(
    seed_label: str,
    out_dir: Path,
    *,
    rf_root: Path = Path("/workspace/models/rfdiffusion2"),
    n_designs: int = 3,
    contig_spec: str = "100",
    timeout_s: int = 1800,
) -> RFD2DesignManifest:
    """Generate `n_designs` unconditional 100-residue scaffolds for the
    given seed label. Uses upstream
    ``scripts/run_inference.py contigmap.contigs=<contig_spec>``."""
    t0 = time.time()
    out_dir.mkdir(parents=True, exist_ok=True)
    designs_dir = out_dir / "designs" / seed_label
    designs_dir.mkdir(parents=True, exist_ok=True)

    repo = rf_root / "repo"
    weights = rf_root / "RF_structure_prediction_weights.pt"

    if not repo.exists():
        return RFD2DesignManifest(
            seed=seed_label,
            n_designs_requested=n_designs,
            n_designs_produced=0,
            design_paths=[],
            contig_spec=contig_spec,
            repo_path=str(repo),
            weights_path=str(weights),
            weights_sha256=None,
            wallclock_seconds=time.time() - t0,
            error=f"RFdiffusion2 repo missing at {repo}; run phase 60 prelude to clone+download.",
            boundary=BOUNDARY,
        )
    if not weights.exists():
        return RFD2DesignManifest(
            seed=seed_label,
            n_designs_requested=n_designs,
            n_designs_produced=0,
            design_paths=[],
            contig_spec=contig_spec,
            repo_path=str(repo),
            weights_path=str(weights),
            weights_sha256=None,
            wallclock_seconds=time.time() - t0,
            error=f"RFdiffusion2 weights missing at {weights}",
            boundary=BOUNDARY,
        )
    weights_sha = _sha256(weights)

    # Discover the inference entrypoint. Upstream lays it out as
    # rfdiffusion/run_inference.py (top-level package script).
    entry = None
    for cand in (
        repo / "scripts" / "run_inference.py",
        repo / "rfdiffusion" / "run_inference.py",
        repo / "run_inference.py",
    ):
        if cand.exists():
            entry = cand
            break
    if entry is None:
        return RFD2DesignManifest(
            seed=seed_label,
            n_designs_requested=n_designs,
            n_designs_produced=0,
            design_paths=[],
            contig_spec=contig_spec,
            repo_path=str(repo),
            weights_path=str(weights),
            weights_sha256=weights_sha,
            wallclock_seconds=time.time() - t0,
            error=f"run_inference.py not found in {repo}",
            boundary=BOUNDARY,
        )

    output_prefix = designs_dir / f"design"
    cmd = [
        "python",
        str(entry),
        f"contigmap.contigs=[{contig_spec}]",
        f"inference.output_prefix={output_prefix}",
        f"inference.num_designs={n_designs}",
        f"inference.ckpt_override_path={weights}",
    ]
    logger.info("Running RFdiffusion2: %s", " ".join(cmd))
    log_path = out_dir / f"rfdiffusion2_{seed_label}.log"
    error: str | None = None
    try:
        with open(log_path, "w") as logf:
            proc = subprocess.run(
                cmd,
                stdout=logf,
                stderr=subprocess.STDOUT,
                cwd=str(repo),
                timeout=timeout_s,
                env={**os.environ, "PYTHONPATH": str(repo)},
                check=False,
            )
        if proc.returncode != 0:
            error = f"rfdiffusion2 exit={proc.returncode}; see {log_path}"
    except subprocess.TimeoutExpired:
        error = f"rfdiffusion2 timed out after {timeout_s}s"
    except Exception as exc:
        error = f"rfdiffusion2 launch failed: {exc}"

    # Collect produced PDBs.
    produced = sorted(designs_dir.glob("*.pdb"))

    manifest = RFD2DesignManifest(
        seed=seed_label,
        n_designs_requested=n_designs,
        n_designs_produced=len(produced),
        design_paths=[str(p) for p in produced],
        contig_spec=contig_spec,
        repo_path=str(repo),
        weights_path=str(weights),
        weights_sha256=weights_sha,
        wallclock_seconds=time.time() - t0,
        error=error,
        boundary=BOUNDARY,
    )
    out_path = out_dir / f"rfdiffusion2_{seed_label}.json"
    out_path.write_text(json.dumps(manifest.to_dict(), indent=2, sort_keys=True))
    logger.info("Wrote %s (n_produced=%d)", out_path, len(produced))
    return manifest


def main() -> int:
    """CLI: ``python -m zer0pa_synbio.runpod_inference.rfdiffusion2_design
    <seed_label> <out_dir> [n_designs] [contig_spec]``."""
    import sys

    logging.basicConfig(
        level=logging.INFO, format="%(levelname)s %(name)s: %(message)s"
    )
    if len(sys.argv) < 3:
        print("usage: rfdiffusion2_design <seed_label> <out_dir> [n_designs] [contig_spec]")
        return 2
    seed = sys.argv[1]
    out = Path(sys.argv[2])
    n = int(sys.argv[3]) if len(sys.argv) > 3 else 3
    contig = sys.argv[4] if len(sys.argv) > 4 else "100"
    m = run_rfdiffusion2(seed, out, n_designs=n, contig_spec=contig)
    print(json.dumps(m.to_dict(), indent=2))
    return 0 if m.error is None else 1


if __name__ == "__main__":
    raise SystemExit(main())
