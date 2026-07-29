# Implements: V2 FR-126–137/180–183, NFR-087/088 — Workflow 2 orchestration.
from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Optional

from finsight.application.failure_contracts import (
    CatalogedApplicationFailure,
    ErrorEnvelope,
    MutationOutcome,
    Retryability,
)
from finsight.domain.review_management import ReportingPeriod
from finsight.domain.source_intake import (
    EvidenceStatus,
    ExtractionStatus,
    IntakePair,
    MetadataEvidence,
    SourceInspection,
    SourceRole,
    SourceStatus,
    evaluate_intake_pair,
)


class SourceIntakeFailure(CatalogedApplicationFailure):
    code = "FS-SRC-001"
    category = "Source intake"
    impact = "No source was bound and the saved review was not changed."
    remedy = "Correct or reselect the source workbook, then retry."
    retryability = Retryability.RETRY_AFTER_CORRECTION

    def __init__(
        self,
        cause: str,
        *,
        code: Optional[str] = None,
        category: Optional[str] = None,
        correlation_id: Optional[str] = None,
    ) -> None:
        super().__init__(
            ErrorEnvelope.build(
                code=code or self.code,
                category=category or self.category,
                correlation_id=correlation_id
                or ("corr_source_" + uuid.uuid4().hex),
                cause=cause,
                impact=self.impact,
                remedies=(self.remedy,),
                retryability=self.retryability,
                mutation_outcome=MutationOutcome.NO_CHANGE,
                diagnostic_event_id="diag_" + uuid.uuid4().hex,
            )
        )


class SourceChangedFailure(SourceIntakeFailure):
    def __init__(self, role: SourceRole) -> None:
        super().__init__(
            f"The selected {role.label} changed after extraction.",
            code="FS-SRC-020",
        )


@dataclass(frozen=True)
class PreparedSourceIntake:
    pair: IntakePair
    idempotency_key: str

    def __post_init__(self) -> None:
        if not self.idempotency_key.strip():
            raise ValueError("Source intake requires an idempotency key.")


@dataclass(frozen=True)
class SourceIntakeResult:
    review: object
    pair: IntakePair
    persisted_summary: dict
    idempotent_replay: bool = False


@dataclass(frozen=True)
class StoredSourceIntake:
    pair: IntakePair
    summary_id: str
    committed_actor_id: str
    committed_at: str


def restore_source_intake(
    summary: dict,
    current_sources: dict[str, dict],
) -> StoredSourceIntake:
    """Restore the report-level intake projection without restoring workbook rows or bytes."""

    selected_period = ReportingPeriod(
        year=int(summary["selected_year"]),
        month=int(summary["selected_month"]),
    )

    def inspection(role: SourceRole) -> SourceInspection:
        record = current_sources[role.value]
        evidence = tuple(
            MetadataEvidence(
                field_name=_restore_evidence_name(item["evidence_type"]),
                status=_restore_evidence_status(item["evidence_status"]),
                raw_value=item.get("raw_scalar"),
                normalized_value=item.get("normalized_scalar"),
                worksheet=item.get("worksheet_name"),
                cell=item.get("cell_reference"),
            )
            for item in record.get("evidence", ())
        )
        return SourceInspection(
            role=role,
            path=record.get("path_hint") or "",
            file_name=record["filename"],
            byte_size=int(record["byte_size"]),
            sha256=record["sha256"],
            worksheet_name=(
                summary["budget_worksheet"]
                if role is SourceRole.BUDGET
                else summary["ged_worksheet"]
            ),
            compatibility_status=SourceStatus.COMPATIBLE,
            extraction_status=ExtractionStatus.COMPLETE,
            record_count=int(
                summary["budget_detail_count"]
                if role is SourceRole.BUDGET
                else summary["ged_transaction_count"]
            ),
            evidence=evidence,
            profile_version=summary["layout_profile_version"],
            safety_profile_version=summary["safety_policy_version"],
        )

    pair = evaluate_intake_pair(
        inspection(SourceRole.BUDGET),
        inspection(SourceRole.GED),
        selected_period,
    )
    return StoredSourceIntake(
        pair=pair,
        summary_id=summary["summary_id"],
        committed_actor_id=summary["committed_actor_id"],
        committed_at=summary["committed_at"],
    )


def _restore_evidence_status(value: str) -> EvidenceStatus:
    for status in EvidenceStatus:
        if value in (status.value, status.name):
            return status
    return EvidenceStatus.MALFORMED


def _restore_evidence_name(value: str) -> str:
    return {
        "DEPARTMENT_NUMBER": "department_number",
        "DEPARTMENT_NAME": "department_name",
        "REPORTING_PERIOD": "reporting_period",
        "REPORTING_PERIOD_DISPLAY": "reporting_period_display",
        "RUN_DATE": "run_date",
        "WORKSHEET": "worksheet",
    }.get(value, value.lower())


class SourceIntakeCoordinator:
    """Presentation-neutral two-source coordinator.

    File reads and workbook extraction remain outside the database transaction. The
    protected Review Management service performs the final fingerprint recheck and
    persists both bindings, lifecycle status, and audit evidence atomically.
    """

    def __init__(self, extractor) -> None:
        self._extractor = extractor

    def inspect(self, path: str, role: SourceRole) -> SourceInspection:
        if not isinstance(role, SourceRole):
            role = SourceRole(role)
        if not path or not str(path).strip():
            raise SourceIntakeFailure(
                f"Select a {role.label} workbook before starting extraction."
            )
        return self._extractor.inspect(str(path), role)

    @staticmethod
    def evaluate(
        *,
        budget: SourceInspection,
        ged: SourceInspection,
        selected_period: ReportingPeriod,
    ) -> IntakePair:
        return evaluate_intake_pair(budget, ged, selected_period)

    def prepare(
        self,
        *,
        budget: SourceInspection,
        ged: SourceInspection,
        selected_period: ReportingPeriod,
        idempotency_key: str,
    ) -> PreparedSourceIntake:
        return PreparedSourceIntake(
            pair=self.evaluate(
                budget=budget,
                ged=ged,
                selected_period=selected_period,
            ),
            idempotency_key=idempotency_key,
        )

    def assert_unchanged(self, inspection: SourceInspection) -> None:
        if not self._extractor.verify_unchanged(
            inspection.path,
            expected_sha256=inspection.sha256,
            expected_size=inspection.byte_size,
        ):
            raise SourceChangedFailure(inspection.role)

    def assert_pair_unchanged(self, pair: IntakePair) -> None:
        self.assert_unchanged(pair.budget)
        self.assert_unchanged(pair.ged)
