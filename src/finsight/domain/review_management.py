# Implements: V2 FR-123/124/125/195/197, ADR-V2-003 — immutable Review Management contracts.
from __future__ import annotations

import calendar
from dataclasses import dataclass
from enum import Enum
from typing import Optional


class ReviewStatus(str, Enum):
    DRAFT = "Draft"
    DATA_UPLOADED = "Data Uploaded"
    DATA_REVIEWED = "Data Reviewed"
    VALIDATION_COMPLETE = "Validation Complete"
    REVIEWED = "Reviewed"
    CLOSED = "Closed"
    ARCHIVED = "Archived"


class StatusOwnerKind(str, Enum):
    CANDIDATE = "WorkingCandidate"
    GENERATION = "ReviewGeneration"


class ReviewDisposition(str, Enum):
    ACTIVE = "Active"
    ABANDONED = "Abandoned"


_STATUS_ORDER = (
    ReviewStatus.DRAFT,
    ReviewStatus.DATA_UPLOADED,
    ReviewStatus.DATA_REVIEWED,
    ReviewStatus.VALIDATION_COMPLETE,
    ReviewStatus.REVIEWED,
    ReviewStatus.CLOSED,
    ReviewStatus.ARCHIVED,
)


def status_owner(status: ReviewStatus) -> StatusOwnerKind:
    if status in (ReviewStatus.DRAFT, ReviewStatus.DATA_UPLOADED):
        return StatusOwnerKind.CANDIDATE
    return StatusOwnerKind.GENERATION


def require_adjacent_transition(previous: ReviewStatus, target: ReviewStatus) -> None:
    """Reject skips and backward lifecycle edits.

    Creating a successor candidate or generation is represented by a new owner/event stream, not by
    moving a prior immutable owner backward.
    """

    position = _STATUS_ORDER.index(previous)
    if position + 1 >= len(_STATUS_ORDER) or _STATUS_ORDER[position + 1] != target:
        raise ValueError(f"Review Status cannot move directly from {previous.value} to {target.value}.")


@dataclass(frozen=True, order=True)
class ReportingPeriod:
    year: int
    month: int

    def __post_init__(self) -> None:
        if isinstance(self.month, bool) or not isinstance(self.month, int) or not 1 <= self.month <= 12:
            raise ValueError("Reporting month must be an integer from 1 through 12.")
        if isinstance(self.year, bool) or not isinstance(self.year, int) or not 1000 <= self.year <= 9999:
            raise ValueError("Reporting year must be a four-digit integer.")

    @property
    def month_name(self) -> str:
        return calendar.month_name[self.month]

    @property
    def label(self) -> str:
        return f"{self.month_name} {self.year:04d}"


@dataclass(frozen=True)
class ReviewCycleRecord:
    review_id: str
    period: ReportingPeriod
    created_by: str
    created_at: str
    disposition: ReviewDisposition = ReviewDisposition.ACTIVE
    origin: str = "NATIVE"

    def __post_init__(self) -> None:
        if self.origin not in ("NATIVE", "LEGACY_SNAPSHOT"):
            raise ValueError("Review origin must be NATIVE or LEGACY_SNAPSHOT.")
        if not self.review_id or (self.origin == "NATIVE" and not self.review_id.startswith("rev_")):
            raise ValueError("Review ID must be an opaque FinSight review identifier.")
        if not self.created_by or not self.created_at:
            raise ValueError("A review requires an attributable creation actor and timestamp.")


@dataclass(frozen=True)
class WorkingCandidate:
    candidate_id: str
    review_id: str
    created_by: str
    created_at: str
    predecessor_generation_id: Optional[str] = None
    creation_trigger: str = "NEW_REVIEW"
    extractor_profile_id: str = "SLV-001"

    def __post_init__(self) -> None:
        if not self.candidate_id or not self.candidate_id.startswith("cand_"):
            raise ValueError("Candidate ID must be an opaque FinSight candidate identifier.")
        if not self.review_id.startswith("rev_"):
            raise ValueError("Working Candidate must belong to an opaque Review ID.")
        if not self.created_by or not self.created_at:
            raise ValueError("A Working Candidate requires an actor and timestamp.")


@dataclass(frozen=True)
class ReviewPointers:
    review_id: str
    active_candidate_id: Optional[str]
    working_generation_id: Optional[str]
    published_generation_id: Optional[str]
    current_rule_set_id: Optional[str]
    revision: int


@dataclass(frozen=True)
class ReviewStatusEvent:
    event_id: str
    review_id: str
    owner_kind: StatusOwnerKind
    owner_id: str
    sequence: int
    previous_status: Optional[ReviewStatus]
    status: ReviewStatus
    actor_id: str
    occurred_at: str
    reason: str

    def __post_init__(self) -> None:
        if self.sequence < 1:
            raise ValueError("Review Status sequence must be positive.")
        if status_owner(self.status) != self.owner_kind:
            raise ValueError("Review Status is assigned to the wrong owner kind.")
        if self.previous_status is None:
            if self.status != ReviewStatus.DRAFT or self.sequence != 1:
                raise ValueError("Only a first Draft event may start a native review-status stream.")
        else:
            require_adjacent_transition(self.previous_status, self.status)


@dataclass(frozen=True)
class ManagedReview:
    review: ReviewCycleRecord
    status: ReviewStatus
    status_owner_kind: StatusOwnerKind
    status_owner_id: str
    candidate_id: Optional[str]
    working_generation_id: Optional[str]
    published_generation_id: Optional[str]
    pointer_revision: int

    @property
    def review_id(self) -> str:
        return self.review.review_id

    @property
    def period(self) -> ReportingPeriod:
        return self.review.period

    @property
    def disposition(self) -> ReviewDisposition:
        return self.review.disposition

    @property
    def context_label(self) -> str:
        if self.status_owner_kind == StatusOwnerKind.CANDIDATE:
            return "Working Candidate"
        if self.published_generation_id == self.status_owner_id:
            return "Published Review Version"
        if self.working_generation_id == self.status_owner_id:
            return "Working Review Version"
        return "Historical Review Version"
