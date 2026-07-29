import itertools

import pytest

from finsight.app import build_query_services
from finsight.application.rule_management import (
    RuleManagementError,
    RuleManagementService,
)
from finsight.domain.source_intake import SourceRole
from tests.support import FixedClock


FIXTURES = "initiatives/configurable-rule-engine-v2/fixtures"


def _confirmed_review(tmp_path):
    services = build_query_services(
        str(tmp_path / "rules.db"), clock=FixedClock()
    )
    review = services.review_management.create_review(
        5, 2026, idempotency_key="create-rules"
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
        review.review_id, pair, idempotency_key="sources-rules"
    )
    dataset = services.financial_review.reconstruct_dataset(review.review_id)
    services.financial_review.confirm_reviewed_data(
        review.review_id, dataset, attestation_text="Reviewed."
    )
    return services, review, dataset


def _rule_service(financial_review):
    ids = (f"{value:032x}" for value in itertools.count(1))
    return RuleManagementService(
        repository=financial_review._repo,
        unit_of_work=financial_review._uow,
        audit_stream=financial_review._audit,
        engine=financial_review._engine,
        actor=financial_review._actor,
        clock=financial_review._clock,
        authorizer=lambda _permission: None,
        id_factory=ids.__next__,
    )


def _persist_and_close(financial, review_id, dataset):
    financial.persist_evaluation(
        review_id, dataset, financial.evaluate(dataset)
    )
    financial.complete_review(review_id)
    return financial.results(review_id)


def _optional_execution(projection, rule_id):
    return next(
        item for item in projection["executions"] if item["rule_id"] == rule_id
    )


def _analytics_rule_outcome(projection, rule_id):
    return next(
        item
        for item in projection["metrics"]["analytics"]["rule_outcomes"]
        if item["rule_id"] == rule_id
    )


def _severity_counts(projection):
    return {
        item["severity"]: item["count"]
        for item in projection["metrics"]["analytics"]["findings_by_severity"]
    }


def _historical_result_content(projection):
    """Content whose exact retention makes a sealed run reproducible."""

    return {
        "run_id": projection["run_id"],
        "generation_id": projection["generation_id"],
        "rule_set_id": projection["rule_set_id"],
        "dataset_fingerprint": projection["dataset_fingerprint"],
        "ledger_hash": projection["ledger_hash"],
        "completion_seal": projection["completion_seal"],
        "executions": projection["executions"],
        "scope_results": projection["scope_results"],
        "findings": projection["findings"],
        "metrics": projection["metrics"],
    }


def test_optional_rule_lifecycle_is_versioned_tested_and_bound(tmp_path):
    services, review, dataset = _confirmed_review(tmp_path)
    rules = _rule_service(services.financial_review)

    draft = rules.create_optional_draft(
        name="Large Transaction Review",
        purpose="Require each GED Amount to remain within the configured limit.",
        severity="Medium",
        operator="LTE",
        threshold="1000000.00",
    )
    successor = rules.edit_optional_draft(
        draft["rule_id"],
        name="Large Transaction Review",
        purpose="Require each GED Amount to remain within the approved limit.",
        severity="High",
        operator="LTE",
        threshold="500000.00",
    )
    assert draft["version"] == "1.0.0"
    assert successor["version"] == "1.0.1"
    assert successor["predecessor_version"] == "1.0.0"
    reviewer_rules = rules.list_repository_rules(review.review_id)
    assert all(
        item["rule_id"] != successor["rule_id"] for item in reviewer_rules
    )
    assert len(reviewer_rules) == 5

    repository_rules = rules.list_repository_rules(
        review.review_id, administrative=True
    )
    visible_draft = next(
        item
        for item in repository_rules
        if item["rule_id"] == successor["rule_id"]
    )
    assert visible_draft["version"] == "1.0.1"
    assert visible_draft["bound"] is False
    assert [
        item["version"] for item in visible_draft["previous_versions"]
    ] == ["1.0.0"]

    test = rules.test_draft(
        review.review_id,
        dataset,
        successor["rule_id"],
        successor["version"],
    )
    assert test["metrics"]["pass_count"] == 257
    assert test["metrics"]["not_evaluated_count"] == 1

    active = rules.activate_optional_version(
        review.review_id, successor["rule_id"], successor["version"]
    )
    assert len(active.rules) == 6
    assert active.rules[-1].name == "Large Transaction Review"
    visible_active = next(
        item
        for item in rules.list_repository_rules(review.review_id)
        if item["rule_id"] == successor["rule_id"]
    )
    assert visible_active["bound"] is True
    assert visible_active["enabled"] is True

    disabled = rules.set_optional_enabled(
        review.review_id, successor["rule_id"], False
    )
    assert len(disabled.rules) == 5
    enabled = rules.set_optional_enabled(
        review.review_id, successor["rule_id"], True
    )
    assert len(enabled.rules) == 6
    retired = rules.retire_optional_rule(review.review_id, successor["rule_id"])
    assert len(retired.rules) == 5
    assert len(rules.rule_set_history(review.review_id)) == 5

    with pytest.raises(RuleManagementError, match="Protected Core Rules"):
        rules.set_optional_enabled(review.review_id, "CORE-01", False)


