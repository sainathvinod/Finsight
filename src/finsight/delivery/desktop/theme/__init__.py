# Centralized design system for the FinSight desktop UI.
# tokens: the single source of colors, spacing, radii, type. qss: builds the Qt stylesheet from tokens.
from finsight.delivery.desktop.theme import tokens
from finsight.delivery.desktop.theme.qss import build_qss

__all__ = ["tokens", "build_qss"]
