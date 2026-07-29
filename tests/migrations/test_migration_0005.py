"""Migration 0005 verification for Workflow 2 authoritative source intake.

Traces: FR-126–FR-135/180–183, NFR-087/NFR-110, AC-01.
"""
from __future__ import annotations

import sqlite3

from finsight.infrastructure.migrations import (
    m0001_baseline,
    m0002_ai_platform,
    m0003_review_lifecycle,
    m0004_v2_review_management,
    m0005_v2_source_intake,
)


INTAKE_TABLES = {
    "v2_source_artifacts",
    "v2_source_binding_versions",
    "v2_candidate_source_heads",
    "v2_metadata_evidence_records",
    "v2_source_intake_summaries",
    "v2_source_intake_idempotency",
}

IMMUTABLE_TABLES = INTAKE_TABLES - {"v2_candidate_source_heads"}


def _connection() -> sqlite3.Connection:
    connection = sqlite3.connect(":memory:")
    connection.execute("PRAGMA foreign_keys=ON")
    for migration in (
        m0001_baseline,
        m0002_ai_platform,
        m0003_review_lifecycle,
        m0004_v2_review_management,
    ):
        migration.up(connection)
    return connection


def test_migration_0005_creates_authoritative_only_intake_schema_and_guards():
    connection = _connection()
    m0005_v2_source_intake.up(connection)

    tables = {
        row[0]
        for row in connection.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        )
    }
    assert INTAKE_TABLES.issubset(tables)

    triggers = {
        row[0]
        for row in connection.execute(
            "SELECT name FROM sqlite_master WHERE type='trigger'"
        )
    }
    for table in IMMUTABLE_TABLES:
        assert f"{table}_no_update" in triggers
        assert f"{table}_no_delete" in triggers
    assert "v2_candidate_source_heads_no_update" not in triggers
    assert "v2_candidate_source_heads_no_delete" in triggers

    for table in INTAKE_TABLES:
        columns = connection.execute(f"PRAGMA table_info({table})").fetchall()
        assert all(column[2].upper() != "BLOB" for column in columns)
        prohibited = {"workbook_bytes", "extracted_rows", "detail_rows", "row_payload"}
        assert prohibited.isdisjoint({column[1] for column in columns})
    connection.close()


def test_migration_0005_is_idempotent_and_does_not_rewrite_records():
    connection = _connection()
    m0005_v2_source_intake.up(connection)
    connection.execute(
        "INSERT INTO v2_source_artifacts("
        "artifact_id,source_role,first_seen_filename,byte_size,sha256,media_type,"
        "file_extension,first_selected_actor_id,first_selected_at"
        ") VALUES(?,?,?,?,?,?,?,?,?)",
        (
            "artifact-budget",
            "BUDGET",
            "Budget.xlsx",
            100,
            "a" * 64,
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            ".xlsx",
            "actor",
            "2026-07-27T00:00:00Z",
        ),
    )

    m0005_v2_source_intake.up(connection)

    assert connection.execute(
        "SELECT artifact_id,sha256 FROM v2_source_artifacts"
    ).fetchone() == ("artifact-budget", "a" * 64)
    connection.close()
