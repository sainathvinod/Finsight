from __future__ import annotations
from typing import List, Optional
from PySide6.QtCore import Qt, QAbstractTableModel, QModelIndex
from finsight.application.read_models.views import ReviewStatusView

_COLS = ["Period", "State", "Findings"]


class ReviewsTableModel(QAbstractTableModel):
    """Presents review cycles (period, state, finding count). Read-only."""

    def __init__(self, rows: Optional[List[ReviewStatusView]] = None, parent=None):
        super().__init__(parent)
        self._rows: List[ReviewStatusView] = list(rows or [])

    def set_rows(self, rows: List[ReviewStatusView]) -> None:
        self.beginResetModel()
        self._rows = list(rows)
        self.endResetModel()

    def review_at(self, row: int) -> Optional[ReviewStatusView]:
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
        r = self._rows[index.row()]
        col = index.column()
        if role == Qt.ItemDataRole.DisplayRole:
            if col == 0:
                return f"{r.month} {r.year}"
            if col == 1:
                return r.state
            if col == 2:
                return str(r.finding_count)
        if role == Qt.ItemDataRole.TextAlignmentRole and col == 2:
            return int(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        return None
