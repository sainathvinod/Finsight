"""Workflow 2 application integration tests using the approved synthetic reports.

Traces: V2 FR-126–137/180–183, NFR-087/090/110, AC-01/02, SLV-001.
"""
from __future__ import annotations

import hashlib
import itertools
import shutil
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path

import pytest
from openpyxl import load_workbook

from finsight.application.review_management import ReviewManagementService
from finsight.application.security import (
    AuthorizationService,
    IdentityResolution,
    StaticRoleAssignmentSource,
)
from finsight.application.source_intake import (
    SourceChangedFailure,
    SourceIntakeCoordinator,
)
from finsight.domain.identity import Actor
from finsight.domain.review_management import ReportingPeriod, ReviewStatus
from finsight.domain.source_intake import (
    IntakeGateStatus,
    MetadataEvidence,
    SourceRole,
)
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
from finsight.infrastructure.slv001_extractor import Slv001Extractor
from finsight.infrastructure.source_intake_repository import (
    SqliteSourceIntakeRepository,
)


pytestmark = pytest.mark.integration

_REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
_FIXTURE_ROOT = (
    _REPOSITORY_ROOT
    / "initiatives"
    / "configurable-rule-engine-v2"
    / "fixtures"
)
_BUDGET = _FIXTURE_ROOT / "Sample_Budget_Report.xlsx"
_GED = _FIXTURE_ROOT / "Sample_GED_Report.xlsx"
_BUDGET_SHA256 = (
    "bf40584183c564d91831214781969422d77d50439989f75750f0bdbe2bfa2b14"
)
_GED_SHA256 = (
    "2213e3f1b10fee56fb4538112250fe37fbdaf36eb5e299fbfe6d17bd0f10603c"
)
_NOW_TEXT = "2026-07-27T18:00:00Z"
_NOW = datetime(2026, 7, 27, 18, 0, tzinfo=timezone.utc)
_ACTOR = Actor("actor-source-reviewer", r"ACME\source.reviewer", "TEST_IDP")


class _Clock:
    def now(self) -> str:
        return _NOW_TEXT


class _Ids:
    def __init__(self, start: int = 1):
        self._values = itertools.count(start)

    def __call__(self) -> str:
        return f"{next(self._values):032x}"


class _Harness:
    def __init__(
        self,
        database_path: Path,
        *,
        service_ids: _Ids | None = None,
        audit_ids: _Ids | None = None,
    ):
        self.clock = _Clock()
        self.dal = Dal(
            str(database_path),
            key_provider=TestEnvironmentStoreKeyProvider(),
        )
        self.uow = SqliteUnitOfWork(self.dal)
        self.reviews = ReviewManagementRepositorySqlite(self.dal)
        self.sources = SqliteSourceIntakeRepository(self.dal)
        self.audit = AuditStreamSqlite(
            self.dal,
            self.dal.key_material.audit_key,
            self.clock,
            audit_ids or _Ids(10_000),
        )
        self.coordinator = SourceIntakeCoordinator(Slv001Extractor())
        assignments = build_local_reviewer_bootstrap_policy(_ACTOR, _NOW)
        self.service = ReviewManagementService(
            repository=self.reviews,
            audit_stream=self.audit,
            uow=self.uow,
            identity_provider=FixedIdentityProvider(
                IdentityResolution.resolved(_ACTOR)
            ),
            assignment_source=StaticRoleAssignmentSource(assignments),
            authorization=AuthorizationService(),
            clock=self.clock,
            source_intake_repository=self.sources,
            source_intake_coordinator=self.coordinator,
            id_factory=service_ids or _Ids(),
        )

    def close(self) -> None:
        self.dal.conn.close()


def _hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _inspect_approved_pair(harness: _Harness):
    budget = harness.coordinator.inspect(str(_BUDGET), SourceRole.BUDGET)
    ged = harness.coordinator.inspect(str(_GED), SourceRole.GED)
    pair = harness.coordinator.evaluate(
        budget=budget,
        ged=ged,
        selected_period=ReportingPeriod(year=2026, month=5),
    )
    return budget, ged, pair


def _replace_evidence(
    items: tuple[MetadataEvidence, ...],
    field_name: str,
    *,
    raw_value: str,
    normalized_value: str,
) -> tuple[MetadataEvidence, ...]:
    return tuple(
        replace(
            item,
            raw_value=raw_value,
            normalized_value=normalized_value,
        )
        if item.field_name == field_name
        else item
        for item in items
    )


