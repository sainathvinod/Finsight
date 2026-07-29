from dataclasses import replace

import pytest

from finsight.domain.financial_validation import (
    CoreFinancialValidationEngine,
    ReviewRecord,
    RuleManifestError,
    RuleDefinitionVersion,
    RuleSetManifest,
    ResultStatus,
    WorkingFinancialDataset,
    core_rule_manifest,
    dataset_from_inspections,
)
from finsight.domain.source_intake import SourceRole
from finsight.infrastructure.slv001_extractor import Slv001Extractor


FIXTURES = "initiatives/configurable-rule-engine-v2/fixtures"


def _evaluation():
    extractor = Slv001Extractor()
    budget = extractor.inspect(
        f"{FIXTURES}/Sample_Budget_Report.xlsx", SourceRole.BUDGET
    )
    ged = extractor.inspect(
        f"{FIXTURES}/Sample_GED_Report.xlsx", SourceRole.GED
    )
    dataset = dataset_from_inspections(
        "rev_fixture",
        budget,
        ged,
        department_number="00-0245",
        department_name="Applications Enginee",
        reporting_period="May 2026",
    )
    return dataset, CoreFinancialValidationEngine().evaluate(dataset)


def test_fixture_rule_ledger_matches_approved_oracle():
    dataset, evaluation = _evaluation()

    assert len(dataset.budget_details) == 71
    assert len(dataset.ged_transactions) == 258
    assert len(evaluation.scope_results) == 986
    assert sum(item.status is ResultStatus.PASS for item in evaluation.scope_results) == 979
    assert sum(item.status is ResultStatus.FAIL for item in evaluation.scope_results) == 5
    assert sum(
        item.status is ResultStatus.NOT_EVALUATED
        for item in evaluation.scope_results
    ) == 2
    assert [
        (item.rule_id, item.status.value, item.pass_count, item.fail_count, item.not_evaluated_count)
        for item in evaluation.executions
    ] == [
        ("CORE-05", "NOT_EVALUATED", 69, 1, 1),
        ("CORE-01", "NOT_EVALUATED", 69, 1, 1),
        ("CORE-02", "FAIL", 257, 1, 0),
        ("CORE-04", "FAIL", 328, 1, 0),
        ("CORE-03", "FAIL", 256, 1, 0),
    ]


def test_fixture_findings_preserve_cross_rule_effects_and_evidence():
    _dataset, evaluation = _evaluation()

    assert [item.rule_id for item in evaluation.findings] == [
        "CORE-01",
        "CORE-02",
        "CORE-04",
        "CORE-05",
        "CORE-03",
    ]
    duplicate = next(item for item in evaluation.findings if item.rule_id == "CORE-03")
    assert duplicate.source_records == ("GED:GED:65", "GED:GED:66")
    assert "$82.50" in duplicate.actual
    missing = next(item for item in evaluation.findings if item.rule_id == "CORE-04")
    assert missing.evidence == ("GED!O87",)
    assert missing.evidence_details == (
        {
            "record_id": "GED:GED:87",
            "source_role": "GED",
            "worksheet": "GED",
            "row": 87,
            "field": "amount",
            "cell": "O87",
            "original_value": None,
            "current_value": None,
            "value_origin": "Original",
        },
    )
    mapping = next(item for item in evaluation.findings if item.rule_id == "CORE-02")
    assert mapping.department_number == "00-0999"
    reconciliation = next(item for item in evaluation.findings if item.rule_id == "CORE-05")
    assert reconciliation.account_number == "527015"
    assert "$0.00" in reconciliation.actual
    assert evaluation.metrics["overall_status"] == "Incomplete"
    assert evaluation.metrics["rag_status"] == "At Risk (Red)"
    assert evaluation.metrics["financial_totals"] == {
        "bgt": "$10,372,000.00",
        "atd": "$3,500,095.00",
        "etc": "$5,882,000.00",
        "eac": "$9,382,095.00",
        "delta": "$989,905.00",
        "ged": "$3,500,095.00",
        "mapped_ged": "$3,498,245.00",
        "unmapped_ged": "$1,850.00",
        "ged_is_complete": False,
        "variance_bgt_to_ged": "$6,871,905.00",
    }
    assert evaluation.metrics["findings_by_severity"] == {
        "Critical": 0,
        "High": 4,
        "Medium": 1,
        "Low": 0,
    }
    assert evaluation.metrics["data_quality_counts"] == {
        "missing_fields": 1,
        "invalid_values": 0,
        "duplicate_records": 1,
        "excluded_records": 57,
        "excluded_budget_rows": 23,
        "excluded_ged_rows": 34,
        "parsing_issues": 1,
        "unmapped_transactions": 1,
        "department_mismatches": 0,
        "period_mismatches": 0,
    }
    account_527015 = next(
        item
        for item in evaluation.metrics["account_comparisons"]
        if item["account_number"] == "527015"
    )
    assert account_527015["ged_amount"] == "$0.00"
    assert account_527015["variance_atd_to_ged"] == "$1,850.00"
    assert account_527015["reconciliation_status"] == "FAIL"


