"""WRL-001 read-only snapshot and hostile-package regression tests."""
from __future__ import annotations

import warnings
import zipfile
from pathlib import Path

import pytest
from openpyxl import load_workbook

from finsight.infrastructure.workbook_safety import (
    WorkbookSafetyInspector,
    WorkbookSafetyLimits,
    WorkbookSafetyViolation,
    verify_unchanged,
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
    assert WorkbookSafetyInspector().inspect(str(BUDGET)).sha256 == BUDGET_SHA256
    assert WorkbookSafetyInspector().inspect(str(GED)).sha256 == GED_SHA256

    yield

    assert BUDGET.read_bytes() == budget_before
    assert GED.read_bytes() == ged_before
    assert WorkbookSafetyInspector().inspect(str(BUDGET)).sha256 == BUDGET_SHA256
    assert WorkbookSafetyInspector().inspect(str(GED)).sha256 == GED_SHA256


def _rewrite_package(
    source: Path,
    target: Path,
    *,
    replacements: dict[str, bytes] | None = None,
    additions: tuple[tuple[str, bytes], ...] = (),
    compression: int = zipfile.ZIP_DEFLATED,
) -> None:
    replacements = replacements or {}
    with zipfile.ZipFile(source, "r") as original:
        entries = [
            (item.filename, replacements.get(item.filename, original.read(item)))
            for item in original.infolist()
        ]
    with zipfile.ZipFile(target, "w", compression) as rewritten:
        for name, content in entries:
            rewritten.writestr(name, content)
        for name, content in additions:
            rewritten.writestr(name, content)


def _package_part(source: Path, name: str) -> bytes:
    with zipfile.ZipFile(source, "r") as workbook:
        return workbook.read(name)


def _shared_strings(count: int) -> bytes:
    items = b"".join(
        f"<x:si><x:t>value-{index}</x:t></x:si>".encode("ascii")
        for index in range(count)
    )
    return (
        b'<?xml version="1.0" encoding="utf-8"?>'
        b'<x:sst xmlns:x="http://schemas.openxmlformats.org/'
        b'spreadsheetml/2006/main" '
        + f'count="{count}" uniqueCount="{count}">'.encode("ascii")
        + items
        + b"</x:sst>"
    )


def _worksheet_with_merges(count: int) -> bytes:
    worksheet = _package_part(BUDGET, "xl/worksheets/sheet1.xml")
    merge_cells = b"".join(
        f'<x:mergeCell ref="{column}1:{column}2" />'.encode("ascii")
        for column in ("A", "B")[:count]
    )
    merge_block = (
        f'<x:mergeCells count="{count}">'.encode("ascii")
        + merge_cells
        + b"</x:mergeCells>"
    )
    return worksheet.replace(
        b"<x:pageMargins",
        merge_block + b"<x:pageMargins",
        1,
    )


class _BoundaryClock:
    def __init__(self, elapsed_after_start: float) -> None:
        self.elapsed_after_start = elapsed_after_start
        self.calls = 0

    def __call__(self) -> float:
        self.calls += 1
        return 0.0 if self.calls == 1 else self.elapsed_after_start


def test_golden_snapshot_hashes_the_exact_unchanged_source_bytes():
    before = BUDGET.read_bytes()

    snapshot = WorkbookSafetyInspector().inspect(str(BUDGET))

    assert snapshot.content == before
    assert snapshot.byte_size == 10_132
    assert snapshot.sha256 == BUDGET_SHA256
    assert BUDGET.read_bytes() == before
    assert verify_unchanged(str(BUDGET), snapshot.sha256, snapshot.byte_size)


def test_identity_recheck_detects_a_changed_selected_file(tmp_path):
    selected = tmp_path / "selected.xlsx"
    selected.write_bytes(BUDGET.read_bytes())
    snapshot = WorkbookSafetyInspector().inspect(str(selected))

    selected.write_bytes(selected.read_bytes() + b"changed")

    assert not verify_unchanged(
        str(selected),
        snapshot.sha256,
        snapshot.byte_size,
    )


@pytest.mark.parametrize(
    ("file_name", "content", "expected_code"),
    (
        ("report.xlsm", b"not inspected", "FS-WRK-001"),
        ("report.xlsx", b"not a ZIP package", "FS-WRK-003"),
    ),
)
def test_wrong_type_and_corrupt_packages_are_safely_rejected(
    tmp_path,
    file_name,
    content,
    expected_code,
):
    selected = tmp_path / file_name
    selected.write_bytes(content)

    with pytest.raises(WorkbookSafetyViolation) as captured:
        WorkbookSafetyInspector().inspect(str(selected))

    assert captured.value.issue.code == expected_code
    assert str(selected) not in captured.value.issue.message


@pytest.mark.parametrize(
    ("case_name", "addition_name", "addition", "expected_code"),
    (
        ("traversal", "../escape.xml", b"<escape/>", "FS-WRK-006"),
        ("macro", "xl/vbaProject.bin", b"macro", "FS-WRK-012"),
        (
            "external-link-part",
            "xl/externalLinks/externalLink1.xml",
            b"<externalLink/>",
            "FS-WRK-012",
        ),
    ),
)
def test_forbidden_package_parts_are_rejected(
    tmp_path,
    case_name,
    addition_name,
    addition,
    expected_code,
):
    selected = tmp_path / f"{case_name}.xlsx"
    _rewrite_package(
        BUDGET,
        selected,
        additions=((addition_name, addition),),
    )

    with pytest.raises(WorkbookSafetyViolation) as captured:
        WorkbookSafetyInspector().inspect(str(selected))

    assert captured.value.issue.code == expected_code


def test_case_insensitive_duplicate_package_entries_are_rejected(tmp_path):
    selected = tmp_path / "duplicate.xlsx"
    _rewrite_package(BUDGET, selected)
    content_types = _package_part(BUDGET, "[Content_Types].xml")
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", UserWarning)
        with zipfile.ZipFile(selected, "a", zipfile.ZIP_DEFLATED) as workbook:
            workbook.writestr("[content_types].xml", content_types)

    with pytest.raises(WorkbookSafetyViolation) as captured:
        WorkbookSafetyInspector().inspect(str(selected))

    assert captured.value.issue.code == "FS-WRK-007"


def test_external_relationship_target_is_rejected(tmp_path):
    selected = tmp_path / "external-relationship.xlsx"
    relationships = _package_part(BUDGET, "_rels/.rels")
    relationships = relationships.replace(
        b"</Relationships>",
        (
            b'<Relationship Id="external-test" Type="urn:finsight:test" '
            b'Target="https://example.invalid/source" TargetMode="External"/>'
            b"</Relationships>"
        ),
    )
    _rewrite_package(
        BUDGET,
        selected,
        replacements={"_rels/.rels": relationships},
    )

    with pytest.raises(WorkbookSafetyViolation) as captured:
        WorkbookSafetyInspector().inspect(str(selected))

    assert captured.value.issue.code == "FS-WRK-013"


def test_workbook_protection_is_rejected(tmp_path):
    selected = tmp_path / "protected.xlsx"
    workbook_xml = _package_part(BUDGET, "xl/workbook.xml")
    workbook_xml = workbook_xml.replace(
        b"</x:workbook>",
        b"<x:workbookProtection lockStructure=\"1\"/></x:workbook>",
    )
    _rewrite_package(
        BUDGET,
        selected,
        replacements={"xl/workbook.xml": workbook_xml},
    )

    with pytest.raises(WorkbookSafetyViolation) as captured:
        WorkbookSafetyInspector().inspect(str(selected))

    assert captured.value.issue.code == "FS-WRK-014"


@pytest.mark.parametrize(
    ("limit_name", "observed", "expected_code"),
    (
        ("compressed_bytes", 10_132, "FS-WRK-002"),
        ("total_uncompressed_bytes", 49_988, "FS-WRK-011"),
        ("one_uncompressed_entry_bytes", 39_541, "FS-WRK-009"),
        ("zip_entries", 8, "FS-WRK-004"),
        ("rows_per_worksheet", 95, "FS-WRK-021"),
        ("columns_per_worksheet", 8, "FS-WRK-022"),
        ("populated_cells", 760, "FS-WRK-016"),
        ("formula_cells", 202, "FS-WRK-017"),
        ("shared_string_bytes", 115, "FS-WRK-019"),
    ),
)
def test_fixture_metric_is_accepted_at_limit_and_rejected_at_limit_plus_one(
    limit_name,
    observed,
    expected_code,
):
    accepted_limits = WorkbookSafetyLimits(**{limit_name: observed})
    snapshot = WorkbookSafetyInspector(accepted_limits).inspect(str(BUDGET))
    assert snapshot.sha256 == BUDGET_SHA256

    plus_one_limits = WorkbookSafetyLimits(**{limit_name: observed - 1})
    with pytest.raises(WorkbookSafetyViolation) as captured:
        WorkbookSafetyInspector(plus_one_limits).inspect(str(BUDGET))

    assert captured.value.issue.code == expected_code


def test_expansion_ratio_is_accepted_at_one_to_one_and_rejected_at_two_to_one(
    tmp_path,
):
    exact = tmp_path / "ratio-exact.xlsx"
    plus_one = tmp_path / "ratio-plus-one.xlsx"
    _rewrite_package(
        BUDGET,
        exact,
        compression=zipfile.ZIP_STORED,
    )
    _rewrite_package(
        BUDGET,
        plus_one,
        compression=zipfile.ZIP_STORED,
    )
    with zipfile.ZipFile(plus_one, "a") as workbook:
        workbook.writestr(
            "custom/ratio-boundary.bin",
            b"A" * 10,
            compress_type=zipfile.ZIP_DEFLATED,
        )
    with zipfile.ZipFile(plus_one, "r") as workbook:
        boundary = workbook.getinfo("custom/ratio-boundary.bin")
        assert boundary.file_size == 10
        assert boundary.compress_size == 5

    limits = WorkbookSafetyLimits(expansion_ratio=1)
    assert WorkbookSafetyInspector(limits).inspect(str(exact)).byte_size > 0
    with pytest.raises(WorkbookSafetyViolation) as captured:
        WorkbookSafetyInspector(limits).inspect(str(plus_one))

    assert captured.value.issue.code == "FS-WRK-010"


def test_worksheet_count_is_accepted_at_one_and_rejected_at_two(tmp_path):
    plus_one = tmp_path / "two-worksheets.xlsx"
    workbook = load_workbook(BUDGET, data_only=False, keep_links=False)
    try:
        workbook.create_sheet("Boundary Sheet")
        workbook.save(plus_one)
    finally:
        workbook.close()

    limits = WorkbookSafetyLimits(worksheets=1)
    assert WorkbookSafetyInspector(limits).inspect(str(BUDGET)).sha256 == BUDGET_SHA256
    with pytest.raises(WorkbookSafetyViolation) as captured:
        WorkbookSafetyInspector(limits).inspect(str(plus_one))

    assert captured.value.issue.code == "FS-WRK-015"


def test_merge_count_is_accepted_at_one_and_rejected_at_two(tmp_path):
    exact = tmp_path / "one-merge.xlsx"
    plus_one = tmp_path / "two-merges.xlsx"
    _rewrite_package(
        BUDGET,
        exact,
        replacements={
            "xl/worksheets/sheet1.xml": _worksheet_with_merges(1)
        },
    )
    _rewrite_package(
        BUDGET,
        plus_one,
        replacements={
            "xl/worksheets/sheet1.xml": _worksheet_with_merges(2)
        },
    )

    limits = WorkbookSafetyLimits(merged_ranges=1)
    assert WorkbookSafetyInspector(limits).inspect(str(exact)).byte_size > 0
    with pytest.raises(WorkbookSafetyViolation) as captured:
        WorkbookSafetyInspector(limits).inspect(str(plus_one))

    assert captured.value.issue.code == "FS-WRK-018"


def test_shared_string_count_is_accepted_at_one_and_rejected_at_two(tmp_path):
    exact = tmp_path / "one-shared-string.xlsx"
    plus_one = tmp_path / "two-shared-strings.xlsx"
    _rewrite_package(
        BUDGET,
        exact,
        replacements={"xl/sharedStrings.xml": _shared_strings(1)},
    )
    _rewrite_package(
        BUDGET,
        plus_one,
        replacements={"xl/sharedStrings.xml": _shared_strings(2)},
    )

    limits = WorkbookSafetyLimits(shared_string_entries=1)
    assert WorkbookSafetyInspector(limits).inspect(str(exact)).byte_size > 0
    with pytest.raises(WorkbookSafetyViolation) as captured:
        WorkbookSafetyInspector(limits).inspect(str(plus_one))

    assert captured.value.issue.code == "FS-WRK-020"


def test_wall_duration_is_inclusive_and_limit_plus_one_is_rejected():
    exact_clock = _BoundaryClock(1.0)
    exact_limits = WorkbookSafetyLimits(wall_seconds=1.0)
    snapshot = WorkbookSafetyInspector(
        exact_limits,
        monotonic=exact_clock,
    ).inspect(str(BUDGET))
    assert snapshot.sha256 == BUDGET_SHA256

    plus_one_clock = _BoundaryClock(2.0)
    with pytest.raises(WorkbookSafetyViolation) as captured:
        WorkbookSafetyInspector(
            exact_limits,
            monotonic=plus_one_clock,
        ).inspect(str(BUDGET))

    assert captured.value.issue.code == "FS-WRK-026"