def test_approved_synthetic_reports_extract_exact_metadata_counts_and_fingerprints():
    extractor = Slv001Extractor()

    budget = extractor.inspect(str(_BUDGET), SourceRole.BUDGET)
    ged = extractor.inspect(str(_GED), SourceRole.GED)

    assert budget.is_compatible
    assert budget.worksheet_name == "Original Budget"
    assert budget.record_count == 71
    assert budget.sha256 == _BUDGET_SHA256
    assert budget.evidence_for("department_number").raw_value == "Department 0245"
    assert (
        budget.evidence_for("department_number").normalized_value == "00-0245"
    )
    assert budget.evidence_for("reporting_period").status.value == (
        "Workspace assigned"
    )

    assert ged.is_compatible
    assert ged.worksheet_name == "GED"
    assert ged.record_count == 258
    assert ged.sha256 == _GED_SHA256
    assert ged.evidence_for("department_number").normalized_value == "00-0245"
    assert (
        ged.evidence_for("department_name").normalized_value
        == "Applications Enginee"
    )
    assert ged.evidence_for("reporting_period").raw_value == (
        "Year-To-Date for Period May 2026"
    )
    assert ged.evidence_for("reporting_period").normalized_value == "2026-05"


def test_file_type_worksheet_and_header_validation_fail_closed(tmp_path):
    extractor = Slv001Extractor()

    wrong_type = tmp_path / "Budget_Report.xls"
    shutil.copyfile(_BUDGET, wrong_type)

    wrong_sheet = tmp_path / "Budget_Wrong_Sheet.xlsx"
    shutil.copyfile(_BUDGET, wrong_sheet)
    workbook = load_workbook(wrong_sheet)
    workbook["Original Budget"].title = "Budget"
    workbook.save(wrong_sheet)
    workbook.close()

    wrong_header = tmp_path / "Budget_Wrong_Header.xlsx"
    shutil.copyfile(_BUDGET, wrong_header)
    workbook = load_workbook(wrong_header)
    workbook["Original Budget"]["A1"] = "Account"
    workbook.save(wrong_header)
    workbook.close()

    cases = (
        (wrong_type, "FS-WRK-001"),
        (wrong_sheet, "FS-SLV-001"),
        (wrong_header, "FS-SLV-002"),
    )
    for path, expected_code in cases:
        inspection = extractor.inspect(str(path), SourceRole.BUDGET)
        assert not inspection.is_compatible
        assert [issue.code for issue in inspection.issues] == [expected_code]
        assert inspection.record_count == 0


def test_draft_to_data_uploaded_commit_is_atomic_audited_and_preserves_sources(
    tmp_path,
):
    harness = _Harness(tmp_path / "finsight.db")
    before = {_BUDGET: _BUDGET.read_bytes(), _GED: _GED.read_bytes()}
    review = harness.service.create_review(
        5, 2026, idempotency_key="create-may"
    )

    harness.service.begin_source_inspection(
        review.review_id, SourceRole.BUDGET
    )
    budget = harness.coordinator.inspect(str(_BUDGET), SourceRole.BUDGET)
    harness.service.record_source_inspection(review.review_id, budget)
    harness.service.begin_source_inspection(review.review_id, SourceRole.GED)
    ged = harness.coordinator.inspect(str(_GED), SourceRole.GED)
    harness.service.record_source_inspection(review.review_id, ged)
    pair = harness.coordinator.evaluate(
        budget=budget,
        ged=ged,
        selected_period=review.period,
    )

    result = harness.service.commit_source_intake(
        review.review_id,
        pair,
        idempotency_key="save-approved-pair",
    )

    assert pair.gate_status is IntakeGateStatus.READY
    assert result.review.status is ReviewStatus.DATA_UPLOADED
    assert [row["status"] for row in harness.reviews.status_history(review.review_id)] == [
        "Draft",
        "Data Uploaded",
    ]
    assert result.persisted_summary["budget_detail_count"] == 71
    assert result.persisted_summary["ged_transaction_count"] == 258
    assert result.persisted_summary["department_match_status"] == "MATCH"
    assert result.persisted_summary["reporting_period_match_status"] == "MATCH"

    current = harness.sources.get_current_pair(review.review_id)
    assert set(current) == {"BUDGET", "GED"}
    assert current["BUDGET"]["sha256"] == _BUDGET_SHA256
    assert current["GED"]["sha256"] == _GED_SHA256
    assert current["BUDGET"]["path_hint"] == str(_BUDGET)
    assert current["GED"]["path_hint"] == str(_GED)
    assert _BUDGET.read_bytes() == before[_BUDGET]
    assert _GED.read_bytes() == before[_GED]

    event_types = [
        event.event_type
        for event in harness.audit.events(review_id=review.review_id)
    ]
    assert event_types == [
        "review_created",
        "source_inspection_started",
        "source_inspection_completed",
        "source_inspection_started",
        "source_inspection_completed",
        "source_intake_completed",
    ]
    final_event = harness.audit.events(review_id=review.review_id)[-1]
    assert final_event.actor_id == _ACTOR.actor_id
    assert final_event.payload["budget_sha256"] == _BUDGET_SHA256
    assert final_event.payload["ged_sha256"] == _GED_SHA256
    assert final_event.payload["metadata_gate_status"] == "Ready"

    # Workflow 2 stores provenance and report-level metadata, not workbook
    # bytes or extracted detail rows.
    assert harness.dal.conn.execute(
        "SELECT COUNT(*) FROM v2_source_artifacts"
    ).fetchone()[0] == 2
    assert harness.dal.conn.execute(
        "SELECT COUNT(*) FROM v2_source_binding_versions"
    ).fetchone()[0] == 2
    assert harness.dal.conn.execute(
        "SELECT COUNT(*) FROM v2_source_intake_summaries"
    ).fetchone()[0] == 1


