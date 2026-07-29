"""Recorded, deterministic business explanations for sealed validation findings.

This module deliberately performs no pass/fail evaluation.  It projects facts
already produced by the financial-validation engine, together with the exact
confirmed source records that were sealed into the same Validation Run.
"""
from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from enum import Enum
import re
from typing import Any, Mapping, Sequence

from finsight.domain.financial_validation import (
    Finding,
    RuleDefinitionVersion,
    RuleSetManifest,
    ValidationEvaluation,
    WorkingFinancialDataset,
)
from finsight.domain.source_intake import RowKind


class FindingReviewStatus(str, Enum):
    """Human workflow state; never a financial or rule-engine decision."""

    NEW = "New"
    ACKNOWLEDGED = "Acknowledged"
    IN_REVIEW = "In Review"
    RESOLVED = "Resolved"
    DISMISSED = "Dismissed"


BUSINESS_TITLES = {
    "CORE-01": "Account over budget",
    "CORE-02": "Unmapped GED transaction",
    "CORE-03": "Candidate duplicate transaction",
    "CORE-04": "Missing or invalid required data",
    "CORE-05": "Budget-to-GED mismatch",
}

FORMULAS = {
    "CORE-01": (
        "SUM(GED.Amount for the exact Department Number + Account Number) "
        "<= Budget.BGT"
    ),
    "CORE-02": (
        "(GED.Department Number, GED.Account Number) must exist in the "
        "Budget detail keys"
    ),
    "CORE-03": (
        "COUNT(the approved all-material-field GED fingerprint) = 1"
    ),
    "CORE-04": (
        "Required GED values must parse; required Budget values must parse; "
        "Budget.EAC = Budget.ATD + Budget.ETC; "
        "Budget.DELTA = Budget.BGT - Budget.EAC"
    ),
    "CORE-05": (
        "Budget.ATD = SUM(GED.Amount for the exact Department Number + "
        "Account Number)"
    ),
}


