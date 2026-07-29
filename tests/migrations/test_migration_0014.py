"""Migration and persistence checks for the private Ask Fin audit."""
from __future__ import annotations

import sqlite3
from types import SimpleNamespace

from finsight.infrastructure.ai.private_audit import (
    PrivateAskFinAuditRepositorySqlite,
)
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
    m0012_workspace_baseline_upgrade_governance,
    m0013_finding_explanations_and_review_status,
    m0014_private_ask_fin_audit,
)
from finsight.infrastructure.persistence import SqliteUnitOfWork


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
        m0010_protected_core_governance_integrity,
        m0011_protected_request_baseline_binding,
        m0012_workspace_baseline_upgrade_governance,
        m0013_finding_explanations_and_review_status,
        m0014_private_ask_fin_audit,
    ):
        migration.up(connection)
    connection.execute(
        "INSERT INTO cycles(cycle_id,month,year,state) "
        "VALUES('rev_A','May','2026','Created')"
    )
    connection.execute(
        "INSERT INTO v2_review_cycles("
        "review_id,selected_month,selected_year,creation_actor_id,"
        "creation_actor_display,identity_source,created_at,origin"
        ") VALUES('rev_A',5,2026,'local-user','Local User','TEST',"
        "'2026-07-29T12:00:00Z','NATIVE')"
    )
    connection.commit()
    return connection


def test_migration_0014_creates_scoped_local_interaction_audit():
    connection = _connection()
    columns = {
        row[1]
        for row in connection.execute(
            "PRAGMA table_info(v2_private_ask_fin_interactions)"
        )
    }
    assert {
        "review_id",
        "validation_run_id",
        "scope_json",
        "question",
        "retrieved_records_json",
        "model_version",
        "prompt_version",
        "response",
        "citations_json",
        "refusal_trigger",
        "latency_ms",
        "failure_state",
    }.issubset(columns)
    assert m0014_private_ask_fin_audit.VERSION == 14


def test_private_audit_round_trips_required_metadata_locally():
    connection = _connection()
    dal = SimpleNamespace(conn=connection)
    repository = PrivateAskFinAuditRepositorySqlite(
        dal,
        SqliteUnitOfWork(dal),
        id_factory=lambda: "1",
    )
    repository.append(
        {
            "timestamp": "2026-07-29T12:00:00Z",
            "user_id": "local-user",
            "review_id": "rev_A",
            "validation_run_id": "run_A",
            "scope": {
                "review_id": "rev_A",
                "object_type": "account",
                "object_id": "00-0245|555035",
            },
            "mode": "financial_review",
            "question": "Why is account 555035 over budget?",
            "retrieved_records": ["account:rev_A:00-0245|555035"],
            "provider": "ollama",
            "model": "local-test:1",
            "model_version": "local-test:1",
            "prompt_version": "stage2-private-v1",
            "response": "Recorded explanation.",
            "citations": ["account:rev_A:00-0245|555035"],
            "refusal_trigger": None,
            "latency_ms": 25,
            "failure_state": None,
            "status": "ok",
            "grounding_review_id": "rev_A",
        }
    )
    rows = repository.list_for_review("rev_A")
    assert len(rows) == 1
    assert rows[0]["question"] == "Why is account 555035 over budget?"
    assert rows[0]["scope"]["review_id"] == "rev_A"
    assert rows[0]["retrieved_records"] == [
        "account:rev_A:00-0245|555035"
    ]
    assert rows[0]["citations"] == ["account:rev_A:00-0245|555035"]
    assert rows[0]["latency_ms"] == 25


def test_private_audit_supports_global_application_help_without_a_review():
    connection = _connection()
    dal = SimpleNamespace(conn=connection)
    repository = PrivateAskFinAuditRepositorySqlite(
        dal,
        SqliteUnitOfWork(dal),
        id_factory=lambda: "global",
    )
    repository.append(
        {
            "timestamp": "2026-07-29T12:00:00Z",
            "user_id": "local-user",
            "review_id": "",
            "validation_run_id": None,
            "scope": None,
            "mode": "application_help",
            "question": "How do I create a review?",
            "retrieved_records": ["help::review-workflow"],
            "provider": "ollama",
            "model": "local-test:1",
            "model_version": "local-test:1",
            "prompt_version": "stage2-private-v1",
            "response": "Create a review.",
            "citations": ["help::review-workflow"],
            "refusal_trigger": None,
            "latency_ms": 25,
            "failure_state": None,
            "status": "ok",
            "grounding_review_id": "",
        }
    )
    rows = repository.list_for_review("")
    assert len(rows) == 1
    assert rows[0]["review_id"] is None
    assert rows[0]["mode"] == "application_help"


def test_private_audit_rejects_unknown_review_scope():
    connection = _connection()
    with connection:
        try:
            connection.execute(
                "INSERT INTO v2_private_ask_fin_interactions("
                "interaction_id,user_id,review_id,scope_json,mode,question,"
                "retrieved_records_json,provider,model,model_version,prompt_version,"
                "response,citations_json,status,created_at"
                ") VALUES('x','u','rev_B',NULL,'application_help','q','[]',"
                "'ollama','m','m','v1','r','[]','ok','2026-07-29T12:00:00Z')"
            )
        except sqlite3.IntegrityError:
            pass
        else:
            raise AssertionError("unknown review scope was accepted")
