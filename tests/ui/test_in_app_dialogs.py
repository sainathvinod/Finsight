"""Focused accessibility and keyboard tests for FinSight-owned dialogs."""
from __future__ import annotations

from pathlib import Path

import pytest
from PySide6.QtCore import Qt
from PySide6.QtTest import QSignalSpy
from PySide6.QtWidgets import QApplication, QPushButton, QVBoxLayout, QWidget

from finsight.delivery.desktop.components import (
    DeleteReviewDialog,
    DialogVariant,
    GovernedSaveDialog,
    InAppDialog,
    InAppMessageDialog,
    InAppTextPromptDialog,
)
from finsight.delivery.desktop.theme import (
    build_application_palette,
    build_qss,
    tokens,
)


pytestmark = [pytest.mark.ui, pytest.mark.accessibility]


def test_desktop_delivery_has_no_native_message_or_text_prompt_dialogs():
    desktop = Path(__file__).resolve().parents[2] / "src/finsight/delivery/desktop"
    sources = "\n".join(
        path.read_text(encoding="utf-8") for path in desktop.rglob("*.py")
    )

    assert "QMessageBox" not in sources
    assert "QInputDialog" not in sources
    assert "QDialog(" not in sources


@pytest.mark.parametrize(
    ("variant", "semantic_name"),
    [
        (DialogVariant.INFORMATION, "Information"),
        (DialogVariant.WARNING, "Warning"),
        (DialogVariant.ERROR, "Error"),
        (DialogVariant.CONFIRMATION, "Confirmation"),
        (DialogVariant.PROTECTED, "Protected control"),
    ],
)
def test_dialog_variants_are_frameless_themed_and_non_color_only(
    qtbot, variant, semantic_name
):
    owner = QWidget()
    qtbot.addWidget(owner)
    owner.show()

    dialog = InAppDialog(
        "Rule action",
        "A plain-language explanation.",
        variant=variant,
        parent=owner,
    )
    qtbot.addWidget(dialog)

    assert dialog.parentWidget() is owner
    assert dialog.isModal()
    assert dialog.windowFlags() & Qt.WindowType.FramelessWindowHint
    assert not dialog.windowFlags() & Qt.WindowType.WindowTitleHint
    assert dialog.property("dialogVariant") == variant.value
    assert dialog.surface.property("role") == "surfaceCard"
    assert semantic_name in dialog.semantic_badge.text()
    assert semantic_name in dialog.accessibleName()
    assert dialog.accessibleDescription() == "A plain-language explanation."
    assert dialog.close_button.accessibleName() == "Close Rule action"


@pytest.mark.parametrize("theme", [tokens.LIGHT, tokens.DARK])
def test_dialog_construction_is_safe_after_application_theme_is_active(
    qtbot, qapp, theme
):
    previous_stylesheet = qapp.styleSheet()
    previous_palette = qapp.palette()
    palette = build_application_palette(theme)
    qapp.setPalette(palette)
    qapp.setStyleSheet(build_qss(theme=theme, palette=palette))
    try:
        dialog = InAppDialog(
            "New validation run",
            "Confirm the exact active Rule Set.",
            variant=DialogVariant.CONFIRMATION,
        )
        qtbot.addWidget(dialog)
        dialog.show()

        assert dialog.isVisible()
        assert dialog.surface is not None
        assert dialog.semantic_badge.text().endswith("Confirmation")
    finally:
        qapp.setStyleSheet(previous_stylesheet)
        qapp.setPalette(previous_palette)


def test_escape_uses_safe_cancel_and_restores_invoking_focus(qtbot):
    owner = QWidget()
    layout = QVBoxLayout(owner)
    invoking_button = QPushButton("Open rules")
    layout.addWidget(invoking_button)
    qtbot.addWidget(owner)
    owner.show()
    owner.activateWindow()
    invoking_button.setFocus(Qt.FocusReason.OtherFocusReason)
    qtbot.waitUntil(lambda: QApplication.focusWidget() is invoking_button)

    dialog = InAppMessageDialog(
        "Confirm rule change",
        "This action creates a new rule version.",
        variant=DialogVariant.CONFIRMATION,
        parent=owner,
        accept_text="Create Version",
        cancel_text="Return to Rule",
    )
    qtbot.addWidget(dialog)
    rejected = QSignalSpy(dialog.rejected)
    dialog.show()
    qtbot.waitUntil(lambda: QApplication.focusWidget() is dialog.cancel_button)

    qtbot.keyClick(dialog, Qt.Key.Key_Escape)

    assert rejected.count() == 1
    assert not dialog.isVisible()
    qtbot.waitUntil(lambda: QApplication.focusWidget() is invoking_button)


def test_confirmation_default_is_safe_and_actions_support_keyboard(qtbot):
    owner = QWidget()
    qtbot.addWidget(owner)
    owner.show()
    dialog = InAppMessageDialog(
        "Protected core rule",
        "Normal users cannot disable this protected control.",
        variant=DialogVariant.PROTECTED,
        parent=owner,
        accept_text="Propose New Version",
        cancel_text="Return to Rule",
    )
    qtbot.addWidget(dialog)
    rejected = QSignalSpy(dialog.rejected)
    dialog.show()

    assert dialog.cancel_button is not None
    assert dialog.cancel_button.isDefault()
    assert not dialog.accept_button.isDefault()
    assert dialog.accept_button.accessibleName() == "Propose New Version"
    qtbot.keyClick(dialog.cancel_button, Qt.Key.Key_Return)
    assert rejected.count() == 1


def test_existing_governed_dialog_apis_use_safe_modern_base(qtbot):
    save_dialog = GovernedSaveDialog(2)
    delete_dialog = DeleteReviewDialog("May 2026")
    qtbot.addWidget(save_dialog)
    qtbot.addWidget(delete_dialog)

    assert isinstance(save_dialog, InAppDialog)
    assert isinstance(delete_dialog, InAppDialog)
    assert save_dialog.objectName() == "GovernedSaveDialog"
    assert delete_dialog.objectName() == "DeleteReviewDialog"
    assert save_dialog.cancel_button.isDefault()
    assert delete_dialog.cancel_button.isDefault()
    assert not save_dialog.save_button.isEnabled()
    assert not delete_dialog.delete_button.isEnabled()
    assert delete_dialog.delete_button.property("role") == "danger"

    save_dialog.acknowledgment.setChecked(True)
    delete_dialog.acknowledgment.setChecked(True)

    assert save_dialog.save_button.isEnabled()
    assert delete_dialog.delete_button.isEnabled()


def test_text_prompt_requires_auditable_value_and_remains_keyboard_safe(qtbot):
    dialog = InAppTextPromptDialog(
        "Update Finding Status",
        "Record the reason for this status change.",
        required_message="A reason is required.",
    )
    qtbot.addWidget(dialog)
    accepted = QSignalSpy(dialog.accepted)
    dialog.show()

    dialog.accept_button.click()

    assert accepted.count() == 0
    assert dialog.error_label.isVisibleTo(dialog)
    assert dialog.error_label.text() == "A reason is required."
    assert dialog.editor.accessibleName()
    assert dialog.cancel_button.isDefault()

    dialog.editor.setPlainText("Reviewer confirmed the source evidence.")
    dialog.accept_button.click()

    assert accepted.count() == 1
    assert dialog.text_value() == "Reviewer confirmed the source evidence."
