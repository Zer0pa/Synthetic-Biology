"""synbio CLI — minimal entrypoint per PRD §7.

    synbio --help
    synbio status              # show wave status from EXECUTION-STATE.md
    synbio falsifiers list     # enumerate the 23 falsifiers
    synbio falsifiers run <id> # run a falsifier against a JSON evidence file
    synbio hmo run <seed>      # run the L1-L7 chain on a single HMO seed
    synbio audit verify <campaign>   # verify a campaign's audit chain (stub)
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import click


REPO_ROOT = Path(__file__).resolve().parents[3]


@click.group()
def cli() -> None:
    """Zer0pa Synthetic Biology Pipeline CLI."""


@cli.command()
def status() -> None:
    """Print EXECUTION-STATE.md head."""
    f = REPO_ROOT / "EXECUTION-STATE.md"
    if not f.exists():
        click.echo("EXECUTION-STATE.md not found", err=True)
        sys.exit(1)
    text = f.read_text(encoding="utf-8")
    click.echo(text[:4000])


@cli.group()
def falsifiers() -> None:
    """Falsifier registry commands."""


@falsifiers.command("list")
def list_falsifiers() -> None:
    from zer0pa_synbio.falsifiers import REGISTRY

    for fid, spec in REGISTRY.items():
        click.echo(f"{fid}\t{spec.tier}\t{spec.severity}\t{spec.gate_action}")


@falsifiers.command("run")
@click.argument("falsifier_id")
@click.argument("evidence_file", type=click.Path(exists=True, dir_okay=False, path_type=Path))
def run_falsifier(falsifier_id: str, evidence_file: Path) -> None:
    from zer0pa_synbio.falsifiers.checks import run

    evidence = json.loads(evidence_file.read_text(encoding="utf-8"))
    result = run(falsifier_id, evidence)
    click.echo(result.model_dump_json(indent=2))
    sys.exit(1 if result.triggered and result.severity == "fail" else 0)


@cli.group()
def hmo() -> None:
    """HMO scientific validation triple commands."""


@hmo.command("run")
@click.argument("seed", type=click.Choice(["2pFL", "3pSL", "DSLNT"]))
def hmo_run(seed: str) -> None:
    """Run the L1-L7 chain on one HMO seed (stub mode; emits envelope chain)."""
    click.echo(f"Running HMO seed: {seed}")
    click.echo(
        "Full pipeline run lives in `validation/hmo-seed-evidence/<seed>/run.py`. "
        "This CLI subcommand will dispatch the run and write outputs to "
        "audit/runtime/hmo_seed_<seed>/ once Wave 9 evidence packets are wired."
    )


@cli.group()
def audit() -> None:
    """Audit-trail commands per docs/synbio-audit-trail-v0.1-spec.md §10."""


@audit.command("verify")
@click.argument("campaign_id")
def audit_verify(campaign_id: str) -> None:
    """Stub of the conformance verifier."""
    runtime = REPO_ROOT / "audit" / "runtime" / campaign_id
    if not runtime.exists():
        click.echo(f"No audit runtime at {runtime}", err=True)
        sys.exit(1)
    envelopes_jsonl = runtime / "envelopes.jsonl"
    if not envelopes_jsonl.exists():
        click.echo(f"No envelopes at {envelopes_jsonl}", err=True)
        sys.exit(1)
    n = sum(1 for _ in envelopes_jsonl.read_text(encoding="utf-8").splitlines())
    click.echo(f"Campaign {campaign_id}: {n} envelopes recorded.")


def main() -> None:  # pragma: no cover
    cli()


if __name__ == "__main__":  # pragma: no cover
    main()