def build_finding_explanations(
    dataset: WorkingFinancialDataset,
    evaluation: ValidationEvaluation,
    manifest: RuleSetManifest,
    *,
    run_id: str,
    generation_id: str,
    actor_id: str,
    recorded_at: str,
    source_files: Mapping[str, Mapping[str, Any]],
) -> tuple[dict[str, Any], ...]:
    """Build immutable explanation projections from one sealed evaluation basis."""

    records = {
        item.record_id: item
        for item in (*dataset.budget_records, *dataset.ged_records)
    }
    accounts = {
        (
            str(item.get("department_number", "")),
            str(item.get("account_number", "")),
        ): dict(item)
        for item in evaluation.metrics["canonical_financial_dataset"]["accounts"]
    }
    definitions = {item.rule_id: item for item in manifest.rules}
    projections: list[dict[str, Any]] = []
    for finding in evaluation.findings:
        persisted_id = f"{run_id}_{finding.finding_id}"
        account = accounts.get(
            (finding.department_number, finding.account_number), {}
        )
        definition = definitions[finding.rule_id]
        transactions = tuple(
            records[record_id]
            for record_id in finding.source_records
            if record_id in records
            and records[record_id].row_kind == RowKind.GED_TRANSACTION.value
        )
        transaction_projection = tuple(
            _transaction_projection(
                item,
                source_files.get("GED", {}),
            )
            for item in transactions
        )
        transaction_amounts = [
            _decimal(item.value("amount")) for item in transactions
        ]
        parseable_total = sum(
            (
                amount
                for amount in transaction_amounts
                if amount is not None
            ),
            Decimal("0"),
        )
        complete_total = all(
            amount is not None for amount in transaction_amounts
        )
        projection = {
            "schema_version": "FINDING-EXPLANATION-1.0",
            "finding_id": persisted_id,
            "business_title": _business_title(finding, transactions),
            "severity": finding.severity,
            "review_required": True,
            "authoritative_source": "SEALED_DETERMINISTIC_VALIDATION_RUN",
            "ai_used": False,
            "what_happened": _what_happened(finding, account, transactions),
            "why_flagged": _why_flagged(finding, account, definition),
            "why_it_matters": _why_it_matters(finding),
            "supporting_evidence": _supporting_evidence(
                finding,
                account,
                dataset,
                definition,
                source_files,
            ),
            "contributing_transactions": list(transaction_projection),
            "contributing_transaction_control": {
                "transaction_count": len(transactions),
                "parseable_amount_count": sum(
                    amount is not None for amount in transaction_amounts
                ),
                "missing_or_invalid_amount_count": sum(
                    amount is None for amount in transaction_amounts
                ),
                "total_cents": _cents(parseable_total),
                "total_label": _currency(parseable_total),
                "complete": complete_total,
                "basis": (
                    "Exact source records cited by the sealed finding; "
                    "no uncited transaction is included."
                ),
            },
            "recommended_next_step": _recommended_next_step(finding),
            "technical_details_collapsed": True,
            "technical_details": {
                "rule_id": finding.rule_id,
                "rule_name": finding.rule_name,
                "rule_version": definition.version,
                "rule_set_id": manifest.rule_set_id,
                "rule_set_version": manifest.version,
                "validation_run_id": run_id,
                "generation_id": generation_id,
                "dataset_fingerprint": evaluation.dataset_fingerprint,
                "calculation_formula": FORMULAS.get(
                    finding.rule_id,
                    _optional_formula(definition),
                ),
                "rule_configuration": dict(definition.parameters or {}),
                "expected": finding.expected,
                "actual": finding.actual,
                "evidence_identifiers": list(finding.evidence),
                "source_record_ids": list(finding.source_records),
                "audit_metadata": {
                    "validation_actor_id": actor_id,
                    "projection_recorded_at": recorded_at,
                    "projection_kind": "DETERMINISTIC_TEMPLATE",
                },
            },
        }
        projections.append(projection)
    return tuple(projections)


