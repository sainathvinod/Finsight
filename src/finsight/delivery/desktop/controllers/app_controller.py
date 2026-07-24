from __future__ import annotations
from typing import Callable, List, Optional
from PySide6.QtCore import QObject, Signal
from finsight.application.read_models.views import (
    ReviewStatusView, FindingView, AuditEventView, SummaryView,
)
from finsight.application.workflow import UploadResult, ValidationResult, AnalysisResult, ExportResult
from finsight.application.review_session import ReviewSession
from finsight.application.ai.ask_fin_contracts import AskFinRequest
from finsight.delivery.desktop.async_worker import run_async
from finsight.diagnostics import get_logger

_log = get_logger("ui.controller")

# Single-user local desktop convention (no authentication/user-management in this application).
DEFAULT_USER_ID = "local-user"


class AppController(QObject):
    """Coordinates the UI with the read-only query services and the stateless review workflow
    command service. The controller OWNS the active ReviewSession (transient working context); the
    UI never touches repositories, SQL, the rules engine, or the database, and performs no
    financial logic."""

    activeReviewChanged = Signal(str)   # cycle_id, or "" when cleared
    reviewsChanged = Signal()           # a review was created
    workflowChanged = Signal(str)       # a transition occurred for cycle_id
    processingChanged = Signal(bool)    # processing started (True) / finished (False)

    def __init__(self, services, parent=None, ask_fin_backend=None):
        super().__init__(parent)
        self._s = services
        self._active: Optional[str] = None
        self._session: Optional[ReviewSession] = None
        # Ask Fin backend runs the whole AskFinService pipeline OFF the UI thread on a worker-local
        # SQLite connection (injected; None disables Ask Fin). The controller never constructs a
        # provider or touches the AI stack directly.
        self._ask_fin = ask_fin_backend
        self._user_id = DEFAULT_USER_ID

    # --- active review + owned session ---
    @property
    def active_review_id(self) -> Optional[str]:
        return self._active

    def _session_for(self, cycle_id: str) -> ReviewSession:
        if self._session is None or self._session.cycle_id != cycle_id:
            self._session = ReviewSession(cycle_id)
            self._active = cycle_id
        return self._session

    def select_review(self, cycle_id: str) -> None:
        if cycle_id == self._active:
            return
        self._active = cycle_id
        self._session = ReviewSession(cycle_id) if cycle_id else None
        self.activeReviewChanged.emit(cycle_id or "")

    def clear_review(self) -> None:
        self._active = None
        self._session = None
        self.activeReviewChanged.emit("")

    def begin_new_review(self) -> None:
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

    def portfolio(self):
        """Deterministic cross-review portfolio summary (Phase 5.3). Built on demand from the existing
        read-only query services — no caching, so it always reflects current persisted state."""
        from finsight.application.read_models.portfolio import PortfolioQueryService
        return PortfolioQueryService(self._s.reviews, self._s.findings).summary()

    def has_session_context(self, cycle_id: str) -> bool:
        s = self._session
        return bool(s and s.cycle_id == cycle_id and s.has_files())

    def validation_snapshot(self, cycle_id: str):
        s = self._session
        return self._s.workflow.validation_snapshot(s) if (s and s.cycle_id == cycle_id) else None

    # --- workflow commands (may raise finsight.application.errors.FinsightAppError) ---
    def create_review(self, cycle_id: str, month: str, year: str):
        cycle = self._s.workflow.create_review(cycle_id, month, year)
        self._active = cycle.cycle_id
        self._session = ReviewSession(cycle.cycle_id)
        self.activeReviewChanged.emit(cycle.cycle_id)
        self.reviewsChanged.emit()
        self.workflowChanged.emit(cycle.cycle_id)
        return cycle

    def upload(self, cycle_id: str, ged_path: str, budget_path: str) -> UploadResult:
        result = self._s.workflow.upload(self._session_for(cycle_id), ged_path, budget_path)
        self.workflowChanged.emit(cycle_id)
        return result

    def process_async(self, cycle_id: str, on_result: Callable[[ValidationResult], None],
                      on_error: Callable[[Exception], None]) -> None:
        """Heavy extraction off the UI thread; DB transition on the UI thread (SQLite is thread-bound)."""
        session = self._session_for(cycle_id)
        self.processingChanged.emit(True)

        def work():
            self._s.workflow.prepare_extraction(session)

        def done(_ignored):
            try:
                result = self._s.workflow.finalize_processing(session)
            except Exception as exc:
                self.processingChanged.emit(False)
                on_error(exc)
                return
            self.processingChanged.emit(False)
            self.workflowChanged.emit(cycle_id)
            on_result(result)

        def failed(exc):
            self.processingChanged.emit(False)
            _log.error("processing worker failed cid=%s: %s", cycle_id, type(exc).__name__, exc_info=exc)
            on_error(exc)

        run_async(work, done, failed)

    def verify(self, cycle_id: str) -> None:
        self._s.workflow.verify(self._session_for(cycle_id))
        self.workflowChanged.emit(cycle_id)

    def analyze(self, cycle_id: str) -> AnalysisResult:
        result = self._s.workflow.analyze(self._session_for(cycle_id))
        self.workflowChanged.emit(cycle_id)
        return result

    def summarize(self, cycle_id: str) -> SummaryView:
        result = self._s.workflow.summarize(self._session_for(cycle_id))
        self.workflowChanged.emit(cycle_id)
        return result

    def export(self, cycle_id: str) -> ExportResult:
        result = self._s.workflow.export(self._session_for(cycle_id))
        self.workflowChanged.emit(cycle_id)
        return result

    # --- Ask Fin (explanation-only; the whole pipeline runs off the UI thread) ---
    def ask_fin_available(self) -> bool:
        return self._ask_fin is not None

    def ask_fin_provider_status_async(self, on_result: Callable, on_error: Callable) -> None:
        """Fetch bounded provider status off the UI thread (DB-free)."""
        if self._ask_fin is None:
            on_error(RuntimeError("ask_fin_unavailable"))
            return
        run_async(self._ask_fin.provider_status, on_result, on_error)

    def ask_fin_explain_async(self, question: str, on_result: Callable, on_error: Callable, *,
                              audience: Optional[str] = None,
                              answer_detail: Optional[str] = None) -> None:
        """Run the full AskFinService pipeline off the UI thread for the CURRENT review only. The
        caller supplies only the question + optional formatting overrides; grounding/memory/history
        are never injected here."""
        if self._ask_fin is None:
            on_error(RuntimeError("ask_fin_unavailable"))
            return
        request = AskFinRequest(user_id=self._user_id, cycle_id=self._active or "", question=question,
                                audience=audience, answer_detail=answer_detail)
        run_async(lambda: self._ask_fin.explain(request), on_result, on_error)
