from __future__ import annotations
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QPushButton


class NavItem(QPushButton):
    """A single primary-navigation entry. Checkable, keyboard-focusable, styled via the [nav] property."""

    activated = Signal(str)

    def __init__(self, key: str, label: str, parent=None):
        super().__init__(label, parent)
        self._key = key
        self.setProperty("nav", True)
        self.setCheckable(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setAccessibleName(label)
        self.setToolTip(label)
        self.clicked.connect(lambda: self.activated.emit(self._key))

    @property
    def key(self) -> str:
        return self._key
