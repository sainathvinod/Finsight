"""Migration 0004 verification for the Workflow 1 Review Management schema.

Traces: FR-123/FR-124/FR-195/FR-197, NFR-082/NFR-090, ADR-V2-003.
"""
from __future__ import annotations

import sqlite3

from finsight.infrastructure.migrations import (
    m0001_baseline,
    m0002_ai_platform,
    m0003_review_lifecycle,
    m0004_v2_review_management,
)


V2_TABLES = {
    "v2_store_security_profiles",
    "v2_store_security_profile_head",
    "v2_actor_snapshots",
    "v2_review_cycles",
    "v2_working_candidates",
    "v2_review_cycle_pointers",
    "v2_review_disposition_events",
    "v2_review_status_events",
    "v2_review_create_requests",
    "v2_authorization_manifest_state",
    "v2_authorization_decision_events",
    "v2_audit_streams",
    "v2_audit_events",
    "v2_audit_event_scopes",
    "v2_generation_analytical_state_events",
}


def _connection():
    connection = sqlite3.connect(":memory:")
    connection.execute("PRAGMA foreign_keys=ON")
    return connection


def _through_v3(connection):
    m0001_baseline.up(connection)
    m0002_ai_platform.up(connection)
    m0003_review_lifecycle.up(connection)


def _table_names(connection):
    return {
        row[0]
        for row in connection.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        )
    }


def test_fresh_migration_creates_complete_workflow_1_schema_and_append_guards():
    connection = _connection()
    _through_v3(connection)
    m0004_v2_review_management.up(connection)

    assert V2_TABLES.issubset(_table_names(connection))
    triggers = {
        row[0]
        for row in connection.execute(
            "SELECT name FROM sqlite_master WHERE type='trigger'"
        )
    }
    for table in (
        "v2_store_security_profiles",
        "v2_actor_snapshots",
        "v2_review_disposition_events",
        "v2_review_status_events",
        "v2_authorization_decision_events",
        "v2_audit_events",
        "v2_audit_event_scopes",
        "v2_generation_analytical_state_events",
    ):
        assert table + "_no_update" in triggers
        assert table + "_no_delete" in triggers
    connection.close()


def test_legacy_cycles_are_adopted_with_honest_status_and_origin():
    connection = _connection()
    m0001_baseline.up(connection)
    m0002_ai_platform.up(connection)
    connection.execute(
        "INSERT INTO cycles(cycle_id,month,year,state) VALUES(?,?,?,?)",
        ("legacy-created", "May", "2026", "Created"),
    )
    connection.execute(
        "INSERT INTO audit(cycle_id,action,actor,ts,detail) VALUES(?,?,?,?,?)",
        (
            "legacy-created",
            "setup",
            "legacy-reviewer",
            "2026-05-01T00:00:00Z",
            "{}",
        ),
    )
    connection.execute(
        "INSERT INTO cycles(cycle_id,month,year,state) VALUES(?,?,?,?)",
        ("legacy-analyzed", "Jun", "2026", "Analyzed"),
    )
    connection.execute(
        "INSERT INTO rule_runs(run_id,cycle_id,ruleset_version,config_version,"
        "input_fingerprint,finding_count) VALUES(?,?,?,?,?,?)",
        ("run-legacy", "legacy-analyzed", "R1", "C1", "fingerprint-legacy", 0),
    )
    m0003_review_lifecycle.up(connection)
    m0004_v2_review_management.up(connection)

    created = connection.execute(
        "SELECT selected_month,selected_year,origin FROM v2_review_cycles "
        "WHERE review_id='legacy-created'"
    ).fetchone()
    assert created == (5, 2026, "LEGACY_SNAPSHOT")
    created_status = connection.execute(
        "SELECT owner_kind,status,origin FROM v2_review_status_events "
        "WHERE review_id='legacy-created'"
    ).fetchone()
    assert created_status == ("WorkingCandidate", "Draft", "LEGACY_SNAPSHOT")

    analyzed_status = connection.execute(
        "SELECT owner_kind,status,origin FROM v2_review_status_events "
        "WHERE review_id='legacy-analyzed'"
    ).fetchone()
    assert analyzed_status == (
        "ReviewGeneration",
        "Validation Complete",
        "LEGACY_SNAPSHOT",
    )
    generation = connection.execute(
        "SELECT generation_id FROM review_generations "
        "WHERE cycle_id='legacy-analyzed'"
    ).fetchone()[0]
    pointers = connection.execute(
        "SELECT working_generation_id,published_generation_id "
        "FROM v2_review_cycle_pointers WHERE review_id='legacy-analyzed'"
    ).fetchone()
    assert pointers == (generation, generation)
    connection.close()


def test_migration_0004_is_idempotent_for_schema_and_legacy_backfill():
    connection = _connection()
    m0001_baseline.up(connection)
    m0002_ai_platform.up(connection)
    connection.execute(
        "INSERT INTO cycles(cycle_id,month,year,state) VALUES('legacy','May','2026','Created')"
    )
    m0003_review_lifecycle.up(connection)
    m0004_v2_review_management.up(connection)
    before = {
        table: connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        for table in V2_TABLES
    }

    m0004_v2_review_management.up(connection)
    after = {
        table: connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        for table in V2_TABLES
    }
    assert after == before
    connection.close()
