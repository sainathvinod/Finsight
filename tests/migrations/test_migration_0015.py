from __future__ import annotations

import sqlite3

from finsight.infrastructure.migrations.runner import run_migrations


def test_migration_0015_creates_append_only_confirmation_ledgers():
    connection = sqlite3.connect(":memory:")
    connection.execute("PRAGMA foreign_keys=ON")
    applied = run_migrations(connection)

    assert 15 in applied
    tables = {
        row[0]
        for row in connection.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        )
    }
    expected = {
        "v2_rule_proposal_draft_events",
        "v2_validation_rule_set_confirmations",
        "v2_validation_attempt_events",
        "v2_validation_confirmation_run_links",
    }
    assert expected.issubset(tables)
    triggers = {
        row[0]
        for row in connection.execute(
            "SELECT name FROM sqlite_master WHERE type='trigger'"
        )
    }
    for table in expected:
        assert f"trg_{table}_no_update" in triggers
        assert f"trg_{table}_no_delete" in triggers


def test_migration_0015_is_idempotent():
    connection = sqlite3.connect(":memory:")
    connection.execute("PRAGMA foreign_keys=ON")
    run_migrations(connection)
    assert run_migrations(connection) == []