@pytest.mark.parametrize(
    "unsafe_threshold",
    (
        "",
        "NaN",
        "Infinity",
        "1e3",
        "$1,000.00",
        "100.001",
        "0; DROP TABLE v2_rule_definition_versions",
    ),
)
def test_invalid_or_unsafe_threshold_is_rejected_before_persistence(
    tmp_path, unsafe_threshold
):
    services, _review, _dataset = _confirmed_review(tmp_path)
    financial = services.financial_review
    rules = _rule_service(financial)
    before_definitions = financial._uow.dal.conn.execute(
        "SELECT COUNT(*) FROM v2_rule_definition_versions "
        "WHERE classification='OPTIONAL_CONFIGURABLE'"
    ).fetchone()[0]
    before_events = financial._uow.dal.conn.execute(
        "SELECT COUNT(*) FROM v2_rule_lifecycle_events"
    ).fetchone()[0]

    with pytest.raises(
        RuleManagementError,
        match="finite financial amount|valid financial amount",
    ):
        rules.create_optional_draft(
            name="Unsafe Rule",
            purpose="This definition must never reach governed storage.",
            severity="High",
            operator="LTE",
            threshold=unsafe_threshold,
        )

    assert (
        financial._uow.dal.conn.execute(
            "SELECT COUNT(*) FROM v2_rule_definition_versions "
            "WHERE classification='OPTIONAL_CONFIGURABLE'"
        ).fetchone()[0]
        == before_definitions
    )
    assert (
        financial._uow.dal.conn.execute(
            "SELECT COUNT(*) FROM v2_rule_lifecycle_events"
        ).fetchone()[0]
        == before_events
    )


def test_invalid_optional_rule_edit_does_not_create_a_successor_version(tmp_path):
    services, _review, _dataset = _confirmed_review(tmp_path)
    financial = services.financial_review
    rules = _rule_service(financial)
    draft = rules.create_optional_draft(
        name="Large Transaction Review",
        purpose="Require each GED Amount to remain within the configured limit.",
        severity="Medium",
        operator="LTE",
        threshold="1000.00",
    )

    with pytest.raises(RuleManagementError, match="finite financial amount"):
        rules.edit_optional_draft(
            draft["rule_id"],
            name="Large Transaction Review",
            purpose="An unsafe edit must not create an immutable successor.",
            severity="High",
            operator="LTE",
            threshold="1000.001",
        )

    versions = financial._uow.dal.conn.execute(
        "SELECT version FROM v2_rule_definition_versions WHERE rule_id=? "
        "ORDER BY version",
        (draft["rule_id"],),
    ).fetchall()
    assert [row[0] for row in versions] == ["1.0.0"]