def build_leadership_summary(
    *,
    review_id: str,
    run_id: str,
    generation_id: str,
    rule_set_id: str,
    rule_set_version: str,
    completed_at: str,
    metrics: Mapping[str, Any],
    findings: Sequence[Mapping[str, Any]],
    basis: Mapping[str, Any],
) -> dict[str, Any]:
    """Project a decision-neutral summary from recorded metrics and findings."""

    analytics = metrics.get("analytics", {})
    financial = analytics.get("financial_summary", {})
    accounts = analytics.get("comparison_by_account", ())
    finding_variance_percentages = {
        (
            str(item.get("department_number", "")),
            str(item.get("account_number", "")),
        ): item["explain_this"]["supporting_evidence"].get(
            "variance_percentage", "Unavailable"
        )
        for item in findings
        if item["explain_this"]["technical_details"]["rule_id"] == "CORE-01"
    }
    material = [
        {
            "department_number": item.get("department_number", ""),
            "account_number": item.get("account_number", ""),
            "account_name": item.get("account_name", ""),
            "budget": item.get("bgt_label", "Unavailable"),
            "actual": item.get("ged_label", "Unavailable"),
            "overrun": item.get("overrun_label", "Unavailable"),
            "variance_percentage": finding_variance_percentages.get(
                (
                    str(item.get("department_number", "")),
                    str(item.get("account_number", "")),
                ),
                "Unavailable",
            ),
            "source_record": item.get("budget_source_record"),
            "contributing_ged_rows": list(
                item.get("contributing_ged_rows", ())
            ),
        }
        for item in accounts
        if (item.get("overrun_cents") or 0) > 0
    ]
    material.sort(
        key=lambda item: (
            -_label_abs_cents(item["overrun"]),
            item["account_number"],
        )
    )
    priority = [
        {
            "finding_id": item["finding_id"],
            "severity": item["severity"],
            "title": item["business_title"],
            "department_number": item.get("department_number", ""),
            "account_number": item.get("account_number", ""),
            "review_status": item.get(
                "review_status", FindingReviewStatus.NEW.value
            ),
            "review_required": bool(item.get("review_required", True)),
            "what_happened": item["explain_this"]["what_happened"],
            "evidence_references": list(
                item["explain_this"]["technical_details"][
                    "evidence_identifiers"
                ]
            ),
        }
        for item in findings
    ]
    limitations: list[str] = []
    if not financial.get("complete", False):
        limitations.append(
            "Actual spend is incomplete because at least one required GED "
            "Amount is missing or invalid."
        )
    not_evaluated = int(metrics.get("scope_not_evaluated", 0) or 0)
    if not_evaluated:
        limitations.append(
            f"{not_evaluated} rule result(s) were not evaluated because "
            "their required source inputs were incomplete."
        )
    unmapped = int(
        metrics.get("data_quality_counts", {}).get(
            "unmapped_transactions", 0
        )
        or 0
    )
    if unmapped:
        limitations.append(
            f"{unmapped} GED transaction(s) do not map to an exact Budget "
            "department/account combination."
        )
    next_steps = list(
        dict.fromkeys(
            item["explain_this"]["recommended_next_step"]
            for item in findings
            if item.get("review_required", True)
        )
    )
    return {
        "schema_version": "LEADERSHIP-SUMMARY-1.0",
        "authoritative_source": "SEALED_DETERMINISTIC_VALIDATION_RUN",
        "ai_required": False,
        "identity": {
            "review_id": review_id,
            "validation_run_id": run_id,
            "generation_id": generation_id,
            "rule_set_id": rule_set_id,
            "rule_set_version": rule_set_version,
            "dataset_fingerprint": metrics.get(
                "canonical_financial_dataset", {}
            ).get("dataset_fingerprint"),
            "department_number": basis.get("department_number", ""),
            "department_name": basis.get("department_name", ""),
            "reporting_period": basis.get("reporting_period", ""),
            "budget_file": basis.get("budget_filename", ""),
            "ged_file": basis.get("ged_filename", ""),
            "validation_timestamp": completed_at,
        },
        "overall_status": metrics.get("overall_status", "Unavailable"),
        "budget_health": metrics.get("budget_health", "Unavailable"),
        "financial_position": {
            "budget": financial.get("bgt_label", "Unavailable"),
            "actual_spend": financial.get("ged_label", "Unavailable"),
            "actual_spend_complete": bool(financial.get("complete", False)),
            "eac": financial.get("eac_label", "Unavailable"),
            "variance": financial.get("delta_label", "Unavailable"),
            "variance_basis": "Budget DELTA (BGT - EAC)",
        },
        "ged_status": {
            "transaction_count": financial.get("ged_transaction_count", 0),
            "data_quality": metrics.get("data_quality", "Unavailable"),
            "reconciliation": metrics.get(
                "reconciliation_status", "Unavailable"
            ),
            "missing_required_data": metrics.get(
                "missing_required_data", 0
            ),
            "duplicate_transactions": metrics.get(
                "duplicate_transactions", 0
            ),
        },
        "material_variances": material,
        "highest_priority_findings": priority[:5],
        "items_requiring_human_review": [
            item for item in priority if item["review_required"]
        ],
        "recommended_next_steps": next_steps,
        "data_quality_limitations": limitations,
        "evidence_references": {
            "finding_ids": [item["finding_id"] for item in priority],
            "source_files": [
                basis.get("budget_filename", ""),
                basis.get("ged_filename", ""),
            ],
            "validation_run_id": run_id,
        },
        "decision_boundary": (
            "This summary reports recorded facts and non-binding review prompts. "
            "It does not approve, reject, resolve, or authorize a financial action."
        ),
    }


