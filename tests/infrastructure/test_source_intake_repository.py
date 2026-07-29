"""Workflow 2 persistence tests for source identity, metadata, and atomic pairing.

Traces: FR-126–FR-135/180–183, NFR-087/NFR-110, AC-01.
"""
from __future__ import annotations

import sqlite3
from dataclasses import asdict, replace
from types import SimpleNamespace

import pytest

from finsight.infrastructure.migrations.runner import run_migrations
from finsight.infrastructure.persistence import SqliteUnitOfWork
from finsight.infrastructure.source_intake_repository import (
    SourceIntakeCommit,
    SourceIntakeEvidence,
    SourceIntakeSource,
    SqliteSourceIntakeRepository,
)


STAMP = "2026-07-27T18:00:00Z"
ACTOR_ID = "WINDOWS:S-1-5-21-100"


def _open():
    connection = sqlite3.connect(":memory:")
    connection.execute("PRAGMA foreign_keys=ON")
    run_migrations(connection)
    dal = SimpleNamespace(conn=connection)
    _seed_draft(connection)
    connection.commit()
    return connection, SqliteSourceIntakeRepository(dal), SqliteUnitOfWork(dal)


def _seed_draft(connection: sqlite3.Connection) -> None:
    connection.execute(
        "INSERT INTO cycles(cycle_id,month,year,state) VALUES('rev-1','May','2026','Created')"
    )
    connection.execute(
        "INSERT INTO v2_review_cycles("
        "review_id,selected_month,selected_year,creation_actor_id,creation_actor_display,"
        "identity_source,created_at,origin"
        ") VALUES('rev-1',5,2026,?,?,?,?,'NATIVE')",
        (ACTOR_ID, r"CORP\reviewer", "WINDOWS_ACCOUNT", STAMP),
    )
    connection.execute(
        "INSERT INTO v2_working_candidates("
        "candidate_id,review_id,predecessor_generation_id,creation_trigger,"
        "extractor_profile_id,creator_actor_id,created_at"
        ") VALUES('cand-1','rev-1',NULL,'NEW_REVIEW','SLV-001',?,?)",
        (ACTOR_ID, STAMP),
    )
    connection.execute(
        "INSERT INTO v2_review_cycle_pointers("
        "review_id,active_candidate_id,working_generation_id,published_generation_id,"
        "current_rule_set_id,revision"
        ") VALUES('rev-1','cand-1',NULL,NULL,NULL,0)"
    )


def _source(
    role: str,
    *,
    suffix: str,
    predecessor: str | None = None,
    evidence_id: str | None = None,
) -> SourceIntakeSource:
    budget = role == "BUDGET"
    return SourceIntakeSource(
        source_role=role,
        artifact_id=f"artifact-{role.lower()}-{suffix}",
        binding_id=f"binding-{role.lower()}-{suffix}",
        filename=(
            f"Sample_Budget_Report_{suffix}.xlsx"
            if budget
            else f"Sample_GED_Report_{suffix}.xlsx"
        ),
        byte_size=10132 if budget else 26452,
        sha256=("a" if budget else "b") * 63 + suffix[-1],
        path_hint=(
            f"/fixtures/budget-{suffix}.xlsx"
            if budget
            else f"/fixtures/ged-{suffix}.xlsx"
        ),
        selected_actor_id=ACTOR_ID,
        selected_at=STAMP,
        bound_actor_id=ACTOR_ID,
        bound_at=STAMP,
        worksheet_name="Original Budget" if budget else "GED",
        upload_status="SUCCEEDED",
        compatibility_status="COMPATIBLE",
        extraction_status="SUCCEEDED",
        predecessor_binding_id=predecessor,
        replacement_reason="INITIAL_INTAKE" if predecessor is None else "REPLACEMENT",
        evidence=(
            SourceIntakeEvidence(
                evidence_id=evidence_id,
                evidence_type="DEPARTMENT_NUMBER",
                evidence_status="PRESENT",
                raw_scalar=(
                    "Department 0245"
                    if budget
                    else "TOTAL FOR DEPARTMENT -  00-0245"
                ),
                normalized_scalar="00-0245",
                worksheet_name="Original Budget" if budget else "GED",
                cell_reference="B95" if budget else "A297",
                source_row=95 if budget else 297,
                source_column=2 if budget else 1,
            ),
        ),
    )


