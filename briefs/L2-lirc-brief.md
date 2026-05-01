# L2 — LIRC corpus / metabolic knowledge brief

**Adapter:** `zer0pa_synbio.adapters.l2_lirc.L2LIRCAdapter`
**Layer:** L2 · v0.1 · references PRD §6.2
**Status:** real Rhea/EC/UniProt/InChIKey-typed slice for 2'-FL + 3'-SL biosynthesis; full LIRC corpus build deferred (Wave 2).

## Boundary

Research infrastructure for in silico synthetic biology / metabolic pathway engineering. Outputs are research artifacts — predicted pathways, predicted KPIs, candidate genetic modification specifications. No regulatory certification claims. No clinical or human-subject use. No environmental release of GMOs. No biocontainment-level claims (the pipeline does not commission BSL-2/3 work). No human gene drive or eugenic application. Defence / weapons / dual-use bio applications excluded under operator policy.

## Purpose

Resolve a `(target_inchi_key, organism_gem_id)` query into a `ReactionGraph` envelope: nodes are `Compound | Reaction | Enzyme`, edges are `produces | consumes | catalyses | requires_cofactor`. The graph is reconciled across **license-clean** sources only.

## Sources (all Class A/B; license-class-enforced)

| Source | License | Use |
|---|---|---|
| Rhea | CC0 (Class A) | reaction equations + balanced atom maps |
| MetaNetX MNXref 4.5 | CC BY 4.0 (Class A) | namespace reconciliation |
| BiGG REST | CC BY 4.0 (Class A) | GEM-derived reaction lists, iML1515 |
| ModelSEED | MIT (Class A) | reconstruction reference + FBA disagreement |
| BRENDA bulk core | CC BY 4.0 (Class A) | enzyme-reaction associations |

## Hard exclusions (binding)

| Source | Reason |
|---|---|
| BKMS-react | Proprietary (Class E); falsifier f018 hard-blocks |
| KEGG bulk content | Commercial (Class E); single-entry IDs as cross-references only |
| ATLAS of Biochemistry | Academic-subscription, no redistribution (Class D); URL/DOI cross-references only |

## Current slice

`fixtures/lirc/2pfl_canonical.json` — 5 canonical reactions for the 2'-FL + 3'-SL pathways:

- RHEA:23900 — Gmd (EC 4.2.1.47, P0AC88): GDP-mannose → GDP-4-keto-6-deoxy-D-mannose
- RHEA:18225 — WcaG (EC 1.1.1.271, P32055): GDP-4-keto-6-deoxy-D-mannose + NADPH → GDP-L-fucose
- RHEA:14457 — FutC (EC 2.4.1.69, Q11075): GDP-L-fucose + lactose → 2'-FL + GDP
- RHEA:13089 — NeuA (EC 2.7.7.43, P0A6S0): CTP + N-acetylneuraminate → CMP-Neu5Ac
- RHEA:14217 — Lst (EC 2.4.99.6, Q56930): CMP-Neu5Ac + lactose → 3'-SL

The Rhea record fetch is a 403 from the public REST endpoint without proper UA/cookies; full record data should be pulled via `https://sparql.rhea-db.org` once authenticated. The IDs + EC + UniProt + InChIKey metadata are the load-bearing data.

## Outputs

```yaml
output_payload:
  reaction_graph:
    schema_version: "synbio.reaction_graph.v0.1"
    nodes:
      - {type: Compound, id: <InChIKey>, ...}
      - {type: Reaction, id: <Rhea ID>, ec: <EC>, ...}
      - {type: Enzyme, id: <UniProt>, ec: <EC>, ...}
    edges:
      - {from: <reaction>, to: <compound>, type: produces|consumes}
      - {from: <enzyme>, to: <reaction>, type: catalyses}
    provenance:
      lirc_slice_uri: "fixtures/lirc/2pfl_canonical.json"
      license_class: "A"
      source_manifests: [...]
      excluded_sources_for_this_query: ["atlas_of_biochemistry_BLOCKED", "bkms_react_BLOCKED", "kegg_bulk_BLOCKED"]
```

## Falsifiers in scope

- `f018_license_drift` (Tier C, fail) — any forbidden-source citation rejected.
- `f021_reaction_not_atom_balanced` (Tier A, fail) — atom-map check at LIRC import time.

## Open questions

- Atom-map canonicalisation strategy: MetaCyc's atom-mapped SMARTS vs RDKit's reaction-mapping — pick one for v1 LIRC.
- KEGG single-entry queries: are they cross-references-only (current policy) or can selected fields (e.g., the equation) be excerpted under fair-use? Current default = pointer only.

## Plug-replaceability

The `reaction_graph` payload schema is invariant across LIRC source-set choices. Removing MetaNetX (use direct Rhea + BiGG only) drops coverage measurably; the test in PRD §6.2 "Plug-replaceability test" verifies that envelope schema is unchanged.

## Wave 2 outstanding (Runpod CPU-feasible)

Full LIRC build:
1. Rhea SPARQL bulk pull (~70k reactions).
2. MNXref reconciliation against MetaNetX 4.5 chemicals + reactions.
3. BiGG REST pull for iML1515 + Yeast9 + ModelSEED reconstructions.
4. BRENDA bulk core CC BY 4.0.
5. Atom-map canonicalisation + dedup.
6. HF push to `Architect-Prime/synbio-lirc-v0.1`.
