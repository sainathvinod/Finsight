# Implements: FR-005/006/026/027/029/070/116, F-02-02 — step-oriented, human-operated review workflow.
# This is the interactive counterpart to Orchestrator.run_review(): it drives the SAME transition
# methods on the SAME Orchestrator instance, one step at a time, so there is a single source of
# transition rules (atomic persistence + audit + state advancement, resume gating, rejected safe
# stop). It holds a per-cycle, in-session recompute context; it performs no UI work and imports no
# UI framework.
from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from finsight.domain.review_cycle import ReviewCycle, CycleState
from finsight.application.orchestrator import _idx
from finsight.application.read_models.views import SummaryView
from finsight.application.errors import (
    MissingFileError, UnsupportedWorkbookError, ValidationRejectedError,
    VerificationRequiredError, InvalidTransitionError, DuplicateReviewError,
    ReviewNotFoundError, PersistenceError, ExportError,
)


@dataclass(frozen=True)
class ProvenanceItem:
    doc_type: str
    name: str
    fingerprint: str
    size: int
    period: str


@dataclass(frozen=True)
class UploadResult:
    items: List[ProvenanceItem]


@dataclass(frozen=True)
class ValidationResult:
    available: bool
    rejected_reason: Optional[str]
    readiness: Dict[str, Any]
    ged_valid: int
    budget_valid: int
    quarantined: int
    provenance: List[ProvenanceItem]


@dataclass(frozen=True)
class AnalysisResult:
    run_id: str
    config_version: str
    input_fingerprint: str
    finding_count: int


@dataclass(frozen=True)
class ExportResult:
    period: str
    content: Dict[str, Any]
    json_text: str


