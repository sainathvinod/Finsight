from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime, timezone
import json

import pytest

from finsight.app import build_query_services
from finsight.application.rule_management import (
    RuleManagementError,
    RuleManagementService,
)
from finsight.application.review_management import ReviewAuthorizationError
from finsight.application.security import AuthorizationContext
from finsight.application.security import (
    AuthorizationAssignment,
    AuthorizationPolicySnapshot,
    IdentityResolution,
    StaticRoleAssignmentSource,
    default_mvp_policy,
)
from finsight.domain.identity import Actor, Permission, Role
from finsight.domain.source_intake import SourceRole
from finsight.infrastructure.financial_review_repository import (
    FinancialReviewRepositorySqlite,
)
from finsight.infrastructure.identity import FixedIdentityProvider
from finsight.infrastructure.persistence import Dal
from finsight.infrastructure.secure_store import (
    TestEnvironmentStoreKeyProvider,
)
from tests.support import FixedClock, persist_confirmed_validation


FIXTURES = "initiatives/configurable-rule-engine-v2/fixtures"
ADMIN = Actor("TEST:rule-admin", "Rule Administrator", "TEST_IDP")
APPROVER = Actor("TEST:control-approver", "Financial Control Approver", "TEST_IDP")
UNAUTHORIZED = Actor("TEST:reviewer", "Reviewer", "TEST_IDP")
_WORKSPACE_AUDIT_COMMON_FIELDS = {
    "event_schema",
    "transition",
    "requested_action",
    "protected_rule_id_set",
    "outcome",
    "reason",
    "request_id",
    "workspace_id",
    "target_protected_baseline_id",
    "target_protected_baseline_version",
    "requester_actor_id",
    "request_timestamp",
}
_WORKSPACE_AUDIT_PROPOSAL_FIELDS = {
    "before_rule_definition",
    "before_rule_configuration",
    "before_binding",
    "old_rule_version",
    "proposed_after_rule_definition",
    "proposed_after_rule_configuration",
    "proposed_after_binding",
    "proposed_successor_rule_version",
    "proposed_effective_time",
}
_WORKSPACE_REQUEST_AUDIT_FIELDS = (
    _WORKSPACE_AUDIT_COMMON_FIELDS
    | _WORKSPACE_AUDIT_PROPOSAL_FIELDS
    | {
        "approver_actor_id",
        "decision_timestamp",
        "decision_reason",
        "activation_timestamp",
        "prior_protected_baseline_version",
        "resulting_protected_baseline_version",
        "activation_outcome",
    }
)
_WORKSPACE_REJECTION_AUDIT_FIELDS = (
    _WORKSPACE_AUDIT_COMMON_FIELDS
    | _WORKSPACE_AUDIT_PROPOSAL_FIELDS
    | {
        "approver_actor_id",
        "decision_timestamp",
        "decision_reason",
        "decision_outcome",
        "activation_timestamp",
        "prior_protected_baseline_version",
        "resulting_protected_baseline_version",
        "activation_outcome",
    }
)
_WORKSPACE_APPLICATION_AUDIT_FIELDS = (
    _WORKSPACE_AUDIT_COMMON_FIELDS
    | {
        "source_protected_baseline_id",
        "source_protected_baseline_version",
        "prior_workspace_rule_set_id",
        "prior_workspace_rule_set_version",
        "resulting_workspace_rule_set_id",
        "resulting_workspace_rule_set_version",
        "prior_binding",
        "resulting_binding",
        "authorizing_financial_control_approver_actor_id",
        "authorization_timestamp",
        "activation_timestamp",
        "activation_outcome",
        "before_rule_definition",
        "after_rule_definition",
        "proposed_successor_rule_version",
    }
)


def _assert_no_blank_audit_value(value):
    assert value is not None
    if isinstance(value, str):
        assert value.strip()
    elif isinstance(value, dict):
        for nested in value.values():
            _assert_no_blank_audit_value(nested)
    elif isinstance(value, list):
        for nested in value:
            _assert_no_blank_audit_value(nested)


def _expected_workspace_audit_fields(transition):
    return {
        "REQUESTED": _WORKSPACE_REQUEST_AUDIT_FIELDS,
        "REJECTED": _WORKSPACE_REJECTION_AUDIT_FIELDS,
        "APPROVED_AND_APPLIED": _WORKSPACE_APPLICATION_AUDIT_FIELDS,
    }[transition]


def _expected_workspace_audit_schema(transition):
    return {
        "REQUESTED": "NFR-090_PROTECTED_REQUEST_SUBMITTED_V1",
        "REJECTED": "NFR-090_PROTECTED_TERMINAL_DECISION_V1",
        "APPROVED_AND_APPLIED": (
            "NFR-090_EXISTING_WORKSPACE_BASELINE_UPGRADE_V1"
        ),
    }[transition]


_WORKSPACE_APPLICATION_NA_FIELDS = {
    "before_rule_definition",
    "after_rule_definition",
    "proposed_successor_rule_version",
}
_WORKSPACE_REQUEST_NA_FIELDS = {
    "approver_actor_id",
    "decision_timestamp",
    "decision_reason",
    "activation_timestamp",
    "prior_protected_baseline_version",
    "resulting_protected_baseline_version",
    "activation_outcome",
}
_WORKSPACE_REJECTION_NA_FIELDS = {
    "activation_timestamp",
    "prior_protected_baseline_version",
    "resulting_protected_baseline_version",
    "activation_outcome",
}


def _expected_workspace_na_fields(transition):
    return {
        "REQUESTED": _WORKSPACE_REQUEST_NA_FIELDS,
        "REJECTED": _WORKSPACE_REJECTION_NA_FIELDS,
        "APPROVED_AND_APPLIED": _WORKSPACE_APPLICATION_NA_FIELDS,
    }[transition]


