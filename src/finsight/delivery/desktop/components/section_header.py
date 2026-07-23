from __future__ import annotations
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from finsight.delivery.desktop.theme import tokens as t


class SectionHeader(QWidget):
    """Screen/section title with an optional subtitle line."""

    def __init__(self, title: str, subtitle: str = "", parent=None):
        super().__init__(parent)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, t.SP_2)
        lay.setSpacing(2)
        self._title = QLabel(title)
        self._title.setProperty("role", "sectionHeader")
        lay.addWidget(self._title)
        self._sub = QLabel(subtitle)
        self._sub.setProperty("role", "sectionSub")
        self._sub.setVisible(bool(subtitle))
        lay.addWidget(self._sub)

    def set_subtitle(self, text: str) -> None:
        self._sub.setText(text)
        self._sub.setVisible(bool(text))
