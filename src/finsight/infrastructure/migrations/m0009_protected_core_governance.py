"""Append-only two-person governance for protected core-rule successors."""
from __future__ import annotations

import sqlite3


VERSION = 9
NAME = "protected_core_governance"


_APPEND_ONLY = (
    "v2_protected_candidate_tests",
    "v2_protected_change_requests",
    "v2_protected_change_decisions",
    "v2_protected_change_activations",
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
        "CREATE TABLE IF NOT EXISTS v2_protected_candidate_tests("
        "test_id TEXT PRIMARY KEY,"
        "rule_id TEXT NOT NULL,"
        "rule_version TEXT NOT NULL,"
        "evidence_context_hash TEXT NOT NULL CHECK(length(evidence_context_hash)=64),"
        "dataset_fingerprint TEXT NOT NULL,"
        "status TEXT NOT NULL CHECK(status='COMPLETE'),"
        "metrics_json TEXT NOT NULL,"
        "ledger_hash TEXT NOT NULL UNIQUE CHECK(length(ledger_hash)=64),"
        "actor_id TEXT NOT NULL,"
        "tested_at TEXT NOT NULL,"
        "FOREIGN KEY(rule_id,rule_version) REFERENCES "
        "v2_rule_definition_versions(rule_id,version))"
    )
    conn.execute(
        "CREATE TABLE IF NOT EXISTS v2_protected_change_requests("
        "request_id TEXT PRIMARY KEY,"
        "rule_id TEXT NOT NULL "
        "CHECK(rule_id IN ('CORE-01','CORE-02','CORE-03','CORE-04','CORE-05')),"
        "predecessor_version TEXT NOT NULL,"
        "candidate_version TEXT NOT NULL,"
        "change_kind TEXT NOT NULL "
        "CHECK(change_kind IN ('SEMANTIC','PARAMETER','SEMANTIC_AND_PARAMETER')),"
        "requested_action TEXT NOT NULL CHECK(requested_action='REPLACE'),"
        "reason TEXT NOT NULL CHECK(length(trim(reason))>0),"
        "proposed_effective_at TEXT NOT NULL,"
        "requester_actor_id TEXT NOT NULL,"
        "requested_at TEXT NOT NULL,"
        "candidate_content_hash TEXT NOT NULL CHECK(length(candidate_content_hash)=64),"
        "evidence_context_hash TEXT NOT NULL CHECK(length(evidence_context_hash)=64),"
        "before_definition_json TEXT NOT NULL,"
        "after_definition_json TEXT NOT NULL,"
        "test_id TEXT NOT NULL UNIQUE REFERENCES v2_protected_candidate_tests(test_id),"
        "prior_request_id TEXT REFERENCES v2_protected_change_requests(request_id),"
        "initial_status TEXT NOT NULL "
        "CHECK(initial_status='PENDING_APPROVAL'),"
        "UNIQUE(rule_id,candidate_version),"
        "FOREIGN KEY(rule_id,predecessor_version) REFERENCES "
        "v2_rule_definition_versions(rule_id,version),"
        "FOREIGN KEY(rule_id,candidate_version) REFERENCES "
        "v2_rule_definition_versions(rule_id,version))"
    )
    conn.execute(
        "CREATE TABLE IF NOT EXISTS v2_protected_change_decisions("
        "request_id TEXT PRIMARY KEY "
        "REFERENCES v2_protected_change_requests(request_id),"
        "decision TEXT NOT NULL CHECK(decision IN ('APPROVED','REJECTED')),"
        "approver_actor_id TEXT NOT NULL,"
        "decided_at TEXT NOT NULL,"
        "reason TEXT NOT NULL CHECK(length(trim(reason))>0),"
        "decision_hash TEXT NOT NULL UNIQUE CHECK(length(decision_hash)=64))"
    )
    conn.execute(
        "CREATE TABLE IF NOT EXISTS v2_protected_change_activations("
        "request_id TEXT PRIMARY KEY "
        "REFERENCES v2_protected_change_requests(request_id),"
        "prior_baseline_id TEXT NOT NULL "
        "REFERENCES v2_core_rule_set_versions(rule_set_id),"
        "resulting_baseline_id TEXT NOT NULL UNIQUE "
        "REFERENCES v2_core_rule_set_versions(rule_set_id),"
        "activated_rule_id TEXT NOT NULL,"
        "activated_rule_version TEXT NOT NULL,"
        "activated_at TEXT NOT NULL,"
        "activation_hash TEXT NOT NULL UNIQUE CHECK(length(activation_hash)=64),"
        "FOREIGN KEY(activated_rule_id,activated_rule_version) REFERENCES "
        "v2_core_rule_versions(rule_id,version))"
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_v2_protected_requests_rule_time "
        "ON v2_protected_change_requests(rule_id,requested_at)"
    )
    conn.execute(
        "CREATE TRIGGER IF NOT EXISTS "
        "trg_v2_protected_request_requires_tested_candidate "
        "BEFORE INSERT ON v2_protected_change_requests "
        "FOR EACH ROW WHEN COALESCE(("
        "SELECT status FROM v2_rule_lifecycle_events "
        "WHERE rule_id=NEW.rule_id AND rule_version=NEW.candidate_version "
        "ORDER BY ordinal DESC LIMIT 1),'') <> 'TESTED' "
        "BEGIN SELECT RAISE(ABORT,'protected candidate must be immutable Tested'); END"
    )
    conn.execute(
        "CREATE TRIGGER IF NOT EXISTS "
        "trg_v2_protected_request_content_hash_matches "
        "BEFORE INSERT ON v2_protected_change_requests "
        "FOR EACH ROW WHEN COALESCE(("
        "SELECT content_hash FROM v2_rule_definition_versions "
        "WHERE rule_id=NEW.rule_id AND version=NEW.candidate_version"
        "),'') <> NEW.candidate_content_hash "
        "BEGIN SELECT RAISE(ABORT,'protected candidate content hash mismatch'); END"
    )
    conn.execute(
        "CREATE TRIGGER IF NOT EXISTS "
        "trg_v2_protected_request_exact_qualification "
        "BEFORE INSERT ON v2_protected_change_requests "
        "FOR EACH ROW WHEN NOT EXISTS("
        "SELECT 1 FROM v2_protected_candidate_tests t "
        "WHERE t.test_id=NEW.test_id "
        "AND t.rule_id=NEW.rule_id "
        "AND t.rule_version=NEW.candidate_version "
        "AND t.evidence_context_hash=NEW.evidence_context_hash "
        "AND t.status='COMPLETE') "
        "BEGIN SELECT RAISE(ABORT,'protected request qualification mismatch'); END"
    )
    conn.execute(
        "CREATE TRIGGER IF NOT EXISTS "
        "trg_v2_protected_request_revision_lineage "
        "BEFORE INSERT ON v2_protected_change_requests "
        "FOR EACH ROW WHEN NEW.prior_request_id IS NOT NULL AND NOT EXISTS("
        "SELECT 1 FROM v2_protected_change_requests p "
        "JOIN v2_protected_change_decisions d "
        "ON d.request_id=p.request_id "
        "WHERE p.request_id=NEW.prior_request_id "
        "AND p.rule_id=NEW.rule_id) "
        "BEGIN SELECT RAISE(ABORT,'protected revision lineage mismatch'); END"
    )
    conn.execute(
        "CREATE TRIGGER IF NOT EXISTS trg_v2_protected_decision_distinct_actor "
        "BEFORE INSERT ON v2_protected_change_decisions "
        "FOR EACH ROW WHEN NEW.approver_actor_id=("
        "SELECT requester_actor_id FROM v2_protected_change_requests "
        "WHERE request_id=NEW.request_id) "
        "BEGIN SELECT RAISE(ABORT,'protected request self-approval denied'); END"
    )
    conn.execute(
        "CREATE TRIGGER IF NOT EXISTS trg_v2_protected_activation_requires_approval "
        "BEFORE INSERT ON v2_protected_change_activations "
        "FOR EACH ROW WHEN COALESCE(("
        "SELECT decision FROM v2_protected_change_decisions "
        "WHERE request_id=NEW.request_id),'') <> 'APPROVED' "
        "BEGIN SELECT RAISE(ABORT,'protected activation requires approval'); END"
    )
    conn.execute(
        "CREATE TRIGGER IF NOT EXISTS trg_v2_protected_activation_exact_candidate "
        "BEFORE INSERT ON v2_protected_change_activations "
        "FOR EACH ROW WHEN NOT EXISTS("
        "SELECT 1 FROM v2_protected_change_requests r "
        "WHERE r.request_id=NEW.request_id "
        "AND r.rule_id=NEW.activated_rule_id "
        "AND r.candidate_version=NEW.activated_rule_version) "
        "BEGIN SELECT RAISE(ABORT,'protected activation candidate mismatch'); END"
    )
    conn.execute(
        "CREATE TRIGGER IF NOT EXISTS trg_v2_protected_activation_current_head "
        "BEFORE INSERT ON v2_protected_change_activations "
        "FOR EACH ROW WHEN NEW.prior_baseline_id <> COALESCE(("
        "SELECT resulting_baseline_id FROM v2_protected_change_activations "
        "ORDER BY rowid DESC LIMIT 1),'FINSIGHT-CORE-2.0') "
        "BEGIN SELECT RAISE(ABORT,'protected activation predecessor mismatch'); END"
    )
    conn.execute(
        "CREATE TRIGGER IF NOT EXISTS trg_v2_protected_activation_exact_baseline "
        "BEFORE INSERT ON v2_protected_change_activations "
        "FOR EACH ROW WHEN "
        "NEW.resulting_baseline_id=NEW.prior_baseline_id OR "
        "(SELECT COUNT(*) FROM v2_core_rule_set_members "
        "WHERE rule_set_id=NEW.resulting_baseline_id)<>5 OR "
        "(SELECT COUNT(*) FROM v2_core_rule_set_members "
        "WHERE rule_set_id=NEW.resulting_baseline_id "
        "AND rule_id IN ('CORE-01','CORE-02','CORE-03','CORE-04','CORE-05'))<>5 OR "
        "NOT EXISTS(SELECT 1 FROM v2_core_rule_set_members "
        "WHERE rule_set_id=NEW.resulting_baseline_id "
        "AND rule_id=NEW.activated_rule_id "
        "AND rule_version=NEW.activated_rule_version) "
        "BEGIN SELECT RAISE(ABORT,'protected activation baseline mismatch'); END"
    )
    for table in _APPEND_ONLY:
        _append_only(conn, table)
