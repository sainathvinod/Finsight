# Phase 5.4 — deterministic verification-preview + review-readiness read models. Read-only, immutable,
# no AI, no source mutation. Representative rows come from the session's already-normalized data (the
# extraction context); nothing re-reads raw workbooks and no duplicate rows are persisted. Readiness
# is DERIVED from persisted workflow state, enriched with session validation facts when available.
from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from finsight.domain.review_cycle import CycleState, state_rank

# Representative-row display cap (first N accepted rows in stable source order; no sampling/sorting).
PREVIEW_ROW_CAP = 10

# Columns actually present in the NORMALIZED rows the deterministic engine uses (the extraction
# pipeline intentionally reduces raw workbook rows to these fields). Showing exactly these makes the
# preview an honest view of what will be analyzed — no raw-only columns (e.g. account_name, vendor)
# that normalization does not retain.
_GED_COLUMNS = ("account", "amount", "confidence", "source")
_BUDGET_COLUMNS = ("account", "budget", "atd", "source")


@dataclass(frozen=True)
class SourcePreview:
    source_type: str                       # "GED" | "Budget Tracker"
    filename: str
    period: str
    columns: Tuple[str, ...]
    rows: Tuple[Tuple[str, ...], ...]      # first N accepted rows, stringified, source order
    accepted_rows: int
    quarantined_rows: int
    available: bool
    messages: Tuple[str, ...]
    fingerprint: str                       # secondary technical metadata


@dataclass(frozen=True)
class VerificationPreview:
    available: bool
    rejected_reason: Optional[str]
    sources: Tuple[SourcePreview, ...] = ()


@dataclass(frozen=True)
class SourceRecords:
    """ALL extracted records for one source (target-product §9) — every accepted and quarantined row,
    each carrying its lineage (the `source` cell = file!row). No cap and no sampling: this is the full
    extracted dataset the reviewer verifies, with the user's current corrections overlaid. Read-only;
    nothing is re-read or persisted."""
    source_type: str                       # "GED" | "Budget Tracker"
    document_type: str                     # "GED" | "BUDGET" (the correction key)
    filename: str
    period: str
    columns: Tuple[str, ...]               # leading "status" + the normalized columns (incl. lineage)
    rows: Tuple[Tuple[str, ...], ...]       # every accepted then quarantined row, effective values
    accepted_rows: int
    quarantined_rows: int
    available: bool
    editable_columns: Tuple[str, ...]      # column indices editable (correctable) for this source
    corrected_cells: Tuple[Tuple[int, int], ...] = ()      # (row, col) cells showing a correction
    originals: Dict = None                  # {(row, col): original extracted value} for corrected cells
    source_refs: Tuple[str, ...] = ()       # per-row lineage ref (parallel to rows), for save calls


def source_records(source_type: str, document_type: str, filename: str, period: str,
                   columns: Tuple[str, ...], accepted_rows: List[dict], quarantined_rows: List[dict],
                   available: bool, overrides=None, editable_fields=()) -> SourceRecords:
    """Build the full record set with the effective corrections overlaid. `overrides` maps
    (source_ref, field) -> (current_value, original_value) for non-reverted corrections; only ACCEPTED
    rows are overlaid (only they feed analysis)."""
    overrides = overrides or {}
    cols = ("status",) + tuple(columns)
    editable_columns = tuple(cols.index(f) for f in editable_fields if f in cols)
    rows: List[Tuple[str, ...]] = []
    refs: List[str] = []
    corrected: List[Tuple[int, int]] = []
    originals: Dict = {}

    def build(status: str, r: dict, apply_overrides: bool):
        ridx = len(rows)
        src = _fmt(r.get("source")) if "source" in columns else ""
        cells = [status]
        for ci, c in enumerate(columns):
            val = _fmt(r.get(c))
            if apply_overrides and (src, c) in overrides:
                current, original = overrides[(src, c)]
                val = current
                corrected.append((ridx, ci + 1))          # +1 for the leading status column
                originals[(ridx, ci + 1)] = original
            cells.append(val)
        rows.append(tuple(cells))
        refs.append(src)

    for r in accepted_rows:
        build("Accepted", r, True)
    for r in quarantined_rows:
        build("Quarantined", r, False)
    return SourceRecords(source_type, document_type, filename, period, cols, tuple(rows),
                         len(accepted_rows), len(quarantined_rows), available, editable_columns,
                         tuple(corrected), dict(originals), tuple(refs))


