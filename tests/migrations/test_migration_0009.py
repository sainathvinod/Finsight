from __future__ import annotations

import sqlite3

import pytest

from finsight.infrastructure.migrations import (
    m0001_baseline,
    m0002_ai_platform,
    m0003_review_lifecycle,
    m0004_v2_review_management,
    m0005_v2_source_intake,
    m0006_v2_integrated_review,
    m0007_configurable_rules_and_reanalysis,
    m0008_review_disposal,
    m0009_protected_core_governance,
)


def _connection():
    connection = sqlite3.connect(":memory:")
    connection.execute("PRAGMA foreign_keys=ON")
    for migration in (
        m0001_baseline,
        m0002_ai_platform,
        m0003_review_lifecycle,
        m0004_v2_review_management,
        m0005_v2_source_intake,
        m0006_v2_integrated_review,
        m0007_configurable_rules_and_reanalysis,
        m0008_review_disposal,
        m0009_protected_core_governance,
    ):
        migration.up(connection)
    return connection


def test_migration_0009_creates_append_only_governance_ledger():
    connection = _connection()
    tables = {
        row[0]
        for row in connection.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        )
    }
    assert {
        "v2_protected_candidate_tests",
        "v2_protected_change_requests",
        "v2_protected_change_decisions",
        "v2_protected_change_activations",
    }.issubset(tables)
    triggers = {
        row[0]
        for row in connection.execute(
            "SELECT name FROM sqlite_master WHERE type='trigger'"
        )
    }
    assert "trg_v2_protected_change_requests_no_update" in triggers
    assert "trg_v2_protected_change_decisions_no_delete" in triggers
    assert "trg_v2_protected_decision_distinct_actor" in triggers
    assert "trg_v2_protected_activation_requires_approval" in triggers
    assert m0009_protected_core_governance.VERSION == 9


def test_migration_0009_denies_self_decision_at_commit_boundary():
    connection = _connection()
    connection.execute(
        "INSERT INTO cycles(cycle_id,month,year,state) "
        "VALUES('rev-governance','May','2026','Created')"
    )
    connection.execute(
        "INSERT INTO v2_review_cycles("
        "review_id,selected_month,selected_year,creation_actor_id,"
        "creation_actor_display,identity_source,created_at,origin"
        ") VALUES('rev-governance',5,2026,'actor-admin','Admin','TEST',"
        "'2026-07-28T00:00:00Z','NATIVE')"
    )
    connection.execute(
        "INSERT INTO v2_rule_definition_versions("
        "rule_id,version,classification,name,purpose,severity,baseline_status,"
        "evaluator_key,parameters_json,required_fields_json,grouping_keys_json,"
        "predecessor_version,created_by,created_at,content_hash"
        ") VALUES('CORE-01','2.0.1','CORE_MANDATORY','Budget Overrun',"
        "'Changed','High','PROTECTED_BASELINE','actual_not_over_budget','{}',"
        "'[]','[]','2.0.0','actor-admin','2026-07-28T00:00:00Z',?)",
        ("a" * 64,),
    )
    connection.execute(
        "INSERT INTO v2_rule_lifecycle_events("
        "event_id,rule_id,rule_version,ordinal,status,actor_id,occurred_at,"
        "reason,event_hash) VALUES('evt-draft','CORE-01','2.0.1',1,'DRAFT',"
        "'actor-admin','2026-07-28T00:00:00Z','draft',?)",
        ("b" * 64,),
    )
    connection.execute(
        "INSERT INTO v2_rule_lifecycle_events("
        "event_id,rule_id,rule_version,ordinal,status,actor_id,occurred_at,"
        "reason,event_hash) VALUES('evt-tested','CORE-01','2.0.1',2,'TESTED',"
        "'actor-admin','2026-07-28T00:00:00Z','tested',?)",
        ("c" * 64,),
    )
    connection.execute(
        "INSERT INTO v2_protected_candidate_tests("
        "test_id,rule_id,rule_version,evidence_context_hash,dataset_fingerprint,"
        "status,metrics_json,ledger_hash,actor_id,tested_at"
        ") VALUES('test-protected','CORE-01','2.0.1',?,?,'COMPLETE','{}',?,"
        "'actor-admin','2026-07-28T00:00:00Z')",
        ("d" * 64, "e" * 64, "f" * 64),
    )
    connection.execute(
        "INSERT INTO v2_protected_change_requests("
        "request_id,rule_id,predecessor_version,candidate_version,"
        "change_kind,requested_action,reason,proposed_effective_at,"
        "requester_actor_id,requested_at,candidate_content_hash,"
        "evidence_context_hash,before_definition_json,after_definition_json,test_id,"
        "prior_request_id,initial_status) VALUES('request-1','CORE-01','2.0.0',"
        "'2.0.1','SEMANTIC','REPLACE','Reason','2026-07-28T00:00:00Z',"
        "'actor-admin','2026-07-28T00:00:00Z',?,?,'{}','{}','test-protected',"
        "NULL,'PENDING_APPROVAL')",
        ("a" * 64, "d" * 64),
    )

    with pytest.raises(
        sqlite3.IntegrityError, match="self-approval denied"
    ):
        connection.execute(
            "INSERT INTO v2_protected_change_decisions("
            "request_id,decision,approver_actor_id,decided_at,reason,decision_hash"
            ") VALUES('request-1','APPROVED','actor-admin',"
            "'2026-07-28T00:00:01Z','Self approval',?)",
            ("0" * 64,),
        )
