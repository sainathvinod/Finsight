"""Focused verification for the Stage 2 application-wide Back behavior."""

from __future__ import annotations

import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QPushButton


pytestmark = pytest.mark.ui


def _settle(qtbot) -> None:
    qtbot.wait(1)


def _create_review(window, qtbot) -> None:
    management = window.view("review_management")
    management.show_create()
    management._month.setCurrentIndex(management._month.findData(5))
    management._year.setText("2026")
    qtbot.mouseClick(
        management._create_submit, Qt.MouseButton.LeftButton
    )
    _settle(qtbot)


def test_header_back_is_consistent_visible_and_returns_to_landing(
    window_factory, empty_db, qtbot
):
    window = window_factory(empty_db)
    window.show()
    management = window.view("review_management")
    back = window.back_button("review_management")

    assert back is not None
    assert back.text() == "← Back"
    assert back.accessibleName() == "Back to previous FinSight page"
    assert not back.isVisibleTo(window)

    qtbot.mouseClick(management._create_button, Qt.MouseButton.LeftButton)
    _settle(qtbot)

    assert management.current_screen() == "create"
    assert back.isVisibleTo(window)
    assert window.can_go_back()
    visible_back_actions = [
        button
        for button in window.findChildren(QPushButton)
        if button.text().startswith("← Back")
        and button.isVisibleTo(window)
    ]
    assert visible_back_actions == [back]

    qtbot.mouseClick(back, Qt.MouseButton.LeftButton)

    assert management.current_screen() == "welcome"
    assert not back.isVisibleTo(window)


def test_global_back_preserves_past_review_filter_and_page_state(
    window_factory, empty_db, qtbot
):
    window = window_factory(empty_db)
    window.show()
    _create_review(window, qtbot)
    management = window.view("review_management")
    window._show_past_reviews()
    management._status_filter.setCurrentText("Draft")
    _settle(qtbot)

    window._show_settings()
    _settle(qtbot)
    assert window.current_view_key() == "settings"
    assert window.back_button("settings").isVisibleTo(window)

    window.go_back()

    assert window.current_view_key() == "past_reviews"
    assert management._status_filter.currentText() == "Draft"
    assert len(management.past_review_ids()) == 1


def test_back_from_upload_returns_to_saved_review_workspace(
    window_factory, empty_db, qtbot
):
    window = window_factory(empty_db)
    window.show()
    _create_review(window, qtbot)
    management = window.view("review_management")
    review_id = management.current_review_id()
    window._show_review_workspace()
    _settle(qtbot)
    assert window.current_view_key() == "review_workspace"

    qtbot.mouseClick(
        management._review_continue, Qt.MouseButton.LeftButton
    )
    _settle(qtbot)
    assert window.current_view_key() == "upload_extraction"
    assert window.back_button("source_intake").isVisibleTo(window)

    window.go_back()

    assert window.current_view_key() == "review_workspace"
    assert management.current_review_id() == review_id


def test_alt_left_uses_the_same_application_history(
    window_factory, empty_db, qtbot
):
    window = window_factory(empty_db)
    window.show()
    management = window.view("review_management")
    qtbot.mouseClick(management._create_button, Qt.MouseButton.LeftButton)
    _settle(qtbot)
    assert management.current_screen() == "create"

    window._global_back_shortcut.activated.emit()

    assert management.current_screen() == "welcome"
    assert management._create_button.hasFocus()
