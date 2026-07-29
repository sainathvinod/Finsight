"""Responsive desktop sidebar used by every FinSight application shell."""
from __future__ import annotations

from PySide6.QtCore import QEvent, QSize, Qt, Signal
from PySide6.QtWidgets import QWidget

from finsight.delivery.desktop.components.nav_item import NavItem
from finsight.delivery.desktop.theme import tokens as t


class AdaptiveSidebar(QWidget):
    """Keep navigation proportional on wide screens without crowding small ones."""

    widthAdjusted = Signal(int)

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self._observed_window: QWidget | None = None
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setFixedWidth(t.SIDEBAR_W)
        self.setProperty("density", "compact")

    @staticmethod
    def width_for(window_width: int) -> int:
        if window_width >= 1600:
            return 330
        if window_width >= 1120:
            return 260
        return t.SIDEBAR_W

    def _apply_window_width(self, window_width: int) -> None:
        width = self.width_for(window_width)
        density = "wide" if width >= 330 else "standard"
        if width == t.SIDEBAR_W:
            density = "compact"
        if self.width() != width:
            self.setFixedWidth(width)
            self.widthAdjusted.emit(width)
        if self.property("density") != density:
            self.setProperty("density", density)
            margin = t.SP_5 if density == "wide" else t.SP_3
            if density == "standard":
                margin = t.SP_4
            if self.layout() is not None:
                self.layout().setContentsMargins(
                    margin,
                    t.SP_4,
                    margin,
                    t.SP_3,
                )
            icon_size = QSize(26, 26) if density == "wide" else QSize(22, 22)
            for item in self.findChildren(NavItem):
                item.setIconSize(icon_size)
            self.style().unpolish(self)
            self.style().polish(self)
            self.updateGeometry()

    def showEvent(self, event) -> None:
        super().showEvent(event)
        host = self.window()
        if host is not self._observed_window:
            if self._observed_window is not None:
                self._observed_window.removeEventFilter(self)
            self._observed_window = host
            host.installEventFilter(self)
        self._apply_window_width(host.width())

    def eventFilter(self, watched, event) -> bool:
        if (
            watched is self._observed_window
            and event.type() is QEvent.Type.Resize
        ):
            self._apply_window_width(event.size().width())
        return super().eventFilter(watched, event)


__all__ = ["AdaptiveSidebar"]
