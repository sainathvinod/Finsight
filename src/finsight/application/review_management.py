# Implements: V2 FR-123/124/125/189/190/195/197, NFR-082/090, AC-02 — Workflow 1 use cases.
from __future__ import annotations

import hashlib
import json
import threading
import uuid
from dataclasses import dataclass, replace
from datetime import datetime, timezone
from typing import Callable, Optional, Sequence

from finsight.application.failure_contracts import (
    CatalogedApplicationFailure,
    ErrorEnvelope,
    MutationOutcome,
    Retryability,
)
from finsight.application.security import (
    AuthorizationContext,
    AuthorizationDecision,
    AuthorizationService,
    IdentityResolution,
)
from finsight.application.review_disposal import (
    ReviewDisposalPreview,
    ReviewDisposalReceipt,
    inventory_fingerprint,
    review_scope_token,
)
from finsight.domain.identity import Actor, Permission
from finsight.domain.review_management import (
    ManagedReview,
    ReportingPeriod,
    ReviewCycleRecord,
    ReviewPointers,
    ReviewStatus,
    ReviewStatusEvent,
    WorkingCandidate,
)
from finsight.domain.source_intake import (
    EvidenceStatus,
    IntakePair,
    SourceInspection,
    SourceIssue,
    SourceRole,
)


class ReviewManagementError(CatalogedApplicationFailure):
    code = "FS-SYS-002"
    category = "Runtime"
    impact = "The requested review-management action could not be completed."
    remedy = (
        "Retry the action once. If it fails again, contact FinSight support "
        "and provide the correlation ID."
    )
    retryability = Retryability.SUPPORT_REQUIRED

    def __init__(
        self,
        message: str,
        *,
        correlation_id: Optional[str] = None,
        actor_reference: Optional[str] = None,
        mutation_outcome: MutationOutcome = MutationOutcome.NO_CHANGE,
    ):
        super().__init__(
            ErrorEnvelope.build(
                code=self.code,
                category=self.category,
                correlation_id=correlation_id
                or ("corr_error_" + uuid.uuid4().hex),
                cause=message,
                impact=self.impact,
                remedies=(self.remedy,),
                retryability=self.retryability,
                mutation_outcome=mutation_outcome,
                actor_reference=actor_reference,
                diagnostic_event_id="diag_" + uuid.uuid4().hex,
            )
        )


class ReviewAuthorizationError(ReviewManagementError):
    code = "FS-AUT-001"
    category = "Authorization"
    impact = "The protected action was denied."
    remedy = "Verify your current role assignment with a FinSight administrator, then retry."
    retryability = Retryability.RETRY_AFTER_AUTHORIZATION

    def __init__(
        self,
        message: str,
        reason_code: str,
        *,
        correlation_id: Optional[str] = None,
        actor_reference: Optional[str] = None,
    ):
        if reason_code.startswith("IDENTITY"):
            self.code = "FS-IDN-001"
            self.category = "Identity"
            self.remedy = (
                "Confirm the signed-in operating-system account and restart FinSight."
            )
        super().__init__(
            message,
            correlation_id=correlation_id,
            actor_reference=actor_reference,
        )
        self.reason_code = reason_code


class ReviewNotFoundError(ReviewManagementError):
    code = "FS-LIF-002"
    category = "Review lifecycle"
    impact = "No saved review was opened or changed."
    remedy = "Return to Past Reviews, refresh the list, and select an available review."
    retryability = Retryability.RETRY_AFTER_CORRECTION


class IdempotencyConflictError(ReviewManagementError):
    code = "FS-LIF-003"
    category = "Review lifecycle"
    impact = "A second review was not created."
    remedy = "Start the Create New Review flow again to obtain a new request identity."
    retryability = Retryability.RETRY_AFTER_CORRECTION


class InvalidReviewTransitionError(ReviewManagementError):
    code = "FS-LIF-004"
    category = "Review lifecycle"
    impact = "The review status was not changed."
    remedy = "Complete the required prior review stage before retrying this action."
    retryability = Retryability.RETRY_AFTER_CORRECTION


class ReviewDisposalConfirmationError(ReviewManagementError):
    code = "FS-LIF-006"
    category = "Review disposal"
    impact = "The review was not deleted."
    remedy = (
        "Return to the review, request a new deletion confirmation, and verify "
        "the reporting period before confirming."
    )
    retryability = Retryability.RETRY_AFTER_CORRECTION


class ReviewIntegrityCheckpointError(ReviewManagementError):
    code = "FS-SYS-003"
    category = "Runtime integrity"
    impact = (
        "The review change was saved, but further protected writes remain locked "
        "until the external integrity checkpoint is reconciled."
    )
    remedy = (
        "Restart FinSight. If access remains locked, contact FinSight support "
        "and provide the correlation ID."
    )
    retryability = Retryability.SUPPORT_REQUIRED


class ReviewAuditIntegrityError(ReviewManagementError):
    code = "FS-AUD-001"
    category = "Audit integrity"
    impact = (
        "No review change was made. Protected actions are locked because "
        "mandatory authorization evidence could not be retained."
    )
    remedy = (
        "Restart FinSight. If access remains locked, contact FinSight support "
        "and provide the correlation ID."
    )
    retryability = Retryability.SUPPORT_REQUIRED

    def __init__(
        self,
        message: str,
        *,
        authorization_denial: Optional[ReviewAuthorizationError] = None,
        **kwargs,
    ) -> None:
        super().__init__(message, **kwargs)
        self.authorization_denial = authorization_denial


@dataclass(frozen=True)
class ReviewAccessAvailability:
    identity_resolved: bool
    can_create: bool
    can_view_past: bool
    has_reviews: bool
    actor_display_name: str
    actor_source: str
    role_labels: tuple[str, ...]
    explanation: str


@dataclass(frozen=True)
class AuditScope:
    """Application-level resource reference accepted by the injected audit port."""

    resource_type: str
    resource_id: str


@dataclass(frozen=True)
class _Authorized:
    actor: Actor
    snapshot: object
    decision: AuthorizationDecision
    timestamp: str
    evaluated_at: datetime
    correlation_id: str


@dataclass(frozen=True)
class _CommitAuthorizationEvidence:
    """The exact identity/authorization facts observed by the commit guard."""

    initiator: _Authorized
    observed_actor: Optional[Actor]
    observed_identity_error_code: Optional[str]
    final_authorization: Optional[_Authorized]
    observed_at: str
    evaluated_at: datetime


class _CommitAuthorizationRejected(ReviewAuthorizationError):
    """Internal typed denial carrying evidence across the business rollback."""

    def __init__(
        self,
        message: str,
        reason_code: str,
        evidence: _CommitAuthorizationEvidence,
    ) -> None:
        super().__init__(
            message,
            reason_code,
            correlation_id=evidence.initiator.correlation_id,
            actor_reference=evidence.initiator.actor.actor_id,
        )
        self.evidence = evidence


def _utc_datetime(value: str) -> datetime:
    normalized = value.strip()
    if normalized.endswith("Z"):
        normalized = normalized[:-1] + "+00:00"
    parsed = datetime.fromisoformat(normalized)
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError("Clock timestamps must include a UTC offset.")
    return parsed.astimezone(timezone.utc)


def _canonical_hash(value: dict) -> str:
    data = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def _evidence_type(field_name: str) -> str:
    return {
        "department_number": "DEPARTMENT_NUMBER",
        "department_name": "DEPARTMENT_NAME",
        "reporting_period": "REPORTING_PERIOD",
        "reporting_period_display": "REPORTING_PERIOD_DISPLAY",
        "run_date": "RUN_DATE",
        "worksheet": "WORKSHEET",
    }.get(field_name, field_name.upper())


