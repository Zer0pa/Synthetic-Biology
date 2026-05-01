"""Audit log: JSONL + DuckDB writer + verifier.

References:
- PRD.md § 9 Audit trail and KG.
- docs/synbio-audit-trail-v0.1-spec.md.

Storage layout:

    audit/runtime/<campaign_id>/envelopes.jsonl     # append-only line-per-envelope
    audit/runtime/<campaign_id>/audit.duckdb        # query layer
    audit/runtime/<campaign_id>/sbol/<spec_id>.sbol3.xml   # SBOL3 docs
    audit/runtime/<campaign_id>/disagreement.jsonl  # CrossModelDisagreementRecord
    audit/runtime/<campaign_id>/early_warning.jsonl # EarlyWarningSignal
    audit/runtime/<campaign_id>/falsifier_results.jsonl
    audit/runtime/<campaign_id>/dossiers/<dossier_id>.json

Writes are append-only and idempotent; envelope_id collisions are flagged
but not silently overwritten.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Iterable

import duckdb

from zer0pa_synbio.envelope import UniversalLayerEnvelope, canonical_json
from zer0pa_synbio.types import (
    CrossModelDisagreementRecord,
    Dossier,
    EarlyWarningSignal,
)


def _runtime_dir(repo_root: Path, campaign_id: str) -> Path:
    p = repo_root / "audit" / "runtime" / campaign_id
    p.mkdir(parents=True, exist_ok=True)
    (p / "sbol").mkdir(exist_ok=True)
    (p / "dossiers").mkdir(exist_ok=True)
    return p


class AuditWriter:
    """Append-only audit writer for one campaign.

    Usage:

        writer = AuditWriter(repo_root, campaign_id)
        writer.write_envelope(env)
        writer.write_disagreement(record)
        writer.write_early_warning(signal)
        writer.write_dossier(dossier)
        writer.close()
    """

    def __init__(self, repo_root: Path, campaign_id: str):
        self.repo_root = repo_root
        self.campaign_id = campaign_id
        self.runtime = _runtime_dir(repo_root, campaign_id)
        self.envelopes_path = self.runtime / "envelopes.jsonl"
        self.disagreement_path = self.runtime / "disagreement.jsonl"
        self.early_warning_path = self.runtime / "early_warning.jsonl"
        self.falsifier_results_path = self.runtime / "falsifier_results.jsonl"
        self.duckdb_path = self.runtime / "audit.duckdb"
        self._con = duckdb.connect(str(self.duckdb_path))
        self._init_schema()

    def _init_schema(self) -> None:
        self._con.execute(
            """
            CREATE TABLE IF NOT EXISTS envelopes (
                envelope_id VARCHAR PRIMARY KEY,
                campaign_id VARCHAR,
                run_id VARCHAR,
                layer VARCHAR,
                domain VARCHAR,
                organism INTEGER,
                gem_id VARCHAR,
                mode VARCHAR,
                adapter VARCHAR,
                tool VARCHAR,
                tool_version VARCHAR,
                execution_mode VARCHAR,
                license_class VARCHAR,
                license_evidence_uri VARCHAR,
                gate_status VARCHAR,
                scientific_valid BOOLEAN,
                created_at VARCHAR,
                input_hash VARCHAR,
                output_hash VARCHAR,
                config_hash VARCHAR,
                git_sha VARCHAR,
                payload_json VARCHAR
            );
            CREATE TABLE IF NOT EXISTS falsifier_results (
                envelope_id VARCHAR,
                falsifier_id VARCHAR,
                triggered BOOLEAN,
                severity VARCHAR,
                gate_action VARCHAR,
                message VARCHAR
            );
            CREATE TABLE IF NOT EXISTS disagreement_records (
                record_id VARCHAR PRIMARY KEY,
                envelope_id VARCHAR,
                layer VARCHAR,
                quantity VARCHAR,
                metric VARCHAR,
                status VARCHAR,
                payload_json VARCHAR
            );
            CREATE TABLE IF NOT EXISTS early_warning_signals (
                signal_id VARCHAR PRIMARY KEY,
                source_envelope_id VARCHAR,
                domain VARCHAR,
                status VARCHAR,
                warning_score DOUBLE,
                payload_json VARCHAR
            );
            CREATE TABLE IF NOT EXISTS dossiers (
                dossier_id VARCHAR PRIMARY KEY,
                campaign_id VARCHAR,
                dbtl_round INTEGER,
                target_compound_inchi_key VARCHAR,
                advisory_only BOOLEAN,
                consumer_recommendation VARCHAR,
                payload_json VARCHAR
            );
            """
        )

    def write_envelope(self, env: UniversalLayerEnvelope) -> None:
        # Append JSONL.
        line = canonical_json(env.model_dump(mode="json")).decode("utf-8") + "\n"
        with open(self.envelopes_path, "a", encoding="utf-8") as f:
            f.write(line)
        # Insert into DuckDB.
        self._con.execute(
            "INSERT OR REPLACE INTO envelopes VALUES "
            "(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            [
                env.envelope_id,
                env.campaign_id,
                str(env.run_id),
                env.layer.value,
                env.domain.value,
                env.organism,
                env.gem_id,
                env.mode.value,
                env.backend.adapter,
                env.backend.tool,
                env.backend.tool_version,
                env.backend.execution_mode.value,
                env.backend.license_class.value,
                env.backend.license_evidence_uri,
                env.falsification.gate_status.value,
                env.falsification.scientific_valid,
                env.provenance.created_at,
                env.provenance.input_hash,
                env.provenance.output_hash,
                env.provenance.config_hash,
                env.provenance.git_sha,
                line.strip(),
            ],
        )
        # Falsifier results table (envelope-level failures).
        for f in env.falsification.failures:
            self._con.execute(
                "INSERT INTO falsifier_results VALUES (?,?,?,?,?,?)",
                [env.envelope_id, f.gate_id, True, f.severity, "", f.message],
            )

    def write_disagreement(self, record: CrossModelDisagreementRecord) -> None:
        line = canonical_json(record.model_dump(mode="json")).decode("utf-8") + "\n"
        with open(self.disagreement_path, "a", encoding="utf-8") as f:
            f.write(line)
        self._con.execute(
            "INSERT OR REPLACE INTO disagreement_records VALUES (?,?,?,?,?,?,?)",
            [
                record.record_id,
                record.envelope_id,
                record.layer,
                record.quantity,
                record.metric,
                record.status,
                line.strip(),
            ],
        )

    def write_early_warning(self, signal: EarlyWarningSignal) -> None:
        line = canonical_json(signal.model_dump(mode="json")).decode("utf-8") + "\n"
        with open(self.early_warning_path, "a", encoding="utf-8") as f:
            f.write(line)
        self._con.execute(
            "INSERT OR REPLACE INTO early_warning_signals VALUES (?,?,?,?,?,?)",
            [
                signal.signal_id,
                signal.source_envelope_id,
                signal.domain,
                signal.status,
                signal.warning_score,
                line.strip(),
            ],
        )

    def write_dossier(self, dossier: Dossier) -> None:
        out = self.runtime / "dossiers" / f"{dossier.dossier_id}.json"
        out.write_text(
            canonical_json(dossier.model_dump(mode="json")).decode("utf-8"), encoding="utf-8"
        )
        self._con.execute(
            "INSERT OR REPLACE INTO dossiers VALUES (?,?,?,?,?,?,?)",
            [
                dossier.dossier_id,
                dossier.campaign_id,
                dossier.dbtl_round,
                dossier.target_compound_inchi_key,
                dossier.advisory_only,
                dossier.consumer_recommendation,
                canonical_json(dossier.model_dump(mode="json")).decode("utf-8"),
            ],
        )

    def query(self, sql: str, params: list[Any] | None = None) -> list[tuple[Any, ...]]:
        cur = self._con.execute(sql, params or [])
        return cur.fetchall()

    def close(self) -> None:
        self._con.close()


__all__ = ["AuditWriter", "_runtime_dir"]
