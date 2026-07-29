"""Configurable rule versions, workspace rule sets, and retained reanalysis."""
from __future__ import annotations

import json
import sqlite3


VERSION = 7
NAME = "configurable_rules_and_reanalysis"


_APPEND_ONLY = (
    "v2_rule_definition_versions",
    "v2_rule_lifecycle_events",
    "v2_rule_test_runs",
    "v2_rule_set_versions",
    "v2_rule_set_members",
    "v2_validation_run_rule_sets",
    "v2_optional_rule_executions",
    "v2_optional_rule_scope_results",
    "v2_optional_validation_findings",
    "v2_reanalysis_generation_bases",
    "v2_review_completion_events",
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


def _json(value) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def up(conn: sqlite3.Connection) -> None:
    conn.execute(
        "CREATE TABLE IF NOT EXISTS v2_rule_definition_versions("
        "rule_id TEXT NOT NULL,version TEXT NOT NULL,classification TEXT NOT NULL "
        "CHECK(classification IN ('CORE_MANDATORY','OPTIONAL_CONFIGURABLE')),"
        "name TEXT NOT NULL,purpose TEXT NOT NULL,severity TEXT NOT NULL "
        "CHECK(severity IN ('Critical','High','Medium','Low')),"
        "baseline_status TEXT NOT NULL "
        "CHECK(baseline_status IN ('PROTECTED_BASELINE','OPTIONAL_CONFIGURABLE')),"
        "evaluator_key TEXT NOT NULL,parameters_json TEXT NOT NULL,"
        "required_fields_json TEXT NOT NULL,grouping_keys_json TEXT NOT NULL,"
        "predecessor_version TEXT,created_by TEXT NOT NULL,created_at TEXT NOT NULL,"
        "content_hash TEXT NOT NULL UNIQUE,PRIMARY KEY(rule_id,version),"
        "FOREIGN KEY(rule_id,predecessor_version) REFERENCES "
        "v2_rule_definition_versions(rule_id,version))"
    )
    conn.execute(
        "CREATE TABLE IF NOT EXISTS v2_rule_lifecycle_events("
        "event_id TEXT PRIMARY KEY,rule_id TEXT NOT NULL,rule_version TEXT NOT NULL,"
        "ordinal INTEGER NOT NULL CHECK(ordinal>0),status TEXT NOT NULL "
        "CHECK(status IN ('DRAFT','TESTED','ACTIVE','RETIRED')),"
        "actor_id TEXT NOT NULL,occurred_at TEXT NOT NULL,reason TEXT NOT NULL,"
        "event_hash TEXT NOT NULL UNIQUE,UNIQUE(rule_id,rule_version,ordinal),"
        "FOREIGN KEY(rule_id,rule_version) REFERENCES "
        "v2_rule_definition_versions(rule_id,version))"
    )
    conn.execute(
        "CREATE TABLE IF NOT EXISTS v2_rule_test_runs("
        "test_id TEXT PRIMARY KEY,review_id TEXT NOT NULL REFERENCES v2_review_cycles(review_id),"
        "rule_id TEXT NOT NULL,rule_version TEXT NOT NULL,dataset_fingerprint TEXT NOT NULL,"
        "status TEXT NOT NULL CHECK(status IN ('COMPLETE','FAILED')),"
        "metrics_json TEXT NOT NULL,ledger_hash TEXT NOT NULL UNIQUE,"
        "actor_id TEXT NOT NULL,tested_at TEXT NOT NULL,"
        "FOREIGN KEY(rule_id,rule_version) REFERENCES "
        "v2_rule_definition_versions(rule_id,version))"
    )
    conn.execute(
        "CREATE TABLE IF NOT EXISTS v2_rule_set_versions("
        "rule_set_id TEXT PRIMARY KEY,review_id TEXT NOT NULL REFERENCES v2_review_cycles(review_id),"
        "version INTEGER NOT NULL CHECK(version>0),predecessor_rule_set_id TEXT "
        "REFERENCES v2_rule_set_versions(rule_set_id),protected_baseline_id TEXT NOT NULL "
        "REFERENCES v2_core_rule_set_versions(rule_set_id),content_hash TEXT NOT NULL UNIQUE,"
        "created_by TEXT NOT NULL,created_at TEXT NOT NULL,reason TEXT NOT NULL,"
        "UNIQUE(review_id,version))"
    )
    conn.execute(
        "CREATE TABLE IF NOT EXISTS v2_rule_set_members("
        "rule_set_id TEXT NOT NULL REFERENCES v2_rule_set_versions(rule_set_id),"
        "ordinal INTEGER NOT NULL CHECK(ordinal>0),rule_id TEXT NOT NULL,"
        "rule_version TEXT NOT NULL,enabled INTEGER NOT NULL CHECK(enabled IN (0,1)),"
        "PRIMARY KEY(rule_set_id,ordinal),UNIQUE(rule_set_id,rule_id),"
        "FOREIGN KEY(rule_id,rule_version) REFERENCES "
        "v2_rule_definition_versions(rule_id,version))"
    )
    conn.execute(
        "CREATE TABLE IF NOT EXISTS v2_validation_run_rule_sets("
        "run_id TEXT PRIMARY KEY REFERENCES v2_validation_runs(run_id),"
        "rule_set_id TEXT NOT NULL REFERENCES v2_rule_set_versions(rule_set_id),"
        "predecessor_run_id TEXT REFERENCES v2_validation_runs(run_id),"
        "revalidation_reason TEXT NOT NULL)"
    )
    conn.execute(
        "CREATE TABLE IF NOT EXISTS v2_optional_rule_executions("
        "execution_id TEXT PRIMARY KEY,run_id TEXT NOT NULL "
        "REFERENCES v2_validation_runs(run_id),ordinal INTEGER NOT NULL CHECK(ordinal>0),"
        "rule_id TEXT NOT NULL,rule_version TEXT NOT NULL,rule_name TEXT NOT NULL,"
        "baseline_status TEXT NOT NULL,status TEXT NOT NULL "
        "CHECK(status IN ('PASS','FAIL','NOT_EVALUATED')),"
        "pass_count INTEGER NOT NULL,fail_count INTEGER NOT NULL,"
        "not_evaluated_count INTEGER NOT NULL,UNIQUE(run_id,ordinal),"
        "UNIQUE(run_id,rule_id),FOREIGN KEY(rule_id,rule_version) "
        "REFERENCES v2_rule_definition_versions(rule_id,version))"
    )
    conn.execute(
        "CREATE TABLE IF NOT EXISTS v2_optional_rule_scope_results("
        "result_id TEXT PRIMARY KEY,run_id TEXT NOT NULL REFERENCES v2_validation_runs(run_id),"
        "execution_id TEXT NOT NULL REFERENCES v2_optional_rule_executions(execution_id),"
        "ordinal INTEGER NOT NULL CHECK(ordinal>0),rule_id TEXT NOT NULL,scope_id TEXT NOT NULL,"
        "status TEXT NOT NULL CHECK(status IN ('PASS','FAIL','NOT_EVALUATED')),"
        "department_number TEXT NOT NULL,account_number TEXT NOT NULL,"
        "source_records_json TEXT NOT NULL,expected TEXT NOT NULL,actual TEXT NOT NULL,"
        "explanation TEXT NOT NULL,evidence_json TEXT NOT NULL,"
        "UNIQUE(run_id,rule_id,scope_id),UNIQUE(run_id,ordinal))"
    )
    conn.execute(
        "CREATE TABLE IF NOT EXISTS v2_optional_validation_findings("
        "finding_id TEXT PRIMARY KEY,run_id TEXT NOT NULL REFERENCES v2_validation_runs(run_id),"
        "rule_id TEXT NOT NULL,rule_name TEXT NOT NULL,severity TEXT NOT NULL,"
        "department_number TEXT NOT NULL,account_number TEXT NOT NULL,"
        "source_records_json TEXT NOT NULL,original_or_edited_value TEXT NOT NULL,"
        "expected TEXT NOT NULL,actual TEXT NOT NULL,explanation TEXT NOT NULL,"
        "recommended_action TEXT NOT NULL,evidence_json TEXT NOT NULL)"
    )
    conn.execute(
        "CREATE TABLE IF NOT EXISTS v2_reanalysis_generation_bases("
        "generation_id TEXT PRIMARY KEY REFERENCES review_generations(generation_id),"
        "review_id TEXT NOT NULL REFERENCES v2_review_cycles(review_id),"
        "source_generation_id TEXT NOT NULL REFERENCES review_generations(generation_id),"
        "dataset_fingerprint TEXT NOT NULL,rule_set_id TEXT NOT NULL "
        "REFERENCES v2_rule_set_versions(rule_set_id),created_by TEXT NOT NULL,"
        "created_at TEXT NOT NULL)"
    )
    conn.execute(
        "CREATE TABLE IF NOT EXISTS v2_review_completion_events("
        "completion_id TEXT PRIMARY KEY,review_id TEXT NOT NULL "
        "REFERENCES v2_review_cycles(review_id),generation_id TEXT NOT NULL "
        "REFERENCES review_generations(generation_id),run_id TEXT NOT NULL UNIQUE "
        "REFERENCES v2_validation_runs(run_id),completed_by TEXT NOT NULL,"
        "completed_at TEXT NOT NULL,completion_note TEXT NOT NULL,seal_hash TEXT NOT NULL UNIQUE)"
    )

    created = "2026-07-28T00:00:00Z"
    definitions = (
        (
            "CORE-05",
            "Budget-to-GED Reconciliation",
            "High",
            "atd_reconciliation",
            "Summed GED Amount must equal Budget ATD for each Department Number + Account Number.",
            ("budget.atd", "ged.fiscal_period", "ged.amount"),
            ("department_number", "account_number"),
        ),
        (
            "CORE-01",
            "Budget Overrun",
            "High",
            "actual_not_over_budget",
            "Total GED actual spending must not exceed BGT for the same Department Number + Account Number.",
            ("budget.bgt", "ged.fiscal_period", "ged.amount"),
            ("department_number", "account_number"),
        ),
        (
            "CORE-02",
            "Valid Account Coding",
            "High",
            "valid_mapping",
            "Every GED Department Number + Account Number combination must exist in the Budget report.",
            ("budget.account_number", "ged.department_number", "ged.account_number"),
            ("source_record",),
        ),
        (
            "CORE-04",
            "Complete and Correct Data",
            "High",
            "required_fields",
            "Required values must parse and Budget EAC/DELTA calculations must be internally consistent.",
            (
                "ged.department_number",
                "ged.account_number",
                "ged.fiscal_period",
                "ged.journal_number",
                "ged.journal_date",
                "ged.amount",
                "budget.account_number",
                "budget.bgt",
                "budget.atd",
                "budget.etc",
                "budget.eac",
                "budget.delta",
            ),
            ("source_record",),
        ),
        (
            "CORE-03",
            "Duplicate Transactions",
            "Medium",
            "exact_duplicates",
            "Flag GED rows with the same approved all-material-field duplicate fingerprint.",
            (
                "ged.department_number",
                "ged.department_name",
                "ged.account_number",
                "ged.account_name",
                "ged.fiscal_period",
                "ged.journal_number",
                "ged.journal_date",
                "ged.invoice_amount",
                "ged.check_number",
                "ged.invoice_date",
                "ged.vendor_name",
                "ged.agency",
                "ged.journal_description",
                "ged.journal_line_description",
                "ged.amount",
            ),
            ("approved_ged_15_field_fingerprint",),
        ),
    )
    for ordinal, (
        rule_id,
        name,
        severity,
        evaluator,
        purpose,
        fields,
        keys,
    ) in enumerate(definitions, 1):
        conn.execute(
            "INSERT OR IGNORE INTO v2_core_rule_versions("
            "rule_id,version,name,severity,baseline_status,evaluator_key,created_at"
            ") VALUES(?,?,?,?,?,?,?)",
            (
                rule_id,
                "2.0.0",
                name,
                severity,
                "PROTECTED_BASELINE",
                evaluator,
                created,
            ),
        )
        content_hash = f"seed-core-2-{rule_id.lower()}"
        conn.execute(
            "INSERT OR IGNORE INTO v2_rule_definition_versions("
            "rule_id,version,classification,name,purpose,severity,baseline_status,"
            "evaluator_key,parameters_json,required_fields_json,grouping_keys_json,"
            "predecessor_version,created_by,created_at,content_hash"
            ") VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                rule_id,
                "2.0.0",
                "CORE_MANDATORY",
                name,
                purpose,
                severity,
                "PROTECTED_BASELINE",
                evaluator,
                "{}",
                _json(fields),
                _json(keys),
                None,
                "finsight-release",
                created,
                content_hash,
            ),
        )
        conn.execute(
            "INSERT OR IGNORE INTO v2_rule_lifecycle_events("
            "event_id,rule_id,rule_version,ordinal,status,actor_id,occurred_at,reason,event_hash"
            ") VALUES(?,?,?,?,?,?,?,?,?)",
            (
                f"seed-core-2-{rule_id.lower()}",
                rule_id,
                "2.0.0",
                1,
                "ACTIVE",
                "finsight-release",
                created,
                "APPROVED_PRODUCT_BASELINE_SUCCESSOR",
                f"seed-core-2-event-{rule_id.lower()}",
            ),
        )
    conn.execute(
        "INSERT OR IGNORE INTO v2_core_rule_set_versions("
        "rule_set_id,version,status,created_at) VALUES(?,?,?,?)",
        ("FINSIGHT-CORE-2.0", "2.0.0", "PROTECTED_BASELINE", created),
    )
    for ordinal, definition in enumerate(definitions, 1):
        conn.execute(
            "INSERT OR IGNORE INTO v2_core_rule_set_members("
            "rule_set_id,ordinal,rule_id,rule_version) VALUES(?,?,?,?)",
            ("FINSIGHT-CORE-2.0", ordinal, definition[0], "2.0.0"),
        )

    conn.execute(
        "INSERT OR IGNORE INTO v2_review_completion_events("
        "completion_id,review_id,generation_id,run_id,completed_by,completed_at,"
        "completion_note,seal_hash) "
        "SELECT completion_id,review_id,generation_id,run_id,completed_by,completed_at,"
        "completion_note,seal_hash FROM v2_review_completions"
    )

    for table in _APPEND_ONLY:
        _append_only(conn, table)