def _assert_workspace_audit_event(
    event,
    *,
    request,
    transition,
    actor_id,
    outcome,
):
    assert event.event_id
    assert event.occurred_at
    assert event.actor_id == actor_id
    assert event.outcome == outcome
    payload = event.payload
    assert set(payload) == _expected_workspace_audit_fields(transition)
    assert payload["event_schema"] == _expected_workspace_audit_schema(
        transition
    )
    assert payload["transition"] == transition
    assert payload["requested_action"] == (
        "APPLY_PROTECTED_BASELINE_TO_EXISTING_WORKSPACE"
    )
    assert payload["protected_rule_id_set"] == [
        "CORE-01",
        "CORE-02",
        "CORE-03",
        "CORE-04",
        "CORE-05",
    ]
    assert payload["outcome"] == outcome
    assert payload["request_id"] == request["request_id"]
    assert payload["workspace_id"] == request["review_id"]
    assert payload["target_protected_baseline_id"] == request[
        "target_baseline_id"
    ]
    assert payload["target_protected_baseline_version"] == request[
        "target_baseline_version"
    ]
    assert payload["requester_actor_id"] == request["requester_actor_id"]
    assert payload["request_timestamp"] == request["requested_at"]
    assert {
        key for key, value in payload.items() if value == "N/A"
    } == _expected_workspace_na_fields(transition)
    _assert_no_blank_audit_value(payload)


def _confirmed_review(tmp_path):
    database = tmp_path / "protected-governance.db"
    services = build_query_services(str(database), clock=FixedClock())
    review = services.review_management.create_review(
        5, 2026, idempotency_key="create-protected-governance"
    )
    budget = services.source_intake.inspect(
        f"{FIXTURES}/Sample_Budget_Report.xlsx", SourceRole.BUDGET
    )
    ged = services.source_intake.inspect(
        f"{FIXTURES}/Sample_GED_Report.xlsx", SourceRole.GED
    )
    pair = services.source_intake.evaluate(
        budget=budget, ged=ged, selected_period=review.period
    )
    services.review_management.commit_source_intake(
        review.review_id,
        pair,
        idempotency_key="protected-governance-sources",
    )
    dataset = services.financial_review.reconstruct_dataset(review.review_id)
    services.financial_review.confirm_reviewed_data(
        review.review_id,
        dataset,
        attestation_text="Reviewed for protected governance tests.",
    )
    return database, services, review, dataset


@dataclass
class _Gate:
    actor: Actor
    permissions: frozenset[Permission]
    uow: object

    def require(
        self,
        permission: Permission,
        context: AuthorizationContext | None = None,
    ) -> None:
        if permission not in self.permissions:
            raise PermissionError(f"{permission.value} is not granted")
        if (
            permission
            in {
                Permission.RULE_PROTECTED_CHANGE_DECIDE,
                Permission.RULE_PROTECTED_WORKSPACE_UPGRADE_AUTHORIZE,
            }
            and context is not None
            and context.protected_requester_actor_id == self.actor.actor_id
        ):
            raise PermissionError("protected request self-approval denied")

    def execute(
        self,
        permission: Permission,
        operation,
        context: AuthorizationContext | None = None,
    ):
        self.require(permission, context)
        with self.uow.atomic():
            return operation()


def _service(financial, actor: Actor, *permissions: Permission):
    gate = _Gate(actor, frozenset(permissions), financial._uow)
    return RuleManagementService(
        repository=financial._repo,
        unit_of_work=financial._uow,
        audit_stream=financial._audit,
        engine=financial._engine,
        actor=actor,
        clock=financial._clock,
        authorizer=gate.require,
        authorization_executor=gate.execute,
    )


def _admin(financial, actor: Actor = ADMIN):
    return _service(
        financial,
        actor,
        Permission.RULE_PROTECTED_DRAFT_MANAGE,
        Permission.RULE_PROTECTED_CHANGE_REQUEST,
        Permission.RULE_PROTECTED_CHANGE_DECIDE,
        Permission.RULE_OPTIONAL_DRAFT_MANAGE,
        Permission.RULE_OPTIONAL_LIFECYCLE_MANAGE,
        Permission.RULE_PROTECTED_WORKSPACE_UPGRADE_REQUEST,
        Permission.RULE_PROTECTED_WORKSPACE_UPGRADE_AUTHORIZE,
    )


def _approver(financial, actor: Actor = APPROVER):
    return _service(
        financial,
        actor,
        Permission.RULE_PROTECTED_CHANGE_DECIDE,
        Permission.RULE_PROTECTED_WORKSPACE_UPGRADE_AUTHORIZE,
    )


def _proposal(**overrides):
    value = {
        "rule_id": "CORE-01",
        "proposed_version": "2.0.1",
        "change_kind": "SEMANTIC",
        "name": "Budget Overrun",
        "purpose": (
            "Total GED actual spending must not exceed BGT for the same "
            "Department Number + Account Number, with governed exception evidence."
        ),
        "severity": "High",
        "parameters": {},
        "reason": "Clarify the protected control evidence required by Finance.",
    }
    value.update(overrides)
    return value


def _submit(admin, review, dataset, **overrides):
    return admin.submit_protected_change_request(
        review_id=review.review_id,
        dataset=dataset,
        **_proposal(**overrides),
    )


def test_protected_request_is_tested_immutable_and_does_not_change_baseline(
    tmp_path,
):
    _database, services, review, dataset = _confirmed_review(tmp_path)
    financial = services.financial_review
    admin = _admin(financial)
    baseline_before = financial._repo.current_protected_baseline_id()

    request = _submit(admin, review, dataset)

    assert request["status"] == "PENDING_APPROVAL"
    assert request["requester_actor_id"] == ADMIN.actor_id
    assert request["reason"] == _proposal()["reason"]
    assert request["candidate_version"] == "2.0.1"
    assert request["change_kind"] == "SEMANTIC"
    assert financial._repo.current_protected_baseline_id() == baseline_before
    candidate = financial._repo.rule_version("CORE-01", "2.0.1")
    assert candidate["lifecycle_status"] == "TESTED"
    assert candidate["content_hash"] == request["candidate_content_hash"]
    qualification_metrics = json.loads(
        financial._uow.dal.conn.execute(
            "SELECT metrics_json FROM v2_protected_candidate_tests "
            "WHERE test_id=?",
            (request["test_id"],),
        ).fetchone()[0]
    )
    qualification = qualification_metrics["qualification"]
    assert (
        qualification["suite_id"]
        == "FINSIGHT-MVP-CORE-EVALUATOR-SUITE-2.0.0"
    )
    assert qualification["candidate_dataset_evaluation"]["pass_count"] > 0
    assert all(qualification["checks"].values())
    assert "eligibility_cases" not in qualification_metrics
    with pytest.raises(Exception, match="append-only"):
        financial._uow.dal.conn.execute(
            "UPDATE v2_protected_change_requests SET reason='rewritten' "
            "WHERE request_id=?",
            (request["request_id"],),
        )
    financial._uow.dal.conn.rollback()


