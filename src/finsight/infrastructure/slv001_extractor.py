# Implements: V2 FR-126–135/180–183, SLV-001 and ADR-V2-006.
"""Exact, read-only extraction for the supplied Budget and GED report layouts."""
from __future__ import annotations

import calendar
import io
import re
import time
from contextlib import contextmanager
from typing import Any, Callable, Iterator, Sequence

from openpyxl import load_workbook
from openpyxl.utils import get_column_letter

from finsight.domain.source_intake import (
    CellSnapshot,
    EvidenceStatus,
    ExtractedRow,
    ExtractionStatus,
    MetadataEvidence,
    RowKind,
    SourceInspection,
    SourceIssue,
    SourceRole,
    SourceStatus,
)
from finsight.infrastructure.workbook_safety import (
    WorkbookSafetyInspector,
    WorkbookSafetyViolation,
    WorkbookSnapshot,
)


_BUDGET_SHEET = "Original Budget"
_GED_SHEET = "GED"
_GED_TITLE = "REPORT LIBRARY TITLE: General Expense Detail Report"

_BUDGET_HEADERS = (
    "Account #",
    "Account Name",
    "bgt",
    "atd",
    "etc",
    "eac",
    "delta",
    "Notes",
)
_BUDGET_FIELDS = (
    "account_number",
    "account_name",
    "bgt",
    "atd",
    "etc",
    "eac",
    "delta",
    "notes",
)
_GED_HEADERS = (
    "DEPT. #",
    "DEPT NAME",
    "ACCOUNT NUMBER",
    "ACCOUNT NAME",
    "FISCAL PERIOD",
    "JOURNAL #",
    "JOURNAL DATE",
    "INVOICE AMT",
    "CHECK #",
    "INVOICE DATE",
    "VENDOR NAME",
    "AGENCY",
    "JOURNAL DESCRIPTION",
    "JOURNAL LINE DESCRIPTION",
    "AMOUNT",
)
_GED_FIELDS = (
    "department_number",
    "department_name",
    "account_number",
    "account_name",
    "fiscal_period",
    "journal_number",
    "journal_date",
    "invoice_amount",
    "check_number",
    "invoice_date",
    "vendor_name",
    "agency",
    "journal_description",
    "journal_line_description",
    "amount",
)
_BUDGET_DEPARTMENT = re.compile(r"^Department ([0-9]{4})$")
_GED_ACCOUNT_TOTAL = re.compile(r"^TOTAL FOR ACCOUNT -  ([0-9]{6})$")
_GED_DEPARTMENT_TOTAL = re.compile(
    r"^TOTAL FOR DEPARTMENT -  ([0-9]{2}-[0-9]{4})$"
)
_GED_PERIOD = re.compile(
    r"^Year-To-Date for Period "
    r"(January|February|March|April|May|June|July|August|September|October|"
    r"November|December) ([0-9]{4})$"
)


class _ProfileViolation(RuntimeError):
    def __init__(self, *issues: SourceIssue) -> None:
        super().__init__(issues[0].message if issues else "SLV-001 profile violation")
        self.issues = tuple(issues)


