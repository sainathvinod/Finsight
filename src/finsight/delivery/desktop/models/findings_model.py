from __future__ import annotations
from typing import List, Optional
from PySide6.QtCore import Qt, QAbstractTableModel, QModelIndex
from PySide6.QtGui import QColor
from finsight.application.read_models.views import FindingView
from finsight.delivery.desktop.components.severity import severity_text, severity_color

_COLS = ["Finding ID", "Account", "Rule", "Type", "Severity", "State", "Period"]


class FindingsTableModel(QAbstractTableModel):
    """Presents deterministic findings. Severity shows a shape glyph + label (never color alone)."""

    def __init__(self, rows: Optional[List[FindingView]] = None, parent=None):
        super().__init__(parent)
        self._rows: List[FindingView] = list(rows or [])

    def set_rows(self, rows: List[FindingView]) -> None:
        self.beginResetModel()
        self._rows = list(rows)
        self.endResetModel()

    def finding_at(self, row: int) -> Optional[FindingView]:
        return self._rows[row] if 0 <= row < len(self._rows) else None

    def rowCount(self, parent=QModelIndex()) -> int:  # noqa: N802
        return 0 if parent.isValid() else len(self._rows)

    def columnCount(self, parent=QModelIndex()) -> int:  # noqa: N802
        return len(_COLS)

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):  # noqa: N802
        if role != Qt.ItemDataRole.DisplayRole:
            return None
        if orientation == Qt.Orientation.Horizontal:
            return _COLS[section]
        return section + 1

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None
        f = self._rows[index.row()]
        col = index.column()
        if role == Qt.ItemDataRole.DisplayRole:
            return [f.id, f.account, f.rule_id, f.finding_type,
                    severity_text(f.severity), f.state, f.period][col]
        # Secondary color reinforcement on the Severity column only; text already conveys it.
        if role == Qt.ItemDataRole.ForegroundRole and col == 4:
            return QColor(severity_color(f.severity))
        if role == Qt.ItemDataRole.ToolTipRole and col == 4:
            return f"Severity: {f.severity}"
        return None
