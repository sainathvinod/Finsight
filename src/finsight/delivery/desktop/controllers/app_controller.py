from __future__ import annotations
from typing import List, Optional
from PySide6.QtCore import QObject, Signal
from finsight.application.read_models.views import (
    ReviewStatusView, FindingView, AuditEventView, SummaryView,
)


class AppController(QObject):
    """Coordinates the UI with the read-only application query services and holds the active-review
    selection. The UI talks only to this controller and the services it wraps — never to
    repositories, SQL, or the deterministic engine."""

    activeReviewChanged = Signal(str)  # cycle_id, or "" when cleared

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

    # --- read-only queries (delegate to services) ---
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