def test_protected_request_rejects_unconfirmed_or_empty_dataset(tmp_path):
    _database, services, review, dataset = _confirmed_review(tmp_path)
    financial = services.financial_review
    empty = replace(dataset, budget_records=(), ged_records=())

    with pytest.raises(
        RuleManagementError, match="confirmed working dataset"
    ):
        _submit(_admin(financial), review, empty)

    assert financial._repo.rule_version("CORE-01", "2.0.1") is None
    assert financial._repo.list_protected_change_requests() == []


def test_different_approver_activates_successor_without_rebinding_old_workspace(
    tmp_path,
):
    _database, services, review, dataset = _confirmed_review(tmp_path)
    financial = services.financial_review
    old_rule_set_id = financial._repo.current_rule_set_id(review.review_id)
    old_manifest = financial.rule_manifest(review.review_id)
    request = _submit(_admin(financial), review, dataset)

    approved = _approver(financial).decide_protected_change(
        request["request_id"],
        decision="APPROVED",
        reason="Independent Finance Control review completed.",
    )

    assert approved["status"] == "APPROVED"
    assert approved["approver_actor_id"] == APPROVER.actor_id
    assert approved["resulting_baseline_id"] != old_manifest.protected_baseline_id
    assert (
        financial._repo.current_protected_baseline_id()
        == approved["resulting_baseline_id"]
    )
    assert financial._repo.current_rule_set_id(review.review_id) == old_rule_set_id
    replay = financial.rule_manifest(review.review_id)
    assert replay.protected_baseline_id == old_manifest.protected_baseline_id
    assert next(
        item.version for item in replay.rules if item.rule_id == "CORE-01"
    ) == "2.0.0"
    assert (
        financial._repo.rule_version("CORE-01", "2.0.0")[
            "lifecycle_status"
        ]
        == "RETIRED"
    )
    assert (
        financial._repo.rule_version("CORE-01", "2.0.1")[
            "lifecycle_status"
        ]
        == "ACTIVE"
    )
    governance_events = financial._audit.events(
        stream_type="RULE_GOVERNANCE"
    )
    assert [
        event.event_type
        for event in governance_events
        if event.event_type.startswith("protected_change")
    ] == [
        "protected_change_requested",
        "protected_change_approved_and_activated",
    ]
    assert governance_events[-1].actor_id == APPROVER.actor_id

    new_review = services.review_management.create_review(
        6, 2026, idempotency_key="new-review-after-protected-approval"
    )
    with financial._uow.atomic():
        new_rule_set_id = financial._repo.ensure_initial_rule_set(
            new_review.review_id,
            actor_id=APPROVER.actor_id,
            created_at=FixedClock().now(),
        )
    new_manifest = financial._repo.rule_set_manifest(new_rule_set_id)
    assert new_manifest.protected_baseline_id == approved["resulting_baseline_id"]
    assert next(
        item.version
        for item in new_manifest.rules
        if item.rule_id == "CORE-01"
    ) == "2.0.1"


def test_pending_request_cannot_merge_with_a_newer_protected_baseline(
    tmp_path,
):
    _database, services, review, dataset = _confirmed_review(tmp_path)
    financial = services.financial_review
    first = _submit(_admin(financial), review, dataset)
    second = _submit(
        _admin(financial),
        review,
        dataset,
        rule_id="CORE-02",
        name="Valid Account Coding",
        purpose=(
            "Every GED Department Number + Account Number combination must "
            "exist in the Budget report, with governed evidence."
        ),
    )

    _approver(financial).decide_protected_change(
        second["request_id"],
        decision="APPROVED",
        reason="Independent Finance Control review completed.",
    )

    with pytest.raises(
        RuleManagementError, match="baseline changed after this request"
    ):
        _approver(financial).decide_protected_change(
            first["request_id"],
            decision="APPROVED",
            reason="This request was qualified against the prior baseline.",
        )
    preserved = financial._repo.protected_change_request(first["request_id"])
    assert preserved["status"] == "PENDING_APPROVAL"
    assert (
        preserved["requested_baseline_id"]
        != financial._repo.current_protected_baseline_id()
    )


def test_stale_pending_request_can_still_be_terminally_rejected(tmp_path):
    _database, services, review, dataset = _confirmed_review(tmp_path)
    financial = services.financial_review
    first = _submit(_admin(financial), review, dataset)
    second = _submit(
        _admin(financial),
        review,
        dataset,
        rule_id="CORE-02",
        name="Valid Account Coding",
        purpose=(
            "Every GED Department Number + Account Number combination must "
            "exist in the Budget report, with governed evidence."
        ),
    )
    approver = _approver(financial)
    approver.decide_protected_change(
        second["request_id"],
        decision="APPROVED",
        reason="Independent Finance Control review completed.",
    )

    rejected = approver.decide_protected_change(
        first["request_id"],
        decision="REJECTED",
        reason="The candidate was qualified against a superseded baseline.",
    )

    assert rejected["status"] == "REJECTED"
    assert rejected["decision_reason"].startswith(
        "The candidate was qualified"
    )
    assert rejected["resulting_baseline_id"] is None


