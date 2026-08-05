"""Accessible Light, Dark, and System Default appearance controls."""
from __future__ import annotations

from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtGui import QAction, QActionGroup
from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QMenu,
    QToolButton,
    QWidget,
)

from finsight.delivery.desktop.theme.appearance import (
    AppearanceManager,
    AppearanceMode,
)
from finsight.delivery.desktop.components.iconography import content_icon


class AppearanceControl(QWidget):
    """Reusable Settings/header control bound to an AppearanceManager."""

    appearanceSelected = Signal(object)

    def __init__(
        self,
        manager: AppearanceManager,
        *,
        compact: bool = False,
        parent: QWidget | None = None,
    ):
        super().__init__(parent)
        self._manager = manager
        self.setProperty("role", "appearanceControl")
        self.setAccessibleName("Appearance setting")
        self.setAccessibleDescription(
            "Choose Light, Dark, or System Default. System Default follows "
            "the operating-system appearance."
        )

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        self.label = QLabel("Appearance")
        self.selector = QComboBox()
        self.selector.setAccessibleName("Appearance")
        self.selector.setAccessibleDescription(
            "Light uses the warm FinSight palette. Dark uses the deep navy "
            "palette. System Default follows the operating system."
        )
        self.label.setBuddy(self.selector)
        if not compact:
            layout.addWidget(self.label)
        else:
            self.label.setVisible(False)
        for mode in (
            AppearanceMode.LIGHT,
            AppearanceMode.DARK,
            AppearanceMode.SYSTEM,
        ):
            self.selector.addItem(mode.label, mode.value)
        self.selector.setMinimumWidth(156)
        layout.addWidget(self.selector)
        self._sync(manager.mode)

        self.selector.currentIndexChanged.connect(self._selection_changed)
        manager.modeChanged.connect(self._sync)

    @property
    def current_mode(self) -> AppearanceMode:
        return AppearanceMode.parse(self.selector.currentData())

    def _selection_changed(self, _index: int) -> None:
        mode = self.current_mode
        if mode is self._manager.mode:
            return
        self._manager.set_mode(mode)
        self.appearanceSelected.emit(mode)

    def _sync(self, mode: AppearanceMode | str) -> None:
        selected = AppearanceMode.parse(mode)
        index = self.selector.findData(selected.value)
        if index < 0 or index == self.selector.currentIndex():
            return
        was_blocked = self.selector.blockSignals(True)
        self.selector.setCurrentIndex(index)
        self.selector.blockSignals(was_blocked)


class AppearanceMenuButton(QToolButton):
    """Compact keyboard-accessible header entry point for appearance settings."""

    appearanceSelected = Signal(object)

    def __init__(
        self,
        manager: AppearanceManager,
        *,
        parent: QWidget | None = None,
    ):
        super().__init__(parent)
        self._manager = manager
        self._actions: dict[AppearanceMode, QAction] = {}
        self.setText("Theme")
        self.setProperty("role", "secondary")
        self.setAccessibleName("Appearance settings")
        self.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        self.setToolButtonStyle(
            Qt.ToolButtonStyle.ToolButtonTextBesideIcon
        )
        self.setIconSize(QSize(18, 18))
        self.refresh_icon()
        self.setMinimumWidth(self.minimumSizeHint().width())

        menu = QMenu(self)
        menu.setAccessibleName("Appearance options")
        group = QActionGroup(menu)
        group.setExclusive(True)
        for mode in (
            AppearanceMode.LIGHT,
            AppearanceMode.DARK,
            AppearanceMode.SYSTEM,
        ):
            action = QAction(mode.label, group)
            action.setCheckable(True)
            action.setData(mode.value)
            menu.addAction(action)
            self._actions[mode] = action
        group.triggered.connect(self._selection_changed)
        self.setMenu(menu)
        self._sync(manager.mode)
        manager.modeChanged.connect(self._sync)
        manager.appearanceChanged.connect(
            lambda _mode, _theme: self.refresh_icon()
        )

    @property
    def current_mode(self) -> AppearanceMode:
        return self._manager.mode

    def action_for(self, mode: AppearanceMode | str) -> QAction:
        return self._actions[AppearanceMode.parse(mode)]

    def refresh_icon(self) -> None:
        self.setIcon(content_icon("appearance", tone="header"))

    def _selection_changed(self, action: QAction) -> None:
        mode = AppearanceMode.parse(action.data())
        self._manager.set_mode(mode)
        self.appearanceSelected.emit(mode)

    def _sync(self, mode: AppearanceMode | str) -> None:
        selected = AppearanceMode.parse(mode)
        for item_mode, action in self._actions.items():
            action.setChecked(item_mode is selected)
        self.setToolTip(f"Appearance: {selected.label}")
        self.setAccessibleDescription(
            f"Current appearance is {selected.label}. Activate to choose Light, "
            "Dark, or System Default."
        )


__all__ = ["AppearanceControl", "AppearanceMenuButton"]
