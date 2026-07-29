"""Accessible business-first messages with optional troubleshooting details."""
from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QFrame, QLabel, QPushButton, QVBoxLayout

from finsight.application.failure_contracts import ErrorPresentation
from finsight.delivery.desktop.theme import tokens as t


class InlineMessage(QFrame):
    visibilityChanged = Signal(bool)

    def __init__(self, *, kind: str = "error", parent=None):
        super().__init__(parent)
        self.setProperty("role", "inlineMessage")
        self.setProperty("kind", kind)
        self.setAccessibleName("FinSight message")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(t.SP_3, t.SP_3, t.SP_3, t.SP_3)
        layout.setSpacing(t.SP_2)

        self.primary = QLabel()
        self.primary.setWordWrap(True)
        self.primary.setProperty("role", "inlineMessageText")
        layout.addWidget(self.primary)

        self.toggle = QPushButton("View technical details")
        self.toggle.setProperty("role", "quiet")
        self.toggle.setAccessibleName("View technical details")
        self.toggle.setCheckable(True)
        self.toggle.setVisible(False)
        self.toggle.toggled.connect(self._toggle)
        layout.addWidget(self.toggle, 0, Qt.AlignmentFlag.AlignLeft)

        self.details = QLabel()
        self.details.setWordWrap(True)
        self.details.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByKeyboard
            | Qt.TextInteractionFlag.TextSelectableByMouse
        )
        self.details.setProperty("role", "technicalDetails")
        self.details.setVisible(False)
        layout.addWidget(self.details)
        self.setVisible(False)

    def show_message(self, presentation: ErrorPresentation | str) -> None:
        if isinstance(presentation, str):
            primary, details = presentation, ""
        else:
            primary = presentation.primary
            details = presentation.technical_details
        self.primary.setText(primary)
        self.primary.setAccessibleDescription(primary)
        self.details.setText(details)
        self.details.setVisible(False)
        self.toggle.blockSignals(True)
        self.toggle.setChecked(False)
        self.toggle.blockSignals(False)
        self.toggle.setText("View technical details")
        self.toggle.setVisible(bool(details))
        self.setVisible(True)
        self.visibilityChanged.emit(True)

    def clear_message(self) -> None:
        self.primary.clear()
        self.details.clear()
        self.details.setVisible(False)
        self.toggle.setVisible(False)
        self.setVisible(False)
        self.visibilityChanged.emit(False)

    def _toggle(self, expanded: bool) -> None:
        self.details.setVisible(expanded)
        self.toggle.setText(
            "Hide technical details" if expanded else "View technical details"
        )
        self.toggle.setAccessibleName(self.toggle.text())
