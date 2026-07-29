# Verifies: V2 FR-123/124/125/189/190/195/197 — Workflow 1 service behavior.
from __future__ import annotations

import itertools
from datetime import datetime, timezone

import pytest

from finsight.application.review_management import (
    IdempotencyConflictError,
    InvalidReviewTransitionError,
    ReviewAuditIntegrityError,
    ReviewAuthorizationError,
    ReviewManagementError,
    ReviewManagementService,
)
from finsight.application.security import (
    AuthorizationPolicySnapshot,
    AuthorizationService,
    IdentityResolution,
    StaticRoleAssignmentSource,
    default_mvp_policy,
)
from finsight.domain.identity import Actor
from finsight.domain.review_management import ReviewStatus
from finsight.infrastructure.audit_stream import AuditStreamSqlite
from finsight.infrastructure.authorization_manifest import (
    build_local_reviewer_bootstrap_policy,
)
from finsight.infrastructure.identity import FixedIdentityProvider
from finsight.infrastructure.persistence import Dal, SqliteUnitOfWork
from finsight.infrastructure.review_management_repository import (
    ReviewManagementRepositorySqlite,
)
from finsight.infrastructure.secure_store import TestEnvironmentStoreKeyProvider

pytestmark = pytest.mark.integration

NOW_TEXT = "2026-07-27T14:00:00Z"
NOW = datetime(2026, 7, 27, 14, 0, tzinfo=timezone.utc)
ACTOR = Actor("actor-501", "ACME\\reviewer", "TEST_IDP")


class _Clock:
    def now(self):
        return NOW_TEXT


class _Ids:
    def __init__(self, start=1):
        self._values = itertools.count(start)

    def __call__(self):
        return f"{next(self._values):032x}"


class _Harness:
    def __init__(
        self,
        database_path,
        assignment_source=None,
        audit_stream=None,
        id_factory=None,
        audit_id_factory=None,
        identity_resolution=None,
    ):
        self.clock = _Clock()
        self.dal = Dal(
            str(database_path),
            key_provider=TestEnvironmentStoreKeyProvider(),
        )
        self.uow = SqliteUnitOfWork(self.dal)
        self.repository = ReviewManagementRepositorySqlite(self.dal)
        self.audit = audit_stream or AuditStreamSqlite(
            self.dal,
            self.dal.key_material.audit_key,
            self.clock,
            audit_id_factory or _Ids(1000),
        )
        identity = identity_resolution or IdentityResolution.resolved(ACTOR)
        snapshot = build_local_reviewer_bootstrap_policy(ACTOR, NOW)
        self.service = ReviewManagementService(
            repository=self.repository,
            audit_stream=self.audit,
            uow=self.uow,
            identity_provider=FixedIdentityProvider(identity),
            assignment_source=assignment_source
            or StaticRoleAssignmentSource(snapshot),
            authorization=AuthorizationService(),
            clock=self.clock,
            id_factory=id_factory or _Ids(),
        )

    def close(self):
        self.dal.conn.close()


@pytest.fixture(autouse=True)
def _secure_test_key(monkeypatch):
    monkeypatch.setenv("FINSIGHT_TEST_MODE", "1")
    monkeypatch.setenv("FINSIGHT_TEST_STORE_KEY_HEX", "4a" * 32)


def test_welcome_availability_disables_past_reviews_until_one_exists(tmp_path):
    harness = _Harness(tmp_path / "finsight.db")

    empty = harness.service.availability()
    harness.service.create_review(7, 2026, idempotency_key="create-1")
    populated = harness.service.availability()

    assert empty.identity_resolved
    assert empty.can_create
    assert not empty.has_reviews
    assert not empty.can_view_past
    assert "No previous reviews" in empty.explanation
    assert populated.has_reviews
    assert populated.can_view_past
    assert populated.role_labels == ("Reviewer",)


def test_create_is_atomic_persisted_and_idempotent(tmp_path):
    harness = _Harness(tmp_path / "finsight.db")

    created = harness.service.create_review(
        5, 2026, idempotency_key="may-2026-create"
    )
    repeated = harness.service.create_review(
        5, 2026, idempotency_key="may-2026-create"
    )

    assert created.review_id.startswith("rev_")
    assert created.candidate_id.startswith("cand_")
    assert created.period.label == "May 2026"
    assert created.status is ReviewStatus.DRAFT
    assert created.context_label == "Working Candidate"
    assert created.review.created_by == ACTOR.actor_id
    assert created.review.created_at == NOW_TEXT
    assert repeated == created
    assert harness.repository.count(include_archived=True) == 1
    history = harness.repository.status_history(created.review_id)
    assert len(history) == 1
    assert history[0]["event_id"].startswith("status_")
    event_without_id = {
        key: value for key, value in history[0].items() if key != "event_id"
    }
    assert event_without_id == {
        "owner_kind": "WorkingCandidate",
        "owner_id": created.candidate_id,
        "sequence": 1,
        "previous_status": None,
        "status": "Draft",
        "actor_id": ACTOR.actor_id,
        "occurred_at": NOW_TEXT,
        "reason": "NEW_REVIEW",
        "origin": "NATIVE",
    }


