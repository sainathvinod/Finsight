"""Governed whole-review disposal guard and content-free tombstones.

The existing append-only triggers remain authoritative for ordinary writes.
This migration narrows their delete branch so a repository-held, in-process
disposal capability may remove only the exact rows pre-authorized for one
review.  Every migrated connection receives a fail-closed
``finsight_disposal_allows`` fallback.  The governed disposal adapter replaces
that fallback with its bounded row-level capability for the duration of a
confirmed disposal.
"""
from __future__ import annotations

import sqlite3


VERSION = 8
NAME = "review_disposal"


def ensure_disposal_guard_function(conn: sqlite3.Connection) -> None:
    """Install the fail-closed guard without replacing an active callback.

    SQLite application-defined functions are connection-local. Migration
    triggers therefore need the fallback registered both when migration 0008
    is first applied and whenever an already-migrated database is reopened.
    """

    # SQLCipher exposes its own DB-API exception classes rather than
    # subclassing ``sqlite3.OperationalError``.
    try:
        conn.execute(
            "SELECT finsight_disposal_allows(?, ?)",
            ("__finsight_guard_probe__", ""),
        ).fetchone()
    except Exception as exc:
        # Match only the precise missing-function failure so every other
        # database error still propagates.
        if "no such function" not in str(exc).lower():
            raise
        conn.create_function(
            "finsight_disposal_allows",
            2,
            lambda _table, _key: 0,
            deterministic=True,
        )


def _guard_delete(
    conn: sqlite3.Connection,
    *,
    trigger: str,
    table: str,
    key_expression: str,
    error: str = "append_only",
) -> None:
    conn.execute(f"DROP TRIGGER IF EXISTS {trigger}")
    conn.execute(
        f"CREATE TRIGGER {trigger} BEFORE DELETE ON {table} "
        f"FOR EACH ROW WHEN COALESCE("
        f"finsight_disposal_allows('{table}', {key_expression}),0) <> 1 "
        f"BEGIN SELECT RAISE(ABORT, '{error}'); END"
    )


