from __future__ import annotations
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from finsight.delivery.desktop.theme import tokens as t


class EmptyState(QWidget):
    """Honest empty state: a title, an explanation, and an optional hint. No decorative imagery."""

    def __init__(self, title: str, message: str = "", hint: str = "", parent=None):
        super().__init__(parent)
        lay = QVBoxLayout(self)
        lay.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.setSpacing(t.SP_2)
        t_lbl = QLabel(title)
        t_lbl.setProperty("role", "emptyTitle")
        t_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(t_lbl)
        if message:
            m = QLabel(message)
            m.setProperty("role", "empty")
            m.setAlignment(Qt.AlignmentFlag.AlignCenter)
            m.setWordWrap(True)
            lay.addWidget(m)
        if hint:
            h = QLabel(hint)
            h.setProperty("role", "empty")
            h.setAlignment(Qt.AlignmentFlag.AlignCenter)
            h.setWordWrap(True)
            lay.addWidget(h)
