# Implements: V2 FR-126–137/180–183, SLV-001 — immutable Workflow 2 source contracts.
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Optional

from finsight.domain.review_management import ReportingPeriod


class SourceRole(str, Enum):
    BUDGET = "BUDGET"
    GED = "GED"

    @property
    def label(self) -> str:
        return "Budget Report" if self is SourceRole.BUDGET else "GED Report"


class SourceStatus(str, Enum):
    WAITING = "Waiting"
    PROCESSING = "Processing"
    COMPATIBLE = "Compatible"
    INCOMPATIBLE = "Incompatible"


class ExtractionStatus(str, Enum):
    NOT_STARTED = "Not started"
    COMPLETE = "Extraction complete"
    FAILED = "Extraction failed"


class EvidenceStatus(str, Enum):
    PRESENT = "Present"
    ABSENT = "Absent"
    CONFLICTING = "Conflicting"
    MALFORMED = "Malformed"
    WORKSPACE_ASSIGNED = "Workspace assigned"


class IntakeGateStatus(str, Enum):
    READY = "Ready"
    BLOCKED = "Blocked"


class RowKind(str, Enum):
    BUDGET_DETAIL = "Budget detail"
    BUDGET_GROUP_TOTAL = "Budget group total"
    BUDGET_SEPARATOR = "Budget separator"
    BUDGET_GRAND_TOTAL = "Budget grand total"
    GED_TRANSACTION = "GED transaction"
    GED_ACCOUNT_TOTAL = "GED account total"
    GED_DEPARTMENT_TOTAL = "GED department total"
    GED_REPEATED_HEADER = "GED repeated header"
    GED_BLANK = "GED blank"


@dataclass(frozen=True)
class SourceIssue:
    code: str
    category: str
    message: str
    blocking: bool = True
    worksheet: Optional[str] = None
    cell: Optional[str] = None
    source_references: tuple[str, ...] = ()
    correlation_id: Optional[str] = None
    permitted_remedies: tuple[str, ...] = ()

    @property
    def location_label(self) -> str:
        if self.source_references:
            return " / ".join(self.source_references)
        if self.worksheet and self.cell:
            return f"{self.worksheet}!{self.cell}"
        return self.worksheet or self.cell or "Workbook"


@dataclass(frozen=True)
class MetadataEvidence:
    field_name: str
    status: EvidenceStatus
    raw_value: Optional[str]
    normalized_value: Optional[str]
    worksheet: Optional[str]
    cell: Optional[str]


@dataclass(frozen=True)
class CellSnapshot:
    field_name: str
    cell: str
    raw_value: Any
    cached_value: Any
    formula: Optional[str] = None


@dataclass(frozen=True)
class ExtractedRow:
    row_number: int
    kind: RowKind
    cells: tuple[CellSnapshot, ...] = ()


@dataclass(frozen=True)
class SourceInspection:
    role: SourceRole
    path: str = field(repr=False, compare=False)
    file_name: str
    byte_size: int
    sha256: str
    worksheet_name: Optional[str]
    compatibility_status: SourceStatus
    extraction_status: ExtractionStatus
    record_count: int
    issues: tuple[SourceIssue, ...] = ()
    evidence: tuple[MetadataEvidence, ...] = ()
    rows: tuple[ExtractedRow, ...] = field(default=(), repr=False, compare=False)
    profile_version: str = "SLV-001"
    safety_profile_version: str = "WRL-001"

    def __post_init__(self) -> None:
        if self.byte_size < 0:
            raise ValueError("Source byte size cannot be negative.")
        if self.sha256 and len(self.sha256) != 64:
            raise ValueError("Source fingerprints must be SHA-256 hex digests.")
        if self.compatibility_status is SourceStatus.COMPATIBLE:
            if self.extraction_status is not ExtractionStatus.COMPLETE:
                raise ValueError("A compatible source must have completed extraction.")
            if not self.sha256 or not self.worksheet_name:
                raise ValueError("A compatible source requires fingerprint and worksheet evidence.")

    @property
    def is_compatible(self) -> bool:
        return (
            self.compatibility_status is SourceStatus.COMPATIBLE
            and self.extraction_status is ExtractionStatus.COMPLETE
            and not any(issue.blocking for issue in self.issues)
        )

    @property
    def fingerprint_short(self) -> str:
        return self.sha256[:12] if self.sha256 else "Unavailable"

    def evidence_for(self, field_name: str) -> Optional[MetadataEvidence]:
        return next(
            (item for item in self.evidence if item.field_name == field_name),
            None,
        )

    @classmethod
    def rejected(
        cls,
        *,
        role: SourceRole,
        path: str,
        byte_size: int = 0,
        sha256: str = "",
        issues: tuple[SourceIssue, ...],
    ) -> "SourceInspection":
        return cls(
            role=role,
            path=path,
            file_name=Path(path).name,
            byte_size=byte_size,
            sha256=sha256,
            worksheet_name=None,
            compatibility_status=SourceStatus.INCOMPATIBLE,
            extraction_status=ExtractionStatus.FAILED,
            record_count=0,
            issues=issues,
        )


