from finsight.app import build_query_services
from finsight.domain.review_management import ReviewStatus
from finsight.domain.source_intake import SourceRole
from tests.support import FixedClock, persist_confirmed_validation


FIXTURES = "initiatives/configurable-rule-engine-v2/fixtures"


def test_integrated_review_persists_sealed_results_and_reopens(tmp_path):
    database_path = str(tmp_path / "finsight.db")
    services = build_query_services(database_path, clock=FixedClock())
    review = services.review_management.create_review(
        5, 2026, idempotency_key="create-may"
    )
    budget = services.source_intake.inspect(
        f"{FIXTURES}/Sample_Budget_Report.xlsx", SourceRole.BUDGET
    )
    ged = services.source_intake.inspect(
        f"{FIXTURES}/Sample_GED_Report.xlsx", SourceRole.GED
    )
    pair = services.source_intake.evaluate(
        budget=budget, ged=ged, selected_period=review.period
    )
    uploaded = services.review_management.commit_source_intake(
        review.review_id, pair, idempotency_key="sources-may"
    ).review
    assert uploaded.status is ReviewStatus.DATA_UPLOADED

    dataset = services.financial_review.reconstruct_dataset(review.review_id)
    confirmed = services.financial_review.confirm_reviewed_data(
        review.review_id,
        dataset,
        attestation_text="I reviewed the extracted Budget and GED data.",
    )
    assert confirmed.status is ReviewStatus.DATA_REVIEWED

    projection = persist_confirmed_validation(
        services.financial_review, review.review_id, dataset
    )
    assert projection["metrics"]["rule_results"] == 986
    assert len(projection["findings"]) == 5
    assert services.review_management.open_review(review.review_id).status is ReviewStatus.VALIDATION_COMPLETE

    completed = services.financial_review.complete_review(review.review_id)
    assert completed.status is ReviewStatus.CLOSED
    reopened = services.review_management.open_review(review.review_id)
    assert reopened.status is ReviewStatus.CLOSED
    saved = services.financial_review.results(review.review_id)
    assert saved["completion"]["run_id"] == saved["run_id"]
    assert saved["metrics"]["scope_passed"] == 979

    restarted = build_query_services(database_path, clock=FixedClock())
    reconstructed = restarted.financial_review.reconstruct_dataset(review.review_id)
    assert len(reconstructed.budget_details) == 71
    assert len(reconstructed.ged_transactions) == 258
    assert reconstructed.fingerprint == dataset.fingerprint


def test_review_local_correction_is_audited_reversible_and_never_changes_source(
    tmp_path,
):
    services = build_query_services(str(tmp_path / "edit.db"), clock=FixedClock())
    review = services.review_management.create_review(
        5, 2026, idempotency_key="create-edit"
    )
    budget = services.source_intake.inspect(
        f"{FIXTURES}/Sample_Budget_Report.xlsx", SourceRole.BUDGET
    )
    ged = services.source_intake.inspect(
        f"{FIXTURES}/Sample_GED_Report.xlsx", SourceRole.GED
    )
    pair = services.source_intake.evaluate(
        budget=budget, ged=ged, selected_period=review.period
    )
    services.review_management.commit_source_intake(
        review.review_id, pair, idempotency_key="sources-edit"
    )
    dataset = services.financial_review.reconstruct_dataset(review.review_id)
    row = next(item for item in dataset.ged_transactions if item.row_number == 87)
    assert row.original["amount"] is None

    services.financial_review.save_correction(
        review.review_id,
        dataset,
        record_id=row.record_id,
        field_name="amount",
        new_value="1700.00",
    )
    corrected = services.financial_review.reconstruct_dataset(review.review_id)
    corrected_row = next(
        item for item in corrected.ged_transactions if item.row_number == 87
    )
    assert corrected_row.original["amount"] is None
    assert corrected_row.current["amount"] == "1700.00"

    services.financial_review.save_correction(
        review.review_id,
        corrected,
        record_id=row.record_id,
        field_name="amount",
        new_value=None,
    )
    reverted = services.financial_review.reconstruct_dataset(review.review_id)
    reverted_row = next(
        item for item in reverted.ged_transactions if item.row_number == 87
    )
    assert reverted_row.original["amount"] is None
    assert reverted_row.current["amount"] is None
    history = services.financial_review.correction_history(review.review_id)
    assert [item["action"] for item in history] == ["EDIT", "REVERT"]
    assert all(item["actor_id"] for item in history)