@dataclass(frozen=True)
class ReviewReadinessSummary:
    """Deterministic, categorical review readiness. No numeric score. Row-count/validation facts are
    populated only when the in-session snapshot is available (they are session-scoped, not persisted)."""
    cycle_id: str
    required_sources_present: bool
    normalized_data_available: bool
    validation_status: str                 # "pending" | "passed" | "failed"
    analysis_available: bool
    export_ready: bool
    accepted_rows: Optional[int] = None
    quarantined_rows: Optional[int] = None
    blocking_reasons: Tuple[str, ...] = ()


def _fmt(value) -> str:
    return "" if value is None else str(value)


def source_preview(source_type: str, filename: str, period: str, columns: Tuple[str, ...],
                   accepted_rows: List[dict], quarantined: int, available: bool,
                   messages: List[str], fingerprint: str) -> SourcePreview:
    rows = tuple(tuple(_fmt(r.get(c)) for c in columns) for r in accepted_rows[:PREVIEW_ROW_CAP])
    return SourcePreview(source_type, filename, period, columns, rows, len(accepted_rows),
                         quarantined, available, tuple(messages), fingerprint)


def ged_columns() -> Tuple[str, ...]:
    return _GED_COLUMNS


def budget_columns() -> Tuple[str, ...]:
    return _BUDGET_COLUMNS


def build_readiness(cycle_id: str, state: Optional[str], snapshot=None) -> ReviewReadinessSummary:
    """Derive readiness from persisted workflow state, enriched by the session snapshot when present.
    `snapshot` is the ValidationResult for the active session (or None for a fresh-loaded review)."""
    r = state_rank(state) if state else -1
    present = r >= state_rank(CycleState.INTAKE)
    normalized = r >= state_rank(CycleState.PROCESSED)
    analysis = r >= state_rank(CycleState.ANALYZED)
    export_ready = r >= state_rank(CycleState.SUMMARIZED)

    accepted = quarantined = None
    validation = "pending"
    if snapshot is not None:
        accepted = snapshot.ged_valid + snapshot.budget_valid
        quarantined = snapshot.quarantined
        validation = "failed" if snapshot.rejected_reason else ("passed" if snapshot.available else "failed")
    elif normalized:
        validation = "passed"   # reaching PROCESSED means validation accepted the data

    reasons: List[str] = []
    if r < state_rank(CycleState.INTAKE):
        reasons.append("Source files not uploaded")
    elif r < state_rank(CycleState.PROCESSED):
        reasons.append("Source data not processed")
    elif snapshot is not None and snapshot.rejected_reason:
        reasons.append("Validation failed: " + snapshot.rejected_reason)
    else:
        if snapshot is not None and snapshot.quarantined:
            reasons.append(f"{snapshot.quarantined} row(s) quarantined — review recommended")
        if r < state_rank(CycleState.VERIFIED):
            reasons.append("Data not yet verified")
        elif r < state_rank(CycleState.ANALYZED):
            reasons.append("Analysis not run")
        elif r < state_rank(CycleState.SUMMARIZED):
            reasons.append("Leadership summary not generated")
        elif r < state_rank(CycleState.EXPORTED):
            reasons.append("Not yet exported")

    return ReviewReadinessSummary(
        cycle_id=cycle_id, required_sources_present=present, normalized_data_available=normalized,
        validation_status=validation, analysis_available=analysis, export_ready=export_ready,
        accepted_rows=accepted, quarantined_rows=quarantined, blocking_reasons=tuple(reasons))