def _commit(
    *,
    suffix: str = "1",
    idempotency_key: str = "intake-1",
    summary_id: str = "summary-1",
    predecessors: tuple[str | None, str | None] = (None, None),
    evidence_id: str | None = None,
) -> SourceIntakeCommit:
    return SourceIntakeCommit(
        review_id="rev-1",
        candidate_id="cand-1",
        idempotency_key=idempotency_key,
        request_hash=f"request-hash-{suffix}",
        summary_id=summary_id,
        committed_actor_id=ACTOR_ID,
        committed_at=STAMP,
        selected_month=5,
        selected_year=2026,
        resolved_department_number="00-0245",
        resolved_department_name="Applications Enginee",
        department_evidence_status="PRESENT",
        period_evidence_status="PRESENT",
        department_match_status="MATCH",
        reporting_period_match_status="MATCH",
        budget_detail_count=71,
        ged_transaction_count=258,
        extraction_profile_version="SLV-001-EXTRACTOR-1",
        layout_profile_version="SLV-001",
        safety_policy_version="WRL-001",
        metadata_policy_version="V1-METADATA-1",
        sources=(
            _source(
                "BUDGET",
                suffix=suffix,
                predecessor=predecessors[0],
                evidence_id=evidence_id,
            ),
            _source(
                "GED",
                suffix=suffix,
                predecessor=predecessors[1],
                evidence_id=evidence_id,
            ),
        ),
    )


def test_commit_pair_round_trips_source_identity_metadata_and_idempotency():
    connection, repository, uow = _open()
    commit = _commit()

    with uow.atomic():
        summary = repository.commit_pair(asdict(commit))
    before = {
        table: connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        for table in (
            "v2_source_artifacts",
            "v2_source_binding_versions",
            "v2_metadata_evidence_records",
            "v2_source_intake_summaries",
            "v2_source_intake_idempotency",
        )
    }
    with uow.atomic():
        replay = repository.commit_pair(commit)

    assert replay == summary
    assert summary["resolved_department_name"] == "Applications Enginee"
    assert summary["budget_detail_count"] == 71
    assert summary["ged_transaction_count"] == 258
    assert len(summary["summary_hash"]) == 64
    pair = repository.get_current_pair("rev-1")
    assert set(pair) == {"BUDGET", "GED"}
    assert pair["BUDGET"]["filename"] == "Sample_Budget_Report_1.xlsx"
    assert pair["BUDGET"]["head_revision"] == 1
    assert pair["GED"]["evidence"][0]["cell_reference"] == "A297"
    assert repository.get_summary("rev-1") == summary
    after = {
        table: connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        for table in before
    }
    assert after == before
    connection.close()


def test_replacement_appends_predecessors_and_advances_only_mutable_heads():
    connection, repository, uow = _open()
    first = _commit()
    with uow.atomic():
        repository.commit_pair(first)

    second = _commit(
        suffix="2",
        idempotency_key="intake-2",
        summary_id="summary-2",
        predecessors=("binding-budget-1", "binding-ged-1"),
    )
    with uow.atomic():
        current = repository.commit_pair(second)

    pair = repository.get_current_pair("rev-1")
    assert pair["BUDGET"]["predecessor_binding_id"] == "binding-budget-1"
    assert pair["GED"]["predecessor_binding_id"] == "binding-ged-1"
    assert pair["BUDGET"]["head_revision"] == 2
    assert current["predecessor_summary_id"] == "summary-1"
    assert current["summary_sequence"] == 2
    assert connection.execute(
        "SELECT COUNT(*) FROM v2_source_binding_versions"
    ).fetchone()[0] == 4

    with pytest.raises(sqlite3.IntegrityError, match="append_only"):
        connection.execute(
            "UPDATE v2_source_binding_versions SET replacement_reason='ALTERED'"
        )
    connection.rollback()
    connection.close()


def test_atomic_failure_leaves_no_partial_source_intake_records():
    connection, repository, uow = _open()
    commit = _commit(evidence_id="duplicate-evidence-id")

    with pytest.raises(sqlite3.IntegrityError):
        with uow.atomic():
            repository.commit_pair(commit)

    for table in (
        "v2_source_artifacts",
        "v2_source_binding_versions",
        "v2_candidate_source_heads",
        "v2_metadata_evidence_records",
        "v2_source_intake_summaries",
        "v2_source_intake_idempotency",
    ):
        assert connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0] == 0
    connection.close()


def test_commit_pair_is_transaction_neutral_and_idempotency_collision_is_rejected():
    connection, repository, _uow = _open()
    repository.commit_pair(_commit())
    assert connection.in_transaction
    connection.rollback()
    assert repository.get_summary("rev-1") is None

    uow = SqliteUnitOfWork(SimpleNamespace(conn=connection))
    with uow.atomic():
        repository.commit_pair(_commit())
    conflicting = replace(_commit(), request_hash="different-request")
    with pytest.raises(ValueError, match="idempotency"):
        with uow.atomic():
            repository.commit_pair(conflicting)
    assert connection.execute(
        "SELECT COUNT(*) FROM v2_source_intake_summaries"
    ).fetchone()[0] == 1
    connection.close()
