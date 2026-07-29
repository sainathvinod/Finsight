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
    m0010_protected_core_governance_integrity,
    m0011_protected_request_baseline_binding,
)


def _connection() -> sqlite3.Connection:
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
        m0010_protected_core_governance_integrity,
    ):
        migration.up(connection)
    return connection


def _seed_request(connection: sqlite3.Connection) -> None:
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
    for ordinal, status in ((1, "DRAFT"), (2, "TESTED")):
        connection.execute(
            "INSERT INTO v2_rule_lifecycle_events("
            "event_id,rule_id,rule_version,ordinal,status,actor_id,occurred_at,"
            "reason,event_hash) VALUES(?,?,?,?,?,'actor-admin',"
            "'2026-07-28T00:00:00Z','qualification',?)",
            (
                f"evt-{ordinal}",
                "CORE-01",
                "2.0.1",
                ordinal,
                status,
                f"{ordinal}" * 64,
            ),
        )
    connection.execute(
        "INSERT INTO v2_protected_candidate_tests("
        "test_id,rule_id,rule_version,evidence_context_hash,dataset_fingerprint,"
        "status,metrics_json,ledger_hash,actor_id,tested_at"
        ") VALUES('test-1','CORE-01','2.0.1',?,?,'COMPLETE','{}',?,"
        "'actor-admin','2026-07-28T00:00:00Z')",
        ("b" * 64, "c" * 64, "d" * 64),
    )
    connection.execute(
        "INSERT INTO v2_protected_change_requests("
        "request_id,rule_id,predecessor_version,candidate_version,"
        "change_kind,requested_action,reason,proposed_effective_at,"
        "requester_actor_id,requested_at,candidate_content_hash,"
        "evidence_context_hash,before_definition_json,after_definition_json,"
        "test_id,prior_request_id,initial_status"
        ") VALUES('request-1','CORE-01','2.0.0','2.0.1','SEMANTIC',"
        "'REPLACE','Reason','2026-07-28T00:00:00Z','actor-admin',"
        "'2026-07-28T00:00:00Z',?,?,'{}','{}','test-1',NULL,"
        "'PENDING_APPROVAL')",
        ("a" * 64, "b" * 64),
    )


def test_migration_0011_backfills_and_locks_request_time_baseline():
    connection = _connection()
    _seed_request(connection)

    m0011_protected_request_baseline_binding.up(connection)

    row = connection.execute(
        "SELECT requested_baseline_id FROM v2_protected_change_requests "
        "WHERE request_id='request-1'"
    ).fetchone()
    assert row == ("FINSIGHT-CORE-2.0",)
    triggers = {
        value[0]
        for value in connection.execute(
            "SELECT name FROM sqlite_master WHERE type='trigger'"
        )
    }
    assert {
        "trg_v2_protected_request_requires_baseline",
        "trg_v2_protected_activation_requested_baseline",
        "trg_v2_protected_change_requests_no_update",
    }.issubset(triggers)
    with pytest.raises(sqlite3.IntegrityError, match="append-only"):
        connection.execute(
            "UPDATE v2_protected_change_requests "
            "SET requested_baseline_id='FINSIGHT-CORE-1.0' "
            "WHERE request_id='request-1'"
        )
    assert m0011_protected_request_baseline_binding.VERSION == 11


def test_new_request_requires_an_existing_protected_baseline():
    connection = _connection()
    _seed_request(connection)
    m0011_protected_request_baseline_binding.up(connection)

    with pytest.raises(
        sqlite3.IntegrityError, match="baseline is required"
    ):
        connection.execute(
            "INSERT INTO v2_protected_change_requests("
            "request_id,rule_id,requested_baseline_id,predecessor_version,"
            "candidate_version,change_kind,requested_action,reason,"
            "proposed_effective_at,requester_actor_id,requested_at,"
            "candidate_content_hash,evidence_context_hash,"
            "before_definition_json,after_definition_json,test_id,"
            "prior_request_id,initial_status"
            ") SELECT 'request-no-baseline',rule_id,NULL,"
            "predecessor_version,'2.0.2',change_kind,requested_action,reason,"
            "proposed_effective_at,requester_actor_id,requested_at,"
            "candidate_content_hash,evidence_context_hash,"
            "before_definition_json,after_definition_json,test_id,"
            "prior_request_id,initial_status "
            "FROM v2_protected_change_requests WHERE request_id='request-1'"
        )