def test_self_approval_and_unauthorized_actions_fail_closed(tmp_path):
    _database, services, review, dataset = _confirmed_review(tmp_path)
    financial = services.financial_review
    request = _submit(_admin(financial), review, dataset)

    with pytest.raises(
        RuleManagementError, match="cannot approve or reject their own"
    ):
        _admin(financial).decide_protected_change(
            request["request_id"],
            decision="APPROVED",
            reason="Attempted self approval.",
        )
    assert (
        financial._repo.protected_change_request(request["request_id"])[
            "status"
        ]
        == "PENDING_APPROVAL"
    )

    reviewer = _service(financial, UNAUTHORIZED)
    with pytest.raises(PermissionError, match="not granted"):
        _submit(
            reviewer,
            review,
            dataset,
            proposed_version="2.0.2",
        )
    with pytest.raises(PermissionError, match="not granted"):
        reviewer.decide_protected_change(
            request["request_id"],
            decision="REJECTED",
            reason="Unauthorized decision.",
        )
    assert financial._repo.rule_version("CORE-01", "2.0.2") is None


def test_rejection_is_terminal_and_preserves_active_baseline(tmp_path):
    _database, services, review, dataset = _confirmed_review(tmp_path)
    financial = services.financial_review
    baseline_before = financial._repo.current_protected_baseline_id()
    request = _submit(_admin(financial), review, dataset)

    rejected = _approver(financial).decide_protected_change(
        request["request_id"],
        decision="REJECTED",
        reason="The proposed wording does not meet control policy.",
    )

    assert rejected["status"] == "REJECTED"
    assert rejected["resulting_baseline_id"] is None
    assert financial._repo.current_protected_baseline_id() == baseline_before
    assert (
        financial._repo.rule_version("CORE-01", "2.0.1")[
            "lifecycle_status"
        ]
        == "TESTED"
    )
    with pytest.raises(RuleManagementError, match="terminal decision"):
        _approver(financial).decide_protected_change(
            request["request_id"],
            decision="APPROVED",
            reason="A later approval must not replace the rejection.",
        )


def test_revised_request_must_link_to_same_protected_rule(tmp_path):
    _database, services, review, dataset = _confirmed_review(tmp_path)
    financial = services.financial_review
    first = _submit(_admin(financial), review, dataset)
    _approver(financial).decide_protected_change(
        first["request_id"],
        decision="REJECTED",
        reason="Retain the original wording.",
    )

    with pytest.raises(RuleManagementError, match="same protected rule"):
        _submit(
            _admin(financial),
            review,
            dataset,
            rule_id="CORE-02",
            name="Valid Account Coding",
            purpose=(
                "Every GED Department Number + Account Number combination "
                "must exist in the Budget report, with clarified evidence."
            ),
            prior_request_id=first["request_id"],
        )

    assert financial._repo.rule_version("CORE-02", "2.0.1") is None


@pytest.mark.parametrize("version", ["2.0.0", "1.9.9", "not-a-version"])
def test_proposed_version_boundary_must_advance(version, tmp_path):
    _database, services, review, dataset = _confirmed_review(tmp_path)
    financial = services.financial_review

    with pytest.raises(RuleManagementError, match="must be later"):
        _submit(
            _admin(financial),
            review,
            dataset,
            proposed_version=version,
        )

    assert financial._repo.list_protected_change_requests() == []


def test_unapproved_parameter_change_fails_closed_without_candidate_or_request(
    tmp_path,
):
    _database, services, review, dataset = _confirmed_review(tmp_path)
    financial = services.financial_review

    with pytest.raises(
        RuleManagementError, match="No configurable parameters are approved"
    ):
        _submit(
            _admin(financial),
            review,
            dataset,
            change_kind="PARAMETER",
            purpose=(
                "Total GED actual spending must not exceed BGT for the same "
                "Department Number + Account Number."
            ),
            parameters={"rounding_policy": "CENTS_EXACT"},
        )

    assert financial._repo.rule_version("CORE-01", "2.0.1") is None
    assert financial._repo.list_protected_change_requests() == []


def test_governance_history_survives_restart(tmp_path):
    database, services, review, dataset = _confirmed_review(tmp_path)
    financial = services.financial_review
    request = _submit(_admin(financial), review, dataset)
    approved = _approver(financial).decide_protected_change(
        request["request_id"],
        decision="APPROVED",
        reason="Approved for persisted restart verification.",
    )
    financial._uow.dal.conn.close()

    reopened = Dal(
        str(database), key_provider=TestEnvironmentStoreKeyProvider()
    )
    try:
        repository = FinancialReviewRepositorySqlite(reopened)
        persisted = repository.protected_change_request(request["request_id"])
        assert persisted["status"] == "APPROVED"
        assert persisted["requester_actor_id"] == ADMIN.actor_id
        assert persisted["approver_actor_id"] == APPROVER.actor_id
        assert (
            repository.current_protected_baseline_id()
            == approved["resulting_baseline_id"]
        )
        assert repository.rule_version("CORE-01", "2.0.0") is not None
        assert repository.rule_version("CORE-01", "2.0.1") is not None
    finally:
        reopened.conn.close()


def test_review_disposal_does_not_erase_global_governance_history(tmp_path):
    _database, services, review, dataset = _confirmed_review(tmp_path)
    financial = services.financial_review
    request = _submit(_admin(financial), review, dataset)
    _approver(financial).decide_protected_change(
        request["request_id"],
        decision="REJECTED",
        reason="Rejected but retained as global governance evidence.",
    )

    preview = services.review_management.prepare_disposal(review.review_id)
    services.review_management.confirm_disposal(
        review.review_id, preview.confirmation_token
    )

    retained = financial._repo.protected_change_request(
        request["request_id"]
    )
    assert retained["status"] == "REJECTED"
    assert retained["evidence_context_hash"]
    assert financial._repo.rule_version("CORE-01", "2.0.1") is not None


