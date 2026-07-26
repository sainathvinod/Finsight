# Implements: FR-005/006/026/027/029/070/116, F-02-02 — step-oriented, human-operated review workflow.
# Interactive counterpart to the batch run_review() path: it drives the SAME public TransitionEngine
# methods, one step at a time. It is STATELESS — it holds no per-cycle context; the caller owns a
# ReviewSession that carries transient recompute state. No UI framework is imported here.
from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from finsight.domain.review_cycle import ReviewCycle, CycleState, has_reached
from finsight.application.review_session import ReviewSession
from finsight.application.read_models.views import SummaryView
from finsight.application.errors import (
    MissingFileError, UnsupportedWorkbookError, ValidationRejectedError,
    VerificationRequiredError, InvalidTransitionError, DuplicateReviewError,
    ReviewNotFoundError, PersistenceError, ExportError,
)
from finsight.diagnostics import get_logger

_log = get_logger("workflow")


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
    def __init__(self, engine):
        self._e = engine   # shared TransitionEngine; the single source of transition rules

    # ---- lookups ----
    def _require_cycle(self, cycle_id: str) -> ReviewCycle:
        cycle = self._e.cycle_repo.get(cycle_id)
        if cycle is None:
            raise ReviewNotFoundError("Review not found: " + cycle_id, cycle_id)
        return cycle

    def state(self, cycle_id: str) -> Optional[str]:
        cycle = self._e.cycle_repo.get(cycle_id)
        return cycle.state.value if cycle else None

    # ---- Step 1: Review Setup ----
    def create_review(self, cycle_id: str, month: str, year: str) -> ReviewCycle:
        cid = (cycle_id or "").strip()
        if not cid or not (month or "").strip() or not (year or "").strip():
            raise InvalidTransitionError("A review needs an identifier, month, and year.")
        if self._e.cycle_repo.get(cid) is not None:
            raise DuplicateReviewError("A review already exists for " + cid + ".", cid)
        cycle = ReviewCycle(cid, month.strip(), year.strip(), CycleState.CREATED)
        try:
            self._e.setup(cycle)
        except Exception as e:  # pragma: no cover - defensive
            _log.error("create_review failed cid=%s: %s", cid, type(e).__name__, exc_info=True)
            raise PersistenceError("Could not create the review.", str(e)) from e
        _log.info("review created cid=%s", cid)
        return cycle

    def open_review(self, cycle_id: str) -> ReviewCycle:
        return self._require_cycle(cycle_id)

    # ---- Step 2: Data Upload (INTAKE) ----
    def upload(self, session: ReviewSession, ged_path: str, budget_path: str,
               invoice_path: str = None, acknowledged_missing=None) -> UploadResult:
        cycle = self._require_cycle(session.cycle_id)
        provenance, missing = self._e.build_provenance(cycle, ged_path, budget_path, invoice_path)
        if missing:
            _log.warning("upload rejected cid=%s missing=%s", session.cycle_id, missing)
            raise MissingFileError(
                "Required file(s) missing or unreadable: " + ", ".join(missing) + ".", missing)
        session.ctx["provenance"] = provenance
        # Only GED/BUDGET feed extraction; the invoice is captured for provenance/audit only (§6).
        paths = {"GED": ged_path, "BUDGET": budget_path}
        if invoice_path:
            paths["INVOICE"] = invoice_path
        session.ctx["paths"] = paths
        # §7: sources the user explicitly chose to proceed WITHOUT (two-step "Continue anyway"). Recorded
        # as an audit fact so the decision never disappears (§19) and can be disclosed in report scope.
        session.ctx["acknowledged_missing"] = list(acknowledged_missing or [])
        try:
            self._e.do_intake(cycle, session.ctx)
        except Exception as e:
            _log.error("intake failed cid=%s: %s", session.cycle_id, type(e).__name__, exc_info=True)
            raise PersistenceError("Could not record the uploaded files.", str(e)) from e
        return UploadResult([ProvenanceItem(f.doc_type, f.name, f.fingerprint, f.size, f.period)
                             for f in provenance])

    # ---- Steps 3+4: Upload Validation + Processing (PROCESSED) ----
    # Split so heavy extraction runs off the UI thread (no DB) while the transition persists on the
    # UI thread (SQLite connections are thread-bound).
    def prepare_extraction(self, session: ReviewSession) -> None:
        """Threadable — no database access."""
        ctx = session.ctx
        if not ctx.get("paths"):
            raise InvalidTransitionError("Upload the source files before processing.")
        g, b = ctx["paths"]["GED"], ctx["paths"]["BUDGET"]
        try:
            extracted = self._e.extract(g, b)
        except Exception as e:
            _log.error("extraction failed cid=%s: %s", session.cycle_id, type(e).__name__, exc_info=True)
            raise UnsupportedWorkbookError("A source workbook could not be read.", str(e)) from e
        ctx["extracted"] = extracted
        ctx["readiness"] = extracted["readiness"]
        ctx["rejected"] = None if extracted["available"] else extracted["reason"]

    def finalize_processing(self, session: ReviewSession) -> ValidationResult:
        """Main-thread only (touches the DB)."""
        cycle = self._require_cycle(session.cycle_id)
        ctx = session.ctx
        if ctx.get("extracted") is None:
            raise InvalidTransitionError("Process the uploaded data before continuing.")
        self._e.do_processed(cycle, ctx)
        if ctx.get("rejected"):
            _log.warning("validation rejected cid=%s reason=%s", session.cycle_id, ctx["rejected"])
        return self._validation_from_ctx(ctx)

    def process(self, session: ReviewSession) -> ValidationResult:
        self._require_cycle(session.cycle_id)
        self.prepare_extraction(session)
        return self.finalize_processing(session)

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

    def validation_snapshot(self, session: ReviewSession) -> Optional[ValidationResult]:
        if session is None or session.ctx.get("extracted") is None:
            return None
        return self._validation_from_ctx(session.ctx)

    def verification_preview(self, session: ReviewSession):
        """Read-only representative-row preview of the SESSION's already-normalized data (Phase 5.4).
        None when no extraction exists in this session. Reads no raw files and persists nothing."""
        from finsight.application.read_models import verification as V
        if session is None or session.ctx.get("extracted") is None:
            return None
        ex = session.ctx["extracted"]
        prov = {p.doc_type: p for p in (session.ctx.get("provenance") or [])}

        def _prov(doc_type):
            p = prov.get(doc_type)
            return (p.name if p else "", p.period if p else "", p.fingerprint if p else "")

        messages = [] if ex.get("available") else [session.ctx.get("rejected") or "Data unavailable"]
        ged_name, ged_period, ged_fp = _prov("GED")
        bud_name, bud_period, bud_fp = _prov("BUDGET")
        sources = (
            V.source_preview("GED", ged_name, ged_period, V.ged_columns(),
                             ex.get("ged_valid", []), len(ex.get("ged_quarantined", [])),
                             bool(ex.get("available")), messages, ged_fp),
            V.source_preview("Budget Tracker", bud_name, bud_period, V.budget_columns(),
                             ex.get("budget_valid", []), len(ex.get("budget_quarantined", [])),
                             bool(ex.get("available")), messages, bud_fp),
        )
        return V.VerificationPreview(available=bool(ex.get("available")),
                                     rejected_reason=session.ctx.get("rejected"), sources=sources)

    def extraction_review(self, session: ReviewSession, overrides=None):
        """ALL extracted records per provided source (target-product §9), for the review-before-verify
        tables, with the user's current corrections overlaid. Returns (records, omitted): `records` has
        one entry per extracted source with every accepted+quarantined row and its lineage; `omitted`
        names captured-but-not-extracted sources (e.g. an invoice). None before extraction exists."""
        from finsight.application.read_models import verification as V
        from finsight.domain.corrections import CORRECTABLE_FIELDS
        if session is None or session.ctx.get("extracted") is None:
            return None
        ex = session.ctx["extracted"]
        prov = {p.doc_type: p for p in (session.ctx.get("provenance") or [])}

        def _p(doc_type, attr, default=""):
            p = prov.get(doc_type)
            return getattr(p, attr) if p else default

        # Effective (non-reverted) corrections, keyed per document: (source_ref, field) -> (cur, orig).
        by_doc = {"GED": {}, "BUDGET": {}}
        for o in (overrides or []):
            if getattr(o, "reverted", False):
                continue
            by_doc.setdefault(o.document_type, {})[(o.source_ref, o.field)] = (o.current_value,
                                                                               o.original_value)

        avail = bool(ex.get("available"))
        records = [
            V.source_records("GED", "GED", _p("GED", "name"), _p("GED", "period"), V.ged_columns(),
                             ex.get("ged_valid", []), ex.get("ged_quarantined", []), avail,
                             overrides=by_doc.get("GED", {}), editable_fields=CORRECTABLE_FIELDS["GED"]),
            V.source_records("Budget Tracker", "BUDGET", _p("BUDGET", "name"), _p("BUDGET", "period"),
                             V.budget_columns(), ex.get("budget_valid", []),
                             ex.get("budget_quarantined", []), avail,
                             overrides=by_doc.get("BUDGET", {}),
                             editable_fields=CORRECTABLE_FIELDS["BUDGET"]),
        ]
        # An invoice, if captured, is NOT extracted (no invoice rules exist — §6/RED CARD). Name it as
        # an omitted source so the review never implies it was analyzed.
        omitted = []
        if "INVOICE" in prov:
            omitted.append(("Invoice", prov["INVOICE"].name,
                            "Captured for the record — not extracted or analyzed in this release."))
        return records, omitted

    # ---- Step 5: Verification (VERIFIED) — explicit human approval ----
    def verify(self, session: ReviewSession) -> ReviewCycle:
        cycle = self._require_cycle(session.cycle_id)
        ctx = session.ctx
        if ctx.get("extracted") is None:
            raise InvalidTransitionError("Process the uploaded data before verification.")
        if ctx.get("rejected"):
            raise ValidationRejectedError("Rejected or unavailable data cannot be verified.", ctx["rejected"])
        try:
            ctx["vds"] = self._e.build_verified(session.cycle_id, ctx["extracted"], approve=True)
        except PermissionError as e:
            raise ValidationRejectedError("This data cannot be verified.", str(e)) from e
        try:
            self._e.do_verified(cycle, ctx)
        except Exception as e:
            _log.error("verify failed cid=%s: %s", session.cycle_id, type(e).__name__, exc_info=True)
            raise PersistenceError("Could not record verification.", str(e)) from e
        _log.info("verified cid=%s", session.cycle_id)
        return cycle

    # ---- Step 6: Analysis (ANALYZED) — deterministic, gated on verification ----
    def analyze(self, session: ReviewSession) -> AnalysisResult:
        cycle = self._require_cycle(session.cycle_id)
        if not has_reached(cycle.state, CycleState.VERIFIED):
            raise VerificationRequiredError("Verify the data before running analysis.")
        ctx = session.ctx
        if ctx.get("vds") is None:
            raise VerificationRequiredError(
                "Re-select the source files and re-verify to run analysis in this session.")
        self._e.do_analyzed(cycle, ctx)
        run = self._e.run_repo.get_by_cycle(session.cycle_id) or {}
        _log.info("analyzed cid=%s findings=%s", session.cycle_id, run.get("finding_count", 0))
        return AnalysisResult(run.get("run_id", ""), run.get("config_version", ""),
                              run.get("input_fingerprint", ""), int(run.get("finding_count", 0)))

    # ---- Step 8: Leadership Summary (SUMMARIZED) ----
    def summarize(self, session: ReviewSession) -> SummaryView:
        cycle = self._require_cycle(session.cycle_id)
        if not has_reached(cycle.state, CycleState.ANALYZED):
            raise InvalidTransitionError("Run analysis before generating the leadership summary.")
        self._e.do_summarized(cycle, session.ctx)
        run = self._e.run_repo.get_by_cycle(session.cycle_id) or {}
        s = self._e.reporting.summary(cycle, self._e.finding_repo.list(session.cycle_id), run)
        return SummaryView(s["section"], s["period"], s["status_label"], s["finding_count"], s["budget_health_lines"])

    # ---- Step 9: Export (EXPORTED) ----
    def export(self, session: ReviewSession) -> ExportResult:
        cycle = self._require_cycle(session.cycle_id)
        if not has_reached(cycle.state, CycleState.SUMMARIZED):
            raise InvalidTransitionError("Generate the leadership summary before export.")
        ctx = session.ctx
        try:
            self._e.do_exported(cycle, ctx)
        except Exception as e:
            _log.error("export transition failed cid=%s: %s", session.cycle_id, type(e).__name__, exc_info=True)
            raise ExportError("Could not produce the export.", str(e)) from e
        content = ctx.get("export")
        if content is None:  # already exported in a prior session — rebuild deterministic content
            run = self._e.run_repo.get_by_cycle(session.cycle_id) or {}
            summary = self._e.reporting.summary(cycle, self._e.finding_repo.list(session.cycle_id), run)
            content = self._e.export.build(cycle, summary, run, data_as_of=self._e.clock.now())
        return ExportResult(content.get("period", ""), content, self._e.export.to_json(content))
