from __future__ import annotations

import itertools
from datetime import datetime, timezone

import pytest

from finsight.application.review_management import (
    ReviewAuthorizationError,
    ReviewDisposalConfirmationError,
    ReviewIntegrityCheckpointError,
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
from finsight.domain.review_management import (
    ReviewStatus,
    ReviewStatusEvent,
    StatusOwnerKind,
)
from finsight.infrastructure.audit_stream import AuditStreamSqlite
from finsight.infrastructure.authorization_manifest import (
    build_local_reviewer_bootstrap_policy,
)
from finsight.infrastructure.disposal_registry import FilesystemDisposalRegistry
from finsight.infrastructure.identity import FixedIdentityProvider
from finsight.infrastructure.migrations import m0008_review_disposal
from finsight.infrastructure.persistence import Dal, SqliteUnitOfWork
from finsight.infrastructure.review_management_repository import (
    ReviewManagementRepositorySqlite,
)
from finsight.infrastructure.secure_store import TestEnvironmentStoreKeyProvider


pytestmark = pytest.mark.integration

NOW_TEXT = "2026-07-28T14:00:00Z"
NOW = datetime(2026, 7, 28, 14, 0, tzinfo=timezone.utc)
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
        *,
        assignment_source=None,
        registry=None,
        service_ids=None,
        audit_ids=None,
    ):
        self.clock = _Clock()
        self.dal = Dal(
            str(database_path),
            key_provider=TestEnvironmentStoreKeyProvider(),
        )
        if self.dal.conn.execute(
            "SELECT 1 FROM schema_migrations WHERE version=8"
        ).fetchone() is None:
            m0008_review_disposal.up(self.dal.conn)
            self.dal.conn.execute(
                "INSERT INTO schema_migrations(version,name,applied_ts) VALUES(8,?,?)",
                (m0008_review_disposal.NAME, NOW_TEXT),
            )
            self.dal.conn.commit()
        self.uow = SqliteUnitOfWork(self.dal)
        self.repository = ReviewManagementRepositorySqlite(self.dal)
        self.audit = AuditStreamSqlite(
            self.dal,
            self.dal.key_material.audit_key,
            self.clock,
            audit_ids or _Ids(1000),
            anchor_registry=registry,
            after_commit=self.uow.after_commit if registry is not None else None,
        )
        identity = IdentityResolution.resolved(ACTOR)
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
            id_factory=service_ids or _Ids(),
        )

    def close(self):
        self.dal.conn.close()


@pytest.fixture(autouse=True)
def _secure_test_key(monkeypatch):
    monkeypatch.setenv("FINSIGHT_TEST_MODE", "1")
    monkeypatch.setenv("FINSIGHT_TEST_STORE_KEY_HEX", "4a" * 32)


def _advance_to(harness: _Harness, review, target: ReviewStatus) -> None:
    if target is ReviewStatus.DRAFT:
        return
    events = [
        (
            ReviewStatus.DATA_UPLOADED,
            StatusOwnerKind.CANDIDATE,
            review.candidate_id,
            2,
            ReviewStatus.DRAFT,
        ),
        (
            ReviewStatus.DATA_REVIEWED,
            StatusOwnerKind.GENERATION,
            "gen-disposal-test",
            1,
            ReviewStatus.DATA_UPLOADED,
        ),
        (
            ReviewStatus.VALIDATION_COMPLETE,
            StatusOwnerKind.GENERATION,
            "gen-disposal-test",
            2,
            ReviewStatus.DATA_REVIEWED,
        ),
        (
            ReviewStatus.REVIEWED,
            StatusOwnerKind.GENERATION,
            "gen-disposal-test",
            3,
            ReviewStatus.VALIDATION_COMPLETE,
        ),
        (
            ReviewStatus.CLOSED,
            StatusOwnerKind.GENERATION,
            "gen-disposal-test",
            4,
            ReviewStatus.REVIEWED,
        ),
    ]
    with harness.uow.atomic():
        for index, (status, owner_kind, owner_id, sequence, previous) in enumerate(
            events, 1
        ):
            harness.repository.append_status(
                ReviewStatusEvent(
                    event_id=f"status-disposal-{target.name}-{index}",
                    review_id=review.review_id,
                    owner_kind=owner_kind,
                    owner_id=owner_id,
                    sequence=sequence,
                    previous_status=previous,
                    status=status,
                    actor_id=ACTOR.actor_id,
                    occurred_at=NOW_TEXT,
                    reason="TEST_LIFECYCLE",
                )
            )
            if status is target:
                break


