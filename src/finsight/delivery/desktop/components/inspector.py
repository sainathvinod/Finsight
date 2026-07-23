from __future__ import annotations
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QScrollArea, QFrame)
from finsight.delivery.desktop.theme import tokens as t


class DetailInspector(QWidget):
    """A right-side inspector that presents key/value detail for the selected record.
    Read-only; carries no actions."""

    def __init__(self, title: str = "Details", parent=None):
        super().__init__(parent)
        self.setObjectName("Inspector")
        self.setMinimumWidth(260)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(t.SP_3, t.SP_3, t.SP_3, t.SP_3)
        outer.setSpacing(t.SP_2)

        self._title = QLabel(title)
        self._title.setProperty("role", "sectionSub")
        self._title.setStyleSheet("font-weight:600;")
        outer.addWidget(self._title)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        self._content = QWidget()
        self._body = QVBoxLayout(self._content)
        self._body.setContentsMargins(0, 0, 0, 0)
        self._body.setSpacing(t.SP_2)
        self._body.setAlignment(Qt.AlignmentFlag.AlignTop)
        scroll.setWidget(self._content)
        outer.addWidget(scroll, 1)

        self.show_placeholder("Select a row to see details.")

    # --- content management ---
    def _clear(self) -> None:
        while self._body.count():
            item = self._body.takeAt(0)
            w = item.widget()
            if w is not None:
                w.setParent(None)   # remove from display synchronously (deleteLater alone is async)
                w.deleteLater()

    def set_title(self, title: str) -> None:
        self._title.setText(title)

    def show_placeholder(self, message: str) -> None:
        self._clear()
        lbl = QLabel(message)
        lbl.setProperty("role", "empty")
        lbl.setWordWrap(True)
        self._body.addWidget(lbl)

    def add_section(self, title: str) -> None:
        lbl = QLabel(title.upper())
        lbl.setProperty("role", "navGroup")
        lbl.setContentsMargins(0, t.SP_2, 0, 0)
        self._body.addWidget(lbl)

    def add_row(self, key: str, value: str, mono: bool = False) -> None:
        row = QFrame()
        h = QVBoxLayout(row)
        h.setContentsMargins(0, 0, 0, 0)
        h.setSpacing(1)
        k = QLabel(key)
        k.setProperty("role", "kvKey")
        v = QLabel(value if value is not None else "")
        v.setProperty("role", "mono" if mono else "kvVal")
        v.setWordWrap(True)
        v.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        h.addWidget(k)
        h.addWidget(v)
        self._body.addWidget(row)

    def begin(self, title: str) -> None:
        """Start a fresh detail render."""
        self.set_title(title)
        self._clear()
