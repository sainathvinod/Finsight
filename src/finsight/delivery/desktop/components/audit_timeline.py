from __future__ import annotations
from typing import List
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame
from finsight.delivery.desktop.theme import tokens as t


class AuditTimelineRow(QFrame):
    """One append-only audit event as a selectable timeline row: time, action, actor."""

    clicked = Signal(int)

    def __init__(self, index: int, ts: str, action: str, actor: str, parent=None):
        super().__init__(parent)
        self._index = index
        self.setProperty("selected", False)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(t.SP_2, t.SP_1, t.SP_2, t.SP_1)
        lay.setSpacing(t.SP_3)
        time_lbl = QLabel(ts)
        time_lbl.setProperty("role", "mono")
        time_lbl.setStyleSheet(f"color:{t.TEXT_MUTED};")
        time_lbl.setMinimumWidth(150)
        action_lbl = QLabel(action)
        action_lbl.setStyleSheet("font-weight:600;")
        actor_lbl = QLabel(actor)
        actor_lbl.setStyleSheet(f"color:{t.TEXT_SECONDARY};")
        lay.addWidget(time_lbl)
        lay.addWidget(action_lbl, 1)
        lay.addWidget(actor_lbl)
        self.setToolTip(f"{action} — {actor} @ {ts}")
        self._apply_style(False)

    def _apply_style(self, selected: bool) -> None:
        bg = t.ACCENT_SUBTLE_BG if selected else "transparent"
        border = t.ACCENT if selected else t.BORDER
        self.setStyleSheet(f"QFrame{{background:{bg}; border-bottom:1px solid {border};}}")

    def set_selected(self, selected: bool) -> None:
        self.setProperty("selected", selected)
        self._apply_style(selected)

    def mousePressEvent(self, event):  # noqa: N802 (Qt override)
        self.clicked.emit(self._index)
        super().mousePressEvent(event)


class AuditTimeline(QWidget):
    """Keyboard-navigable ordered timeline of audit events. Emits currentChanged(index)."""

    currentChanged = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self._lay = QVBoxLayout(self)
        self._lay.setContentsMargins(0, 0, 0, 0)
        self._lay.setSpacing(0)
        self._lay.setAlignment(Qt.AlignmentFlag.AlignTop)
        self._rows: List[AuditTimelineRow] = []
        self._current = -1

    def set_events(self, events) -> None:
        while self._lay.count():
            item = self._lay.takeAt(0)
            w = item.widget()
            if w is not None:
                w.deleteLater()
        self._rows = []
        for i, e in enumerate(events):
            row = AuditTimelineRow(i, e.ts, e.action, e.actor)
            row.clicked.connect(self.set_current)
            self._rows.append(row)
            self._lay.addWidget(row)
        self._current = -1
        if self._rows:
            self.set_current(0)

    def set_current(self, index: int) -> None:
        if not self._rows or not (0 <= index < len(self._rows)):
            return
        if self._current == index:
            return
        if 0 <= self._current < len(self._rows):
            self._rows[self._current].set_selected(False)
        self._current = index
        self._rows[index].set_selected(True)
        self.currentChanged.emit(index)

    def current_index(self) -> int:
        return self._current

    def keyPressEvent(self, event):  # noqa: N802 (Qt override)
        key = event.key()
        if key in (Qt.Key.Key_Down, Qt.Key.Key_J):
            self.set_current(min(self._current + 1, len(self._rows) - 1))
        elif key in (Qt.Key.Key_Up, Qt.Key.Key_K):
            self.set_current(max(self._current - 1, 0))
        elif key == Qt.Key.Key_Home:
            self.set_current(0)
        elif key == Qt.Key.Key_End:
            self.set_current(len(self._rows) - 1)
        else:
            super().keyPressEvent(event)
