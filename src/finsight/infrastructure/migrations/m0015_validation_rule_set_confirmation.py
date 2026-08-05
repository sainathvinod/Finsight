"""Append-only rule-set proposal, confirmation, and validation-attempt evidence."""
from __future__ import annotations

import sqlite3

from finsight.infrastructure.migrations.m0008_review_disposal import (
    _guard_delete,
    ensure_disposal_guard_function,
)


VERSION = 15
NAME = "validation_rule_set_confirmation"


_APPEND_ONLY = (
    "v2_rule_proposal_draft_events",
    "v2_validation_rule_set_confirmations",
    "v2_validation_attempt_events",
    "v2_validation_confirmation_run_links",
)


def _append_only(conn: sqlite3.Connection, table: str) -> None:
    conn.execute(
        f"CREATE TRIGGER IF NOT EXISTS trg_{table}_no_update "
        f"BEFORE UPDATE ON {table} BEGIN "
        f"SELECT RAISE(ABORT,'{table} is append-only'); END"
    )
    conn.execute(
        f"CREATE TRIGGER IF NOT EXISTS trg_{table}_no_delete "
        f"BEFORE DELETE ON {table} BEGIN "
        f"SELECT RAISE(ABORT,'{table} is append-only'); END"
    )


def up(conn: sqlite3.Connection) -> None:
    conn.execute(
        "CREATE TABLE IF NOT EXISTS v2_rule_proposal_draft_events("
        "event_id TEXT PRIMARY KEY,"
        "review_id TEXT NOT NULL REFERENCES v2_review_cycles(review_id),"
        "rule_id TEXT NOT NULL,rule_version TEXT NOT NULL,"
        "action TEXT NOT NULL CHECK(action IN ('EXCLUDED','RESTORED')),"
        "actor_id TEXT NOT NULL,occurred_at TEXT NOT NULL,reason TEXT NOT NULL,"
        "event_hash TEXT NOT NULL UNIQUE,"
        "FOREIGN KEY(rule_id,rule_version) REFERENCES "
        "v2_rule_definition_versions(rule_id,version))"
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_v2_rule_proposal_draft_events "
        "ON v2_rule_proposal_draft_events("
        "review_id,rule_id,rule_version,occurred_at,event_id)"
    )
    conn.execute(
        "CREATE TABLE IF NOT EXISTS v2_validation_rule_set_confirmations("
        "confirmation_id TEXT PRIMARY KEY,"
        "review_id TEXT NOT NULL REFERENCES v2_review_cycles(review_id),"
        "rule_set_id TEXT NOT NULL REFERENCES v2_rule_set_versions(rule_set_id),"
        "rule_set_version TEXT NOT NULL,"
        "dataset_fingerprint TEXT NOT NULL,"
        "source_generation_id TEXT NOT NULL REFERENCES review_generations(generation_id),"
        "source_data_version TEXT NOT NULL,"
        "prior_run_id TEXT REFERENCES v2_validation_runs(run_id),"
        "rules_json TEXT NOT NULL,excluded_drafts_json TEXT NOT NULL,"
        "changes_json TEXT NOT NULL,actor_id TEXT NOT NULL,confirmed_at TEXT NOT NULL,"
        "confirmation_hash TEXT NOT NULL UNIQUE)"
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_v2_validation_confirmations_review "
        "ON v2_validation_rule_set_confirmations(review_id,confirmed_at,confirmation_id)"
    )
    conn.execute(
        "CREATE TABLE IF NOT EXISTS v2_validation_attempt_events("
        "event_id TEXT PRIMARY KEY,"
        "confirmation_id TEXT NOT NULL REFERENCES "
        "v2_validation_rule_set_confirmations(confirmation_id),"
        "ordinal INTEGER NOT NULL CHECK(ordinal>0),"
        "event_type TEXT NOT NULL CHECK(event_type IN "
        "('CONFIRMED','STARTED','COMPLETED','FAILED')),"
        "run_id TEXT REFERENCES v2_validation_runs(run_id),"
        "actor_id TEXT NOT NULL,occurred_at TEXT NOT NULL,reason TEXT NOT NULL,"
        "payload_json TEXT NOT NULL,event_hash TEXT NOT NULL UNIQUE,"
        "UNIQUE(confirmation_id,ordinal))"
    )
    conn.execute(
        "CREATE TABLE IF NOT EXISTS v2_validation_confirmation_run_links("
        "confirmation_id TEXT PRIMARY KEY REFERENCES "
        "v2_validation_rule_set_confirmations(confirmation_id),"
        "run_id TEXT NOT NULL UNIQUE REFERENCES v2_validation_runs(run_id),"
        "prior_run_id TEXT REFERENCES v2_validation_runs(run_id),"
        "linked_at TEXT NOT NULL,link_hash TEXT NOT NULL UNIQUE)"
    )
    for table in _APPEND_ONLY:
        _append_only(conn, table)
    # The separately confirmed whole-review disposal is the only exception to
    # append-only retention. Its repository supplies an exact row capability;
    # every ordinary deletion remains fail-closed.
    ensure_disposal_guard_function(conn)
    for table, key_expression in (
        ("v2_rule_proposal_draft_events", "OLD.event_id"),
        ("v2_validation_rule_set_confirmations", "OLD.confirmation_id"),
        ("v2_validation_attempt_events", "OLD.event_id"),
        ("v2_validation_confirmation_run_links", "OLD.confirmation_id"),
    ):
        _guard_delete(
            conn,
            trigger=f"trg_{table}_no_delete",
            table=table,
            key_expression=key_expression,
            error=f"{table} is append-only",
        )
