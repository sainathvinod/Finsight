"""Theme-aware, application-owned dialogs for governed desktop actions."""
from __future__ import annotations

import weakref
from enum import Enum

from PySide6.QtCore import QEvent, QTimer, Qt
from PySide6.QtGui import QKeyEvent, QShowEvent
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
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


class DialogVariant(str, Enum):
    """Stable semantic variants for FinSight-owned dialog surfaces."""

    INFORMATION = "information"
    WARNING = "warning"
    ERROR = "error"
    CONFIRMATION = "confirmation"
    PROTECTED = "protected"


_VARIANT_PRESENTATION = {
    DialogVariant.INFORMATION: ("i", "Information", "statusPill"),
    DialogVariant.WARNING: ("!", "Warning", "warning"),
    DialogVariant.ERROR: ("!", "Error", "error"),
    DialogVariant.CONFIRMATION: ("✓", "Confirmation", "success"),
    DialogVariant.PROTECTED: ("◆", "Protected control", "warning"),
}


class InAppDialog(QDialog):
    """Reusable frameless dialog that remains owned by the FinSight window.

    The global FinSight stylesheet supplies the active light, dark, system, or
    high-contrast palette. This component supplies an internal title bar so the
    operating system never adds a native title bar or macOS traffic lights.
    """

    def __init__(
        self,
        title: str,
        message: str = "",
        *,
        variant: DialogVariant | str = DialogVariant.INFORMATION,
        parent: QWidget | None = None,
        object_name: str = "InAppDialog",
        minimum_width: int = 520,
    ) -> None:
        application = QApplication.instance()
        initial_focus = QApplication.focusWidget()
        owner = parent
        if owner is None and application is not None:
            active_window = application.activeWindow()
            owner = active_window if isinstance(active_window, QWidget) else None
        super().__init__(owner)

        self.variant = DialogVariant(variant)
        self._previous_focus: weakref.ReferenceType[QWidget] | None = (
            weakref.ref(initial_focus)
            if isinstance(initial_focus, QWidget)
            else None
        )
        self._safe_focus: QWidget | None = None
        self._focus_restored = False

        self.setObjectName(object_name)
        self.setWindowTitle(title)
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint)
        self.setWindowModality(Qt.WindowModality.WindowModal)
        self.setModal(True)
        self.setMinimumWidth(minimum_width)
        self.setProperty("dialogVariant", self.variant.value)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setAccessibleName(f"{self.semantic_name} dialog: {title}")
        self.setAccessibleDescription(message or f"{self.semantic_name}: {title}")

        root = QVBoxLayout(self)
        root.setContentsMargins(t.SP_2, t.SP_2, t.SP_2, t.SP_2)
        root.setSpacing(0)

        self.surface = QFrame()
        self.surface.setObjectName("InAppDialogSurface")
        self.surface.setProperty("role", "surfaceCard")
        self.surface.setProperty("dialogVariant", self.variant.value)
        root.addWidget(self.surface)

        surface_layout = QVBoxLayout(self.surface)
        surface_layout.setContentsMargins(t.SP_5, t.SP_5, t.SP_5, t.SP_5)
        surface_layout.setSpacing(t.SP_3)

        title_row = QHBoxLayout()
        title_row.setSpacing(t.SP_2)
        glyph, semantic_name, semantic_role = _VARIANT_PRESENTATION[self.variant]
        self.semantic_badge = _label(
            f"{glyph} {semantic_name}", semantic_role, wrap=False
        )
        self.semantic_badge.setObjectName("InAppDialogSemanticBadge")
        self.semantic_badge.setAccessibleName(f"Dialog type: {semantic_name}")
        title_row.addWidget(self.semantic_badge, 0, Qt.AlignmentFlag.AlignTop)

        self.title_label = _label(title, "sectionHeader")
        self.title_label.setObjectName("InAppDialogTitle")
        self.title_label.setAccessibleName(f"Dialog title: {title}")
        title_row.addWidget(self.title_label, 1)

        self.close_button = QPushButton("×")
        self.close_button.setObjectName("InAppDialogCloseButton")
        self.close_button.setProperty("role", "quiet")
        self.close_button.setAccessibleName(f"Close {title}")
        self.close_button.setAccessibleDescription(
            "Close this dialog without applying the action."
        )
        self.close_button.setAutoDefault(False)
        self.close_button.setDefault(False)
        self.close_button.setFixedWidth(36)
        self.close_button.clicked.connect(self.reject)
        title_row.addWidget(self.close_button, 0, Qt.AlignmentFlag.AlignTop)
        surface_layout.addLayout(title_row)

        self.message_label = _label(message, "sectionSub")
        self.message_label.setObjectName("InAppDialogMessage")
        self.message_label.setAccessibleName("Dialog explanation")
        self.message_label.setVisible(bool(message))
        surface_layout.addWidget(self.message_label)

        self.content = QWidget()
        self.content.setObjectName("InAppDialogContent")
        self.content_layout = QVBoxLayout(self.content)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(t.SP_3)
        surface_layout.addWidget(self.content)

        self.actions = QWidget()
        self.actions.setObjectName("InAppDialogActions")
        self.actions_layout = QHBoxLayout(self.actions)
        self.actions_layout.setContentsMargins(0, 0, 0, 0)
        self.actions_layout.setSpacing(t.SP_2)
        self.actions_layout.addStretch(1)
        surface_layout.addWidget(self.actions)

        self.set_safe_focus(self.close_button)

    @property
    def semantic_name(self) -> str:
        """Plain-language semantic name, independent of color."""

        return _VARIANT_PRESENTATION[self.variant][1]

    def add_action(
        self,
        text: str,
        *,
        role: str = "secondary",
        accessible_name: str | None = None,
        accessible_description: str | None = None,
        accept: bool = False,
        reject: bool = False,
        default: bool = False,
    ) -> QPushButton:
        """Add a keyboard-accessible action to the internal action row."""

        if accept and reject:
            raise ValueError("A dialog action cannot both accept and reject.")
        button = QPushButton(text)
        button.setProperty("role", role)
        button.setAccessibleName(accessible_name or text)
        if accessible_description:
            button.setAccessibleDescription(accessible_description)
        button.setAutoDefault(default)
        button.setDefault(default)
        if accept:
            button.clicked.connect(self.accept)
        elif reject:
            button.clicked.connect(self.reject)
        self.actions_layout.addWidget(button)
        return button

    def set_safe_focus(self, widget: QWidget) -> None:
        """Choose the non-destructive control focused when the dialog opens."""

        if not self.isAncestorOf(widget):
            raise ValueError("Safe focus must belong to this dialog.")
        self._safe_focus = widget

    def showEvent(self, event: QShowEvent) -> None:  # noqa: N802 - Qt API
        focus = QApplication.focusWidget()
        if (
            self._previous_focus is None
            and focus is not None
            and focus is not self
            and not self.isAncestorOf(focus)
        ):
            self._previous_focus = weakref.ref(focus)
        self._focus_restored = False
        super().showEvent(event)
        if self._safe_focus is not None and self._safe_focus.isEnabled():
            self._safe_focus.setFocus(Qt.FocusReason.OtherFocusReason)

    def keyPressEvent(self, event: QKeyEvent) -> None:  # noqa: N802 - Qt API
        if event.key() == Qt.Key.Key_Escape:
            event.accept()
            self.reject()
            return
        super().keyPressEvent(event)

    def done(self, result: int) -> None:
        """Close and return keyboard focus to the invoking control."""

        super().done(result)
        if self._focus_restored:
            return
        self._focus_restored = True
        previous_focus = self._previous_focus

        def restore_focus() -> None:
            target = previous_focus() if previous_focus is not None else None
            if target is None:
                return
            try:
                if target.isEnabled() and target.isVisible():
                    owner_window = target.window()
                    if owner_window is not None:
                        owner_window.activateWindow()
                    target.setFocus(Qt.FocusReason.OtherFocusReason)
            except RuntimeError:
                # The invoking page may have been destroyed while the modal was open.
                return

        QTimer.singleShot(0, restore_focus)

    def changeEvent(self, event: QEvent) -> None:  # noqa: N802 - Qt API
        """Let application-wide theme changes restyle an open dialog."""

        super().changeEvent(event)
        if event.type() in {
            QEvent.Type.ApplicationPaletteChange,
            QEvent.Type.PaletteChange,
            QEvent.Type.StyleChange,
        }:
            # Qt can deliver a style event from ``setWindowFlags`` while the
            # constructor is still building the internal surface. Theme
            # application must therefore tolerate this early lifecycle event.
            surface = getattr(self, "surface", None)
            if surface is not None:
                surface.style().unpolish(surface)
                surface.style().polish(surface)


