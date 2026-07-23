from __future__ import annotations
from PySide6.QtWidgets import QLabel
from finsight.delivery.desktop.theme import tokens as t

# Restrained inline messaging: a thin left rule in the kind's color + muted text. No modal, no fill.
_KIND_COLOR = {
    "info": t.ACCENT,
    "success": t.STATUS_OK,
    "warning": t.STATUS_ATTENTION,
    "error": t.SEVERITY["Critical"]["color"],
}


class InlineMessage(QLabel):
    """A compact, non-modal status/validation message shown inline within a panel."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWordWrap(True)
        self.setVisible(False)

    def show_message(self, text: str, kind: str = "info") -> None:
        color = _KIND_COLOR.get(kind, t.TEXT_SECONDARY)
        self.setText(text)
        self.setStyleSheet(
            f"color:{t.TEXT_PRIMARY}; border-left:3px solid {color};"
            f"padding:{t.SP_2}px {t.SP_3}px; background:{t.BG_SUBTLE};")
        self.setVisible(True)

    def clear_message(self) -> None:
        self.setText("")
        self.setVisible(False)
