# Implements: V2 FR-126/127/132/175/180-183, NFR-093-096, ADR-V2-006.
"""Bounded, read-only ``.xlsx`` source snapshots and WRL-001 package checks.

The snapshot bytes are the single byte stream used for both SHA-256 provenance
and extraction.  This module never writes to, recalculates, or otherwise opens
the source workbook for mutation.
"""
from __future__ import annotations

import hashlib
import io
import os
import re
import time
import zipfile
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath
from typing import Callable, Iterable
from xml.etree import ElementTree as ET

from finsight.domain.source_intake import SourceIssue


@dataclass(frozen=True)
class WorkbookSafetyLimits:
    compressed_bytes: int = 64 * 1024 * 1024
    total_uncompressed_bytes: int = 512 * 1024 * 1024
    one_uncompressed_entry_bytes: int = 128 * 1024 * 1024
    expansion_ratio: int = 100
    zip_entries: int = 10_000
    worksheets: int = 32
    rows_per_worksheet: int = 100_000
    columns_per_worksheet: int = 256
    populated_cells: int = 2_000_000
    formula_cells: int = 250_000
    merged_ranges: int = 20_000
    shared_string_entries: int = 1_000_000
    shared_string_bytes: int = 128 * 1024 * 1024
    ged_transactions: int = 10_000
    wall_seconds: float = 90.0

    def __post_init__(self) -> None:
        values = vars(self)
        if any(not isinstance(value, (int, float)) or value <= 0 for value in values.values()):
            raise ValueError("Workbook safety limits must all be positive.")


@dataclass(frozen=True)
class WorkbookSnapshot:
    path: str = field(repr=False, compare=False)
    file_name: str
    byte_size: int
    sha256: str
    content: bytes = field(repr=False, compare=False)


class WorkbookSafetyViolation(RuntimeError):
    """A user-safe, classified WRL-001 rejection."""

    def __init__(
        self,
        issue: SourceIssue,
        *,
        byte_size: int = 0,
        sha256: str = "",
    ) -> None:
        super().__init__(issue.message)
        self.issue = issue
        self.byte_size = byte_size
        self.sha256 = sha256


_REQUIRED_PARTS = frozenset(
    {
        "[Content_Types].xml",
        "_rels/.rels",
        "xl/workbook.xml",
        "xl/_rels/workbook.xml.rels",
    }
)
_EXECUTABLE_SUFFIXES = frozenset(
    {
        ".bat",
        ".cmd",
        ".com",
        ".dll",
        ".exe",
        ".jar",
        ".js",
        ".msi",
        ".ps1",
        ".scr",
        ".vbs",
    }
)
_FORBIDDEN_PART_PREFIXES = (
    "xl/activex/",
    "xl/embeddings/",
    "xl/externallinks/",
)
_CELL_REFERENCE = re.compile(r"^\$?([A-Z]{1,3})\$?([1-9][0-9]*)$")
_DIMENSION_REFERENCE = re.compile(
    r"^\$?([A-Z]{1,3})\$?([1-9][0-9]*)(?::\$?([A-Z]{1,3})\$?([1-9][0-9]*))?$"
)


def verify_unchanged(path: str, expected_sha256: str, expected_size: int) -> bool:
    """Recheck a selected source immediately before authoritative persistence."""

    if not expected_sha256 or len(expected_sha256) != 64 or expected_size < 0:
        return False
    try:
        with open(path, "rb") as source:
            observed = os.fstat(source.fileno())
            if not os.path.isfile(path) or observed.st_size != expected_size:
                return False
            digest = hashlib.sha256()
            size = 0
            for chunk in iter(lambda: source.read(64 * 1024), b""):
                digest.update(chunk)
                size += len(chunk)
    except (OSError, ValueError):
        return False
    return size == expected_size and digest.hexdigest() == expected_sha256