class InAppMessageDialog(InAppDialog):
    """Concise semantic notice or confirmation without a native message box."""

    def __init__(
        self,
        title: str,
        message: str,
        *,
        variant: DialogVariant | str = DialogVariant.INFORMATION,
        parent: QWidget | None = None,
        accept_text: str = "OK",
        cancel_text: str | None = None,
        accept_role: str = "primary",
        accept_accessible_name: str | None = None,
    ) -> None:
        super().__init__(title, message, variant=variant, parent=parent)
        self.cancel_button: QPushButton | None = None
        if cancel_text:
            self.cancel_button = self.add_action(
                cancel_text,
                role="secondary",
                accessible_name=f"{cancel_text}: close without applying the action",
                reject=True,
                default=True,
            )
            self.set_safe_focus(self.cancel_button)
        self.accept_button = self.add_action(
            accept_text,
            role=accept_role,
            accessible_name=accept_accessible_name or accept_text,
            accept=True,
            default=not bool(cancel_text),
        )
        if self.cancel_button is None:
            self.set_safe_focus(self.accept_button)


class InAppTextPromptDialog(InAppDialog):
    """Theme-aware text prompt for short, attributable user rationale."""

    def __init__(
        self,
        title: str,
        prompt: str,
        *,
        parent: QWidget | None = None,
        placeholder: str = "",
        accept_text: str = "Continue",
        variant: DialogVariant | str = DialogVariant.CONFIRMATION,
        required_message: str = "Enter a value before continuing.",
        maximum_length: int = 500,
    ) -> None:
        super().__init__(
            title,
            prompt,
            variant=variant,
            parent=parent,
            object_name="InAppTextPromptDialog",
            minimum_width=560,
        )
        self._required_message = required_message
        self._maximum_length = maximum_length
        self.editor = QPlainTextEdit()
        self.editor.setObjectName("InAppTextPromptEditor")
        self.editor.setAccessibleName(prompt)
        self.editor.setAccessibleDescription(
            f"Required text response; maximum {maximum_length} characters."
        )
        self.editor.setPlaceholderText(placeholder)
        self.editor.setMaximumHeight(120)
        self.editor.textChanged.connect(self._enforce_maximum_length)
        self.content_layout.addWidget(self.editor)
        self.error_label = _label("", "error")
        self.error_label.setAccessibleName("Text prompt validation error")
        self.error_label.setVisible(False)
        self.content_layout.addWidget(self.error_label)
        self.cancel_button = self.add_action(
            "Cancel",
            role="secondary",
            accessible_name=f"Cancel {title}",
            reject=True,
            default=True,
        )
        self.accept_button = self.add_action(
            accept_text,
            role="primary",
            accessible_name=accept_text,
        )
        self.accept_button.clicked.connect(self._validate_and_accept)
        self.set_safe_focus(self.cancel_button)

    def _enforce_maximum_length(self) -> None:
        text = self.editor.toPlainText()
        if len(text) <= self._maximum_length:
            return
        cursor = self.editor.textCursor()
        position = min(cursor.position(), self._maximum_length)
        self.editor.blockSignals(True)
        self.editor.setPlainText(text[: self._maximum_length])
        cursor = self.editor.textCursor()
        cursor.setPosition(position)
        self.editor.setTextCursor(cursor)
        self.editor.blockSignals(False)

    def _validate_and_accept(self) -> None:
        if not self.text_value():
            self.error_label.setText(self._required_message)
            self.error_label.setVisible(True)
            self.editor.setFocus(Qt.FocusReason.OtherFocusReason)
            return
        self.accept()

    def text_value(self) -> str:
        """Return the trimmed user response."""

        return self.editor.toPlainText().strip()


