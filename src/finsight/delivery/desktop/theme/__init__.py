"""Centralized design and appearance system for the FinSight desktop UI."""

from finsight.delivery.desktop.theme import tokens
from finsight.delivery.desktop.theme.appearance import (
    AppearanceManager,
    AppearanceMode,
    AppearanceSettings,
    build_application_palette,
)
from finsight.delivery.desktop.theme.qss import build_qss

__all__ = [
    "AppearanceManager",
    "AppearanceMode",
    "AppearanceSettings",
    "build_application_palette",
    "build_qss",
    "tokens",
]