def test_reused_idempotency_key_with_different_request_is_rejected(tmp_path):
    harness = _Harness(tmp_path / "finsight.db")
    harness.service.create_review(5, 2026, idempotency_key="one-request")

    with pytest.raises(IdempotencyConflictError):
        harness.service.create_review(6, 2026, idempotency_key="one-request")

    assert harness.repository.count(include_archived=True) == 1


def test_list_and_open_return_saved_review_and_append_required_audit(tmp_path):
    harness = _Harness(tmp_path / "finsight.db")
    created = harness.service.create_review(5, 2026, idempotency_key="create-1")

    listed = harness.service.list_reviews()
    reopened = harness.service.open_review(created.review_id)
    review_events = harness.audit.events(review_id=created.review_id)
    security_events = harness.audit.events(stream_type="SECURITY")

    assert [item.review_id for item in listed] == [created.review_id]
    assert reopened == created
    assert [event.event_type for event in review_events] == [
        "review_created",
        "review_reopened",
    ]
    assert all(event.actor_id == ACTOR.actor_id for event in review_events)
    assert review_events[0].payload["reporting_period"] == "May 2026"
    assert review_events[1].payload["status"] == "Draft"
    assert any(event.event_type == "past_reviews_viewed" for event in security_events)
    decisions = harness.dal.conn.execute(
        "SELECT permission,decision,resource_id FROM v2_authorization_decision_events "
        "ORDER BY rowid"
    ).fetchall()
    assert ("review.create", "ALLOW", created.review_id) in decisions
    assert ("review.list", "ALLOW", None) in decisions
    assert ("review.open", "ALLOW", created.review_id) in decisions


def test_review_persists_across_database_close_and_reopen(tmp_path):
    database = tmp_path / "finsight.db"
    service_ids = _Ids()
    audit_ids = _Ids(1000)
    first = _Harness(
        database,
        id_factory=service_ids,
        audit_id_factory=audit_ids,
    )
    created = first.service.create_review(12, 2027, idempotency_key="create-1")
    first.close()

    second = _Harness(
        database,
        id_factory=service_ids,
        audit_id_factory=audit_ids,
    )
    listed = second.service.list_reviews()
    reopened = second.service.open_review(created.review_id)
    second.audit.verify_all()

    assert [item.review_id for item in listed] == [created.review_id]
    assert reopened.period.label == "December 2027"
    assert reopened.status is ReviewStatus.DRAFT
    assert [
        event.event_type
        for event in second.audit.events(review_id=created.review_id)
    ] == ["review_created", "review_reopened"]


def test_unauthorized_create_fails_closed_and_records_denial_only(tmp_path):
    no_roles = AuthorizationPolicySnapshot(
        source_kind="TEST_POLICY",
        version="1",
        fingerprint="f" * 64,
        policy=default_mvp_policy(),
        assignments=(),
    )
    harness = _Harness(
        tmp_path / "finsight.db",
        assignment_source=StaticRoleAssignmentSource(no_roles),
    )

    with pytest.raises(ReviewAuthorizationError) as denied:
        harness.service.create_review(5, 2026, idempotency_key="denied-create")

    assert denied.value.reason_code == "NOT_GRANTED"
    assert harness.repository.count(include_archived=True) == 0
    decisions = harness.dal.conn.execute(
        "SELECT permission,decision,reason_code FROM v2_authorization_decision_events"
    ).fetchall()
    assert decisions == [("review.create", "DENY", "NOT_GRANTED")]
    events = harness.audit.events(stream_type="SECURITY")
    assert len(events) == 1
    assert events[0].event_type == "authorization_denied"
    assert events[0].outcome == "DENIED"
    assert denied.value.envelope.code == "FS-AUT-001"
    assert denied.value.envelope.correlation_id == events[0].correlation_id
    diagnostics = harness.repository.diagnostic_events(
        denied.value.envelope.correlation_id
    )
    assert len(diagnostics) == 1
    assert diagnostics[0]["code"] == "FS-AUT-001"
    assert diagnostics[0]["actor_id"] == ACTOR.actor_id
    assert diagnostics[0]["mutation_outcome"] == "No changes were made."


