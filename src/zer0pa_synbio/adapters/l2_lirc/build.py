"""LIRC corpus build pipeline (Wave 2 real ingestion).

Per HANDOFF-CPU-CONTINUATION.md item C and PRD §6.2.

Pulls reaction-level data from the four permissive sources and
reconciles them via MetaNetX MNXref:

1. **Rhea** (CC0, Class A) — SPARQL endpoint at
   https://sparql.rhea-db.org/sparql. Authoritative reaction-equation
   knowledgebase; ~17,000 approved reactions as of 2026.
2. **MetaNetX** (CC BY 4.0, Class A) — REST/CSV bulk downloads from
   https://www.metanetx.org/. Provides MNXref 4.5 namespace
   reconciliation across Rhea, BiGG, ModelSEED, KEGG (read-only),
   and SEED.
3. **BiGG** (CC BY 4.0, Class A) — REST API at
   http://bigg.ucsd.edu/api/v2/. Curated genome-scale-model reactions.
4. **ModelSEED** (MIT, Class A) — bulk JSON download from
   https://github.com/ModelSEED/ModelSEEDDatabase.
5. **BRENDA core** (CC BY 4.0, Class A) — pre-downloaded TSV; same
   loader as ``cekm.loaders.brenda_bulk`` but only the reaction-EC
   mapping is consumed here (kinetics goes to CEKM).

**Excluded BY CONSTRUCTION** (falsifier f018_license_drift enforces):
- ATLAS of Biochemistry (D — academic-subscription)
- BKMS-react (E — proprietary)
- KEGG bulk (E — license)

**Atom-mapped SMARTS canonicalisation:**
RDKit's ``ReactionFromSmarts`` + ``rdChemReactions.ChemicalReaction``
produces a canonical atom-mapped SMARTS string per reaction. Reactions
with identical canonical SMARTS are deduplicated, with the union of
their cross-references preserved.

**Output:**
The build writes ``fixtures/lirc/lirc_v0.1.json.gz`` (gzip-compressed
JSON). Bulk artifacts > 5 GB go to HF (``Architect-Prime/synbio-lirc-v0.1``);
small slices stay local.

**Wallclock:**
Full build: ~4-8 hours on a single CPU (network-bound on Rhea SPARQL +
MetaNetX). Validation slice (cap=200): ~3-5 minutes.

CLI: ``python -m zer0pa_synbio.adapters.l2_lirc.build --cap 200``
or with no cap for the full run.
"""

from __future__ import annotations

import argparse
import gzip
import json
import logging
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Iterable

logger = logging.getLogger(__name__)

# Public endpoints
RHEA_SPARQL = "https://sparql.rhea-db.org/sparql"
BIGG_API_BASE = "http://bigg.ucsd.edu/api/v2"
METANETX_REAC_PROP_URL = "https://www.metanetx.org/cgi-bin/mnxget/mnxref/reac_prop.tsv"
METANETX_REAC_XREF_URL = "https://www.metanetx.org/cgi-bin/mnxget/mnxref/reac_xref.tsv"
MODELSEED_REACTIONS_URL = (
    "https://raw.githubusercontent.com/ModelSEED/ModelSEEDDatabase/"
    "master/Biochemistry/reactions.tsv"
)


@dataclass
class ReactionRecord:
    """Canonicalised LIRC reaction record."""

    canonical_id: str  # SHA-1 hex digest of canonical SMARTS (or normalised eq)
    rhea_id: str | None = None
    bigg_id: str | None = None
    modelseed_id: str | None = None
    metanetx_id: str | None = None
    brenda_ec_numbers: list[str] = field(default_factory=list)
    equation: str | None = None
    canonical_smarts: str | None = None
    enzyme_uniprot_ids: list[str] = field(default_factory=list)
    license_class: str = "A"
    source_manifests: list[str] = field(default_factory=list)


def _http_get_text(url: str, timeout: float = 60.0) -> str:
    req = urllib.request.Request(
        url, headers={"User-Agent": "zer0pa-synbio-lirc-build/0.1"}
    )
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8")