def test_rule_set_reanalysis_retains_prior_run_and_comparison(tmp_path):
    services, review, dataset = _confirmed_review(tmp_path)
    financial = services.financial_review
    initial = financial.persist_evaluation(
        review.review_id, dataset, financial.evaluate(dataset)
    )
    financial.complete_review(review.review_id)
    rules = _rule_service(financial)
    draft = rules.create_optional_draft(
        name="Large Transaction Review",
        purpose="Require each GED Amount to remain within the configured limit.",
        severity="Medium",
        operator="LTE",
        threshold="1000000.00",
    )
    rules.test_draft(
        review.review_id, dataset, draft["rule_id"], draft["version"]
    )
    rules.activate_optional_version(
        review.review_id, draft["rule_id"], draft["version"]
    )

    successor = financial.persist_evaluation(
        review.review_id, dataset, financial.evaluate(dataset)
    )
    financial.complete_review(review.review_id)

    history = financial.validation_history(review.review_id)
    comparison = financial.compare_validation_runs(
        review.review_id, initial["run_id"], successor["run_id"]
    )
    assert len(history) == 2
    assert history[0]["generation_id"] != history[1]["generation_id"]
    assert comparison["rules_added"] == [draft["rule_id"]]
    assert comparison["findings_added"] == []
    assert (
        financial._uow.dal.conn.execute(
            "SELECT COUNT(*) FROM v2_review_completion_events WHERE review_id=?",
            (review.review_id,),
        ).fetchone()[0]
        == 2
    )


