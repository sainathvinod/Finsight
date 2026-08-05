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
    m0012_workspace_baseline_upgrade_governance,
)
from tests.application.test_protected_rule_governance import (
    ADMIN,
    APPROVER,
    _activate_governed_baseline,
    _admin,
    _approver,
    _confirmed_review,
)
from tests.support import persist_confirmed_validation


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
        m0011_protected_request_baseline_binding,
        m0012_workspace_baseline_upgrade_governance,
    ):
        migration.up(connection)
    return connection


def test_migration_0012_creates_append_only_integrity_ledgers():
    connection = _connection()
    tables = {
        row[0]
        for row in connection.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        )
    }
    assert {
        "v2_workspace_baseline_upgrade_requests",
        "v2_workspace_baseline_upgrade_decisions",
        "v2_workspace_baseline_upgrade_applications",
    }.issubset(tables)
    triggers = {
        row[0]
        for row in connection.execute(
            "SELECT name FROM sqlite_master WHERE type='trigger'"
        )
    }
    assert {
        "trg_v2_workspace_baseline_upgrade_requests_no_update",
        "trg_v2_workspace_baseline_upgrade_decisions_no_delete",
        "trg_v2_workspace_baseline_upgrade_applications_no_update",
        "trg_v2_workspace_upgrade_request_current_workspace",
        "trg_v2_workspace_upgrade_request_current_run",
        "trg_v2_workspace_upgrade_request_exact_source_members",
        "trg_v2_workspace_upgrade_request_effective_target",
        "trg_v2_workspace_upgrade_decision_distinct_actor",
        "trg_v2_workspace_upgrade_approval_not_stale",
        "trg_v2_workspace_upgrade_application_exact_request",
        "trg_v2_workspace_upgrade_application_exact_members",
    }.issubset(triggers)
    assert m0012_workspace_baseline_upgrade_governance.VERSION == 12


def test_migration_0012_rejects_self_decision_and_unbound_application(
    tmp_path,
):
    _database, services, review, dataset = _confirmed_review(tmp_path)
    financial = services.financial_review
    admin = _admin(financial)
    approver = _approver(financial)
    persist_confirmed_validation(financial, review.review_id, dataset)
    _activate_governed_baseline(admin, approver, review, dataset)
    request = admin.request_workspace_upgrade(
        review.review_id, "Exercise migration-level integrity guards."
    )
    connection = financial._uow.dal.conn

    with pytest.raises(Exception, match="self-approval denied"):
        connection.execute(
            "INSERT INTO v2_workspace_baseline_upgrade_decisions("
            "request_id,decision,approver_actor_id,decided_at,reason,"
            "decision_hash) VALUES(?,?,?,?,?,?)",
            (
                request["request_id"],
                "APPROVED",
                ADMIN.actor_id,
                "2026-07-28T01:00:00Z",
                "Self decision",
                "a" * 64,
            ),
        )
    connection.rollback()

    connection.execute(
        "INSERT INTO v2_workspace_baseline_upgrade_decisions("
        "request_id,decision,approver_actor_id,decided_at,reason,"
        "decision_hash) VALUES(?,?,?,?,?,?)",
        (
            request["request_id"],
            "APPROVED",
            APPROVER.actor_id,
            "2026-07-28T01:00:00Z",
            "Independent decision",
            "b" * 64,
        ),
    )
    with pytest.raises(Exception, match="workspace upgrade .* mismatch"):
        connection.execute(
            "INSERT INTO v2_workspace_baseline_upgrade_applications("
            "request_id,review_id,prior_rule_set_id,resulting_rule_set_id,"
            "source_baseline_id,target_baseline_id,applied_by_actor_id,"
            "applied_at,application_hash) VALUES(?,?,?,?,?,?,?,?,?)",
            (
                request["request_id"],
                review.review_id,
                request["requested_rule_set_id"],
                request["requested_rule_set_id"],
                request["source_baseline_id"],
                request["target_baseline_id"],
                APPROVER.actor_id,
                "2026-07-28T01:00:00Z",
                "c" * 64,
            ),
        )
    connection.rollback()
    assert financial._repo.workspace_upgrade_request(request["request_id"])[
        "status"
    ] == "PENDING_APPROVAL"