def test_unresolved_identity_denies_without_mutating_audit_or_application_state(
    tmp_path,
):
    unresolved = IdentityResolution.unresolved(
        "IDENTITY_LOST",
        "The authenticated account is no longer available.",
    )
    harness = _Harness(
        tmp_path / "finsight.db",
        identity_resolution=unresolved,
    )

    with pytest.raises(ReviewAuthorizationError):
        harness.service.create_review(5, 2026, idempotency_key="unresolved")

    assert harness.repository.count(include_archived=True) == 0
    assert harness.dal.conn.execute(
        "SELECT COUNT(*) FROM v2_authorization_decision_events"
    ).fetchone()[0] == 0
    assert harness.dal.conn.execute(
        "SELECT COUNT(*) FROM v2_audit_events"
    ).fetchone()[0] == 0


def test_audit_write_failure_rolls_back_entire_creation_bundle(tmp_path):
    database = tmp_path / "finsight.db"
    harness = _Harness(database)

    class _FailingAudit:
        def append(self, **_kwargs):
            raise OSError("synthetic audit failure")

    harness.service._audit = _FailingAudit()

    with pytest.raises(ReviewManagementError) as failed:
        harness.service.create_review(5, 2026, idempotency_key="fault")

    assert "synthetic audit failure" not in failed.value.user_message()
    assert failed.value.envelope.code == "FS-SYS-002"
    assert failed.value.envelope.mutation_outcome.value == "No changes were made."
    assert harness.repository.count(include_archived=True) == 0
    assert harness.repository.create_request("fault") is None
    for table in (
        "cycles",
        "v2_review_cycles",
        "v2_working_candidates",
        "v2_review_cycle_pointers",
        "v2_review_status_events",
        "v2_review_disposition_events",
        "v2_authorization_decision_events",
    ):
        assert harness.dal.conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0] == 0
    diagnostics = harness.repository.diagnostic_events(
        failed.value.envelope.correlation_id
    )
    assert len(diagnostics) == 1
    assert diagnostics[0]["code"] == "FS-SYS-002"


def test_invalid_terminal_transition_preserves_draft_review(tmp_path):
    harness = _Harness(tmp_path / "finsight.db")
    created = harness.service.create_review(5, 2026, idempotency_key="create-1")

    with pytest.raises(InvalidReviewTransitionError, match="must be Reviewed"):
        harness.service.close_review(created.review_id, "too early")

    persisted = harness.repository.get(created.review_id)
    assert persisted.status is ReviewStatus.DRAFT
    assert len(harness.repository.status_history(created.review_id)) == 1


def test_role_revocation_at_commit_boundary_rolls_back_review_creation(tmp_path):
    granted = build_local_reviewer_bootstrap_policy(ACTOR, NOW)
    revoked = AuthorizationPolicySnapshot(
        source_kind="TEST_POLICY",
        version="2",
        fingerprint="e" * 64,
        policy=default_mvp_policy(),
        assignments=(),
    )

    class _RevokedBeforeCommit:
        def __init__(self):
            self.calls = 0

        def load_current(self, _at, _actor):
            self.calls += 1
            return granted if self.calls == 1 else revoked

    source = _RevokedBeforeCommit()
    harness = _Harness(
        tmp_path / "finsight.db",
        assignment_source=source,
    )

    with pytest.raises(
        ReviewAuthorizationError,
        match="Authorization changed",
    ) as denied:
        harness.service.create_review(
            5,
            2026,
            idempotency_key="revoked-at-commit",
        )

    assert denied.value.reason_code == "AUTHORIZATION_CHANGED_DURING_OPERATION"
    assert source.calls == 2
    assert harness.repository.count(include_archived=True) == 0
    assert harness.repository.create_request("revoked-at-commit") is None
    decisions = harness.dal.conn.execute(
        "SELECT decision,reason_code,manifest_version,authorization_fingerprint,"
        "effective_assignment_ids,effective_roles,correlation_id "
        "FROM v2_authorization_decision_events"
    ).fetchall()
    assert decisions == [
        (
            "DENY",
            "NOT_GRANTED",
            2,
            "e" * 64,
            "[]",
            "[]",
            denied.value.envelope.correlation_id,
        )
    ]
    events = harness.audit.events(stream_type="SECURITY")
    assert [event.event_type for event in events] == [
        "authorization_revoked_at_commit"
    ]
    assert events[0].correlation_id == denied.value.envelope.correlation_id
    assert events[0].payload == {
        "permission": "review.create",
        "gate_reason_code": "AUTHORIZATION_CHANGED_DURING_OPERATION",
        "final_evaluation_allowed": False,
        "final_evaluation_reason_code": "NOT_GRANTED",
        "initiating_actor_id": ACTOR.actor_id,
        "initiating_actor_source": ACTOR.source,
        "observed_actor_id": ACTOR.actor_id,
        "observed_actor_source": ACTOR.source,
        "observed_identity_error_code": None,
        "authorization_source_version": "2",
        "authorization_source_fingerprint": "e" * 64,
        "effective_assignment_ids": [],
    }
    assert harness.repository.diagnostic_events(
        denied.value.envelope.correlation_id
    )[0]["code"] == "FS-AUT-001"


