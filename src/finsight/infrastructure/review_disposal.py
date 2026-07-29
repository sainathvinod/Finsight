"""Scoped SQLite implementation of governed whole-review disposal.

The caller owns the transaction.  This adapter never opens, changes, or
removes an uploaded workbook path.  It deletes only database rows belonging to
the requested review, retains shared source artifacts, and writes one
content-free tombstone with an exact table-by-table receipt.
"""
from __future__ import annotations

import json
import threading
from dataclasses import dataclass
from typing import Mapping

from finsight.application.review_disposal import (
    inventory_fingerprint,
    review_audit_stream_token,
    review_scope_token,
)


def _canonical(value: object) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    )


@dataclass(frozen=True)
class _ScopePlan:
    inventory: Mapping[str, int]
    retained_shared: Mapping[str, int]
    allowed_rows: Mapping[str, frozenset[str]]


class ScopedReviewDisposalSqlite:
    """Exact review closure and guarded deletion for one DAL connection."""

    _COUNT_QUERIES = {
        "ai_messages": (
            "SELECT COUNT(*) FROM ai_messages WHERE conversation_id IN "
            "(SELECT conversation_id FROM ai_conversations WHERE cycle_id=?)"
        ),
        "ai_conversations": "SELECT COUNT(*) FROM ai_conversations WHERE cycle_id=?",
        "ai_review_memory": "SELECT COUNT(*) FROM ai_review_memory WHERE cycle_id=?",
        "ai_interactions": "SELECT COUNT(*) FROM ai_interactions WHERE cycle_id=?",
        "v2_audit_event_scopes": (
            "SELECT COUNT(*) FROM v2_audit_event_scopes WHERE event_id IN ("
            "SELECT e.event_id FROM v2_audit_events e JOIN v2_audit_streams s "
            "ON s.stream_id=e.stream_id WHERE s.review_id=?)"
        ),
        "v2_audit_events": (
            "SELECT COUNT(*) FROM v2_audit_events WHERE stream_id IN "
            "(SELECT stream_id FROM v2_audit_streams WHERE review_id=?)"
        ),
        "v2_audit_streams": "SELECT COUNT(*) FROM v2_audit_streams WHERE review_id=?",
        "v2_finding_review_status_events": (
            "SELECT COUNT(*) FROM v2_finding_review_status_events "
            "WHERE review_id=?"
        ),
        "v2_finding_explanation_projections": (
            "SELECT COUNT(*) FROM v2_finding_explanation_projections "
            "WHERE run_id IN (SELECT run_id FROM v2_validation_runs "
            "WHERE review_id=?)"
        ),
        "v2_leadership_summary_projections": (
            "SELECT COUNT(*) FROM v2_leadership_summary_projections "
            "WHERE run_id IN (SELECT run_id FROM v2_validation_runs "
            "WHERE review_id=?)"
        ),
        "v2_review_completion_events": (
            "SELECT COUNT(*) FROM v2_review_completion_events WHERE review_id=?"
        ),
        "v2_optional_validation_findings": (
            "SELECT COUNT(*) FROM v2_optional_validation_findings WHERE run_id IN "
            "(SELECT run_id FROM v2_validation_runs WHERE review_id=?)"
        ),
        "v2_optional_rule_scope_results": (
            "SELECT COUNT(*) FROM v2_optional_rule_scope_results WHERE run_id IN "
            "(SELECT run_id FROM v2_validation_runs WHERE review_id=?)"
        ),
        "v2_optional_rule_executions": (
            "SELECT COUNT(*) FROM v2_optional_rule_executions WHERE run_id IN "
            "(SELECT run_id FROM v2_validation_runs WHERE review_id=?)"
        ),
        "v2_validation_run_rule_sets": (
            "SELECT COUNT(*) FROM v2_validation_run_rule_sets WHERE run_id IN "
            "(SELECT run_id FROM v2_validation_runs WHERE review_id=?)"
        ),
        "v2_reanalysis_generation_bases": (
            "SELECT COUNT(*) FROM v2_reanalysis_generation_bases WHERE review_id=?"
        ),
        "v2_rule_test_runs": (
            "SELECT COUNT(*) FROM v2_rule_test_runs WHERE review_id=?"
        ),
        "v2_rule_set_members": (
            "SELECT COUNT(*) FROM v2_rule_set_members WHERE rule_set_id IN "
            "(SELECT rule_set_id FROM v2_rule_set_versions WHERE review_id=?)"
        ),
        "v2_rule_set_versions": (
            "SELECT COUNT(*) FROM v2_rule_set_versions WHERE review_id=?"
        ),
        "v2_review_completions": "SELECT COUNT(*) FROM v2_review_completions WHERE review_id=?",
        "v2_validation_findings": (
            "SELECT COUNT(*) FROM v2_validation_findings WHERE run_id IN "
            "(SELECT run_id FROM v2_validation_runs WHERE review_id=?)"
        ),
        "v2_rule_scope_results": (
            "SELECT COUNT(*) FROM v2_rule_scope_results WHERE run_id IN "
            "(SELECT run_id FROM v2_validation_runs WHERE review_id=?)"
        ),
        "v2_rule_executions": (
            "SELECT COUNT(*) FROM v2_rule_executions WHERE run_id IN "
            "(SELECT run_id FROM v2_validation_runs WHERE review_id=?)"
        ),
        "v2_validation_runs": "SELECT COUNT(*) FROM v2_validation_runs WHERE review_id=?",
        "v2_generation_review_bases": (
            "SELECT COUNT(*) FROM v2_generation_review_bases WHERE review_id=?"
        ),
        "v2_review_confirmations": "SELECT COUNT(*) FROM v2_review_confirmations WHERE review_id=?",
        "v2_review_correction_events": (
            "SELECT COUNT(*) FROM v2_review_correction_events WHERE review_id=?"
        ),
        "v2_source_intake_idempotency": (
            "SELECT COUNT(*) FROM v2_source_intake_idempotency WHERE review_id=?"
        ),
        "v2_source_intake_summaries": (
            "SELECT COUNT(*) FROM v2_source_intake_summaries WHERE review_id=?"
        ),
        "v2_metadata_evidence_records": (
            "SELECT COUNT(*) FROM v2_metadata_evidence_records WHERE review_id=?"
        ),
        "v2_candidate_source_heads": (
            "SELECT COUNT(*) FROM v2_candidate_source_heads WHERE candidate_id IN "
            "(SELECT candidate_id FROM v2_working_candidates WHERE review_id=?)"
        ),
        "v2_source_artifacts": (
            "SELECT COUNT(DISTINCT b.artifact_id) FROM v2_source_binding_versions b "
            "WHERE b.review_id=? AND NOT EXISTS("
            "SELECT 1 FROM v2_source_binding_versions other "
            "WHERE other.artifact_id=b.artifact_id AND other.review_id<>?)"
        ),
        "v2_source_binding_versions": (
            "SELECT COUNT(*) FROM v2_source_binding_versions WHERE review_id=?"
        ),
        "v2_generation_analytical_state_events": (
            "SELECT COUNT(*) FROM v2_generation_analytical_state_events WHERE review_id=?"
        ),
        "export_artifacts": "SELECT COUNT(*) FROM export_artifacts WHERE cycle_id=?",
        "generation_supersessions": (
            "SELECT COUNT(*) FROM generation_supersessions WHERE prior_generation_id IN "
            "(SELECT generation_id FROM review_generations WHERE cycle_id=?) "
            "OR successor_generation_id IN "
            "(SELECT generation_id FROM review_generations WHERE cycle_id=?)"
        ),
        "findings": "SELECT COUNT(*) FROM findings WHERE cycle_id=?",
        "rule_runs": "SELECT COUNT(*) FROM rule_runs WHERE cycle_id=?",
        "review_generations": "SELECT COUNT(*) FROM review_generations WHERE cycle_id=?",
        "source_bindings": "SELECT COUNT(*) FROM source_bindings WHERE cycle_id=?",
        "ingested_files": "SELECT COUNT(*) FROM ingested_files WHERE cycle_id=?",
        "audit": "SELECT COUNT(*) FROM audit WHERE cycle_id=?",
        "migration_diagnostics": (
            "SELECT COUNT(*) FROM migration_diagnostics WHERE cycle_id=?"
        ),
        "v2_authorization_decision_events": (
            "SELECT COUNT(*) FROM v2_authorization_decision_events WHERE resource_id=?"
        ),
        "v2_review_create_requests": (
            "SELECT COUNT(*) FROM v2_review_create_requests WHERE review_id=?"
        ),
        "v2_review_status_events": (
            "SELECT COUNT(*) FROM v2_review_status_events WHERE review_id=?"
        ),
        "v2_review_disposition_events": (
            "SELECT COUNT(*) FROM v2_review_disposition_events WHERE review_id=?"
        ),
        "v2_review_cycle_pointers": (
            "SELECT COUNT(*) FROM v2_review_cycle_pointers WHERE review_id=?"
        ),
        "v2_working_candidates": (
            "SELECT COUNT(*) FROM v2_working_candidates WHERE review_id=?"
        ),
        "v2_review_cycles": "SELECT COUNT(*) FROM v2_review_cycles WHERE review_id=?",
        "cycles": "SELECT COUNT(*) FROM cycles WHERE cycle_id=?",
    }

    _DELETE_QUERIES = {
        "ai_messages": (
            "DELETE FROM ai_messages WHERE conversation_id IN "
            "(SELECT conversation_id FROM ai_conversations WHERE cycle_id=?)"
        ),
        "ai_conversations": "DELETE FROM ai_conversations WHERE cycle_id=?",
        "ai_review_memory": "DELETE FROM ai_review_memory WHERE cycle_id=?",
        "ai_interactions": "DELETE FROM ai_interactions WHERE cycle_id=?",
        "v2_audit_event_scopes": (
            "DELETE FROM v2_audit_event_scopes WHERE event_id IN ("
            "SELECT e.event_id FROM v2_audit_events e JOIN v2_audit_streams s "
            "ON s.stream_id=e.stream_id WHERE s.review_id=?)"
        ),
        "v2_audit_events": (
            "DELETE FROM v2_audit_events WHERE stream_id IN "
            "(SELECT stream_id FROM v2_audit_streams WHERE review_id=?)"
        ),
        "v2_audit_streams": "DELETE FROM v2_audit_streams WHERE review_id=?",
        "v2_finding_review_status_events": (
            "DELETE FROM v2_finding_review_status_events WHERE review_id=?"
        ),
        "v2_finding_explanation_projections": (
            "DELETE FROM v2_finding_explanation_projections "
            "WHERE run_id IN (SELECT run_id FROM v2_validation_runs "
            "WHERE review_id=?)"
        ),
        "v2_leadership_summary_projections": (
            "DELETE FROM v2_leadership_summary_projections "
            "WHERE run_id IN (SELECT run_id FROM v2_validation_runs "
            "WHERE review_id=?)"
        ),
        "v2_review_completion_events": (
            "DELETE FROM v2_review_completion_events WHERE review_id=?"
        ),
        "v2_optional_validation_findings": (
            "DELETE FROM v2_optional_validation_findings WHERE run_id IN "
            "(SELECT run_id FROM v2_validation_runs WHERE review_id=?)"
        ),
        "v2_optional_rule_scope_results": (
            "DELETE FROM v2_optional_rule_scope_results WHERE run_id IN "
            "(SELECT run_id FROM v2_validation_runs WHERE review_id=?)"
        ),
        "v2_optional_rule_executions": (
            "DELETE FROM v2_optional_rule_executions WHERE run_id IN "
            "(SELECT run_id FROM v2_validation_runs WHERE review_id=?)"
        ),
        "v2_validation_run_rule_sets": (
            "DELETE FROM v2_validation_run_rule_sets WHERE run_id IN "
            "(SELECT run_id FROM v2_validation_runs WHERE review_id=?)"
        ),
        "v2_reanalysis_generation_bases": (
            "DELETE FROM v2_reanalysis_generation_bases WHERE review_id=?"
        ),
        "v2_rule_test_runs": (
            "DELETE FROM v2_rule_test_runs WHERE review_id=?"
        ),
        "v2_rule_set_members": (
            "DELETE FROM v2_rule_set_members WHERE rule_set_id IN "
            "(SELECT rule_set_id FROM v2_rule_set_versions WHERE review_id=?)"
        ),
        "v2_rule_set_versions": (
            "DELETE FROM v2_rule_set_versions WHERE review_id=?"
        ),
        "v2_review_completions": "DELETE FROM v2_review_completions WHERE review_id=?",
        "v2_validation_findings": (
            "DELETE FROM v2_validation_findings WHERE run_id IN "
            "(SELECT run_id FROM v2_validation_runs WHERE review_id=?)"
        ),
        "v2_rule_scope_results": (
            "DELETE FROM v2_rule_scope_results WHERE run_id IN "
            "(SELECT run_id FROM v2_validation_runs WHERE review_id=?)"
        ),
        "v2_rule_executions": (
            "DELETE FROM v2_rule_executions WHERE run_id IN "
            "(SELECT run_id FROM v2_validation_runs WHERE review_id=?)"
        ),
        "v2_validation_runs": "DELETE FROM v2_validation_runs WHERE review_id=?",
        "v2_generation_review_bases": (
            "DELETE FROM v2_generation_review_bases WHERE review_id=?"
        ),
        "v2_review_confirmations": "DELETE FROM v2_review_confirmations WHERE review_id=?",
        "v2_review_correction_events": (
            "DELETE FROM v2_review_correction_events WHERE review_id=?"
        ),
        "v2_source_intake_idempotency": (
            "DELETE FROM v2_source_intake_idempotency WHERE review_id=?"
        ),
        "v2_source_intake_summaries": (
            "DELETE FROM v2_source_intake_summaries WHERE review_id=?"
        ),
        "v2_metadata_evidence_records": (
            "DELETE FROM v2_metadata_evidence_records WHERE review_id=?"
        ),
        "v2_candidate_source_heads": (
            "DELETE FROM v2_candidate_source_heads WHERE candidate_id IN "
            "(SELECT candidate_id FROM v2_working_candidates WHERE review_id=?)"
        ),
        # Delete orphaned artifacts while their target bindings still identify
        # them. Foreign keys are deferred until all target bindings are gone.
        "v2_source_artifacts": (
            "DELETE FROM v2_source_artifacts WHERE artifact_id IN ("
            "SELECT b.artifact_id FROM v2_source_binding_versions b "
            "WHERE b.review_id=? AND NOT EXISTS("
            "SELECT 1 FROM v2_source_binding_versions other "
            "WHERE other.artifact_id=b.artifact_id AND other.review_id<>?))"
        ),
        "v2_source_binding_versions": (
            "DELETE FROM v2_source_binding_versions WHERE review_id=?"
        ),
        "v2_generation_analytical_state_events": (
            "DELETE FROM v2_generation_analytical_state_events WHERE review_id=?"
        ),
        "export_artifacts": "DELETE FROM export_artifacts WHERE cycle_id=?",
        "generation_supersessions": (
            "DELETE FROM generation_supersessions WHERE prior_generation_id IN "
            "(SELECT generation_id FROM review_generations WHERE cycle_id=?) "
            "OR successor_generation_id IN "
            "(SELECT generation_id FROM review_generations WHERE cycle_id=?)"
        ),
        "findings": "DELETE FROM findings WHERE cycle_id=?",
        "rule_runs": "DELETE FROM rule_runs WHERE cycle_id=?",
        "source_bindings": "DELETE FROM source_bindings WHERE cycle_id=?",
        "ingested_files": "DELETE FROM ingested_files WHERE cycle_id=?",
        "audit": "DELETE FROM audit WHERE cycle_id=?",
        "migration_diagnostics": (
            "DELETE FROM migration_diagnostics WHERE cycle_id=?"
        ),
        "v2_authorization_decision_events": (
            "DELETE FROM v2_authorization_decision_events WHERE resource_id=?"
        ),
        "v2_review_create_requests": (
            "DELETE FROM v2_review_create_requests WHERE review_id=?"
        ),
        "v2_review_status_events": (
            "DELETE FROM v2_review_status_events WHERE review_id=?"
        ),
        "v2_review_disposition_events": (
            "DELETE FROM v2_review_disposition_events WHERE review_id=?"
        ),
        "v2_review_cycle_pointers": (
            "DELETE FROM v2_review_cycle_pointers WHERE review_id=?"
        ),
        "v2_working_candidates": (
            "DELETE FROM v2_working_candidates WHERE review_id=?"
        ),
        "v2_review_cycles": "DELETE FROM v2_review_cycles WHERE review_id=?",
        "review_generations": "DELETE FROM review_generations WHERE cycle_id=?",
        "cycles": "DELETE FROM cycles WHERE cycle_id=?",
    }

    _GUARD_KEY_QUERIES = {
        "v2_review_cycles": "SELECT review_id FROM v2_review_cycles WHERE review_id=?",
        "v2_working_candidates": (
            "SELECT candidate_id FROM v2_working_candidates WHERE review_id=?"
        ),
        "v2_review_disposition_events": (
            "SELECT event_id FROM v2_review_disposition_events WHERE review_id=?"
        ),
        "v2_review_status_events": (
            "SELECT event_id FROM v2_review_status_events WHERE review_id=?"
        ),
        "v2_review_create_requests": (
            "SELECT idempotency_key FROM v2_review_create_requests WHERE review_id=?"
        ),
        "v2_authorization_decision_events": (
            "SELECT event_id FROM v2_authorization_decision_events WHERE resource_id=?"
        ),
        "v2_audit_events": (
            "SELECT e.event_id FROM v2_audit_events e JOIN v2_audit_streams s "
            "ON s.stream_id=e.stream_id WHERE s.review_id=?"
        ),
        "v2_audit_event_scopes": (
            "SELECT e.event_id FROM v2_audit_events e JOIN v2_audit_streams s "
            "ON s.stream_id=e.stream_id WHERE s.review_id=?"
        ),
        "v2_generation_analytical_state_events": (
            "SELECT event_id FROM v2_generation_analytical_state_events WHERE review_id=?"
        ),
        "v2_finding_review_status_events": (
            "SELECT event_id FROM v2_finding_review_status_events "
            "WHERE review_id=?"
        ),
        "v2_finding_explanation_projections": (
            "SELECT finding_id FROM v2_finding_explanation_projections "
            "WHERE run_id IN (SELECT run_id FROM v2_validation_runs "
            "WHERE review_id=?)"
        ),
        "v2_leadership_summary_projections": (
            "SELECT run_id FROM v2_leadership_summary_projections "
            "WHERE run_id IN (SELECT run_id FROM v2_validation_runs "
            "WHERE review_id=?)"
        ),
        "v2_source_artifacts": (
            "SELECT DISTINCT b.artifact_id FROM v2_source_binding_versions b "
            "WHERE b.review_id=? AND NOT EXISTS("
            "SELECT 1 FROM v2_source_binding_versions other "
            "WHERE other.artifact_id=b.artifact_id AND other.review_id<>?)"
        ),
        "v2_source_binding_versions": (
            "SELECT binding_id FROM v2_source_binding_versions WHERE review_id=?"
        ),
        "v2_candidate_source_heads": (
            "SELECT candidate_id FROM v2_candidate_source_heads WHERE candidate_id IN "
            "(SELECT candidate_id FROM v2_working_candidates WHERE review_id=?)"
        ),
        "v2_metadata_evidence_records": (
            "SELECT evidence_id FROM v2_metadata_evidence_records WHERE review_id=?"
        ),
        "v2_source_intake_summaries": (
            "SELECT summary_id FROM v2_source_intake_summaries WHERE review_id=?"
        ),
        "v2_source_intake_idempotency": (
            "SELECT DISTINCT review_id FROM v2_source_intake_idempotency WHERE review_id=?"
        ),
        "v2_review_correction_events": (
            "SELECT correction_id FROM v2_review_correction_events WHERE review_id=?"
        ),
        "v2_review_confirmations": (
            "SELECT confirmation_id FROM v2_review_confirmations WHERE review_id=?"
        ),
        "v2_generation_review_bases": (
            "SELECT generation_id FROM v2_generation_review_bases WHERE review_id=?"
        ),
        "v2_validation_runs": (
            "SELECT run_id FROM v2_validation_runs WHERE review_id=?"
        ),
        "v2_rule_executions": (
            "SELECT execution_id FROM v2_rule_executions WHERE run_id IN "
            "(SELECT run_id FROM v2_validation_runs WHERE review_id=?)"
        ),
        "v2_rule_scope_results": (
            "SELECT result_id FROM v2_rule_scope_results WHERE run_id IN "
            "(SELECT run_id FROM v2_validation_runs WHERE review_id=?)"
        ),
        "v2_validation_findings": (
            "SELECT finding_id FROM v2_validation_findings WHERE run_id IN "
            "(SELECT run_id FROM v2_validation_runs WHERE review_id=?)"
        ),
        "v2_review_completions": (
            "SELECT completion_id FROM v2_review_completions WHERE review_id=?"
        ),
        "v2_review_completion_events": (
            "SELECT completion_id FROM v2_review_completion_events WHERE review_id=?"
        ),
        "v2_optional_validation_findings": (
            "SELECT finding_id FROM v2_optional_validation_findings WHERE run_id IN "
            "(SELECT run_id FROM v2_validation_runs WHERE review_id=?)"
        ),
        "v2_optional_rule_scope_results": (
            "SELECT result_id FROM v2_optional_rule_scope_results WHERE run_id IN "
            "(SELECT run_id FROM v2_validation_runs WHERE review_id=?)"
        ),
        "v2_optional_rule_executions": (
            "SELECT execution_id FROM v2_optional_rule_executions WHERE run_id IN "
            "(SELECT run_id FROM v2_validation_runs WHERE review_id=?)"
        ),
        "v2_validation_run_rule_sets": (
            "SELECT run_id FROM v2_validation_run_rule_sets WHERE run_id IN "
            "(SELECT run_id FROM v2_validation_runs WHERE review_id=?)"
        ),
        "v2_reanalysis_generation_bases": (
            "SELECT generation_id FROM v2_reanalysis_generation_bases WHERE review_id=?"
        ),
        "v2_rule_test_runs": (
            "SELECT test_id FROM v2_rule_test_runs WHERE review_id=?"
        ),
        "v2_rule_set_members": (
            "SELECT rule_set_id FROM v2_rule_set_members WHERE rule_set_id IN "
            "(SELECT rule_set_id FROM v2_rule_set_versions WHERE review_id=?)"
        ),
        "v2_rule_set_versions": (
            "SELECT rule_set_id FROM v2_rule_set_versions WHERE review_id=?"
        ),
        "generation_supersessions": (
            "SELECT prior_generation_id FROM generation_supersessions "
            "WHERE prior_generation_id IN "
            "(SELECT generation_id FROM review_generations WHERE cycle_id=?) "
            "OR successor_generation_id IN "
            "(SELECT generation_id FROM review_generations WHERE cycle_id=?)"
        ),
        "export_artifacts": (
            "SELECT export_id FROM export_artifacts WHERE cycle_id=?"
        ),
    }

    def __init__(self, dal):
        self._dal = dal
        self._lock = threading.RLock()
        self._allowed_rows: Mapping[str, frozenset[str]] = {}
        self._dal.conn.create_function(
            "finsight_disposal_allows",
            2,
            self._disposal_allows,
            deterministic=False,
        )

    def _disposal_allows(self, table: object, key: object) -> int:
        table_name = "" if table is None else str(table)
        row_key = "" if key is None else str(key)
        return int(row_key in self._allowed_rows.get(table_name, frozenset()))

    def inventory(self, review_id: str) -> dict[str, int]:
        return dict(self._scope_plan(review_id).inventory)

    def tombstone(self, scope_token: str):
        row = self._dal.conn.execute(
            "SELECT tombstone_id,operation_id,scope_token,audit_stream_token,"
            "confirmation_fingerprint,inventory_fingerprint,deleted_inventory_json,"
            "retained_shared_json,actor_id,disposed_at,reason_code "
            "FROM v2_review_disposal_tombstones WHERE scope_token=?",
            (scope_token,),
        ).fetchone()
        if row is None:
            return None
        keys = (
            "tombstone_id",
            "operation_id",
            "scope_token",
            "audit_stream_token",
            "confirmation_fingerprint",
            "inventory_fingerprint",
            "deleted_inventory",
            "retained_shared",
            "actor_id",
            "disposed_at",
            "reason_code",
        )
        values = list(row)
        values[6] = json.loads(values[6])
        values[7] = json.loads(values[7])
        return dict(zip(keys, values))

    def dispose(
        self,
        *,
        review_id: str,
        operation_id: str,
        tombstone_id: str,
        confirmation_fingerprint: str,
        actor_id: str,
        disposed_at: str,
        reason_code: str,
    ) -> dict:
        if not self._dal.conn.in_transaction:
            raise RuntimeError("Review disposal requires an active transaction.")
        with self._lock:
            if self._allowed_rows:
                raise RuntimeError("Another review disposal is already active.")
            plan = self._scope_plan(review_id)
            if plan.inventory["v2_review_cycles"] != 1:
                raise LookupError("The review no longer exists.")
            scope = review_scope_token(review_id)
            audit_token = review_audit_stream_token(review_id)
            fingerprint = inventory_fingerprint(plan.inventory)
            self._allowed_rows = plan.allowed_rows
            deleted: dict[str, int] = {}
            try:
                self._dal.conn.execute("PRAGMA defer_foreign_keys=ON")
                for table, statement in self._DELETE_QUERIES.items():
                    parameters = self._parameters(table, review_id)
                    changed = self._dal.conn.execute(statement, parameters).rowcount
                    expected = int(plan.inventory[table])
                    if changed != expected:
                        raise RuntimeError(
                            f"Disposal inventory changed for {table}: "
                            f"expected {expected}, deleted {changed}."
                        )
                    deleted[table] = changed
                remaining = self._remaining_counts(review_id)
                if any(remaining.values()):
                    raise RuntimeError(
                        "The review disposal closure was incomplete: "
                        + _canonical(remaining)
                    )
                self._dal.conn.execute(
                    "INSERT INTO v2_review_disposal_tombstones("
                    "tombstone_id,operation_id,scope_token,audit_stream_token,"
                    "confirmation_fingerprint,inventory_fingerprint,"
                    "deleted_inventory_json,retained_shared_json,actor_id,disposed_at,"
                    "reason_code) VALUES(?,?,?,?,?,?,?,?,?,?,?)",
                    (
                        tombstone_id,
                        operation_id,
                        scope,
                        audit_token,
                        confirmation_fingerprint,
                        fingerprint,
                        _canonical(deleted),
                        _canonical(plan.retained_shared),
                        actor_id,
                        disposed_at,
                        reason_code,
                    ),
                )
            finally:
                self._allowed_rows = {}
            return {
                "operation_id": operation_id,
                "tombstone_id": tombstone_id,
                "scope_token": scope,
                "audit_stream_token": audit_token,
                "inventory_fingerprint": fingerprint,
                "actor_id": actor_id,
                "disposed_at": disposed_at,
                "deleted_counts": deleted,
                "retained_shared_counts": dict(plan.retained_shared),
            }

    def _scope_plan(self, review_id: str) -> _ScopePlan:
        inventory = {}
        for table, statement in self._COUNT_QUERIES.items():
            parameters = self._parameters(table, review_id)
            inventory[table] = int(
                self._dal.conn.execute(statement, parameters).fetchone()[0]
            )
        allowed = {}
        for table, statement in self._GUARD_KEY_QUERIES.items():
            parameters = self._parameters(table, review_id)
            allowed[table] = frozenset(
                str(row[0])
                for row in self._dal.conn.execute(statement, parameters).fetchall()
            )
        target_artifacts = int(
            self._dal.conn.execute(
                "SELECT COUNT(DISTINCT artifact_id) "
                "FROM v2_source_binding_versions WHERE review_id=?",
                (review_id,),
            ).fetchone()[0]
        )
        retained_shared = {
            "v2_source_artifacts": max(
                0, target_artifacts - inventory["v2_source_artifacts"]
            )
        }
        return _ScopePlan(
            inventory=dict(sorted(inventory.items())),
            retained_shared=retained_shared,
            allowed_rows=allowed,
        )

    def _remaining_counts(self, review_id: str) -> dict[str, int]:
        remaining = {}
        for table, statement in self._COUNT_QUERIES.items():
            if table == "v2_source_artifacts":
                # Shared artifacts intentionally remain, but no binding may
                # continue to associate them with the disposed review.
                continue
            parameters = self._parameters(table, review_id)
            count = int(self._dal.conn.execute(statement, parameters).fetchone()[0])
            if count:
                remaining[table] = count
        return remaining

    @staticmethod
    def _parameters(table: str, review_id: str) -> tuple[str, ...]:
        if table in ("v2_source_artifacts", "generation_supersessions"):
            return (review_id, review_id)
        return (review_id,)
