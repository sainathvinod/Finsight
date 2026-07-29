"""Governed confirmation dialogs for material review actions."""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from finsight.delivery.desktop.theme import tokens as t


def _label(text: str, role: str, *, wrap: bool = True) -> QLabel:
    label = QLabel(text)
    label.setProperty("role", role)
    label.setWordWrap(wrap)
    return label


class GovernedSaveDialog(QDialog):
    """Require explicit understanding before reviewed values become authoritative."""

    def __init__(self, change_count: int, parent: QWidget | None = None):
        super().__init__(parent)
        self.setObjectName("GovernedSaveDialog")
        self.setWindowTitle("Save these changes?")
        self.setModal(True)
        self.setMinimumWidth(560)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(t.SP_5, t.SP_5, t.SP_5, t.SP_5)
        layout.setSpacing(t.SP_3)
        layout.addWidget(_label("Save these changes?", "sectionHeader"))
        layout.addWidget(
            _label(
                "Validation results will be calculated using the edited values. "
                "The original values will remain preserved, and all changes will "
                "be recorded in the audit history.",
                "sectionSub",
            )
        )
        layout.addWidget(
            _label(
                f"{change_count} reviewed value "
                f"{'change is' if change_count == 1 else 'changes are'} ready to save.",
                "cardDetail",
            )
        )
        self.acknowledgment = QCheckBox(
            "I understand that validation will use these edited values."
        )
        self.acknowledgment.setAccessibleName(
            "Acknowledge use of edited values for validation"
        )
        layout.addWidget(self.acknowledgment)
        actions = QHBoxLayout()
        actions.addStretch(1)
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.setProperty("role", "secondary")
        self.cancel_button.setAccessibleName(
            "Cancel saving reviewed-data changes"
        )
        self.cancel_button.clicked.connect(self.reject)
        actions.addWidget(self.cancel_button)
        self.save_button = QPushButton("Save Changes")
        self.save_button.setProperty("role", "primary")
        self.save_button.setAccessibleName(
            "Save acknowledged reviewed-data changes"
        )
        self.save_button.setEnabled(False)
        self.save_button.clicked.connect(self.accept)
        actions.addWidget(self.save_button)
        layout.addLayout(actions)
        self.acknowledgment.toggled.connect(self.save_button.setEnabled)
        self.cancel_button.setFocus(Qt.FocusReason.OtherFocusReason)


class DeleteReviewDialog(QDialog):
    """Irreversible review-disposal confirmation with a disabled safe default."""

    def __init__(self, period_label: str, parent: QWidget | None = None):
        super().__init__(parent)
        self.setObjectName("DeleteReviewDialog")
        self.setWindowTitle("Permanently delete this review?")
        self.setModal(True)
        self.setMinimumWidth(600)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(t.SP_5, t.SP_5, t.SP_5, t.SP_5)
        layout.setSpacing(t.SP_3)
        layout.addWidget(
            _label("Permanently delete this review?", "sectionHeader")
        )
        layout.addWidget(
            _label(
                "This will permanently delete the review, its working data, edits, "
                "validation runs, findings, and audit history from this FinSight "
                "installation. This action cannot be undone.",
                "sectionSub",
            )
        )
        layout.addWidget(_label(f"Review: {period_label}", "cardDetail"))
        self.acknowledgment = QCheckBox(
            "I understand this action cannot be undone."
        )
        self.acknowledgment.setAccessibleName(
            "Acknowledge permanent review deletion"
        )
        layout.addWidget(self.acknowledgment)
        actions = QHBoxLayout()
        actions.addStretch(1)
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.setProperty("role", "secondary")
        self.cancel_button.setAccessibleName(
            "Cancel permanent review deletion"
        )
        self.cancel_button.clicked.connect(self.reject)
        actions.addWidget(self.cancel_button)
        self.delete_button = QPushButton("Permanently Delete")
        self.delete_button.setProperty("role", "destructive")
        self.delete_button.setAccessibleName(
            "Permanently delete the selected review"
        )
        self.delete_button.setEnabled(False)
        self.delete_button.clicked.connect(self.accept)
        actions.addWidget(self.delete_button)
        layout.addLayout(actions)
        self.acknowledgment.toggled.connect(self.delete_button.setEnabled)
        self.cancel_button.setFocus(Qt.FocusReason.OtherFocusReason)
