#!/usr/bin/env python3
"""Independent Stage 1 control oracle for the approved synthetic workbooks.

This verifier deliberately imports no FinSight modules and no spreadsheet
library.  It reads the cached values in the workbook OOXML packages directly,
uses ``Decimal`` for every financial calculation, and compares the observed
fixture facts with the manually approved control expectations.
"""
from __future__ import annotations

import argparse
import json
import re
import zipfile
from collections import Counter, defaultdict
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Iterable
from xml.etree import ElementTree


SHEET_NS = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
NS = {"x": SHEET_NS}
BUDGET_COLUMNS = {
    "A": "account_number",
    "B": "account_name",
    "C": "bgt",
    "D": "atd",
    "E": "etc",
    "F": "eac",
    "G": "delta",
    "H": "notes",
}
GED_COLUMNS = {
    "A": "department_number",
    "B": "department_name",
    "C": "account_number",
    "D": "account_name",
    "E": "fiscal_period",
    "F": "journal_number",
    "G": "journal_date",
    "H": "invoice_amount",
    "I": "check_number",
    "J": "invoice_date",
    "K": "vendor_name",
    "L": "agency",
    "M": "journal_description",
    "N": "journal_line_description",
    "O": "amount",
}
REQUIRED_GED_FIELDS = (
    "department_number",
    "account_number",
    "fiscal_period",
    "journal_number",
    "journal_date",
    "amount",
)
MONEY_FIELDS = ("bgt", "atd", "etc", "eac", "delta")
ZERO = Decimal("0.00")


@dataclass(frozen=True)
class Cell:
    reference: str
    value: str | None
    formula: str | None


@dataclass(frozen=True)
class WorkbookSheet:
    name: str
    rows: dict[int, dict[str, Cell]]


def _column(reference: str) -> str:
    match = re.match(r"([A-Z]+)", reference)
    if match is None:
        raise ValueError(f"Invalid cell reference {reference!r}.")
    return match.group(1)


def _shared_strings(archive: zipfile.ZipFile) -> list[str]:
    try:
        root = ElementTree.fromstring(archive.read("xl/sharedStrings.xml"))
    except KeyError:
        return []
    return [
        "".join(node.text or "" for node in item.findall(".//x:t", NS))
        for item in root.findall("x:si", NS)
    ]


def _workbook_sheet_name(archive: zipfile.ZipFile) -> str:
    root = ElementTree.fromstring(archive.read("xl/workbook.xml"))
    sheet = root.find("x:sheets/x:sheet", NS)
    if sheet is None:
        raise ValueError("The workbook does not contain a worksheet.")
    return str(sheet.attrib["name"])


def read_first_sheet(path: Path) -> WorkbookSheet:
    with zipfile.ZipFile(path) as archive:
        shared = _shared_strings(archive)
        sheet_name = _workbook_sheet_name(archive)
        root = ElementTree.fromstring(
            archive.read("xl/worksheets/sheet1.xml")
        )
    rows: dict[int, dict[str, Cell]] = {}
    for row_node in root.findall("x:sheetData/x:row", NS):
        row_number = int(row_node.attrib["r"])
        row: dict[str, Cell] = {}
        for cell_node in row_node.findall("x:c", NS):
            reference = str(cell_node.attrib["r"])
            value_node = cell_node.find("x:v", NS)
            formula_node = cell_node.find("x:f", NS)
            value = value_node.text if value_node is not None else None
            cell_type = cell_node.attrib.get("t")
            if cell_type == "s" and value is not None:
                value = shared[int(value)]
            elif cell_type == "inlineStr":
                value = "".join(
                    node.text or ""
                    for node in cell_node.findall(".//x:t", NS)
                )
            row[_column(reference)] = Cell(
                reference,
                value,
                formula_node.text if formula_node is not None else None,
            )
        rows[row_number] = row
    return WorkbookSheet(sheet_name, rows)


def _value(row: dict[str, Cell], column: str) -> str | None:
    cell = row.get(column)
    return cell.value if cell is not None else None


