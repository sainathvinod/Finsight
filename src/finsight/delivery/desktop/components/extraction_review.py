# Implements:
#   Feature: F-01-09 (review extracted data before verification); target-product §9
#   Requirements: FR-016, FR-027 (present extracted records with lineage before analysis)
#   UI surface: Verification step — per-source extraction review.
#
# Product purpose:
#   The per-source extraction review (§9): one tab per provided source (GED, Budget), each showing
#   EVERY extracted record — accepted and quarantined — with its lineage (the `source` cell = file!row),
#   plus per-tab search and sortable, resizable columns. Row status is shown as text ("Accepted" /
#   "Quarantined"), never by color alone (NFR-025). Captured-but-not-extracted sources (an invoice) are
#   named below the tabs so the review never implies they were analyzed.
from __future__ import annotations
from PySide6.QtCore import Qt, QSortFilterProxyModel
from PySide6.QtGui import QStandardItemModel, QStandardItem
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QTabWidget)
from finsight.delivery.desktop.components.data_table import DataTable
from finsight.delivery.desktop.theme import tokens as t


class _SourceTab(QWidget):
    def __init__(self, records, parent=None):
        super().__init__(parent)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(t.SP_2, t.SP_2, t.SP_2, t.SP_2)
        lay.setSpacing(t.SP_2)

        top = QHBoxLayout()
        self._count = QLabel()
        self._count.setProperty("role", "context")
        top.addWidget(self._count)
        top.addStretch(1)
        self._search = QLineEdit()
        self._search.setPlaceholderText("Search records…")
        self._search.setClearButtonEnabled(True)
        self._search.setMaximumWidth(260)
        top.addWidget(self._search)
        lay.addLayout(top)

        self._model = QStandardItemModel(self)
        self._proxy = QSortFilterProxyModel(self)
        self._proxy.setSourceModel(self._model)
        self._proxy.setFilterKeyColumn(-1)                     # search across all columns
        self._proxy.setFilterCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self._table = DataTable()
        self._search.textChanged.connect(self._proxy.setFilterFixedString)
        self._search.textChanged.connect(lambda _t: self._update_count())
        lay.addWidget(self._table, 1)

        self.set_records(records)

    def set_records(self, records) -> None:
        self._records = records
        self._model.clear()
        self._model.setHorizontalHeaderLabels([c.replace("_", " ").title() for c in records.columns])
        for row in records.rows:
            self._model.appendRow([_cell(v) for v in row])
        self._table.set_model(self._proxy)
        self._update_count()

    def _update_count(self) -> None:
        shown = self._proxy.rowCount()
        total = self._model.rowCount()
        suffix = "" if shown == total else f" ({shown} shown)"
        self._count.setText(
            f"{self._records.accepted_rows} accepted · {self._records.quarantined_rows} quarantined · "
            f"{total} record(s){suffix}")

    # --- seams (stable for tests) ---
    def total_rows(self) -> int:
        return self._model.rowCount()

    def visible_rows(self) -> int:
        return self._proxy.rowCount()

    def set_filter(self, text: str) -> None:
        self._search.setText(text)


def _cell(value) -> QStandardItem:
    item = QStandardItem(str(value))
    item.setEditable(False)
    return item


class ExtractionReview(QWidget):
    """Per-source extraction review (§9): a tab per provided source + an omitted-sources note."""

    def __init__(self, parent=None):
        super().__init__(parent)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(t.SP_2)
        self._tabs = QTabWidget()
        lay.addWidget(self._tabs)
        self._omitted = QLabel()
        self._omitted.setProperty("role", "context")
        self._omitted.setWordWrap(True)
        self._omitted.setVisible(False)
        lay.addWidget(self._omitted)
        self._by_name = {}

    def set_data(self, records, omitted=()) -> None:
        self._tabs.clear()
        self._by_name = {}
        for rec in records or ():
            tab = _SourceTab(rec)
            self._by_name[rec.source_type] = tab
            self._tabs.addTab(tab, f"{rec.source_type}  ({rec.accepted_rows + rec.quarantined_rows})")
        if omitted:
            lines = [f"Not extracted: {name} — {note}" for (_st, name, note) in omitted]
            self._omitted.setText("  ".join(lines))
            self._omitted.setVisible(True)
        else:
            self._omitted.setVisible(False)

    # --- seams (stable for tests) ---
    def source_names(self):
        return list(self._by_name.keys())

    def tab(self, source_type: str):
        return self._by_name.get(source_type)