def test_composed_live_rbac_allows_only_distinct_effective_approver(tmp_path):
    database = tmp_path / "composed-protected-governance.db"
    effective_from = datetime(2020, 1, 1, tzinfo=timezone.utc)
    assigned_at = datetime(2019, 12, 1, tzinfo=timezone.utc)
    snapshot = AuthorizationPolicySnapshot(
        source_kind="TEST_POLICY",
        version="protected-governance-1",
        fingerprint="9" * 64,
        policy=default_mvp_policy(),
        assignments=(
            AuthorizationAssignment(
                assignment_id="rule-admin",
                actor_id=ADMIN.actor_id,
                actor_source=ADMIN.source,
                allow_roles=frozenset(
                    {Role.REVIEWER, Role.RULE_ADMINISTRATOR}
                ),
                effective_from=effective_from,
                assigning_actor_id="security-admin",
                assigned_at=assigned_at,
            ),
            AuthorizationAssignment(
                assignment_id="control-approver",
                actor_id=APPROVER.actor_id,
                actor_source=APPROVER.source,
                allow_roles=frozenset(
                    {Role.FINANCIAL_CONTROL_APPROVER}
                ),
                effective_from=effective_from,
                assigning_actor_id="security-admin",
                assigned_at=assigned_at,
            ),
        ),
    )
    assignments = StaticRoleAssignmentSource(snapshot)
    admin_services = build_query_services(
        str(database),
        clock=FixedClock(),
        identity_provider=FixedIdentityProvider(
            IdentityResolution.resolved(ADMIN)
        ),
        role_assignment_source=assignments,
    )
    review = admin_services.review_management.create_review(
        5, 2026, idempotency_key="composed-protected-review"
    )
    budget = admin_services.source_intake.inspect(
        f"{FIXTURES}/Sample_Budget_Report.xlsx", SourceRole.BUDGET
    )
    ged = admin_services.source_intake.inspect(
        f"{FIXTURES}/Sample_GED_Report.xlsx", SourceRole.GED
    )
    pair = admin_services.source_intake.evaluate(
        budget=budget, ged=ged, selected_period=review.period
    )
    admin_services.review_management.commit_source_intake(
        review.review_id,
        pair,
        idempotency_key="composed-protected-sources",
    )
    dataset = admin_services.financial_review.reconstruct_dataset(
        review.review_id
    )
    admin_services.financial_review.confirm_reviewed_data(
        review.review_id,
        dataset,
        attestation_text="Reviewed for composed authorization.",
    )
    request = admin_services.rule_management.submit_protected_change_request(
        review_id=review.review_id,
        dataset=dataset,
        **_proposal(),
    )
    request_authorization = (
        admin_services.financial_review._uow.dal.conn.execute(
            "SELECT decision,authorization_fingerprint,"
            "effective_assignment_ids FROM v2_authorization_decision_events "
            "WHERE permission=? ORDER BY rowid DESC LIMIT 1",
            (Permission.RULE_PROTECTED_CHANGE_REQUEST.value,),
        ).fetchone()
    )
    assert request_authorization is not None
    assert request_authorization[0] == "ALLOW"
    assert request_authorization[1] == snapshot.fingerprint
    assert "rule-admin" in json.loads(request_authorization[2])
    admin_services.financial_review._uow.dal.conn.close()

    approver_services = build_query_services(
        str(database),
        clock=FixedClock(),
        identity_provider=FixedIdentityProvider(
            IdentityResolution.resolved(APPROVER)
        ),
        role_assignment_source=assignments,
    )
    try:
        approved = approver_services.rule_management.decide_protected_change(
            request["request_id"],
            decision="APPROVED",
            reason="Approved through the composed live policy boundary.",
        )
        assert approved["status"] == "APPROVED"
        assert approved["approver_actor_id"] == APPROVER.actor_id
        decision_authorization = (
            approver_services.financial_review._uow.dal.conn.execute(
                "SELECT decision,authorization_fingerprint,"
                "effective_assignment_ids "
                "FROM v2_authorization_decision_events "
                "WHERE permission=? ORDER BY rowid DESC LIMIT 1",
                (Permission.RULE_PROTECTED_CHANGE_DECIDE.value,),
            ).fetchone()
        )
        assert decision_authorization is not None
        assert decision_authorization[0] == "ALLOW"
        assert decision_authorization[1] == snapshot.fingerprint
        assert "control-approver" in json.loads(
            decision_authorization[2]
        )
    finally:
        approver_services.financial_review._uow.dal.conn.close()


def _activate_governed_baseline(admin, approver, review, dataset):
    request = _submit(admin, review, dataset)
    return approver.decide_protected_change(
        request["request_id"],
        decision="APPROVED",
        reason="Independent Finance Control approval for workspace-upgrade tests.",
    )


