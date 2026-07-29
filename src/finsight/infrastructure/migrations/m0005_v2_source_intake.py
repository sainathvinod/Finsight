# Implements: V2 FR-126–FR-135/180–183, NFR-087/110, AC-01 — Workflow 2 intake.
from __future__ import annotations

import sqlite3

VERSION = 5
NAME = "v2_source_intake"


_IMMUTABLE_TABLES = (
    "v2_source_artifacts",
    "v2_source_binding_versions",
    "v2_metadata_evidence_records",
    "v2_source_intake_summaries",
    "v2_source_intake_idempotency",
)


def _append_only_triggers(conn: sqlite3.Connection, table: str) -> None:
    conn.execute(
        f"CREATE TRIGGER IF NOT EXISTS {table}_no_update BEFORE UPDATE ON {table} "
        "BEGIN SELECT RAISE(ABORT, 'append_only'); END"
    )
    conn.execute(
        f"CREATE TRIGGER IF NOT EXISTS {table}_no_delete BEFORE DELETE ON {table} "
        "BEGIN SELECT RAISE(ABORT, 'append_only'); END"
    )


def up(conn: sqlite3.Connection) -> None:
    """Add authoritative source-intake facts without storing workbook bytes or detail rows."""

    conn.execute(
        "CREATE TABLE IF NOT EXISTS v2_source_artifacts("
        "artifact_id TEXT PRIMARY KEY, "
        "source_role TEXT NOT NULL CHECK(source_role IN ('BUDGET','GED')), "
        "first_seen_filename TEXT NOT NULL CHECK(length(trim(first_seen_filename))>0), "
        "byte_size INTEGER NOT NULL CHECK(byte_size>=0), "
        "sha256 TEXT NOT NULL CHECK(length(sha256)=64), "
        "media_type TEXT NOT NULL CHECK(media_type="
        "'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'), "
        "file_extension TEXT NOT NULL CHECK(file_extension='.xlsx'), "
        "first_selected_actor_id TEXT NOT NULL, first_selected_at TEXT NOT NULL, "
        "UNIQUE(source_role,sha256))"
    )
    conn.execute(
        "CREATE TABLE IF NOT EXISTS v2_source_binding_versions("
        "binding_id TEXT PRIMARY KEY, "
        "review_id TEXT NOT NULL REFERENCES v2_review_cycles(review_id), "
        "candidate_id TEXT NOT NULL REFERENCES v2_working_candidates(candidate_id), "
        "source_role TEXT NOT NULL CHECK(source_role IN ('BUDGET','GED')), "
        "artifact_id TEXT NOT NULL REFERENCES v2_source_artifacts(artifact_id), "
        "selected_filename TEXT NOT NULL CHECK(length(trim(selected_filename))>0), "
        "path_hint TEXT NOT NULL, predecessor_binding_id TEXT "
        "REFERENCES v2_source_binding_versions(binding_id), "
        "replacement_reason TEXT NOT NULL, binding_sequence INTEGER NOT NULL "
        "CHECK(binding_sequence>0), selected_actor_id TEXT NOT NULL, "
        "selected_at TEXT NOT NULL, bound_actor_id TEXT NOT NULL, bound_at TEXT NOT NULL, "
        "extraction_profile_version TEXT NOT NULL, layout_profile_version TEXT NOT NULL, "
        "safety_policy_version TEXT NOT NULL, "
        "UNIQUE(candidate_id,source_role,binding_sequence))"
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_v2_source_bindings_review "
        "ON v2_source_binding_versions(review_id,candidate_id,source_role,binding_sequence)"
    )
    conn.execute(
        "CREATE TABLE IF NOT EXISTS v2_candidate_source_heads("
        "candidate_id TEXT NOT NULL REFERENCES v2_working_candidates(candidate_id), "
        "source_role TEXT NOT NULL CHECK(source_role IN ('BUDGET','GED')), "
        "current_binding_id TEXT NOT NULL REFERENCES v2_source_binding_versions(binding_id), "
        "revision INTEGER NOT NULL CHECK(revision>0), updated_actor_id TEXT NOT NULL, "
        "updated_at TEXT NOT NULL, PRIMARY KEY(candidate_id,source_role))"
    )
    conn.execute(
        "CREATE TRIGGER IF NOT EXISTS v2_candidate_source_heads_no_delete "
        "BEFORE DELETE ON v2_candidate_source_heads "
        "BEGIN SELECT RAISE(ABORT, 'head_delete_forbidden'); END"
    )
    conn.execute(
        "CREATE TABLE IF NOT EXISTS v2_metadata_evidence_records("
        "evidence_id TEXT PRIMARY KEY, "
        "review_id TEXT NOT NULL REFERENCES v2_review_cycles(review_id), "
        "candidate_id TEXT NOT NULL REFERENCES v2_working_candidates(candidate_id), "
        "binding_id TEXT NOT NULL REFERENCES v2_source_binding_versions(binding_id), "
        "source_role TEXT NOT NULL CHECK(source_role IN ('BUDGET','GED')), "
        "evidence_type TEXT NOT NULL CHECK(length(trim(evidence_type))>0), "
        "ordinal INTEGER NOT NULL CHECK(ordinal>0), raw_scalar TEXT, normalized_scalar TEXT, "
        "evidence_status TEXT NOT NULL CHECK(length(trim(evidence_status))>0), "
        "worksheet_name TEXT, cell_reference TEXT, source_row INTEGER CHECK(source_row>0), "
        "source_column INTEGER CHECK(source_column>0), parser_profile_version TEXT NOT NULL, "
        "extraction_profile_version TEXT NOT NULL, metadata_policy_version TEXT NOT NULL, "
        "UNIQUE(binding_id,evidence_type,ordinal))"
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_v2_metadata_evidence_candidate "
        "ON v2_metadata_evidence_records(candidate_id,source_role,evidence_type,ordinal)"
    )
    conn.execute(
        "CREATE TABLE IF NOT EXISTS v2_source_intake_summaries("
        "summary_id TEXT PRIMARY KEY, "
        "review_id TEXT NOT NULL REFERENCES v2_review_cycles(review_id), "
        "candidate_id TEXT NOT NULL REFERENCES v2_working_candidates(candidate_id), "
        "summary_sequence INTEGER NOT NULL CHECK(summary_sequence>0), "
        "predecessor_summary_id TEXT REFERENCES v2_source_intake_summaries(summary_id), "
        "budget_binding_id TEXT NOT NULL REFERENCES v2_source_binding_versions(binding_id), "
        "ged_binding_id TEXT NOT NULL REFERENCES v2_source_binding_versions(binding_id), "
        "selected_month INTEGER NOT NULL CHECK(selected_month BETWEEN 1 AND 12), "
        "selected_year INTEGER NOT NULL CHECK(selected_year BETWEEN 1000 AND 9999), "
        "resolved_department_number TEXT, resolved_department_name TEXT, "
        "department_evidence_status TEXT NOT NULL, period_evidence_status TEXT NOT NULL, "
        "department_match_status TEXT NOT NULL, reporting_period_match_status TEXT NOT NULL, "
        "budget_filename TEXT NOT NULL, ged_filename TEXT NOT NULL, "
        "budget_worksheet TEXT NOT NULL, ged_worksheet TEXT NOT NULL, "
        "budget_detail_count INTEGER NOT NULL CHECK(budget_detail_count>=0), "
        "ged_transaction_count INTEGER NOT NULL CHECK(ged_transaction_count>=0), "
        "budget_upload_status TEXT NOT NULL, budget_compatibility_status TEXT NOT NULL, "
        "budget_extraction_status TEXT NOT NULL, budget_structural_issue_count INTEGER NOT NULL "
        "CHECK(budget_structural_issue_count>=0), "
        "ged_upload_status TEXT NOT NULL, ged_compatibility_status TEXT NOT NULL, "
        "ged_extraction_status TEXT NOT NULL, ged_structural_issue_count INTEGER NOT NULL "
        "CHECK(ged_structural_issue_count>=0), "
        "extraction_profile_version TEXT NOT NULL, layout_profile_version TEXT NOT NULL, "
        "safety_policy_version TEXT NOT NULL, metadata_policy_version TEXT NOT NULL, "
        "committed_actor_id TEXT NOT NULL, committed_at TEXT NOT NULL, "
        "summary_hash TEXT NOT NULL CHECK(length(summary_hash)=64), "
        "UNIQUE(review_id,candidate_id,summary_sequence))"
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_v2_intake_summary_review "
        "ON v2_source_intake_summaries(review_id,summary_sequence DESC)"
    )
    conn.execute(
        "CREATE TABLE IF NOT EXISTS v2_source_intake_idempotency("
        "review_id TEXT NOT NULL REFERENCES v2_review_cycles(review_id), "
        "idempotency_key TEXT NOT NULL, request_hash TEXT NOT NULL, "
        "summary_id TEXT NOT NULL REFERENCES v2_source_intake_summaries(summary_id), "
        "actor_id TEXT NOT NULL, committed_at TEXT NOT NULL, "
        "PRIMARY KEY(review_id,idempotency_key))"
    )

    for table in _IMMUTABLE_TABLES:
        _append_only_triggers(conn, table)
