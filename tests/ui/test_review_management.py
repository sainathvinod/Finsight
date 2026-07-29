# Verifies: Workflow 1 Review Management UI — welcome, creation, persistence, past reviews, reopen.
import pytest
from PySide6.QtCore import QSize, Qt
from PySide6.QtWidgets import QLabel, QWidget

from finsight.delivery.desktop.components import ReviewProgress

pytestmark = pytest.mark.ui


def test_empty_welcome_is_the_launch_surface_and_disables_past_reviews(
    window_factory, empty_db
):
    window = window_factory(empty_db)
    view = window.view("review_management")

    assert window.current_view_key() == "welcome"
    assert view.welcome_title() == "FinSight"
    assert view._create_button.isEnabled()
    assert not view.past_reviews_enabled()
    assert "No previous reviews" in view._past_button.accessibleDescription()


def test_month_and_year_are_required_before_review_creation(
    window_factory, empty_db, qtbot
):
    window = window_factory(empty_db)
    window.show()
    view = window.view("review_management")
    qtbot.mouseClick(view._create_button, Qt.MouseButton.LeftButton)
    assert view.current_screen() == "create"

    qtbot.mouseClick(view._create_submit, Qt.MouseButton.LeftButton)
    assert view._create_error.isVisible()
    assert view._create_error.text() == "Please enter the required month and year."


def test_create_review_shows_saved_draft_and_no_financial_claims(
    window_factory, empty_db, qtbot
):
    window = window_factory(empty_db)
    window.show()
    view = window.view("review_management")
    qtbot.mouseClick(view._create_button, Qt.MouseButton.LeftButton)
    view._month.setCurrentIndex(view._month.findData(5))
    view._year.setText("2026")
    assert view._period_preview.text() == "Reporting period: May 2026"

    qtbot.mouseClick(view._create_submit, Qt.MouseButton.LeftButton)

    assert view.current_screen() == "review_workspace"
    assert view.current_review_id().startswith("rev_")
    assert view._review_period.text() == "May 2026"
    assert view._review_status.text() == "Draft"
    assert view._review_disposition.text() == "Active"
    assert view._publication_status.text() == "Not created"
    assert "validation has not run" in view._financial_status.text()
    assert "safely close" in view._saved_message.text()


def test_saved_review_survives_window_recreation_and_reopens_by_opaque_id(
    window_factory, empty_db, qtbot
):
    first = window_factory(empty_db)
    first.show()
    first_view = first.view("review_management")
    first_view.show_create()
    first_view._month.setCurrentIndex(first_view._month.findData(12))
    first_view._year.setText("2027")
    qtbot.mouseClick(first_view._create_submit, Qt.MouseButton.LeftButton)
    review_id = first_view.current_review_id()
    first.close()

    reopened = window_factory(empty_db)
    reopened.show()
    view = reopened.view("review_management")
    assert view.past_reviews_enabled()
    qtbot.mouseClick(view._past_button, Qt.MouseButton.LeftButton)
    assert view.current_screen() == "past_reviews"
    assert view.past_review_ids() == [review_id]

    qtbot.mouseClick(view._past_cards[0].open_button, Qt.MouseButton.LeftButton)
    assert view.current_screen() == "review_workspace"
    assert view.current_review_id() == review_id
    assert view._review_period.text() == "December 2027"


def test_past_review_status_filter_and_back_navigation(
    window_factory, empty_db, qtbot
):
    window = window_factory(empty_db)
    window.show()
    view = window.view("review_management")
    view.show_create()
    view._month.setCurrentIndex(view._month.findData(1))
    view._year.setText("2028")
    qtbot.mouseClick(view._create_submit, Qt.MouseButton.LeftButton)
    view.show_past()

    draft_index = view._status_filter.findText("Draft")
    view._status_filter.setCurrentIndex(draft_index)
    assert len(view.past_review_ids()) == 1

    closed_index = view._status_filter.findText("Closed")
    view._status_filter.setCurrentIndex(closed_index)
    assert view.past_review_ids() == []

    view._past_back.setFocus()
    qtbot.keyClick(view._past_back, Qt.Key.Key_Space)
    assert view.current_screen() == "welcome"


def test_keyboard_actions_reach_create_and_past_reviews(
    window_factory, empty_db, qtbot
):
    window = window_factory(empty_db)
    window.show()
    window.activateWindow()
    view = window.view("review_management")
    view._create_button.setFocus()
    qtbot.keyClick(view._create_button, Qt.Key.Key_Space)
    assert view.current_screen() == "create"
    view._create_back.setFocus()
    qtbot.keyClick(view._create_back, Qt.Key.Key_Space)
    assert view.current_screen() == "welcome"

    view.show_create()
    view._month.setCurrentIndex(view._month.findData(3))
    view._year.setText("2026")
    qtbot.mouseClick(view._create_submit, Qt.MouseButton.LeftButton)
    view.show_welcome()
    view._past_button.setFocus()
    qtbot.keyClick(view._past_button, Qt.Key.Key_Space)
    assert view.current_screen() == "past_reviews"


