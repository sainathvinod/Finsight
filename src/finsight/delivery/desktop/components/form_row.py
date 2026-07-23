from __future__ import annotations
from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel
from finsight.delivery.desktop.theme import tokens as t


class FormRow(QWidget):
    """A labeled form row: a fixed-width caption and a field widget, consistently aligned."""

    def __init__(self, label: str, field: QWidget, label_width: int = 120, parent=None):
        super().__init__(parent)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(t.SP_3)
        cap = QLabel(label)
        cap.setProperty("role", "kvKey")
        cap.setFixedWidth(label_width)
        lay.addWidget(cap)
        lay.addWidget(field, 1)
        self.field = field
