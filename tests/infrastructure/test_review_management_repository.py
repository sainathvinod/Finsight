"""Workflow 1 persistence tests for review identity, Draft status, and history.

Traces: FR-123/FR-124/FR-195/FR-197, NFR-082/NFR-090, ADR-V2-003.
"""
from __future__ import annotations

import sqlite3
from types import SimpleNamespace

import pytest

from finsight.domain.identity import Actor
from finsight.domain.review_management import (
    ReportingPeriod,
    ReviewCycleRecord,
    ReviewPointers,
    ReviewStatus,
    ReviewStatusEvent,
    StatusOwnerKind,
    WorkingCandidate,
)
from finsight.infrastructure.migrations.runner import run_migrations
from finsight.infrastructure.persistence import SqliteUnitOfWork
from finsight.infrastructure.review_management_repository import (
    ReviewManagementRepositorySqlite,
)


ACTOR = Actor("WINDOWS:S-1-5-21-100", r"CORP\reviewer", "WINDOWS_ACCOUNT")
STAMP = "2026-07-27T18:00:00Z"


def _open(path=":memory:"):
    connection = sqlite3.connect(path)
    connection.execute("PRAGMA foreign_keys=ON")
    run_migrations(connection)
    dal = SimpleNamespace(conn=connection)
    return connection, ReviewManagementRepositorySqlite(dal), SqliteUnitOfWork(dal)


def _create(
    repository,
    uow,
    *,
    review_id="rev_001",
    candidate_id="cand_001",
    month=5,
    year=2026,
    request_key="request-001",
):
    review = ReviewCycleRecord(
        review_id=review_id,
        period=ReportingPeriod(year=year, month=month),
        created_by=ACTOR.actor_id,
        created_at=STAMP,
    )
    candidate = WorkingCandidate(
        candidate_id=candidate_id,
        review_id=review_id,
        created_by=ACTOR.actor_id,
        created_at=STAMP,
    )
    status = ReviewStatusEvent(
        event_id="status_" + review_id,
        review_id=review_id,
        owner_kind=StatusOwnerKind.CANDIDATE,
        owner_id=candidate_id,
        sequence=1,
        previous_status=None,
        status=ReviewStatus.DRAFT,
        actor_id=ACTOR.actor_id,
        occurred_at=STAMP,
        reason="NEW_REVIEW",
    )
    with uow.atomic():
        repository.create_bundle(
            review=review,
            candidate=candidate,
            pointers=ReviewPointers(review_id, candidate_id, None, None, None, 0),
            status_event=status,
            disposition_event_id="disposition_" + review_id,
            request_key=request_key,
            request_hash="hash-" + request_key,
            actor=ACTOR,
        )
    return repository.get(review_id)


def test_create_bundle_round_trips_review_period_draft_status_and_pointers():
    connection, repository, uow = _open()
    review = _create(repository, uow)

    assert review.review_id == "rev_001"
    assert review.period == ReportingPeriod(2026, 5)
    assert review.status is ReviewStatus.DRAFT
    assert review.status_owner_kind is StatusOwnerKind.CANDIDATE
    assert review.candidate_id == "cand_001"
    assert review.context_label == "Working Candidate"
    assert review.pointer_revision == 0
    assert repository.count() == 1
    assert repository.create_request("request-001")["review_id"] == "rev_001"
    assert set(repository.storage_inventory("rev_001").values()) == {0}
    connection.close()


def test_restart_reopens_persisted_review_without_recreating_it(tmp_path):
    database = str(tmp_path / "reviews.db")
    first, repository, uow = _open(database)
    expected = _create(repository, uow)
    first.close()

    reopened, repository2, _uow2 = _open(database)
    actual = repository2.get("rev_001")
    assert actual == expected
    assert repository2.count(include_archived=True) == 1
    assert len(repository2.status_history("rev_001")) == 1
    reopened.close()


def test_list_orders_periods_and_can_filter_by_latest_status():
    connection, repository, uow = _open()
    _create(
        repository,
        uow,
        review_id="rev_may",
        candidate_id="cand_may",
        month=5,
        year=2026,
        request_key="request-may",
    )
    _create(
        repository,
        uow,
        review_id="rev_june",
        candidate_id="cand_june",
        month=6,
        year=2026,
        request_key="request-june",
    )
    with uow.atomic():
        repository.append_status(
            ReviewStatusEvent(
                event_id="status_rev_june_uploaded",
                review_id="rev_june",
                owner_kind=StatusOwnerKind.CANDIDATE,
                owner_id="cand_june",
                sequence=2,
                previous_status=ReviewStatus.DRAFT,
                status=ReviewStatus.DATA_UPLOADED,
                actor_id=ACTOR.actor_id,
                occurred_at=STAMP,
                reason="SOURCE_BINDINGS_COMPLETE",
            )
        )

    assert [item.review_id for item in repository.list()] == ["rev_june", "rev_may"]
    assert [
        item.review_id
        for item in repository.list(statuses=[ReviewStatus.DATA_UPLOADED])
    ] == ["rev_june"]
    assert repository.get("rev_june").status is ReviewStatus.DATA_UPLOADED
    assert repository.next_status_sequence(
        StatusOwnerKind.CANDIDATE, "cand_june"
    ) == 3
    connection.close()


@pytest.mark.parametrize(
    ("table", "column", "value"),
    [
        ("v2_actor_snapshots", "display_name", "altered"),
        ("v2_review_disposition_events", "reason", "altered"),
        ("v2_review_status_events", "reason", "altered"),
    ],
)
def test_append_only_history_tables_reject_update_and_delete(table, column, value):
    connection, repository, uow = _open()
    _create(repository, uow)
    with pytest.raises(sqlite3.IntegrityError, match="append_only"):
        connection.execute(f"UPDATE {table} SET {column}=?", (value,))
    connection.rollback()
    with pytest.raises(sqlite3.IntegrityError, match="append_only"):
        connection.execute(f"DELETE FROM {table}")
    connection.rollback()
    connection.close()

@pytest.mark.parametrize(
    ("table", "column", "value"),
    [
        ("v2_review_cycles", "selected_month", 6),
        ("v2_working_candidates", "creation_trigger", "ALTERED"),
        ("v2_review_create_requests", "request_hash", "altered"),
    ],
)
def test_immutable_review_identity_records_reject_in_place_update(table, column, value):
    connection, repository, uow = _open()
    _create(repository, uow)
    with pytest.raises(sqlite3.IntegrityError, match="append_only"):
        connection.execute(f"UPDATE {table} SET {column}=?", (value,))
    connection.rollback()
    connection.close()
