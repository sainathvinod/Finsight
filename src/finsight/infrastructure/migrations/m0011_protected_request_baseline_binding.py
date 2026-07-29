"""Bind every protected-rule request to the exact baseline it qualified."""
from __future__ import annotations

import sqlite3


VERSION = 11
NAME = "protected_request_baseline_binding"


def _has_column(
    conn: sqlite3.Connection, table: str, column: str
) -> bool:
    return any(
        str(row[1]) == column
        for row in conn.execute(f"PRAGMA table_info({table})")
    )


def up(conn: sqlite3.Connection) -> None:
    """Add an immutable request-time baseline and enforce it at activation."""

    if not _has_column(
        conn,
        "v2_protected_change_requests",
        "requested_baseline_id",
    ):
        conn.execute(
            "ALTER TABLE v2_protected_change_requests "
            "ADD COLUMN requested_baseline_id TEXT "
            "REFERENCES v2_core_rule_set_versions(rule_set_id)"
        )

    # Migration 0009 made the request ledger append-only. Temporarily remove
    # only its update guard while historical request-time baselines are
    # reconstructed, then restore the guard inside this migration transaction.
    conn.execute(
        "DROP TRIGGER IF EXISTS "
        "trg_v2_protected_change_requests_no_update"
    )
    conn.execute(
        "UPDATE v2_protected_change_requests AS r "
        "SET requested_baseline_id=COALESCE("
        "(SELECT a.prior_baseline_id "
        " FROM v2_protected_change_activations a "
        " WHERE a.request_id=r.request_id),"
        "(SELECT a.resulting_baseline_id "
        " FROM v2_protected_change_activations a "
        " WHERE a.activated_at<=r.requested_at "
        " ORDER BY a.activated_at DESC,a.rowid DESC LIMIT 1),"
        "'FINSIGHT-CORE-2.0') "
        "WHERE requested_baseline_id IS NULL"
    )
    conn.execute(
        "CREATE TRIGGER IF NOT EXISTS "
        "trg_v2_protected_change_requests_no_update "
        "BEFORE UPDATE ON v2_protected_change_requests BEGIN "
        "SELECT RAISE(ABORT,'v2_protected_change_requests is append-only'); END"
    )
    conn.execute(
        "CREATE TRIGGER IF NOT EXISTS "
        "trg_v2_protected_request_requires_baseline "
        "BEFORE INSERT ON v2_protected_change_requests "
        "FOR EACH ROW WHEN NEW.requested_baseline_id IS NULL OR NOT EXISTS("
        "SELECT 1 FROM v2_core_rule_set_versions b "
        "WHERE b.rule_set_id=NEW.requested_baseline_id "
        "AND b.status='PROTECTED_BASELINE') "
        "BEGIN SELECT RAISE(ABORT,'protected request baseline is required'); END"
    )
    conn.execute(
        "CREATE TRIGGER IF NOT EXISTS "
        "trg_v2_protected_activation_requested_baseline "
        "BEFORE INSERT ON v2_protected_change_activations "
        "FOR EACH ROW WHEN NOT EXISTS("
        "SELECT 1 FROM v2_protected_change_requests r "
        "WHERE r.request_id=NEW.request_id "
        "AND r.requested_baseline_id=NEW.prior_baseline_id) "
        "BEGIN SELECT RAISE(ABORT,'protected activation request baseline mismatch'); END"
    )
