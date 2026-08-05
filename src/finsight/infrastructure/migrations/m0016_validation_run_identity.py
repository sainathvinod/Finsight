"""Allocate a stable Validation Run identity before deterministic execution."""
from __future__ import annotations

import sqlite3

from finsight.infrastructure.migrations.m0008_review_disposal import (
    _guard_delete,
    ensure_disposal_guard_function,
)


VERSION = 16
NAME = "validation_run_identity"


def _append_only(conn: sqlite3.Connection, table: str) -> None:
    conn.execute(
        f"CREATE TRIGGER IF NOT EXISTS trg_{table}_no_update "
        f"BEFORE UPDATE ON {table} BEGIN "
        f"SELECT RAISE(ABORT,'{table} is append-only'); END"
    )


def up(conn: sqlite3.Connection) -> None:
    # Confirmations created by migration 15 pre-date stable pre-execution Run
    # identity. Preserve them, binding a completed Run where one exists and an
    # immutable legacy attempt identity otherwise.
    conn.execute(
        "DROP TRIGGER IF EXISTS "
        "trg_v2_validation_rule_set_confirmations_no_update"
    )
    columns = {
        row[1]
        for row in conn.execute(
            "PRAGMA table_info(v2_validation_rule_set_confirmations)"
        )
    }
    if "run_id" not in columns:
        conn.execute(
            "ALTER TABLE v2_validation_rule_set_confirmations "
            "ADD COLUMN run_id TEXT"
        )
    conn.execute(
        "UPDATE v2_validation_rule_set_confirmations SET run_id=COALESCE("
        "(SELECT link.run_id FROM v2_validation_confirmation_run_links link "
        "WHERE link.confirmation_id="
        "v2_validation_rule_set_confirmations.confirmation_id),"
        "'run_legacy_' || lower(hex(randomblob(16)))) "
        "WHERE run_id IS NULL OR trim(run_id)=''"
    )
    conn.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS "
        "idx_v2_validation_confirmations_run "
        "ON v2_validation_rule_set_confirmations(run_id)"
    )
    conn.execute(
        "CREATE TRIGGER IF NOT EXISTS "
        "trg_v2_validation_confirmations_run_required "
        "BEFORE INSERT ON v2_validation_rule_set_confirmations "
        "WHEN NEW.run_id IS NULL OR trim(NEW.run_id)='' BEGIN "
        "SELECT RAISE(ABORT,'validation confirmation requires a Run ID'); END"
    )
    _append_only(conn, "v2_validation_rule_set_confirmations")

    # Migration 15 referenced only already-completed runs, which forced
    # STARTED/FAILED events to have no Run ID. Rebuild this new ledger so every
    # event carries the identity allocated at confirmation while immutable
    # completed financial results stay in their existing tables.
    conn.execute(
        "DROP TRIGGER IF EXISTS trg_v2_validation_attempt_events_no_update"
    )
    conn.execute(
        "DROP TRIGGER IF EXISTS trg_v2_validation_attempt_events_no_delete"
    )
    conn.execute(
        "ALTER TABLE v2_validation_attempt_events "
        "RENAME TO v2_validation_attempt_events_legacy"
    )
    conn.execute(
        "CREATE TABLE v2_validation_attempt_events("
        "event_id TEXT PRIMARY KEY,"
        "confirmation_id TEXT NOT NULL REFERENCES "
        "v2_validation_rule_set_confirmations(confirmation_id),"
        "ordinal INTEGER NOT NULL CHECK(ordinal>0),"
        "event_type TEXT NOT NULL CHECK(event_type IN "
        "('CONFIRMED','STARTED','COMPLETED','FAILED')),"
        "run_id TEXT NOT NULL,"
        "actor_id TEXT NOT NULL,occurred_at TEXT NOT NULL,reason TEXT NOT NULL,"
        "payload_json TEXT NOT NULL,event_hash TEXT NOT NULL UNIQUE,"
        "UNIQUE(confirmation_id,ordinal))"
    )
    conn.execute(
        "INSERT INTO v2_validation_attempt_events("
        "event_id,confirmation_id,ordinal,event_type,run_id,actor_id,"
        "occurred_at,reason,payload_json,event_hash) "
        "SELECT event.event_id,event.confirmation_id,event.ordinal,"
        "event.event_type,confirmation.run_id,event.actor_id,event.occurred_at,"
        "event.reason,event.payload_json,event.event_hash "
        "FROM v2_validation_attempt_events_legacy event "
        "JOIN v2_validation_rule_set_confirmations confirmation "
        "ON confirmation.confirmation_id=event.confirmation_id"
    )
    conn.execute("DROP TABLE v2_validation_attempt_events_legacy")
    conn.execute(
        "CREATE TRIGGER IF NOT EXISTS trg_v2_validation_attempt_run_matches "
        "BEFORE INSERT ON v2_validation_attempt_events "
        "WHEN NEW.run_id != (SELECT run_id FROM "
        "v2_validation_rule_set_confirmations "
        "WHERE confirmation_id=NEW.confirmation_id) BEGIN "
        "SELECT RAISE(ABORT,'validation event Run ID does not match confirmation'); END"
    )
    _append_only(conn, "v2_validation_attempt_events")
    ensure_disposal_guard_function(conn)
    _guard_delete(
        conn,
        trigger="trg_v2_validation_attempt_events_no_delete",
        table="v2_validation_attempt_events",
        key_expression="OLD.event_id",
        error="v2_validation_attempt_events is append-only",
    )
