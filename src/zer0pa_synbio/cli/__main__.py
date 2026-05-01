"""synbio CLI — minimal entrypoint per PRD §7.

    synbio --help
    synbio status              # show wave status from EXECUTION-STATE.md
    synbio falsifiers list     # enumerate the 23 falsifiers
    synbio falsifiers run <id> # run a falsifier against a JSON evidence file
    synbio hmo run <seed>      # run the L1-L7 chain on a single HMO seed
    synbio audit verify <campaign>   # verify a campaign's audit chain (stub)
    synbio cekm train --config <yaml> [--resume]   # train CEKM (Wave 4)
    synbio cekm smoke                               # CPU data-pipeline smoke test
    synbio cekm eval --config <yaml> --checkpoint <meta.json>  # calibration audit
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
@click.option("--json", "as_json", is_flag=True, help="Emit JSON instead of human-readable summary.")
def audit_verify(campaign_id: str, as_json: bool) -> None:
    """Conformance verifier per docs/synbio-audit-trail-v0.1-spec.md § 10."""
    from zer0pa_synbio.audit.verify import verify_campaign

    report = verify_campaign(REPO_ROOT, campaign_id)
    if as_json:
        click.echo(json.dumps(report.to_dict(), indent=2, sort_keys=True))
    else:
        click.echo(report.summary())
    sys.exit(0 if report.passed else 1)


@cli.group()
def cekm() -> None:
    """CEKM (Conditional Enzyme Kinetics Model) commands — PRD §12."""


# Attach the sub-commands from zer0pa_synbio.cekm.train.  This indirection
# keeps the train module importable standalone (the cekm_group click.Group
# object) while also registering it under the top-level `synbio cekm` group
# here in the canonical CLI entrypoint.
def _register_cekm_subcommands() -> None:
    from zer0pa_synbio.cekm.train import cekm_group

    for cmd_name, cmd_obj in cekm_group.commands.items():
        cekm.add_command(cmd_obj, name=cmd_name)


_register_cekm_subcommands()


def main() -> None:  # pragma: no cover
    cli()


if __name__ == "__main__":  # pragma: no cover
    main()
