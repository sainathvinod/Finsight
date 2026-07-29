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
)


_MIGRATIONS = (
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
)

_GUARDS = (
    "trg_v2_protected_request_exact_qualification",
    "trg_v2_protected_request_revision_lineage",
    "trg_v2_protected_activation_current_head",
    "trg_v2_protected_activation_exact_baseline",
)


def _connection(*, through_integrity: bool = True) -> sqlite3.Connection:
    connection = sqlite3.connect(":memory:")
    connection.execute("PRAGMA foreign_keys=ON")
    migrations = _MIGRATIONS if through_integrity else _MIGRATIONS[:-1]
    for migration in migrations:
        migration.up(connection)
    return connection


def _seed_candidate(
    connection: sqlite3.Connection,
    *,
    rule_id: str = "CORE-01",
    version: str = "2.0.1",
    content_hash: str = "a" * 64,
) -> None:
    connection.execute(
        "INSERT INTO v2_rule_definition_versions("
        "rule_id,version,classification,name,purpose,severity,baseline_status,"
        "evaluator_key,parameters_json,required_fields_json,grouping_keys_json,"
        "predecessor_version,created_by,created_at,content_hash"
        ") VALUES(?,?,'CORE_MANDATORY','Governed successor','Changed','High',"
        "'PROTECTED_BASELINE','actual_not_over_budget','{}','[]','[]','2.0.0',"
        "'actor-admin','2026-07-28T00:00:00Z',?)",
        (rule_id, version, content_hash),
    )
    for ordinal, status in ((1, "DRAFT"), (2, "TESTED")):
        connection.execute(
            "INSERT INTO v2_rule_lifecycle_events("
            "event_id,rule_id,rule_version,ordinal,status,actor_id,occurred_at,"
            "reason,event_hash) VALUES(?,?,?,?,?,'actor-admin',"
            "'2026-07-28T00:00:00Z','qualification',?)",
            (
                f"evt-{rule_id}-{version}-{ordinal}",
                rule_id,
                version,
                ordinal,
                status,
                f"{ordinal}" * 64,
            ),
        )


def _insert_request(
    connection: sqlite3.Connection,
    *,
    request_id: str,
    test_id: str,
    evidence_hash: str,
    content_hash: str = "a" * 64,
) -> None:
    connection.execute(
        "INSERT INTO v2_protected_change_requests("
        "request_id,rule_id,predecessor_version,candidate_version,"
        "change_kind,requested_action,reason,proposed_effective_at,"
        "requester_actor_id,requested_at,candidate_content_hash,"
        "evidence_context_hash,before_definition_json,after_definition_json,"
        "test_id,prior_request_id,initial_status"
        ") VALUES(?,'CORE-01','2.0.0','2.0.1','SEMANTIC','REPLACE','Reason',"
        "'2026-07-28T00:00:00Z','actor-admin','2026-07-28T00:00:00Z',?,?,"
        "'{}','{}',?,NULL,'PENDING_APPROVAL')",
        (request_id, content_hash, evidence_hash, test_id),
    )


def _seed_correct_request(connection: sqlite3.Connection) -> None:
    _seed_candidate(connection)
    connection.execute(
        "INSERT INTO v2_protected_candidate_tests("
        "test_id,rule_id,rule_version,evidence_context_hash,dataset_fingerprint,"
        "status,metrics_json,ledger_hash,actor_id,tested_at"
        ") VALUES('test-correct','CORE-01','2.0.1',?,?,'COMPLETE','{}',?,"
        "'actor-admin','2026-07-28T00:00:00Z')",
        ("d" * 64, "e" * 64, "f" * 64),
    )
    _insert_request(
        connection,
        request_id="request-correct",
        test_id="test-correct",
        evidence_hash="d" * 64,
    )
    connection.execute(
        "INSERT INTO v2_protected_change_decisions("
        "request_id,decision,approver_actor_id,decided_at,reason,decision_hash"
        ") VALUES('request-correct','APPROVED','actor-approver',"
        "'2026-07-28T01:00:00Z','Approved',?)",
        ("9" * 64,),
    )
    connection.execute(
        "INSERT INTO v2_core_rule_versions("
        "rule_id,version,name,severity,baseline_status,evaluator_key,created_at"
        ") VALUES('CORE-01','2.0.1','Governed successor','High',"
        "'PROTECTED_BASELINE','actual_not_over_budget','2026-07-28T01:00:00Z')"
    )