def _projected_account(evaluation, department_number, account_number):
    return next(
        item
        for item in evaluation.metrics["canonical_financial_dataset"]["accounts"]
        if item["department_number"] == department_number
        and item["account_number"] == account_number
    )


def test_canonical_dataset_is_the_exact_department_account_union():
    _dataset, evaluation = _evaluation()
    canonical = evaluation.metrics["canonical_financial_dataset"]

    assert canonical["schema_version"] == "CFD-1.0"
    assert canonical["matching_grain"] == [
        "department_number",
        "account_number",
    ]
    assert len(canonical["accounts"]) == 72
    assert len(
        {
            (item["department_number"], item["account_number"])
            for item in canonical["accounts"]
        }
    ) == 72
    assert (
        sum(item["budget_mapping"] == "MAPPED" for item in canonical["accounts"])
        == 71
    )
    assert canonical["unscoped_ged_records"] == []

    overrun = _projected_account(evaluation, "00-0245", "555035")
    assert {
        "bgt_cents": overrun["bgt_cents"],
        "atd_cents": overrun["atd_cents"],
        "etc_cents": overrun["etc_cents"],
        "eac_cents": overrun["eac_cents"],
        "delta_cents": overrun["delta_cents"],
        "summed_ged_amount_cents": overrun["summed_ged_amount_cents"],
        "budget_to_ged_difference_cents": overrun[
            "budget_to_ged_difference_cents"
        ],
        "remaining_budget_cents": overrun["remaining_budget_cents"],
        "over_budget_amount_cents": overrun["over_budget_amount_cents"],
        "budget_utilization_hundredths": overrun[
            "budget_utilization_hundredths"
        ],
    } == {
        "bgt_cents": 110_000_000,
        "atd_cents": 125_000_000,
        "etc_cents": 65_000_000,
        "eac_cents": 190_000_000,
        "delta_cents": -80_000_000,
        "summed_ged_amount_cents": 125_000_000,
        "budget_to_ged_difference_cents": 0,
        "remaining_budget_cents": -15_000_000,
        "over_budget_amount_cents": 15_000_000,
        "budget_utilization_hundredths": 11_364,
    }
    assert overrun["ged_transaction_count"] == 44
    assert overrun["reconciliation_status"] == "PASS"
    assert overrun["finding_badges"] == ["CORE-01 · High"]

    invalid_mapping = _projected_account(evaluation, "00-0999", "527015")
    assert invalid_mapping["budget_mapping"] == "UNMAPPED"
    assert invalid_mapping["budget_source_record"] is None
    assert invalid_mapping["summed_ged_amount_cents"] == 185_000
    assert invalid_mapping["contributing_ged_rows"] == [43]
    assert invalid_mapping["finding_badges"] == ["CORE-02 · High"]

    displaced_budget_scope = _projected_account(evaluation, "00-0245", "527015")
    assert displaced_budget_scope["budget_mapping"] == "MAPPED"
    assert displaced_budget_scope["summed_ged_amount_cents"] == 0
    assert displaced_budget_scope["budget_to_ged_difference_cents"] == 185_000
    assert displaced_budget_scope["reconciliation_status"] == "FAIL"