class ReviewWorkflowService:
    def __init__(self, orchestrator):
        self._o = orchestrator
        self._ctx: Dict[str, Dict[str, Any]] = {}   # cycle_id -> in-session recompute context

    # ---- session context (not persisted; mirrors the orchestrator's per-run ctx) ----
    def _ctx_for(self, cycle_id: str) -> Dict[str, Any]:
        return self._ctx.setdefault(cycle_id, {
            "provenance": None, "paths": None, "extracted": None, "readiness": None,
            "rejected": None, "vds": None, "findings": None, "run": None})

    def has_session_context(self, cycle_id: str) -> bool:
        """True if the source files have been (re)attached this session (needed to progress forward)."""
        return bool(self._ctx.get(cycle_id, {}).get("paths"))

    def validation_snapshot(self, cycle_id: str) -> Optional["ValidationResult"]:
        """The last in-session validation result for this review, or None if not processed yet.
        Read-only: it re-presents cached extraction output; it runs nothing."""
        ctx = self._ctx.get(cycle_id)
        if not ctx or ctx.get("extracted") is None:
            return None
        return self._validation_from_ctx(ctx)

    def _require_cycle(self, cycle_id: str) -> ReviewCycle:
        cycle = self._o.cycle_repo.get(cycle_id)
        if cycle is None:
            raise ReviewNotFoundError("Review not found: " + cycle_id, cycle_id)
        return cycle

    def state(self, cycle_id: str) -> Optional[str]:
        cycle = self._o.cycle_repo.get(cycle_id)
        return cycle.state.value if cycle else None

    # ---- Step 1: Review Setup ----
    def create_review(self, cycle_id: str, month: str, year: str) -> ReviewCycle:
        cid = (cycle_id or "").strip()
        if not cid or not (month or "").strip() or not (year or "").strip():
            raise InvalidTransitionError("A review needs an identifier, month, and year.")
        if self._o.cycle_repo.get(cid) is not None:
            raise DuplicateReviewError("A review already exists for " + cid + ".", cid)
        cycle = ReviewCycle(cid, month.strip(), year.strip(), CycleState.CREATED)
        try:
            with self._o.uow.atomic():
                self._o.cycle_repo.save(cycle)
                self._o._audit(cid, "setup", {"month": cycle.month, "year": cycle.year})
        except Exception as e:  # pragma: no cover - defensive
            raise PersistenceError("Could not create the review.", str(e)) from e
        return cycle

    def open_review(self, cycle_id: str) -> ReviewCycle:
        return self._require_cycle(cycle_id)

    # ---- Step 2: Data Upload (INTAKE) ----
    def upload(self, cycle_id: str, ged_path: str, budget_path: str) -> UploadResult:
        cycle = self._require_cycle(cycle_id)
        provenance, missing = self._o._build_provenance(cycle, ged_path, budget_path)
        if missing:
            raise MissingFileError(
                "Required file(s) missing or unreadable: " + ", ".join(missing) + ".", missing)
        ctx = self._ctx_for(cycle_id)
        ctx["provenance"] = provenance
        ctx["paths"] = {"GED": ged_path, "BUDGET": budget_path}
        try:
            self._o._do_intake(cycle, ctx)  # idempotent: skipped if already past INTAKE
        except Exception as e:
            raise PersistenceError("Could not record the uploaded files.", str(e)) from e
        return UploadResult([ProvenanceItem(f.doc_type, f.name, f.fingerprint, f.size, f.period)
                             for f in provenance])

    # ---- Steps 3+4: Upload Validation + Processing (PROCESSED) ----
    # Split so the heavy extraction (reading workbooks) can run off the UI thread while the
    # database transition stays on the main thread (SQLite connections are thread-bound).
    def prepare_extraction(self, cycle_id: str) -> None:
        """Run the extraction pipeline into the session context. Threadable — no database access."""
        ctx = self._ctx_for(cycle_id)
        if not ctx.get("paths"):
            raise InvalidTransitionError("Upload the source files before processing.")
        g, b = ctx["paths"]["GED"], ctx["paths"]["BUDGET"]
        try:
            extracted = self._o._extract(g, b)
        except Exception as e:
            raise UnsupportedWorkbookError("A source workbook could not be read.", str(e)) from e
        ctx["extracted"] = extracted
        ctx["readiness"] = extracted["readiness"]
        ctx["rejected"] = None if extracted["available"] else extracted["reason"]

    def finalize_processing(self, cycle_id: str) -> ValidationResult:
        """Persist the PROCESSED transition (audit + state). Main-thread only (touches the DB)."""
        cycle = self._require_cycle(cycle_id)
        ctx = self._ctx_for(cycle_id)
        if ctx.get("extracted") is None:
            raise InvalidTransitionError("Process the uploaded data before continuing.")
        self._o._do_processed(cycle, ctx)   # audits validate + extract; safe stop leaves state=PROCESSED
        return self._validation_from_ctx(ctx)

    def process(self, cycle_id: str) -> ValidationResult:
        """Synchronous convenience: extract then persist (used by tests and headless callers)."""
        self._require_cycle(cycle_id)
        self.prepare_extraction(cycle_id)
        return self.finalize_processing(cycle_id)

    def _validation_from_ctx(self, ctx) -> ValidationResult:
        ex = ctx["extracted"]
        return ValidationResult(
            available=bool(ex["available"]),
            rejected_reason=ctx.get("rejected"),
            readiness=ex["readiness"],
            ged_valid=len(ex.get("ged_valid", [])),
            budget_valid=len(ex.get("budget_valid", [])),
            quarantined=len(ex.get("ged_quarantined", [])) + len(ex.get("budget_quarantined", [])),
            provenance=[ProvenanceItem(f.doc_type, f.name, f.fingerprint, f.size, f.period)
                        for f in (ctx.get("provenance") or [])],
        )

    # ---- Step 5: Verification (VERIFIED) — explicit human approval ----
    def verify(self, cycle_id: str) -> ReviewCycle:
        cycle = self._require_cycle(cycle_id)
        ctx = self._ctx_for(cycle_id)
        if ctx.get("extracted") is None:
            raise InvalidTransitionError("Process the uploaded data before verification.")
        if ctx.get("rejected"):
            raise ValidationRejectedError("Rejected or unavailable data cannot be verified.", ctx["rejected"])
        try:
            ctx["vds"] = self._o._build_verified(cycle_id, ctx["extracted"], approve=True)
        except PermissionError as e:
            raise ValidationRejectedError("This data cannot be verified.", str(e)) from e
        try:
            self._o._do_verified(cycle, ctx)   # idempotent; audits "verify"
        except Exception as e:
            raise PersistenceError("Could not record verification.", str(e)) from e
        return cycle

    # ---- Step 6: Analysis (ANALYZED) — deterministic, gated on verification ----
    def analyze(self, cycle_id: str) -> AnalysisResult:
        cycle = self._require_cycle(cycle_id)
        if _idx(cycle.state) < _idx(CycleState.VERIFIED):
            raise VerificationRequiredError("Verify the data before running analysis.")
        ctx = self._ctx_for(cycle_id)
        if ctx.get("vds") is None:
            # Reopened this session without re-running verification (deterministic recompute needed).
            raise VerificationRequiredError(
                "Re-select the source files and re-verify to run analysis in this session.")
        self._o._do_analyzed(cycle, ctx)   # idempotent: no duplicate findings / rule run
        run = self._o.run_repo.get_by_cycle(cycle_id) or {}
        return AnalysisResult(run.get("run_id", ""), run.get("config_version", ""),
                              run.get("input_fingerprint", ""), int(run.get("finding_count", 0)))

    # ---- Step 8: Leadership Summary (SUMMARIZED) ----
    def summarize(self, cycle_id: str) -> SummaryView:
        cycle = self._require_cycle(cycle_id)
        if _idx(cycle.state) < _idx(CycleState.ANALYZED):
            raise InvalidTransitionError("Run analysis before generating the leadership summary.")
        self._o._do_summarized(cycle, self._ctx_for(cycle_id))
        run = self._o.run_repo.get_by_cycle(cycle_id) or {}
        s = self._o.reporting.summary(cycle, self._o.finding_repo.list(cycle_id), run)
        return SummaryView(s["section"], s["period"], s["status_label"], s["finding_count"], s["budget_health_lines"])

    # ---- Step 9: Export (EXPORTED) ----
    def export(self, cycle_id: str) -> ExportResult:
        cycle = self._require_cycle(cycle_id)
        if _idx(cycle.state) < _idx(CycleState.SUMMARIZED):
            raise InvalidTransitionError("Generate the leadership summary before export.")
        ctx = self._ctx_for(cycle_id)
        try:
            self._o._do_exported(cycle, ctx)   # idempotent; audits "export"
        except Exception as e:
            raise ExportError("Could not produce the export.", str(e)) from e
        content = ctx.get("export")
        if content is None:  # already exported in a prior session — rebuild deterministic content
            run = self._o.run_repo.get_by_cycle(cycle_id) or {}
            summary = self._o.reporting.summary(cycle, self._o.finding_repo.list(cycle_id), run)
            content = self._o.export.build(cycle, summary, run, data_as_of=self._o.clock.now())
        return ExportResult(content.get("period", ""), content, self._o.export.to_json(content))
