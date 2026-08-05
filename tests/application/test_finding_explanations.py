from __future__ import annotations

import copy

import pytest

from finsight.app import build_query_services
from finsight.domain.finding_explanations import FindingReviewStatus
from finsight.domain.source_intake import SourceRole
from tests.support import FixedClock, persist_confirmed_validation


FIXTURES = "initiatives/configurable-rule-engine-v2/fixtures"


def _validated_review(tmp_path):
    database = str(tmp_path / "finding-explanations.db")
    services = build_query_services(database, clock=FixedClock())
    review = services.review_management.create_review(
        5, 2026, idempotency_key="create-stage-2-explain"
    )
    budget = services.source_intake.inspect(
        f"{FIXTURES}/Sample_Budget_Report.xlsx", SourceRole.BUDGET
    )
    ged = services.source_intake.inspect(
        f"{FIXTURES}/Sample_GED_Report.xlsx", SourceRole.GED
    )
    pair = services.source_intake.evaluate(
        budget=budget,
        ged=ged,
        selected_period=review.period,
    )
    services.review_management.commit_source_intake(
        review.review_id,
        pair,
        idempotency_key="sources-stage-2-explain",
    )
    dataset = services.financial_review.reconstruct_dataset(review.review_id)
    services.financial_review.confirm_reviewed_data(
        review.review_id,
        dataset,
        attestation_text="Reviewed for deterministic explanations.",
    )
    projection = persist_confirmed_validation(
        services.financial_review,
        review.review_id,
        dataset,
    )
    return database, services, review, projection


def _finding(projection, rule_id):
    return next(
        item for item in projection["findings"] if item["rule_id"] == rule_id
    )


def test_all_five_core_findings_have_recorded_business_explanations(tmp_path):
    _database, services, review, projection = _validated_review(tmp_path)
    titles = {
        "CORE-01": "Account over budget",
        "CORE-02": "Unmapped GED transaction",
        "CORE-03": "Candidate duplicate transaction",
        "CORE-04": "Missing or invalid required GED value",
        "CORE-05": "Budget-to-GED mismatch",
    }

    assert {item["rule_id"] for item in projection["findings"]} == set(titles)
    for rule_id, title in titles.items():
        finding = _finding(projection, rule_id)
        explanation = services.financial_review.explain_finding(
            review.review_id, finding["finding_id"]
        )
        assert finding["business_title"] == title
        assert finding["review_status"] == "New"
        assert finding["review_required"] is True
        assert explanation["business_title"] == title
        assert explanation["ai_used"] is False
        assert explanation["authoritative_source"] == (
            "SEALED_DETERMINISTIC_VALIDATION_RUN"
        )
        assert explanation["technical_details_collapsed"] is True
        assert explanation["what_happened"]
        assert explanation["why_flagged"]
        assert explanation["why_it_matters"]
        assert explanation["recommended_next_step"]
        assert explanation["technical_details"]["rule_id"] == rule_id
        assert explanation["technical_details"]["rule_version"] == "2.0.0"
        assert explanation["technical_details"]["validation_run_id"] == (
            projection["run_id"]
        )
        assert explanation["technical_details"]["evidence_identifiers"]
        assert "should be changed" not in explanation[
            "recommended_next_step"
        ].lower()


def test_core_explanation_controls_match_the_independent_stage_1_oracle(
    tmp_path,
):
    _database, _services, _review, projection = _validated_review(tmp_path)

    overrun = _finding(projection, "CORE-01")["explain_this"]
    assert overrun["supporting_evidence"]["budget"] == "$1,100,000.00"
    assert overrun["supporting_evidence"]["ged_actual"] == "$1,250,000.00"
    assert overrun["supporting_evidence"]["variance"] == "$150,000.00"
    assert overrun["supporting_evidence"]["variance_percentage"] == "13.64%"
    assert [
        item["source_row"] for item in overrun["contributing_transactions"]
    ] == list(range(246, 290))
    assert overrun["contributing_transaction_control"] == {
        "transaction_count": 44,
        "parseable_amount_count": 44,
        "missing_or_invalid_amount_count": 0,
        "total_cents": 125_000_000,
        "total_label": "$1,250,000.00",
        "complete": True,
        "basis": (
            "Exact source records cited by the sealed finding; "
            "no uncited transaction is included."
        ),
    }
    assert sum(
        item["amount_cents"]
        for item in overrun["contributing_transactions"]
    ) == overrun["contributing_transaction_control"]["total_cents"]

    duplicate = _finding(projection, "CORE-03")["explain_this"]
    assert [
        item["source_row"]
        for item in duplicate["contributing_transactions"]
    ] == [65, 66]
    assert [
        item["amount_label"]
        for item in duplicate["contributing_transactions"]
    ] == ["$82.50", "$82.50"]
    assert duplicate["contributing_transaction_control"]["total_cents"] == 16_500
    assert "all 15" in duplicate["what_happened"]

    missing = _finding(projection, "CORE-04")["explain_this"]
    assert missing["supporting_evidence"]["lineage"][0]["row"] == 87
    assert missing["supporting_evidence"]["lineage"][0]["cell"] == "O87"
    assert missing["contributing_transactions"][0]["amount_label"] == (
        "Missing or invalid"
    )
    assert missing["contributing_transaction_control"]["complete"] is False

    unmapped = _finding(projection, "CORE-02")["explain_this"]
    assert unmapped["supporting_evidence"]["department_number"] == "00-0999"
    assert unmapped["supporting_evidence"]["account_number"] == "527015"
    assert unmapped["contributing_transactions"][0]["source_row"] == 43
    assert unmapped["contributing_transactions"][0]["amount_label"] == (
        "$1,850.00"
    )

    reconciliation = _finding(projection, "CORE-05")["explain_this"]
    assert reconciliation["supporting_evidence"]["budget_atd"] == "$1,850.00"
    assert reconciliation["supporting_evidence"]["lineage"][0]["row"] == 11
    assert reconciliation["supporting_evidence"]["lineage"][0]["cell"] == "D11"
    assert reconciliation["contributing_transactions"] == []
    assert reconciliation["contributing_transaction_control"]["total_cents"] == 0
    assert "Exact-key GED sum $0.00" in reconciliation[
        "supporting_evidence"
    ]["actual"]


