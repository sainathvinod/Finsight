"""Append-only governance for applying a newer protected baseline to one workspace."""
from __future__ import annotations

import sqlite3


VERSION = 12
NAME = "workspace_baseline_upgrade_governance"


_CORE_IDS = "'CORE-01','CORE-02','CORE-03','CORE-04','CORE-05'"
_APPEND_ONLY = (
    "v2_workspace_baseline_upgrade_requests",
    "v2_workspace_baseline_upgrade_decisions",
    "v2_workspace_baseline_upgrade_applications",
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
        "CREATE TABLE IF NOT EXISTS v2_workspace_baseline_upgrade_requests("
        "request_id TEXT PRIMARY KEY,"
        "request_type TEXT NOT NULL CHECK(request_type='WORKSPACE_BASELINE_UPGRADE'),"
        "review_id TEXT NOT NULL REFERENCES v2_review_cycles(review_id),"
        "requested_rule_set_id TEXT NOT NULL "
        "REFERENCES v2_rule_set_versions(rule_set_id),"
        "requested_rule_set_content_hash TEXT NOT NULL "
        "CHECK(length(requested_rule_set_content_hash)=64),"
        "source_baseline_id TEXT NOT NULL "
        "REFERENCES v2_core_rule_set_versions(rule_set_id),"
        "target_baseline_id TEXT NOT NULL "
        "REFERENCES v2_core_rule_set_versions(rule_set_id),"
        "target_baseline_hash TEXT NOT NULL CHECK(length(target_baseline_hash)=64),"
        "requested_run_id TEXT NOT NULL REFERENCES v2_validation_runs(run_id),"
        "requested_generation_id TEXT NOT NULL "
        "REFERENCES review_generations(generation_id),"
        "requester_actor_id TEXT NOT NULL,"
        "requested_at TEXT NOT NULL,"
        "reason TEXT NOT NULL CHECK(length(trim(reason))>0),"
        "initial_status TEXT NOT NULL CHECK(initial_status='PENDING_APPROVAL'),"
        "request_hash TEXT NOT NULL UNIQUE CHECK(length(request_hash)=64),"
        "CHECK(source_baseline_id<>target_baseline_id))"
    )
    conn.execute(
        "CREATE TABLE IF NOT EXISTS v2_workspace_baseline_upgrade_decisions("
        "request_id TEXT PRIMARY KEY "
        "REFERENCES v2_workspace_baseline_upgrade_requests(request_id),"
        "decision TEXT NOT NULL CHECK(decision IN ('APPROVED','REJECTED')),"
        "approver_actor_id TEXT NOT NULL,"
        "decided_at TEXT NOT NULL,"
        "reason TEXT NOT NULL CHECK(length(trim(reason))>0),"
        "decision_hash TEXT NOT NULL UNIQUE CHECK(length(decision_hash)=64))"
    )
    conn.execute(
        "CREATE TABLE IF NOT EXISTS v2_workspace_baseline_upgrade_applications("
        "request_id TEXT PRIMARY KEY "
        "REFERENCES v2_workspace_baseline_upgrade_requests(request_id),"
        "review_id TEXT NOT NULL REFERENCES v2_review_cycles(review_id),"
        "prior_rule_set_id TEXT NOT NULL "
        "REFERENCES v2_rule_set_versions(rule_set_id),"
        "resulting_rule_set_id TEXT NOT NULL UNIQUE "
        "REFERENCES v2_rule_set_versions(rule_set_id),"
        "source_baseline_id TEXT NOT NULL "
        "REFERENCES v2_core_rule_set_versions(rule_set_id),"
        "target_baseline_id TEXT NOT NULL "
        "REFERENCES v2_core_rule_set_versions(rule_set_id),"
        "applied_by_actor_id TEXT NOT NULL,"
        "applied_at TEXT NOT NULL,"
        "application_hash TEXT NOT NULL UNIQUE CHECK(length(application_hash)=64))"
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_v2_workspace_upgrade_review_time "
        "ON v2_workspace_baseline_upgrade_requests(review_id,requested_at)"
    )

    conn.execute(
        "CREATE TRIGGER IF NOT EXISTS "
        "trg_v2_workspace_upgrade_request_current_workspace "
        "BEFORE INSERT ON v2_workspace_baseline_upgrade_requests "
        "FOR EACH ROW WHEN NOT EXISTS("
        "SELECT 1 FROM v2_rule_set_versions s "
        "JOIN v2_review_cycle_pointers p ON p.review_id=s.review_id "
        "WHERE s.rule_set_id=NEW.requested_rule_set_id "
        "AND s.review_id=NEW.review_id "
        "AND s.content_hash=NEW.requested_rule_set_content_hash "
        "AND s.protected_baseline_id=NEW.source_baseline_id "
        "AND p.current_rule_set_id=s.rule_set_id) "
        "BEGIN SELECT RAISE(ABORT,'workspace upgrade request is stale'); END"
    )
    conn.execute(
        "CREATE TRIGGER IF NOT EXISTS "
        "trg_v2_workspace_upgrade_request_current_run "
        "BEFORE INSERT ON v2_workspace_baseline_upgrade_requests "
        "FOR EACH ROW WHEN NOT EXISTS("
        "SELECT 1 FROM v2_validation_runs v "
        "JOIN v2_validation_run_rule_sets b ON b.run_id=v.run_id "
        "JOIN v2_review_cycle_pointers p ON p.review_id=v.review_id "
        "WHERE v.run_id=NEW.requested_run_id "
        "AND v.review_id=NEW.review_id "
        "AND v.generation_id=NEW.requested_generation_id "
        "AND v.status='COMPLETE' "
        "AND b.rule_set_id=NEW.requested_rule_set_id "
        "AND p.published_generation_id=v.generation_id "
        "AND v.rowid=(SELECT MAX(latest.rowid) FROM v2_validation_runs latest "
        "WHERE latest.review_id=NEW.review_id AND latest.status='COMPLETE')) "
        "BEGIN SELECT RAISE(ABORT,'workspace upgrade requires current complete run'); END"
    )
    conn.execute(
        "CREATE TRIGGER IF NOT EXISTS "
        "trg_v2_workspace_upgrade_request_exact_source_members "
        "BEFORE INSERT ON v2_workspace_baseline_upgrade_requests "
        "FOR EACH ROW WHEN "
        "(SELECT COUNT(*) FROM v2_rule_set_members "
        "WHERE rule_set_id=NEW.requested_rule_set_id "
        f"AND rule_id IN ({_CORE_IDS}))<>5 OR "
        "EXISTS(SELECT 1 FROM v2_core_rule_set_members source "
        "WHERE source.rule_set_id=NEW.source_baseline_id AND NOT EXISTS("
        "SELECT 1 FROM v2_rule_set_members bound "
        "WHERE bound.rule_set_id=NEW.requested_rule_set_id "
        "AND bound.ordinal=source.ordinal "
        "AND bound.rule_id=source.rule_id "
        "AND bound.rule_version=source.rule_version "
        "AND bound.enabled=1)) "
        "BEGIN SELECT RAISE(ABORT,'workspace upgrade source members mismatch'); END"
    )
    conn.execute(
        "CREATE TRIGGER IF NOT EXISTS "
        "trg_v2_workspace_upgrade_request_effective_target "
        "BEFORE INSERT ON v2_workspace_baseline_upgrade_requests "
        "FOR EACH ROW WHEN "
        "NEW.target_baseline_id<>COALESCE(("
        "SELECT resulting_baseline_id FROM v2_protected_change_activations "
        "ORDER BY rowid DESC LIMIT 1),'FINSIGHT-CORE-2.0') OR "
        "(SELECT COUNT(*) FROM v2_core_rule_set_members "
        "WHERE rule_set_id=NEW.target_baseline_id)<>5 OR "
        "(SELECT COUNT(*) FROM v2_core_rule_set_members "
        f"WHERE rule_set_id=NEW.target_baseline_id AND rule_id IN ({_CORE_IDS}))<>5 "
        "BEGIN SELECT RAISE(ABORT,'workspace upgrade target is not effective'); END"
    )
    conn.execute(
        "CREATE TRIGGER IF NOT EXISTS "
        "trg_v2_workspace_upgrade_decision_distinct_actor "
        "BEFORE INSERT ON v2_workspace_baseline_upgrade_decisions "
        "FOR EACH ROW WHEN NEW.approver_actor_id=("
        "SELECT requester_actor_id FROM v2_workspace_baseline_upgrade_requests "
        "WHERE request_id=NEW.request_id) "
        "BEGIN SELECT RAISE(ABORT,'workspace upgrade self-approval denied'); END"
    )
    conn.execute(
        "CREATE TRIGGER IF NOT EXISTS "
        "trg_v2_workspace_upgrade_approval_not_stale "
        "BEFORE INSERT ON v2_workspace_baseline_upgrade_decisions "
        "FOR EACH ROW WHEN NEW.decision='APPROVED' AND EXISTS("
        "SELECT 1 FROM v2_workspace_baseline_upgrade_requests r "
        "WHERE r.request_id=NEW.request_id AND ("
        "r.target_baseline_id<>COALESCE(("
        "SELECT resulting_baseline_id FROM v2_protected_change_activations "
        "ORDER BY rowid DESC LIMIT 1),'FINSIGHT-CORE-2.0') OR "
        "r.requested_rule_set_id<>COALESCE(("
        "SELECT current_rule_set_id FROM v2_review_cycle_pointers "
        "WHERE review_id=r.review_id),'') OR "
        "r.requested_run_id<>COALESCE(("
        "SELECT run_id FROM v2_validation_runs "
        "WHERE review_id=r.review_id AND status='COMPLETE' "
        "ORDER BY rowid DESC LIMIT 1),'') OR "
        "r.requested_generation_id<>COALESCE(("
        "SELECT published_generation_id FROM v2_review_cycle_pointers "
        "WHERE review_id=r.review_id),''))) "
        "BEGIN SELECT RAISE(ABORT,'workspace upgrade approval is stale'); END"
    )
    conn.execute(
        "CREATE TRIGGER IF NOT EXISTS "
        "trg_v2_workspace_upgrade_application_exact_request "
        "BEFORE INSERT ON v2_workspace_baseline_upgrade_applications "
        "FOR EACH ROW WHEN NOT EXISTS("
        "SELECT 1 FROM v2_workspace_baseline_upgrade_requests r "
        "JOIN v2_workspace_baseline_upgrade_decisions d "
        "ON d.request_id=r.request_id "
        "JOIN v2_rule_set_versions s "
        "ON s.rule_set_id=NEW.resulting_rule_set_id "
        "JOIN v2_review_cycle_pointers p ON p.review_id=r.review_id "
        "WHERE r.request_id=NEW.request_id "
        "AND d.decision='APPROVED' "
        "AND d.approver_actor_id=NEW.applied_by_actor_id "
        "AND r.review_id=NEW.review_id "
        "AND r.requested_rule_set_id=NEW.prior_rule_set_id "
        "AND r.source_baseline_id=NEW.source_baseline_id "
        "AND r.target_baseline_id=NEW.target_baseline_id "
        "AND s.review_id=r.review_id "
        "AND s.predecessor_rule_set_id=r.requested_rule_set_id "
        "AND s.version=(SELECT prior.version+1 FROM v2_rule_set_versions prior "
        "WHERE prior.rule_set_id=r.requested_rule_set_id) "
        "AND s.protected_baseline_id=r.target_baseline_id "
        "AND s.created_by=NEW.applied_by_actor_id "
        "AND p.current_rule_set_id=s.rule_set_id "
        "AND p.published_generation_id=r.requested_generation_id "
        "AND r.target_baseline_id=COALESCE(("
        "SELECT resulting_baseline_id FROM v2_protected_change_activations "
        "ORDER BY rowid DESC LIMIT 1),'FINSIGHT-CORE-2.0') "
        "AND r.requested_run_id=("
        "SELECT run_id FROM v2_validation_runs "
        "WHERE review_id=r.review_id AND status='COMPLETE' "
        "ORDER BY rowid DESC LIMIT 1)) "
        "BEGIN SELECT RAISE(ABORT,'workspace upgrade application mismatch'); END"
    )
    conn.execute(
        "CREATE TRIGGER IF NOT EXISTS "
        "trg_v2_workspace_upgrade_application_exact_members "
        "BEFORE INSERT ON v2_workspace_baseline_upgrade_applications "
        "FOR EACH ROW WHEN "
        "(SELECT COUNT(*) FROM v2_rule_set_members "
        "WHERE rule_set_id=NEW.resulting_rule_set_id "
        f"AND rule_id IN ({_CORE_IDS}))<>5 OR "
        "EXISTS(SELECT 1 FROM v2_core_rule_set_members target "
        "WHERE target.rule_set_id=NEW.target_baseline_id AND NOT EXISTS("
        "SELECT 1 FROM v2_rule_set_members result "
        "WHERE result.rule_set_id=NEW.resulting_rule_set_id "
        "AND result.ordinal=target.ordinal "
        "AND result.rule_id=target.rule_id "
        "AND result.rule_version=target.rule_version "
        "AND result.enabled=1)) OR "
        "EXISTS(SELECT 1 FROM v2_rule_set_members prior "
        "WHERE prior.rule_set_id=NEW.prior_rule_set_id "
        f"AND prior.rule_id NOT IN ({_CORE_IDS}) AND NOT EXISTS("
        "SELECT 1 FROM v2_rule_set_members result "
        "WHERE result.rule_set_id=NEW.resulting_rule_set_id "
        "AND result.ordinal=prior.ordinal "
        "AND result.rule_id=prior.rule_id "
        "AND result.rule_version=prior.rule_version "
        "AND result.enabled=prior.enabled)) OR "
        "EXISTS(SELECT 1 FROM v2_rule_set_members result "
        "WHERE result.rule_set_id=NEW.resulting_rule_set_id "
        f"AND result.rule_id NOT IN ({_CORE_IDS}) AND NOT EXISTS("
        "SELECT 1 FROM v2_rule_set_members prior "
        "WHERE prior.rule_set_id=NEW.prior_rule_set_id "
        "AND prior.ordinal=result.ordinal "
        "AND prior.rule_id=result.rule_id "
        "AND prior.rule_version=result.rule_version "
        "AND prior.enabled=result.enabled)) "
        "BEGIN SELECT RAISE(ABORT,'workspace upgrade members mismatch'); END"
    )

    for table in _APPEND_ONLY:
        _append_only(conn, table)
