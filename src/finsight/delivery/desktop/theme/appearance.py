"""Application-wide Light, Dark, and System Default appearance management."""
from __future__ import annotations

from enum import Enum
from typing import Any

from PySide6.QtCore import QObject, QSettings, Qt, Signal
from PySide6.QtGui import QColor, QGuiApplication, QPalette

from finsight.delivery.desktop.theme import tokens as t
from finsight.delivery.desktop.theme.qss import (
    build_qss,
    high_contrast_requested,
)


class AppearanceMode(str, Enum):
    LIGHT = "light"
    DARK = "dark"
    SYSTEM = "system"

    @property
    def label(self) -> str:
        return {
            AppearanceMode.LIGHT: "Light",
            AppearanceMode.DARK: "Dark",
            AppearanceMode.SYSTEM: "System Default",
        }[self]

    @classmethod
    def parse(cls, value: Any) -> "AppearanceMode":
        if isinstance(value, cls):
            return value
        normalized = str(value or "").strip().lower()
        aliases = {
            "light": cls.LIGHT,
            "dark": cls.DARK,
            "system": cls.SYSTEM,
            "system default": cls.SYSTEM,
        }
        return aliases.get(normalized, cls.SYSTEM)


class AppearanceSettings:
    """Small persistence adapter so appearance preferences are testable."""

    KEY = "appearance/mode"

    def __init__(self, settings: QSettings | None = None):
        self._settings = settings or QSettings("FinSight", "FinSight")

    def load(self) -> AppearanceMode:
        return AppearanceMode.parse(
            self._settings.value(self.KEY, AppearanceMode.SYSTEM.value)
        )

    def save(self, mode: AppearanceMode) -> None:
        self._settings.setValue(self.KEY, mode.value)
        self._settings.sync()


def build_application_palette(theme: t.ThemePalette | str) -> QPalette:
    """Create the QPalette used by widgets that do not consume QSS directly."""

    colors = theme if isinstance(theme, t.ThemePalette) else t.palette_for(theme)
    palette = QPalette()

    def set_role(role: QPalette.ColorRole, color: str) -> None:
        palette.setColor(QPalette.ColorGroup.All, role, QColor(color))

    set_role(QPalette.ColorRole.Window, colors.canvas)
    set_role(QPalette.ColorRole.WindowText, colors.text_primary)
    set_role(QPalette.ColorRole.Base, colors.surface)
    set_role(QPalette.ColorRole.AlternateBase, colors.surface_subtle)
    set_role(QPalette.ColorRole.ToolTipBase, colors.tooltip_surface)
    set_role(QPalette.ColorRole.ToolTipText, colors.tooltip_text)
    set_role(QPalette.ColorRole.Text, colors.text_primary)
    set_role(QPalette.ColorRole.Button, colors.surface)
    set_role(QPalette.ColorRole.ButtonText, colors.text_primary)
    set_role(QPalette.ColorRole.BrightText, colors.error)
    set_role(QPalette.ColorRole.Highlight, colors.accent_subtle)
    set_role(QPalette.ColorRole.HighlightedText, colors.text_primary)
    set_role(QPalette.ColorRole.Link, colors.accent)
    set_role(QPalette.ColorRole.LinkVisited, colors.accent_hover)
    set_role(QPalette.ColorRole.Light, colors.surface_raised)
    set_role(QPalette.ColorRole.Midlight, colors.surface_subtle)
    set_role(QPalette.ColorRole.Mid, colors.border_strong)
    set_role(QPalette.ColorRole.Dark, colors.border)
    set_role(QPalette.ColorRole.Shadow, colors.navigation)
    set_role(QPalette.ColorRole.PlaceholderText, colors.text_muted)

    for role in (
        QPalette.ColorRole.WindowText,
        QPalette.ColorRole.Text,
        QPalette.ColorRole.ButtonText,
        QPalette.ColorRole.PlaceholderText,
    ):
        palette.setColor(
            QPalette.ColorGroup.Disabled, role, QColor(colors.disabled_text)
        )
    palette.setColor(
        QPalette.ColorGroup.Disabled,
        QPalette.ColorRole.Button,
        QColor(colors.disabled_surface),
    )
    palette.setColor(
        QPalette.ColorGroup.Disabled,
        QPalette.ColorRole.Base,
        QColor(colors.disabled_surface),
    )
    return palette


