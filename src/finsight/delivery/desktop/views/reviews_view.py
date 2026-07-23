from __future__ import annotations
from PySide6.QtCore import Signal, QModelIndex
from PySide6.QtWidgets import QWidget, QVBoxLayout, QStackedWidget
from finsight.delivery.desktop.components import SectionHeader, DataTable, EmptyState
from finsight.delivery.desktop.models import ReviewsTableModel
from finsight.delivery.desktop.theme import tokens as t


class ReviewsView(QWidget):
    """Home: list persisted reviews. Selecting a row sets the active review; opening (Enter or
    double-click) navigates to the review workspace."""

    reviewActivated = Signal(str)  # cycle_id when a review is opened

    def __init__(self, controller, parent=None):
        super().__init__(parent)
        self._c = controller
        self._model = ReviewsTableModel()

        root = QVBoxLayout(self)
        root.setContentsMargins(t.SP_5, t.SP_5, t.SP_5, t.SP_5)
        root.setSpacing(t.SP_3)
        root.addWidget(SectionHeader("Reviews", "Select a review to open its workspace."))

        self._stack = QStackedWidget()
        self._table = DataTable()
        self._table.setModel(self._model)
        self._table.doubleClicked.connect(self._on_open)
        self._table.activated.connect(self._on_open)
        self._table.selectionModel().currentRowChanged.connect(self._on_current_changed)
        self._empty = EmptyState(
            "No reviews yet",
            "No review cycles have been created in this database.",
            "Reviews created through the FinSight workflow will appear here.",
        )
        self._stack.addWidget(self._table)
        self._stack.addWidget(self._empty)
        root.addWidget(self._stack, 1)

        self.refresh()

    def refresh(self) -> None:
        rows = self._c.reviews_with_status()
        self._model.set_rows(rows)
        self._stack.setCurrentWidget(self._table if rows else self._empty)
        if rows:
            self._table.selectRow(0)  # emits currentRowChanged -> sets active review

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