def legacy_explanation(
    finding: Mapping[str, Any],
    run: Mapping[str, Any],
    basis: Mapping[str, Any],
) -> dict[str, Any]:
    """Best-effort projection for retained runs created before schema 1.0.

    It uses only the finding's sealed values and evidence.  Missing historical
    transaction columns remain explicit rather than being reconstructed.
    """

    rule_id = str(finding["rule_id"])
    source_records = list(finding.get("source_records", ()))
    transactions = [
        {
            "record_id": record_id,
            "source_file": basis.get("ged_filename", ""),
            "workbook": basis.get("ged_filename", ""),
            "worksheet": _record_parts(record_id)[1],
            "source_row": _record_parts(record_id)[2],
            "vendor": "Unavailable in retained explanation projection",
            "journal_or_invoice_reference": (
                "Unavailable in retained explanation projection"
            ),
            "description": "Unavailable in retained explanation projection",
            "date": "Unavailable in retained explanation projection",
            "amount_label": "See sealed finding evidence",
        }
        for record_id in source_records
        if record_id.startswith("GED:")
    ]
    return {
        "schema_version": "FINDING-EXPLANATION-LEGACY-1.0",
        "finding_id": finding["finding_id"],
        "business_title": BUSINESS_TITLES.get(
            rule_id, str(finding.get("rule_name", "Validation finding"))
        ),
        "severity": finding.get("severity", "Unavailable"),
        "review_required": True,
        "authoritative_source": "SEALED_DETERMINISTIC_VALIDATION_RUN",
        "ai_used": False,
        "what_happened": finding.get("explanation", ""),
        "why_flagged": (
            f"The recorded {finding.get('rule_name', rule_id)} result failed: "
            f"{finding.get('actual', '')}"
        ),
        "why_it_matters": _generic_why_it_matters(rule_id),
        "supporting_evidence": {
            "source_files": [
                basis.get("budget_filename", ""),
                basis.get("ged_filename", ""),
            ],
            "department_number": finding.get("department_number", ""),
            "account_number": finding.get("account_number", ""),
            "expected": finding.get("expected", ""),
            "actual": finding.get("actual", ""),
            "lineage": list(finding.get("evidence_details", ())),
        },
        "contributing_transactions": transactions,
        "contributing_transaction_control": {
            "transaction_count": len(transactions),
            "parseable_amount_count": 0,
            "missing_or_invalid_amount_count": len(transactions),
            "total_cents": None,
            "total_label": "Unavailable in retained explanation projection",
            "complete": False,
            "basis": "Only fields sealed in the retained finding are shown.",
        },
        "recommended_next_step": _generic_next_step(rule_id),
        "technical_details_collapsed": True,
        "technical_details": {
            "rule_id": rule_id,
            "rule_name": finding.get("rule_name", ""),
            "rule_version": finding.get("rule_version", "Unavailable"),
            "rule_set_id": run.get("rule_set_id", ""),
            "rule_set_version": "Unavailable",
            "validation_run_id": run.get("run_id", ""),
            "generation_id": run.get("generation_id", ""),
            "dataset_fingerprint": run.get("dataset_fingerprint", ""),
            "calculation_formula": FORMULAS.get(
                rule_id, "See the retained rule definition."
            ),
            "rule_configuration": {},
            "expected": finding.get("expected", ""),
            "actual": finding.get("actual", ""),
            "evidence_identifiers": list(finding.get("evidence", ())),
            "source_record_ids": source_records,
            "audit_metadata": {
                "validation_actor_id": run.get("actor_id", ""),
                "projection_recorded_at": run.get("completed_at", ""),
                "projection_kind": "RETAINED_SEALED_VALUES_ONLY",
            },
        },
    }


def _business_title(
    finding: Finding, transactions: Sequence[Any]
) -> str:
    if finding.rule_id == "CORE-04":
        return (
            "Missing or invalid required GED value"
            if transactions
            else "Incomplete or inconsistent Budget data"
        )
    return BUSINESS_TITLES.get(finding.rule_id, finding.rule_name)


