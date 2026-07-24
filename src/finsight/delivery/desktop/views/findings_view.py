# Findings workspace (Phase 5.2): a practical reviewer surface over the deterministic findings —
# search, severity/account/state filters, stable header sorting, result counts, clear-filters, honest
# empty states, selection-preserving inspector, and deterministic CSV export. All filtering/sorting is
# pure and in-memory over already-loaded FindingView objects; no repository access, no AI, no mutation.
from __future__ import annotations
import os
from typing import List, Optional

from PySide6.QtCore import Qt, QModelIndex
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QStackedWidget, QSplitter, QLineEdit, QComboBox, QPushButton,
    QLabel, QFileDialog,
)
from finsight.delivery.desktop.components import SectionHeader, DataTable, DetailInspector
from finsight.delivery.desktop.components.severity import severity_text
from finsight.delivery.desktop.models import FindingsTableModel
from finsight.delivery.desktop import findings_filter as ff
from finsight.delivery.desktop.findings_export import findings_to_csv
from finsight.delivery.desktop.views.workflow_meta import rank, RANK
from finsight.delivery.desktop.theme import tokens as t

_COL_SORT_KEY = {0: "severity", 1: "account", 2: "finding", 3: "period", 4: "state"}
_ALL_ACCOUNTS = "All accounts"
_ALL_STATES = "All states"


