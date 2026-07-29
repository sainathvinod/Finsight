"""Deterministic finding explanations, review status history, and summaries."""
from __future__ import annotations

import sqlite3

from finsight.infrastructure.migrations.m0008_review_disposal import (
    _guard_delete,
    ensure_disposal_guard_function,
)

VERSION = 13
NAME = "finding_explanations_and_review_status"


_APPEND_ONLY = (
    "v2_finding_explanation_projections",
    "v2_finding_review_status_events",
    "v2_leadership_summary_projections",
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
        "CREATE TABLE IF NOT EXISTS v2_finding_explanation_projections("
        "finding_id TEXT PRIMARY KEY,run_id TEXT NOT NULL "
        "REFERENCES v2_validation_runs(run_id),projection_json TEXT NOT NULL,"
        "content_hash TEXT NOT NULL UNIQUE,created_at TEXT NOT NULL)"
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_v2_finding_explanations_run "
        "ON v2_finding_explanation_projections(run_id,finding_id)"
    )
    conn.execute(
        "CREATE TRIGGER IF NOT EXISTS "
        "trg_v2_finding_explanation_exact_sealed_finding "
        "BEFORE INSERT ON v2_finding_explanation_projections "
        "FOR EACH ROW WHEN NOT EXISTS("
        "SELECT 1 FROM v2_validation_findings f "
        "WHERE f.finding_id=NEW.finding_id AND f.run_id=NEW.run_id "
        "UNION ALL SELECT 1 FROM v2_optional_validation_findings f "
        "WHERE f.finding_id=NEW.finding_id AND f.run_id=NEW.run_id"
        ") BEGIN SELECT RAISE(ABORT,"
        "'finding explanation must bind one sealed finding'); END"
    )
    conn.execute(
        "CREATE TABLE IF NOT EXISTS v2_finding_review_status_events("
        "event_id TEXT PRIMARY KEY,review_id TEXT NOT NULL "
        "REFERENCES v2_review_cycles(review_id),run_id TEXT NOT NULL "
        "REFERENCES v2_validation_runs(run_id),finding_id TEXT NOT NULL "
        "REFERENCES v2_finding_explanation_projections(finding_id),"
        "ordinal INTEGER NOT NULL CHECK(ordinal>0),previous_status TEXT,"
        "status TEXT NOT NULL CHECK(status IN "
        "('New','Acknowledged','In Review','Resolved','Dismissed')),"
        "event_kind TEXT NOT NULL CHECK(event_kind IN "
        "('INITIAL_ASSIGNMENT','REVIEW_UPDATE')),"
        "review_required INTEGER NOT NULL CHECK(review_required IN (0,1)),"
        "actor_id TEXT NOT NULL,occurred_at TEXT NOT NULL,reason TEXT NOT NULL,"
        "event_hash TEXT NOT NULL UNIQUE,UNIQUE(finding_id,ordinal))"
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_v2_finding_status_review "
        "ON v2_finding_review_status_events("
        "review_id,run_id,status,finding_id,ordinal)"
    )
    conn.execute(
        "CREATE TRIGGER IF NOT EXISTS "
        "trg_v2_finding_status_exact_review_run "
        "BEFORE INSERT ON v2_finding_review_status_events "
        "FOR EACH ROW WHEN NOT EXISTS("
        "SELECT 1 FROM v2_finding_explanation_projections e "
        "JOIN v2_validation_runs r ON r.run_id=e.run_id "
        "WHERE e.finding_id=NEW.finding_id AND e.run_id=NEW.run_id "
        "AND r.review_id=NEW.review_id"
        ") BEGIN SELECT RAISE(ABORT,"
        "'finding status must bind the exact review and run'); END"
    )
    conn.execute(
        "CREATE TRIGGER IF NOT EXISTS trg_v2_finding_status_initial_state "
        "BEFORE INSERT ON v2_finding_review_status_events "
        "FOR EACH ROW WHEN NEW.ordinal=1 AND ("
        "NEW.previous_status IS NOT NULL OR NEW.status<>'New' "
        "OR NEW.event_kind<>'INITIAL_ASSIGNMENT'"
        ") BEGIN SELECT RAISE(ABORT,"
        "'finding status history must begin at New'); END"
    )
    conn.execute(
        "CREATE TRIGGER IF NOT EXISTS trg_v2_finding_status_contiguous_history "
        "BEFORE INSERT ON v2_finding_review_status_events "
        "FOR EACH ROW WHEN NEW.ordinal>1 AND ("
        "NEW.event_kind<>'REVIEW_UPDATE' OR NEW.ordinal<>COALESCE(("
        "SELECT MAX(prior.ordinal)+1 "
        "FROM v2_finding_review_status_events prior "
        "WHERE prior.finding_id=NEW.finding_id),1) "
        "OR NEW.previous_status IS NULL OR NEW.previous_status<>(SELECT prior.status "
        "FROM v2_finding_review_status_events prior "
        "WHERE prior.finding_id=NEW.finding_id "
        "ORDER BY prior.ordinal DESC LIMIT 1)"
        ") BEGIN SELECT RAISE(ABORT,"
        "'finding status history must be contiguous'); END"
    )
    conn.execute(
        "CREATE TABLE IF NOT EXISTS v2_leadership_summary_projections("
        "run_id TEXT PRIMARY KEY REFERENCES v2_validation_runs(run_id),"
        "projection_json TEXT NOT NULL,content_hash TEXT NOT NULL UNIQUE,"
        "created_at TEXT NOT NULL)"
    )
    for table in _APPEND_ONLY:
        _append_only(conn, table)
    # Whole-review disposal is the sole governed exception to append-only
    # retention.  It supplies an exact row-level capability for these keys.
    ensure_disposal_guard_function(conn)
    _guard_delete(
        conn,
        trigger="trg_v2_finding_explanation_projections_no_delete",
        table="v2_finding_explanation_projections",
        key_expression="OLD.finding_id",
        error="v2_finding_explanation_projections is append-only",
    )
    _guard_delete(
        conn,
        trigger="trg_v2_finding_review_status_events_no_delete",
        table="v2_finding_review_status_events",
        key_expression="OLD.event_id",
        error="v2_finding_review_status_events is append-only",
    )
    _guard_delete(
        conn,
        trigger="trg_v2_leadership_summary_projections_no_delete",
        table="v2_leadership_summary_projections",
        key_expression="OLD.run_id",
        error="v2_leadership_summary_projections is append-only",
    )
