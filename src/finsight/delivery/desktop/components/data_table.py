from __future__ import annotations
from PySide6.QtCore import Qt, QAbstractItemModel
from PySide6.QtWidgets import QTableView, QAbstractItemView, QHeaderView
from finsight.delivery.desktop.theme import tokens as t


class DataTable(QTableView):
    """A dense, readable, keyboard-navigable read-only table. Row selection, sortable headers."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.setAlternatingRowColors(True)
        self.setSortingEnabled(True)
        self.setWordWrap(False)
        self.setShowGrid(False)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setTabKeyNavigation(True)
        self.verticalHeader().setVisible(False)
        self.verticalHeader().setDefaultSectionSize(t.ROW_H)
        hh = self.horizontalHeader()
        hh.setHighlightSections(False)
        hh.setStretchLastSection(True)
        hh.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)

    def set_model(self, model: QAbstractItemModel) -> None:
        self.setModel(model)
        self.resizeColumnsToContents()
        if model.rowCount() > 0:
            self.selectRow(0)