def test_missing_amount_preserves_partial_evidence_but_blocks_account_totals():
    _dataset, evaluation = _evaluation()
    purchased_software = _projected_account(evaluation, "00-0245", "537035")

    assert purchased_software["ged_transaction_count"] == 2
    assert purchased_software["contributing_ged_rows"] == [87, 88]
    assert purchased_software["missing_amount_count"] == 1
    assert purchased_software["parseable_ged_subtotal_cents"] == 630_000
    assert purchased_software["summed_ged_amount_cents"] is None
    assert purchased_software["summed_ged_amount_label"] == "Not evaluated"
    assert purchased_software["budget_to_ged_difference_cents"] is None
    assert purchased_software["remaining_budget_cents"] is None
    assert purchased_software["budget_utilization_hundredths"] is None
    assert purchased_software["reconciliation_status"] == "NOT_EVALUATED"
    outcomes = {
        item["rule_id"]: item["status"]
        for item in purchased_software["rule_outcomes"]
    }
    assert outcomes["CORE-04"] == "FAIL"
    assert outcomes["CORE-01"] == "NOT_EVALUATED"
    assert outcomes["CORE-05"] == "NOT_EVALUATED"


def test_financial_control_report_has_exact_totals_and_row_classifications():
    _dataset, evaluation = _evaluation()
    controls = evaluation.metrics["financial_control_report"]

    assert controls["schema_version"] == "FCR-1.0"
    assert "Exact Decimal arithmetic" in controls["decimal_policy"]
    assert {
        field_name: control["exact_decimal"]
        for field_name, control in controls["budget"]["totals"].items()
    } == {
        "bgt": "10372000.00",
        "atd": "3500095.00",
        "etc": "5882000.00",
        "eac": "9382095.00",
        "delta": "989905.00",
    }
    assert all(
        control["source_row_count"] == 71
        and control["excluded_row_count"] == 23
        and control["complete"]
        for control in controls["budget"]["totals"].values()
    )
    assert (
        controls["budget"]["source_rows_read"],
        controls["budget"]["included_row_count"],
        controls["budget"]["excluded_row_count"],
    ) == (94, 71, 23)
    assert {
        item["row_type"]: item["count"]
        for item in controls["budget"]["row_types"]
    } == {
        "Budget detail": 71,
        "Budget grand total": 1,
        "Budget group total": 11,
        "Budget separator": 11,
    }
    budget_row_types = {
        item["row_type"]: item for item in controls["budget"]["row_types"]
    }
    assert budget_row_types["Budget grand total"]["source_rows"] == [95]
    assert budget_row_types["Budget detail"]["treatment"] == "Included"

    ged = controls["ged"]
    assert (ged["source_rows_read"], ged["included_row_count"], ged["excluded_row_count"]) == (
        292,
        258,
        34,
    )
    assert {
        item["row_type"]: item["count"] for item in ged["row_types"]
    } == {
        "GED account total": 31,
        "GED blank": 2,
        "GED department total": 1,
        "GED transaction": 258,
    }
    ged_row_types = {item["row_type"]: item for item in ged["row_types"]}
    assert ged_row_types["GED department total"]["source_rows"] == [297]
    assert ged_row_types["GED blank"]["source_rows"] == [298, 299]
    assert {
        name: ged[name]["exact_decimal"]
        for name in (
            "total_eligible_amount",
            "mapped_amount",
            "unmapped_amount",
            "excluded_transaction_amount",
        )
    } == {
        "total_eligible_amount": "3500095.00",
        "mapped_amount": "3498245.00",
        "unmapped_amount": "1850.00",
        "excluded_transaction_amount": "0.00",
    }
    assert ged["total_eligible_amount"]["parseable_amount_count"] == 257
    assert ged["total_eligible_amount"]["missing_or_unparseable_amount_count"] == 1
    assert ged["total_eligible_amount"]["complete"] is False
    assert ged["excluded_transaction_amount"]["source_row_count"] == 0