class AppearanceManager(QObject):
    """Resolve, persist, and apply the application appearance.

    System high contrast takes precedence over authored Light/Dark palettes.
    ``System Default`` follows ``QStyleHints.colorSchemeChanged`` at runtime.
    """

    modeChanged = Signal(object)
    themeChanged = Signal(object)
    appearanceChanged = Signal(str, str)

    def __init__(
        self,
        application: QGuiApplication,
        *,
        settings: QSettings | AppearanceSettings | None = None,
        style_hints: QObject | None = None,
        system_palette: QPalette | None = None,
        auto_apply: bool = True,
        parent: QObject | None = None,
    ):
        super().__init__(parent)
        self._application = application
        self._settings = (
            settings
            if isinstance(settings, AppearanceSettings)
            else AppearanceSettings(settings)
        )
        self._style_hints = style_hints or application.styleHints()
        self._system_palette = QPalette(system_palette or application.palette())
        self._last_system_scheme = self._read_system_scheme()
        self._mode = self._settings.load()
        self._resolved = self._resolve_palette()
        self._high_contrast = False
        self._connected = False
        signal = getattr(self._style_hints, "colorSchemeChanged", None)
        if signal is not None:
            signal.connect(self._on_system_scheme_changed)
            self._connected = True
        if auto_apply:
            self.apply()

    @property
    def mode(self) -> AppearanceMode:
        return self._mode

    @property
    def resolved_palette(self) -> t.ThemePalette:
        return self._resolved

    @property
    def is_high_contrast(self) -> bool:
        return self._high_contrast

    def set_mode(self, mode: AppearanceMode | str) -> None:
        selected = AppearanceMode.parse(mode)
        changed = selected is not self._mode
        self._mode = selected
        self._settings.save(selected)
        self.apply()
        if changed:
            self.modeChanged.emit(selected)

    def apply(self) -> None:
        """Apply palette and stylesheet consistently across the QApplication."""

        previous = self._resolved
        self._resolved = self._resolve_palette()
        self._high_contrast = high_contrast_requested(self._system_palette)
        if self._high_contrast:
            qt_palette = QPalette(self._system_palette)
            stylesheet = build_qss(
                theme=self._resolved,
                high_contrast=True,
                palette=qt_palette,
            )
        else:
            qt_palette = build_application_palette(self._resolved)
            stylesheet = build_qss(
                theme=self._resolved,
                high_contrast=False,
                palette=qt_palette,
            )
        self._application.setPalette(qt_palette)
        self._application.setStyleSheet(stylesheet)
        self._application.setProperty(
            "finsightAppearanceMode", self._mode.value
        )
        self._application.setProperty(
            "finsightResolvedTheme", self._resolved.name
        )
        self._application.setProperty(
            "finsightHighContrast", self._high_contrast
        )
        if previous is not self._resolved:
            self.themeChanged.emit(self._resolved)
        self.appearanceChanged.emit(self._mode.value, self._resolved.name)

    def refresh_system_appearance(
        self, *, palette: QPalette | None = None
    ) -> None:
        """Refresh a system palette/scheme after an OS accessibility change."""

        if palette is not None:
            self._system_palette = QPalette(palette)
        self._last_system_scheme = self._read_system_scheme()
        if self._mode is AppearanceMode.SYSTEM or high_contrast_requested(
            self._system_palette
        ):
            self.apply()

    def dispose(self) -> None:
        """Disconnect the operating-system signal for deterministic teardown."""

        if not self._connected:
            return
        signal = getattr(self._style_hints, "colorSchemeChanged", None)
        if signal is not None:
            try:
                signal.disconnect(self._on_system_scheme_changed)
            except (RuntimeError, TypeError):
                pass
        self._connected = False

    def _on_system_scheme_changed(self, scheme: Qt.ColorScheme) -> None:
        normalized = self._normalize_scheme(scheme)
        if normalized is not None:
            self._last_system_scheme = normalized
        if self._mode is AppearanceMode.SYSTEM:
            self.apply()

    def _read_system_scheme(self) -> Qt.ColorScheme:
        getter = getattr(self._style_hints, "colorScheme", None)
        if getter is not None:
            normalized = self._normalize_scheme(getter())
            if normalized is not None:
                return normalized
        window = self._system_palette.color(QPalette.ColorRole.Window)
        text = self._system_palette.color(QPalette.ColorRole.WindowText)
        return (
            Qt.ColorScheme.Dark
            if window.lightnessF() < text.lightnessF()
            else Qt.ColorScheme.Light
        )

    @staticmethod
    def _normalize_scheme(value: Any) -> Qt.ColorScheme | None:
        if value == Qt.ColorScheme.Dark:
            return Qt.ColorScheme.Dark
        if value == Qt.ColorScheme.Light:
            return Qt.ColorScheme.Light
        return None

    def _resolve_palette(self) -> t.ThemePalette:
        if self._mode is AppearanceMode.LIGHT:
            return t.LIGHT
        if self._mode is AppearanceMode.DARK:
            return t.DARK
        return (
            t.DARK
            if self._last_system_scheme == Qt.ColorScheme.Dark
            else t.LIGHT
        )


__all__ = [
    "AppearanceManager",
    "AppearanceMode",
    "AppearanceSettings",
    "build_application_palette",
]