def _what_happened(
    finding: Finding,
    account: Mapping[str, Any],
    transactions: Sequence[Any],
) -> str:
    account_label = _account_label(finding, account)
    if finding.rule_id == "CORE-01":
        return (
            f"{account_label} is "
            f"{account.get('over_budget_amount_label', 'an unavailable amount')} "
            "over budget. "
            f"Recorded GED spend is {account.get('summed_ged_amount_label', 'Unavailable')} "
            f"against BGT {account.get('bgt_label', 'Unavailable')}."
        )
    if finding.rule_id == "CORE-02":
        row = transactions[0].row_number if transactions else "Unavailable"
        amount = (
            _currency(_decimal(transactions[0].value("amount")))
            if transactions and _decimal(transactions[0].value("amount")) is not None
            else "an unavailable amount"
        )
        return (
            f"GED row {row} records {amount} against Department "
            f"{finding.department_number} and Account {finding.account_number}, "
            "but that exact combination does not exist in the Budget report."
        )
    if finding.rule_id == "CORE-03":
        rows = ", ".join(str(item.row_number) for item in transactions)
        return (
            f"GED rows {rows} are identical across all 15 approved material "
            f"transaction fields. The recorded duplicate-copy exposure is "
            f"{finding.original_or_edited_value}."
        )
    if finding.rule_id == "CORE-04":
        source = transactions[0] if transactions else None
        location = (
            f"GED row {source.row_number}" if source else "The cited Budget row"
        )
        detail = finding.actual.rstrip(".")
        if detail.startswith("Missing or invalid:"):
            fields = detail.split(":", 1)[1].strip()
            return f"{location} has a missing or invalid {fields} value."
        return f"{location} contains incomplete or inconsistent required data: {detail}."
    if finding.rule_id == "CORE-05":
        return (
            f"{account_label} has {finding.expected.rstrip('.')}, while "
            f"{finding.actual[0].lower() + finding.actual[1:]}"
        )
    return (
        f"{finding.rule_name} failed for {account_label}: "
        f"{finding.actual}"
    )


def _why_flagged(
    finding: Finding,
    account: Mapping[str, Any],
    definition: RuleDefinitionVersion,
) -> str:
    if finding.rule_id == "CORE-01":
        return (
            "The exact-key GED total exceeded the account's recorded BGT. "
            f"The account-specific control value was "
            f"{account.get('bgt_label', finding.expected)}; this baseline rule "
            "does not apply a separate materiality threshold."
        )
    if finding.rule_id == "CORE-02":
        return (
            "The transaction's exact Department Number + Account Number key "
            "was absent from the sealed Budget detail keys."
        )
    if finding.rule_id == "CORE-03":
        return (
            "More than one GED row shared the same fingerprint across all 15 "
            "approved material transaction fields."
        )
    if finding.rule_id == "CORE-04":
        return (
            "At least one required value was missing or could not be parsed "
            "under the approved Budget/GED source contract."
        )
    if finding.rule_id == "CORE-05":
        return (
            "Budget ATD did not equal the complete exact-key sum of GED Amounts "
            "for the same Department Number + Account Number."
        )
    configuration = dict(definition.parameters or {})
    return (
        f"The recorded transaction did not satisfy {definition.name} version "
        f"{definition.version} with configuration {configuration}."
    )


def _why_it_matters(finding: Finding) -> str:
    return _generic_why_it_matters(finding.rule_id)


def _generic_why_it_matters(rule_id: str) -> str:
    return {
        "CORE-01": (
            "An unfavorable budget variance may require an authorized reviewer "
            "to examine spending, coding, and the current forecast."
        ),
        "CORE-02": (
            "Unmapped activity can be omitted from account-level controls or "
            "reported under an unintended financial scope until reviewed."
        ),
        "CORE-03": (
            "A duplicate copy can overstate recorded activity if both rows are "
            "treated as valid transactions."
        ),
        "CORE-04": (
            "Missing or invalid required data prevents reliable aggregation and "
            "can cause dependent rules to remain not evaluated."
        ),
        "CORE-05": (
            "A Budget-to-GED difference means the two approved sources do not "
            "present the same actual-to-date position for this account."
        ),
    }.get(
        rule_id,
        "The recorded exception may affect the completeness or interpretation "
        "of the financial review and should be examined by an authorized user.",
    )