def test_workspace_upgrade_preserves_optional_members_history_and_other_workspaces(
    tmp_path,
):
    _database, services, review, dataset = _confirmed_review(tmp_path)
    financial = services.financial_review
    admin = _admin(financial)
    approver = _approver(financial)

    draft = admin.create_optional_draft(
        name="Large Transaction Review",
        purpose="Require each GED Amount to remain within the configured limit.",
        severity="Medium",
        operator="LTE",
        threshold="1000000.00",
    )
    admin.test_draft(
        review.review_id, dataset, draft["rule_id"], draft["version"]
    )
    admin.activate_optional_version(
        review.review_id, draft["rule_id"], draft["version"]
    )
    admin.set_optional_enabled(review.review_id, draft["rule_id"], False)
    initial = persist_confirmed_validation(
        financial, review.review_id, dataset
    )
    prior_rule_set_id = financial._repo.current_rule_set_id(review.review_id)
    prior_members = financial._repo.rule_set_members(prior_rule_set_id)
    prior_history = financial._repo.rule_set_history(review.review_id)

    other = services.review_management.create_review(
        6, 2026, idempotency_key="workspace-upgrade-other-review"
    )
    with financial._uow.atomic():
        other_rule_set_id = financial._repo.ensure_initial_rule_set(
            other.review_id,
            actor_id=ADMIN.actor_id,
            created_at=FixedClock().now(),
        )
        financial._uow.dal.conn.execute(
            "UPDATE v2_review_cycle_pointers "
            "SET current_rule_set_id=?,revision=revision+1 WHERE review_id=?",
            (other_rule_set_id, other.review_id),
        )
    target = _activate_governed_baseline(
        admin, approver, review, dataset
    )["resulting_baseline_id"]

    candidates = admin.list_workspace_upgrade_candidates()
    selected = next(
        item for item in candidates if item["review_id"] == review.review_id
    )
    other_candidate = next(
        item for item in candidates if item["review_id"] == other.review_id
    )
    assert selected["upgrade_state"] == "UPGRADE_AVAILABLE"
    assert selected["latest_run_id"] == initial["run_id"]
    assert other_candidate["upgrade_state"] == "NOT_ELIGIBLE"
    assert set(selected).isdisjoint(
        {"department_number", "department_name", "budget_filename", "ged_filename"}
    )

    request = admin.request_workspace_upgrade(
        review.review_id,
        "Adopt the currently effective protected baseline for this workspace.",
        target_baseline_id=target,
    )
    assert request["request_type"] == "WORKSPACE_BASELINE_UPGRADE"
    assert request["requested_rule_set_id"] == prior_rule_set_id
    assert request["requested_run_id"] == initial["run_id"]
    assert request["target_baseline_id"] == target
    assert request["status"] == "PENDING_APPROVAL"
    assert request["state"] == "PENDING_APPROVAL"
    assert request["protected_rule_ids"] == [
        "CORE-01",
        "CORE-02",
        "CORE-03",
        "CORE-04",
        "CORE-05",
    ]
    assert len(request["protected_member_changes"]) == 5
    assert request["preserved_optional_advisory_binding_count"] == 1
    assert request["preserved_optional_advisory_rule_ids"] == [
        draft["rule_id"]
    ]

    with pytest.raises(Exception, match="append-only"):
        financial._uow.dal.conn.execute(
            "UPDATE v2_workspace_baseline_upgrade_requests "
            "SET reason='mutated' WHERE request_id=?",
            (request["request_id"],),
        )
    financial._uow.dal.conn.rollback()

    approved = approver.decide_workspace_upgrade(
        request["request_id"],
        decision="APPROVED",
        reason="The exact workspace and target baseline evidence was approved.",
    )

    assert approved["status"] == "APPLIED"
    assert approved["decision"] == "APPROVED"
    assert approved["approver_actor_id"] == APPROVER.actor_id
    assert approved["resulting_rule_set_id"] != prior_rule_set_id
    assert (
        approved["resulting_optional_advisory_binding_hash"]
        == approved["preserved_optional_advisory_binding_hash"]
    )
    assert financial._repo.current_rule_set_id(review.review_id) == approved[
        "resulting_rule_set_id"
    ]
    assert financial._repo.current_rule_set_id(other.review_id) == other_rule_set_id
    assert financial._repo.rule_set_history(review.review_id)[:-1] == prior_history
    assert financial._repo.latest_run(review.review_id)["run_id"] == initial["run_id"]

    resulting = financial._repo.rule_set_members(
        approved["resulting_rule_set_id"]
    )
    resulting_core = [
        item for item in resulting if item["rule_id"].startswith("CORE-")
    ]
    target_core = financial._repo.protected_baseline_members(target)
    assert resulting_core == target_core
    assert [
        item for item in resulting if not item["rule_id"].startswith("CORE-")
    ] == [
        item
        for item in prior_members
        if not item["rule_id"].startswith("CORE-")
    ]

    reviewer = _service(financial, UNAUTHORIZED, Permission.RULE_BOUND_READ)
    status = reviewer.workspace_upgrade_status(review.review_id)
    assert status["state"] == "APPLIED_REVALIDATION_REQUIRED"
    assert status["current_baseline_id"] == target
    assert status["pending_request_id"] is None

    successor = persist_confirmed_validation(
        financial, review.review_id, dataset
    )
    assert successor["run_id"] != initial["run_id"]
    assert reviewer.workspace_upgrade_status(review.review_id)["state"] == "VALIDATED"

    governance_events = [
        event
        for event in financial._audit.events(
            stream_type="RULE_GOVERNANCE"
        )
        if event.payload.get("request_id") == request["request_id"]
    ]
    assert [event.event_type for event in governance_events] == [
        "workspace_baseline_upgrade_requested",
        "workspace_baseline_upgrade_approved_and_applied",
    ]
    assert len(governance_events) == 2
    requested_event, applied_event = governance_events
    _assert_workspace_audit_event(
        requested_event,
        request=request,
        transition="REQUESTED",
        actor_id=ADMIN.actor_id,
        outcome="PENDING_APPROVAL",
    )
    assert requested_event.occurred_at == request["requested_at"]
    assert requested_event.payload["reason"] == request["reason"]
    assert requested_event.payload["before_binding"] == {
        "workspace_id": request["review_id"],
        "workspace_rule_set_id": request["requested_rule_set_id"],
        "workspace_rule_set_version": request[
            "requested_rule_set_version"
        ],
        "workspace_rule_set_content_hash": request[
            "requested_rule_set_content_hash"
        ],
        "protected_baseline_id": request["source_baseline_id"],
        "protected_baseline_version": request[
            "source_baseline_version"
        ],
        "protected_baseline_hash": request["source_baseline_hash"],
        "protected_rule_versions": [
            {
                "rule_id": item["rule_id"],
                "rule_version": item["rule_version"],
            }
            for item in request["source_protected_rule_evidence"]
        ],
        "optional_advisory_binding_count": request[
            "preserved_optional_advisory_binding_count"
        ],
        "optional_advisory_binding_hash": request[
            "preserved_optional_advisory_binding_hash"
        ],
        "optional_advisory_rule_ids": request[
            "preserved_optional_advisory_rule_ids"
        ],
    }
    proposed_binding = requested_event.payload["proposed_after_binding"]
    assert proposed_binding["workspace_rule_set_version"] == (
        request["requested_rule_set_version"] + 1
    )
    assert proposed_binding["protected_baseline_id"] == request[
        "target_baseline_id"
    ]
    assert proposed_binding["protected_baseline_version"] == request[
        "target_baseline_version"
    ]
    assert proposed_binding[
        "preserved_optional_advisory_binding_hash"
    ] == request["preserved_optional_advisory_binding_hash"]
    assert len(requested_event.payload["before_rule_definition"]) == 5
    assert len(requested_event.payload["before_rule_configuration"]) == 5
    assert len(
        requested_event.payload["proposed_after_rule_definition"]
    ) == 5
    assert len(
        requested_event.payload["proposed_after_rule_configuration"]
    ) == 5
    assert len(
        requested_event.payload["proposed_successor_rule_version"]
    ) == 5
    assert requested_event.payload["proposed_effective_time"] == (
        "IMMEDIATE_ON_DISTINCT_FINANCIAL_CONTROL_APPROVAL"
    )

    _assert_workspace_audit_event(
        applied_event,
        request=approved,
        transition="APPROVED_AND_APPLIED",
        actor_id=APPROVER.actor_id,
        outcome="APPLIED",
    )
    assert applied_event.occurred_at == approved["decided_at"]
    assert applied_event.payload["reason"] == approved["decision_reason"]
    assert applied_event.payload[
        "authorizing_financial_control_approver_actor_id"
    ] == APPROVER.actor_id
    assert applied_event.payload["authorization_timestamp"] == approved[
        "decided_at"
    ]
    assert applied_event.payload["activation_timestamp"] == approved[
        "applied_at"
    ]
    assert applied_event.payload["activation_outcome"] == "APPLIED"
    assert applied_event.payload["resulting_workspace_rule_set_id"] == approved[
        "resulting_rule_set_id"
    ]
    assert applied_event.payload[
        "resulting_workspace_rule_set_version"
    ] == approved["resulting_rule_set_version"]
    assert applied_event.payload["prior_binding"][
        "workspace_rule_set_id"
    ] == request["requested_rule_set_id"]
    assert applied_event.payload["prior_binding"][
        "workspace_rule_set_version"
    ] == request["requested_rule_set_version"]
    assert applied_event.payload["resulting_binding"][
        "workspace_rule_set_id"
    ] == approved["resulting_rule_set_id"]
    assert applied_event.payload["resulting_binding"][
        "workspace_rule_set_version"
    ] == approved["resulting_rule_set_version"]
    assert applied_event.payload["resulting_binding"][
        "workspace_rule_set_content_hash"
    ] == approved["resulting_rule_set_content_hash"]


