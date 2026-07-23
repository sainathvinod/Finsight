from __future__ import annotations
from PySide6.QtCore import Qt, QModelIndex
from PySide6.QtWidgets import QWidget, QVBoxLayout, QStackedWidget, QSplitter
from finsight.delivery.desktop.components import SectionHeader, DataTable, EmptyState, DetailInspector
from finsight.delivery.desktop.components.severity import severity_text
from finsight.delivery.desktop.models import FindingsTableModel
from finsight.delivery.desktop.theme import tokens as t


class FindingsView(QWidget):
    """Read-only findings table with a detail inspector showing evidence and source references."""

    def __init__(self, controller, parent=None):
        super().__init__(parent)
        self._c = controller
        self._model = FindingsTableModel()

        root = QVBoxLayout(self)
        root.setContentsMargins(t.SP_5, t.SP_5, t.SP_5, t.SP_5)
        root.setSpacing(t.SP_3)
        self._header = SectionHeader("Findings", "")
        root.addWidget(self._header)

        self._stack = QStackedWidget()
        root.addWidget(self._stack, 1)

        split = QSplitter(Qt.Orientation.Horizontal)
        self._table = DataTable()
        self._table.setModel(self._model)
        self._table.selectionModel().currentRowChanged.connect(self._on_row)
        self._inspector = DetailInspector("Finding")
        split.addWidget(self._table)
        split.addWidget(self._inspector)
        split.setStretchFactor(0, 3)
        split.setStretchFactor(1, 2)
        split.setSizes([620, 360])   # explicit initial proportion (stretch alone leaves inspector to collapse)
        self._stack.addWidget(split)

        self._empty = EmptyState(
            "No findings",
            "This review has no deterministic findings, or no review is selected.",
            "Findings are produced only by the deterministic rules engine.",
        )
        self._stack.addWidget(self._empty)
        self.refresh()

    def refresh(self) -> None:
        cid = self._c.active_review_id
        rows = self._c.findings(cid) if cid else []
        self._model.set_rows(rows)
        if rows:
            self._header.set_subtitle(f"{len(rows)} finding(s)")
            self._stack.setCurrentIndex(0)
            self._table.selectRow(0)
        else:
            self._header.set_subtitle("")
            self._inspector.show_placeholder("Select a finding to see its evidence.")
            self._stack.setCurrentWidget(self._empty)

    def _on_row(self, current: QModelIndex, _prev: QModelIndex) -> None:
        if not current.isValid():
            return
        f = self._model.finding_at(current.row())
        if f is None:
            return
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
