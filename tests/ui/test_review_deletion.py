import pytest
from PySide6.QtWidgets import QDialog

import finsight.delivery.desktop.views.review_management_view as management_view

from finsight.delivery.desktop.components import DeleteReviewDialog


pytestmark = pytest.mark.ui


def test_past_review_delete_uses_governed_confirmation_and_refreshes(
    window_factory, empty_db, qtbot, monkeypatch
):
    window = window_factory(empty_db)
    controller = window._c
    review = controller.create_managed_review(
        5, 2026, "ui-delete-review"
    )
    management = window.view("review_management")
    management.show_past()

    monkeypatch.setattr(
        DeleteReviewDialog,
        "exec",
        lambda _dialog: QDialog.DialogCode.Accepted,
    )
    monkeypatch.setattr(
        management_view,
        "show_in_app_message",
        lambda *_args, **_kwargs: QDialog.DialogCode.Accepted,
    )
    management._delete_review(review)

    assert controller.managed_reviews() == []
    assert controller.active_review_id is None
    assert management.current_screen() == "past_reviews"
    assert management._past_cards == []
