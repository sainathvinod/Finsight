"""Persisted V2 reviewed-data basis and deterministic validation ledger."""
from __future__ import annotations

import sqlite3


VERSION = 6
NAME = "v2_integrated_financial_review"


_APPEND_ONLY = (
    "v2_core_rule_versions",
    "v2_core_rule_set_versions",
    "v2_core_rule_set_members",
    "v2_review_correction_events",
    "v2_review_confirmations",
    "v2_generation_review_bases",
    "v2_validation_runs",
    "v2_rule_executions",
    "v2_rule_scope_results",
    "v2_validation_findings",
    "v2_review_completions",
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
        "CREATE TABLE IF NOT EXISTS v2_core_rule_versions("
        "rule_id TEXT NOT NULL,version TEXT NOT NULL,name TEXT NOT NULL,"
        "severity TEXT NOT NULL,baseline_status TEXT NOT NULL "
        "CHECK(baseline_status='PROTECTED_BASELINE'),evaluator_key TEXT NOT NULL,"
        "created_at TEXT NOT NULL,PRIMARY KEY(rule_id,version))"
    )
    conn.execute(
        "CREATE TABLE IF NOT EXISTS v2_core_rule_set_versions("
        "rule_set_id TEXT PRIMARY KEY,version TEXT NOT NULL,status TEXT NOT NULL "
        "CHECK(status='PROTECTED_BASELINE'),created_at TEXT NOT NULL)"
    )
    conn.execute(
        "CREATE TABLE IF NOT EXISTS v2_core_rule_set_members("
        "rule_set_id TEXT NOT NULL REFERENCES v2_core_rule_set_versions(rule_set_id),"
        "ordinal INTEGER NOT NULL CHECK(ordinal>0),rule_id TEXT NOT NULL,"
        "rule_version TEXT NOT NULL,PRIMARY KEY(rule_set_id,ordinal),"
        "UNIQUE(rule_set_id,rule_id),"
        "FOREIGN KEY(rule_id,rule_version) REFERENCES "
        "v2_core_rule_versions(rule_id,version))"
    )
    conn.execute(
        "CREATE TABLE IF NOT EXISTS v2_review_correction_events("
        "correction_id TEXT PRIMARY KEY,review_id TEXT NOT NULL "
        "REFERENCES v2_review_cycles(review_id),candidate_id TEXT NOT NULL,"
        "record_id TEXT NOT NULL,source_role TEXT NOT NULL "
        "CHECK(source_role IN ('BUDGET','GED')),worksheet_name TEXT NOT NULL,"
        "source_row INTEGER NOT NULL CHECK(source_row>0),field_name TEXT NOT NULL,"
        "source_cell TEXT NOT NULL,original_value_json TEXT NOT NULL,"
        "prior_value_json TEXT NOT NULL,new_value_json TEXT NOT NULL,"
        "action TEXT NOT NULL CHECK(action IN ('EDIT','REVERT')),"
        "actor_id TEXT NOT NULL,occurred_at TEXT NOT NULL,"
        "predecessor_correction_id TEXT REFERENCES v2_review_correction_events(correction_id),"
        "event_hash TEXT NOT NULL UNIQUE)"
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_v2_corrections_review "
        "ON v2_review_correction_events(review_id,source_role,source_row,field_name,occurred_at)"
    )
    conn.execute(
        "CREATE TABLE IF NOT EXISTS v2_review_confirmations("
        "confirmation_id TEXT PRIMARY KEY,review_id TEXT NOT NULL "
        "REFERENCES v2_review_cycles(review_id),candidate_id TEXT NOT NULL,"
        "generation_id TEXT NOT NULL UNIQUE REFERENCES review_generations(generation_id),"
        "dataset_fingerprint TEXT NOT NULL,budget_sha256 TEXT NOT NULL,"
        "ged_sha256 TEXT NOT NULL,correction_count INTEGER NOT NULL CHECK(correction_count>=0),"
        "attestation_text TEXT NOT NULL,actor_id TEXT NOT NULL,confirmed_at TEXT NOT NULL)"
    )
    conn.execute(
        "CREATE TABLE IF NOT EXISTS v2_generation_review_bases("
        "generation_id TEXT PRIMARY KEY REFERENCES review_generations(generation_id),"
        "review_id TEXT NOT NULL REFERENCES v2_review_cycles(review_id),"
        "candidate_id TEXT NOT NULL,confirmation_id TEXT NOT NULL UNIQUE "
        "REFERENCES v2_review_confirmations(confirmation_id),"
        "dataset_fingerprint TEXT NOT NULL,department_number TEXT NOT NULL,"
        "department_name TEXT NOT NULL,reporting_period TEXT NOT NULL,"
        "budget_filename TEXT NOT NULL,ged_filename TEXT NOT NULL,"
        "budget_sha256 TEXT NOT NULL,ged_sha256 TEXT NOT NULL,"
        "budget_record_count INTEGER NOT NULL,ged_transaction_count INTEGER NOT NULL,"
        "correction_count INTEGER NOT NULL,extractor_profile_version TEXT NOT NULL,"
        "created_at TEXT NOT NULL)"
    )
    conn.execute(
        "CREATE TABLE IF NOT EXISTS v2_validation_runs("
        "run_id TEXT PRIMARY KEY,review_id TEXT NOT NULL "
        "REFERENCES v2_review_cycles(review_id),generation_id TEXT NOT NULL UNIQUE "
        "REFERENCES review_generations(generation_id),rule_set_id TEXT NOT NULL "
        "REFERENCES v2_core_rule_set_versions(rule_set_id),"
        "dataset_fingerprint TEXT NOT NULL,status TEXT NOT NULL "
        "CHECK(status IN ('COMPLETE','FAILED')),started_at TEXT NOT NULL,"
        "completed_at TEXT NOT NULL,actor_id TEXT NOT NULL,metrics_json TEXT NOT NULL,"
        "ledger_hash TEXT NOT NULL UNIQUE,completion_seal TEXT NOT NULL UNIQUE)"
    )
    conn.execute(
        "CREATE TABLE IF NOT EXISTS v2_rule_executions("
        "execution_id TEXT PRIMARY KEY,run_id TEXT NOT NULL "
        "REFERENCES v2_validation_runs(run_id),ordinal INTEGER NOT NULL CHECK(ordinal>0),"
        "rule_id TEXT NOT NULL,rule_version TEXT NOT NULL,rule_name TEXT NOT NULL,"
        "baseline_status TEXT NOT NULL,status TEXT NOT NULL "
        "CHECK(status IN ('PASS','FAIL','NOT_EVALUATED')),"
        "pass_count INTEGER NOT NULL,fail_count INTEGER NOT NULL,"
        "not_evaluated_count INTEGER NOT NULL,UNIQUE(run_id,ordinal),"
        "UNIQUE(run_id,rule_id),FOREIGN KEY(rule_id,rule_version) "
        "REFERENCES v2_core_rule_versions(rule_id,version))"
    )
    conn.execute(
        "CREATE TABLE IF NOT EXISTS v2_rule_scope_results("
        "result_id TEXT PRIMARY KEY,run_id TEXT NOT NULL "
        "REFERENCES v2_validation_runs(run_id),execution_id TEXT NOT NULL "
        "REFERENCES v2_rule_executions(execution_id),ordinal INTEGER NOT NULL CHECK(ordinal>0),"
        "rule_id TEXT NOT NULL,scope_id TEXT NOT NULL,status TEXT NOT NULL "
        "CHECK(status IN ('PASS','FAIL','NOT_EVALUATED')),"
        "department_number TEXT NOT NULL,account_number TEXT NOT NULL,"
        "source_records_json TEXT NOT NULL,expected TEXT NOT NULL,actual TEXT NOT NULL,"
        "explanation TEXT NOT NULL,evidence_json TEXT NOT NULL,"
        "UNIQUE(run_id,rule_id,scope_id),UNIQUE(run_id,ordinal))"
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_v2_scope_results_run_status "
        "ON v2_rule_scope_results(run_id,status,rule_id)"
    )
    conn.execute(
        "CREATE TABLE IF NOT EXISTS v2_validation_findings("
        "finding_id TEXT PRIMARY KEY,run_id TEXT NOT NULL "
        "REFERENCES v2_validation_runs(run_id),rule_id TEXT NOT NULL,"
        "rule_name TEXT NOT NULL,severity TEXT NOT NULL,department_number TEXT NOT NULL,"
        "account_number TEXT NOT NULL,source_records_json TEXT NOT NULL,"
        "original_or_edited_value TEXT NOT NULL,expected TEXT NOT NULL,actual TEXT NOT NULL,"
        "explanation TEXT NOT NULL,recommended_action TEXT NOT NULL,evidence_json TEXT NOT NULL)"
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_v2_findings_run "
        "ON v2_validation_findings(run_id,severity,rule_id)"
    )
    conn.execute(
        "CREATE TABLE IF NOT EXISTS v2_review_completions("
        "completion_id TEXT PRIMARY KEY,review_id TEXT NOT NULL UNIQUE "
        "REFERENCES v2_review_cycles(review_id),generation_id TEXT NOT NULL "
        "REFERENCES review_generations(generation_id),run_id TEXT NOT NULL UNIQUE "
        "REFERENCES v2_validation_runs(run_id),completed_by TEXT NOT NULL,"
        "completed_at TEXT NOT NULL,completion_note TEXT NOT NULL,seal_hash TEXT NOT NULL UNIQUE)"
    )

    created = "2026-01-01T00:00:00Z"
    definitions = (
        ("CORE-01", "1.0.0", "Actual spend must not exceed BGT", "High", "actual_not_over_budget"),
        ("CORE-02", "1.0.0", "Every GED transaction must map to Budget", "High", "valid_mapping"),
        ("CORE-03", "1.0.0", "Exact duplicate GED transactions", "Medium", "exact_duplicates"),
        ("CORE-04", "1.0.0", "Required GED fields must be present and parseable", "High", "required_fields"),
        ("CORE-05", "1.0.0", "Budget ATD must equal summed GED Amount", "High", "atd_reconciliation"),
    )
    for rule_id, version, name, severity, evaluator_key in definitions:
        conn.execute(
            "INSERT OR IGNORE INTO v2_core_rule_versions("
            "rule_id,version,name,severity,baseline_status,evaluator_key,created_at"
            ") VALUES(?,?,?,?,?,?,?)",
            (
                rule_id,
                version,
                name,
                severity,
                "PROTECTED_BASELINE",
                evaluator_key,
                created,
            ),
        )
    conn.execute(
        "INSERT OR IGNORE INTO v2_core_rule_set_versions("
        "rule_set_id,version,status,created_at) VALUES(?,?,?,?)",
        ("FINSIGHT-CORE-1.0", "1.0.0", "PROTECTED_BASELINE", created),
    )
    for ordinal, definition in enumerate(definitions, 1):
        conn.execute(
            "INSERT OR IGNORE INTO v2_core_rule_set_members("
            "rule_set_id,ordinal,rule_id,rule_version) VALUES(?,?,?,?)",
            ("FINSIGHT-CORE-1.0", ordinal, definition[0], definition[1]),
        )

    for table in _APPEND_ONLY:
        _append_only(conn, table)