def test_existing_reporting_period_warns_without_blocking_separate_review(
    window_factory, empty_db, qtbot
):
    window = window_factory(empty_db)
    window.show()
    view = window.view("review_management")
    view.show_create()
    view._month.setCurrentIndex(view._month.findData(5))
    view._year.setText("2026")
    qtbot.mouseClick(view._create_submit, Qt.MouseButton.LeftButton)

    window.show_review_management()
    view.show_create()
    view._month.setCurrentIndex(view._month.findData(5))
    view._year.setText("2026")

    assert view._duplicate_warning.isVisible()
    assert "already use this reporting period" in view._duplicate_warning.text()
    assert view._create_submit.isEnabled()


def test_unexpected_create_error_uses_safe_cataloged_diagnostic_contract(
    window_factory, empty_db, qtbot, monkeypatch
):
    window = window_factory(empty_db)
    window.show()
    view = window.view("review_management")
    view.show_create()
    view._month.setCurrentIndex(view._month.findData(5))
    view._year.setText("2026")

    def unsafe_failure(*_args, **_kwargs):
        raise RuntimeError("/private/secret.db salary=100000")

    monkeypatch.setattr(view._c, "create_managed_review", unsafe_failure)
    qtbot.mouseClick(view._create_submit, Qt.MouseButton.LeftButton)

    message = view._create_error.text()
    assert message == (
        "FinSight could not complete the requested action. "
        "Try the action once more. If it still does not work, "
        "contact FinSight support."
    )
    assert "FS-SYS-001" not in message
    assert "Correlation ID:" not in message
    assert "/private/secret.db" not in message
    assert "salary" not in message


def test_desktop_landing_matches_the_approved_hierarchy_and_has_no_recent_section(
    window_factory, empty_db, qtbot
):
    window = window_factory(empty_db)
    window.resize(1180, 720)
    window.show()
    view = window.view("review_management")
    qtbot.waitUntil(view.shell_visible)
    qtbot.waitUntil(view.action_cards_side_by_side)

    assert view._home_nav.isChecked()
    assert not view._reviews_nav.isChecked()
    assert view._ask_fin_nav.isVisibleTo(view)
    assert view._ask_fin_nav.isEnabled()
    assert view._ask_fin_button.isVisibleTo(view)
    assert view._ask_fin_button.isEnabled()
    assert view._create_action_card.y() == view._past_action_card.y()
    assert view._create_action_card.x() < view._past_action_card.x()
    assert view._create_action_card.size() == view._past_action_card.size()
    assert view._welcome_title.text() == "FinSight"
    assert (
        view._welcome_subtitle.text()
        == "Your Personal Financial Review Assistant"
    )
    assert view._welcome_description.text() == (
        "Create monthly financial reviews, validate Budget and GED reports, "
        "identify exceptions early, and generate leadership-ready insights "
        "through one guided workflow."
    )
    assert (
        view._create_action_card._landing_description.text()
        == "Start a new monthly financial review."
    )
    assert (
        view._past_action_card._landing_description.text()
        == "Open and continue a previous review."
    )
    visible_labels = [
        label.text()
        for label in view.findChildren(QLabel)
        if label.isVisibleTo(view)
    ]
    assert "Recent Reviews" not in visible_labels
    assert "NEW MONTHLY REVIEW" not in visible_labels
    assert "SAVED WORK" not in visible_labels
    assert not view._shell_crumb.isVisibleTo(view)
    assert not view._shell_context.isVisibleTo(view)


def test_landing_uses_compact_desktop_scale_without_changing_its_structure(
    window_factory, empty_db, qtbot
):
    window = window_factory(empty_db)
    window.resize(1280, 900)
    window.show()
    view = window.view("review_management")
    qtbot.waitUntil(view.action_cards_side_by_side)
    qtbot.waitUntil(lambda: view._action_holder.width() == 760)

    assert view._welcome_title.font().pointSizeF() <= 74
    assert view._welcome_subtitle.font().pointSizeF() <= 30
    assert view._welcome_description.font().pointSizeF() <= 18
    assert view._landing_top_spacer.geometry().height() <= 28
    assert view._action_holder.width() == 760
    assert 320 <= view._create_action_card.width() <= 380
    assert view._create_action_card.height() <= 270
    assert view._create_action_card._landing_badge.size() == QSize(60, 60)
    assert view._create_action_card.y() == view._past_action_card.y()