class Slv001Extractor:
    """Classify one selected workbook under the exact first-release layout."""

    def __init__(
        self,
        safety: WorkbookSafetyInspector | None = None,
        *,
        monotonic: Callable[[], float] = time.monotonic,
    ) -> None:
        self.safety = safety or WorkbookSafetyInspector(monotonic=monotonic)
        self._monotonic = monotonic

    def inspect(self, path: str, role: SourceRole) -> SourceInspection:
        if not isinstance(role, SourceRole):
            role = SourceRole(role)
        started = self._monotonic()
        try:
            snapshot = self.safety.inspect(path)
        except WorkbookSafetyViolation as violation:
            return SourceInspection.rejected(
                role=role,
                path=path,
                byte_size=violation.byte_size,
                sha256=violation.sha256,
                issues=(violation.issue,),
            )

        try:
            if role is SourceRole.BUDGET:
                return self._inspect_budget(snapshot, started)
            return self._inspect_ged(snapshot, started)
        except _ProfileViolation as violation:
            return SourceInspection.rejected(
                role=role,
                path=path,
                byte_size=snapshot.byte_size,
                sha256=snapshot.sha256,
                issues=violation.issues,
            )
        except Exception:
            return SourceInspection.rejected(
                role=role,
                path=path,
                byte_size=snapshot.byte_size,
                sha256=snapshot.sha256,
                issues=(
                    SourceIssue(
                        "FS-SLV-099",
                        "Source compatibility",
                        "The workbook could not be interpreted safely under SLV-001.",
                    ),
                ),
            )

    def verify_unchanged(
        self, path: str, expected_sha256: str, expected_size: int
    ) -> bool:
        return self.safety.verify_unchanged(path, expected_sha256, expected_size)

    def _inspect_budget(
        self, snapshot: WorkbookSnapshot, started: float
    ) -> SourceInspection:
        with _dual_workbooks(snapshot) as (formula_book, cached_book):
            formula_sheet, cached_sheet, max_row = self._sheets(
                formula_book,
                cached_book,
                _BUDGET_SHEET,
                minimum_row=2,
            )
            row_pairs = _paired_rows(
                formula_sheet,
                cached_sheet,
                max_row=max_row,
                max_column=len(_BUDGET_HEADERS),
            )

            extracted: list[ExtractedRow] = []
            detail_accounts: dict[str, int] = {}
            detail_count = 0
            grand_row: int | None = None
            department_raw: str | None = None
            department_number: str | None = None

            for row_number, formula_row, cached_row in row_pairs:
                self._check_deadline(started)
                values = tuple(cell.value for cell in formula_row)
                if row_number == 1:
                    issues = _header_issues(
                        worksheet=_BUDGET_SHEET,
                        row_number=1,
                        observed=values,
                        expected=_BUDGET_HEADERS,
                    )
                    if issues:
                        raise _ProfileViolation(*issues)
                    continue

                if grand_row is not None:
                    if not _row_is_blank(values):
                        raise _ProfileViolation(
                            _structure_issue(
                                "FS-SLV-006",
                                "The Budget Grand Total must be the final populated report row.",
                                _BUDGET_SHEET,
                                f"A{row_number}:H{row_number}",
                            )
                        )
                    continue

                if _row_is_blank(values):
                    extracted.append(
                        ExtractedRow(row_number, RowKind.BUDGET_SEPARATOR)
                    )
                    continue

                account_value = values[0]
                account_text = _outer_text(account_value)
                if account_text == "Grand Total":
                    department_raw = _raw_text(values[1])
                    match = _BUDGET_DEPARTMENT.fullmatch(
                        _outer_text(values[1])
                    )
                    if match is None:
                        raise _ProfileViolation(
                            _structure_issue(
                                "FS-SLV-007",
                                "The Budget Grand Total requires 'Department NNNN' in column B.",
                                _BUDGET_SHEET,
                                f"B{row_number}",
                            )
                        )
                    grand_row = row_number
                    department_number = f"00-{match.group(1)}"
                    extracted.append(
                        ExtractedRow(
                            row_number,
                            RowKind.BUDGET_GRAND_TOTAL,
                            _cell_snapshots(
                                formula_row,
                                cached_row,
                                _BUDGET_FIELDS,
                                row_number,
                            ),
                        )
                    )
                    continue

                account_number = _account_token(account_value)
                if account_number is None or len(account_number) not in (3, 6):
                    raise _ProfileViolation(
                        _structure_issue(
                            "FS-SLV-008",
                            "The Budget row is not an SLV-001 detail, group, separator, or Grand Total row.",
                            _BUDGET_SHEET,
                            f"A{row_number}:H{row_number}",
                        )
                    )
                if _is_blank(values[1]):
                    raise _ProfileViolation(
                        _structure_issue(
                            "FS-SLV-009",
                            "An SLV-001 Budget detail or group row requires an Account Name.",
                            _BUDGET_SHEET,
                            f"B{row_number}",
                        )
                    )

                if len(account_number) == 6:
                    previous = detail_accounts.get(account_number)
                    if previous is not None:
                        raise _ProfileViolation(
                            _structure_issue(
                                "FS-SLV-010",
                                "The Budget contains a duplicate six-digit detail account.",
                                _BUDGET_SHEET,
                                f"A{row_number}",
                            )
                        )
                    detail_accounts[account_number] = row_number
                    detail_count += 1
                    row_kind = RowKind.BUDGET_DETAIL
                else:
                    row_kind = RowKind.BUDGET_GROUP_TOTAL
                extracted.append(
                    ExtractedRow(
                        row_number,
                        row_kind,
                        _cell_snapshots(
                            formula_row,
                            cached_row,
                            _BUDGET_FIELDS,
                            row_number,
                        ),
                    )
                )

            if grand_row is None or department_number is None:
                raise _ProfileViolation(
                    _structure_issue(
                        "FS-SLV-011",
                        "The Budget requires one final Grand Total department row.",
                        _BUDGET_SHEET,
                        "A2:H2",
                    )
                )

        evidence = (
            MetadataEvidence(
                "worksheet",
                EvidenceStatus.PRESENT,
                _BUDGET_SHEET,
                _BUDGET_SHEET,
                _BUDGET_SHEET,
                None,
            ),
            MetadataEvidence(
                "department_number",
                EvidenceStatus.PRESENT,
                department_raw,
                department_number,
                _BUDGET_SHEET,
                f"B{grand_row}",
            ),
            MetadataEvidence(
                "reporting_period",
                EvidenceStatus.WORKSPACE_ASSIGNED,
                None,
                None,
                _BUDGET_SHEET,
                None,
            ),
        )
        return SourceInspection(
            role=SourceRole.BUDGET,
            path=snapshot.path,
            file_name=snapshot.file_name,
            byte_size=snapshot.byte_size,
            sha256=snapshot.sha256,
            worksheet_name=_BUDGET_SHEET,
            compatibility_status=SourceStatus.COMPATIBLE,
            extraction_status=ExtractionStatus.COMPLETE,
            record_count=detail_count,
            evidence=evidence,
            rows=tuple(extracted),
        )

    def _inspect_ged(
        self, snapshot: WorkbookSnapshot, started: float
    ) -> SourceInspection:
        with _dual_workbooks(snapshot) as (formula_book, cached_book):
            formula_sheet, cached_sheet, max_row = self._sheets(
                formula_book,
                cached_book,
                _GED_SHEET,
                minimum_row=8,
            )
            row_pairs = _paired_rows(
                formula_sheet,
                cached_sheet,
                max_row=max_row,
                max_column=len(_GED_HEADERS),
            )

            extracted: list[ExtractedRow] = []
            transaction_count = 0
            department_total_row: int | None = None
            department_total_raw: str | None = None
            department_number: str | None = None
            period_raw: str | None = None
            run_date_raw: str | None = None
            department_names: list[tuple[str, str, int]] = []

            for row_number, formula_row, cached_row in row_pairs:
                self._check_deadline(started)
                values = tuple(cell.value for cell in formula_row)
                if row_number == 1:
                    if _outer_text(values[0]) != _GED_TITLE:
                        raise _ProfileViolation(
                            _structure_issue(
                                "FS-SLV-012",
                                "The GED report title is missing from its required row.",
                                _GED_SHEET,
                                "A1",
                            )
                        )
                    continue
                if row_number == 3:
                    period_raw = _raw_text(values[0])
                    continue
                if row_number == 4:
                    run_date_raw = _raw_text(values[0])
                    continue
                if row_number == 7:
                    issues = _header_issues(
                        worksheet=_GED_SHEET,
                        row_number=7,
                        observed=values,
                        expected=_GED_HEADERS,
                    )
                    if issues:
                        raise _ProfileViolation(*issues)
                    continue
                if row_number < 8:
                    continue

                snapshots = _cell_snapshots(
                    formula_row,
                    cached_row,
                    _GED_FIELDS,
                    row_number,
                )
                if department_total_row is not None:
                    if not _row_is_blank(values):
                        raise _ProfileViolation(
                            _structure_issue(
                                "FS-SLV-013",
                                "The GED department total must be the final nonblank A:O row.",
                                _GED_SHEET,
                                f"A{row_number}:O{row_number}",
                            )
                        )
                    extracted.append(
                        ExtractedRow(row_number, RowKind.GED_BLANK)
                    )
                    continue

                if _row_is_blank(values):
                    extracted.append(
                        ExtractedRow(row_number, RowKind.GED_BLANK)
                    )
                    continue
                if _is_repeated_header(values):
                    extracted.append(
                        ExtractedRow(
                            row_number,
                            RowKind.GED_REPEATED_HEADER,
                            snapshots,
                        )
                    )
                    continue

                first = _outer_text(values[0])
                account_total = _GED_ACCOUNT_TOTAL.fullmatch(first)
                department_total = _GED_DEPARTMENT_TOTAL.fullmatch(first)
                total_shape = (
                    all(_is_blank(value) for value in values[1:14])
                    and not _is_blank(values[14])
                )
                if account_total is not None and total_shape:
                    extracted.append(
                        ExtractedRow(
                            row_number,
                            RowKind.GED_ACCOUNT_TOTAL,
                            snapshots,
                        )
                    )
                    continue
                if department_total is not None and total_shape:
                    department_total_row = row_number
                    department_total_raw = _raw_text(values[0])
                    department_number = department_total.group(1)
                    extracted.append(
                        ExtractedRow(
                            row_number,
                            RowKind.GED_DEPARTMENT_TOTAL,
                            snapshots,
                        )
                    )
                    continue
                if first.startswith(
                    ("TOTAL FOR ACCOUNT", "TOTAL FOR DEPARTMENT")
                ):
                    raise _ProfileViolation(
                        _structure_issue(
                            "FS-SLV-014",
                            "A GED total-like row does not match the exact SLV-001 total shape.",
                            _GED_SHEET,
                            f"A{row_number}:O{row_number}",
                        )
                    )

                transaction_count += 1
                if transaction_count > self.safety.limits.ged_transactions:
                    raise _ProfileViolation(
                        _structure_issue(
                            "FS-SLV-015",
                            "The GED exceeds the WRL-001 transaction limit.",
                            _GED_SHEET,
                            f"A{row_number}:O{row_number}",
                        )
                    )
                extracted.append(
                    ExtractedRow(
                        row_number,
                        RowKind.GED_TRANSACTION,
                        snapshots,
                    )
                )
                canonical_department = _canonical_department(values[0])
                name = _outer_text(values[1])
                if canonical_department is not None and name:
                    department_names.append(
                        (canonical_department, name, row_number)
                    )

            if department_total_row is None or department_number is None:
                raise _ProfileViolation(
                    _structure_issue(
                        "FS-SLV-016",
                        "The GED requires one exact final Department Total row.",
                        _GED_SHEET,
                        "A8:O8",
                    )
                )

        period_evidence = _period_evidence(period_raw)
        department_name_evidence = _department_name_evidence(
            department_names,
            department_number,
        )
        run_date_status = (
            EvidenceStatus.ABSENT
            if _is_blank(run_date_raw)
            else EvidenceStatus.PRESENT
        )
        evidence = (
            MetadataEvidence(
                "worksheet",
                EvidenceStatus.PRESENT,
                _GED_SHEET,
                _GED_SHEET,
                _GED_SHEET,
                None,
            ),
            MetadataEvidence(
                "department_number",
                EvidenceStatus.PRESENT,
                department_total_raw,
                department_number,
                _GED_SHEET,
                f"A{department_total_row}",
            ),
            department_name_evidence,
            period_evidence,
            MetadataEvidence(
                "run_date",
                run_date_status,
                run_date_raw,
                _outer_text(run_date_raw) or None,
                _GED_SHEET,
                "A4",
            ),
        )
        return SourceInspection(
            role=SourceRole.GED,
            path=snapshot.path,
            file_name=snapshot.file_name,
            byte_size=snapshot.byte_size,
            sha256=snapshot.sha256,
            worksheet_name=_GED_SHEET,
            compatibility_status=SourceStatus.COMPATIBLE,
            extraction_status=ExtractionStatus.COMPLETE,
            record_count=transaction_count,
            evidence=evidence,
            rows=tuple(extracted),
        )

    @staticmethod
    def _sheets(
        formula_book,
        cached_book,
        expected_name: str,
        *,
        minimum_row: int,
    ):
        if (
            expected_name not in formula_book.sheetnames
            or expected_name not in cached_book.sheetnames
        ):
            raise _ProfileViolation(
                _structure_issue(
                    "FS-SLV-001",
                    f"The workbook requires the '{expected_name}' worksheet.",
                    expected_name,
                    None,
                )
            )
        formula_sheet = formula_book[expected_name]
        cached_sheet = cached_book[expected_name]
        formula_sheet.calculate_dimension(force=True)
        cached_sheet.calculate_dimension(force=True)
        max_row = max(
            formula_sheet.max_row or 0,
            cached_sheet.max_row or 0,
            minimum_row,
        )
        return formula_sheet, cached_sheet, max_row

    def _check_deadline(self, started: float) -> None:
        if self._monotonic() - started > self.safety.limits.wall_seconds:
            raise _ProfileViolation(
                SourceIssue(
                    "FS-WRK-026",
                    "Workbook safety",
                    "Workbook processing exceeded the WRL-001 time limit.",
                )
            )