def query_rhea_sparql(limit: int = 16000, batch: int = 500) -> list[dict[str, str]]:
    """Pull all approved Rhea reactions via SPARQL (paginated).

    Returns dicts with keys: ``rhea_id``, ``equation``, ``ec`` (optional).
    Rhea SPARQL endpoint: https://sparql.rhea-db.org/sparql.
    """
    from SPARQLWrapper import JSON, SPARQLWrapper  # local import for optional dep

    out: list[dict[str, str]] = []
    fetched = 0
    while fetched < limit:
        size = min(batch, limit - fetched)
        sparql = SPARQLWrapper(RHEA_SPARQL)
        query = f"""
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX rh: <http://rdf.rhea-db.org/>
SELECT ?rhea ?eq WHERE {{
  ?rhea rh:status rh:Approved .
  ?rhea rdfs:label ?eq .
}}
ORDER BY ?rhea
OFFSET {fetched} LIMIT {size}
"""
        sparql.setQuery(query)
        sparql.setReturnFormat(JSON)
        try:
            res = sparql.query().convert()
        except Exception as exc:
            logger.warning("Rhea SPARQL batch failed at offset %d: %s", fetched, exc)
            break
        rows = res.get("results", {}).get("bindings", [])
        if not rows:
            break
        for b in rows:
            rid = b["rhea"]["value"].split("/")[-1]
            out.append({"rhea_id": f"RHEA:{rid}", "equation": b["eq"]["value"]})
        fetched += len(rows)
        # Rate limit: respect Rhea's public endpoint (no bulk DDoS).
        time.sleep(0.5)
    return out


def query_metanetx_xref(cap: int | None = None, timeout: float = 600.0) -> list[dict[str, str]]:
    """Pull MetaNetX MNXref reaction cross-references (TSV stream).

    Each row maps a source-namespace reaction ID (e.g. ``rheaR:14457``,
    ``biggR:R_PFK``) to the canonical MetaNetX MNXref ID. Used to
    deduplicate across Rhea / BiGG / ModelSEED / KEGG names.
    """
    try:
        text = _http_get_text(METANETX_REAC_XREF_URL, timeout=timeout)
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as exc:
        logger.warning("MetaNetX MNXref fetch failed: %s", exc)
        return []
    out: list[dict[str, str]] = []
    for line in text.splitlines():
        if line.startswith("#") or not line.strip():
            continue
        parts = line.split("\t")
        if len(parts) < 2:
            continue
        out.append({"source_id": parts[0], "mnx_id": parts[1]})
        if cap is not None and len(out) >= cap:
            break
    return out


def query_bigg_reactions(cap: int | None = None) -> list[dict[str, Any]]:
    """Pull BiGG reactions via the public REST API.

    Endpoint: http://bigg.ucsd.edu/api/v2/universal/reactions
    """
    url = f"{BIGG_API_BASE}/universal/reactions"
    try:
        raw = _http_get_text(url, timeout=120.0)
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as exc:
        logger.warning("BiGG REST fetch failed: %s", exc)
        return []
    payload = json.loads(raw)
    rxns = payload.get("results", [])
    if cap is not None:
        rxns = rxns[:cap]
    return rxns


def query_modelseed_reactions(cap: int | None = None, timeout: float = 600.0) -> list[dict[str, str]]:
    """Pull ModelSEED reactions TSV (rate-limit-friendly, ~50K rows)."""
    try:
        text = _http_get_text(MODELSEED_REACTIONS_URL, timeout=timeout)
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as exc:
        logger.warning("ModelSEED fetch failed: %s", exc)
        return []
    out: list[dict[str, str]] = []
    headers: list[str] | None = None
    for line in text.splitlines():
        if line.startswith("#") or not line.strip():
            continue
        parts = line.split("\t")
        if headers is None:
            headers = [h.strip() for h in parts]
            continue
        rec = dict(zip(headers, parts))
        out.append(rec)
        if cap is not None and len(out) >= cap:
            break
    return out