def test_enhanced_analytics_are_exact_complete_and_traceable():
    _dataset, evaluation = _evaluation()
    analytics = evaluation.metrics["analytics"]

    assert analytics["financial_summary"] == {
        "bgt_cents": 1_037_200_000,
        "bgt_label": "$10,372,000.00",
        "atd_cents": 350_009_500,
        "atd_label": "$3,500,095.00",
        "etc_cents": 588_200_000,
        "etc_label": "$5,882,000.00",
        "eac_cents": 938_209_500,
        "eac_label": "$9,382,095.00",
        "delta_cents": 98_990_500,
        "delta_label": "$989,905.00",
        "ged_cents": 350_009_500,
        "ged_label": "Partial — $3,500,095.00",
        "actual_variance_cents": None,
        "actual_variance_label": "Unavailable",
        "actual_variance_percentage_hundredths": None,
        "actual_variance_percentage_label": "Unavailable",
        "complete": False,
        "account_count": 71,
        "ged_transaction_count": 258,
    }
    assert len(analytics["budget_by_account"]) == 71
    assert len(analytics["comparison_by_account"]) == 71
    assert len(analytics["account_hierarchy"]) == 72
    assert len(analytics["ged_by_account"]) == 31
    assert len(analytics["ged_by_period"]) == 5
    assert len(analytics["ged_by_vendor"]) == 24
    assert len(analytics["largest_transactions"]) == 20
    assert len(analytics["ged_by_polarity"]) == 4
    overrun = next(
        item
        for item in analytics["comparison_by_account"]
        if item["account_number"] == "555035"
    )
    assert {
        "actual_variance_cents": overrun["actual_variance_cents"],
        "actual_variance_label": overrun["actual_variance_label"],
        "actual_variance_percentage_hundredths": overrun[
            "actual_variance_percentage_hundredths"
        ],
        "actual_variance_percentage_label": overrun[
            "actual_variance_percentage_label"
        ],
    } == {
        "actual_variance_cents": 15_000_000,
        "actual_variance_label": "$150,000.00",
        "actual_variance_percentage_hundredths": 1_364,
        "actual_variance_percentage_label": "+13.64%",
    }
    incomplete = next(
        item
        for item in analytics["comparison_by_account"]
        if item["account_number"] == "537035"
    )
    assert incomplete["actual_variance_cents"] is None
    assert incomplete["actual_variance_label"] == "Unavailable"
    assert incomplete["actual_variance_percentage_label"] == "Unavailable"

    no_vendor = analytics["ged_by_vendor"][0]
    assert no_vendor == {
        "vendor_name": "No vendor recorded",
        "amount_cents": 185_604_000,
        "amount_label": "Partial — $1,856,040.00",
        "transaction_count": 178,
        "complete": False,
        "missing_amount_count": 1,
    }
    largest = analytics["largest_transactions"][0]
    assert {
        "record_id": largest["record_id"],
        "source_row": largest["source_row"],
        "account_number": largest["account_number"],
        "journal_number": largest["journal_number"],
        "amount_cents": largest["amount_cents"],
        "polarity": largest["polarity"],
    } == {
        "record_id": "GED:GED:14",
        "source_row": 14,
        "account_number": "525005",
        "journal_number": "PAY0190938",
        "amount_cents": 11_586_300,
        "polarity": "Positive",
    }
    assert [
        (
            item["polarity"],
            item["amount_cents"],
            item["transaction_count"],
            item["missing_amount_count"],
        )
        for item in analytics["ged_by_polarity"]
    ] == [
        ("Positive", 355_684_800, 250, 0),
        ("Negative", -5_675_300, 7, 0),
        ("Zero", 0, 0, 0),
        ("Missing / invalid", 0, 1, 1),
    ]
    assert analytics["account_status_counts"] == {
        "over_budget": 1,
        "within_budget": 69,
        "not_evaluated": 1,
    }
    assert analytics["reconciliation_status_counts"] == {
        "reconciled": 69,
        "different": 1,
        "not_evaluated": 1,
    }
    assert analytics["variance_ranked_accounts"][0]["scope_key"] == (
        "00-0245|555035"
    )