def test_saved_intake_summary_survives_database_restart_without_detail_rows(
    tmp_path,
):
    database = tmp_path / "finsight.db"
    service_ids = _Ids()
    audit_ids = _Ids(10_000)
    first = _Harness(
        database, service_ids=service_ids, audit_ids=audit_ids
    )
    review = first.service.create_review(
        5, 2026, idempotency_key="create-may"
    )
    _budget, _ged, pair = _inspect_approved_pair(first)
    committed = first.service.commit_source_intake(
        review.review_id,
        pair,
        idempotency_key="save-approved-pair",
    )
    expected_summary_id = committed.persisted_summary["summary_id"]
    first.close()

    reopened = _Harness(
        database, service_ids=service_ids, audit_ids=audit_ids
    )
    stored = reopened.service.source_intake_summary(review.review_id)
    persisted_review = reopened.reviews.get(review.review_id)

    assert persisted_review.status is ReviewStatus.DATA_UPLOADED
    assert stored.summary_id == expected_summary_id
    assert stored.pair.gate_status is IntakeGateStatus.READY
    assert stored.pair.department_number == "00-0245"
    assert stored.pair.department_name == "Applications Enginee"
    assert stored.pair.selected_period.label == "May 2026"
    assert stored.pair.budget.record_count == 71
    assert stored.pair.ged.record_count == 258
    assert stored.pair.budget.rows == ()
    assert stored.pair.ged.rows == ()
    reopened.audit.verify_all()


def test_department_and_period_mismatches_block_metadata_gate_and_are_persistable(
    tmp_path,
):
    harness = _Harness(tmp_path / "finsight.db")
    review = harness.service.create_review(
        5, 2026, idempotency_key="create-may"
    )
    budget, ged, _pair = _inspect_approved_pair(harness)

    mismatched_department = replace(
        ged,
        evidence=_replace_evidence(
            ged.evidence,
            "department_number",
            raw_value="TOTAL FOR DEPARTMENT -  00-0999",
            normalized_value="00-0999",
        ),
    )
    department_pair = harness.coordinator.evaluate(
        budget=budget,
        ged=mismatched_department,
        selected_period=review.period,
    )
    mismatched_period = replace(
        ged,
        evidence=_replace_evidence(
            ged.evidence,
            "reporting_period",
            raw_value="Year-To-Date for Period April 2026",
            normalized_value="2026-04",
        ),
    )
    period_pair = harness.coordinator.evaluate(
        budget=budget,
        ged=mismatched_period,
        selected_period=review.period,
    )

    assert department_pair.gate_status is IntakeGateStatus.BLOCKED
    assert [issue.code for issue in department_pair.issues] == ["FS-MET-002"]
    assert period_pair.gate_status is IntakeGateStatus.BLOCKED
    assert [issue.code for issue in period_pair.issues] == ["FS-MET-004"]

    committed = harness.service.commit_source_intake(
        review.review_id,
        department_pair,
        idempotency_key="save-department-mismatch",
    )
    restored = harness.service.source_intake_summary(review.review_id)
    assert committed.review.status is ReviewStatus.DATA_UPLOADED
    assert committed.persisted_summary["department_match_status"] == "MISMATCH"
    assert committed.persisted_summary["resolved_department_number"] is None
    assert committed.pair.issues[0].correlation_id
    assert committed.pair.issues[0].permitted_remedies
    assert committed.pair.issues[0].source_references == (
        "Original Budget!B95",
        "GED!A297",
    )
    mismatch_diagnostics = harness.reviews.diagnostic_events(
        committed.pair.issues[0].correlation_id
    )
    assert [item["code"] for item in mismatch_diagnostics] == ["FS-MET-002"]
    assert mismatch_diagnostics[0]["permitted_remedies"]
    assert restored.pair.gate_status is IntakeGateStatus.BLOCKED
    assert [issue.code for issue in restored.pair.issues] == ["FS-MET-002"]
    assert (
        restored.pair.issues[0].correlation_id
        == committed.pair.issues[0].correlation_id
    )


