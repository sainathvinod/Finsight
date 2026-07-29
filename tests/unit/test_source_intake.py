# Verifies: V2 FR-129–135 — deterministic report-level metadata gates.
from finsight.domain.review_management import ReportingPeriod
from finsight.domain.source_intake import (
    EvidenceStatus,
    ExtractionStatus,
    IntakeGateStatus,
    MetadataEvidence,
    SourceInspection,
    SourceRole,
    SourceStatus,
    evaluate_intake_pair,
)


def _inspection(
    role: SourceRole,
    *,
    department: str = "00-0245",
    period: str = "2026-05",
    name: str = "Applications Enginee",
) -> SourceInspection:
    evidence = [
        MetadataEvidence(
            "department_number",
            EvidenceStatus.PRESENT,
            department,
            department,
            "Original Budget" if role is SourceRole.BUDGET else "GED",
            "B95" if role is SourceRole.BUDGET else "A297",
        )
    ]
    if role is SourceRole.GED:
        evidence.extend(
            (
                MetadataEvidence(
                    "department_name",
                    EvidenceStatus.PRESENT,
                    name,
                    name,
                    "GED",
                    "B8:B296",
                ),
                MetadataEvidence(
                    "reporting_period",
                    EvidenceStatus.PRESENT,
                    "Year-To-Date for Period May 2026",
                    period,
                    "GED",
                    "A3",
                ),
            )
        )
    return SourceInspection(
        role=role,
        path=f"/fixtures/{role.value.lower()}.xlsx",
        file_name=f"{role.value}.xlsx",
        byte_size=100,
        sha256=("a" if role is SourceRole.BUDGET else "b") * 64,
        worksheet_name="Original Budget" if role is SourceRole.BUDGET else "GED",
        compatibility_status=SourceStatus.COMPATIBLE,
        extraction_status=ExtractionStatus.COMPLETE,
        record_count=71 if role is SourceRole.BUDGET else 258,
        evidence=tuple(evidence),
    )


def test_matching_pair_resolves_exact_raw_department_name_and_period():
    pair = evaluate_intake_pair(
        _inspection(SourceRole.BUDGET),
        _inspection(SourceRole.GED),
        ReportingPeriod(year=2026, month=5),
    )

    assert pair.gate_status is IntakeGateStatus.READY
    assert pair.department_number == "00-0245"
    assert pair.department_name == "Applications Enginee"
    assert pair.ged_period == ReportingPeriod(year=2026, month=5)
    assert pair.budget.record_count == 71
    assert pair.ged.record_count == 258


def test_report_level_department_mismatch_is_blocking():
    pair = evaluate_intake_pair(
        _inspection(SourceRole.BUDGET),
        _inspection(SourceRole.GED, department="00-0999"),
        ReportingPeriod(year=2026, month=5),
    )

    assert pair.gate_status is IntakeGateStatus.BLOCKED
    assert pair.department_number is None
    assert [issue.code for issue in pair.issues] == ["FS-MET-002"]
    assert pair.issues[0].source_references == (
        "Original Budget!B95",
        "GED!A297",
    )


def test_reporting_period_mismatch_is_blocking_without_budget_source_period():
    pair = evaluate_intake_pair(
        _inspection(SourceRole.BUDGET),
        _inspection(SourceRole.GED, period="2026-04"),
        ReportingPeriod(year=2026, month=5),
    )

    assert pair.gate_status is IntakeGateStatus.BLOCKED
    assert [issue.code for issue in pair.issues] == ["FS-MET-004"]
    assert pair.issues[0].source_references == (
        "Review workspace period",
        "GED!A3",
    )