def test_field_coverage_accounts_for_every_approved_source_column():
    _dataset, evaluation = _evaluation()
    coverage = evaluation.metrics["field_coverage"]

    assert len(coverage) == 23
    assert {
        (item["source"], item["source_column"], item["source_field"])
        for item in coverage
    } == {
        ("Budget", "A", "account_number"),
        ("Budget", "B", "account_name"),
        ("Budget", "C", "bgt"),
        ("Budget", "D", "atd"),
        ("Budget", "E", "etc"),
        ("Budget", "F", "eac"),
        ("Budget", "G", "delta"),
        ("Budget", "H", "notes"),
        ("GED", "A", "department_number"),
        ("GED", "B", "department_name"),
        ("GED", "C", "account_number"),
        ("GED", "D", "account_name"),
        ("GED", "E", "fiscal_period"),
        ("GED", "F", "journal_number"),
        ("GED", "G", "journal_date"),
        ("GED", "H", "invoice_amount"),
        ("GED", "I", "check_number"),
        ("GED", "J", "invoice_date"),
        ("GED", "K", "vendor_name"),
        ("GED", "L", "agency"),
        ("GED", "M", "journal_description"),
        ("GED", "N", "journal_line_description"),
        ("GED", "O", "amount"),
    }
    assert all(
        item["dataset"]
        and item["used_for"]
        and item["displayed_where"]
        and item["validation_impact"]
        and item["exclusion_reason"] == ""
        for item in coverage
    )
    by_field = {
        (item["source"], item["source_field"]): item for item in coverage
    }
    assert "CORE-05" in by_field[("Budget", "atd")]["validation_impact"]
    assert "Vendor analysis" in by_field[("GED", "vendor_name")]["used_for"]
    assert "CORE-01" in by_field[("GED", "amount")]["validation_impact"]


def _single_scope(amount, *, bgt=100, atd=100):
    budget = ReviewRecord(
        "BUDGET:Original Budget:2",
        "BUDGET",
        "Original Budget",
        2,
        "Budget detail",
        {
            "account_number": "517025",
            "account_name": "Test",
            "bgt": bgt,
            "atd": atd,
            "etc": 0,
            "eac": atd,
            "delta": bgt - atd,
        },
        {
            "account_number": "517025",
            "account_name": "Test",
            "bgt": bgt,
            "atd": atd,
            "etc": 0,
            "eac": atd,
            "delta": bgt - atd,
        },
        {
            "account_number": "A2",
            "bgt": "C2",
            "atd": "D2",
            "etc": "E2",
            "eac": "F2",
            "delta": "G2",
        },
    )
    values = {
        "department_number": "00-0245",
        "department_name": "Test Department",
        "account_number": "517025",
        "account_name": "Test",
        "fiscal_period": "2026-05",
        "journal_number": "J-1",
        "journal_date": "2026-05-31",
        "invoice_amount": None,
        "check_number": ".",
        "invoice_date": ".",
        "vendor_name": None,
        "agency": "9999COR",
        "journal_description": "Test",
        "journal_line_description": "Test",
        "amount": amount,
    }
    ged = ReviewRecord(
        "GED:GED:8",
        "GED",
        "GED",
        8,
        "GED transaction",
        values,
        values,
        {field: "A8" for field in values},
    )
    return WorkingFinancialDataset(
        "rev_boundary",
        "00-0245",
        "Test Department",
        "May 2026",
        "a" * 64,
        "b" * 64,
        (budget,),
        (ged,),
    )


def test_budget_boundary_equal_to_bgt_passes_and_reconciles():
    result = CoreFinancialValidationEngine().evaluate(_single_scope(100))
    by_rule = {item.rule_id: item for item in result.executions}
    assert by_rule["CORE-01"].status is ResultStatus.PASS
    assert by_rule["CORE-05"].status is ResultStatus.PASS
    assert result.findings == ()


def test_budget_overrun_evidence_includes_amount_and_percentage():
    result = CoreFinancialValidationEngine().evaluate(
        _single_scope(125, bgt=100, atd=125)
    )
    finding = next(
        item for item in result.findings if item.rule_id == "CORE-01"
    )
    assert "BGT $100.00" in finding.actual
    assert "GED spend $125.00" in finding.actual
    assert "overrun $25.00" in finding.actual
    assert "overrun percentage 25.00%" in finding.actual