@contextmanager
def _dual_workbooks(snapshot: WorkbookSnapshot) -> Iterator[tuple[Any, Any]]:
    formula_book = None
    cached_book = None
    try:
        formula_book = load_workbook(
            io.BytesIO(snapshot.content),
            read_only=True,
            data_only=False,
            keep_links=False,
        )
        cached_book = load_workbook(
            io.BytesIO(snapshot.content),
            read_only=True,
            data_only=True,
            keep_links=False,
        )
        yield formula_book, cached_book
    finally:
        if formula_book is not None:
            formula_book.close()
        if cached_book is not None:
            cached_book.close()


def _paired_rows(
    formula_sheet,
    cached_sheet,
    *,
    max_row: int,
    max_column: int,
):
    formula_rows = formula_sheet.iter_rows(
        min_row=1,
        max_row=max_row,
        min_col=1,
        max_col=max_column,
    )
    cached_rows = cached_sheet.iter_rows(
        min_row=1,
        max_row=max_row,
        min_col=1,
        max_col=max_column,
    )
    for row_number, (formula_row, cached_row) in enumerate(
        zip(formula_rows, cached_rows),
        start=1,
    ):
        yield row_number, formula_row, cached_row


def _cell_snapshots(
    formula_row: Sequence[Any],
    cached_row: Sequence[Any],
    fields: Sequence[str],
    row_number: int,
) -> tuple[CellSnapshot, ...]:
    result: list[CellSnapshot] = []
    for column_number, (formula_cell, cached_cell, field_name) in enumerate(
        zip(formula_row, cached_row, fields),
        start=1,
    ):
        is_formula = getattr(formula_cell, "data_type", None) == "f"
        raw = formula_cell.value
        result.append(
            CellSnapshot(
                field_name=field_name,
                cell=f"{get_column_letter(column_number)}{row_number}",
                raw_value=raw,
                cached_value=cached_cell.value,
                formula=str(raw) if is_formula and raw is not None else None,
            )
        )
    return tuple(result)


