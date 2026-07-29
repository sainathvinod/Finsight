from __future__ import annotations
from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtGui import QKeyEvent
from PySide6.QtWidgets import QPushButton

from finsight.delivery.desktop.components.iconography import navigation_icon


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
        self.setIconSize(QSize(22, 22))
        self.setProperty("iconKey", key)
        self.refresh_icon()
        self.clicked.connect(lambda: self.activated.emit(self._key))

    @property
    def key(self) -> str:
        return self._key

    def refresh_icon(self) -> None:
        """Rebuild the semantic icon after a Light/Dark/System appearance change."""

        self.setIcon(navigation_icon(self._key))

    def keyPressEvent(self, event: QKeyEvent) -> None:
        """Activate primary navigation with either desktop Enter key."""
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self.click()
            event.accept()
            return
        super().keyPressEvent(event)