def _text(value: Any) -> str:
    return "" if value is None else str(value).strip()


def _money(value: Any) -> Decimal | None:
    text = _text(value)
    if not text or "e" in text.lower():
        return None
    try:
        result = Decimal(text)
    except (InvalidOperation, ValueError):
        return None
    if not result.is_finite() or result.as_tuple().exponent < -2:
        return None
    return result.quantize(Decimal("0.01"))


def _currency(value: Decimal | None) -> str:
    if value is None:
        return "Not available"
    sign = "-" if value < 0 else ""
    return f"{sign}${abs(value):,.2f}"


def _budget_row_kind(row: dict[str, Cell]) -> str:
    account = _text(_value(row, "A"))
    if re.fullmatch(r"\d{6}", account):
        return "detail"
    if re.fullmatch(r"\d{3}", account):
        return "group_total"
    if account.casefold() == "grand total":
        return "grand_total"
    if not any(_text(cell.value) for cell in row.values()):
        return "separator"
    return "unexpected"


def _ged_row_kind(row: dict[str, Cell]) -> str:
    first = _text(_value(row, "A"))
    if first.startswith("TOTAL FOR ACCOUNT -"):
        return "account_total"
    if first.startswith("TOTAL FOR DEPARTMENT -"):
        return "department_total"
    if not any(_text(cell.value) for cell in row.values()):
        return "blank"
    return "transaction"


def _mapped(row: dict[str, Cell], columns: dict[str, str]) -> dict[str, Any]:
    return {
        field: _value(row, column)
        for column, field in columns.items()
    }


def _valid_department(value: Any) -> bool:
    return bool(re.fullmatch(r"\d{2}-\d{4}", _text(value)))


def _valid_account(value: Any) -> bool:
    return bool(re.fullmatch(r"\d{6}", _text(value)))


def _valid_period(value: Any) -> bool:
    return bool(re.fullmatch(r"\d{4}-(0[1-9]|1[0-2])", _text(value)))


def _valid_date(value: Any) -> bool:
    return bool(re.fullmatch(r"\d{4}-(0[1-9]|1[0-2])-[0-3]\d", _text(value)))


def _canonical_fingerprint(row: dict[str, Any]) -> tuple[tuple[str, str], ...]:
    result: list[tuple[str, str]] = []
    for field in GED_COLUMNS.values():
        value = row[field]
        if value is None or _text(value) == "":
            result.append(("null", ""))
        elif field in {"amount", "invoice_amount"} and _money(value) is not None:
            result.append(("money", format(_money(value), ".2f")))
        else:
            result.append(("text", _text(value)))
    return tuple(result)


def _control(
    expected: Any,
    actual: Any,
    *,
    difference: Any = None,
) -> dict[str, Any]:
    return {
        "expected": expected,
        "actual": actual,
        "difference": difference,
        "status": "PASS" if expected == actual else "FAIL",
    }


def _sum_money(rows: Iterable[dict[str, Any]], field: str) -> Decimal:
    return sum((_money(row[field]) or ZERO for row in rows), ZERO)


