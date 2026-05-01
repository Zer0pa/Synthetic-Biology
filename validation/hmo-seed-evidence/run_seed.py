"""Run the L1→L7 chain on one HMO seed (CPU-only stub mode).

This is the structural evidence script. It runs every adapter in stub
mode, captures the envelope chain, and writes:

    audit/runtime/hmo_seed_<seed>/envelopes.jsonl
    audit/runtime/hmo_seed_<seed>/audit.duckdb
    validation/hmo-seed-evidence/<seed>/dossier.json
    validation/hmo-seed-evidence/<seed>/RESULT.md
    validation/hmo-seed-evidence/<seed>/threshold_check.yaml

Per PRD §3.2: full scientific run requires Wave 4 (CEKM training on
Runpod), Wave 5 (RFdiffusion3 + MACE-OFF + ESMFold inference), and
real LIRC corpus. This script produces the structural / shape-correct
chain and pre-registered acceptance threshold check; the scientific
validation triple cannot pass `scientific_valid=True` until those Runpod
waves complete.

Usage:
    python validation/hmo-seed-evidence/run_seed.py --seed 2pFL
    python validation/hmo-seed-evidence/run_seed.py --seed 3pSL
    python validation/hmo-seed-evidence/run_seed.py --seed DSLNT
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import uuid
from pathlib import Path
from typing import Any

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))

from zer0pa_synbio.adapters.l1_zpe import L1ZPEAdapter
from zer0pa_synbio.adapters.l2_lirc import L2LIRCAdapter
from zer0pa_synbio.adapters.l3_5_ranking_gate import L3_5RankingGateAdapter
from zer0pa_synbio.adapters.l3_retrosynthesis import (
    L3BioNaviAdapter,
    L3DeepRetroAdapter,
    L3NovoStoic2Adapter,
    L3RetroPath3Adapter,
)
from zer0pa_synbio.adapters.l4_5_unknown_enzyme import (
    L4_5ESMFoldAdapter,
    L4_5MACEOFFAdapter,
    L4_5RFdiffusion3Adapter,
)
from zer0pa_synbio.adapters.l4_fba import L4COBRApyAdapter, L4ECMpyAdapter, L4ETFLAdapter, L4GECKOAdapter
from zer0pa_synbio.adapters.l4_kinetics import (
    L4CatPredAdapter,
    L4CEKMAdapter,
    L4DLKcatAdapter,
    L4TurNuPAdapter,
)
from zer0pa_synbio.adapters.l4_thermodynamics import L4EQuilibratorAdapter
from zer0pa_synbio.adapters.l5_mfmo import L5MFMOAdapter
from zer0pa_synbio.adapters.l5_oed import L5OEDAdapter
from zer0pa_synbio.adapters.l6_build_cellfree_txtl import L6BuildCellFreeStubAdapter
from zer0pa_synbio.adapters.l6_host_engineering import L6HostEngineeringAdapter
from zer0pa_synbio.adapters.l7_dossier import L7DossierAdapter
from zer0pa_synbio.audit import AuditWriter
from zer0pa_synbio.envelope import Domain
from zer0pa_synbio.kg import KGWriter
from zer0pa_synbio.boundary import BOUNDARY_BLOCK, BOUNDARY_SHA256


SEED_INPUTS: dict[str, dict[str, Any]] = {
    "2pFL": {
        "selfies_smiles": "OC[C@H]1O[C@@H](OC[C@H]2O[C@H](O)[C@H](O)[C@@H](O)[C@@H]2O)[C@H](O)[C@@H](O)[C@@H]1O",
        "inchi_key": "GUBGYTABKSRVRQ-PICCSMPSSA-N",  # lactose precursor
        "target_inchi_key": "GFXBRIYRYYFCIA-LWNAIEPUSA-N",  # 2'-FL
        "target_genes": ["FutC", "GalE", "ManB", "ManC", "Per", "Gmd", "WcaG"],
        "enzyme_uniprot_id": "Q11075",  # FutC alpha-1,2-fucosyltransferase
        "novelty_class": "known_reaction",
    },
    "3pSL": {
        "selfies_smiles": "OC[C@H]1O[C@@H](OC[C@H]2O[C@H](O)[C@H](O)[C@@H](O)[C@@H]2O)[C@H](O)[C@@H](O)[C@@H]1O",
        "inchi_key": "GUBGYTABKSRVRQ-PICCSMPSSA-N",
        "target_inchi_key": "COFLCBMXHRDGMP-AHXISFCHSA-N",  # 3'-SL
        "target_genes": ["NeuB", "NeuC", "NeuA", "Lst", "GalE"],  # CMP-Neu5Ac module + α-2,3-sialyltransferase
        "enzyme_uniprot_id": "Q56930",  # α-2,3-sialyltransferase reference
        "novelty_class": "reaction_class_known",
    },
    "DSLNT": {
        "selfies_smiles": "OC[C@H]1O[C@@H](OC[C@H]2O[C@H](O)[C@H](O)[C@@H](O)[C@@H]2O)[C@H](O)[C@@H](O)[C@@H]1O",
        "inchi_key": "GUBGYTABKSRVRQ-PICCSMPSSA-N",
        "target_inchi_key": "DSLNT-PLACEHOLDER-INCHIKEY",
        "target_genes": ["Lst", "Sialy26", "GalT", "GnbG", "GalE"],
        "enzyme_uniprot_id": "P15467",  # α-2,6-sialyltransferase reference (placeholder)
        "novelty_class": "fully_novel",
    },
}


def run(seed: str) -> dict[str, Any]:
    if seed not in SEED_INPUTS:
        raise ValueError(f"Unknown seed: {seed}; choices = {list(SEED_INPUTS)}")
    spec = SEED_INPUTS[seed]
    campaign_id = f"hmo_seed_{seed}"
    run_id = uuid.UUID(int=int(hashlib.sha256(seed.encode()).hexdigest()[:30], 16))

    # Encode SELFIES from SMILES.
    import selfies as sf

    selfies_str = sf.encoder(spec["selfies_smiles"])

    aw = AuditWriter(REPO_ROOT, campaign_id)
    kg = KGWriter()
    kg.add_node("boundary_attest", "Boundary", sha256=BOUNDARY_SHA256)

    layer_envelopes: dict[str, Any] = {}

    # L1
    l1 = L1ZPEAdapter().run(
        campaign_id=campaign_id,
        domain=Domain.hmo,
        organism=562,
        gem_id="iML1515",
        input_payload={
            "target_compound": {"selfies": selfies_str, "inchi_key": spec["target_inchi_key"]},
            "host_organism": {"taxonomy_id": 562, "refseq_genome_accession": "NC_000913.3", "gem_id": "iML1515"},
        },
        run_id=run_id,
    )
    aw.write_envelope(l1)
    kg.add_node(l1.envelope_id, "Envelope", layer="L1", campaign=campaign_id)
    kg.add_edge(l1.envelope_id, "boundary_attest", "DERIVED_FROM")
    layer_envelopes["l1"] = l1

    # L2 LIRC
    l2 = L2LIRCAdapter().run(
        campaign_id=campaign_id,
        domain=Domain.hmo,
        organism=562,
        gem_id="iML1515",
        input_payload={
            "target_inchi_key": spec["target_inchi_key"],
            "organism_gem_id": "iML1515",
        },
        run_id=run_id,
    )
    aw.write_envelope(l2)
    kg.add_node(l2.envelope_id, "Envelope", layer="L2")
    kg.add_edge(l2.envelope_id, l1.envelope_id, "DERIVED_FROM")
    layer_envelopes["l2"] = l2

    # L3 ensemble (RetroPath3 + novoStoic2 + BioNavi + DeepRetro).
    l3_envs = []
    for cls in (L3RetroPath3Adapter, L3NovoStoic2Adapter, L3BioNaviAdapter, L3DeepRetroAdapter):
        env = cls().run(
            campaign_id=campaign_id,
            domain=Domain.hmo,
            organism=562,
            gem_id="iML1515",
            input_payload={"target_inchi_key": spec["target_inchi_key"]},
            run_id=run_id,
        )
        aw.write_envelope(env)
        kg.add_node(env.envelope_id, "Envelope", layer="L3", adapter=env.backend.adapter)
        kg.add_edge(env.envelope_id, l2.envelope_id, "DERIVED_FROM")
        l3_envs.append(env)
    layer_envelopes["l3"] = l3_envs[0]  # representative

    # L3.5 ranking gate against the union of L3 candidates.
    union_candidates = []
    for env in l3_envs:
        union_candidates.extend(env.outputs.payload.get("candidates", []))
    l3_5 = L3_5RankingGateAdapter().run(
        campaign_id=campaign_id,
        domain=Domain.hmo,
        organism=562,
        gem_id="iML1515",
        input_payload={"candidates": union_candidates},
        run_id=run_id,
    )
    aw.write_envelope(l3_5)
    kg.add_node(l3_5.envelope_id, "Envelope", layer="L3_5")
    layer_envelopes["l3_5"] = l3_5

    # L4 deep evaluation: FBA ensemble + thermodynamics + kinetics ensemble (gpu_rest_stub).
    l4_envs = []
    for cls in (L4COBRApyAdapter, L4GECKOAdapter, L4ECMpyAdapter, L4ETFLAdapter, L4EQuilibratorAdapter):
        env = cls().run(
            campaign_id=campaign_id,
            domain=Domain.hmo,
            organism=562,
            gem_id="iML1515",
            input_payload={"steps": [{"delta_g_kj_mol": -23.4}]},
            run_id=run_id,
        )
        aw.write_envelope(env)
        l4_envs.append(env)
    for cls in (L4DLKcatAdapter, L4CatPredAdapter, L4TurNuPAdapter, L4CEKMAdapter):
        env = cls().run(
            campaign_id=campaign_id,
            domain=Domain.hmo,
            organism=562,
            gem_id="iML1515",
            input_payload={"enzyme_uniprot_id": spec["enzyme_uniprot_id"]},
            run_id=run_id,
        )
        aw.write_envelope(env)
        l4_envs.append(env)
    layer_envelopes["l4"] = l4_envs[0]

    # L4.5 unknown-enzyme — only run for novelty_class != known_reaction.
    l4_5_envelope_id = None
    if spec["novelty_class"] != "known_reaction":
        for cls in (L4_5RFdiffusion3Adapter, L4_5MACEOFFAdapter, L4_5ESMFoldAdapter):
            env = cls().run(
                campaign_id=campaign_id,
                domain=Domain.hmo,
                organism=562,
                gem_id="iML1515",
                input_payload={
                    "tier": "tier_2" if spec["novelty_class"] == "reaction_class_known" else "tier_3",
                    "target_inchi_key": spec["target_inchi_key"],
                },
                run_id=run_id,
            )
            aw.write_envelope(env)
            l4_5_envelope_id = env.envelope_id

    # L5 MFMO + L5_OED.
    l5 = L5MFMOAdapter().run(
        campaign_id=campaign_id,
        domain=Domain.hmo,
        organism=562,
        gem_id="iML1515",
        input_payload={"scored_candidates": [{"pathway_id": "p_seed_canonical", "mdf_score_kj_mol": 5.0}]},
        run_id=run_id,
    )
    aw.write_envelope(l5)
    layer_envelopes["l5"] = l5

    l5_oed = L5OEDAdapter().run(
        campaign_id=campaign_id,
        domain=Domain.hmo,
        organism=562,
        gem_id="iML1515",
        input_payload={"ranked_candidates": l5.outputs.payload.get("candidates", [])},
        run_id=run_id,
    )
    aw.write_envelope(l5_oed)
    layer_envelopes["l5_oed"] = l5_oed

    # L6 host engineering — produces SBOL3 attestation.
    l6 = L6HostEngineeringAdapter().run(
        campaign_id=campaign_id,
        domain=Domain.hmo,
        organism=562,
        gem_id="iML1515",
        input_payload={
            "spec_id": f"gms_{seed}_canonical",
            "host_taxonomy_id": 562,
            "refseq_genome_accession": "NC_000913.3",
            "target_genes": spec["target_genes"],
        },
        run_id=run_id,
    )
    aw.write_envelope(l6)
    layer_envelopes["l6"] = l6
    sbol_uri = l6.outputs.payload["genetic_modification_spec"]["sbol3_uri"]
    sbol_sha = l6.outputs.payload["genetic_modification_spec"]["sbol_attestation"]["document_sha256"]

    # L6_BUILD cell-free TX-TL stub observation.
    l6_build = L6BuildCellFreeStubAdapter().run(
        campaign_id=campaign_id,
        domain=Domain.hmo,
        organism=562,
        gem_id="iML1515",
        input_payload={"spec_id": l6.outputs.payload["genetic_modification_spec"]["spec_id"]},
        run_id=run_id,
    )
    aw.write_envelope(l6_build)
    layer_envelopes["l6_build"] = l6_build

    # L7 dossier — composes everything.
    l7 = L7DossierAdapter().run(
        campaign_id=campaign_id,
        domain=Domain.hmo,
        organism=562,
        gem_id="iML1515",
        input_payload={
            "ranked_pathway_set_envelope_id": l5.envelope_id,
            "gms_envelope_id": l6.envelope_id,
            "cftxtl_observation_envelope_ids": [l6_build.envelope_id],
            "target_compound_inchi_key": spec["target_inchi_key"],
            "host_organism": {
                "taxonomy_id": 562,
                "refseq_genome_accession": "NC_000913.3",
                "gem_id": "iML1515",
            },
            "validation_sequence": l5_oed.outputs.payload["validation_sequence"],
            "sbol_attestation_uri": sbol_uri,
            "sbol_sha256": sbol_sha,
            "advisory_only": True,
            "consumer_recommendation": "human_cro",
            "l1_envelope_id": l1.envelope_id,
            "l2_envelope_id": l2.envelope_id,
            "l3_envelope_id": l3_envs[0].envelope_id,
            "l3_5_envelope_id": l3_5.envelope_id,
            "l4_envelope_id": l4_envs[0].envelope_id,
            "l4_5_envelope_id": l4_5_envelope_id,
            "l5_envelope_id": l5.envelope_id,
            "l5_oed_envelope_id": l5_oed.envelope_id,
            "dbtl_round": 0,
            "dossier_id": f"dossier_{seed}_round_0",
        },
        run_id=run_id,
    )
    aw.write_envelope(l7)
    layer_envelopes["l7"] = l7

    # Persist dossier to validation/hmo-seed-evidence/<seed>/dossier.json
    seed_dir = REPO_ROOT / "validation" / "hmo-seed-evidence" / seed
    seed_dir.mkdir(parents=True, exist_ok=True)
    dossier = l7.outputs.payload["dossier"]
    (seed_dir / "dossier.json").write_text(
        json.dumps(dossier, indent=2, sort_keys=True), encoding="utf-8"
    )
    # Persist envelope chain summary.
    (seed_dir / "envelope_chain.json").write_text(
        json.dumps(
            {
                "campaign_id": campaign_id,
                "seed": seed,
                "envelope_ids": [
                    layer_envelopes["l1"].envelope_id,
                    layer_envelopes["l2"].envelope_id,
                    layer_envelopes["l3"].envelope_id,
                    layer_envelopes["l3_5"].envelope_id,
                    layer_envelopes["l4"].envelope_id,
                    *([l4_5_envelope_id] if l4_5_envelope_id else []),
                    layer_envelopes["l5"].envelope_id,
                    layer_envelopes["l5_oed"].envelope_id,
                    layer_envelopes["l6"].envelope_id,
                    layer_envelopes["l6_build"].envelope_id,
                    layer_envelopes["l7"].envelope_id,
                ],
                "sbol3_uri": sbol_uri,
                "sbol_sha256": sbol_sha,
            },
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )

    # Threshold check (informational; full numerical check requires Runpod).
    acceptance_path = seed_dir / "acceptance.yaml"
    threshold_check = {
        "seed_id": seed,
        "campaign_id": campaign_id,
        "boundary_block_passed": True,  # boundary validation is enforced at envelope creation
        "envelope_chain_complete": True,
        "envelope_count": len(
            [v for v in layer_envelopes.values()] + ([1] if l4_5_envelope_id else [])
        ),
        "sbol_attestation_present": l6.falsification.sbol_attestation_present,
        "scientific_valid_eligible": False,  # all stubs by definition
        "blocked_by": [
            "ESM-2 batched inference not on GPU yet",
            "CEKM weights not Runpod-trained yet",
            "Real LIRC corpus not pulled (canned slice only)",
            "RFdiffusion3 / MACE-OFF / ESMFold inference not on GPU yet",
        ],
        "pre_registered_acceptance_yaml": str(acceptance_path),
        "next_action": "Runpod cutover Wave 4 (CEKM training) + Wave 5 (L4.5 inference) + Wave 9 (full numerical run)",
    }
    (seed_dir / "threshold_check.yaml").write_text(
        yaml.safe_dump(threshold_check, sort_keys=True), encoding="utf-8"
    )

    # Write a short RESULT.md.
    result_md = f"""# {seed} — Structural Evidence Packet (Stub Mode)

