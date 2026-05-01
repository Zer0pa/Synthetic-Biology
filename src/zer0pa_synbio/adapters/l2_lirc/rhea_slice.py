"""Build a real (small) LIRC slice for the canonical HMO biosynthesis
pathways via Rhea API.

Rhea is CC0 (Class A); see audit/source_manifests/rhea.yaml.

The slice replaces the canned 2'-FL ReactionGraph in `L2LIRCAdapter`'s
default output. For the full 70-80% LIRC corpus build, see
NEXT-WAVE-PLAN.md §B.1.

This module is invoked at L2 build time via:

    from zer0pa_synbio.adapters.l2_lirc.rhea_slice import (
        build_2pfl_slice,
    )

It writes `fixtures/lirc/2pfl_canonical.json` once. The L2 adapter then
loads from disk if present; the canned shape stays as a fallback.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any


# Rhea reaction IDs for the canonical 2'-FL + 3'-SL biosynthesis pathways
# (E. coli, MetaCyc-mapped). Source: published HMO-engineering literature
# (Drouillard 2006, Lee 2012, Yu 2016, Jang 2024). EC and UniProt
# cross-references are normative; the Rhea record itself can be fetched
# via SPARQL (https://sparql.rhea-db.org) with the query in
# `docs/decisions/lirc-rhea-slice.md` once it's authored.
RHEA_2PFL_REACTIONS = {
    "RHEA:23900": {
        "label": "Gmd: GDP-mannose -> GDP-4-keto-6-deoxy-D-mannose + H2O",
        "ec": "4.2.1.47",
        "enzyme_uniprot": "P0AC88",  # E. coli K-12 Gmd
        "substrate_inchi_keys": ["WUUGFSXJNOTRMR-IOSLPCCCSA-N"],  # GDP-mannose
        "product_inchi_keys": [
            "RWHOZGRAXYWHAT-UHFFFAOYSA-N"  # GDP-4-keto-6-deoxy-D-mannose (placeholder)
        ],
    },
    "RHEA:18225": {
        "label": "WcaG: GDP-4-keto-6-deoxy-D-mannose + NADPH -> GDP-L-fucose + NADP+",
        "ec": "1.1.1.271",
        "enzyme_uniprot": "P32055",  # E. coli K-12 WcaG (also called Fcl)
    },
    "RHEA:14457": {
        "label": "FutC: GDP-L-fucose + lactose -> 2'-fucosyllactose + GDP",
        "ec": "2.4.1.69",
        "enzyme_uniprot": "Q11075",  # H. pylori FutC; the canonical heterologous enzyme used in E. coli 2'-FL strains
        "substrate_inchi_keys": [
            "WUUGFSXJNOTRMR-IOSLPCCCSA-N",  # GDP-fucose
            "GUBGYTABKSRVRQ-PICCSMPSSA-N",  # lactose
        ],
        "product_inchi_keys": [
            "GFXBRIYRYYFCIA-LWNAIEPUSA-N",  # 2'-FL
            "RQFCJASXJCIDSX-UUOKFMHZSA-N",  # GDP
        ],
    },
    "RHEA:13089": {
        "label": "NeuA: CTP + N-acetylneuraminate -> CMP-Neu5Ac + diphosphate",
        "ec": "2.7.7.43",
        "enzyme_uniprot": "P0A6S0",  # E. coli K-12 NeuA
    },
    "RHEA:14217": {
        "label": "Lst: CMP-Neu5Ac + lactose -> 3'-sialyllactose + CMP",
        "ec": "2.4.99.6",
        "enzyme_uniprot": "Q56930",  # N. meningitidis Lst (heterologous in E. coli)
    },
}


RHEA_API_BASE = "https://www.rhea-db.org/rhea"


def _fetch_rhea_record(rhea_id: str, timeout: float = 30.0) -> dict[str, Any]:
    """Fetch a Rhea reaction record as JSON via the public API."""
    # Rhea provides JSON via /rhea/{id}.json
    url = f"{RHEA_API_BASE}/{rhea_id.replace('RHEA:', '')}.json"
    req = urllib.request.Request(url, headers={"User-Agent": "zer0pa-synbio-bootstrap/0.1"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode("utf-8"))
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as exc:
        return {"rhea_id": rhea_id, "error": str(exc), "fetch_failed": True}
    except Exception as exc:
        return {"rhea_id": rhea_id, "error": str(exc), "fetch_failed": True}


def build_2pfl_slice(output_path: Path | None = None) -> dict[str, Any]:
    """Build the canonical 2'-FL + 3'-SL pathway slice.

    Returns the slice as a dict; if `output_path` is given, also writes
    JSON to disk.
    """
    repo_root = Path(__file__).resolve().parents[4]
    if output_path is None:
        output_path = repo_root / "fixtures" / "lirc" / "2pfl_canonical.json"

    reactions: list[dict[str, Any]] = []
    fetch_errors: list[dict[str, str]] = []
    for rid, meta in RHEA_2PFL_REACTIONS.items():
        rec = _fetch_rhea_record(rid)
        if rec.get("fetch_failed"):
            fetch_errors.append({"rhea_id": rid, "error": rec["error"]})
            rec = {
                "rhea_id": rid,
                "fetch_failed": True,
                "fallback": True,
                **meta,
            }
        else:
            rec["rhea_id"] = rid
            for k, v in meta.items():
                rec.setdefault(k, v)
        reactions.append(rec)

    slice_data = {
        "schema_version": "synbio.lirc_slice.v0.1",
        "slice_name": "hmo_2pfl_3psl_canonical",
        "source_manifests": [
            "audit/source_manifests/rhea.yaml",
            "audit/source_manifests/metanetx.yaml",
        ],
        "license_class": "A",
        "reactions": reactions,
        "fetch_errors": fetch_errors,
        "boundary": (
            "Research infrastructure for in silico synthetic biology / "
            "metabolic pathway engineering. Outputs are research artifacts. "
            "No regulatory certification claims. No clinical or human-subject "
            "use. No environmental release of GMOs."
        ),
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(slice_data, indent=2, sort_keys=True), encoding="utf-8")
    return slice_data


__all__ = ["RHEA_2PFL_REACTIONS", "build_2pfl_slice"]
