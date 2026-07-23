from __future__ import annotations
from typing import Callable, List, Optional
from PySide6.QtCore import QObject, Signal
from finsight.application.read_models.views import (
    ReviewStatusView, FindingView, AuditEventView, SummaryView,
)
from finsight.application.workflow import UploadResult, ValidationResult, AnalysisResult, ExportResult
from finsight.delivery.desktop.async_worker import run_async


class AppController(QObject):
    """Coordinates the UI with the read-only query services and the review workflow command service,
    and holds the active-review selection. The UI talks only to this controller — never to
    repositories, SQL, the rules engine, or the database."""

    activeReviewChanged = Signal(str)   # cycle_id, or "" when cleared
    reviewsChanged = Signal()           # the set of reviews changed (a review was created)
    workflowChanged = Signal(str)       # a transition occurred for cycle_id
    processingChanged = Signal(bool)    # processing started (True) / finished (False)

    def __init__(self, services, parent=None):
        super().__init__(parent)
        self._s = services
        self._active: Optional[str] = None

    # --- active review ---
    @property
    def active_review_id(self) -> Optional[str]:
        return self._active

    def select_review(self, cycle_id: str) -> None:
        if cycle_id == self._active:
            return
        self._active = cycle_id
        self.activeReviewChanged.emit(cycle_id or "")

    def clear_review(self) -> None:
        self._active = None
        self.activeReviewChanged.emit("")

    def begin_new_review(self) -> None:
        """Enter 'create a new review' mode (no active review)."""
        self.clear_review()

    # --- read-only queries ---
    def reviews_with_status(self) -> List[ReviewStatusView]:
        return self._s.reviews.list_with_status()

    def review_status(self, cycle_id: str) -> Optional[ReviewStatusView]:
        return self._s.reviews.get_status(cycle_id)

    def summary(self, cycle_id: str) -> Optional[SummaryView]:
        return self._s.summary.for_cycle(cycle_id)

    def findings(self, cycle_id: str) -> List[FindingView]:
        return self._s.findings.list_for_cycle(cycle_id)

    def audit_timeline(self, cycle_id: str) -> List[AuditEventView]:
        return self._s.audit.timeline(cycle_id)

    def workflow_state(self, cycle_id: str) -> Optional[str]:
        return self._s.workflow.state(cycle_id)

    def has_session_context(self, cycle_id: str) -> bool:
        return self._s.workflow.has_session_context(cycle_id)

    def validation_snapshot(self, cycle_id: str):
        return self._s.workflow.validation_snapshot(cycle_id)

    # --- workflow commands (may raise finsight.application.errors.FinsightAppError) ---
    def create_review(self, cycle_id: str, month: str, year: str):
        cycle = self._s.workflow.create_review(cycle_id, month, year)
        self._active = cycle.cycle_id
        self.activeReviewChanged.emit(cycle.cycle_id)
        self.reviewsChanged.emit()
        self.workflowChanged.emit(cycle.cycle_id)
        return cycle

    def upload(self, cycle_id: str, ged_path: str, budget_path: str) -> UploadResult:
        result = self._s.workflow.upload(cycle_id, ged_path, budget_path)
        self.workflowChanged.emit(cycle_id)
        return result

    def process_async(self, cycle_id: str, on_result: Callable[[ValidationResult], None],
                      on_error: Callable[[Exception], None]) -> None:
        """Run the heavy extraction off the UI thread; persist the transition on the UI thread
        (SQLite connections are thread-bound)."""
        self.processingChanged.emit(True)

        def work():
            self._s.workflow.prepare_extraction(cycle_id)   # extraction only; no database access

        def done(_ignored):
            try:
                result = self._s.workflow.finalize_processing(cycle_id)   # DB write on the UI thread
            except Exception as exc:
                self.processingChanged.emit(False)
                on_error(exc)
                return
            self.processingChanged.emit(False)
            self.workflowChanged.emit(cycle_id)
            on_result(result)

        def failed(exc):
            self.processingChanged.emit(False)
            on_error(exc)

        run_async(work, done, failed)

    def verify(self, cycle_id: str) -> None:
        self._s.workflow.verify(cycle_id)
        self.workflowChanged.emit(cycle_id)

    def analyze(self, cycle_id: str) -> AnalysisResult:
        result = self._s.workflow.analyze(cycle_id)
        self.workflowChanged.emit(cycle_id)
        return result

    def summarize(self, cycle_id: str) -> SummaryView:
        result = self._s.workflow.summarize(cycle_id)
        self.workflowChanged.emit(cycle_id)
        return result

    def export(self, cycle_id: str) -> ExportResult:
        result = self._s.workflow.export(cycle_id)
        self.workflowChanged.emit(cycle_id)
        return result