def _header_issues(
    *,
    worksheet: str,
    row_number: int,
    observed: Sequence[Any],
    expected: Sequence[str],
) -> tuple[SourceIssue, ...]:
    issues: list[SourceIssue] = []
    for column_number, (observed_value, expected_value) in enumerate(
        zip(observed, expected),
        start=1,
    ):
        if _header_text(observed_value) == expected_value:
            continue
        coordinate = f"{get_column_letter(column_number)}{row_number}"
        issues.append(
            _structure_issue(
                "FS-SLV-002",
                f"The required '{expected_value}' header is not at {coordinate}.",
                worksheet,
                coordinate,
            )
        )
    return tuple(issues)


def _header_text(value: Any) -> str:
    if value is None:
        return ""
    return re.sub(r"\r\n|\r|\n", " ", str(value)).strip()


def _raw_text(value: Any) -> str | None:
    return None if value is None else str(value)


def _outer_text(value: Any) -> str:
    return "" if value is None else str(value).strip()


def _is_blank(value: Any) -> bool:
    return value is None or (isinstance(value, str) and not value.strip())


def _row_is_blank(values: Sequence[Any]) -> bool:
    return all(_is_blank(value) for value in values)


def _is_repeated_header(values: Sequence[Any]) -> bool:
    return tuple(_header_text(value) for value in values) == _GED_HEADERS


