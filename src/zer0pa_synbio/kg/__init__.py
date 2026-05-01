"""Knowledge-graph writer: nodes/edges CSV + GraphML/RDF export.

References:
- PRD.md § 9 KG nodes/edges.
- kg/schema.cypher, kg/nodes.csv, kg/edges.csv (canonical taxonomy).

The KG is a Tier-3 export by default — public falsifier discoveries,
LIRC contributions, PathGym splits. Tier-1 customer-confidential data is
written to a per-campaign isolated KG store under
`audit/runtime/<campaign_id>/kg/` and never merged into the public export.
"""

from __future__ import annotations

import csv
from collections.abc import Iterable
from pathlib import Path

import networkx as nx


VALID_NODE_LABELS = {
    "Boundary",
    "Compound",
    "Reaction",
    "Pathway",
    "Enzyme",
    "Organism",
    "Strain",
    "Modification",
    "Assay",
    "GeneticModificationSpec",
    "CellFreeTXTLObservation",
    "Dossier",
    "Envelope",
    "SBOLDocument",
    "ProvActivity",
    "ProvAgent",
    "ProvEntity",
    "ToolAdapter",
    "ModelCheckpoint",
    "SimulationRun",
    "PathwayCandidate",
    "ScoredPathway",
    "RankedPathway",
    "ValidationExperiment",
    "FalsifierResult",
    "DisagreementRecord",
    "EarlyWarningSignal",
    "LicenseFinding",
    "RightsPolicy",
    "SourceManifest",
    "ReasonerTuple",
    "TDADiagram",
    "FluxGraph",
    "Embedding",
}


VALID_EDGE_TYPES = {
    "catalyses",
    "requires_cofactor",
    "produces",
    "consumes",
    "encodes",
    "regulates",
    "has_source",
    "has_falsifier",
    "has_audit",
    "member_of_pathway",
    "instantiates_in_organism",
    "measured_by",
    "supports",
    "contradicts",
    "DERIVED_FROM",
    "USED_TOOL",
    "USED_MODEL",
    "USED_SOURCE",
    "PRODUCED",
    "VALIDATED_BY",
    "FAILED_BY",
    "DISAGREES_WITH",
    "FEEDS_L4",
    "FEEDS_L5",
    "ATTESTED_BY_SBOL",
    "PROV_GENERATED",
    "PROV_USED",
    "PROV_WAS_DERIVED_FROM",
    "RIGHTS_CONSTRAINED_BY",
    "OWNED_BY",
}


class KGWriter:
    """In-memory knowledge graph builder with GraphML / Cypher / RDF export."""

    def __init__(self) -> None:
        self.g = nx.MultiDiGraph()

    def add_node(self, node_id: str, label: str, **properties: object) -> None:
        if label not in VALID_NODE_LABELS:
            raise ValueError(f"Invalid node label {label!r}; not in KG taxonomy")
        if node_id in self.g.nodes:
            # Merge properties; keep label.
            self.g.nodes[node_id].update(properties)
        else:
            self.g.add_node(node_id, label=label, **properties)

    def add_edge(
        self,
        from_id: str,
        to_id: str,
        edge_type: str,
        **properties: object,
    ) -> None:
        if edge_type not in VALID_EDGE_TYPES:
            raise ValueError(f"Invalid edge type {edge_type!r}; not in KG taxonomy")
        self.g.add_edge(from_id, to_id, key=edge_type, type=edge_type, **properties)

    def export_graphml(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        nx.write_graphml(self.g, path)

    def export_cypher(self, path: Path) -> None:
        """Emit a Cypher CREATE script for the graph (Neo4j ingest path)."""
        lines = []
        for node_id, attrs in self.g.nodes(data=True):
            label = attrs.get("label", "Node")
            props = {k: v for k, v in attrs.items() if k != "label"}
            props["id"] = node_id
            prop_str = ", ".join(f"{k}: {self._cy(v)}" for k, v in props.items())
            lines.append(f"CREATE (:{label} {{{prop_str}}});")
        for u, v, key, attrs in self.g.edges(data=True, keys=True):
            etype = attrs.get("type", key)
            props = {k: val for k, val in attrs.items() if k != "type"}
            prop_str = ", ".join(f"{k}: {self._cy(val)}" for k, val in props.items())
            prop_part = f" {{{prop_str}}}" if prop_str else ""
            lines.append(
                f"MATCH (a {{id: {self._cy(u)}}}), (b {{id: {self._cy(v)}}}) "
                f"CREATE (a)-[:{etype}{prop_part}]->(b);"
            )
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    def export_rdf(self, path: Path, base_uri: str = "https://zer0pa.ai/synbio/kg/") -> None:
        """Emit RDF Turtle. Uses simple URI scheme; PROV-O alignment is the
        consumer's responsibility."""
        from rdflib import Graph, Literal, Namespace, URIRef
        from rdflib.namespace import RDF, RDFS

        g = Graph()
        ns = Namespace(base_uri)
        g.bind("synbio", ns)
        for node_id, attrs in self.g.nodes(data=True):
            label = attrs.get("label", "Node")
            uri = URIRef(base_uri + node_id)
            g.add((uri, RDF.type, ns[label]))
            g.add((uri, RDFS.label, Literal(node_id)))
            for k, v in attrs.items():
                if k == "label":
                    continue
                g.add((uri, ns[k], Literal(v)))
        for u, v, key, attrs in self.g.edges(data=True, keys=True):
            etype = attrs.get("type", key)
            g.add((URIRef(base_uri + u), ns[etype], URIRef(base_uri + v)))
        path.parent.mkdir(parents=True, exist_ok=True)
        g.serialize(destination=str(path), format="turtle")

    @staticmethod
    def _cy(v: object) -> str:
        """Cypher literal serialiser for primitive values."""
        if isinstance(v, str):
            return '"' + v.replace('"', '\\"') + '"'
        if isinstance(v, bool):
            return "true" if v else "false"
        if v is None:
            return "null"
        return str(v)

    def stats(self) -> dict[str, int]:
        return {
            "nodes": self.g.number_of_nodes(),
            "edges": self.g.number_of_edges(),
            "node_labels": len({d["label"] for _, d in self.g.nodes(data=True) if "label" in d}),
            "edge_types": len({d["type"] for _, _, d in self.g.edges(data=True) if "type" in d}),
        }


__all__ = ["KGWriter", "VALID_NODE_LABELS", "VALID_EDGE_TYPES"]
