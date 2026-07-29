from __future__ import annotations

import sqlite3

import pytest

from finsight.infrastructure.migrations import (
    m0001_baseline,
    m0002_ai_platform,
    m0003_review_lifecycle,
    m0004_v2_review_management,
    m0005_v2_source_intake,
    m0006_v2_integrated_review,
    m0007_configurable_rules_and_reanalysis,
    m0008_review_disposal,
)
from finsight.infrastructure.migrations.runner import run_migrations


def _connection():
    connection = sqlite3.connect(":memory:")
    connection.execute("PRAGMA foreign_keys=ON")
    for migration in (
        m0001_baseline,
        m0002_ai_platform,
        m0003_review_lifecycle,
        m0004_v2_review_management,
        m0005_v2_source_intake,
        m0006_v2_integrated_review,
        m0007_configurable_rules_and_reanalysis,
    ):
        migration.up(connection)
    return connection


def test_migration_0008_creates_content_free_immutable_tombstone():
    connection = _connection()
    m0008_review_disposal.up(connection)

    columns = {
        row[1]
        for row in connection.execute(
            "PRAGMA table_info(v2_review_disposal_tombstones)"
        )
    }
    assert "review_id" not in columns
    assert "reporting_period" not in columns
    assert "scope_token" in columns
    assert "deleted_inventory_json" in columns
    triggers = {
        row[0]
        for row in connection.execute(
            "SELECT name FROM sqlite_master WHERE type='trigger'"
        )
    }
    assert "v2_review_disposal_tombstones_no_update" in triggers
    assert "v2_review_disposal_tombstones_no_delete" in triggers
    assert m0008_review_disposal.VERSION == 8


def test_migration_0008_preserves_append_only_delete_default():
    connection = _connection()
    m0008_review_disposal.up(connection)
    connection.execute(
        "INSERT INTO cycles(cycle_id,month,year,state) VALUES("
        "'rev_guard','May','2026','Created')"
    )
    connection.execute(
        "INSERT INTO v2_review_cycles("
        "review_id,selected_month,selected_year,creation_actor_id,"
        "creation_actor_display,identity_source,created_at,origin"
        ") VALUES('rev_guard',5,2026,'actor','Actor','TEST',"
        "'2026-07-28T00:00:00Z','NATIVE')"
    )

    with pytest.raises(sqlite3.IntegrityError, match="append_only"):
        connection.execute(
            "DELETE FROM v2_review_cycles WHERE review_id='rev_guard'"
        )
    connection.rollback()


def test_reopened_database_restores_fail_closed_delete_guard(tmp_path):
    database = tmp_path / "reopened.db"
    connection = sqlite3.connect(database)
    run_migrations(connection)
    connection.execute(
        "INSERT INTO cycles(cycle_id,month,year,state) VALUES("
        "'rev_reopened','May','2026','Created')"
    )
    connection.execute(
        "INSERT INTO v2_review_cycles("
        "review_id,selected_month,selected_year,creation_actor_id,"
        "creation_actor_display,identity_source,created_at,origin"
        ") VALUES('rev_reopened',5,2026,'actor','Actor','TEST',"
        "'2026-07-28T00:00:00Z','NATIVE')"
    )
    connection.commit()
    connection.close()

    reopened = sqlite3.connect(database)
    assert run_migrations(reopened) == []
    with pytest.raises(sqlite3.IntegrityError, match="append_only"):
        reopened.execute(
            "DELETE FROM v2_review_cycles WHERE review_id='rev_reopened'"
        )