def test_migration_0010_backfills_guards_after_0009_was_already_applied():
    connection = _connection(through_integrity=False)
    for name in _GUARDS:
        connection.execute(f"DROP TRIGGER IF EXISTS {name}")

    m0010_protected_core_governance_integrity.up(connection)

    triggers = {
        row[0]
        for row in connection.execute(
            "SELECT name FROM sqlite_master WHERE type='trigger'"
        )
    }
    assert set(_GUARDS).issubset(triggers)
    assert m0010_protected_core_governance_integrity.VERSION == 10


@pytest.mark.parametrize(
    ("test_rule", "test_version", "test_evidence", "request_evidence"),
    (
        ("CORE-02", "2.0.0", "d" * 64, "d" * 64),
        ("CORE-01", "2.0.1", "d" * 64, "e" * 64),
    ),
)
def test_request_requires_exact_rule_version_and_evidence_qualification(
    test_rule: str,
    test_version: str,
    test_evidence: str,
    request_evidence: str,
):
    connection = _connection()
    _seed_candidate(connection)
    connection.execute(
        "INSERT INTO v2_protected_candidate_tests("
        "test_id,rule_id,rule_version,evidence_context_hash,dataset_fingerprint,"
        "status,metrics_json,ledger_hash,actor_id,tested_at"
        ") VALUES('test-mismatch',?,?,?,?,'COMPLETE','{}',?,'actor-admin',"
        "'2026-07-28T00:00:00Z')",
        (
            test_rule,
            test_version,
            test_evidence,
            "7" * 64,
            "8" * 64,
        ),
    )

    with pytest.raises(
        sqlite3.IntegrityError, match="qualification mismatch"
    ):
        _insert_request(
            connection,
            request_id="request-mismatch",
            test_id="test-mismatch",
            evidence_hash=request_evidence,
        )


def test_activation_requires_current_head_and_exact_five_member_baseline():
    connection = _connection()
    _seed_correct_request(connection)
    connection.execute(
        "INSERT INTO v2_core_rule_set_versions("
        "rule_set_id,version,status,created_at"
        ") VALUES('bad-baseline','2.0.1','PROTECTED_BASELINE',"
        "'2026-07-28T01:00:00Z')"
    )
    connection.execute(
        "INSERT INTO v2_core_rule_set_members("
        "rule_set_id,ordinal,rule_id,rule_version"
        ") SELECT 'bad-baseline',ordinal,rule_id,rule_version "
        "FROM v2_core_rule_set_members "
        "WHERE rule_set_id='FINSIGHT-CORE-2.0'"
    )

    with pytest.raises(
        sqlite3.IntegrityError, match="baseline mismatch"
    ):
        connection.execute(
            "INSERT INTO v2_protected_change_activations("
            "request_id,prior_baseline_id,resulting_baseline_id,"
            "activated_rule_id,activated_rule_version,activated_at,"
            "activation_hash) VALUES('request-correct','FINSIGHT-CORE-2.0',"
            "'bad-baseline','CORE-01','2.0.1','2026-07-28T01:00:00Z',?)",
            ("0" * 64,),
        )

    connection.execute(
        "INSERT INTO v2_core_rule_set_versions("
        "rule_set_id,version,status,created_at"
        ") VALUES('candidate-baseline','2.0.2','PROTECTED_BASELINE',"
        "'2026-07-28T01:00:00Z')"
    )
    connection.execute(
        "INSERT INTO v2_core_rule_set_members("
        "rule_set_id,ordinal,rule_id,rule_version"
        ") SELECT 'candidate-baseline',ordinal,rule_id,"
        "CASE WHEN rule_id='CORE-01' THEN '2.0.1' ELSE rule_version END "
        "FROM v2_core_rule_set_members "
        "WHERE rule_set_id='FINSIGHT-CORE-2.0'"
    )
    with pytest.raises(
        sqlite3.IntegrityError, match="predecessor mismatch"
    ):
        connection.execute(
            "INSERT INTO v2_protected_change_activations("
            "request_id,prior_baseline_id,resulting_baseline_id,"
            "activated_rule_id,activated_rule_version,activated_at,"
            "activation_hash) VALUES('request-correct','FINSIGHT-CORE-1.0',"
            "'candidate-baseline','CORE-01','2.0.1',"
            "'2026-07-28T01:00:00Z',?)",
            ("1" * 64,),
        )