@pytest.mark.parametrize(
    "status",
    (
        ReviewStatus.DRAFT,
        ReviewStatus.DATA_UPLOADED,
        ReviewStatus.VALIDATION_COMPLETE,
        ReviewStatus.CLOSED,
    ),
)
def test_governed_disposal_supports_required_review_statuses(tmp_path, status):
    harness = _Harness(tmp_path / f"{status.name}.db")
    created = harness.service.create_review(
        5, 2026, idempotency_key=f"create-{status.name}"
    )
    _advance_to(harness, created, status)

    preview = harness.service.prepare_review_disposal(created.review_id)
    receipt = harness.service.dispose_review(
        created.review_id,
        confirmation_token=preview.confirmation_token,
    )

    assert harness.repository.get(created.review_id) is None
    assert receipt.deleted_counts["v2_review_cycles"] == 1
    assert receipt.deleted_counts["cycles"] == 1
    assert receipt.deleted_counts["v2_review_status_events"] >= 1
    tombstone = harness.repository.review_disposal_tombstone(receipt.scope_token)
    assert tombstone["operation_id"] == receipt.operation_id
    assert tombstone["deleted_inventory"] == dict(receipt.deleted_counts)
    assert tombstone["retained_shared"] == dict(receipt.retained_shared_counts)
    assert created.review_id not in repr(tombstone)
    harness.audit.verify_all()


def test_cancel_and_invalid_confirmation_leave_review_untouched(tmp_path):
    harness = _Harness(tmp_path / "cancel.db")
    created = harness.service.create_review(5, 2026, idempotency_key="create")
    preview = harness.service.prepare_review_disposal(created.review_id)

    assert harness.service.cancel_review_disposal(preview.confirmation_token)
    with pytest.raises(ReviewDisposalConfirmationError):
        harness.service.dispose_review(
            created.review_id,
            confirmation_token=preview.confirmation_token,
        )

    assert harness.repository.get(created.review_id) == created
    assert harness.repository.review_disposal_tombstone(preview.scope_token) is None
    assert harness.dal.conn.execute(
        "SELECT COUNT(*) FROM v2_review_disposal_tombstones"
    ).fetchone()[0] == 0


def test_disposal_is_authorized_and_confirmation_is_bound_to_one_review(tmp_path):
    no_roles = AuthorizationPolicySnapshot(
        source_kind="TEST_POLICY",
        version="1",
        fingerprint="f" * 64,
        policy=default_mvp_policy(),
        assignments=(),
    )
    denied = _Harness(
        tmp_path / "denied.db",
        assignment_source=StaticRoleAssignmentSource(no_roles),
    )
    review = denied.repository
    with pytest.raises(ReviewAuthorizationError):
        denied.service.prepare_review_disposal("rev_not_visible")
    assert review.count(include_archived=True) == 0

    harness = _Harness(tmp_path / "bound.db")
    first = harness.service.create_review(5, 2026, idempotency_key="first")
    second = harness.service.create_review(6, 2026, idempotency_key="second")
    preview = harness.service.prepare_review_disposal(first.review_id)
    with pytest.raises(ReviewDisposalConfirmationError):
        harness.service.dispose_review(
            second.review_id,
            confirmation_token=preview.confirmation_token,
        )
    assert harness.repository.get(first.review_id) is not None
    assert harness.repository.get(second.review_id) is not None


