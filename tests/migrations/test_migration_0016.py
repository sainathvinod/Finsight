from __future__ import annotations

import sqlite3

import pytest

from finsight.infrastructure.migrations.m0016_validation_run_identity import up
from finsight.infrastructure.migrations.runner import MIGRATIONS, run_migrations


def test_migration_0016_requires_stable_matching_run_identity():
    connection = sqlite3.connect(":memory:")
    connection.execute("PRAGMA foreign_keys=ON")
    applied = run_migrations(connection)

    assert applied[-1] == 16
    columns = {
        row[1]
        for row in connection.execute(
            "PRAGMA table_info(v2_validation_rule_set_confirmations)"
        )
    }
    assert "run_id" in columns
    event_run = next(
        row
        for row in connection.execute(
            "PRAGMA table_info(v2_validation_attempt_events)"
        )
        if row[1] == "run_id"
    )
    assert event_run[3] == 1


def test_migration_0016_backfills_preexisting_attempt_events():
    connection = sqlite3.connect(":memory:")
    run_migrations(connection, migrations=MIGRATIONS[:15])
    _seed_confirmation(connection)

    up(connection)

    confirmation_run = connection.execute(
        "SELECT run_id FROM v2_validation_rule_set_confirmations "
        "WHERE confirmation_id='confirm-1'"
    ).fetchone()[0]
    event_run = connection.execute(
        "SELECT run_id FROM v2_validation_attempt_events "
        "WHERE confirmation_id='confirm-1'"
    ).fetchone()[0]
    assert confirmation_run.startswith("run_legacy_")
    assert event_run == confirmation_run
    with pytest.raises(sqlite3.IntegrityError, match="does not match"):
        connection.execute(
            "INSERT INTO v2_validation_attempt_events("
            "event_id,confirmation_id,ordinal,event_type,run_id,actor_id,"
            "occurred_at,reason,payload_json,event_hash) "
            "VALUES('event-2','confirm-1',2,'STARTED','wrong-run','actor',"
            "'2026-07-31T12:01:00Z','START','{}','hash-2')"
        )


def _seed_confirmation(connection: sqlite3.Connection) -> None:
    # Parent identifiers may be synthetic here because this test exercises
    # only the shape-preserving upgrade of the two migration-15 ledgers.
    connection.execute(
        "INSERT INTO v2_validation_rule_set_confirmations("
        "confirmation_id,review_id,rule_set_id,rule_set_version,"
        "dataset_fingerprint,source_generation_id,source_data_version,"
        "prior_run_id,rules_json,excluded_drafts_json,changes_json,actor_id,"
        "confirmed_at,confirmation_hash) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (
            "confirm-1",
            "review-1",
            "ruleset-1",
            "1",
            "dataset-1",
            "generation-1",
            "generation-1:dataset-1",
            None,
            "[]",
            "[]",
            "[]",
            "actor",
            "2026-07-31T12:00:00Z",
            "confirm-hash-1",
        ),
    )
    connection.execute(
        "INSERT INTO v2_validation_attempt_events("
        "event_id,confirmation_id,ordinal,event_type,run_id,actor_id,"
        "occurred_at,reason,payload_json,event_hash) "
        "VALUES('event-1','confirm-1',1,'CONFIRMED',NULL,'actor',"
        "'2026-07-31T12:00:00Z','CONFIRMED','{}','hash-1')"
    )
