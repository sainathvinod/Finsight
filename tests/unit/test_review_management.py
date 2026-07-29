# Verifies: V2 FR-124/125/195 — Workflow 1 period and lifecycle invariants.
from dataclasses import FrozenInstanceError

import pytest

from finsight.domain.review_management import (
    ManagedReview,
    ReportingPeriod,
    ReviewCycleRecord,
    ReviewStatus,
    ReviewStatusEvent,
    StatusOwnerKind,
    status_owner,
    require_adjacent_transition,
)

pytestmark = pytest.mark.unit


@pytest.mark.parametrize(
    ("month", "year", "label"),
    [
        (1, 1000, "January 1000"),
        (7, 2026, "July 2026"),
        (12, 9999, "December 9999"),
    ],
)
def test_reporting_period_accepts_boundaries_and_has_unambiguous_label(
    month, year, label
):
    period = ReportingPeriod(year=year, month=month)

    assert period.month_name == label.split()[0]
    assert period.label == label


@pytest.mark.parametrize(
    ("month", "year"),
    [
        (0, 2026),
        (13, 2026),
        (True, 2026),
        ("5", 2026),
        (5, 999),
        (5, 10000),
        (5, True),
        (5, "2026"),
    ],
)
def test_reporting_period_rejects_missing_or_noncanonical_values(month, year):
    with pytest.raises(ValueError):
        ReportingPeriod(year=year, month=month)


def test_reporting_period_is_immutable_and_orders_chronologically():
    may = ReportingPeriod(year=2026, month=5)
    june = ReportingPeriod(year=2026, month=6)

    assert may < june
    with pytest.raises(FrozenInstanceError):
        may.month = 6


def test_all_seven_review_statuses_have_the_approved_order_and_owner():
    statuses = (
        ReviewStatus.DRAFT,
        ReviewStatus.DATA_UPLOADED,
        ReviewStatus.DATA_REVIEWED,
        ReviewStatus.VALIDATION_COMPLETE,
        ReviewStatus.REVIEWED,
        ReviewStatus.CLOSED,
        ReviewStatus.ARCHIVED,
    )

    assert [status.value for status in statuses] == [
        "Draft",
        "Data Uploaded",
        "Data Reviewed",
        "Validation Complete",
        "Reviewed",
        "Closed",
        "Archived",
    ]
    assert status_owner(ReviewStatus.DRAFT) is StatusOwnerKind.CANDIDATE
    assert status_owner(ReviewStatus.DATA_UPLOADED) is StatusOwnerKind.CANDIDATE
    for status in statuses[2:]:
        assert status_owner(status) is StatusOwnerKind.GENERATION


def test_every_approved_forward_adjacent_transition_is_accepted():
    statuses = list(ReviewStatus)

    for previous, target in zip(statuses, statuses[1:]):
        require_adjacent_transition(previous, target)


@pytest.mark.parametrize(
    ("previous", "target"),
    [
        (ReviewStatus.DRAFT, ReviewStatus.DRAFT),
        (ReviewStatus.DRAFT, ReviewStatus.DATA_REVIEWED),
        (ReviewStatus.DATA_REVIEWED, ReviewStatus.DATA_UPLOADED),
        (ReviewStatus.CLOSED, ReviewStatus.REVIEWED),
        (ReviewStatus.ARCHIVED, ReviewStatus.DRAFT),
    ],
)
def test_skipped_same_and_backward_status_transitions_are_rejected(previous, target):
    with pytest.raises(ValueError, match="cannot move directly"):
        require_adjacent_transition(previous, target)


def _status_event(**overrides):
    values = {
        "event_id": "status_1",
        "review_id": "rev_1",
        "owner_kind": StatusOwnerKind.CANDIDATE,
        "owner_id": "cand_1",
        "sequence": 1,
        "previous_status": None,
        "status": ReviewStatus.DRAFT,
        "actor_id": "actor-1",
        "occurred_at": "2026-07-27T14:00:00Z",
        "reason": "NEW_REVIEW",
    }
    values.update(overrides)
    return ReviewStatusEvent(**values)


def test_native_status_stream_can_only_start_with_first_draft_event():
    created = _status_event()

    assert created.sequence == 1
    with pytest.raises(ValueError, match="first Draft"):
        _status_event(sequence=2)
    with pytest.raises(ValueError, match="first Draft"):
        _status_event(
            owner_kind=StatusOwnerKind.GENERATION,
            owner_id="gen_1",
            status=ReviewStatus.DATA_REVIEWED,
        )


def test_status_event_enforces_owner_kind_sequence_and_adjacency():
    with pytest.raises(ValueError, match="positive"):
        _status_event(sequence=0)
    with pytest.raises(ValueError, match="wrong owner"):
        _status_event(owner_kind=StatusOwnerKind.GENERATION)
    with pytest.raises(ValueError, match="cannot move directly"):
        _status_event(
            owner_kind=StatusOwnerKind.GENERATION,
            owner_id="gen_1",
            sequence=1,
            previous_status=ReviewStatus.DRAFT,
            status=ReviewStatus.DATA_REVIEWED,
        )


def test_managed_review_context_distinguishes_candidate_working_and_published():
    review = ReviewCycleRecord(
        review_id="rev_1",
        period=ReportingPeriod(2026, 7),
        created_by="actor-1",
        created_at="2026-07-27T14:00:00Z",
    )
    candidate = ManagedReview(
        review,
        ReviewStatus.DRAFT,
        StatusOwnerKind.CANDIDATE,
        "cand_1",
        "cand_1",
        None,
        None,
        0,
    )
    working = ManagedReview(
        review,
        ReviewStatus.DATA_REVIEWED,
        StatusOwnerKind.GENERATION,
        "gen_working",
        None,
        "gen_working",
        None,
        1,
    )
    published = ManagedReview(
        review,
        ReviewStatus.VALIDATION_COMPLETE,
        StatusOwnerKind.GENERATION,
        "gen_published",
        None,
        "gen_published",
        "gen_published",
        2,
    )

    assert candidate.context_label == "Working Candidate"
    assert working.context_label == "Working Review Version"
    assert published.context_label == "Published Review Version"