def _account_token(value: Any) -> str | None:
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, int):
        token = str(value)
    elif isinstance(value, float):
        if not value.is_integer():
            return None
        token = str(int(value))
    elif isinstance(value, str):
        token = value.strip()
    else:
        return None
    return token if token.isascii() and token.isdigit() else None


def _canonical_department(value: Any) -> str | None:
    token = _outer_text(value)
    return token if re.fullmatch(r"[0-9]{2}-[0-9]{4}", token) else None


def _period_evidence(raw_value: str | None) -> MetadataEvidence:
    trimmed = _outer_text(raw_value)
    if not trimmed:
        status = EvidenceStatus.ABSENT
        normalized = None
    else:
        match = _GED_PERIOD.fullmatch(trimmed)
        if match is None:
            status = EvidenceStatus.MALFORMED
            normalized = None
        else:
            status = EvidenceStatus.PRESENT
            month = list(calendar.month_name).index(match.group(1))
            normalized = f"{match.group(2)}-{month:02d}"
    return MetadataEvidence(
        "reporting_period",
        status,
        raw_value,
        normalized,
        _GED_SHEET,
        "A3",
    )


def _department_name_evidence(
    department_names: Sequence[tuple[str, str, int]],
    authoritative_department: str,
) -> MetadataEvidence:
    ordered: list[tuple[str, int]] = []
    seen: set[str] = set()
    for department, name, row_number in department_names:
        if department != authoritative_department:
            continue
        if name in seen:
            continue
        seen.add(name)
        ordered.append((name, row_number))

    if not ordered:
        return MetadataEvidence(
            "department_name",
            EvidenceStatus.ABSENT,
            None,
            None,
            _GED_SHEET,
            None,
        )
    if len(ordered) == 1:
        name, row_number = ordered[0]
        return MetadataEvidence(
            "department_name",
            EvidenceStatus.PRESENT,
            name,
            name,
            _GED_SHEET,
            f"B{row_number}",
        )
    return MetadataEvidence(
        "department_name",
        EvidenceStatus.CONFLICTING,
        " | ".join(name for name, _row in ordered),
        None,
        _GED_SHEET,
        f"B{ordered[0][1]}",
    )


def _structure_issue(
    code: str,
    message: str,
    worksheet: str,
    cell: str | None,
) -> SourceIssue:
    return SourceIssue(
        code,
        "Source compatibility",
        message,
        worksheet=worksheet,
        cell=cell,
    )