def test_actor_change_at_commit_boundary_rolls_back_review_creation(tmp_path):
    second_actor = Actor("actor-999", "ACME\\other", "TEST_IDP")

    class _ChangingIdentity:
        def __init__(self):
            self.calls = 0

        def resolve_current_actor(self):
            self.calls += 1
            selected = ACTOR if self.calls == 1 else second_actor
            return IdentityResolution.resolved(selected)

    snapshot = build_local_reviewer_bootstrap_policy(ACTOR, NOW)
    harness = _Harness(tmp_path / "finsight.db")
    harness.service._identity = _ChangingIdentity()
    harness.service._assignments = StaticRoleAssignmentSource(snapshot)

    with pytest.raises(
        ReviewAuthorizationError,
        match="authenticated account changed",
    ) as denied:
        harness.service.create_review(
            5,
            2026,
            idempotency_key="actor-changed-at-commit",
        )

    assert denied.value.reason_code == "IDENTITY_CHANGED_DURING_OPERATION"
    assert harness.repository.count(include_archived=True) == 0
    assert harness.dal.conn.execute(
        "SELECT decision,reason_code FROM v2_authorization_decision_events"
    ).fetchall() == [
        ("DENY", "IDENTITY_CHANGED_DURING_OPERATION")
    ]
    assert [
        event.event_type
        for event in harness.audit.events(stream_type="SECURITY")
    ] == ["authorization_revoked_at_commit"]
    event = harness.audit.events(stream_type="SECURITY")[0]
    assert event.actor_id == ACTOR.actor_id
    assert event.payload["gate_reason_code"] == "IDENTITY_CHANGED_DURING_OPERATION"
    assert event.payload["initiating_actor_id"] == ACTOR.actor_id
    assert event.payload["observed_actor_id"] == second_actor.actor_id
    assert event.payload["observed_actor_source"] == second_actor.source
    assert event.payload["final_evaluation_allowed"] is None


def test_denial_evidence_failure_locks_all_later_protected_writes(tmp_path):
    granted = build_local_reviewer_bootstrap_policy(ACTOR, NOW)
    revoked = AuthorizationPolicySnapshot(
        source_kind="TEST_POLICY",
        version="2",
        fingerprint="e" * 64,
        policy=default_mvp_policy(),
        assignments=(),
    )

    class _RevokedBeforeCommit:
        def __init__(self):
            self.calls = 0

        def load_current(self, _at, _actor):
            self.calls += 1
            return granted if self.calls == 1 else revoked

    harness = _Harness(
        tmp_path / "finsight.db",
        assignment_source=_RevokedBeforeCommit(),
    )
    real_audit = harness.audit

    class _FailingDenialAudit:
        def append(self, **kwargs):
            if kwargs["event_type"] == "authorization_revoked_at_commit":
                raise OSError("injected denial-evidence failure")
            return real_audit.append(**kwargs)

        def verify_all(self, **kwargs):
            return real_audit.verify_all(**kwargs)

    harness.service._audit = _FailingDenialAudit()

    with pytest.raises(ReviewAuditIntegrityError) as failed:
        harness.service.create_review(
            5,
            2026,
            idempotency_key="denial-evidence-fault",
        )

    assert failed.value.envelope.code == "FS-AUD-001"
    assert failed.value.envelope.mutation_outcome.value == "No changes were made."
    assert failed.value.authorization_denial is not None
    assert (
        failed.value.authorization_denial.reason_code
        == "AUTHORIZATION_CHANGED_DURING_OPERATION"
    )
    assert (
        failed.value.envelope.correlation_id
        == failed.value.authorization_denial.envelope.correlation_id
    )
    assert harness.uow.control_plane_faulted
    assert harness.repository.count(include_archived=True) == 0
    assert harness.dal.conn.execute(
        "SELECT COUNT(*) FROM v2_authorization_decision_events"
    ).fetchone()[0] == 0
    assert harness.dal.conn.execute(
        "SELECT COUNT(*) FROM v2_audit_events"
    ).fetchone()[0] == 0

    with pytest.raises(ReviewAuditIntegrityError) as locked:
        harness.service.create_review(
            6,
            2026,
            idempotency_key="must-remain-locked",
        )

    assert locked.value.envelope.code == "FS-AUD-001"
    assert harness.repository.count(include_archived=True) == 0
    assert harness.dal.conn.execute(
        "SELECT COUNT(*) FROM v2_authorization_decision_events"
    ).fetchone()[0] == 0
    assert harness.dal.conn.execute(
        "SELECT COUNT(*) FROM v2_audit_events"
    ).fetchone()[0] == 0