def test_finding_review_status_is_append_only_authorized_and_non_financial(
    tmp_path,
):
    database, services, review, projection = _validated_review(tmp_path)
    financial = services.financial_review
    finding = _finding(projection, "CORE-01")
    finding_id = finding["finding_id"]
    connection = financial._uow.dal.conn
    immutable_before = connection.execute(
        "SELECT * FROM v2_validation_findings WHERE finding_id=?",
        (finding_id,),
    ).fetchone()

    for status in (
        FindingReviewStatus.ACKNOWLEDGED,
        FindingReviewStatus.IN_REVIEW,
        FindingReviewStatus.RESOLVED,
        FindingReviewStatus.DISMISSED,
    ):
        changed = financial.update_finding_review_status(
            review.review_id,
            finding_id,
            status,
            reason=f"Reviewer recorded {status.value}; no financial decision.",
        )
        assert changed["status"] == status.value
        assert changed["review_required"] is (
            status
            not in {
                FindingReviewStatus.RESOLVED,
                FindingReviewStatus.DISMISSED,
            }
        )
        assert changed["actor_id"]
        assert changed["occurred_at"]

    history = financial.finding_review_history(
        review.review_id, finding_id
    )
    assert [item["status"] for item in history] == [
        "New",
        "Acknowledged",
        "In Review",
        "Resolved",
        "Dismissed",
    ]
    assert [item["ordinal"] for item in history] == [1, 2, 3, 4, 5]
    assert connection.execute(
        "SELECT * FROM v2_validation_findings WHERE finding_id=?",
        (finding_id,),
    ).fetchone() == immutable_before
    saved = financial.results(review.review_id)
    saved_finding = next(
        item for item in saved["findings"] if item["finding_id"] == finding_id
    )
    assert saved_finding["review_status"] == "Dismissed"
    assert saved_finding["review_required"] is False
    assert saved_finding["explain_this"] == finding["explain_this"]
    summary = financial.leadership_summary(review.review_id)
    assert finding_id not in {
        item["finding_id"]
        for item in summary["items_requiring_human_review"]
    }
    audit = [
        item
        for item in financial._audit.events(review_id=review.review_id)
        if item.event_type == "finding_review_status_changed"
    ]
    assert len(audit) == 4
    assert all(
        item.payload["financial_decision_recorded"] is False for item in audit
    )
    assert [
        item.payload["review_required"] for item in audit
    ] == [True, True, False, False]
    financial._audit.verify_all()

    restarted = build_query_services(database, clock=FixedClock())
    reopened = restarted.financial_review.results(review.review_id)
    reopened_finding = next(
        item
        for item in reopened["findings"]
        if item["finding_id"] == finding_id
    )
    assert reopened_finding["review_status"] == "Dismissed"
    assert reopened_finding["review_required"] is False
    assert len(reopened_finding["review_status_history"]) == 5


def test_denied_status_change_preserves_finding_and_status_history(
    tmp_path, monkeypatch
):
    _database, services, review, projection = _validated_review(tmp_path)
    financial = services.financial_review
    finding = _finding(projection, "CORE-02")
    before = copy.deepcopy(
        financial.finding_review_history(
            review.review_id, finding["finding_id"]
        )
    )

    def deny(_permission):
        raise PermissionError("Reviewer permission denied.")

    monkeypatch.setattr(financial, "_authorizer", deny)
    with pytest.raises(PermissionError, match="denied"):
        financial.update_finding_review_status(
            review.review_id,
            finding["finding_id"],
            FindingReviewStatus.ACKNOWLEDGED,
            reason="Attempted without Reviewer authorization.",
        )
    assert financial.finding_review_history(
        review.review_id, finding["finding_id"]
    ) == before


def test_leadership_summary_uses_only_recorded_run_values(tmp_path):
    _database, services, review, projection = _validated_review(tmp_path)
    summary = services.financial_review.leadership_summary(review.review_id)

    assert summary["authoritative_source"] == (
        "SEALED_DETERMINISTIC_VALIDATION_RUN"
    )
    assert summary["ai_required"] is False
    assert summary["identity"]["validation_run_id"] == projection["run_id"]
    assert summary["identity"]["department_number"] == "00-0245"
    assert summary["identity"]["reporting_period"] == "May 2026"
    assert summary["financial_position"] == {
        "budget": "$10,372,000.00",
        "actual_spend": "Partial — $3,500,095.00",
        "actual_spend_complete": False,
        "eac": "$9,382,095.00",
        "variance": "$989,905.00",
        "variance_basis": "Budget DELTA (BGT - EAC)",
    }
    assert summary["overall_status"] == "Incomplete"
    assert summary["budget_health"] == "Incomplete"
    assert summary["ged_status"]["transaction_count"] == 258
    assert summary["ged_status"]["missing_required_data"] == 1
    assert summary["ged_status"]["duplicate_transactions"] == 1
    assert summary["material_variances"][0]["account_number"] == "555035"
    assert summary["material_variances"][0]["overrun"] == "$150,000.00"
    assert summary["material_variances"][0]["variance_percentage"] == "13.64%"
    assert len(summary["items_requiring_human_review"]) == 5
    assert summary["data_quality_limitations"]
    assert "does not approve" in summary["decision_boundary"]