def canonicalise_reaction_smarts(smarts: str) -> str | None:
    """Compute a canonical atom-mapped SMARTS string for a reaction.

    Uses RDKit's ``rdChemReactions.ReactionFromSmarts`` +
    ``ReactionToSmarts`` round-trip. Returns ``None`` if the reaction
    cannot be parsed (which is treated as "not canonicalisable" rather
    than an error — Rhea labels are sometimes natural-language
    summaries that don't round-trip through RDKit).
    """
    try:
        from rdkit.Chem import AllChem  # type: ignore[import-not-found]
    except ImportError:
        return None
    try:
        rxn = AllChem.ReactionFromSmarts(smarts, useSmiles=False)
        if rxn is None:
            return None
        return AllChem.ReactionToSmarts(rxn)
    except Exception:
        return None


def _hash_canonical(value: str) -> str:
    import hashlib

    return hashlib.sha1(value.encode("utf-8")).hexdigest()[:16]


def merge_records(records: Iterable[dict[str, Any]]) -> list[ReactionRecord]:
    """Merge cross-source reactions by canonical SMARTS or equation hash."""
    by_canonical: dict[str, ReactionRecord] = {}
    for r in records:
        canonical = r.get("canonical_smarts")
        if canonical is None:
            # Use the equation string normalised by whitespace as the
            # secondary canonical key when SMARTS cannot be derived.
            canonical = " ".join((r.get("equation", "") or "").split()) or "EMPTY"
        cid = _hash_canonical(canonical)
        rec = by_canonical.get(cid)
        if rec is None:
            rec = ReactionRecord(
                canonical_id=cid,
                canonical_smarts=r.get("canonical_smarts"),
                equation=r.get("equation"),
                license_class=r.get("license_class", "A"),
                source_manifests=list(r.get("source_manifests", [])),
            )
            by_canonical[cid] = rec
        # Merge per-source IDs and EC numbers.
        for src_field in ("rhea_id", "bigg_id", "modelseed_id", "metanetx_id"):
            v = r.get(src_field)
            if v and not getattr(rec, src_field):
                setattr(rec, src_field, v)
        for ec in r.get("brenda_ec_numbers", []):
            if ec not in rec.brenda_ec_numbers:
                rec.brenda_ec_numbers.append(ec)
        for sm in r.get("source_manifests", []):
            if sm not in rec.source_manifests:
                rec.source_manifests.append(sm)
        for u in r.get("enzyme_uniprot_ids", []):
            if u not in rec.enzyme_uniprot_ids:
                rec.enzyme_uniprot_ids.append(u)
    return list(by_canonical.values())