class WorkbookSafetyInspector:
    """Create one immutable source snapshot after the WRL-001 checks pass."""

    def __init__(
        self,
        limits: WorkbookSafetyLimits | None = None,
        *,
        monotonic: Callable[[], float] = time.monotonic,
    ) -> None:
        self.limits = limits or WorkbookSafetyLimits()
        self._monotonic = monotonic

    def inspect(self, path: str) -> WorkbookSnapshot:
        started = self._monotonic()
        source_path = Path(path)
        if source_path.suffix.lower() != ".xlsx":
            self._reject(
                "FS-WRK-001",
                "Workbook safety",
                "Only an .xlsx workbook can be used for this source role.",
            )
        try:
            if not source_path.is_file():
                self._reject(
                    "FS-SRC-001",
                    "Source access",
                    "The selected source file does not exist or is not a regular file.",
                )
            content, digest = self._read_source(source_path, started)
        except WorkbookSafetyViolation:
            raise
        except (OSError, PermissionError) as exc:
            raise WorkbookSafetyViolation(
                SourceIssue(
                    "FS-SRC-002",
                    "Source access",
                    "The selected source file could not be read.",
                )
            ) from exc

        snapshot = WorkbookSnapshot(
            path=str(source_path),
            file_name=source_path.name,
            byte_size=len(content),
            sha256=digest,
            content=content,
        )
        try:
            self._inspect_package(snapshot, started)
        except WorkbookSafetyViolation as violation:
            raise WorkbookSafetyViolation(
                violation.issue,
                byte_size=snapshot.byte_size,
                sha256=snapshot.sha256,
            ) from violation
        return snapshot

    def verify_unchanged(
        self, path: str, expected_sha256: str, expected_size: int
    ) -> bool:
        return verify_unchanged(path, expected_sha256, expected_size)

    def _read_source(self, path: Path, started: float) -> tuple[bytes, str]:
        with path.open("rb") as source:
            initial = os.fstat(source.fileno())
            if initial.st_size > self.limits.compressed_bytes:
                self._reject(
                    "FS-WRK-002",
                    "Workbook safety",
                    "The workbook exceeds the WRL-001 compressed-size limit.",
                )
            digest = hashlib.sha256()
            chunks: list[bytes] = []
            size = 0
            while True:
                self._check_deadline(started)
                chunk = source.read(64 * 1024)
                if not chunk:
                    break
                size += len(chunk)
                if size > self.limits.compressed_bytes:
                    self._reject(
                        "FS-WRK-002",
                        "Workbook safety",
                        "The workbook exceeds the WRL-001 compressed-size limit.",
                    )
                chunks.append(chunk)
                digest.update(chunk)
            final = os.fstat(source.fileno())
        if (
            final.st_dev != initial.st_dev
            or final.st_ino != initial.st_ino
            or final.st_size != initial.st_size
            or size != initial.st_size
        ):
            self._reject(
                "FS-SRC-003",
                "Source access",
                "The selected source changed while FinSight was reading it.",
            )
        return b"".join(chunks), digest.hexdigest()

    def _inspect_package(self, snapshot: WorkbookSnapshot, started: float) -> None:
        try:
            workbook = zipfile.ZipFile(io.BytesIO(snapshot.content))
        except (zipfile.BadZipFile, zipfile.LargeZipFile) as exc:
            raise WorkbookSafetyViolation(
                SourceIssue(
                    "FS-WRK-003",
                    "Workbook safety",
                    "The selected file is not a readable Office Open XML workbook.",
                )
            ) from exc

        with workbook:
            infos = workbook.infolist()
            if len(infos) > self.limits.zip_entries:
                self._reject(
                    "FS-WRK-004",
                    "Workbook safety",
                    "The workbook exceeds the WRL-001 ZIP-entry limit.",
                )
            self._check_entry_names(infos)
            self._check_entry_sizes(infos)
            names = {info.filename for info in infos}
            missing = sorted(_REQUIRED_PARTS - names)
            if missing:
                self._reject(
                    "FS-WRK-005",
                    "Workbook safety",
                    "The workbook package is missing required Office Open XML parts.",
                )
            self._check_forbidden_parts(names)
            self._check_content_types(workbook)
            self._check_relationships(workbook, infos, started)
            self._check_workbook_shape(workbook, infos, started)

    def _check_entry_names(self, infos: Iterable[zipfile.ZipInfo]) -> None:
        observed: set[str] = set()
        for info in infos:
            normalized = info.filename.replace("\\", "/")
            pure = PurePosixPath(normalized)
            key = normalized.casefold()
            if (
                not normalized
                or "\\" in info.filename
                or normalized.startswith("/")
                or pure.is_absolute()
                or ".." in pure.parts
                or "\x00" in normalized
            ):
                self._reject(
                    "FS-WRK-006",
                    "Workbook safety",
                    "The workbook contains an unsafe package path.",
                )
            if key in observed:
                self._reject(
                    "FS-WRK-007",
                    "Workbook safety",
                    "The workbook contains duplicate or ambiguous package entries.",
                )
            observed.add(key)
            if info.flag_bits & 0x1:
                self._reject(
                    "FS-WRK-008",
                    "Workbook safety",
                    "Encrypted or password-protected workbook entries are not supported.",
                )

    def _check_entry_sizes(self, infos: Iterable[zipfile.ZipInfo]) -> None:
        total_uncompressed = 0
        total_compressed = 0
        for info in infos:
            if info.file_size > self.limits.one_uncompressed_entry_bytes:
                self._reject(
                    "FS-WRK-009",
                    "Workbook safety",
                    "A workbook package entry exceeds the WRL-001 size limit.",
                )
            if info.file_size and (
                info.compress_size == 0
                or info.file_size / info.compress_size > self.limits.expansion_ratio
            ):
                self._reject(
                    "FS-WRK-010",
                    "Workbook safety",
                    "The workbook exceeds the WRL-001 expansion-ratio limit.",
                )
            total_uncompressed += info.file_size
            total_compressed += info.compress_size
        if total_uncompressed > self.limits.total_uncompressed_bytes:
            self._reject(
                "FS-WRK-011",
                "Workbook safety",
                "The workbook exceeds the WRL-001 total uncompressed-size limit.",
            )
        if total_uncompressed and (
            total_compressed == 0
            or total_uncompressed / total_compressed > self.limits.expansion_ratio
        ):
            self._reject(
                "FS-WRK-010",
                "Workbook safety",
                "The workbook exceeds the WRL-001 expansion-ratio limit.",
            )

    def _check_forbidden_parts(self, names: Iterable[str]) -> None:
        for name in names:
            lowered = name.casefold()
            suffix = PurePosixPath(lowered).suffix
            if (
                lowered == "xl/vbaproject.bin"
                or any(lowered.startswith(prefix) for prefix in _FORBIDDEN_PART_PREFIXES)
                or suffix in _EXECUTABLE_SUFFIXES
            ):
                self._reject(
                    "FS-WRK-012",
                    "Workbook safety",
                    "The workbook contains macros, external links, or embedded executable content.",
                )

    def _check_content_types(self, workbook: zipfile.ZipFile) -> None:
        content = self._xml_bytes(workbook, "[Content_Types].xml")
        lowered = content.lower()
        forbidden = (
            b"macroenabled",
            b"vbaproject",
            b"activex",
            b"oleobject",
            b"external-link",
        )
        if any(token in lowered for token in forbidden):
            self._reject(
                "FS-WRK-012",
                "Workbook safety",
                "The workbook contains macros, external links, or embedded executable content.",
            )

    def _check_relationships(
        self,
        workbook: zipfile.ZipFile,
        infos: Iterable[zipfile.ZipInfo],
        started: float,
    ) -> None:
        for info in infos:
            if not info.filename.casefold().endswith(".rels"):
                continue
            self._check_deadline(started)
            root = self._xml_root(workbook, info.filename)
            for relationship in root.iter():
                if _local_name(relationship.tag) != "Relationship":
                    continue
                if relationship.attrib.get("TargetMode", "").casefold() == "external":
                    self._reject(
                        "FS-WRK-013",
                        "Workbook safety",
                        "External workbook relationships are not supported.",
                    )

    def _check_workbook_shape(
        self,
        workbook: zipfile.ZipFile,
        infos: Iterable[zipfile.ZipInfo],
        started: float,
    ) -> None:
        root = self._xml_root(workbook, "xl/workbook.xml")
        if any(_local_name(node.tag) == "workbookProtection" for node in root.iter()):
            self._reject(
                "FS-WRK-014",
                "Workbook safety",
                "Workbook or worksheet protection is not supported.",
            )
        worksheet_count = sum(
            1 for node in root.iter() if _local_name(node.tag) == "sheet"
        )
        if worksheet_count > self.limits.worksheets:
            self._reject(
                "FS-WRK-015",
                "Workbook safety",
                "The workbook exceeds the WRL-001 worksheet limit.",
            )

        populated = 0
        formulas = 0
        merges = 0
        worksheet_infos = [
            info
            for info in infos
            if info.filename.casefold().startswith("xl/worksheets/")
            and info.filename.casefold().endswith(".xml")
            and "/_rels/" not in info.filename.casefold()
        ]
        for info in worksheet_infos:
            self._check_deadline(started)
            data = self._xml_bytes(workbook, info.filename)
            sheet_populated, sheet_formulas, sheet_merges = self._worksheet_metrics(
                data, started
            )
            populated += sheet_populated
            formulas += sheet_formulas
            merges += sheet_merges
            if populated > self.limits.populated_cells:
                self._reject(
                    "FS-WRK-016",
                    "Workbook safety",
                    "The workbook exceeds the WRL-001 populated-cell limit.",
                )
            if formulas > self.limits.formula_cells:
                self._reject(
                    "FS-WRK-017",
                    "Workbook safety",
                    "The workbook exceeds the WRL-001 formula-cell limit.",
                )
            if merges > self.limits.merged_ranges:
                self._reject(
                    "FS-WRK-018",
                    "Workbook safety",
                    "The workbook exceeds the WRL-001 merged-range limit.",
                )

        shared = next(
            (
                info
                for info in infos
                if info.filename.casefold() == "xl/sharedstrings.xml"
            ),
            None,
        )
        if shared is not None:
            if shared.file_size > self.limits.shared_string_bytes:
                self._reject(
                    "FS-WRK-019",
                    "Workbook safety",
                    "The workbook exceeds the WRL-001 shared-string size limit.",
                )
            shared_root = self._xml_root(workbook, shared.filename)
            declared = max(
                int(shared_root.attrib.get("count", "0") or 0),
                int(shared_root.attrib.get("uniqueCount", "0") or 0),
            )
            actual = sum(
                1 for node in shared_root.iter() if _local_name(node.tag) == "si"
            )
            if max(declared, actual) > self.limits.shared_string_entries:
                self._reject(
                    "FS-WRK-020",
                    "Workbook safety",
                    "The workbook exceeds the WRL-001 shared-string entry limit.",
                )

    def _worksheet_metrics(
        self, data: bytes, started: float
    ) -> tuple[int, int, int]:
        populated = 0
        formulas = 0
        merges = 0
        try:
            iterator = ET.iterparse(io.BytesIO(data), events=("start",))
            for _event, node in iterator:
                self._check_deadline(started)
                name = _local_name(node.tag)
                if name == "dimension":
                    self._check_dimension(node.attrib.get("ref", ""))
                elif name == "row":
                    row_text = node.attrib.get("r")
                    if row_text and int(row_text) > self.limits.rows_per_worksheet:
                        self._reject(
                            "FS-WRK-021",
                            "Workbook safety",
                            "A worksheet exceeds the WRL-001 row limit.",
                        )
                elif name == "c":
                    populated += 1
                    reference = node.attrib.get("r", "")
                    if reference:
                        column, row = _cell_coordinate(reference)
                        if (
                            column > self.limits.columns_per_worksheet
                            or row > self.limits.rows_per_worksheet
                        ):
                            self._reject(
                                "FS-WRK-022",
                                "Workbook safety",
                                "A worksheet exceeds the WRL-001 row or column limit.",
                            )
                elif name == "f":
                    formulas += 1
                elif name == "mergeCell":
                    merges += 1
                elif name == "sheetProtection":
                    self._reject(
                        "FS-WRK-014",
                        "Workbook safety",
                        "Workbook or worksheet protection is not supported.",
                    )
        except (ET.ParseError, TypeError, ValueError) as exc:
            raise WorkbookSafetyViolation(
                SourceIssue(
                    "FS-WRK-023",
                    "Workbook safety",
                    "The workbook contains malformed or ambiguous worksheet XML.",
                )
            ) from exc
        return populated, formulas, merges

    def _check_dimension(self, reference: str) -> None:
        if not reference:
            return
        match = _DIMENSION_REFERENCE.fullmatch(reference)
        if match is None:
            self._reject(
                "FS-WRK-023",
                "Workbook safety",
                "The workbook contains malformed or ambiguous worksheet XML.",
            )
        final_column = match.group(3) or match.group(1)
        final_row = int(match.group(4) or match.group(2))
        if (
            _column_number(final_column) > self.limits.columns_per_worksheet
            or final_row > self.limits.rows_per_worksheet
        ):
            self._reject(
                "FS-WRK-022",
                "Workbook safety",
                "A worksheet exceeds the WRL-001 row or column limit.",
            )

    def _xml_bytes(self, workbook: zipfile.ZipFile, name: str) -> bytes:
        try:
            data = workbook.read(name)
        except (KeyError, OSError, RuntimeError, zipfile.BadZipFile) as exc:
            raise WorkbookSafetyViolation(
                SourceIssue(
                    "FS-WRK-024",
                    "Workbook safety",
                    "A required workbook package part could not be read.",
                )
            ) from exc
        lowered = data.lower()
        if b"<!doctype" in lowered or b"<!entity" in lowered:
            self._reject(
                "FS-WRK-025",
                "Workbook safety",
                "Document type declarations and XML entities are not supported.",
            )
        return data

    def _xml_root(self, workbook: zipfile.ZipFile, name: str) -> ET.Element:
        try:
            return ET.fromstring(self._xml_bytes(workbook, name))
        except ET.ParseError as exc:
            raise WorkbookSafetyViolation(
                SourceIssue(
                    "FS-WRK-023",
                    "Workbook safety",
                    "The workbook contains malformed or ambiguous package XML.",
                )
            ) from exc

    def _check_deadline(self, started: float) -> None:
        if self._monotonic() - started > self.limits.wall_seconds:
            self._reject(
                "FS-WRK-026",
                "Workbook safety",
                "Workbook processing exceeded the WRL-001 time limit.",
            )

    @staticmethod
    def _reject(code: str, category: str, message: str) -> None:
        raise WorkbookSafetyViolation(SourceIssue(code, category, message))


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _column_number(label: str) -> int:
    number = 0
    for character in label:
        number = number * 26 + (ord(character) - ord("A") + 1)
    return number


def _cell_coordinate(reference: str) -> tuple[int, int]:
    match = _CELL_REFERENCE.fullmatch(reference)
    if match is None:
        raise ValueError("invalid cell coordinate")
    return _column_number(match.group(1)), int(match.group(2))