def test_two_review_isolation_exact_receipt_and_external_source_is_untouched(
    tmp_path,
):
    harness = _Harness(tmp_path / "isolated.db")
    first = harness.service.create_review(5, 2026, idempotency_key="first")
    second = harness.service.create_review(6, 2026, idempotency_key="second")
    source = tmp_path / "original-budget.xlsx"
    source.write_bytes(b"not-a-real-workbook")
    harness.dal.conn.execute(
        "INSERT INTO source_bindings("
        "cycle_id,document_type,last_known_path,source_fingerprint,selected_at,actor"
        ") VALUES(?,?,?,?,?,?)",
        (
            first.review_id,
            "Budget",
            str(source),
            "fingerprint",
            NOW_TEXT,
            ACTOR.actor_id,
        ),
    )
    harness.dal.conn.execute(
        "INSERT INTO v2_source_artifacts("
        "artifact_id,source_role,first_seen_filename,byte_size,sha256,media_type,"
        "file_extension,first_selected_actor_id,first_selected_at"
        ") VALUES(?,?,?,?,?,?,?,?,?)",
        (
            "shared-artifact",
            "BUDGET",
            source.name,
            source.stat().st_size,
            "a" * 64,
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            ".xlsx",
            ACTOR.actor_id,
            NOW_TEXT,
        ),
    )
    for index, review in enumerate((first, second), 1):
        harness.dal.conn.execute(
            "INSERT INTO v2_source_binding_versions("
            "binding_id,review_id,candidate_id,source_role,artifact_id,"
            "selected_filename,path_hint,predecessor_binding_id,replacement_reason,"
            "binding_sequence,selected_actor_id,selected_at,bound_actor_id,bound_at,"
            "extraction_profile_version,layout_profile_version,safety_policy_version"
            ") VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                f"shared-binding-{index}",
                review.review_id,
                review.candidate_id,
                "BUDGET",
                "shared-artifact",
                source.name,
                str(source),
                None,
                "TEST",
                1,
                ACTOR.actor_id,
                NOW_TEXT,
                ACTOR.actor_id,
                NOW_TEXT,
                "SLV-001",
                "BUDGET-REAL-001",
                "SAFE-001",
            ),
        )
    harness.dal.conn.execute(
        "INSERT INTO v2_rule_test_runs("
        "test_id,review_id,rule_id,rule_version,dataset_fingerprint,status,"
        "metrics_json,ledger_hash,actor_id,tested_at"
        ") VALUES(?,?,?,?,?,'COMPLETE','{}',?,?,?)",
        (
            "optional-test-first",
            first.review_id,
            "CORE-01",
            "2.0.0",
            "dataset-fingerprint",
            "optional-test-ledger",
            ACTOR.actor_id,
            NOW_TEXT,
        ),
    )
    harness.dal.conn.execute(
        "INSERT INTO v2_rule_set_versions("
        "rule_set_id,review_id,version,predecessor_rule_set_id,"
        "protected_baseline_id,content_hash,created_by,created_at,reason"
        ") VALUES(?,?,1,NULL,'FINSIGHT-CORE-2.0',?,?,?,'TEST')",
        (
            "review-rule-set-first",
            first.review_id,
            "review-rule-set-content",
            ACTOR.actor_id,
            NOW_TEXT,
        ),
    )
    harness.dal.conn.execute(
        "INSERT INTO v2_rule_set_members("
        "rule_set_id,ordinal,rule_id,rule_version,enabled"
        ") VALUES('review-rule-set-first',1,'CORE-01','2.0.0',1)"
    )
    harness.dal.conn.commit()

    preview = harness.service.prepare_review_disposal(first.review_id)
    receipt = harness.service.dispose_review(
        first.review_id,
        confirmation_token=preview.confirmation_token,
    )

    assert source.exists()
    assert source.read_bytes() == b"not-a-real-workbook"
    assert harness.repository.get(first.review_id) is None
    assert harness.repository.get(second.review_id) == second
    assert harness.repository.count(include_archived=True) == 1
    assert receipt.deleted_counts["source_bindings"] == 1
    assert receipt.deleted_counts["v2_source_binding_versions"] == 1
    assert receipt.deleted_counts["v2_source_artifacts"] == 0
    assert receipt.retained_shared_counts["v2_source_artifacts"] == 1
    assert receipt.deleted_counts["v2_rule_test_runs"] == 1
    assert receipt.deleted_counts["v2_rule_set_members"] == 1
    assert receipt.deleted_counts["v2_rule_set_versions"] == 1
    assert harness.dal.conn.execute(
        "SELECT COUNT(*) FROM v2_source_artifacts WHERE artifact_id='shared-artifact'"
    ).fetchone()[0] == 1
    assert harness.dal.conn.execute(
        "SELECT review_id FROM v2_source_binding_versions "
        "WHERE artifact_id='shared-artifact'"
    ).fetchall() == [(second.review_id,)]
    assert receipt.deleted_counts["v2_review_cycles"] == 1
    assert receipt.deleted_counts["v2_authorization_decision_events"] >= 3
    assert all(
        count == 0
        for count in harness.repository.review_disposal_inventory(first.review_id).values()
    )
    disposal_event = harness.audit.events(stream_type="DISPOSAL")[-1]
    assert disposal_event.payload["deleted_counts"] == dict(receipt.deleted_counts)
    assert first.review_id not in repr(disposal_event.payload)