def up(conn: sqlite3.Connection) -> None:
    ensure_disposal_guard_function(conn)
    conn.execute(
        "CREATE TABLE IF NOT EXISTS v2_review_disposal_tombstones("
        "tombstone_id TEXT PRIMARY KEY,"
        "operation_id TEXT NOT NULL UNIQUE,"
        "scope_token TEXT NOT NULL UNIQUE CHECK(length(scope_token)=64),"
        "audit_stream_token TEXT NOT NULL UNIQUE CHECK(length(audit_stream_token)=64),"
        "confirmation_fingerprint TEXT NOT NULL CHECK(length(confirmation_fingerprint)=64),"
        "inventory_fingerprint TEXT NOT NULL CHECK(length(inventory_fingerprint)=64),"
        "deleted_inventory_json TEXT NOT NULL,"
        "retained_shared_json TEXT NOT NULL,"
        "actor_id TEXT NOT NULL,"
        "disposed_at TEXT NOT NULL,"
        "reason_code TEXT NOT NULL)"
    )
    conn.execute(
        "CREATE TRIGGER IF NOT EXISTS v2_review_disposal_tombstones_no_update "
        "BEFORE UPDATE ON v2_review_disposal_tombstones "
        "BEGIN SELECT RAISE(ABORT,'append_only'); END"
    )
    conn.execute(
        "CREATE TRIGGER IF NOT EXISTS v2_review_disposal_tombstones_no_delete "
        "BEFORE DELETE ON v2_review_disposal_tombstones "
        "BEGIN SELECT RAISE(ABORT,'append_only'); END"
    )

    guarded = (
        # Workflow 1 review identity and events.
        (
            "v2_review_cycles_no_delete",
            "v2_review_cycles",
            "OLD.review_id",
            "append_only",
        ),
        (
            "v2_working_candidates_no_delete",
            "v2_working_candidates",
            "OLD.candidate_id",
            "append_only",
        ),
        (
            "v2_review_disposition_events_no_delete",
            "v2_review_disposition_events",
            "OLD.event_id",
            "append_only",
        ),
        (
            "v2_review_status_events_no_delete",
            "v2_review_status_events",
            "OLD.event_id",
            "append_only",
        ),
        (
            "v2_review_create_requests_no_delete",
            "v2_review_create_requests",
            "OLD.idempotency_key",
            "append_only",
        ),
        (
            "v2_authorization_decision_events_no_delete",
            "v2_authorization_decision_events",
            "OLD.event_id",
            "append_only",
        ),
        (
            "v2_audit_events_no_delete",
            "v2_audit_events",
            "OLD.event_id",
            "append_only",
        ),
        (
            "v2_audit_event_scopes_no_delete",
            "v2_audit_event_scopes",
            "OLD.event_id",
            "append_only",
        ),
        (
            "v2_generation_analytical_state_events_no_delete",
            "v2_generation_analytical_state_events",
            "OLD.event_id",
            "append_only",
        ),
        # Workflow 2 source intake.
        (
            "v2_source_artifacts_no_delete",
            "v2_source_artifacts",
            "OLD.artifact_id",
            "append_only",
        ),
        (
            "v2_source_binding_versions_no_delete",
            "v2_source_binding_versions",
            "OLD.binding_id",
            "append_only",
        ),
        (
            "v2_candidate_source_heads_no_delete",
            "v2_candidate_source_heads",
            "OLD.candidate_id",
            "head_delete_forbidden",
        ),
        (
            "v2_metadata_evidence_records_no_delete",
            "v2_metadata_evidence_records",
            "OLD.evidence_id",
            "append_only",
        ),
        (
            "v2_source_intake_summaries_no_delete",
            "v2_source_intake_summaries",
            "OLD.summary_id",
            "append_only",
        ),
        (
            "v2_source_intake_idempotency_no_delete",
            "v2_source_intake_idempotency",
            "OLD.review_id",
            "append_only",
        ),
        # Deterministic review/validation ledger.
        (
            "trg_v2_review_correction_events_no_delete",
            "v2_review_correction_events",
            "OLD.correction_id",
            "append_only",
        ),
        (
            "trg_v2_review_confirmations_no_delete",
            "v2_review_confirmations",
            "OLD.confirmation_id",
            "append_only",
        ),
        (
            "trg_v2_generation_review_bases_no_delete",
            "v2_generation_review_bases",
            "OLD.generation_id",
            "append_only",
        ),
        (
            "trg_v2_validation_runs_no_delete",
            "v2_validation_runs",
            "OLD.run_id",
            "append_only",
        ),
        (
            "trg_v2_rule_executions_no_delete",
            "v2_rule_executions",
            "OLD.execution_id",
            "append_only",
        ),
        (
            "trg_v2_rule_scope_results_no_delete",
            "v2_rule_scope_results",
            "OLD.result_id",
            "append_only",
        ),
        (
            "trg_v2_validation_findings_no_delete",
            "v2_validation_findings",
            "OLD.finding_id",
            "append_only",
        ),
        (
            "trg_v2_review_completions_no_delete",
            "v2_review_completions",
            "OLD.completion_id",
            "append_only",
        ),
        # Configurable-rule snapshots and retained reanalysis added by V2-0007.
        (
            "trg_v2_rule_test_runs_no_delete",
            "v2_rule_test_runs",
            "OLD.test_id",
            "v2_rule_test_runs is append-only",
        ),
        (
            "trg_v2_rule_set_versions_no_delete",
            "v2_rule_set_versions",
            "OLD.rule_set_id",
            "v2_rule_set_versions is append-only",
        ),
        (
            "trg_v2_rule_set_members_no_delete",
            "v2_rule_set_members",
            "OLD.rule_set_id",
            "v2_rule_set_members is append-only",
        ),
        (
            "trg_v2_validation_run_rule_sets_no_delete",
            "v2_validation_run_rule_sets",
            "OLD.run_id",
            "v2_validation_run_rule_sets is append-only",
        ),
        (
            "trg_v2_optional_rule_executions_no_delete",
            "v2_optional_rule_executions",
            "OLD.execution_id",
            "v2_optional_rule_executions is append-only",
        ),
        (
            "trg_v2_optional_rule_scope_results_no_delete",
            "v2_optional_rule_scope_results",
            "OLD.result_id",
            "v2_optional_rule_scope_results is append-only",
        ),
        (
            "trg_v2_optional_validation_findings_no_delete",
            "v2_optional_validation_findings",
            "OLD.finding_id",
            "v2_optional_validation_findings is append-only",
        ),
        (
            "trg_v2_reanalysis_generation_bases_no_delete",
            "v2_reanalysis_generation_bases",
            "OLD.generation_id",
            "v2_reanalysis_generation_bases is append-only",
        ),
        (
            "trg_v2_review_completion_events_no_delete",
            "v2_review_completion_events",
            "OLD.completion_id",
            "v2_review_completion_events is append-only",
        ),
        # Legacy lineage records that are also immutable.
        (
            "trg_supersession_no_delete",
            "generation_supersessions",
            "OLD.prior_generation_id",
            "generation_supersessions is append-only",
        ),
        (
            "trg_export_no_delete",
            "export_artifacts",
            "OLD.export_id",
            "export_artifacts is append-only",
        ),
    )
    for trigger, table, key_expression, error in guarded:
        _guard_delete(
            conn,
            trigger=trigger,
            table=table,
            key_expression=key_expression,
            error=error,
        )