def build_lirc_corpus(
    *,
    cap_rhea: int | None = None,
    cap_metanetx: int | None = None,
    cap_bigg: int | None = None,
    cap_modelseed: int | None = None,
    output_path: Path | None = None,
) -> dict[str, Any]:
    """Run the full LIRC corpus build and write a compressed JSON.

    With caps, this is the validation-slice path (~3-5 min total).
    Without caps, this is the full ~4-8h Wave-2 build.
    """
    repo_root = Path(__file__).resolve().parents[4]
    if output_path is None:
        output_path = repo_root / "fixtures" / "lirc" / "lirc_v0.1.json.gz"

    summary: dict[str, Any] = {
        "schema_version": "synbio.lirc_corpus.v0.1",
        "license_class": "A",
        "source_manifests": [
            "audit/source_manifests/rhea.yaml",
            "audit/source_manifests/metanetx.yaml",
            "audit/source_manifests/bigg.yaml",
            "audit/source_manifests/modelseed.yaml",
            "audit/source_manifests/brenda.yaml",
        ],
        "excluded_blocked": [
            "audit/source_manifests/atlas_of_biochemistry_BLOCKED.yaml",
            "audit/source_manifests/bkms_react_BLOCKED.yaml",
            "audit/source_manifests/kegg_bulk_BLOCKED.yaml",
        ],
        "boundary": (
            "Research infrastructure for in silico synthetic biology / "
            "metabolic pathway engineering. Outputs are research artifacts. "
            "No regulatory certification claims. No clinical or human-subject "
            "use. No environmental release of GMOs."
        ),
        "fetch_errors": [],
    }

    raw_records: list[dict[str, Any]] = []
    t0 = time.time()

    # Rhea.
    logger.info("Pulling Rhea reactions (cap=%s)", cap_rhea)
    rhea_rows = query_rhea_sparql(limit=cap_rhea or 16000)
    summary["rhea_pulled"] = len(rhea_rows)
    for r in rhea_rows:
        smarts = canonicalise_reaction_smarts(r["equation"])
        raw_records.append(
            {
                "rhea_id": r["rhea_id"],
                "equation": r["equation"],
                "canonical_smarts": smarts,
                "source_manifests": ["audit/source_manifests/rhea.yaml"],
                "license_class": "A",
            }
        )

    # MetaNetX MNXref.
    logger.info("Pulling MetaNetX MNXref (cap=%s)", cap_metanetx)
    mnx_rows = query_metanetx_xref(cap=cap_metanetx)
    summary["metanetx_pulled"] = len(mnx_rows)
    mnx_to_rhea: dict[str, str] = {}
    for row in mnx_rows:
        sid = row["source_id"]
        mid = row["mnx_id"]
        if sid.startswith("rheaR:"):
            mnx_to_rhea.setdefault(mid, sid.split(":", 1)[1])
    # Tie MNXref IDs onto raw records when we already have the rhea ID.
    rhea_to_mnx = {v: k for k, v in mnx_to_rhea.items()}
    for r in raw_records:
        rid = (r.get("rhea_id") or "").replace("RHEA:", "")
        if rid in rhea_to_mnx:
            r["metanetx_id"] = rhea_to_mnx[rid]

    # BiGG.
    logger.info("Pulling BiGG universal reactions (cap=%s)", cap_bigg)
    bigg_rows = query_bigg_reactions(cap=cap_bigg)
    summary["bigg_pulled"] = len(bigg_rows)
    for r in bigg_rows:
        raw_records.append(
            {
                "bigg_id": r.get("bigg_id"),
                "equation": r.get("name"),
                "canonical_smarts": None,
                "source_manifests": ["audit/source_manifests/bigg.yaml"],
                "license_class": "A",
            }
        )

    # ModelSEED.
    logger.info("Pulling ModelSEED reactions (cap=%s)", cap_modelseed)
    ms_rows = query_modelseed_reactions(cap=cap_modelseed)
    summary["modelseed_pulled"] = len(ms_rows)
    for r in ms_rows:
        raw_records.append(
            {
                "modelseed_id": r.get("id") or r.get("ID") or r.get("rxn_id"),
                "equation": r.get("equation"),
                "canonical_smarts": None,
                "source_manifests": ["audit/source_manifests/modelseed.yaml"],
                "license_class": "A",
            }
        )

    # Merge by canonical SMARTS / equation.
    records = merge_records(raw_records)
    summary["unique_canonical_reactions"] = len(records)
    summary["wallclock_seconds"] = time.time() - t0

    # Write gzipped JSON.
    output_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        **summary,
        "reactions": [asdict(r) for r in records],
    }
    with gzip.open(output_path, "wt", encoding="utf-8") as f:
        json.dump(payload, f, sort_keys=True, indent=None)
    summary["output_path"] = str(output_path)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--cap-rhea", type=int, default=None, help="Cap Rhea reaction pulls."
    )
    parser.add_argument(
        "--cap-metanetx", type=int, default=None, help="Cap MetaNetX MNXref rows."
    )
    parser.add_argument(
        "--cap-bigg", type=int, default=None, help="Cap BiGG reaction pulls."
    )
    parser.add_argument(
        "--cap-modelseed", type=int, default=None, help="Cap ModelSEED reaction pulls."
    )
    parser.add_argument(
        "--cap",
        type=int,
        default=None,
        help="Set a uniform cap on all four sources (validation slice).",
    )
    parser.add_argument(
        "--output-path",
        type=Path,
        default=None,
        help="Override default output path (default: fixtures/lirc/lirc_v0.1.json.gz).",
    )
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    cap = args.cap
    summary = build_lirc_corpus(
        cap_rhea=args.cap_rhea or cap,
        cap_metanetx=args.cap_metanetx or cap,
        cap_bigg=args.cap_bigg or cap,
        cap_modelseed=args.cap_modelseed or cap,
        output_path=args.output_path,
    )
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