def build_oracle(budget_path: Path, ged_path: Path) -> dict[str, Any]:
    budget_sheet = read_first_sheet(budget_path)
    ged_sheet = read_first_sheet(ged_path)
    if budget_sheet.name != "Original Budget":
        raise ValueError(
            f"Expected Budget worksheet 'Original Budget'; got {budget_sheet.name!r}."
        )
    if ged_sheet.name != "GED":
        raise ValueError(f"Expected GED worksheet 'GED'; got {ged_sheet.name!r}.")

    budget_rows: list[dict[str, Any]] = []
    budget_kinds: Counter[str] = Counter()
    budget_source_rows: defaultdict[str, list[int]] = defaultdict(list)
    budget_formulas: list[dict[str, Any]] = []
    for row_number, raw in sorted(budget_sheet.rows.items()):
        if row_number == 1:
            continue
        kind = _budget_row_kind(raw)
        budget_kinds[kind] += 1
        budget_source_rows[kind].append(row_number)
        values = _mapped(raw, BUDGET_COLUMNS)
        values.update(row_number=row_number, kind=kind)
        if kind == "detail":
            atd = _money(values["atd"])
            etc = _money(values["etc"])
            bgt = _money(values["bgt"])
            eac = _money(values["eac"])
            delta = _money(values["delta"])
            budget_formulas.append(
                {
                    "row": row_number,
                    "eac_formula": raw.get("F").formula if raw.get("F") else None,
                    "delta_formula": raw.get("G").formula if raw.get("G") else None,
                    "eac_valid": (
                        None not in (atd, etc, eac) and eac == atd + etc
                    ),
                    "delta_valid": (
                        None not in (bgt, eac, delta) and delta == bgt - eac
                    ),
                }
            )
            budget_rows.append(values)

    ged_rows: list[dict[str, Any]] = []
    ged_kinds: Counter[str] = Counter()
    ged_source_rows: defaultdict[str, list[int]] = defaultdict(list)
    excluded_ged_display_amount = ZERO
    for row_number, raw in sorted(ged_sheet.rows.items()):
        if row_number <= 7:
            continue
        kind = _ged_row_kind(raw)
        ged_kinds[kind] += 1
        ged_source_rows[kind].append(row_number)
        values = _mapped(raw, GED_COLUMNS)
        values.update(row_number=row_number, kind=kind)
        if kind == "transaction":
            ged_rows.append(values)
        elif kind in {"account_total", "department_total"}:
            excluded_ged_display_amount += _money(values["amount"]) or ZERO

    budget_by_key = {
        ("00-0245", _text(row["account_number"])): row
        for row in budget_rows
    }
    ged_by_key: defaultdict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in ged_rows:
        department = _text(row["department_number"])
        account = _text(row["account_number"])
        if _valid_department(department) and _valid_account(account):
            ged_by_key[(department, account)].append(row)

    account_controls: list[dict[str, Any]] = []
    reconciliation = Counter()
    overrun = Counter()
    for key, budget in sorted(budget_by_key.items()):
        transactions = ged_by_key.get(key, [])
        missing_amounts = sum(_money(row["amount"]) is None for row in transactions)
        invalid_periods = sum(
            not _valid_period(row["fiscal_period"]) for row in transactions
        )
        complete = missing_amounts == 0 and invalid_periods == 0
        ged_amount = (
            _sum_money(transactions, "amount") if complete else None
        )
        bgt = _money(budget["bgt"])
        atd = _money(budget["atd"])
        if not complete or bgt is None or atd is None:
            reconciliation_status = "NOT_EVALUATED"
            overrun_status = "NOT_EVALUATED"
        else:
            reconciliation_status = "PASS" if atd == ged_amount else "FAIL"
            overrun_status = "PASS" if ged_amount <= bgt else "FAIL"
        reconciliation[reconciliation_status] += 1
        overrun[overrun_status] += 1
        account_controls.append(
            {
                "department_number": key[0],
                "account_number": key[1],
                "account_name": _text(budget["account_name"]),
                "budget_row": budget["row_number"],
                "ged_rows": [row["row_number"] for row in transactions],
                "ged_transaction_count": len(transactions),
                "bgt": _currency(bgt),
                "atd": _currency(atd),
                "etc": _currency(_money(budget["etc"])),
                "eac": _currency(_money(budget["eac"])),
                "delta": _currency(_money(budget["delta"])),
                "summed_ged_amount": _currency(ged_amount),
                "difference_atd_to_ged": _currency(
                    atd - ged_amount
                    if atd is not None and ged_amount is not None
                    else None
                ),
                "remaining_budget": _currency(
                    bgt - ged_amount
                    if bgt is not None and ged_amount is not None
                    else None
                ),
                "overrun": _currency(
                    max(ged_amount - bgt, ZERO)
                    if bgt is not None and ged_amount is not None
                    else None
                ),
                "utilization": (
                    "Not available"
                    if bgt in {None, ZERO} or ged_amount is None
                    else f"{((ged_amount / bgt) * Decimal('100')).quantize(Decimal('0.01'))}%"
                ),
                "reconciliation_status": reconciliation_status,
                "overrun_status": overrun_status,
                "missing_amount_count": missing_amounts,
            }
        )

    valid_mappings = set(budget_by_key)
    invalid_mapping_rows = [
        row
        for row in ged_rows
        if (
            _text(row["department_number"]),
            _text(row["account_number"]),
        )
        not in valid_mappings
    ]
    required_failures: list[dict[str, Any]] = []
    for row in ged_rows:
        invalid: list[str] = []
        if not _valid_department(row["department_number"]):
            invalid.append("department_number")
        if not _valid_account(row["account_number"]):
            invalid.append("account_number")
        if not _valid_period(row["fiscal_period"]):
            invalid.append("fiscal_period")
        if not _text(row["journal_number"]):
            invalid.append("journal_number")
        if not _valid_date(row["journal_date"]):
            invalid.append("journal_date")
        if _money(row["amount"]) is None:
            invalid.append("amount")
        if invalid:
            required_failures.append(
                {"row": row["row_number"], "fields": invalid}
            )
    formula_failures = [
        item
        for item in budget_formulas
        if not item["eac_valid"] or not item["delta_valid"]
    ]

    duplicate_groups: defaultdict[
        tuple[tuple[str, str], ...], list[dict[str, Any]]
    ] = defaultdict(list)
    for row in ged_rows:
        duplicate_groups[_canonical_fingerprint(row)].append(row)
    duplicates = [
        {
            "rows": [row["row_number"] for row in rows],
            "department_number": _text(rows[0]["department_number"]),
            "account_number": _text(rows[0]["account_number"]),
            "amount": _currency(_money(rows[0]["amount"])),
            "matched_fields": list(GED_COLUMNS.values()),
        }
        for rows in duplicate_groups.values()
        if len(rows) > 1
    ]

    budget_totals = {
        field: _sum_money(budget_rows, field) for field in MONEY_FIELDS
    }
    parseable_ged_amounts = [
        _money(row["amount"])
        for row in ged_rows
        if _money(row["amount"]) is not None
    ]
    ged_total = sum(parseable_ged_amounts, ZERO)
    mapped_total = sum(
        (
            _money(row["amount"]) or ZERO
            for row in ged_rows
            if (
                _text(row["department_number"]),
                _text(row["account_number"]),
            )
            in valid_mappings
        ),
        ZERO,
    )
    unmapped_total = ged_total - mapped_total

    observed_rule_counts = {
        "CORE-05": {
            "PASS": reconciliation["PASS"],
            "FAIL": reconciliation["FAIL"],
            "NOT_EVALUATED": reconciliation["NOT_EVALUATED"],
        },
        "CORE-01": {
            "PASS": overrun["PASS"],
            "FAIL": overrun["FAIL"],
            "NOT_EVALUATED": overrun["NOT_EVALUATED"],
        },
        "CORE-02": {
            "PASS": len(ged_rows) - len(invalid_mapping_rows),
            "FAIL": len(invalid_mapping_rows),
            "NOT_EVALUATED": 0,
        },
        "CORE-04": {
            "PASS": len(ged_rows)
            + len(budget_rows)
            - len(required_failures)
            - len(formula_failures),
            "FAIL": len(required_failures) + len(formula_failures),
            "NOT_EVALUATED": 0,
        },
        "CORE-03": {
            "PASS": sum(len(rows) == 1 for rows in duplicate_groups.values()),
            "FAIL": sum(len(rows) > 1 for rows in duplicate_groups.values()),
            "NOT_EVALUATED": 0,
        },
    }
    expected_rule_counts = {
        "CORE-05": {"PASS": 69, "FAIL": 1, "NOT_EVALUATED": 1},
        "CORE-01": {"PASS": 69, "FAIL": 1, "NOT_EVALUATED": 1},
        "CORE-02": {"PASS": 257, "FAIL": 1, "NOT_EVALUATED": 0},
        "CORE-04": {"PASS": 328, "FAIL": 1, "NOT_EVALUATED": 0},
        "CORE-03": {"PASS": 256, "FAIL": 1, "NOT_EVALUATED": 0},
    }

    overrun_account = next(
        item for item in account_controls if item["account_number"] == "555035"
    )
    reconciliation_account = next(
        item for item in account_controls if item["account_number"] == "527015"
    )
    incomplete_account = next(
        item
        for item in account_controls
        if item["missing_amount_count"] == 1
    )

    expected_totals = {
        "bgt": Decimal("10372000.00"),
        "atd": Decimal("3500095.00"),
        "etc": Decimal("5882000.00"),
        "eac": Decimal("9382095.00"),
        "delta": Decimal("989905.00"),
        "ged": Decimal("3500095.00"),
        "mapped_ged": Decimal("3498245.00"),
        "unmapped_ged": Decimal("1850.00"),
    }
    actual_totals = {
        **budget_totals,
        "ged": ged_total,
        "mapped_ged": mapped_total,
        "unmapped_ged": unmapped_total,
    }
    total_controls = {
        key: _control(
            _currency(expected),
            _currency(actual_totals[key]),
            difference=_currency(actual_totals[key] - expected),
        )
        for key, expected in expected_totals.items()
    }
    row_controls = {
        "budget_detail_rows": _control(71, budget_kinds["detail"]),
        "budget_group_total_rows": _control(11, budget_kinds["group_total"]),
        "budget_separator_rows": _control(11, budget_kinds["separator"]),
        "budget_grand_total_rows": _control(1, budget_kinds["grand_total"]),
        "ged_transaction_rows": _control(258, ged_kinds["transaction"]),
        "ged_account_total_rows": _control(31, ged_kinds["account_total"]),
        "ged_department_total_rows": _control(
            1, ged_kinds["department_total"]
        ),
        "ged_blank_rows": _control(2, ged_kinds["blank"]),
        "missing_or_unparseable_ged_amounts": _control(
            1, len(ged_rows) - len(parseable_ged_amounts)
        ),
    }
    issue_controls = {
        "budget_overrun_555035": _control(
            {
                "budget_row": 91,
                "bgt": "$1,100,000.00",
                "ged": "$1,250,000.00",
                "overrun": "$150,000.00",
                "utilization": "113.64%",
            },
            {
                "budget_row": overrun_account["budget_row"],
                "bgt": overrun_account["bgt"],
                "ged": overrun_account["summed_ged_amount"],
                "overrun": overrun_account["overrun"],
                "utilization": overrun_account["utilization"],
            },
        ),
        "duplicate_rows": _control(
            [{"rows": [65, 66], "account_number": "533003", "amount": "$82.50"}],
            [
                {
                    "rows": item["rows"],
                    "account_number": item["account_number"],
                    "amount": item["amount"],
                }
                for item in duplicates
            ],
        ),
        "missing_amount": _control(
            {"row": 87, "field": "amount"},
            {
                "row": required_failures[0]["row"],
                "field": required_failures[0]["fields"][0],
            }
            if required_failures
            else None,
        ),
        "invalid_mapping": _control(
            {
                "row": 43,
                "department_number": "00-0999",
                "account_number": "527015",
                "amount": "$1,850.00",
            },
            {
                "row": invalid_mapping_rows[0]["row_number"],
                "department_number": _text(
                    invalid_mapping_rows[0]["department_number"]
                ),
                "account_number": _text(
                    invalid_mapping_rows[0]["account_number"]
                ),
                "amount": _currency(_money(invalid_mapping_rows[0]["amount"])),
            }
            if invalid_mapping_rows
            else None,
        ),
        "reconciliation_527015": _control(
            {
                "budget_row": 11,
                "atd": "$1,850.00",
                "ged": "$0.00",
                "difference": "$1,850.00",
                "status": "FAIL",
            },
            {
                "budget_row": reconciliation_account["budget_row"],
                "atd": reconciliation_account["atd"],
                "ged": reconciliation_account["summed_ged_amount"],
                "difference": reconciliation_account[
                    "difference_atd_to_ged"
                ],
                "status": reconciliation_account["reconciliation_status"],
            },
        ),
        "dependent_not_evaluated": _control(
            {
                "account_number": "537035",
                "missing_amount_count": 1,
                "overrun_status": "NOT_EVALUATED",
                "reconciliation_status": "NOT_EVALUATED",
            },
            {
                "account_number": incomplete_account["account_number"],
                "missing_amount_count": incomplete_account[
                    "missing_amount_count"
                ],
                "overrun_status": incomplete_account["overrun_status"],
                "reconciliation_status": incomplete_account[
                    "reconciliation_status"
                ],
            },
        ),
    }
    rule_controls = {
        rule_id: _control(expected_rule_counts[rule_id], actual)
        for rule_id, actual in observed_rule_counts.items()
    }
    all_controls = (
        list(total_controls.values())
        + list(row_controls.values())
        + list(issue_controls.values())
        + list(rule_controls.values())
    )

    return {
        "oracle": {
            "name": "FinSight Stage 1 independent OOXML financial oracle",
            "implementation_dependency": "None",
            "numeric_policy": "Decimal, exactly two fractional digits",
            "matching_grain": [
                "Department Number",
                "Account Number",
            ],
            "overall_status": (
                "PASS"
                if all(item["status"] == "PASS" for item in all_controls)
                else "FAIL"
            ),
        },
        "sources": {
            "budget": {
                "file": budget_path.name,
                "worksheet": budget_sheet.name,
            },
            "ged": {
                "file": ged_path.name,
                "worksheet": ged_sheet.name,
            },
        },
        "totals_control_matrix": total_controls,
        "row_control_matrix": row_controls,
        "known_issue_control_matrix": issue_controls,
        "rule_control_matrix": rule_controls,
        "financial_control_report": {
            "budget_formula": "SUM each C:G field across six-digit Budget detail rows only.",
            "budget_included_rows": budget_source_rows["detail"],
            "budget_excluded_rows": {
                key: value
                for key, value in budget_source_rows.items()
                if key != "detail"
            },
            "ged_formula": (
                "SUM parseable GED Amount values in O across transaction rows "
                "only; totals and blanks are presentation rows."
            ),
            "ged_included_transaction_rows": ged_source_rows["transaction"],
            "ged_excluded_rows": {
                key: value
                for key, value in ged_source_rows.items()
                if key != "transaction"
            },
            "excluded_transaction_amount": "$0.00",
            "excluded_report_total_display_values": _currency(
                excluded_ged_display_amount
            ),
            "missing_amount_rows": [
                item["row"] for item in required_failures
                if "amount" in item["fields"]
            ],
            "formula_failures": formula_failures,
        },
        "account_oracle": account_controls,
        "duplicate_oracle": duplicates,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--budget",
        type=Path,
        default=Path(
            "initiatives/configurable-rule-engine-v2/fixtures/"
            "Sample_Budget_Report.xlsx"
        ),
    )
    parser.add_argument(
        "--ged",
        type=Path,
        default=Path(
            "initiatives/configurable-rule-engine-v2/fixtures/"
            "Sample_GED_Report.xlsx"
        ),
    )
    parser.add_argument(
        "--compact",
        action="store_true",
        help="Print only the aggregate control matrices.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Also write the exact JSON oracle to this path.",
    )
    args = parser.parse_args()
    result = build_oracle(args.budget.resolve(), args.ged.resolve())
    if args.compact:
        result = {
            key: value
            for key, value in result.items()
            if key
            in {
                "oracle",
                "sources",
                "totals_control_matrix",
                "row_control_matrix",
                "known_issue_control_matrix",
                "rule_control_matrix",
                "financial_control_report",
            }
        }
    payload = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload, encoding="utf-8")
    print(payload, end="")
    return 0 if result["oracle"]["overall_status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
