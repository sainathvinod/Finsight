# Implements:
#   Feature: F-01-09 (review + correct extracted data before verification); target-product §9-§11
#   Requirements: FR-016, FR-027 (present records + lineage); FR-028/029, NFR-056 (correct values)
#   UI surface: Verification step — per-source extraction review with in-place correction.
#
# Product purpose:
#   The per-source extraction review (§9) AND the correction surface (§10-11). One tab per provided
#   source (GED, Budget), each showing EVERY extracted record with its lineage (source cell = file!row),
#   per-tab search, and sortable/resizable columns. Before verification, correctable cells on accepted
#   rows are editable in place; a corrected cell is marked with a ✎ glyph + bold + a tooltip showing the
#   ORIGINAL value (distinguishable WITHOUT relying on color — NFR-025), and can be reverted from its
#   context menu. Row status is text ("Accepted" / "Quarantined"), never color alone. Captured-but-not-
#   extracted sources (an invoice) are named below the tabs so the review never implies they were run.
#
# Trust: this widget only emits intent (correctionEdited / revertRequested); the panel routes it to the
#   deterministic CorrectionService. No storage, no financial logic, no AI here.
from __future__ import annotations
from PySide6.QtCore import Qt, QSortFilterProxyModel, Signal
from PySide6.QtGui import QStandardItemModel, QStandardItem, QFont
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QTabWidget,
                               QAbstractItemView, QMenu)
from finsight.delivery.desktop.components.data_table import DataTable
from finsight.delivery.desktop.theme import tokens as t

_CORRECTED_GLYPH = "✎ "   # ✎ pencil — a shape marker, not color, for a corrected cell (NFR-025)


class _SourceTab(QWidget):
    correctionEdited = Signal(str, str, str, str, str)   # doc_type, source_ref, field, original, new
    revertRequested = Signal(str, str, str)              # doc_type, source_ref, field

    def __init__(self, records, editable: bool, parent=None):
        super().__init__(parent)
        self._records = records
        self._editable = editable
        self._suspend = False
        self._preedit = {}                              # (row, col) -> value before the current edit

        lay = QVBoxLayout(self)
        lay.setContentsMargins(t.SP_2, t.SP_2, t.SP_2, t.SP_2)
        lay.setSpacing(t.SP_2)
        top = QHBoxLayout()
        self._count = QLabel(); self._count.setProperty("role", "context")
        top.addWidget(self._count); top.addStretch(1)
        self._search = QLineEdit(); self._search.setPlaceholderText("Search records…")
        self._search.setClearButtonEnabled(True); self._search.setMaximumWidth(260)
        top.addWidget(self._search)
        lay.addLayout(top)

        self._model = QStandardItemModel(self)
        self._proxy = QSortFilterProxyModel(self)
        self._proxy.setSourceModel(self._model)
        self._proxy.setFilterKeyColumn(-1)
        self._proxy.setFilterCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self._table = DataTable()
        if editable:
            self._table.setEditTriggers(QAbstractItemView.EditTrigger.DoubleClicked
                                        | QAbstractItemView.EditTrigger.EditKeyPressed)
            self._table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
            self._table.customContextMenuRequested.connect(self._on_context_menu)
        self._search.textChanged.connect(self._proxy.setFilterFixedString)
        self._search.textChanged.connect(lambda _t: self._update_count())
        self._model.itemChanged.connect(self._on_item_changed)
        lay.addWidget(self._table, 1)
        self.set_records(records)

    def set_records(self, records) -> None:
        self._records = records
        self._suspend = True
        self._model.clear()
        self._preedit = {}
        self._model.setHorizontalHeaderLabels([c.replace("_", " ").title() for c in records.columns])
        editable_cols = set(records.editable_columns or ())
        corrected = set(records.corrected_cells or ())
        originals = records.originals or {}
        for ridx, row in enumerate(records.rows):
            is_accepted = ridx < records.accepted_rows
            items = []
            for cidx, value in enumerate(row):
                item = QStandardItem(str(value))
                cell_editable = self._editable and is_accepted and cidx in editable_cols
                item.setEditable(cell_editable)
                if cell_editable:
                    self._preedit[(ridx, cidx)] = str(value)
                if (ridx, cidx) in corrected:
                    # The ✎ marker lives ONLY in the DISPLAY text; the EDIT value stays the plain value,
                    # so re-editing a corrected cell can never capture the marker into a saved correction
                    # (defense-in-depth: _on_item_changed also reads EditRole + strips the glyph).
                    item.setText(_CORRECTED_GLYPH + str(value))          # DisplayRole (shown)
                    item.setData(str(value), Qt.ItemDataRole.EditRole)   # EditRole (edited + read back)
                    f = QFont(); f.setBold(True); item.setFont(f)
                    item.setToolTip("Corrected. Original: %s" % originals.get((ridx, cidx), ""))
                items.append(item)
            self._model.appendRow(items)
        self._table.set_model(self._proxy)
        self._suspend = False
        self._update_count()

    def _on_item_changed(self, item) -> None:
        if self._suspend:
            return
        row, col = item.row(), item.column()
        if col not in set(self._records.editable_columns or ()) or row >= self._records.accepted_rows:
            return
        field = self._records.columns[col]
        source_ref = self._records.source_refs[row] if row < len(self._records.source_refs) else ""
        # Read the EDIT value (plain), and strip the display marker if it ever leaked in — the certified
        # correction must be exactly what the reviewer typed, never a UI glyph.
        raw = item.data(Qt.ItemDataRole.EditRole)
        raw = "" if raw is None else str(raw)
        if raw.startswith(_CORRECTED_GLYPH):
            raw = raw[len(_CORRECTED_GLYPH):]
        new_value = raw.strip()
        original = (self._records.originals or {}).get((row, col)) or self._preedit.get((row, col), "")
        if new_value == self._preedit.get((row, col), ""):
            return                                       # no change
        self.correctionEdited.emit(self._records.document_type, source_ref, field, original, new_value)

    def _on_context_menu(self, pos) -> None:
        index = self._table.indexAt(pos)
        if not index.isValid():
            return
        src = self._proxy.mapToSource(index)
        cell = (src.row(), src.column())
        if cell not in set(self._records.corrected_cells or ()):
            return                                       # only corrected cells can be reverted
        field = self._records.columns[src.column()]
        source_ref = self._records.source_refs[src.row()] if src.row() < len(self._records.source_refs) else ""
        menu = QMenu(self)
        act = menu.addAction("Revert to original")
        if menu.exec(self._table.viewport().mapToGlobal(pos)) is act:
            self.revertRequested.emit(self._records.document_type, source_ref, field)

    def _update_count(self) -> None:
        shown, total = self._proxy.rowCount(), self._model.rowCount()
        suffix = "" if shown == total else " (%d shown)" % shown
        edited = len(self._records.corrected_cells or ())
        edited_txt = ("  ·  %d corrected" % edited) if edited else ""
        self._count.setText("%d accepted · %d quarantined · %d record(s)%s%s" % (
            self._records.accepted_rows, self._records.quarantined_rows, total, suffix, edited_txt))

    # --- seams (stable for tests) ---
    def total_rows(self) -> int:
        return self._model.rowCount()

    def visible_rows(self) -> int:
        return self._proxy.rowCount()

    def set_filter(self, text: str) -> None:
        self._search.setText(text)

    def edit_cell(self, row: int, col: int, value: str) -> None:
        """Test seam: simulate a user committing an edit (sets EditRole exactly like the cell editor)."""
        self._model.item(row, col).setData(value, Qt.ItemDataRole.EditRole)