def test_optional_rule_revalidation_pipeline_is_versioned_and_reproducible(
    tmp_path
):
    services, review, dataset = _confirmed_review(tmp_path)
    financial = services.financial_review
    rules = _rule_service(financial)

    initial = _persist_and_close(financial, review.review_id, dataset)
    initial_severity = _severity_counts(initial)
    initial_financial_summary = initial["metrics"]["analytics"][
        "financial_summary"
    ]

    draft = rules.create_optional_draft(
        name="Large Transaction Review",
        purpose="Require each GED Amount to remain within the configured limit.",
        severity="Medium",
        operator="LTE",
        threshold="1000.00",
    )
    draft_test = rules.test_draft(
        review.review_id, dataset, draft["rule_id"], draft["version"]
    )
    assert draft_test["metrics"]["fail_count"] > 0
    assert draft_test["metrics"]["not_evaluated_count"] == 1
    rules.activate_optional_version(
        review.review_id, draft["rule_id"], draft["version"]
    )
    with_optional = _persist_and_close(
        financial, review.review_id, dataset
    )

    first_execution = _optional_execution(with_optional, draft["rule_id"])
    first_outcome = _analytics_rule_outcome(with_optional, draft["rule_id"])
    first_findings = [
        item
        for item in with_optional["findings"]
        if item["rule_id"] == draft["rule_id"]
    ]
    assert first_execution["version"] == "1.0.0"
    assert first_execution["fail_count"] == draft_test["metrics"]["fail_count"]
    assert first_execution["not_evaluated_count"] == 1
    assert len(first_findings) == first_execution["fail_count"]
    assert all(item["rule_version"] == "1.0.0" for item in first_findings)
    assert first_outcome["failed"] == first_execution["fail_count"]
    assert with_optional["metrics"]["rules_executed"] == 6
    assert (
        with_optional["metrics"]["findings"]
        == initial["metrics"]["findings"] + len(first_findings)
    )
    assert (
        _severity_counts(with_optional)["Medium"]
        == initial_severity["Medium"] + len(first_findings)
    )
    assert (
        with_optional["metrics"]["analytics"]["financial_summary"]
        == initial_financial_summary
    )

    addition = financial.compare_validation_runs(
        review.review_id, initial["run_id"], with_optional["run_id"]
    )
    assert addition["rules_added"] == [draft["rule_id"]]
    assert len(addition["findings_added"]) == len(first_findings)
    assert addition["findings_removed"] == []
    assert addition["findings_changed"] == []

    successor = rules.edit_optional_draft(
        draft["rule_id"],
        name="Large Transaction Review",
        purpose="Require each GED Amount to remain within the revised limit.",
        severity="High",
        operator="LTE",
        threshold="10000.00",
    )
    successor_test = rules.test_draft(
        review.review_id,
        dataset,
        successor["rule_id"],
        successor["version"],
    )
    assert 0 < successor_test["metrics"]["fail_count"] < first_execution[
        "fail_count"
    ]
    rules.activate_optional_version(
        review.review_id, successor["rule_id"], successor["version"]
    )
    edited = _persist_and_close(financial, review.review_id, dataset)

    edited_execution = _optional_execution(edited, successor["rule_id"])
    edited_outcome = _analytics_rule_outcome(edited, successor["rule_id"])
    edited_findings = [
        item
        for item in edited["findings"]
        if item["rule_id"] == successor["rule_id"]
    ]
    assert edited_execution["version"] == "1.0.1"
    assert (
        edited_execution["fail_count"]
        == successor_test["metrics"]["fail_count"]
    )
    assert edited_outcome["failed"] == edited_execution["fail_count"]
    assert all(item["rule_version"] == "1.0.1" for item in edited_findings)
    assert (
        edited["metrics"]["findings"]
        == initial["metrics"]["findings"] + len(edited_findings)
    )
    assert (
        _severity_counts(edited)["High"]
        == initial_severity["High"] + len(edited_findings)
    )
    assert (
        edited["metrics"]["analytics"]["financial_summary"]
        == initial_financial_summary
    )

    changed = financial.compare_validation_runs(
        review.review_id, with_optional["run_id"], edited["run_id"]
    )
    assert [item["rule_id"] for item in changed["rules_changed"]] == [
        successor["rule_id"]
    ]
    assert len(changed["findings_removed"]) == (
        len(first_findings) - len(edited_findings)
    )
    assert len(changed["findings_changed"]) == len(edited_findings)
    assert changed["findings_added"] == []
    assert all(
        item["before"]["rule_version"] == "1.0.0"
        and item["after"]["rule_version"] == "1.0.1"
        for item in changed["findings_changed"]
    )

    rules.set_optional_enabled(review.review_id, successor["rule_id"], False)
    disabled = _persist_and_close(financial, review.review_id, dataset)
    assert all(
        item["rule_id"] != successor["rule_id"]
        for item in disabled["executions"]
    )
    assert all(
        item["rule_id"] != successor["rule_id"]
        for item in disabled["metrics"]["analytics"]["rule_outcomes"]
    )
    assert disabled["metrics"]["rules_executed"] == 5
    assert disabled["metrics"]["findings"] == initial["metrics"]["findings"]
    assert _severity_counts(disabled) == initial_severity
    assert (
        disabled["metrics"]["analytics"]["financial_summary"]
        == initial_financial_summary
    )

    removal = financial.compare_validation_runs(
        review.review_id, edited["run_id"], disabled["run_id"]
    )
    assert removal["rules_removed"] == [successor["rule_id"]]
    assert len(removal["findings_removed"]) == len(edited_findings)
    assert removal["findings_resolved"] == removal["findings_removed"]
    assert removal["findings_added"] == []

    current_history = financial.validation_history(review.review_id)
    assert [item["run_id"] for item in current_history] == [
        initial["run_id"],
        with_optional["run_id"],
        edited["run_id"],
        disabled["run_id"],
    ]
    retained_optional = _optional_execution(
        current_history[1], draft["rule_id"]
    )
    assert retained_optional["version"] == "1.0.0"
    assert retained_optional["fail_count"] == len(first_findings)
    assert len(rules.rule_set_history(review.review_id)) == 4

    reopened = build_query_services(
        str(tmp_path / "rules.db"), clock=FixedClock()
    )
    reopened_history = reopened.financial_review.validation_history(
        review.review_id
    )
    assert len(reopened_history) == 4
    assert [
        _historical_result_content(item) for item in reopened_history
    ] == [
        _historical_result_content(item) for item in current_history
    ]
    assert reopened.financial_review.compare_validation_runs(
        review.review_id, edited["run_id"], disabled["run_id"]
    ) == removal