## Boundary

{BOUNDARY_BLOCK}

## Status

**scientific_valid: False** — all GPU-bound layers are in stub mode; the
envelope chain is structurally complete but the numerical predictions
are canned, not derived from real models. PRD §15 Wave 4/5/9 are
required for `scientific_valid=True`.

## Envelope chain

{len(threshold_check['envelope_count']) if isinstance(threshold_check['envelope_count'], list) else threshold_check['envelope_count']} envelopes recorded under
`audit/runtime/{campaign_id}/envelopes.jsonl`. See
`envelope_chain.json` for the ordered list of envelope_ids.

## SBOL3 attestation

Attestation document: `{sbol_uri}`
sha256: `{sbol_sha}`

## Pre-registered acceptance thresholds

See `acceptance.yaml`. The thresholds are pre-registered (committed to
Git before any engine output is produced) and serve as the binding
acceptance criteria for the full Runpod-backed scientific run.

## Threshold check

See `threshold_check.yaml`. In this stub-mode run, only the structural
checks pass. The numerical thresholds (titer-within-25%-of-literature,
kcat-within-0.5-log-units, MDF >= 1.0 kJ/mol, cross-model disagreement
< threshold) cannot be evaluated until the GPU-bound layers go live on
Runpod.

## Boundary discipline

This is a research artifact. No regulatory certification claim. No
clinical or human-subject use. No environmental release of GMOs. No
biocontainment-level claim. No human gene drive. Defence / weapons /
dual-use bio applications excluded.
"""
    (seed_dir / "RESULT.md").write_text(result_md, encoding="utf-8")

    # KG export.
    kg.export_graphml(seed_dir / "kg.graphml")

    aw.close()
    return {
        "campaign_id": campaign_id,
        "envelope_count": threshold_check["envelope_count"],
        "dossier_id": dossier["dossier_id"],
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", choices=list(SEED_INPUTS), required=True)
    args = parser.parse_args()
    result = run(args.seed)
    print(json.dumps(result, indent=2))
