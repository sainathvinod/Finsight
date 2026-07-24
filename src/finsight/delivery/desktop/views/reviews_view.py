from __future__ import annotations
from PySide6.QtCore import Qt, Signal, QModelIndex
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QStackedWidget, QPushButton, QLabel
from finsight.delivery.desktop.components import SectionHeader, DataTable
from finsight.delivery.desktop.models import ReviewsTableModel
from finsight.delivery.desktop.theme import tokens as t

# Concise, professional first-run guidance (not a marketing page).
_FIRST_RUN_TITLE = "Welcome to FinSight"
_FIRST_RUN_LEAD = ("FinSight runs a monthly financial review end to end: upload the source workbooks, "
                   "verify the extracted data, run the deterministic analysis, review findings, and "
                   "export the package — with a complete audit trail throughout.")
_FIRST_RUN_POINTS = [
    "Lifecycle:  Create → Upload → Verify → Analyze → Findings → Summary → Export.",
    "Your source files are never modified — FinSight only reads them.",
    "Deterministic analysis is the source of truth; every finding traces to a rule and its inputs.",
    "Ask Fin explains verified results — it never creates findings, amounts, or decisions.",
]


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
        self._stack.addWidget(self._build_first_run())
        root.addWidget(self._stack, 1)

        self.refresh()

    def _build_first_run(self) -> QWidget:
        wrap = QWidget()
        outer = QVBoxLayout(wrap)
        outer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card = QWidget()
        card.setProperty("role", "card")
        card.setMaximumWidth(640)                     # bounded width — no giant empty canvas
        lay = QVBoxLayout(card)
        lay.setContentsMargins(t.SP_6, t.SP_6, t.SP_6, t.SP_6)
        lay.setSpacing(t.SP_3)
        title = QLabel(_FIRST_RUN_TITLE)
        title.setProperty("role", "sectionHeader")
        lay.addWidget(title)
        lead = QLabel(_FIRST_RUN_LEAD)
        lead.setProperty("role", "kvVal")
        lead.setWordWrap(True)
        lay.addWidget(lead)
        for point in _FIRST_RUN_POINTS:
            p = QLabel("•  " + point)
            p.setProperty("role", "context")
            p.setWordWrap(True)
            lay.addWidget(p)
        row = QHBoxLayout()
        row.addStretch(1)
        self._first_run_btn = QPushButton("Create first review")
        self._first_run_btn.setProperty("role", "primary")
        self._first_run_btn.clicked.connect(self.newReviewRequested.emit)
        row.addWidget(self._first_run_btn)
        lay.addLayout(row)
        outer.addWidget(card)
        return wrap

    def refresh(self) -> None:
        rows = self._c.reviews_with_status()
        self._model.set_rows(rows)
        self._stack.setCurrentIndex(0 if rows else 1)   # table, else first-run welcome
        if rows:
            self._table.selectRow(0)  # emits currentRowChanged -> sets active review

    # --- public seams ---
    def first_run_message(self) -> str:
        """The welcome guidance shown on an empty database ('' when reviews exist)."""
        return _FIRST_RUN_LEAD if self._stack.currentIndex() == 1 else ""

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