def _supporting_evidence(
    finding: Finding,
    account: Mapping[str, Any],
    dataset: WorkingFinancialDataset,
    definition: RuleDefinitionVersion,
    source_files: Mapping[str, Mapping[str, Any]],
) -> dict[str, Any]:
    lineage = []
    for detail in finding.evidence_details:
        item = dict(detail)
        source_role = str(item.get("source_role", ""))
        source = source_files.get(source_role, {})
        item["source_file"] = source.get("file_name", "")
        item["workbook"] = source.get("file_name", "")
        lineage.append(item)
    vendors = list(account.get("vendors", ()))
    periods = list(account.get("fiscal_periods", ()))
    return {
        "source_files": [
            {
                "source_role": role,
                "file_name": source.get("file_name", ""),
                "sha256": source.get("sha256", ""),
            }
            for role, source in sorted(source_files.items())
        ],
        "department_number": finding.department_number,
        "department_name": account.get(
            "department_name", dataset.department_name
        ),
        "account_number": finding.account_number,
        "account_name": account.get("account_name", ""),
        "vendors": vendors,
        "fiscal_periods": periods,
        "reporting_period": dataset.reporting_period,
        "budget": account.get("bgt_label", "Unavailable"),
        "budget_atd": account.get("atd_label", "Unavailable"),
        "etc": account.get("etc_label", "Unavailable"),
        "eac": account.get("eac_label", "Unavailable"),
        "ged_actual": account.get(
            "summed_ged_amount_label", "Unavailable"
        ),
        "variance": account.get(
            "over_budget_amount_label",
            account.get(
                "budget_to_ged_difference_label", "Unavailable"
            ),
        ),
        "variance_percentage": _variance_percentage(finding),
        "expected": finding.expected,
        "actual": finding.actual,
        "applicable_rule": finding.rule_name,
        "rule_version": definition.version,
        "threshold": _threshold_label(finding, account, definition),
        "lineage": lineage,
        "contributing_source_records": list(finding.source_records),
    }


def _threshold_label(
    finding: Finding,
    account: Mapping[str, Any],
    definition: RuleDefinitionVersion,
) -> str:
    if finding.rule_id == "CORE-01":
        return (
            f"Account BGT {account.get('bgt_label', 'Unavailable')} "
            "(no separate materiality threshold)"
        )
    if finding.rule_id == "CORE-02":
        return "One exact Budget Department Number + Account Number match"
    if finding.rule_id == "CORE-03":
        return "One row per approved all-material-field fingerprint"
    if finding.rule_id == "CORE-04":
        return "All approved required values present and parseable"
    if finding.rule_id == "CORE-05":
        return "Exact equality between Budget ATD and exact-key GED sum"
    return str(dict(definition.parameters or {}))


def _recommended_next_step(finding: Finding) -> str:
    return _generic_next_step(finding.rule_id)


def _generic_next_step(rule_id: str) -> str:
    return {
        "CORE-01": (
            "Review the contributing transactions and determine whether a "
            "coding correction, explanation, reforecast, or budget review is "
            "appropriate under your organization's approval process."
        ),
        "CORE-02": (
            "Review the cited transaction and Budget coding, then determine "
            "whether an authorized reviewed-data correction is appropriate."
        ),
        "CORE-03": (
            "Compare both cited rows with the source evidence and document "
            "whether each transaction is valid before making any correction."
        ),
        "CORE-04": (
            "Review the cited source cell and, if supported by source evidence, "
            "record a reviewed value before revalidating."
        ),
        "CORE-05": (
            "Review the Budget ATD and exact-key GED records, then document or "
            "correct the difference through the authorized review workflow."
        ),
    }.get(
        rule_id,
        "Review the cited evidence and rule configuration before an authorized "
        "user records any correction or disposition.",
    )