def _evidence_status(inspection: SourceInspection, field_name: str) -> str:
    evidence = inspection.evidence_for(field_name)
    return (
        evidence.status.value if evidence is not None else EvidenceStatus.ABSENT.value
    )


def _department_evidence_status(pair: IntakePair) -> str:
    statuses = (
        _evidence_status(pair.budget, "department_number"),
        _evidence_status(pair.ged, "department_number"),
    )
    return (
        EvidenceStatus.PRESENT.value
        if all(value == EvidenceStatus.PRESENT.value for value in statuses)
        else EvidenceStatus.CONFLICTING.value
    )


def _department_match_status(pair: IntakePair) -> str:
    budget = pair.budget.evidence_for("department_number")
    ged = pair.ged.evidence_for("department_number")
    if (
        budget is None
        or ged is None
        or budget.normalized_value is None
        or ged.normalized_value is None
    ):
        return "ABSENT"
    return "MATCH" if budget.normalized_value == ged.normalized_value else "MISMATCH"


def _period_match_status(pair: IntakePair) -> str:
    if pair.ged_period is None:
        return "ABSENT"
    return "MATCH" if pair.ged_period == pair.selected_period else "MISMATCH"


def _source_issue_remedies(issue: SourceIssue) -> tuple[str, ...]:
    if issue.code.startswith("FS-MET-"):
        return (
            "Select Budget and GED reports for the same department and reporting "
            "period, or return to the review and correct the selected period.",
        )
    if issue.code.startswith("FS-SLV-"):
        return (
            "Select the approved Budget or GED report with the required worksheet, "
            "headers, totals, and row layout, then retry.",
        )
    if issue.code.startswith("FS-WRK-"):
        return (
            "Select an unprotected .xlsx workbook that meets the approved WRL-001 "
            "safety and resource limits, then retry.",
        )
    return (
        "Verify the file still exists and is readable, then reselect it and retry.",
    )


def _catalog_source_issue(
    issue: SourceIssue, correlation_id: str
) -> SourceIssue:
    return replace(
        issue,
        correlation_id=correlation_id,
        permitted_remedies=(
            issue.permitted_remedies or _source_issue_remedies(issue)
        ),
    )


def _catalog_inspection(
    inspection: SourceInspection, correlation_id: str
) -> SourceInspection:
    return replace(
        inspection,
        issues=tuple(
            _catalog_source_issue(issue, correlation_id)
            for issue in inspection.issues
        ),
    )


def _catalog_pair(pair: IntakePair, correlation_id: str) -> IntakePair:
    return replace(
        pair,
        issues=tuple(
            _catalog_source_issue(issue, correlation_id)
            for issue in pair.issues
        ),
    )


