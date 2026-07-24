from __future__ import annotations
from PySide6.QtCore import Signal, QModelIndex
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QStackedWidget, QPushButton
from finsight.delivery.desktop.components import SectionHeader, DataTable
from finsight.delivery.desktop.components.first_run import build_first_run_card, FIRST_RUN_LEAD
from finsight.delivery.desktop.models import ReviewsTableModel
from finsight.delivery.desktop.theme import tokens as t


class ReviewsView(QWidget):
    """Home: list persisted reviews, or a first-run welcome when the database is empty. Selecting a
    row sets the active review; opening navigates to the review. 'Create review' starts the workflow."""

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

        self.refresh()

    def refresh(self) -> None:
        rows = self._c.reviews_with_status()
        self._model.set_rows(rows)
        self._stack.setCurrentIndex(0 if rows else 1)   # table, else first-run welcome
        if rows:
            self._table.selectRow(0)  # emits currentRowChanged -> sets active review

    # --- public seams ---
    def first_run_message(self) -> str:
        """The welcome guidance shown on an empty database ('' when reviews exist)."""
        return FIRST_RUN_LEAD if self._stack.currentIndex() == 1 else ""

    def primary_action_text(self) -> str:
        return self._first_run_btn.text()

    def _on_current_changed(self, current: QModelIndex, _prev: QModelIndex) -> None:
        if current.isValid():
            self._sync_selection(current.row())

    def _sync_selection(self, row: int) -> None:
        item = self._model.review_at(row)
        if item is not None:
            self._c.select_review(item.cycle_id)

    def _on_open(self, index: QModelIndex) -> None:
        item = self._model.review_at(index.row())
        if item is not None:
            self._c.select_review(item.cycle_id)
            self.reviewActivated.emit(item.cycle_id)