def _transaction_projection(
    record: Any, source: Mapping[str, Any]
) -> dict[str, Any]:
    amount = _decimal(record.value("amount"))
    journal = _text(record.value("journal_number"))
    edited_fields = [
        field_name
        for field_name in record.current
        if record.current.get(field_name) != record.original.get(field_name)
    ]
    return {
        "record_id": record.record_id,
        "source_file": source.get("file_name", ""),
        "workbook": source.get("file_name", ""),
        "worksheet": record.worksheet,
        "source_row": record.row_number,
        "department_number": _text(record.value("department_number")),
        "account_number": _text(record.value("account_number")),
        "account_name": _text(record.value("account_name")),
        "vendor": _text(record.value("vendor_name")) or "No vendor recorded",
        "journal_or_invoice_reference": journal or "No reference recorded",
        "journal_number": journal,
        "description": (
            _text(record.value("journal_line_description"))
            or _text(record.value("journal_description"))
        ),
        "journal_description": _text(
            record.value("journal_description")
        ),
        "date": _json_value(record.value("journal_date")),
        "fiscal_period": _text(record.value("fiscal_period")),
        "amount_cents": _cents(amount),
        "amount_label": (
            _currency(amount) if amount is not None else "Missing or invalid"
        ),
        "amount_complete": amount is not None,
        "value_origin": "Edited" if edited_fields else "Original",
        "edited_fields": edited_fields,
        "source_cells": dict(record.cells),
    }


def _optional_formula(definition: RuleDefinitionVersion) -> str:
    if definition.evaluator_key == "ged_amount_threshold":
        parameters = definition.parameters or {}
        return (
            f"GED.Amount {parameters.get('operator', '?')} "
            f"{parameters.get('threshold', 'Unavailable')}"
        )
    return "See the sealed rule definition."


def _account_label(
    finding: Finding, account: Mapping[str, Any]
) -> str:
    name = str(account.get("account_name", "")).strip()
    return (
        f"{finding.account_number} {name}".strip()
        if finding.account_number
        else "The cited financial record"
    )


def _decimal(value: Any) -> Decimal | None:
    if value is None or isinstance(value, bool):
        return None
    text = str(value).strip().replace(",", "").replace("$", "")
    if text in {"", ".", "-", "—"}:
        return None
    if text.startswith("(") and text.endswith(")"):
        text = "-" + text[1:-1]
    try:
        result = Decimal(text)
    except (InvalidOperation, ValueError):
        return None
    return result if result.is_finite() else None


def _currency(value: Decimal) -> str:
    quantized = value.quantize(Decimal("0.01"))
    prefix = "-$" if quantized < 0 else "$"
    return f"{prefix}{abs(quantized):,.2f}"


def _cents(value: Decimal | None) -> int | None:
    if value is None:
        return None
    return int((value * Decimal("100")).quantize(Decimal("1")))


def _text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _json_value(value: Any) -> Any:
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    return value


def _record_parts(record_id: str) -> tuple[str, str, int | None]:
    parts = record_id.split(":")
    if len(parts) < 3:
        return "", "", None
    try:
        row = int(parts[-1])
    except ValueError:
        row = None
    return parts[0], ":".join(parts[1:-1]), row


def _variance_percentage(finding: Finding) -> str:
    if finding.rule_id != "CORE-01":
        return "Not applicable"
    match = re.search(
        r"overrun percentage\s+(-?[0-9]+(?:\.[0-9]+)?%)",
        finding.actual,
        flags=re.IGNORECASE,
    )
    return match.group(1) if match else "Unavailable"


def _label_abs_cents(label: Any) -> int:
    value = _decimal(label)
    return abs(_cents(value) or 0)