@dataclass(frozen=True)
class IntakePair:
    budget: SourceInspection
    ged: SourceInspection
    selected_period: ReportingPeriod
    gate_status: IntakeGateStatus
    department_number: Optional[str]
    department_name: Optional[str]
    ged_period: Optional[ReportingPeriod]
    issues: tuple[SourceIssue, ...]

    def __post_init__(self) -> None:
        if self.budget.role is not SourceRole.BUDGET:
            raise ValueError("The Budget source has the wrong source role.")
        if self.ged.role is not SourceRole.GED:
            raise ValueError("The GED source has the wrong source role.")
        expected = (
            IntakeGateStatus.BLOCKED
            if any(issue.blocking for issue in self.issues)
            else IntakeGateStatus.READY
        )
        if self.gate_status is not expected:
            raise ValueError("Intake gate status does not agree with its issues.")

    @property
    def pair_fingerprint(self) -> str:
        import hashlib

        material = (
            f"{self.budget.sha256}\0{self.ged.sha256}\0"
            f"{self.selected_period.year:04d}-{self.selected_period.month:02d}"
        ).encode("utf-8")
        return hashlib.sha256(material).hexdigest()


def _normalized_evidence(
    inspection: SourceInspection, field_name: str
) -> Optional[str]:
    evidence = inspection.evidence_for(field_name)
    if evidence is None or evidence.status is not EvidenceStatus.PRESENT:
        return None
    return evidence.normalized_value


def _evidence_reference(evidence: Optional[MetadataEvidence]) -> Optional[str]:
    if evidence is None:
        return None
    if evidence.worksheet and evidence.cell:
        return f"{evidence.worksheet}!{evidence.cell}"
    return evidence.worksheet or evidence.cell


def _references(*values: Optional[str]) -> tuple[str, ...]:
    return tuple(value for value in values if value)


def evaluate_intake_pair(
    budget: SourceInspection,
    ged: SourceInspection,
    selected_period: ReportingPeriod,
) -> IntakePair:
    """Evaluate report-level source identity without inspecting transaction-level exceptions."""

    issues: list[SourceIssue] = []
    if not budget.is_compatible:
        issues.append(
            SourceIssue(
                "FS-SRC-011",
                "Source compatibility",
                "The Budget Report is not structurally compatible with SLV-001.",
            )
        )
    if not ged.is_compatible:
        issues.append(
            SourceIssue(
                "FS-SRC-012",
                "Source compatibility",
                "The GED Report is not structurally compatible with SLV-001.",
            )
        )

    budget_department = _normalized_evidence(budget, "department_number")
    ged_department = _normalized_evidence(ged, "department_number")
    budget_department_evidence = budget.evidence_for("department_number")
    ged_department_evidence = ged.evidence_for("department_number")
    department_references = _references(
        _evidence_reference(budget_department_evidence),
        _evidence_reference(ged_department_evidence),
    )
    if budget.is_compatible and ged.is_compatible:
        if not budget_department or not ged_department:
            issues.append(
                SourceIssue(
                    "FS-MET-001",
                    "Metadata",
                    "A report-level Department Number is absent or malformed.",
                    source_references=department_references,
                )
            )
        elif budget_department != ged_department:
            issues.append(
                SourceIssue(
                    "FS-MET-002",
                    "Metadata",
                    "Budget and GED report-level Department Numbers do not match.",
                    source_references=department_references,
                )
            )

    department_name = _normalized_evidence(ged, "department_name")
    period_text = _normalized_evidence(ged, "reporting_period")
    ged_period_evidence = ged.evidence_for("reporting_period")
    period_references = _references(
        "Review workspace period",
        _evidence_reference(ged_period_evidence),
    )
    ged_period: Optional[ReportingPeriod] = None
    if ged.is_compatible:
        if period_text:
            try:
                year_text, month_text = period_text.split("-", 1)
                ged_period = ReportingPeriod(
                    year=int(year_text), month=int(month_text)
                )
            except (TypeError, ValueError):
                ged_period = None
        if ged_period is None:
            issues.append(
                SourceIssue(
                    "FS-MET-003",
                    "Metadata",
                    "The GED reporting period is absent or malformed.",
                    worksheet=ged.worksheet_name,
                    cell="A3",
                    source_references=period_references,
                )
            )
        elif ged_period != selected_period:
            issues.append(
                SourceIssue(
                    "FS-MET-004",
                    "Metadata",
                    "The GED reporting period does not match the selected review period.",
                    worksheet=ged.worksheet_name,
                    cell="A3",
                    source_references=period_references,
                )
            )

    resolved_department = (
        budget_department
        if budget_department and budget_department == ged_department
        else None
    )
    return IntakePair(
        budget=budget,
        ged=ged,
        selected_period=selected_period,
        gate_status=(
            IntakeGateStatus.BLOCKED
            if any(issue.blocking for issue in issues)
            else IntakeGateStatus.READY
        ),
        department_number=resolved_department,
        department_name=department_name,
        ged_period=ged_period,
        issues=tuple(issues),
    )