class FindingsView(QWidget):
    """Read-only findings table + evidence inspector with a deterministic filter/sort toolbar."""

    def __init__(self, controller, parent=None):
        super().__init__(parent)
        self._c = controller
        self._model = FindingsTableModel()
        self._all: List = []            # every finding for the active review
        self._displayed: List = []      # filtered + sorted subset currently shown
        self._selected_id: Optional[str] = None
        self._sort_key = "severity"
        self._descending = True
        self._empty_code = "no_review"
        self._syncing = False

        root = QVBoxLayout(self)
        root.setContentsMargins(t.SP_5, t.SP_5, t.SP_5, t.SP_5)
        root.setSpacing(t.SP_3)
        self._header = SectionHeader("Findings", "")
        root.addWidget(self._header)
        root.addWidget(self._build_toolbar())

        self._stack = QStackedWidget()
        root.addWidget(self._stack, 1)

        split = QSplitter(Qt.Orientation.Horizontal)
        self._table = DataTable()
        self._table.setModel(self._model)
        self._table.selectionModel().currentRowChanged.connect(self._on_row)
        self._table.horizontalHeader().setSectionsClickable(True)
        self._table.horizontalHeader().sectionClicked.connect(self._on_sort_column)
        self._inspector = DetailInspector("Finding")
        split.addWidget(self._table)
        split.addWidget(self._inspector)
        split.setStretchFactor(0, 3)
        split.setStretchFactor(1, 2)
        split.setSizes([620, 360])
        self._stack.addWidget(split)
        self._stack.addWidget(self._build_empty())
        self.refresh()

    # --- construction ---
    def _build_toolbar(self) -> QWidget:
        bar = QWidget()
        lay = QVBoxLayout(bar)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(t.SP_2)

        row1 = QHBoxLayout()
        row1.setSpacing(t.SP_2)
        self._search = QLineEdit()
        self._search.setPlaceholderText("Search findings (account, rule, type, id…)")
        self._search.setClearButtonEnabled(True)
        self._search.textChanged.connect(self._recompute)
        row1.addWidget(self._search, 1)
        self._sev_btns = {}
        for label in ff.SEVERITY_ORDER:
            b = QPushButton(severity_text(label))     # glyph + label — never color alone
            b.setCheckable(True)
            b.setProperty("role", "secondary")
            b.toggled.connect(self._recompute)
            self._sev_btns[label] = b
            row1.addWidget(b)
        lay.addLayout(row1)

        row2 = QHBoxLayout()
        row2.setSpacing(t.SP_2)
        self._account = QComboBox()
        self._account.currentIndexChanged.connect(self._recompute)
        self._state = QComboBox()
        self._state.currentIndexChanged.connect(self._recompute)
        row2.addWidget(self._account)
        row2.addWidget(self._state)
        self._count = QLabel("")
        self._count.setProperty("role", "context")
        row2.addWidget(self._count)
        row2.addStretch(1)
        self._clear = QPushButton("Clear filters")
        self._clear.setProperty("role", "secondary")
        self._clear.clicked.connect(self.clear_filters)
        row2.addWidget(self._clear)
        self._export = QPushButton("Export findings…")
        self._export.setProperty("role", "primary")
        self._export.clicked.connect(self._on_export)
        row2.addWidget(self._export)
        lay.addLayout(row2)
        return bar

    def _build_empty(self) -> QWidget:
        wrap = QWidget()
        lay = QVBoxLayout(wrap)
        lay.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.setSpacing(t.SP_2)
        self._empty_title = QLabel("")
        self._empty_title.setProperty("role", "emptyTitle")
        self._empty_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(self._empty_title)
        self._empty_body = QLabel("")
        self._empty_body.setProperty("role", "empty")
        self._empty_body.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._empty_body.setWordWrap(True)
        lay.addWidget(self._empty_body)
        return wrap

    # --- data lifecycle ---
    def refresh(self) -> None:
        cid = self._c.active_review_id
        self._all = self._c.findings(cid) if cid else []
        self._sync_filter_options()
        self._recompute()

    def _sync_filter_options(self) -> None:
        self._syncing = True
        self._account.clear()
        self._account.addItem(_ALL_ACCOUNTS, None)
        for acc in ff.distinct_accounts(self._all):
            self._account.addItem(acc, acc)
        self._state.clear()
        self._state.addItem(_ALL_STATES, None)
        for st in ff.distinct_states(self._all):
            self._state.addItem(st, st)
        self._syncing = False

    def _query(self) -> ff.FindingsQuery:
        sev = frozenset(lbl for lbl, b in self._sev_btns.items() if b.isChecked())
        return ff.FindingsQuery(
            search=self._search.text(),
            severities=sev,
            account=self._account.currentData(),
            state=self._state.currentData(),
            sort_key=self._sort_key,
            descending=self._descending,
        )

    def _recompute(self, *_a) -> None:
        if self._syncing:
            return
        query = self._query()
        self._displayed = query.apply(self._all)
        self._model.set_rows(self._displayed)
        self._update_count(query)
        self._update_empty(query)
        self._restore_selection()
        self._export.setEnabled(bool(self._displayed))
        self._clear.setEnabled(query.is_filtered() or (self._sort_key, self._descending) != ("severity", True))

    def _update_count(self, query: ff.FindingsQuery) -> None:
        total = len(self._all)
        shown = len(self._displayed)
        self._count.setText(f"{shown} findings" if shown == total else f"{shown} of {total} findings")

    def _update_empty(self, query: ff.FindingsQuery) -> None:
        cid = self._c.active_review_id
        if not cid:
            self._empty_code = "no_review"
            self._set_empty("No review selected", "Choose a review to see its findings.")
        elif not self._all:
            state = self._c.workflow_state(cid)
            if rank(state) < RANK["Analyzed"]:
                self._empty_code = "not_ready"
                self._set_empty("Findings not available yet",
                                "Findings appear after the review's analysis step has run.")
            else:
                self._empty_code = "no_findings"
                self._set_empty("No findings",
                                "No findings were generated for this review.")
        elif not self._displayed:
            self._empty_code = "no_matches"
            self._set_empty("No matches", "No findings match the current filters.")
        else:
            self._empty_code = ""
            self._stack.setCurrentIndex(0)
            return
        self._inspector.show_placeholder("Select a finding to see its evidence.")
        self._stack.setCurrentIndex(1)

    def _set_empty(self, title: str, body: str) -> None:
        self._empty_title.setText(title)
        self._empty_body.setText(body)

    def _restore_selection(self) -> None:
        if not self._displayed:
            self._selected_id = None
            return
        target = 0
        if self._selected_id is not None:
            for i, f in enumerate(self._displayed):
                if f.id == self._selected_id:
                    target = i
                    break
        self._table.selectRow(target)   # emits currentRowChanged -> _on_row

    # --- filters/sort (public seams) ---
    def set_search_text(self, text: str) -> None:
        self._search.setText(text)

    def set_severity_filter(self, labels) -> None:
        wanted = set(labels or [])
        self._syncing = True
        for lbl, b in self._sev_btns.items():
            b.setChecked(lbl in wanted)
        self._syncing = False
        self._recompute()

    def set_account_filter(self, account: Optional[str]) -> None:
        idx = self._account.findData(account) if account is not None else 0
        self._account.setCurrentIndex(max(0, idx))

    def set_state_filter(self, state: Optional[str]) -> None:
        idx = self._state.findData(state) if state is not None else 0
        self._state.setCurrentIndex(max(0, idx))

    def clear_filters(self) -> None:
        self._syncing = True
        self._search.clear()
        for b in self._sev_btns.values():
            b.setChecked(False)
        self._account.setCurrentIndex(0)
        self._state.setCurrentIndex(0)
        self._sort_key, self._descending = "severity", True
        self._table.horizontalHeader().setSortIndicator(0, Qt.SortOrder.DescendingOrder)
        self._syncing = False
        self._recompute()

    def _on_sort_column(self, col: int) -> None:
        key = _COL_SORT_KEY.get(col)
        if key is None:
            return
        if key == self._sort_key:
            self._descending = not self._descending
        else:
            self._sort_key = key
            self._descending = (key == "severity")   # severity defaults desc; others asc
        order = Qt.SortOrder.DescendingOrder if self._descending else Qt.SortOrder.AscendingOrder
        self._table.horizontalHeader().setSortIndicator(col, order)
        self._recompute()

    # --- selection / inspector ---
    def selected_finding(self):
        idx = self._table.currentIndex()
        return self._model.finding_at(idx.row()) if idx.isValid() else None

    def _on_row(self, current: QModelIndex, _prev: QModelIndex) -> None:
        if not current.isValid():
            self._selected_id = None
            return
        f = self._model.finding_at(current.row())
        if f is None:
            return
        self._selected_id = f.id
        self._inspector.begin(f"Finding {f.id}")
        self._inspector.add_section("Finding")
        self._inspector.add_row("Account", f.account)
        self._inspector.add_row("Rule", f.rule_id)
        self._inspector.add_row("Type", f.finding_type)
        self._inspector.add_row("Severity", severity_text(f.severity))
        self._inspector.add_row("State", f.state)
        self._inspector.add_row("Period", f.period)
        self._inspector.add_section("Evidence")
        if f.evidence:
            for k, v in f.evidence.items():
                self._inspector.add_row(k, str(v), mono=True)
        else:
            self._inspector.add_row("(none)", "")
        self._inspector.add_section("Source references")
        if f.source_refs:
            for ref in f.source_refs:
                self._inspector.add_row("ref", str(ref), mono=True)
        else:
            self._inspector.add_row("(none)", "")

    # --- export ---
    def _on_export(self) -> None:
        if not self._displayed:
            return
        cid = self._c.active_review_id or "review"
        default = f"{cid}-findings.csv"
        path, _ = QFileDialog.getSaveFileName(self, "Export findings", default, "CSV (*.csv)")
        if not path:
            return
        try:
            with open(path, "w", encoding="utf-8", newline="") as fh:
                fh.write(findings_to_csv(self._displayed))
        except OSError as exc:
            self._count.setText(f"Could not write the export file: {exc}")
            return
        total = len(self._all)
        shown = len(self._displayed)
        scope = f"{shown} finding(s)" if shown == total else f"{shown} of {total} (current filter)"
        self._count.setText(f"Exported {scope} to {os.path.basename(path)}")

    # --- public seams ---
    def displayed_finding_ids(self) -> List[str]:
        return [f.id for f in self._displayed]

    def filtered_count(self) -> int:
        return len(self._displayed)

    def total_count(self) -> int:
        return len(self._all)

    def active_sort(self):
        return ff.active_sort(self._query())

    def export_action_enabled(self) -> bool:
        return self._export.isEnabled()

    def displayed_empty_state(self) -> str:
        return self._empty_code

    def selected_finding_id(self) -> Optional[str]:
        return self._selected_id if self._empty_code == "" else None
