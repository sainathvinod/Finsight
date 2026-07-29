"""Golden and structural tests for the exact SLV-001 Budget/GED extractor."""
from __future__ import annotations

from collections import Counter
from pathlib import Path

import pytest
from openpyxl import load_workbook

from finsight.domain.source_intake import (
    EvidenceStatus,
    RowKind,
    SourceRole,
)
from finsight.infrastructure.slv001_extractor import Slv001Extractor
from finsight.infrastructure.workbook_safety import (
    WorkbookSafetyInspector,
    WorkbookSafetyLimits,
)


FIXTURES = (
    Path(__file__).parents[2]
    / "initiatives"
    / "configurable-rule-engine-v2"
    / "fixtures"
)
BUDGET = FIXTURES / "Sample_Budget_Report.xlsx"
GED = FIXTURES / "Sample_GED_Report.xlsx"
BUDGET_SHA256 = (
    "bf40584183c564d91831214781969422d77d50439989f75750f0bdbe2bfa2b14"
)
GED_SHA256 = (
    "2213e3f1b10fee56fb4538112250fe37fbdaf36eb5e299fbfe6d17bd0f10603c"
)


@pytest.fixture(scope="module", autouse=True)
def _approved_fixtures_remain_unchanged():
    budget_before = BUDGET.read_bytes()
    ged_before = GED.read_bytes()

    yield

    assert BUDGET.read_bytes() == budget_before
    assert GED.read_bytes() == ged_before
    assert Slv001Extractor().inspect(
        str(BUDGET),
        SourceRole.BUDGET,
    ).sha256 == BUDGET_SHA256
    assert Slv001Extractor().inspect(
        str(GED),
        SourceRole.GED,
    ).sha256 == GED_SHA256


def _row(inspection, row_number):
    return next(item for item in inspection.rows if item.row_number == row_number)


def _cell(row, field_name):
    return next(item for item in row.cells if item.field_name == field_name)


def _mutate(source: Path, target: Path, mutation) -> None:
    workbook = load_workbook(source, data_only=False, keep_links=False)
    try:
        mutation(workbook)
        workbook.save(target)
    finally:
        workbook.close()


def test_supplied_budget_golden_layout_count_metadata_and_formula_lineage():
    source_before = BUDGET.read_bytes()

    inspection = Slv001Extractor().inspect(str(BUDGET), SourceRole.BUDGET)

    assert inspection.is_compatible
    assert inspection.record_count == 71
    assert inspection.byte_size == 10_132
    assert (
        inspection.sha256
        == "bf40584183c564d91831214781969422d77d50439989f75750f0bdbe2bfa2b14"
    )
    assert Counter(item.kind for item in inspection.rows) == {
        RowKind.BUDGET_DETAIL: 71,
        RowKind.BUDGET_GROUP_TOTAL: 11,
        RowKind.BUDGET_SEPARATOR: 11,
        RowKind.BUDGET_GRAND_TOTAL: 1,
    }
    assert inspection.evidence_for(
        "department_number"
    ).normalized_value == "00-0245"
    period = inspection.evidence_for("reporting_period")
    assert period.status is EvidenceStatus.WORKSPACE_ASSIGNED
    assert period.raw_value is None
    detail = _row(inspection, 2)
    assert detail.kind is RowKind.BUDGET_DETAIL
    assert _cell(detail, "bgt").cell == "C2"
    assert _cell(detail, "bgt").raw_value == 12_000
    assert _cell(detail, "eac").formula == "=D2+E2"
    assert _cell(detail, "eac").cached_value == 6_900
    grand_total = _row(inspection, 95)
    assert _cell(grand_total, "bgt").cached_value == 10_372_000
    assert BUDGET.read_bytes() == source_before


def test_supplied_ged_golden_layout_count_metadata_and_intentional_rows():
    source_before = GED.read_bytes()

    inspection = Slv001Extractor().inspect(str(GED), SourceRole.GED)

    assert inspection.is_compatible
    assert inspection.record_count == 258
    assert inspection.byte_size == 26_452
    assert (
        inspection.sha256
        == "2213e3f1b10fee56fb4538112250fe37fbdaf36eb5e299fbfe6d17bd0f10603c"
    )
    assert Counter(item.kind for item in inspection.rows) == {
        RowKind.GED_TRANSACTION: 258,
        RowKind.GED_ACCOUNT_TOTAL: 31,
        RowKind.GED_DEPARTMENT_TOTAL: 1,
        RowKind.GED_BLANK: 2,
    }
    assert inspection.evidence_for(
        "department_number"
    ).normalized_value == "00-0245"
    department_name = inspection.evidence_for("department_name")
    assert department_name.status is EvidenceStatus.PRESENT
    assert department_name.raw_value == "Applications Enginee"
    reporting_period = inspection.evidence_for("reporting_period")
    assert reporting_period.status is EvidenceStatus.PRESENT
    assert reporting_period.normalized_value == "2026-05"

    invalid_key = _row(inspection, 43)
    assert invalid_key.kind is RowKind.GED_TRANSACTION
    assert _cell(invalid_key, "department_number").raw_value == "00-0999"
    missing_amount = _row(inspection, 87)
    assert missing_amount.kind is RowKind.GED_TRANSACTION
    assert _cell(missing_amount, "amount").raw_value is None
    account_total = _row(inspection, 10)
    assert account_total.kind is RowKind.GED_ACCOUNT_TOTAL
    assert _cell(account_total, "amount").formula == "=SUM(O8:O9)"
    assert _cell(account_total, "amount").cached_value == 2_100
    assert _row(inspection, 297).kind is RowKind.GED_DEPARTMENT_TOTAL
    assert _row(inspection, 298).kind is RowKind.GED_BLANK
    assert GED.read_bytes() == source_before