def test_saved_review_is_available_only_after_opening_past_reviews(
    window_factory, empty_db, qtbot
):
    window = window_factory(empty_db)
    window.resize(1180, 720)
    window.show()
    view = window.view("review_management")
    view.show_create()
    view._month.setCurrentIndex(view._month.findData(5))
    view._year.setText("2026")
    qtbot.mouseClick(view._create_submit, Qt.MouseButton.LeftButton)
    review_id = view.current_review_id()

    window.show_review_management()
    assert view.past_reviews_enabled()
    assert "May 2026" not in [
        label.text()
        for label in view._welcome_page.findChildren(QLabel)
        if label.isVisibleTo(view)
    ]
    qtbot.mouseClick(view._past_button, Qt.MouseButton.LeftButton)
    assert view.current_screen() == "past_reviews"
    assert view.past_review_ids() == [review_id]
    assert view._past_cards[0].open_button.text() == "Resume"
    qtbot.mouseClick(view._past_cards[0].open_button, Qt.MouseButton.LeftButton)

    assert view.current_screen() == "review_workspace"
    assert view.current_review_id() == review_id


def test_landing_sidebar_has_consistent_labeled_icons_and_no_identity_footer(
    window_factory, empty_db
):
    window = window_factory(empty_db)
    window.resize(1180, 720)
    window.show()
    view = window.view("review_management")

    items = (
        (view._home_nav, "Home"),
        (view._reviews_nav, "Past Reviews"),
        (view._rule_governance_nav, "Rule Governance"),
        (view._settings_nav, "Settings"),
        (view._ask_fin_nav, "Ask Fin"),
    )
    assert all(item.text() == label for item, label in items)
    assert all(item.accessibleName() == label for item, label in items)
    assert all(not item.icon().isNull() for item, _label in items)
    assert len({item.iconSize() for item, _label in items}) == 1
    assert all(
        widget.accessibleName() != "Authenticated account and roles"
        for widget in window.findChildren(QWidget)
    )
    assert all(
        not label.text().startswith("Signed in as")
        for label in window.findChildren(QLabel)
    )


def test_landing_sidebar_scales_with_desktop_width(
    window_factory, empty_db, qtbot
):
    window = window_factory(empty_db)
    window.resize(2048, 1104)
    window.show()
    view = window.view("review_management")
    qtbot.waitUntil(lambda: view._sidebar.width() == 330)
    assert view._home_nav.iconSize() == QSize(26, 26)

    window.resize(1180, 860)
    qtbot.waitUntil(lambda: view._sidebar.width() == 260)
    assert view._home_nav.iconSize() == QSize(22, 22)

    window.resize(940, 600)
    qtbot.waitUntil(lambda: view._sidebar.width() == 240)


def test_landing_actions_stack_only_at_narrow_desktop_width(
    window_factory, empty_db, qtbot
):
    window = window_factory(empty_db)
    window.resize(1180, 720)
    window.show()
    view = window.view("review_management")
    qtbot.waitUntil(view.action_cards_side_by_side)

    window.resize(980, 720)
    qtbot.waitUntil(lambda: not view.action_cards_side_by_side())
    qtbot.waitUntil(
        lambda: view._create_action_card.y() < view._past_action_card.y()
    )


def test_create_review_uses_step_progress_and_a_compact_form(
    window_factory, empty_db
):
    window = window_factory(empty_db)
    window.resize(1180, 720)
    window.show()
    view = window.view("review_management")
    view.show_create()

    assert view._shell_crumb.text() == "Create Review"
    assert isinstance(view._workflow_progress, ReviewProgress)
    assert "Create current" in view._workflow_progress.accessibleDescription()
    assert "Upload upcoming" in view._workflow_progress.accessibleDescription()
    assert view._create_form_card.maximumWidth() == 720
    assert view._create_form_card.width() < view._create_page.viewport().width()


def test_shell_navigation_remains_present_on_all_workflow1_surfaces(
    window_factory, empty_db, qtbot
):
    window = window_factory(empty_db)
    window.resize(1180, 720)
    window.show()
    view = window.view("review_management")
    assert view.shell_visible()

    view.show_create()
    assert view.shell_visible()

    view._month.setCurrentIndex(view._month.findData(6))
    view._year.setText("2026")
    qtbot.mouseClick(view._create_submit, Qt.MouseButton.LeftButton)
    assert view.shell_visible()
    assert view._reviews_nav.isChecked()

    view.show_past()
    assert view.shell_visible()
    assert view._shell_crumb.text() == "Past Reviews"
    assert view._reviews_nav.isChecked()