def test_approved_signed_reversal_is_valid_financial_data():
    result = CoreFinancialValidationEngine().evaluate(
        _single_scope(-10, bgt=100, atd=-10)
    )
    by_rule = {item.rule_id: item for item in result.executions}
    assert by_rule["CORE-04"].status is ResultStatus.PASS
    assert by_rule["CORE-01"].status is ResultStatus.PASS
    assert by_rule["CORE-05"].status is ResultStatus.PASS


def test_missing_amount_fails_required_rule_and_blocks_only_aggregates():
    result = CoreFinancialValidationEngine().evaluate(_single_scope(None))
    by_rule = {item.rule_id: item for item in result.executions}
    assert by_rule["CORE-04"].status is ResultStatus.FAIL
    assert by_rule["CORE-01"].status is ResultStatus.NOT_EVALUATED
    assert by_rule["CORE-05"].status is ResultStatus.NOT_EVALUATED
    assert result.metrics["reconciliation_not_evaluated"] == 1


def test_complete_and_correct_data_detects_budget_eac_and_delta_mismatch():
    dataset = _single_scope(100)
    budget = dataset.budget_records[0]
    current = {**budget.current, "eac": 99, "delta": 0}
    changed = replace(budget, current=current)

    result = CoreFinancialValidationEngine().evaluate(
        replace(dataset, budget_records=(changed,))
    )

    execution = next(
        item for item in result.executions if item.rule_id == "CORE-04"
    )
    finding = next(item for item in result.findings if item.rule_id == "CORE-04")
    assert execution.status is ResultStatus.FAIL
    assert "EAC" in finding.actual
    assert "DELTA" in finding.actual


def test_allowlisted_optional_ged_amount_threshold_uses_common_contract():
    base = core_rule_manifest()
    optional = RuleDefinitionVersion(
        "OPT-THRESHOLD",
        "Large Transaction Review",
        "1.0.0",
        "Medium",
        "OPTIONAL_CONFIGURABLE",
        "ged_amount_threshold",
        6,
        "OPTIONAL_CONFIGURABLE",
        "Require each GED Amount to be at or below the configured limit.",
        ("ged.amount",),
        ("source_record",),
        {"operator": "LTE", "threshold": "99.99"},
    )
    manifest = RuleSetManifest(
        "RULESET-OPTIONAL-1",
        "2",
        (*base.rules, optional),
        base.protected_baseline_id,
    )

    result = CoreFinancialValidationEngine().evaluate(
        _single_scope(100), manifest
    )

    execution = next(
        item for item in result.executions if item.rule_id == "OPT-THRESHOLD"
    )
    finding = next(
        item for item in result.findings if item.rule_id == "OPT-THRESHOLD"
    )
    assert execution.status is ResultStatus.FAIL
    assert execution.fail_count == 1
    assert finding.rule_name == "Large Transaction Review"
    assert finding.actual == "$100.00"


def test_engine_dispatches_the_versioned_manifest_and_projects_its_metadata():
    base = core_rule_manifest()
    budget_rule = next(item for item in base.rules if item.rule_id == "CORE-01")
    revised = replace(
        budget_rule,
        name="Governed budget health control",
        version="2.1.0",
        severity="Critical",
    )
    manifest = RuleSetManifest(
        "RULESET-GOVERNED-2",
        "2.0.0",
        tuple(revised if item.rule_id == "CORE-01" else item for item in base.rules),
    )

    result = CoreFinancialValidationEngine().evaluate(
        _single_scope(101, bgt=100, atd=101),
        manifest,
    )

    assert result.rule_set_id == "RULESET-GOVERNED-2"
    execution = next(item for item in result.executions if item.rule_id == "CORE-01")
    finding = next(item for item in result.findings if item.rule_id == "CORE-01")
    assert execution.rule_name == "Governed budget health control"
    assert execution.version == "2.1.0"
    assert finding.rule_name == "Governed budget health control"
    assert finding.severity == "Critical"


def test_engine_fails_closed_when_a_protected_rule_is_missing():
    base = core_rule_manifest()
    manifest = RuleSetManifest(
        "RULESET-INCOMPLETE",
        "1.0.0",
        tuple(item for item in base.rules if item.rule_id != "CORE-05"),
    )

    with pytest.raises(RuleManifestError, match="CORE-05"):
        CoreFinancialValidationEngine().evaluate(_single_scope(100), manifest)