class ExtractionReview(QWidget):
    """Per-source extraction review (§9) + correction surface (§10-11)."""

    correctionEdited = Signal(str, str, str, str, str)   # doc_type, source_ref, field, original, new
    revertRequested = Signal(str, str, str)              # doc_type, source_ref, field

    def __init__(self, parent=None):
        super().__init__(parent)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(t.SP_2)
        self._hint = QLabel("Double-click a value to correct it before verifying. Your original is kept "
                            "and every change is recorded in the audit trail.")
        self._hint.setProperty("role", "context"); self._hint.setWordWrap(True)
        lay.addWidget(self._hint)
        self._tabs = QTabWidget()
        lay.addWidget(self._tabs)
        self._omitted = QLabel(); self._omitted.setProperty("role", "context")
        self._omitted.setWordWrap(True); self._omitted.setVisible(False)
        lay.addWidget(self._omitted)
        self._by_name = {}
        self._editable = True

    def set_editable(self, editable: bool) -> None:
        self._editable = editable
        self._hint.setVisible(editable)

    def set_data(self, records, omitted=()) -> None:
        self._tabs.clear()
        self._by_name = {}
        for rec in records or ():
            tab = _SourceTab(rec, self._editable)
            tab.correctionEdited.connect(self.correctionEdited.emit)
            tab.revertRequested.connect(self.revertRequested.emit)
            self._by_name[rec.source_type] = tab
            self._tabs.addTab(tab, "%s  (%d)" % (rec.source_type, rec.accepted_rows + rec.quarantined_rows))
        if omitted:
            self._omitted.setText("  ".join("Not extracted: %s — %s" % (name, note)
                                            for (_st, name, note) in omitted))
            self._omitted.setVisible(True)
        else:
            self._omitted.setVisible(False)

    # --- seams (stable for tests) ---
    def source_names(self):
        return list(self._by_name.keys())

    def tab(self, source_type: str):
        return self._by_name.get(source_type)
