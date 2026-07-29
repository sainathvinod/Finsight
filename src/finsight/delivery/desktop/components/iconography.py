"""Theme-aware FinSight iconography built from QtAwesome's Phosphor set.

The icon font is bundled by QtAwesome, so the desktop application gets one
consistent, cross-platform outline language without depending on operating
system theme-icon availability.
"""
from __future__ import annotations

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QIcon, QPalette
from PySide6.QtWidgets import QApplication, QFrame, QLabel, QVBoxLayout
import qtawesome as qta

from finsight.delivery.desktop.theme import tokens as t


_NAVIGATION_SYMBOLS: dict[str, tuple[str, str]] = {
    "welcome": ("ph.house", "ph.house-fill"),
    "home": ("ph.house", "ph.house-fill"),
    "past_reviews": (
        "ph.clock-counter-clockwise",
        "ph.clock-counter-clockwise",
    ),
    "past": ("ph.clock-counter-clockwise", "ph.clock-counter-clockwise"),
    "rule_governance": ("ph.shield-check", "ph.shield-check-fill"),
    "rules": ("ph.shield-check", "ph.shield-check-fill"),
    "settings": ("ph.gear-six", "ph.gear-six-fill"),
    "ask_fin": ("ph.chat-circle", "ph.chat-circle-fill"),
    "ask": ("ph.chat-circle", "ph.chat-circle-fill"),
    "askfin": ("ph.chat-circle", "ph.chat-circle-fill"),
    "upload": ("ph.upload", "ph.upload-fill"),
    "financial_review": ("ph.file-text", "ph.file-text-fill"),
    "dashboard": ("ph.squares-four", "ph.squares-four-fill"),
    "reviews": ("ph.files", "ph.files-fill"),
    "overview": ("ph.chart-pie", "ph.chart-pie-fill"),
    "workspace": ("ph.path", "ph.path"),
    "findings": ("ph.warning-circle", "ph.warning-circle-fill"),
    "audit": ("ph.list-bullets", "ph.list-bullets-fill"),
}

_CONTENT_SYMBOLS: dict[str, str] = {
    "create_review": "ph.file-plus",
    "open_review": "ph.folder",
    "appearance": "ph.sun",
    "close": "ph.x",
}


def _active_palette() -> t.ThemePalette:
    application = QApplication.instance()
    if application is not None:
        selected = application.property("finsightResolvedTheme")
        if selected:
            try:
                return t.palette_for(str(selected))
            except ValueError:
                pass
        window = application.palette().color(QPalette.ColorRole.Window)
        text = application.palette().color(QPalette.ColorRole.WindowText)
        if window.lightnessF() < text.lightnessF():
            return t.DARK
    return t.LIGHT


def navigation_icon(key: str) -> QIcon:
    """Return a navigation icon with correct normal, selected, and disabled colors."""

    names = _NAVIGATION_SYMBOLS.get(str(key).strip().lower())
    if names is None:
        return QIcon()
    normal_name, selected_name = names
    palette = _active_palette()
    return qta.icon(
        normal_name,
        on=selected_name,
        color=palette.navigation_text,
        color_on=palette.navigation_active_text,
        color_active=palette.navigation_text,
        color_off_active=palette.navigation_text,
        color_on_active=palette.navigation_active_text,
        color_selected=palette.navigation_active_text,
        color_off_selected=palette.navigation_active_text,
        color_on_selected=palette.navigation_active_text,
        color_disabled=palette.navigation_muted,
        color_off_disabled=palette.navigation_muted,
        color_on_disabled=palette.navigation_muted,
        scale_factor=0.88,
    )


def content_icon(name: str, *, tone: str = "accent") -> QIcon:
    """Return a content/utility icon using one semantic theme color."""

    symbol = _CONTENT_SYMBOLS[name]
    palette = _active_palette()
    colors = {
        "accent": palette.accent,
        "neutral": palette.text_secondary,
        "header": palette.text_secondary,
    }
    color = colors[tone]
    return qta.icon(
        symbol,
        color=color,
        color_active=color,
        color_selected=color,
        color_disabled=palette.disabled_text,
        scale_factor=0.9,
    )


class IconBadge(QFrame):
    """Circular landing-card icon medallion that follows the active appearance."""

    def __init__(
        self,
        icon_name: str,
        *,
        tone: str,
        accessible_name: str,
        parent=None,
    ):
        super().__init__(parent)
        self._icon_name = icon_name
        self._tone = tone
        self.setProperty("role", "landingIconBadge")
        self.setProperty("tone", tone)
        self.setFixedSize(60, 60)
        self.setAccessibleName(accessible_name)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        self._icon = QLabel()
        self._icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._icon.setAttribute(
            Qt.WidgetAttribute.WA_TransparentForMouseEvents, True
        )
        layout.addWidget(self._icon)
        self.refresh_icon()

    def refresh_icon(self) -> None:
        icon = content_icon(
            self._icon_name,
            tone="accent" if self._tone == "create" else "neutral",
        )
        self._icon.setPixmap(
            icon.pixmap(
                QSize(30, 30),
                QIcon.Mode.Normal,
                QIcon.State.Off,
            )
        )


__all__ = [
    "IconBadge",
    "content_icon",
    "navigation_icon",
]