def test_stale_workspace_upgrade_cannot_be_approved_but_can_be_rejected(
    tmp_path,
):
    _database, services, review, dataset = _confirmed_review(tmp_path)
    financial = services.financial_review
    admin = _admin(financial)
    approver = _approver(financial)
    persist_confirmed_validation(financial, review.review_id, dataset)
    _activate_governed_baseline(admin, approver, review, dataset)
    request = admin.request_workspace_upgrade(
        review.review_id, "Request against the current workspace evidence."
    )

    draft = admin.create_optional_draft(
        name="Stale Request Control",
        purpose="Create a governed successor workspace Rule Set.",
        severity="Low",
        operator="LTE",
        threshold="1000000.00",
    )
    admin.test_draft(
        review.review_id, dataset, draft["rule_id"], draft["version"]
    )
    admin.activate_optional_version(
        review.review_id, draft["rule_id"], draft["version"]
    )

    pending = admin.list_workspace_upgrade_requests(review.review_id)[0]
    assert pending["state"] == "STALE_PENDING"
    assert pending["stale"] is True
    assert "WORKSPACE_RULE_SET_CHANGED" in pending["stale_reasons"]
    with pytest.raises(RuleManagementError, match="Rule Set changed"):
        approver.decide_workspace_upgrade(
            request["request_id"],
            decision="APPROVED",
            reason="This approval must fail closed.",
        )
    preserved = financial._repo.workspace_upgrade_request(
        request["request_id"]
    )
    assert preserved["status"] == "PENDING_APPROVAL"
    assert preserved["resulting_rule_set_id"] is None

    rejected = approver.decide_workspace_upgrade(
        request["request_id"],
        decision="REJECTED",
        reason="The workspace Rule Set changed after the request.",
    )
    assert rejected["status"] == "REJECTED"
    assert rejected["resulting_rule_set_id"] is None
    governance_events = [
        event
        for event in financial._audit.events(
            stream_type="RULE_GOVERNANCE"
        )
        if event.payload.get("request_id") == request["request_id"]
    ]
    assert [event.event_type for event in governance_events] == [
        "workspace_baseline_upgrade_requested",
        "workspace_baseline_upgrade_rejected",
    ]
    assert len(governance_events) == 2
    rejected_event = governance_events[1]
    _assert_workspace_audit_event(
        rejected_event,
        request=rejected,
        transition="REJECTED",
        actor_id=APPROVER.actor_id,
        outcome="REJECTED",
    )
    assert rejected_event.occurred_at == rejected["decided_at"]
    assert rejected_event.payload["reason"] == rejected["decision_reason"]
    assert rejected_event.payload["approver_actor_id"] == APPROVER.actor_id
    assert rejected_event.payload["decision_timestamp"] == rejected[
        "decided_at"
    ]
    assert rejected_event.payload["decision_reason"] == rejected[
        "decision_reason"
    ]
    assert rejected_event.payload["decision_outcome"] == "REJECTED"
    assert rejected_event.payload["before_binding"][
        "workspace_rule_set_id"
    ] == request["requested_rule_set_id"]
    assert rejected_event.payload["proposed_after_binding"][
        "protected_baseline_id"
    ] == request["target_baseline_id"]


def test_stale_workspace_upgrade_target_cannot_be_approved_and_remains_rejectable(
    tmp_path,
):
    _database, services, review, dataset = _confirmed_review(tmp_path)
    financial = services.financial_review
    admin = _admin(financial)
    approver = _approver(financial)
    persist_confirmed_validation(financial, review.review_id, dataset)
    _activate_governed_baseline(admin, approver, review, dataset)
    request = admin.request_workspace_upgrade(
        review.review_id, "Bind the first effective successor baseline."
    )

    newer = _submit(
        admin,
        review,
        dataset,
        rule_id="CORE-02",
        name="Valid Account Coding",
        purpose=(
            "Every GED Department Number + Account Number combination must "
            "exist in the Budget report, with governed evidence."
        ),
    )
    approver.decide_protected_change(
        newer["request_id"],
        decision="APPROVED",
        reason="Activate a later effective baseline.",
    )

    pending = admin.list_workspace_upgrade_requests(review.review_id)[0]
    assert pending["state"] == "STALE_PENDING"
    assert "TARGET_BASELINE_CHANGED" in pending["stale_reasons"]
    with pytest.raises(
        RuleManagementError, match="effective protected baseline changed"
    ):
        approver.decide_workspace_upgrade(
            request["request_id"],
            decision="APPROVED",
            reason="Stale target approval must fail.",
        )
    rejected = approver.decide_workspace_upgrade(
        request["request_id"],
        decision="REJECTED",
        reason="The requested target is no longer the effective baseline.",
    )
    assert rejected["status"] == "REJECTED"
    assert rejected["resulting_rule_set_id"] is None