def test_incompatible_source_cannot_partially_persist_or_advance_draft(
    tmp_path,
):
    harness = _Harness(tmp_path / "finsight.db")
    review = harness.service.create_review(
        5, 2026, idempotency_key="create-may"
    )
    invalid_path = tmp_path / "Budget_Report.xls"
    shutil.copyfile(_BUDGET, invalid_path)
    bad_budget = harness.coordinator.inspect(
        str(invalid_path), SourceRole.BUDGET
    )
    ged = harness.coordinator.inspect(str(_GED), SourceRole.GED)
    pair = harness.coordinator.evaluate(
        budget=bad_budget,
        ged=ged,
        selected_period=review.period,
    )

    cataloged = harness.service.record_source_inspection(
        review.review_id, bad_budget
    )
    with pytest.raises(ValueError, match="structurally compatible"):
        harness.service.commit_source_intake(
            review.review_id,
            pair,
            idempotency_key="must-not-save",
        )

    assert harness.reviews.get(review.review_id).status is ReviewStatus.DRAFT
    for table in (
        "v2_source_artifacts",
        "v2_source_binding_versions",
        "v2_candidate_source_heads",
        "v2_metadata_evidence_records",
        "v2_source_intake_summaries",
        "v2_source_intake_idempotency",
    ):
        assert harness.dal.conn.execute(
            f"SELECT COUNT(*) FROM {table}"
        ).fetchone()[0] == 0
    rejection = harness.audit.events(review_id=review.review_id)[-1]
    assert rejection.event_type == "source_inspection_rejected"
    assert rejection.outcome == "REJECTED"
    assert rejection.payload["issue_codes"] == ["FS-WRK-001"]
    issue = cataloged.issues[0]
    assert issue.correlation_id == rejection.correlation_id
    assert issue.permitted_remedies
    first_lookup = harness.reviews.diagnostic_events(issue.correlation_id)
    second_lookup = harness.reviews.diagnostic_events(issue.correlation_id)
    assert first_lookup == second_lookup
    assert [item["code"] for item in first_lookup] == ["FS-WRK-001"]
    assert first_lookup[0]["permitted_remedies"] == list(
        issue.permitted_remedies
    )


def test_source_changed_after_extraction_cannot_bind_or_advance_draft(
    tmp_path,
):
    harness = _Harness(tmp_path / "finsight.db")
    review = harness.service.create_review(
        5, 2026, idempotency_key="create-may"
    )
    selected_budget = tmp_path / "Selected_Budget.xlsx"
    selected_ged = tmp_path / "Selected_GED.xlsx"
    shutil.copyfile(_BUDGET, selected_budget)
    shutil.copyfile(_GED, selected_ged)
    budget = harness.coordinator.inspect(
        str(selected_budget), SourceRole.BUDGET
    )
    ged = harness.coordinator.inspect(str(selected_ged), SourceRole.GED)
    pair = harness.coordinator.evaluate(
        budget=budget,
        ged=ged,
        selected_period=review.period,
    )

    selected_budget.write_bytes(selected_budget.read_bytes() + b"changed")

    with pytest.raises(SourceChangedFailure) as captured:
        harness.service.commit_source_intake(
            review.review_id,
            pair,
            idempotency_key="changed-source-must-not-bind",
        )

    assert captured.value.envelope.code == "FS-SRC-020"
    assert harness.reviews.get(review.review_id).status is ReviewStatus.DRAFT
    assert harness.sources.get_current_pair(review.review_id) == {}
    assert harness.sources.get_summary(review.review_id) is None


def test_unexpected_inspection_failure_returns_lookup_stable_diagnostic(
    tmp_path,
):
    harness = _Harness(tmp_path / "finsight.db")
    review = harness.service.create_review(
        5, 2026, idempotency_key="create-may"
    )

    failure = harness.service.record_source_inspection_failure(
        review.review_id, SourceRole.BUDGET
    )

    assert failure.envelope.code == "FS-SRC-099"
    assert failure.envelope.correlation_id
    assert failure.envelope.permitted_remedies
    first_lookup = harness.reviews.diagnostic_events(
        failure.envelope.correlation_id
    )
    second_lookup = harness.reviews.diagnostic_events(
        failure.envelope.correlation_id
    )
    assert first_lookup == second_lookup
    assert [item["code"] for item in first_lookup] == ["FS-SRC-099"]
    assert harness.reviews.get(review.review_id).status is ReviewStatus.DRAFT