def test_non_report_department_name_does_not_change_report_metadata(tmp_path):
    selected = tmp_path / "row-level-exception.xlsx"

    def change_outlier_name(workbook):
        workbook["GED"]["B43"] = "Another Department"

    _mutate(GED, selected, change_outlier_name)

    inspection = Slv001Extractor().inspect(str(selected), SourceRole.GED)

    assert inspection.is_compatible
    assert (
        inspection.evidence_for("department_name").normalized_value
        == "Applications Enginee"
    )


def test_missing_expected_worksheet_is_incompatible(tmp_path):
    selected = tmp_path / "wrong-sheet.xlsx"

    def rename_sheet(workbook):
        workbook["Original Budget"].title = "Budget"

    _mutate(BUDGET, selected, rename_sheet)

    inspection = Slv001Extractor().inspect(str(selected), SourceRole.BUDGET)

    assert not inspection.is_compatible
    assert inspection.issues[0].code == "FS-SLV-001"


def test_all_header_mismatches_identify_their_exact_cells(tmp_path):
    selected = tmp_path / "wrong-headers.xlsx"

    def change_headers(workbook):
        sheet = workbook["GED"]
        sheet["C7"] = "ACCOUNT"
        sheet["O7"] = "VALUE"

    _mutate(GED, selected, change_headers)

    inspection = Slv001Extractor().inspect(str(selected), SourceRole.GED)

    assert not inspection.is_compatible
    assert [issue.cell for issue in inspection.issues] == ["C7", "O7"]
    assert all(issue.code == "FS-SLV-002" for issue in inspection.issues)


def test_total_like_row_with_wrong_shape_blocks_extraction(tmp_path):
    selected = tmp_path / "malformed-total.xlsx"

    def change_total(workbook):
        workbook["GED"]["A10"] = "TOTAL FOR ACCOUNT - 517025"

    _mutate(GED, selected, change_total)

    inspection = Slv001Extractor().inspect(str(selected), SourceRole.GED)

    assert not inspection.is_compatible
    assert inspection.issues[0].code == "FS-SLV-014"
    assert inspection.issues[0].cell == "A10:O10"


def test_nonblank_row_after_department_total_blocks_extraction(tmp_path):
    selected = tmp_path / "post-total-data.xlsx"

    def add_later_data(workbook):
        workbook["GED"]["A298"] = "unexpected"

    _mutate(GED, selected, add_later_data)

    inspection = Slv001Extractor().inspect(str(selected), SourceRole.GED)

    assert not inspection.is_compatible
    assert inspection.issues[0].code == "FS-SLV-013"
    assert inspection.issues[0].cell == "A298:O298"


def test_duplicate_budget_detail_account_blocks_extraction(tmp_path):
    selected = tmp_path / "duplicate-budget-key.xlsx"

    def duplicate_account(workbook):
        workbook["Original Budget"]["A3"] = 517025

    _mutate(BUDGET, selected, duplicate_account)

    inspection = Slv001Extractor().inspect(str(selected), SourceRole.BUDGET)

    assert not inspection.is_compatible
    assert inspection.issues[0].code == "FS-SLV-010"
    assert inspection.issues[0].cell == "A3"


def test_malformed_period_remains_visible_evidence_without_guessing(tmp_path):
    selected = tmp_path / "malformed-period.xlsx"

    def change_period(workbook):
        workbook["GED"]["A3"] = "YTD May 2026"

    _mutate(GED, selected, change_period)

    inspection = Slv001Extractor().inspect(str(selected), SourceRole.GED)

    assert inspection.is_compatible
    evidence = inspection.evidence_for("reporting_period")
    assert evidence.status is EvidenceStatus.MALFORMED
    assert evidence.raw_value == "YTD May 2026"
    assert evidence.normalized_value is None


def test_ged_transaction_boundary_accepts_limit_and_rejects_limit_plus_one(
    tmp_path,
):
    limits = WorkbookSafetyLimits(ged_transactions=258)
    safety = WorkbookSafetyInspector(limits)
    exact = Slv001Extractor(safety).inspect(str(GED), SourceRole.GED)
    assert exact.is_compatible
    assert exact.record_count == 258

    plus_one_source = tmp_path / "ged-259-transactions.xlsx"

    def add_transaction(workbook):
        sheet = workbook["GED"]
        sheet.insert_rows(297)
        for column in range(1, 16):
            sheet.cell(297, column).value = sheet.cell(8, column).value

    _mutate(GED, plus_one_source, add_transaction)
    plus_one = Slv001Extractor(
        WorkbookSafetyInspector(
            WorkbookSafetyLimits(ged_transactions=258)
        )
    ).inspect(
        str(plus_one_source),
        SourceRole.GED,
    )

    assert not plus_one.is_compatible
    assert plus_one.issues[0].code == "FS-SLV-015"