def test_workspace_upgrade_requires_run_and_enforces_roles_and_distinct_actor(
    tmp_path,
):
    _database, services, review, dataset = _confirmed_review(tmp_path)
    financial = services.financial_review
    admin = _admin(financial)
    approver = _approver(financial)
    _activate_governed_baseline(admin, approver, review, dataset)

    candidate = next(
        item
        for item in admin.list_workspace_upgrade_candidates()
        if item["review_id"] == review.review_id
    )
    assert candidate["upgrade_state"] == "NOT_ELIGIBLE"
    with pytest.raises(RuleManagementError, match="complete authoritative"):
        admin.request_workspace_upgrade(
            review.review_id, "Cannot upgrade before a completed run."
        )

    persist_confirmed_validation(financial, review.review_id, dataset)
    request = admin.request_workspace_upgrade(
        review.review_id, "Now bind the completed authoritative run."
    )
    with pytest.raises(PermissionError, match="self-approval denied"):
        admin.decide_workspace_upgrade(
            request["request_id"],
            decision="APPROVED",
            reason="Self approval must be denied.",
        )

    unauthorized = _service(financial, UNAUTHORIZED)
    with pytest.raises(PermissionError, match="not granted"):
        unauthorized.list_workspace_upgrade_candidates()
    with pytest.raises(PermissionError, match="not granted"):
        unauthorized.decide_workspace_upgrade(
            request["request_id"],
            decision="REJECTED",
            reason="Unauthorized actors cannot decide.",
        )


def test_composed_role_self_upgrade_is_denied_and_audited_once(tmp_path):
    database, services, review, dataset = _confirmed_review(tmp_path)
    financial = services.financial_review
    admin = _admin(financial)
    persist_confirmed_validation(financial, review.review_id, dataset)
    _activate_governed_baseline(
        admin, _approver(financial), review, dataset
    )
    request = admin.request_workspace_upgrade(
        review.review_id,
        "Request a protected baseline upgrade for separation-of-duties testing.",
    )
    prior_rule_set_id = financial._repo.current_rule_set_id(review.review_id)
    financial._uow.dal.conn.close()

    assignment = AuthorizationAssignment(
        assignment_id="combined-upgrade-governance",
        actor_id=ADMIN.actor_id,
        actor_source=ADMIN.source,
        allow_roles=frozenset(
            {
                Role.RULE_ADMINISTRATOR,
                Role.FINANCIAL_CONTROL_APPROVER,
            }
        ),
        effective_from=datetime(2020, 1, 1, tzinfo=timezone.utc),
        assigning_actor_id="security-admin",
        assigned_at=datetime(2020, 1, 1, tzinfo=timezone.utc),
    )
    snapshot = AuthorizationPolicySnapshot(
        source_kind="TEST_POLICY",
        version="workspace-upgrade-self-denial-1",
        fingerprint="d" * 64,
        policy=default_mvp_policy(),
        assignments=(assignment,),
    )
    composed = build_query_services(
        str(database),
        clock=FixedClock(),
        identity_provider=FixedIdentityProvider(
            IdentityResolution.resolved(ADMIN)
        ),
        role_assignment_source=StaticRoleAssignmentSource(snapshot),
    )
    try:
        with pytest.raises(ReviewAuthorizationError) as denied:
            composed.rule_management.decide_workspace_upgrade(
                request["request_id"],
                decision="APPROVED",
                reason="A requester must never authorize their own upgrade.",
            )
        assert denied.value.reason_code == "EXPLICIT_DENY"

        authorization_rows = (
            composed.financial_review._uow.dal.conn.execute(
                "SELECT decision,reason_code,actor_id,"
                "authorization_fingerprint,effective_assignment_ids "
                "FROM v2_authorization_decision_events "
                "WHERE permission=? ORDER BY rowid",
                (
                    Permission.RULE_PROTECTED_WORKSPACE_UPGRADE_AUTHORIZE.value,
                ),
            ).fetchall()
        )
        assert authorization_rows == [
            (
                "DENY",
                "EXPLICIT_DENY",
                ADMIN.actor_id,
                snapshot.fingerprint,
                json.dumps(
                    [assignment.assignment_id],
                    separators=(",", ":"),
                ),
            )
        ]

        security_events = [
            event
            for event in composed.financial_review._audit.events(
                stream_type="SECURITY"
            )
            if event.event_type == "authorization_denied"
            and event.payload["permission"]
            == Permission.RULE_PROTECTED_WORKSPACE_UPGRADE_AUTHORIZE.value
        ]
        assert len(security_events) == 1
        security_event = security_events[0]
        assert security_event.actor_id == ADMIN.actor_id
        assert security_event.outcome == "DENIED"
        assert security_event.payload == {
            "permission": (
                Permission.RULE_PROTECTED_WORKSPACE_UPGRADE_AUTHORIZE.value
            ),
            "reason_code": "EXPLICIT_DENY",
            "policy_version": snapshot.policy.version,
            "authorization_source_version": snapshot.version,
            "authorization_source_fingerprint": snapshot.fingerprint,
            "effective_assignment_ids": [assignment.assignment_id],
        }

        governance_events = [
            event
            for event in composed.financial_review._audit.events(
                stream_type="RULE_GOVERNANCE"
            )
            if event.payload.get("request_id") == request["request_id"]
        ]
        assert [event.event_type for event in governance_events] == [
            "workspace_baseline_upgrade_requested"
        ]
        saved = (
            composed.financial_review._repo.workspace_upgrade_request(
                request["request_id"]
            )
        )
        assert saved["status"] == "PENDING_APPROVAL"
        assert saved["decision"] is None
        assert saved["resulting_rule_set_id"] is None
        assert (
            composed.financial_review._repo.current_rule_set_id(
                review.review_id
            )
            == prior_rule_set_id
        )
    finally:
        composed.financial_review._uow.dal.conn.close()
