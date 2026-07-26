# Theme manager (target-product §20): applies Light / Dark / System / High-Contrast + zoom to the whole
# app in one setStyleSheet call, and persists the choice per user (QSettings — native, no DB, local).
from __future__ import annotations
from PySide6.QtCore import Qt, QSettings
from PySide6.QtWidgets import QApplication
from finsight.delivery.desktop.theme.palettes import make_palette, PALETTES
from finsight.delivery.desktop.theme.qss import build_qss

MODES = ("system", "light", "dark", "high-contrast")
MIN_SCALE, MAX_SCALE, STEP = 0.8, 1.8, 0.1


def _clamp(scale: float) -> float:
    return round(max(MIN_SCALE, min(MAX_SCALE, scale)), 2)


def resolve_mode(mode: str, app=None) -> str:
    """Resolve 'system' to light/dark from the OS colour scheme; pass concrete modes through."""
    if mode != "system":
        return mode if mode in PALETTES else "light"
    try:
        app = app or QApplication.instance()
        return "dark" if app.styleHints().colorScheme() == Qt.ColorScheme.Dark else "light"
    except Exception:
        return "light"


class ThemeManager:
    """Holds the chosen mode + zoom scale, builds the themed QSS, and persists the choice."""

    def __init__(self, settings=None):
        self._settings = settings if settings is not None else QSettings("FinSight", "FinSight")
        self.mode = self._settings.value("theme/mode", "system") or "system"
        if self.mode not in MODES:
            self.mode = "system"
        try:
            self.scale = _clamp(float(self._settings.value("theme/scale", 1.0) or 1.0))
        except (TypeError, ValueError):
            self.scale = 1.0

    def qss(self, app=None) -> str:
        return build_qss(make_palette(resolve_mode(self.mode, app), self.scale))

    def apply(self, app) -> None:
        app.setStyleSheet(self.qss(app))
        self._save()

    def set_mode(self, mode: str, app) -> None:
        self.mode = mode if mode in MODES else "system"
        self.apply(app)

    def set_scale(self, scale: float, app) -> None:
        self.scale = _clamp(scale)
        self.apply(app)

    def zoom_in(self, app) -> None:
        self.set_scale(self.scale + STEP, app)

    def zoom_out(self, app) -> None:
        self.set_scale(self.scale - STEP, app)

    def reset_zoom(self, app) -> None:
        self.set_scale(1.0, app)

    def _save(self) -> None:
        self._settings.setValue("theme/mode", self.mode)
        self._settings.setValue("theme/scale", self.scale)