class ReviewManagementService:
    """Protected application boundary for Review Management and Source Intake.

    Identity and authorization are re-resolved for every action. Repository/audit writes are grouped in
    one Unit of Work. The optional source-intake collaborators are deterministic Workflow 2 ports;
    evaluator, finding, AI, report, and export services remain outside this boundary.
    """

    def __init__(
        self,
        *,
        repository,
        audit_stream,
        uow,
        identity_provider,
        assignment_source,
        authorization: Optional[AuthorizationService],
        clock,
        source_intake_repository=None,
        source_intake_coordinator=None,
        id_factory: Callable[[], str] = lambda: uuid.uuid4().hex,
    ):
        self._repo = repository
        self._audit = audit_stream
        self._uow = uow
        self._identity = identity_provider
        self._assignments = assignment_source
        self._authorization = authorization or AuthorizationService()
        self._clock = clock
        self._source_intake_repo = source_intake_repository
        self._source_intake = source_intake_coordinator
        self._id = id_factory
        self._disposal_lock = threading.RLock()
        self._pending_disposals: dict[
            str, tuple[ReviewDisposalPreview, str]
        ] = {}
        self._consuming_disposals: set[str] = set()

    def _snapshot(self, evaluated_at: datetime, actor: Actor):
        source = self._assignments
        return (
            source.load_current(evaluated_at, actor)
            if hasattr(source, "load_current")
            else source(evaluated_at, actor)
        )

    def _evaluation(
        self,
        permission: Permission,
        context: Optional[AuthorizationContext] = None,
    ):
        timestamp = self._clock.now()
        evaluated_at = _utc_datetime(timestamp)
        identity: IdentityResolution = self._identity.resolve_current_actor()
        if not identity.is_resolved:
            return identity, None, None, timestamp, evaluated_at
        snapshot = self._snapshot(evaluated_at, identity.require_actor())
        decision = self._authorization.decide(
            identity,
            permission,
            snapshot,
            evaluated_at,
            context,
        )
        return identity, snapshot, decision, timestamp, evaluated_at

    def availability(self) -> ReviewAccessAvailability:
        """Passive Welcome projection; it reads only after successful identity/authorization.

        Rendering or refreshing this projection does not create a reopen/read audit event.
        """

        with self._uow.atomic():
            self._repo.ensure_authorization_transaction()
            identity, snapshot, create, _timestamp, evaluated_at = self._evaluation(
                Permission.REVIEW_CREATE
            )
            if not identity.is_resolved:
                return ReviewAccessAvailability(
                    False,
                    False,
                    False,
                    False,
                    "Identity unavailable",
                    "",
                    (),
                    "FinSight could not verify your account. Review data remains locked.",
                )
            list_decision = self._authorization.decide(
                identity, Permission.REVIEW_LIST, snapshot, evaluated_at
            )
            actor = identity.require_actor()
            roles = tuple(
                sorted(
                    role.value
                    for role in create.effective_roles.union(
                        list_decision.effective_roles
                    )
                )
            )
            can_list = list_decision.allowed
            count = self._repo.count(include_archived=True) if can_list else 0
        explanation = (
            "No previous reviews are available yet."
            if can_list and count == 0
            else (
                "Your current role does not allow access to saved reviews."
                if not can_list
                else ""
            )
        )
        return ReviewAccessAvailability(
            True,
            create.allowed,
            can_list and count > 0,
            count > 0,
            actor.display_name,
            actor.source,
            roles,
            explanation,
        )

    def create_review(
        self,
        month: int,
        year: int,
        *,
        idempotency_key: str,
    ) -> ManagedReview:
        period = ReportingPeriod(year=year, month=month)
        if not idempotency_key or not idempotency_key.strip():
            raise ValueError("Review creation requires an idempotency key.")
        request_key = idempotency_key.strip()

        def create(authorized: _Authorized) -> ManagedReview:
            request_hash = _canonical_hash(
                {
                    "actor_id": authorized.actor.actor_id,
                    "month": period.month,
                    "year": period.year,
                }
            )
            existing = self._repo.create_request(request_key)
            if existing:
                if (
                    existing["request_hash"] != request_hash
                    or existing["actor_id"] != authorized.actor.actor_id
                ):
                    raise IdempotencyConflictError(
                        "That creation request was already used for a different review.",
                        correlation_id=authorized.correlation_id,
                        actor_reference=authorized.actor.actor_id,
                    )
                review = self._repo.get(existing["review_id"])
                if review is None:
                    raise ReviewManagementError(
                        "The saved creation request references a missing review.",
                        correlation_id=authorized.correlation_id,
                        actor_reference=authorized.actor.actor_id,
                    )
                self._record_authorization(
                    authorized,
                    Permission.REVIEW_CREATE,
                    resource_type="Review",
                    resource_id=review.review_id,
                )
                return review

            review_id = "rev_" + self._id()
            candidate_id = "cand_" + self._id()
            timestamp = authorized.timestamp
            review = ReviewCycleRecord(
                review_id=review_id,
                period=period,
                created_by=authorized.actor.actor_id,
                created_at=timestamp,
            )
            candidate = WorkingCandidate(
                candidate_id=candidate_id,
                review_id=review_id,
                created_by=authorized.actor.actor_id,
                created_at=timestamp,
            )
            pointers = ReviewPointers(review_id, candidate_id, None, None, None, 0)
            status = ReviewStatusEvent(
                event_id="status_" + self._id(),
                review_id=review_id,
                owner_kind=candidate_owner_kind(),
                owner_id=candidate_id,
                sequence=1,
                previous_status=None,
                status=ReviewStatus.DRAFT,
                actor_id=authorized.actor.actor_id,
                occurred_at=timestamp,
                reason="NEW_REVIEW",
            )
            self._repo.create_bundle(
                review=review,
                candidate=candidate,
                pointers=pointers,
                status_event=status,
                disposition_event_id="disp_" + self._id(),
                request_key=request_key,
                request_hash=request_hash,
                actor=authorized.actor,
            )
            self._record_authorization(
                authorized,
                Permission.REVIEW_CREATE,
                resource_type="Review",
                resource_id=review_id,
            )
            self._audit.append(
                review_id=review_id,
                event_type="review_created",
                actor=authorized.actor,
                occurred_at=timestamp,
                correlation_id=authorized.correlation_id,
                payload={
                    "review_id": review_id,
                    "candidate_id": candidate_id,
                    "reporting_period": period.label,
                    "status": ReviewStatus.DRAFT.value,
                    "policy_version": authorized.snapshot.policy.version,
                    "authorization_source_version": authorized.snapshot.version,
                    "authorization_source_fingerprint": authorized.snapshot.fingerprint,
                },
                scopes=(
                    AuditScope("Review", review_id),
                    AuditScope("WorkingCandidate", candidate_id),
                ),
            )
            created = self._repo.get(review_id)
            if created is None:  # pragma: no cover - transactional invariant
                raise ReviewManagementError(
                    "The created review could not be reloaded.",
                    correlation_id=authorized.correlation_id,
                    actor_reference=authorized.actor.actor_id,
                )
            return created

        return self._execute(Permission.REVIEW_CREATE, create)

    def existing_review_count_for_period(self, month: int, year: int) -> int:
        """Return a passive, authorized duplicate-period warning projection."""

        period = ReportingPeriod(year=year, month=month)

        def count(authorized: _Authorized) -> int:
            self._record_authorization(
                authorized,
                Permission.REVIEW_LIST,
                resource_type="ReviewCollection",
                resource_id=None,
            )
            return self._repo.count_for_period(period.month, period.year)

        return self._execute(Permission.REVIEW_LIST, count)

    def list_reviews(
        self, statuses: Optional[Sequence[ReviewStatus]] = None
    ) -> list[ManagedReview]:
        def list_authorized(authorized: _Authorized) -> list[ManagedReview]:
            reviews = self._repo.list(statuses=statuses, include_archived=statuses is not None)
            self._record_authorization(
                authorized, Permission.REVIEW_LIST, resource_type="ReviewCollection", resource_id=None
            )
            self._audit.append(
                stream_type="SECURITY",
                event_type="past_reviews_viewed",
                actor=authorized.actor,
                occurred_at=authorized.timestamp,
                correlation_id=authorized.correlation_id,
                payload={
                    "result_count": len(reviews),
                    "status_filters": [ReviewStatus(item).value for item in statuses]
                    if statuses
                    else [],
                    "policy_version": authorized.snapshot.policy.version,
                },
            )
            return reviews

        return self._execute(Permission.REVIEW_LIST, list_authorized)

    def open_review(self, review_id: str) -> ManagedReview:
        def open_authorized(authorized: _Authorized) -> ManagedReview:
            review = self._repo.get(review_id)
            if review is None:
                # Not-found is evaluated only after authorization so review IDs are not leaked.
                raise ReviewNotFoundError(
                    "The selected review no longer exists.",
                    correlation_id=authorized.correlation_id,
                    actor_reference=authorized.actor.actor_id,
                )
            self._record_authorization(
                authorized,
                Permission.REVIEW_OPEN,
                resource_type="Review",
                resource_id=review_id,
            )
            self._audit.append(
                review_id=review_id,
                event_type="review_reopened",
                actor=authorized.actor,
                occurred_at=authorized.timestamp,
                correlation_id=authorized.correlation_id,
                payload={
                    "review_id": review_id,
                    "status": review.status.value,
                    "reporting_period": review.period.label,
                    "policy_version": authorized.snapshot.policy.version,
                    "authorization_source_version": authorized.snapshot.version,
                },
                scopes=(AuditScope("Review", review_id),),
            )
            return review

        return self._execute(Permission.REVIEW_OPEN, open_authorized)

    def begin_source_inspection(
        self, review_id: str, role: SourceRole
    ) -> ManagedReview:
        """Authorize and audit one read-only file-selection attempt before worker extraction."""

        normalized_role = SourceRole(role)

        def begin(authorized: _Authorized) -> ManagedReview:
            review = self._require_source_intake_review(
                review_id, authorized, allow_uploaded=True
            )
            self._record_authorization(
                authorized,
                Permission.REVIEW_ADVANCE,
                resource_type="WorkingCandidate",
                resource_id=review.candidate_id,
            )
            self._audit.append(
                review_id=review_id,
                event_type="source_inspection_started",
                actor=authorized.actor,
                occurred_at=authorized.timestamp,
                correlation_id=authorized.correlation_id,
                payload={
                    "source_role": normalized_role.value,
                    "layout_profile_version": "SLV-001",
                    "safety_policy_version": "WRL-001",
                    "policy_version": authorized.snapshot.policy.version,
                    "authorization_source_version": authorized.snapshot.version,
                },
                scopes=(
                    AuditScope("Review", review_id),
                    AuditScope("WorkingCandidate", review.candidate_id),
                ),
            )
            return review

        return self._execute(Permission.REVIEW_ADVANCE, begin)

    def record_source_inspection(
        self, review_id: str, inspection: SourceInspection
    ) -> SourceInspection:
        """Retain privacy-bounded extraction outcome evidence after worker inspection."""

        def record(authorized: _Authorized) -> SourceInspection:
            review = self._require_source_intake_review(
                review_id, authorized, allow_uploaded=True
            )
            cataloged = _catalog_inspection(
                inspection, authorized.correlation_id
            )
            self._record_authorization(
                authorized,
                Permission.REVIEW_ADVANCE,
                resource_type="WorkingCandidate",
                resource_id=review.candidate_id,
            )
            self._audit.append(
                review_id=review_id,
                event_type=(
                    "source_inspection_completed"
                    if cataloged.is_compatible
                    else "source_inspection_rejected"
                ),
                actor=authorized.actor,
                occurred_at=authorized.timestamp,
                correlation_id=authorized.correlation_id,
                outcome="SUCCEEDED" if cataloged.is_compatible else "REJECTED",
                payload={
                    "source_role": cataloged.role.value,
                    "filename": cataloged.file_name,
                    "byte_size": cataloged.byte_size,
                    "sha256": cataloged.sha256 or None,
                    "compatibility_status": cataloged.compatibility_status.value,
                    "extraction_status": cataloged.extraction_status.value,
                    "record_count": cataloged.record_count,
                    "issue_codes": [item.code for item in cataloged.issues],
                    "worksheet": cataloged.worksheet_name,
                    "layout_profile_version": cataloged.profile_version,
                    "safety_policy_version": cataloged.safety_profile_version,
                },
                scopes=(
                    AuditScope("Review", review_id),
                    AuditScope("WorkingCandidate", review.candidate_id),
                ),
            )
            for issue in cataloged.issues:
                self._append_source_issue_diagnostic(
                    issue,
                    authorized,
                    mutation_outcome=MutationOutcome.NO_CHANGE,
                    impact="The selected source was not bound to the review.",
                )
            return cataloged

        return self._execute(Permission.REVIEW_ADVANCE, record)

    def record_source_inspection_failure(
        self, review_id: str, role: SourceRole
    ) -> CatalogedApplicationFailure:
        """Record a content-free unexpected worker failure without exposing raw exceptions."""

        normalized_role = SourceRole(role)

        def record(authorized: _Authorized) -> CatalogedApplicationFailure:
            from finsight.application.source_intake import SourceIntakeFailure

            review = self._require_source_intake_review(
                review_id, authorized, allow_uploaded=True
            )
            failure = SourceIntakeFailure(
                f"FinSight could not read the selected {normalized_role.label}.",
                code="FS-SRC-099",
                correlation_id=authorized.correlation_id,
            )
            self._record_authorization(
                authorized,
                Permission.REVIEW_ADVANCE,
                resource_type="WorkingCandidate",
                resource_id=review.candidate_id,
            )
            self._audit.append(
                review_id=review_id,
                event_type="source_inspection_failed",
                actor=authorized.actor,
                occurred_at=authorized.timestamp,
                correlation_id=authorized.correlation_id,
                outcome="FAILED",
                payload={
                    "source_role": normalized_role.value,
                    "error_code": "FS-SRC-099",
                    "state_changed": False,
                },
                scopes=(
                    AuditScope("Review", review_id),
                    AuditScope("WorkingCandidate", review.candidate_id),
                ),
            )
            self._append_failure_diagnostic(failure.envelope, authorized)
            return failure

        return self._execute(Permission.REVIEW_ADVANCE, record)

    def commit_source_intake(
        self,
        review_id: str,
        pair: IntakePair,
        *,
        idempotency_key: str,
    ):
        """Atomically bind exactly one Budget and GED source and advance the Draft."""

        if self._source_intake_repo is None or self._source_intake is None:
            raise ReviewManagementError(
                "Source intake is not available in this FinSight composition."
            )
        if not idempotency_key or not idempotency_key.strip():
            raise ValueError("Source intake requires an idempotency key.")
        if not pair.budget.is_compatible or not pair.ged.is_compatible:
            raise ValueError("Only structurally compatible source pairs can be saved.")

        def commit(authorized: _Authorized):
            from finsight.application.source_intake import SourceIntakeResult

            review = self._require_source_intake_review(
                review_id, authorized, allow_uploaded=True
            )
            # Final source identity check immediately precedes authoritative
            # binding. It reads only SHA-256/size and retains no workbook bytes.
            self._source_intake.assert_pair_unchanged(pair)
            if review.period != pair.selected_period:
                raise InvalidReviewTransitionError(
                    "The selected source pair belongs to a different review period.",
                    correlation_id=authorized.correlation_id,
                    actor_reference=authorized.actor.actor_id,
                )
            current = self._source_intake_repo.get_current_pair(review_id)
            request_hash = _canonical_hash(
                {
                    "review_id": review_id,
                    "candidate_id": review.candidate_id,
                    "actor_id": authorized.actor.actor_id,
                    "selected_period": pair.selected_period.label,
                    "budget_sha256": pair.budget.sha256,
                    "ged_sha256": pair.ged.sha256,
                }
            )
            summary_id = "summary_" + self._id()
            commit_record = self._source_commit_record(
                review,
                pair,
                authorized,
                idempotency_key=idempotency_key.strip(),
                request_hash=request_hash,
                summary_id=summary_id,
                current=current,
            )
            persisted = self._source_intake_repo.commit_pair(commit_record)
            replay = persisted["summary_id"] != summary_id
            result_pair = _catalog_pair(
                pair,
                (
                    self._source_summary_correlation(
                        review_id, persisted["summary_id"]
                    )
                    if replay
                    else authorized.correlation_id
                ),
            )
            if not replay and review.status is ReviewStatus.DRAFT:
                status = ReviewStatusEvent(
                    event_id="status_" + self._id(),
                    review_id=review_id,
                    owner_kind=candidate_owner_kind(),
                    owner_id=review.candidate_id,
                    sequence=self._repo.next_status_sequence(
                        candidate_owner_kind(), review.candidate_id
                    ),
                    previous_status=ReviewStatus.DRAFT,
                    status=ReviewStatus.DATA_UPLOADED,
                    actor_id=authorized.actor.actor_id,
                    occurred_at=authorized.timestamp,
                    reason="SOURCE_INTAKE_COMPLETED",
                )
                self._repo.append_status(status)
            self._record_authorization(
                authorized,
                Permission.REVIEW_ADVANCE,
                resource_type="WorkingCandidate",
                resource_id=review.candidate_id,
            )
            if not replay:
                for issue in result_pair.issues:
                    self._append_source_issue_diagnostic(
                        issue,
                        authorized,
                        mutation_outcome=MutationOutcome.COMMITTED,
                        impact=(
                            "The source pair was saved, but cross-file validation "
                            "remains blocked."
                        ),
                    )
                self._audit.append(
                    review_id=review_id,
                    event_type=(
                        "source_intake_replaced"
                        if current
                        else "source_intake_completed"
                    ),
                    actor=authorized.actor,
                    occurred_at=authorized.timestamp,
                    correlation_id=authorized.correlation_id,
                    payload={
                        "summary_id": persisted["summary_id"],
                        "candidate_id": review.candidate_id,
                        "budget_binding_id": persisted["budget_binding_id"],
                        "ged_binding_id": persisted["ged_binding_id"],
                        "budget_filename": pair.budget.file_name,
                        "ged_filename": pair.ged.file_name,
                        "budget_sha256": pair.budget.sha256,
                        "ged_sha256": pair.ged.sha256,
                        "budget_detail_count": pair.budget.record_count,
                        "ged_transaction_count": pair.ged.record_count,
                        "department_number": pair.department_number,
                        "department_name_status": _evidence_status(
                            pair.ged, "department_name"
                        ),
                        "department_match_status": _department_match_status(pair),
                        "reporting_period_match_status": _period_match_status(pair),
                        "metadata_gate_status": result_pair.gate_status.value,
                        "layout_profile_version": pair.budget.profile_version,
                        "safety_policy_version": pair.budget.safety_profile_version,
                        "policy_version": authorized.snapshot.policy.version,
                        "authorization_source_version": authorized.snapshot.version,
                    },
                    scopes=(
                        AuditScope("Review", review_id),
                        AuditScope("WorkingCandidate", review.candidate_id),
                        AuditScope("SourceIntakeSummary", persisted["summary_id"]),
                    ),
                )
            updated = self._repo.get(review_id)
            if updated is None:  # pragma: no cover - transactional invariant
                raise ReviewManagementError(
                    "The updated review could not be reloaded.",
                    correlation_id=authorized.correlation_id,
                    actor_reference=authorized.actor.actor_id,
                )
            return SourceIntakeResult(
                review=updated,
                pair=result_pair,
                persisted_summary=persisted,
                idempotent_replay=replay,
            )

        return self._execute(Permission.REVIEW_ADVANCE, commit)

    def source_intake_summary(self, review_id: str):
        """Return the saved report-level projection without workbook bytes or detail rows."""

        if self._source_intake_repo is None:
            return None

        def read(authorized: _Authorized):
            from finsight.application.source_intake import restore_source_intake

            review = self._repo.get(review_id)
            if review is None:
                raise ReviewNotFoundError(
                    "The selected review no longer exists.",
                    correlation_id=authorized.correlation_id,
                    actor_reference=authorized.actor.actor_id,
                )
            self._record_authorization(
                authorized,
                Permission.REVIEW_READ,
                resource_type="SourceIntakeSummary",
                resource_id=review_id,
            )
            summary = self._source_intake_repo.get_summary(review_id)
            if summary is None:
                return None
            sources = self._source_intake_repo.get_current_pair(review_id)
            restored = restore_source_intake(summary, sources)
            return replace(
                restored,
                pair=_catalog_pair(
                    restored.pair,
                    self._source_summary_correlation(
                        review_id, restored.summary_id
                    ),
                ),
            )

        return self._execute(Permission.REVIEW_READ, read)

    def _require_source_intake_review(
        self,
        review_id: str,
        authorized: _Authorized,
        *,
        allow_uploaded: bool,
    ) -> ManagedReview:
        review = self._repo.get(review_id)
        if review is None:
            raise ReviewNotFoundError(
                "The selected review no longer exists.",
                correlation_id=authorized.correlation_id,
                actor_reference=authorized.actor.actor_id,
            )
        allowed = {ReviewStatus.DRAFT}
        if allow_uploaded:
            allowed.add(ReviewStatus.DATA_UPLOADED)
        if review.status not in allowed or review.candidate_id is None:
            raise InvalidReviewTransitionError(
                "Source intake is available only for a Draft or Data Uploaded Working Candidate.",
                correlation_id=authorized.correlation_id,
                actor_reference=authorized.actor.actor_id,
            )
        return review

    def _source_commit_record(
        self,
        review: ManagedReview,
        pair: IntakePair,
        authorized: _Authorized,
        *,
        idempotency_key: str,
        request_hash: str,
        summary_id: str,
        current: dict,
    ) -> dict:
        def source(inspection: SourceInspection) -> dict:
            predecessor = current.get(inspection.role.value, {}).get("binding_id")
            return {
                "source_role": inspection.role.value,
                "artifact_id": "artifact_" + self._id(),
                "binding_id": "binding_" + self._id(),
                "filename": inspection.file_name,
                "byte_size": inspection.byte_size,
                "sha256": inspection.sha256,
                "path_hint": inspection.path,
                "selected_actor_id": authorized.actor.actor_id,
                "selected_at": authorized.timestamp,
                "bound_actor_id": authorized.actor.actor_id,
                "bound_at": authorized.timestamp,
                "worksheet_name": inspection.worksheet_name,
                "upload_status": "SUCCEEDED",
                "compatibility_status": "COMPATIBLE",
                "extraction_status": "SUCCEEDED",
                "structural_issue_count": len(inspection.issues),
                "predecessor_binding_id": predecessor,
                "replacement_reason": (
                    "REPLACEMENT" if predecessor else "INITIAL_INTAKE"
                ),
                "evidence": [
                    {
                        "evidence_type": _evidence_type(item.field_name),
                        "evidence_status": item.status.value,
                        "ordinal": ordinal,
                        "raw_scalar": item.raw_value,
                        "normalized_scalar": item.normalized_value,
                        "worksheet_name": item.worksheet,
                        "cell_reference": item.cell,
                        "parser_profile_version": inspection.profile_version,
                        "extraction_profile_version": inspection.profile_version,
                        "metadata_policy_version": "V1-METADATA-1",
                    }
                    for ordinal, item in enumerate(inspection.evidence, start=1)
                ],
            }

        return {
            "review_id": review.review_id,
            "candidate_id": review.candidate_id,
            "idempotency_key": idempotency_key,
            "request_hash": request_hash,
            "summary_id": summary_id,
            "committed_actor_id": authorized.actor.actor_id,
            "committed_at": authorized.timestamp,
            "selected_month": review.period.month,
            "selected_year": review.period.year,
            "resolved_department_number": pair.department_number,
            "resolved_department_name": pair.department_name,
            "department_evidence_status": _department_evidence_status(pair),
            "period_evidence_status": _evidence_status(
                pair.ged, "reporting_period"
            ),
            "department_match_status": _department_match_status(pair),
            "reporting_period_match_status": _period_match_status(pair),
            "budget_detail_count": pair.budget.record_count,
            "ged_transaction_count": pair.ged.record_count,
            "extraction_profile_version": pair.budget.profile_version,
            "layout_profile_version": pair.budget.profile_version,
            "safety_policy_version": pair.budget.safety_profile_version,
            "metadata_policy_version": "V1-METADATA-1",
            "sources": [source(pair.budget), source(pair.ged)],
        }

    def _source_summary_correlation(
        self, review_id: str, summary_id: str
    ) -> str:
        for event in reversed(
            tuple(self._audit.events(review_id=review_id))
        ):
            if (
                event.event_type
                in ("source_intake_completed", "source_intake_replaced")
                and event.payload.get("summary_id") == summary_id
            ):
                return event.correlation_id
        raise ReviewManagementError(
            "The saved source intake is missing its diagnostic correlation evidence."
        )

    def _append_source_issue_diagnostic(
        self,
        issue: SourceIssue,
        authorized: _Authorized,
        *,
        mutation_outcome: MutationOutcome,
        impact: str,
    ) -> None:
        if not issue.correlation_id or not issue.permitted_remedies:
            raise ReviewManagementError(
                "A source diagnostic is missing its actionable identity.",
                correlation_id=authorized.correlation_id,
                actor_reference=authorized.actor.actor_id,
            )
        self._repo.append_diagnostic_event(
            diagnostic_event_id="diag_" + self._id(),
            correlation_id=issue.correlation_id,
            code=issue.code,
            category=issue.category,
            user_safe_cause=issue.message,
            user_safe_impact=impact,
            permitted_remedies=issue.permitted_remedies,
            retryability=Retryability.RETRY_AFTER_CORRECTION.value,
            mutation_outcome=mutation_outcome.value,
            actor_id=authorized.actor.actor_id,
            component="source-intake",
            occurred_at=authorized.timestamp,
            taxonomy_version="1",
        )

    def _append_failure_diagnostic(
        self, envelope: ErrorEnvelope, authorized: _Authorized
    ) -> None:
        self._repo.append_diagnostic_event(
            diagnostic_event_id=envelope.diagnostic_event_id
            or ("diag_" + self._id()),
            correlation_id=envelope.correlation_id,
            code=envelope.code,
            category=envelope.category,
            user_safe_cause=envelope.user_safe_cause,
            user_safe_impact=envelope.user_safe_impact,
            permitted_remedies=envelope.permitted_remedies,
            retryability=envelope.retryability.value,
            mutation_outcome=envelope.mutation_outcome.value,
            actor_id=authorized.actor.actor_id,
            component="source-intake",
            occurred_at=authorized.timestamp,
            taxonomy_version=envelope.taxonomy_version,
        )

    def prepare_review_disposal(self, review_id: str) -> ReviewDisposalPreview:
        """Authorize deletion and issue a one-time, in-memory confirmation token."""

        confirmation_token = "dispose-confirm-" + self._id()

        def prepare(
            authorized: _Authorized,
        ) -> tuple[ReviewDisposalPreview, str]:
            review = self._repo.get(review_id)
            if review is None:
                raise ReviewNotFoundError(
                    "The selected review no longer exists.",
                    correlation_id=authorized.correlation_id,
                    actor_reference=authorized.actor.actor_id,
                )
            inventory = self._repo.review_disposal_inventory(review_id)
            self._record_authorization(
                authorized,
                Permission.REVIEW_DISPOSAL_REQUEST,
                resource_type="Review",
                resource_id=review_id,
            )
            return (
                ReviewDisposalPreview(
                    confirmation_token=confirmation_token,
                    review_id=review_id,
                    reporting_period=review.period.label,
                    status=review.status.value,
                    pointer_revision=review.pointer_revision,
                    scope_token=review_scope_token(review_id),
                    inventory_fingerprint=inventory_fingerprint(inventory),
                    inventory=inventory,
                ),
                authorized.actor.actor_id,
            )

        preview, actor_id = self._execute(
            Permission.REVIEW_DISPOSAL_REQUEST, prepare
        )
        with self._disposal_lock:
            self._pending_disposals[confirmation_token] = (preview, actor_id)
        return preview

    def prepare_disposal(self, review_id: str) -> ReviewDisposalPreview:
        """Stable UI-facing alias for the governed preview operation."""

        return self.prepare_review_disposal(review_id)

    def cancel_review_disposal(self, confirmation_token: str) -> bool:
        """Invalidate a preview without changing persisted review data."""

        with self._disposal_lock:
            pending = self._pending_disposals.get(confirmation_token)
            if pending is None or confirmation_token in self._consuming_disposals:
                return False
        identity, _snapshot, decision, _timestamp, _evaluated_at = self._evaluation(
            Permission.REVIEW_DISPOSAL_REQUEST
        )
        if (
            not identity.is_resolved
            or decision is None
            or not decision.allowed
            or identity.require_actor().actor_id != pending[1]
        ):
            return False
        with self._disposal_lock:
            return self._pending_disposals.pop(confirmation_token, None) is not None

    def cancel_disposal(self, confirmation_token: str) -> bool:
        return self.cancel_review_disposal(confirmation_token)

    def dispose_review(
        self,
        review_id: str,
        *,
        confirmation_token: str,
    ) -> ReviewDisposalReceipt:
        """Permanently remove one review after explicit, same-actor confirmation."""

        with self._disposal_lock:
            pending = self._pending_disposals.get(confirmation_token)
            if pending is None:
                raise ReviewDisposalConfirmationError(
                    "The deletion confirmation is missing, expired, or was already used."
                )
            if confirmation_token in self._consuming_disposals:
                raise ReviewDisposalConfirmationError(
                    "That deletion confirmation is already being processed."
                )
            self._consuming_disposals.add(confirmation_token)
        preview, preview_actor_id = pending
        scope_token = preview.scope_token
        try:
            if preview.review_id != review_id:
                raise ReviewDisposalConfirmationError(
                    "The deletion confirmation belongs to a different review."
                )

            operation_id = "review-disposal-" + self._id()
            tombstone_id = "disposal-tombstone-" + self._id()
            confirmation_fingerprint = hashlib.sha256(
                b"FinSight/ReviewDisposal/Confirmation/v1\0"
                + confirmation_token.encode("utf-8")
            ).hexdigest()

            def dispose(authorized: _Authorized) -> ReviewDisposalReceipt:
                review = self._repo.get(review_id)
                if review is None:
                    raise ReviewNotFoundError(
                        "The selected review no longer exists.",
                        correlation_id=authorized.correlation_id,
                        actor_reference=authorized.actor.actor_id,
                    )
                if authorized.actor.actor_id != preview_actor_id:
                    raise ReviewDisposalConfirmationError(
                        "The deletion must be confirmed by the same authenticated user.",
                        correlation_id=authorized.correlation_id,
                        actor_reference=authorized.actor.actor_id,
                    )
                if (
                    review.pointer_revision != preview.pointer_revision
                    or review.status.value != preview.status
                    or review.period.label != preview.reporting_period
                ):
                    raise ReviewDisposalConfirmationError(
                        "The review changed after the deletion preview was opened.",
                        correlation_id=authorized.correlation_id,
                        actor_reference=authorized.actor.actor_id,
                    )
                self._record_authorization(
                    authorized,
                    Permission.REVIEW_DISPOSAL_REQUEST,
                    resource_type="Review",
                    resource_id=review_id,
                )
                result = self._repo.dispose_review(
                    review_id=review_id,
                    operation_id=operation_id,
                    tombstone_id=tombstone_id,
                    confirmation_fingerprint=confirmation_fingerprint,
                    actor_id=authorized.actor.actor_id,
                    disposed_at=authorized.timestamp,
                    reason_code="USER_CONFIRMED_PERMANENT_DELETION",
                )
                self._uow.before_commit(
                    lambda: self._audit.prepare_review_disposal(
                        operation_id=operation_id,
                        review_id=review_id,
                        scope_token=result["scope_token"],
                        inventory_fingerprint=result["inventory_fingerprint"],
                        actor_id=authorized.actor.actor_id,
                    )
                )
                self._audit.append(
                    stream_type="DISPOSAL",
                    event_type="review_disposed",
                    actor=authorized.actor,
                    occurred_at=authorized.timestamp,
                    correlation_id=authorized.correlation_id,
                    payload={
                        "operation_id": operation_id,
                        "tombstone_id": tombstone_id,
                        "scope_token": result["scope_token"],
                        "inventory_fingerprint": result[
                            "inventory_fingerprint"
                        ],
                        "deleted_counts": result["deleted_counts"],
                        "retained_shared_counts": result[
                            "retained_shared_counts"
                        ],
                        "reason_code": "USER_CONFIRMED_PERMANENT_DELETION",
                    },
                    scopes=(AuditScope("DisposedReview", result["scope_token"]),),
                )
                self._uow.after_commit(
                    lambda: self._audit.commit_review_disposal(
                        operation_id, authorized.actor.actor_id
                    )
                )
                return ReviewDisposalReceipt(
                    operation_id=operation_id,
                    tombstone_id=tombstone_id,
                    review_id=review_id,
                    scope_token=result["scope_token"],
                    inventory_fingerprint=result["inventory_fingerprint"],
                    actor_id=authorized.actor.actor_id,
                    disposed_at=authorized.timestamp,
                    deleted_counts=result["deleted_counts"],
                    retained_shared_counts=result["retained_shared_counts"],
                )

            receipt = self._execute(
                Permission.REVIEW_DISPOSAL_REQUEST, dispose
            )
        except Exception:
            # A post-commit control-plane failure may raise even though the
            # tombstone proves the review is gone. Consume the token in that
            # case so it can never authorize a second operation.
            if self._repo.review_disposal_tombstone(scope_token) is not None:
                with self._disposal_lock:
                    self._pending_disposals.pop(confirmation_token, None)
            raise
        else:
            with self._disposal_lock:
                self._pending_disposals.pop(confirmation_token, None)
            return receipt
        finally:
            with self._disposal_lock:
                self._consuming_disposals.discard(confirmation_token)

    def confirm_disposal(
        self,
        review_id: str,
        confirmation_token: str,
    ) -> ReviewDisposalReceipt:
        """Stable UI-facing alias; confirmation always consumes a preview token."""

        return self.dispose_review(
            review_id,
            confirmation_token=confirmation_token,
        )

    def close_review(self, review_id: str, reason: str) -> ManagedReview:
        return self._advance_terminal(
            review_id, Permission.REVIEW_CLOSE, ReviewStatus.REVIEWED, ReviewStatus.CLOSED, reason
        )

    def archive_review(self, review_id: str, reason: str) -> ManagedReview:
        return self._advance_terminal(
            review_id, Permission.REVIEW_ARCHIVE, ReviewStatus.CLOSED, ReviewStatus.ARCHIVED, reason
        )

    def _advance_terminal(
        self,
        review_id: str,
        permission: Permission,
        required: ReviewStatus,
        target: ReviewStatus,
        reason: str,
    ) -> ManagedReview:
        def advance(authorized: _Authorized) -> ManagedReview:
            review = self._repo.get(review_id)
            if review is None:
                raise ReviewNotFoundError(
                    "The selected review no longer exists.",
                    correlation_id=authorized.correlation_id,
                    actor_reference=authorized.actor.actor_id,
                )
            if review.status != required:
                raise InvalidReviewTransitionError(
                    f"A review must be {required.value} before it can become {target.value}.",
                    correlation_id=authorized.correlation_id,
                    actor_reference=authorized.actor.actor_id,
                )
            event = ReviewStatusEvent(
                event_id="status_" + self._id(),
                review_id=review_id,
                owner_kind=review.status_owner_kind,
                owner_id=review.status_owner_id,
                sequence=self._repo.next_status_sequence(
                    review.status_owner_kind, review.status_owner_id
                ),
                previous_status=required,
                status=target,
                actor_id=authorized.actor.actor_id,
                occurred_at=authorized.timestamp,
                reason=(reason or "").strip()
                or target.value.upper().replace(" ", "_"),
            )
            self._repo.append_status(event)
            self._record_authorization(
                authorized, permission, resource_type="Review", resource_id=review_id
            )
            self._audit.append(
                review_id=review_id,
                event_type="review_status_changed",
                actor=authorized.actor,
                occurred_at=authorized.timestamp,
                correlation_id=authorized.correlation_id,
                payload={
                    "review_id": review_id,
                    "from_status": required.value,
                    "to_status": target.value,
                    "reason": event.reason,
                },
                scopes=(AuditScope("Review", review_id),),
            )
            return self._repo.get(review_id)

        return self._execute(permission, advance)

    def audit_events(self, review_id: str):
        def read_audit(authorized: _Authorized):
            self._record_authorization(
                authorized,
                Permission.REVIEW_READ,
                resource_type="ReviewAudit",
                resource_id=review_id,
            )
            # Opening the review is the separately chained sensitive-read action.
            return self._audit.events(review_id=review_id)

        return self._execute(Permission.REVIEW_READ, read_audit)

    def storage_inventory(self, review_id: str) -> dict[str, int]:
        def read_inventory(authorized: _Authorized) -> dict[str, int]:
            self._record_authorization(
                authorized,
                Permission.REVIEW_READ,
                resource_type="ReviewStorageInventory",
                resource_id=review_id,
            )
            return self._repo.storage_inventory(review_id)

        return self._execute(Permission.REVIEW_READ, read_inventory)

    def require_permission(
        self,
        permission: Permission,
        context: Optional[AuthorizationContext] = None,
    ) -> None:
        """Authorize a composed application service through the same live policy gate.

        Rule-management commands use this boundary so identity is re-resolved,
        the current signed assignments are reloaded, and the decision remains
        auditable without coupling that service to Review Management internals.
        """

        def authorize(authorized: _Authorized) -> None:
            self._record_authorization(
                authorized,
                permission,
                resource_type="ApplicationCapability",
                resource_id=permission.value,
            )

        self._execute(permission, authorize, context=context)

    def execute_authorized(
        self,
        permission: Permission,
        operation,
        context: Optional[AuthorizationContext] = None,
    ):
        """Run another application service command inside this live policy gate."""

        def execute(authorized: _Authorized):
            result = operation()
            self._record_authorization(
                authorized,
                permission,
                resource_type="ApplicationCapability",
                resource_id=permission.value,
            )
            return result

        return self._execute(
            permission,
            execute,
            context=context,
        )

    def _execute(
        self,
        permission: Permission,
        operation,
        *,
        context: Optional[AuthorizationContext] = None,
    ):
        correlation_id = "corr_" + self._id()
        denial: Optional[ReviewAuthorizationError] = None
        result = None
        actor_reference: Optional[str] = None
        authorized: Optional[_Authorized] = None
        try:
            with self._uow.atomic():
                self._repo.ensure_authorization_transaction()
                identity, snapshot, decision, timestamp, evaluated_at = (
                    self._evaluation(permission, context)
                )
                if not identity.is_resolved:
                    reason = f"IDENTITY_UNRESOLVED:{identity.error_code}"
                    denial = ReviewAuthorizationError(
                        "FinSight could not verify your account. Review data remains locked.",
                        reason,
                        correlation_id=correlation_id,
                    )
                else:
                    actor = identity.require_actor()
                    actor_reference = actor.actor_id
                    authorized = _Authorized(
                        actor,
                        snapshot,
                        decision,
                        timestamp,
                        evaluated_at,
                        correlation_id,
                    )
                    if decision.allowed:
                        self._uow.before_commit(
                            lambda: self._assert_commit_authorization(
                                authorized,
                                permission,
                                context,
                            )
                        )
                        result = operation(authorized)
                    else:
                        self._record_authorization(
                            authorized,
                            permission,
                            resource_type=None,
                            resource_id=None,
                        )
                        self._audit.append(
                            stream_type="SECURITY",
                            event_type="authorization_denied",
                            actor=actor,
                            occurred_at=timestamp,
                            correlation_id=correlation_id,
                            outcome="DENIED",
                            payload={
                                "permission": permission.value,
                                "reason_code": decision.reason,
                                "policy_version": snapshot.policy.version,
                                "authorization_source_version": snapshot.version,
                                "authorization_source_fingerprint": snapshot.fingerprint,
                                "effective_assignment_ids": list(
                                    decision.effective_assignment_ids
                                ),
                            },
                        )
                        denial = ReviewAuthorizationError(
                            "Your verified role does not permit this action.",
                            decision.reason,
                            correlation_id=correlation_id,
                            actor_reference=actor.actor_id,
                        )
        except CatalogedApplicationFailure as failure:
            if isinstance(failure, _CommitAuthorizationRejected):
                self._persist_commit_authorization_denial(
                    permission,
                    failure,
                )
            self._persist_diagnostic(failure.envelope)
            raise
        except Exception as exc:
            committed = bool(
                getattr(self._uow, "last_commit_completed", False)
            )
            control_plane_faulted = bool(
                getattr(self._uow, "control_plane_faulted", False)
            )
            failure_type = (
                ReviewIntegrityCheckpointError
                if committed
                else (
                    ReviewAuditIntegrityError
                    if control_plane_faulted
                    else ReviewManagementError
                )
            )
            failure = failure_type(
                (
                    "The review action was saved, but its integrity checkpoint "
                    "could not be completed."
                    if committed
                    else (
                        "Mandatory audit evidence is unavailable, so protected "
                        "actions remain locked."
                        if control_plane_faulted
                        else "FinSight could not complete the requested review action."
                    )
                ),
                correlation_id=correlation_id,
                actor_reference=actor_reference,
                mutation_outcome=(
                    MutationOutcome.COMMITTED
                    if committed
                    else MutationOutcome.NO_CHANGE
                ),
            )
            if committed and control_plane_faulted:
                self._try_reconcile_control_plane()
            self._persist_diagnostic(failure.envelope)
            raise failure from exc
        if denial is not None:
            self._persist_diagnostic(denial.envelope)
            raise denial
        return result

    def _persist_commit_authorization_denial(
        self,
        permission: Permission,
        failure: _CommitAuthorizationRejected,
    ) -> None:
        """Retain the exact commit-time denial facts after business rollback."""

        observed = failure.evidence
        original = observed.initiator
        final = observed.final_authorization
        if final is None:
            # Identity changed or became unresolved before a new actor was
            # authorized. Attribute the denial to the initiating actor and
            # retain the separately observed identity facts in the HMAC event.
            denied = replace(
                original.decision,
                allowed=False,
                reason=failure.reason_code,
            )
            decision_evidence = replace(
                original,
                decision=denied,
                timestamp=observed.observed_at,
                evaluated_at=observed.evaluated_at,
            )
            evaluation_reason = None
            evaluation_allowed = None
        else:
            # Persist the fresh snapshot and exact denied decision. If the new
            # snapshot still grants access, the commit guard itself is the
            # denial, so derive a DENY from that fresh evaluation.
            final_decision = (
                final.decision
                if not final.decision.allowed
                else replace(
                    final.decision,
                    allowed=False,
                    reason=failure.reason_code,
                )
            )
            decision_evidence = replace(final, decision=final_decision)
            evaluation_reason = final.decision.reason
            evaluation_allowed = final.decision.allowed
        try:
            with self._uow.atomic():
                self._record_authorization(
                    decision_evidence,
                    permission,
                    resource_type=None,
                    resource_id=None,
                )
                self._audit.append(
                    stream_type="SECURITY",
                    event_type="authorization_revoked_at_commit",
                    actor=original.actor,
                    occurred_at=observed.observed_at,
                    correlation_id=original.correlation_id,
                    outcome="DENIED",
                    payload={
                        "permission": permission.value,
                        "gate_reason_code": failure.reason_code,
                        "final_evaluation_allowed": evaluation_allowed,
                        "final_evaluation_reason_code": evaluation_reason,
                        "initiating_actor_id": original.actor.actor_id,
                        "initiating_actor_source": original.actor.source,
                        "observed_actor_id": (
                            observed.observed_actor.actor_id
                            if observed.observed_actor is not None
                            else None
                        ),
                        "observed_actor_source": (
                            observed.observed_actor.source
                            if observed.observed_actor is not None
                            else None
                        ),
                        "observed_identity_error_code": (
                            observed.observed_identity_error_code
                        ),
                        "authorization_source_version": (
                            decision_evidence.snapshot.version
                        ),
                        "authorization_source_fingerprint": (
                            decision_evidence.snapshot.fingerprint
                        ),
                        "effective_assignment_ids": list(
                            decision_evidence.decision.effective_assignment_ids
                        ),
                    },
                )
        except Exception as evidence_failure:
            committed = bool(
                getattr(self._uow, "last_commit_completed", False)
            )
            if committed and self._try_reconcile_control_plane():
                return
            self._uow.mark_control_plane_faulted()
            raise ReviewAuditIntegrityError(
                (
                    "Authorization was denied, but its mandatory audit "
                    "evidence could not be retained."
                ),
                correlation_id=original.correlation_id,
                actor_reference=original.actor.actor_id,
                authorization_denial=failure,
            ) from evidence_failure

    def _try_reconcile_control_plane(self) -> bool:
        try:
            self._audit.verify_all(reconcile_committed_gap=True)
        except Exception:
            return False
        self._uow.clear_control_plane_fault_after_verified_reconciliation()
        return True

    def _persist_diagnostic(self, envelope: ErrorEnvelope) -> None:
        """Best-effort privacy-safe support lookup without masking the primary failure."""

        try:
            with self._uow.atomic():
                self._repo.append_diagnostic_event(
                    diagnostic_event_id=envelope.diagnostic_event_id
                    or ("diag_" + self._id()),
                    correlation_id=envelope.correlation_id,
                    code=envelope.code,
                    category=envelope.category,
                    user_safe_cause=envelope.user_safe_cause,
                    user_safe_impact=envelope.user_safe_impact,
                    permitted_remedies=envelope.permitted_remedies,
                    retryability=envelope.retryability.value,
                    mutation_outcome=envelope.mutation_outcome.value,
                    actor_id=envelope.actor_reference,
                    component="review-management",
                    occurred_at=self._clock.now(),
                    taxonomy_version=envelope.taxonomy_version,
                )
        except Exception:
            # Diagnostics must never replace the original privacy-safe failure.
            return

    def _assert_commit_authorization(
        self,
        authorized: _Authorized,
        permission: Permission,
        context: Optional[AuthorizationContext] = None,
    ) -> None:
        """Refresh identity and authorization immediately before the UoW commits.

        A changed actor, source version, effective assignment set, or permission causes the
        business work and its audit evidence to roll back together. The caller can then retry
        against the newly accepted authorization state.
        """

        timestamp = self._clock.now()
        evaluated_at = _utc_datetime(timestamp)
        identity: IdentityResolution = self._identity.resolve_current_actor()
        if not identity.is_resolved:
            raise _CommitAuthorizationRejected(
                "Your identity changed before the operation could be committed.",
                f"IDENTITY_UNRESOLVED:{identity.error_code}",
                _CommitAuthorizationEvidence(
                    initiator=authorized,
                    observed_actor=None,
                    observed_identity_error_code=identity.error_code,
                    final_authorization=None,
                    observed_at=timestamp,
                    evaluated_at=evaluated_at,
                ),
            )
        actor = identity.require_actor()
        if (
            actor.actor_id != authorized.actor.actor_id
            or actor.source != authorized.actor.source
        ):
            raise _CommitAuthorizationRejected(
                "Your authenticated account changed before the operation could be committed.",
                "IDENTITY_CHANGED_DURING_OPERATION",
                _CommitAuthorizationEvidence(
                    initiator=authorized,
                    observed_actor=actor,
                    observed_identity_error_code=None,
                    final_authorization=None,
                    observed_at=timestamp,
                    evaluated_at=evaluated_at,
                ),
            )
        snapshot = self._snapshot(evaluated_at, actor)
        decision = self._authorization.decide(
            identity,
            permission,
            snapshot,
            evaluated_at,
            context,
        )
        final_authorization = _Authorized(
            actor=actor,
            snapshot=snapshot,
            decision=decision,
            timestamp=timestamp,
            evaluated_at=evaluated_at,
            correlation_id=authorized.correlation_id,
        )
        evidence = _CommitAuthorizationEvidence(
            initiator=authorized,
            observed_actor=actor,
            observed_identity_error_code=None,
            final_authorization=final_authorization,
            observed_at=timestamp,
            evaluated_at=evaluated_at,
        )
        if (
            snapshot.source_kind != authorized.snapshot.source_kind
            or snapshot.version != authorized.snapshot.version
            or snapshot.fingerprint != authorized.snapshot.fingerprint
            or snapshot.key_id != authorized.snapshot.key_id
            or decision.effective_assignment_ids
            != authorized.decision.effective_assignment_ids
        ):
            raise _CommitAuthorizationRejected(
                "Authorization changed before the operation could be committed. Retry the action.",
                "AUTHORIZATION_CHANGED_DURING_OPERATION",
                evidence,
            )
        if not decision.allowed:
            raise _CommitAuthorizationRejected(
                "Your current role no longer permits this action.",
                decision.reason,
                evidence,
            )

    def _record_authorization(
        self,
        authorized: _Authorized,
        permission: Permission,
        *,
        resource_type: Optional[str],
        resource_id: Optional[str],
    ) -> None:
        version = authorized.snapshot.version
        manifest_version = int(version) if str(version).isdigit() else None
        self._repo.append_authorization_decision(
            event_id="authz_" + self._id(),
            actor_id=authorized.actor.actor_id,
            permission=permission.value,
            resource_type=resource_type,
            resource_id=resource_id,
            decision="ALLOW" if authorized.decision.allowed else "DENY",
            policy_version=authorized.snapshot.policy.version,
            manifest_version=manifest_version,
            authorization_source_kind=authorized.snapshot.source_kind,
            authorization_fingerprint=authorized.snapshot.fingerprint,
            authorization_key_id=authorized.snapshot.key_id,
            effective_assignment_ids=authorized.decision.effective_assignment_ids,
            effective_roles=tuple(
                role.value for role in authorized.decision.effective_roles
            ),
            denied_roles=tuple(
                role.value for role in authorized.decision.denied_roles
            ),
            reason_code=authorized.decision.reason,
            correlation_id=authorized.correlation_id,
            occurred_at=authorized.timestamp,
        )


def candidate_owner_kind():
    # Kept as a tiny named seam to make the candidate/generation boundary explicit in tests.
    from finsight.domain.review_management import StatusOwnerKind

    return StatusOwnerKind.CANDIDATE