def test_append_only_delete_guard_rejects_unscoped_sql(tmp_path):
    harness = _Harness(tmp_path / "guard.db")
    created = harness.service.create_review(5, 2026, idempotency_key="create")

    with pytest.raises(Exception, match="append_only"):
        harness.dal.conn.execute(
            "DELETE FROM v2_review_cycles WHERE review_id=?",
            (created.review_id,),
        )
    harness.dal.conn.rollback()
    assert harness.repository.get(created.review_id) is not None


def test_external_audit_anchor_is_retired_and_restart_verifies(tmp_path):
    registry_root = tmp_path / "registry"
    registry = FilesystemDisposalRegistry(
        str(registry_root),
        protection_key=b"r" * 32,
        clock=_Clock(),
        id_factory=_Ids(5000),
    )
    registry.create_fresh("store-001", ACTOR.actor_id)
    database = tmp_path / "anchored.db"
    service_ids = _Ids()
    audit_ids = _Ids(1000)
    first = _Harness(
        database,
        registry=registry,
        service_ids=service_ids,
        audit_ids=audit_ids,
    )
    review = first.service.create_review(5, 2026, idempotency_key="create")
    review_stream = first.audit.review_stream_id(review.review_id)
    assert registry.audit_anchor(review_stream) is not None

    preview = first.service.prepare_review_disposal(review.review_id)
    receipt = first.service.dispose_review(
        review.review_id,
        confirmation_token=preview.confirmation_token,
    )
    first.audit.verify_all(reconcile_committed_gap=True)
    assert registry.audit_anchor(review_stream) is None
    assert registry.disposal_event(receipt.operation_id).event_kind.value == (
        "DISPOSAL_COMMITTED"
    )
    first.close()

    reopened_registry = FilesystemDisposalRegistry(
        str(registry_root),
        protection_key=b"r" * 32,
        clock=_Clock(),
        id_factory=_Ids(9000),
    )
    reopened = _Harness(
        database,
        registry=reopened_registry,
        service_ids=service_ids,
        audit_ids=audit_ids,
    )
    reopened.audit.verify_all(reconcile_committed_gap=True)
    assert reopened.repository.get(review.review_id) is None
    assert reopened.repository.review_disposal_tombstone(receipt.scope_token) is not None


def test_committed_disposal_reconciles_one_failed_external_commit(tmp_path):
    base = FilesystemDisposalRegistry(
        str(tmp_path / "registry"),
        protection_key=b"r" * 32,
        clock=_Clock(),
        id_factory=_Ids(5000),
    )
    base.create_fresh("store-001", ACTOR.actor_id)

    class _FailCommitOnce:
        def __init__(self, target):
            self.target = target
            self.failed = False

        def __getattr__(self, name):
            return getattr(self.target, name)

        def commit_disposal(self, operation_id, actor_id):
            if not self.failed:
                self.failed = True
                raise OSError("injected disposal checkpoint failure")
            return self.target.commit_disposal(operation_id, actor_id)

    registry = _FailCommitOnce(base)
    harness = _Harness(tmp_path / "reconcile.db", registry=registry)
    review = harness.service.create_review(5, 2026, idempotency_key="create")
    preview = harness.service.prepare_disposal(review.review_id)

    with pytest.raises(ReviewIntegrityCheckpointError) as checkpoint:
        harness.service.confirm_disposal(
            review.review_id, preview.confirmation_token
        )

    assert checkpoint.value.envelope.mutation_outcome.value == (
        "The requested change was saved."
    )
    assert harness.repository.get(review.review_id) is None
    assert not harness.uow.control_plane_faulted
    harness.audit.verify_all(reconcile_committed_gap=True)
    event = next(
        event
        for event in base.read_events()
        if event.operation_id.startswith("review-disposal-")
        and event.event_kind.value == "DISPOSAL_COMMITTED"
    )
    assert event.event_kind.value == "DISPOSAL_COMMITTED"
