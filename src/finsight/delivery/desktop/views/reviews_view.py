# Implements:
#   Feature: F-01-01 — Monthly Review Cycle Workspace (incl. abandonment/inactivity, DEC-035)
#   ADRs: ADR-014 (abandonment + inactivity reminders); ADR-011 §9 (published = trusted status)
#         ADR-013 (Ollama-independent core)
#   UI surface: Reviews (home) screen.
#
# Product purpose:
#   Lists persisted reviews and lets a reviewer select/open one. Surfaces each selected review's
#   lifecycle: a deterministic 30/60-day inactivity reminder and an explicit, reversible
#   abandon / resume action.
#
# Trust / lifecycle constraints:
#   - Abandonment is explicit + non-destructive (routed through the controller/service); the reminder
#     is informational and NEVER changes review state automatically. No AI dependency.
from __future__ import annotations
from PySide6.QtCore import Signal, QModelIndex
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QStackedWidget, QPushButton, QLabel
from finsight.delivery.desktop.components import SectionHeader, DataTable
from finsight.delivery.desktop.components.first_run import build_first_run_card, FIRST_RUN_LEAD
from finsight.delivery.desktop.models import ReviewsTableModel
from finsight.delivery.desktop.theme import tokens as t


class ReviewsView(QWidget):
    """Home: list persisted reviews, or a first-run welcome when the database is empty. Selecting a
    row sets the active review; opening navigates to the review. 'Create review' starts the workflow.
    A lifecycle bar shows the selected review's inactivity reminder + abandon/resume (ADR-014)."""

    reviewActivated = Signal(str)   # cycle_id when a review is opened
    newReviewRequested = Signal()   # user asked to create a new review

    def __init__(self, controller, parent=None):
        super().__init__(parent)
        self._c = controller
        self._model = ReviewsTableModel()

        root = QVBoxLayout(self)
        root.setContentsMargins(t.SP_5, t.SP_5, t.SP_5, t.SP_5)
        root.setSpacing(t.SP_3)
        header_row = QHBoxLayout()
        header_row.addWidget(SectionHeader("Reviews", "Select a review to open it."), 1)
        self._new_btn = QPushButton("New review")
        self._new_btn.setProperty("role", "secondary")
        self._new_btn.clicked.connect(self.newReviewRequested.emit)
        header_row.addWidget(self._new_btn)
        root.addLayout(header_row)

        self._stack = QStackedWidget()
        self._table = DataTable()
        self._table.setModel(self._model)
        self._table.doubleClicked.connect(self._on_open)
        self._table.activated.connect(self._on_open)
        self._table.selectionModel().currentRowChanged.connect(self._on_current_changed)
        self._stack.addWidget(self._table)
        first_run, self._first_run_btn = build_first_run_card(self.newReviewRequested.emit)
        self._stack.addWidget(first_run)
        root.addWidget(self._stack, 1)

        # Lifecycle bar (ADR-014): inactivity reminder + explicit abandon/resume for the selected review.
        self._lifecycle_row = QHBoxLayout()
        self._lifecycle_msg = QLabel("")
        self._lifecycle_msg.setProperty("role", "kvVal")
        self._lifecycle_msg.setWordWrap(True)
        self._lifecycle_row.addWidget(self._lifecycle_msg, 1)
        self._lifecycle_btn = QPushButton("")
        self._lifecycle_btn.setProperty("role", "secondary")
        self._lifecycle_btn.clicked.connect(self._on_lifecycle_action)
        self._lifecycle_row.addWidget(self._lifecycle_btn)
        root.addLayout(self._lifecycle_row)

        controller.reviewDispositionChanged.connect(lambda _c: self._refresh_lifecycle())
        self.refresh()

    def _refresh_lifecycle(self) -> None:
        cid = self.selected_review_id()
        if not cid:
            self._lifecycle_msg.setText("")
            self._lifecycle_btn.setText("")
            self._lifecycle_btn.setVisible(False)
            return
        status = self._c.review_lifecycle_status(cid)
        abandoned = status.disposition.value == "Abandoned"
        # Message: abandoned state is explicit; otherwise the (possibly empty) inactivity reminder.
        self._lifecycle_msg.setText("This review is abandoned. Resume it to continue."
                                    if abandoned else status.message)
        self._lifecycle_btn.setText("Resume review" if abandoned else "Mark abandoned")
        self._lifecycle_btn.setVisible(True)

    def _on_lifecycle_action(self) -> None:
        cid = self.selected_review_id()
        if not cid:
            return
        status = self._c.review_lifecycle_status(cid)
        if status.disposition.value == "Abandoned":
            self._c.resume_abandoned_review(cid)
        else:
            self._c.abandon_review(cid)     # explicit, audited, non-destructive; reversible

    def refresh(self) -> None:
        rows = self._c.reviews_with_status()
        active = self._c.active_review_id
        # Rebuilding the model must not emit a destructive active-review change (Phase 6.4a).
        sm = self._table.selectionModel()
        sm.blockSignals(True)
        self._model.set_rows(rows)
        sm.blockSignals(False)
        self._stack.setCurrentIndex(0 if rows else 1)   # table, else first-run welcome
        if not rows:
            return
        # Reselect the ACTIVE review by cycle_id (not row 0). Only default to the first row when no
        # review is active. Selecting the active review is a no-op in the controller, so navigating
        # here never silently changes the active review.
        target = self._row_for_cycle(active) if active else 0
        if target is None:
            self._refresh_lifecycle()
            return                              # active review not in the list — leave it unchanged
        self._table.selectRow(target)           # currentRowChanged -> _sync_selection (no-op if active)
        self._refresh_lifecycle()

    def _row_for_cycle(self, cycle_id):
        if not cycle_id:
            return None
        for r in range(self._model.rowCount()):
            item = self._model.review_at(r)
            if item is not None and item.cycle_id == cycle_id:
                return r
        return None

    # --- public seams ---
    def selected_review_id(self):
        idx = self._table.currentIndex()
        item = self._model.review_at(idx.row()) if idx.isValid() else None
        return item.cycle_id if item is not None else None

    def refresh_preserves_active_review(self) -> bool:
        """True iff the current table selection matches the controller's active review (or there is
        no active review). Used to verify navigation is non-destructive."""
        active = self._c.active_review_id
        return active is None or self.selected_review_id() == active

    def first_run_message(self) -> str:
        """The welcome guidance shown on an empty database ('' when reviews exist)."""
        return FIRST_RUN_LEAD if self._stack.currentIndex() == 1 else ""

    def primary_action_text(self) -> str:
        return self._first_run_btn.text()

    def lifecycle_message(self) -> str:
        """The lifecycle bar text for the selected review (inactivity reminder or abandoned notice)."""
        return self._lifecycle_msg.text()

    def lifecycle_action_text(self) -> str:
        """'Mark abandoned' / 'Resume review' / '' — the abandon/resume affordance label."""
        return self._lifecycle_btn.text()

    def _on_current_changed(self, current: QModelIndex, _prev: QModelIndex) -> None:
        if current.isValid():
            self._sync_selection(current.row())
            self._refresh_lifecycle()

    def _sync_selection(self, row: int) -> None:
        item = self._model.review_at(row)
        if item is not None:
            self._c.select_review(item.cycle_id)

    def _on_open(self, index: QModelIndex) -> None:
        item = self._model.review_at(index.row())
        if item is not None:
            self._c.select_review(item.cycle_id)
            self.reviewActivated.emit(item.cycle_id)