def show_in_app_message(
    parent: QWidget | None,
    title: str,
    message: str,
    *,
    variant: DialogVariant | str = DialogVariant.INFORMATION,
    accept_text: str = "OK",
) -> int:
    """Show one application-owned semantic notice and return its result."""

    return InAppMessageDialog(
        title,
        message,
        variant=variant,
        parent=parent,
        accept_text=accept_text,
    ).exec()


class GovernedSaveDialog(InAppDialog):
    """Require explicit understanding before reviewed values become authoritative."""

    def __init__(self, change_count: int, parent: QWidget | None = None):
        super().__init__(
            "Save these changes?",
            "Validation results will be calculated using the edited values. "
            "The original values will remain preserved, and all changes will "
            "be recorded in the audit history.",
            variant=DialogVariant.CONFIRMATION,
            parent=parent,
            object_name="GovernedSaveDialog",
            minimum_width=560,
        )
        self.content_layout.addWidget(
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
        self.content_layout.addWidget(self.acknowledgment)
        self.cancel_button = self.add_action(
            "Cancel",
            role="secondary",
            accessible_name="Cancel saving reviewed-data changes",
            reject=True,
            default=True,
        )
        self.save_button = self.add_action(
            "Save Changes",
            role="primary",
            accessible_name="Save acknowledged reviewed-data changes",
            accept=True,
        )
        self.save_button.setEnabled(False)
        self.acknowledgment.toggled.connect(self.save_button.setEnabled)
        self.set_safe_focus(self.cancel_button)


class DeleteReviewDialog(InAppDialog):
    """Irreversible review-disposal confirmation with a disabled safe default."""

    def __init__(self, period_label: str, parent: QWidget | None = None):
        super().__init__(
            "Permanently delete this review?",
            "This will permanently delete the review, its working data, edits, "
            "validation runs, findings, and audit history from this FinSight "
            "installation. This action cannot be undone.",
            variant=DialogVariant.WARNING,
            parent=parent,
            object_name="DeleteReviewDialog",
            minimum_width=600,
        )
        self.content_layout.addWidget(
            _label(f"Review: {period_label}", "cardDetail")
        )
        self.acknowledgment = QCheckBox(
            "I understand this action cannot be undone."
        )
        self.acknowledgment.setAccessibleName(
            "Acknowledge permanent review deletion"
        )
        self.content_layout.addWidget(self.acknowledgment)
        self.cancel_button = self.add_action(
            "Cancel",
            role="secondary",
            accessible_name="Cancel permanent review deletion",
            reject=True,
            default=True,
        )
        self.delete_button = self.add_action(
            "Permanently Delete",
            role="danger",
            accessible_name="Permanently delete the selected review",
            accept=True,
        )
        self.delete_button.setEnabled(False)
        self.acknowledgment.toggled.connect(self.delete_button.setEnabled)
        self.set_safe_focus(self.cancel_button)
