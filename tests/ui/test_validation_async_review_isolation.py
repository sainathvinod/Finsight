from __future__ import annotations

from types import SimpleNamespace

import pytest

import finsight.delivery.desktop.controllers.app_controller as controller_module
from finsight.delivery.desktop.controllers.app_controller import AppController
from finsight.delivery.desktop.views.financial_review_view import (
    FinancialReviewView,
)


pytestmark = pytest.mark.ui


class _FinancialReviewService:
    def __init__(self):
        self.persisted: list[tuple[str, object]] = []
        self.failures: list[tuple[str, BaseException]] = []

    def start_validation_attempt(self, confirmation_id, dataset):
        return {
            "confirmation_id": confirmation_id,
            "review_id": dataset.review_id,
        }

    def timestamp(self):
        return "2026-07-31T12:00:00Z"

    def evaluate_manifest(self, dataset, manifest):
        return {
            "review_id": dataset.review_id,
            "confirmation_id": manifest["confirmation_id"],
        }

    def persist_evaluation(
        self,
        review_id,
        _dataset,
        evaluation,
        *,
        confirmation_id,
        started_at,
    ):
        assert confirmation_id == "confirmation-review-a"
        assert started_at == "2026-07-31T12:00:00Z"
        self.persisted.append((review_id, evaluation))
        return {"run_id": "run-review-a", "review_id": review_id}

    def record_validation_failure(self, confirmation_id, error):
        self.failures.append((confirmation_id, error))


def test_async_validation_persists_origin_review_but_suppresses_stale_ui_callback(
    qtbot, monkeypatch
):
    service = _FinancialReviewService()
    services = SimpleNamespace(
        financial_review=service,
        identity_resolution=None,
    )
    controller = AppController(services)
    controller.select_review("review-a")
    pending = {}

    def capture_async(work, done, failed):
        pending.update(work=work, done=done, failed=failed)
        return object()

    monkeypatch.setattr(controller_module, "run_async", capture_async)
    delivered_results = []
    delivered_errors = []
    changed_reviews = []
    processing_states = []
    controller.financialReviewChanged.connect(changed_reviews.append)
    controller.processingChanged.connect(processing_states.append)

    controller.validate_financial_async(
        SimpleNamespace(review_id="review-a"),
        lambda _stage: None,
        delivered_results.append,
        delivered_errors.append,
        confirmation_id="confirmation-review-a",
    )

    controller.select_review("review-b")
    pending["done"](pending["work"]())

    assert service.persisted == [
        (
            "review-a",
            {
                "review_id": "review-a",
                "confirmation_id": "confirmation-review-a",
            },
        )
    ]
    assert changed_reviews == ["review-a"]
    assert processing_states == [True, False]
    assert delivered_results == []
    assert delivered_errors == []
    assert controller.active_review_id == "review-b"


class _ViewController:
    def __init__(self):
        self.active_review_id = "review-a"
        self.done = None
        self.failed = None

    def audit_timeline(self, _review_id):
        # The results workspace hosts the audit trail tab; this stub has no recorded trail.
        return []

    def validate_financial_async(
        self,
        _dataset,
        _on_progress,
        on_result,
        on_error,
        *,
        confirmation_id,
    ):
        assert confirmation_id == "confirmation-review-a"
        self.done = on_result
        self.failed = on_error


def _review(review_id: str):
    return SimpleNamespace(
        review_id=review_id,
        period=SimpleNamespace(label="May 2026"),
        status=SimpleNamespace(value="Validation Complete"),
    )


def test_financial_review_view_ignores_callback_bound_to_previous_review(qtbot):
    controller = _ViewController()
    view = FinancialReviewView(controller)
    qtbot.addWidget(view)
    view._review = _review("review-a")
    view._dataset = SimpleNamespace(review_id="review-a")
    prior_projection = {"run_id": "prior-review-a-run"}
    view._projection = prior_projection

    view._start_validation(
        {"confirmation_id": "confirmation-review-a", "rules": ()}
    )

    controller.active_review_id = "review-b"
    view._review = _review("review-b")
    controller.done({"run_id": "new-review-a-run"})

    assert view._projection is prior_projection
    assert not view._validation_finished
