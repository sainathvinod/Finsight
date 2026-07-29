"""Deterministic V2 financial-validation domain.

This module intentionally does not reuse the legacy account-only validation path.
It evaluates the supplied Budget/GED contract at Department Number + Account
Number grain and emits a complete, reproducible PASS/FAIL/NOT_EVALUATED ledger.
"""
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, replace
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from enum import Enum
from typing import Any, Mapping, Sequence

from finsight.domain.source_intake import RowKind, SourceInspection


LEGACY_CORE_RULE_SET_ID = "FINSIGHT-CORE-1.0"
CORE_RULE_SET_ID = "FINSIGHT-CORE-2.0"
CORE_RULE_VERSIONS = (
    ("CORE-05", "Budget-to-GED Reconciliation", "2.0.0", "High"),
    ("CORE-01", "Budget Overrun", "2.0.0", "High"),
    ("CORE-02", "Valid Account Coding", "2.0.0", "High"),
    ("CORE-04", "Complete and Correct Data", "2.0.0", "High"),
    ("CORE-03", "Duplicate Transactions", "2.0.0", "Medium"),
)
CORE_EVALUATOR_KEYS = {
    "CORE-01": "actual_not_over_budget",
    "CORE-02": "valid_mapping",
    "CORE-03": "exact_duplicates",
    "CORE-04": "required_fields",
    "CORE-05": "atd_reconciliation",
}


class RuleManifestError(ValueError):
    pass


class ResultStatus(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    NOT_EVALUATED = "NOT_EVALUATED"


@dataclass(frozen=True)
class ReviewRecord:
    record_id: str
    source_role: str
    worksheet: str
    row_number: int
    row_kind: str
    original: Mapping[str, Any]
    current: Mapping[str, Any]
    cells: Mapping[str, str]

    def value(self, field_name: str) -> Any:
        return self.current.get(field_name)


@dataclass(frozen=True)
class WorkingFinancialDataset:
    review_id: str
    department_number: str
    department_name: str
    reporting_period: str
    budget_fingerprint: str
    ged_fingerprint: str
    budget_records: tuple[ReviewRecord, ...]
    ged_records: tuple[ReviewRecord, ...]
    correction_count: int = 0

    @property
    def budget_details(self) -> tuple[ReviewRecord, ...]:
        return tuple(
            row for row in self.budget_records
            if row.row_kind == RowKind.BUDGET_DETAIL.value
        )

    @property
    def ged_transactions(self) -> tuple[ReviewRecord, ...]:
        return tuple(
            row for row in self.ged_records
            if row.row_kind == RowKind.GED_TRANSACTION.value
        )

    @property
    def fingerprint(self) -> str:
        payload = {
            "review_id": self.review_id,
            "department_number": self.department_number,
            "reporting_period": self.reporting_period,
            "budget_fingerprint": self.budget_fingerprint,
            "ged_fingerprint": self.ged_fingerprint,
            "records": [
                [row.record_id, _json_value(row.current)]
                for row in (*self.budget_records, *self.ged_records)
            ],
        }
        return hashlib.sha256(_canonical_json(payload).encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class VerifiedFinancialAccount:
    """One deterministic Department + Account financial scope.

    The source rows remain immutable ``ReviewRecord`` instances.  This value
    object owns the financial join and completeness semantics used by aggregate
    rules and every downstream projection.
    """

    department_number: str
    department_name: str
    account_number: str
    account_name: str
    budget_record: ReviewRecord | None
    ged_records: tuple[ReviewRecord, ...]
    bgt: Decimal | None
    atd: Decimal | None
    etc: Decimal | None
    eac: Decimal | None
    delta: Decimal | None
    parseable_ged_amount: Decimal
    summed_ged_amount: Decimal | None
    missing_amount_count: int
    invalid_fiscal_period_count: int
    budget_to_ged_difference: Decimal | None
    budget_utilization_percentage: Decimal | None
    remaining_budget: Decimal | None
    over_budget_amount: Decimal | None
    budget_edited_fields: tuple[str, ...]
    edited_ged_records: tuple[str, ...]
    edited_ged_field_count: int

    @property
    def key(self) -> tuple[str, str]:
        return self.department_number, self.account_number

    @property
    def scope_id(self) -> str:
        return f"{self.department_number}|{self.account_number}"

    @property
    def has_budget_mapping(self) -> bool:
        return self.budget_record is not None

    @property
    def aggregation_complete(self) -> bool:
        return (
            self.summed_ged_amount is not None
            and self.missing_amount_count == 0
            and self.invalid_fiscal_period_count == 0
        )


@dataclass(frozen=True)
class CanonicalFinancialDataset:
    """Verified financial hierarchy used by rules and recorded projections."""

    review_id: str
    department_number: str
    department_name: str
    reporting_period: str
    dataset_fingerprint: str
    accounts: tuple[VerifiedFinancialAccount, ...]
    unscoped_ged_records: tuple[ReviewRecord, ...]
    budget_records: tuple[ReviewRecord, ...]
    ged_records: tuple[ReviewRecord, ...]

    @property
    def budget_accounts(self) -> tuple[VerifiedFinancialAccount, ...]:
        return tuple(item for item in self.accounts if item.has_budget_mapping)

    @property
    def account_index(self) -> Mapping[tuple[str, str], VerifiedFinancialAccount]:
        return {item.key: item for item in self.accounts}


@dataclass(frozen=True)
class RuleScopeResult:
    rule_id: str
    scope_id: str
    status: ResultStatus
    department_number: str = ""
    account_number: str = ""
    source_records: tuple[str, ...] = ()
    expected: str = ""
    actual: str = ""
    explanation: str = ""
    evidence: tuple[str, ...] = ()
    evidence_details: tuple[Mapping[str, Any], ...] = ()


@dataclass(frozen=True)
class Finding:
    finding_id: str
    rule_id: str
    rule_name: str
    severity: str
    department_number: str
    account_number: str
    source_records: tuple[str, ...]
    original_or_edited_value: str
    expected: str
    actual: str
    explanation: str
    recommended_action: str
    evidence: tuple[str, ...]
    evidence_details: tuple[Mapping[str, Any], ...] = ()


@dataclass(frozen=True)
class RuleExecution:
    rule_id: str
    rule_name: str
    version: str
    baseline_status: str
    status: ResultStatus
    pass_count: int
    fail_count: int
    not_evaluated_count: int
    purpose: str = ""


@dataclass(frozen=True)
class RuleDefinitionVersion:
    rule_id: str
    name: str
    version: str
    severity: str
    baseline_status: str
    evaluator_key: str
    ordinal: int
    classification: str = "CORE_MANDATORY"
    purpose: str = ""
    required_fields: tuple[str, ...] = ()
    grouping_keys: tuple[str, ...] = ()
    parameters: Mapping[str, Any] | None = None


@dataclass(frozen=True)
class RuleSetManifest:
    rule_set_id: str
    version: str
    rules: tuple[RuleDefinitionVersion, ...]
    protected_baseline_id: str = CORE_RULE_SET_ID


def core_rule_manifest() -> RuleSetManifest:
    return RuleSetManifest(
        CORE_RULE_SET_ID,
        "1.0.0",
        tuple(
            RuleDefinitionVersion(
                rule_id,
                name,
                version,
                severity,
                "PROTECTED_BASELINE",
                CORE_EVALUATOR_KEYS[rule_id],
                ordinal,
                "CORE_MANDATORY",
                _core_purpose(rule_id),
                _core_required_fields(rule_id),
                _core_grouping_keys(rule_id),
                {},
            )
            for ordinal, (rule_id, name, version, severity) in enumerate(
                CORE_RULE_VERSIONS, 1
            )
        ),
    )


def _validate_manifest(manifest: RuleSetManifest) -> None:
    if not manifest.rule_set_id or not manifest.version or not manifest.rules:
        raise RuleManifestError("A sealed Rule Set identity and members are required.")
    ordinals = [item.ordinal for item in manifest.rules]
    if ordinals != sorted(ordinals) or len(set(ordinals)) != len(ordinals):
        raise RuleManifestError("Rule Set members must have unique stable ordering.")
    rule_ids = [item.rule_id for item in manifest.rules]
    if len(set(rule_ids)) != len(rule_ids):
        raise RuleManifestError("A Rule Set cannot contain a duplicate Rule ID.")
    protected = {item[0] for item in CORE_RULE_VERSIONS}
    missing = sorted(protected - set(rule_ids))
    if missing:
        raise RuleManifestError(
            "Protected baseline rule(s) are missing: " + ", ".join(missing)
        )
    for item in manifest.rules:
        if item.rule_id in protected and item.baseline_status != "PROTECTED_BASELINE":
            raise RuleManifestError(
                f"{item.rule_id} is not marked as a protected baseline rule."
            )
        if item.rule_id in protected:
            expected_evaluator = CORE_EVALUATOR_KEYS[item.rule_id]
            if item.evaluator_key != expected_evaluator:
                raise RuleManifestError(
                    f"{item.rule_id} must use evaluator {expected_evaluator!r}."
                )
            if item.classification != "CORE_MANDATORY":
                raise RuleManifestError(
                    f"{item.rule_id} must remain a Core Mandatory rule."
                )
        elif item.classification != "OPTIONAL_CONFIGURABLE":
            raise RuleManifestError(
                f"{item.rule_id} has an unsupported rule classification."
            )
        if item.evaluator_key == "ged_amount_threshold":
            parameters = item.parameters or {}
            if set(parameters) != {"operator", "threshold"}:
                raise RuleManifestError(
                    "GED Amount threshold rules require operator and threshold."
                )
            if parameters["operator"] not in {"EQ", "NE", "LT", "LTE", "GT", "GTE"}:
                raise RuleManifestError("The optional-rule operator is not allowlisted.")
            if _money(parameters["threshold"]) is None:
                raise RuleManifestError(
                    "The optional-rule threshold must be an exact financial amount."
                )
        elif item.rule_id not in protected:
            raise RuleManifestError(
                f"Evaluator {item.evaluator_key!r} is not allowlisted."
            )


@dataclass(frozen=True)
class ValidationEvaluation:
    rule_set_id: str
    protected_baseline_id: str
    dataset_fingerprint: str
    executions: tuple[RuleExecution, ...]
    scope_results: tuple[RuleScopeResult, ...]
    findings: tuple[Finding, ...]
    metrics: Mapping[str, Any]


def dataset_from_inspections(
    review_id: str,
    budget: SourceInspection,
    ged: SourceInspection,
    *,
    department_number: str,
    department_name: str,
    reporting_period: str,
    corrections: Sequence[Mapping[str, Any]] = (),
) -> WorkingFinancialDataset:
    """Build a review-local dataset without modifying either source workbook."""

    latest: dict[tuple[str, str], Any] = {}
    for correction in corrections:
        latest[(str(correction["record_id"]), str(correction["field_name"]))] = (
            correction.get("new_value")
        )

    def records(inspection: SourceInspection) -> tuple[ReviewRecord, ...]:
        output: list[ReviewRecord] = []
        worksheet = inspection.worksheet_name or inspection.role.value
        for extracted in inspection.rows:
            original: dict[str, Any] = {}
            current: dict[str, Any] = {}
            cells: dict[str, str] = {}
            record_id = (
                f"{inspection.role.value}:{worksheet}:{extracted.row_number}"
            )
            for cell in extracted.cells:
                # Formula cells validate against their stored result while retaining
                # the original formula in source lineage.
                value = (
                    cell.cached_value
                    if cell.formula is not None and cell.cached_value is not None
                    else cell.raw_value
                )
                original[cell.field_name] = value
                current[cell.field_name] = latest.get(
                    (record_id, cell.field_name), value
                )
                cells[cell.field_name] = cell.cell
            output.append(
                ReviewRecord(
                    record_id=record_id,
                    source_role=inspection.role.value,
                    worksheet=worksheet,
                    row_number=extracted.row_number,
                    row_kind=extracted.kind.value,
                    original=original,
                    current=current,
                    cells=cells,
                )
            )
        return tuple(output)

    return WorkingFinancialDataset(
        review_id=review_id,
        department_number=department_number,
        department_name=department_name,
        reporting_period=reporting_period,
        budget_fingerprint=budget.sha256,
        ged_fingerprint=ged.sha256,
        budget_records=records(budget),
        ged_records=records(ged),
        correction_count=len(corrections),
    )


def build_canonical_financial_dataset(
    dataset: WorkingFinancialDataset,
) -> CanonicalFinancialDataset:
    """Join the reviewed Budget and GED rows at the approved exact key.

    Duplicate GED rows intentionally remain in the aggregation.  An account
    with any missing/unparseable Amount or Fiscal Period receives no completed
    GED total; its parseable subtotal is retained only as control evidence.
    """

    budget_by_key: dict[tuple[str, str], ReviewRecord] = {}
    ordered_keys: list[tuple[str, str]] = []
    for record in sorted(dataset.budget_details, key=lambda item: item.row_number):
        account = _account(record.value("account_number"))
        if account is None:
            # Keep the source-visible value in the hierarchy so CORE-04 can
            # explain it, but never let it become a valid GED mapping key.
            account = _text(record.value("account_number"))
        key = (dataset.department_number, account)
        if key not in budget_by_key:
            budget_by_key[key] = record
            ordered_keys.append(key)

    ged_by_key: dict[tuple[str, str], list[ReviewRecord]] = {}
    unscoped: list[ReviewRecord] = []
    for record in sorted(dataset.ged_transactions, key=lambda item: item.row_number):
        department = _department(record.value("department_number"))
        account = _account(record.value("account_number"))
        if department is None or account is None:
            unscoped.append(record)
            continue
        key = (department, account)
        ged_by_key.setdefault(key, []).append(record)
        if key not in budget_by_key and key not in ordered_keys:
            ordered_keys.append(key)

    accounts: list[VerifiedFinancialAccount] = []
    for department, account in ordered_keys:
        budget = budget_by_key.get((department, account))
        transactions = tuple(ged_by_key.get((department, account), ()))
        bgt = _money(budget.value("bgt")) if budget else None
        atd = _money(budget.value("atd")) if budget else None
        etc = _money(budget.value("etc")) if budget else None
        eac = _money(budget.value("eac")) if budget else None
        delta = _money(budget.value("delta")) if budget else None
        parsed_amounts = [_money(record.value("amount")) for record in transactions]
        fiscal_validity = [
            _fiscal_period(record.value("fiscal_period"))
            for record in transactions
        ]
        parseable_ged_amount = sum(
            (value for value in parsed_amounts if value is not None),
            Decimal("0"),
        )
        missing_amount_count = sum(value is None for value in parsed_amounts)
        invalid_fiscal_period_count = sum(not value for value in fiscal_validity)
        aggregate_complete = (
            missing_amount_count == 0 and invalid_fiscal_period_count == 0
        )
        summed_ged_amount = (
            parseable_ged_amount if aggregate_complete else None
        )
        budget_to_ged_difference = (
            atd - summed_ged_amount
            if atd is not None and summed_ged_amount is not None
            else None
        )
        remaining_budget = (
            bgt - summed_ged_amount
            if bgt is not None and summed_ged_amount is not None
            else None
        )
        over_budget_amount = (
            max(-remaining_budget, Decimal("0"))
            if remaining_budget is not None
            else None
        )
        utilization = (
            (
                (summed_ged_amount / bgt) * Decimal("100")
            ).quantize(Decimal("0.01"))
            if bgt not in (None, Decimal("0"))
            and summed_ged_amount is not None
            else None
        )
        account_name = (
            _text(budget.value("account_name"))
            if budget
            else (
                _text(transactions[0].value("account_name"))
                if transactions
                else ""
            )
        )
        department_name = (
            dataset.department_name
            if budget
            else (
                _text(transactions[0].value("department_name"))
                if transactions
                else dataset.department_name
            )
        )
        budget_edited_fields = (
            tuple(
                field_name
                for field_name in budget.current
                if budget.current.get(field_name) != budget.original.get(field_name)
            )
            if budget
            else ()
        )
        edited_ged_records = tuple(
            record.record_id
            for record in transactions
            if any(
                record.current.get(field_name) != record.original.get(field_name)
                for field_name in record.current
            )
        )
        edited_ged_field_count = sum(
            record.current.get(field_name) != record.original.get(field_name)
            for record in transactions
            for field_name in record.current
        )
        accounts.append(
            VerifiedFinancialAccount(
                department,
                department_name,
                account,
                account_name,
                budget,
                transactions,
                bgt,
                atd,
                etc,
                eac,
                delta,
                parseable_ged_amount,
                summed_ged_amount,
                missing_amount_count,
                invalid_fiscal_period_count,
                budget_to_ged_difference,
                utilization,
                remaining_budget,
                over_budget_amount,
                budget_edited_fields,
                edited_ged_records,
                edited_ged_field_count,
            )
        )

    return CanonicalFinancialDataset(
        dataset.review_id,
        dataset.department_number,
        dataset.department_name,
        dataset.reporting_period,
        dataset.fingerprint,
        tuple(accounts),
        tuple(unscoped),
        dataset.budget_records,
        dataset.ged_records,
    )


class CoreFinancialValidationEngine:
    """Allowlisted evaluators for the five protected, versioned baseline rules."""

    def evaluate(
        self,
        dataset: WorkingFinancialDataset,
        manifest: RuleSetManifest | None = None,
    ) -> ValidationEvaluation:
        manifest = manifest or core_rule_manifest()
        _validate_manifest(manifest)
        canonical = build_canonical_financial_dataset(dataset)
        registry = {
            "actual_not_over_budget": self._actual_not_over_budget,
            "valid_mapping": self._valid_mapping,
            "exact_duplicates": self._exact_duplicates,
            "required_fields": self._required_fields,
            "atd_reconciliation": self._atd_reconciliation,
            "ged_amount_threshold": self._ged_amount_threshold,
        }
        scope_results: list[RuleScopeResult] = []
        findings: list[Finding] = []
        for definition in manifest.rules:
            evaluator = registry.get(definition.evaluator_key)
            if evaluator is None:
                raise RuleManifestError(
                    f"Evaluator {definition.evaluator_key!r} is not allowlisted."
                )
            if definition.evaluator_key == "ged_amount_threshold":
                result, result_findings = evaluator(dataset, definition)
            elif definition.evaluator_key in {
                "actual_not_over_budget",
                "atd_reconciliation",
            }:
                result, result_findings = evaluator(dataset, canonical)
            else:
                result, result_findings = evaluator(dataset)
            if any(item.rule_id != definition.rule_id for item in result):
                raise RuleManifestError(
                    f"Evaluator {definition.evaluator_key!r} returned the wrong Rule ID."
                )
            result = [
                _result_with_structured_evidence(dataset, item) for item in result
            ]
            scope_results.extend(result)
            findings.extend(
                Finding(
                    item.finding_id,
                    item.rule_id,
                    definition.name,
                    definition.severity,
                    item.department_number,
                    item.account_number,
                    item.source_records,
                    item.original_or_edited_value,
                    item.expected,
                    item.actual,
                    item.explanation,
                    item.recommended_action,
                    item.evidence,
                    _structured_evidence(
                        dataset, item.source_records, item.evidence
                    ),
                )
                for item in result_findings
            )

        executions: list[RuleExecution] = []
        for definition in manifest.rules:
            rule_results = [
                item
                for item in scope_results
                if item.rule_id == definition.rule_id
            ]
            counts = {
                status: sum(item.status is status for item in rule_results)
                for status in ResultStatus
            }
            # Incomplete coverage is more important than a failed evaluated scope.
            status = (
                ResultStatus.NOT_EVALUATED
                if counts[ResultStatus.NOT_EVALUATED]
                else (
                    ResultStatus.FAIL
                    if counts[ResultStatus.FAIL]
                    else ResultStatus.PASS
                )
            )
            executions.append(
                RuleExecution(
                    definition.rule_id,
                    definition.name,
                    definition.version,
                    definition.baseline_status,
                    status,
                    counts[ResultStatus.PASS],
                    counts[ResultStatus.FAIL],
                    counts[ResultStatus.NOT_EVALUATED],
                    definition.purpose,
                )
            )

        ordered_findings = tuple(
            sorted(
                findings,
                key=lambda item: (
                    {"Critical": 0, "High": 1, "Medium": 2, "Low": 3}.get(
                        item.severity, 9
                    ),
                    item.rule_id,
                    item.department_number,
                    item.account_number,
                    item.source_records,
                ),
            )
        )
        failed_rules = sum(
            item.status is ResultStatus.FAIL for item in executions
        )
        incomplete_rules = sum(
            item.status is ResultStatus.NOT_EVALUATED for item in executions
        )
        budget_totals = _budget_totals(dataset.budget_details)
        ged_totals = _ged_totals(canonical)
        account_comparisons = _account_comparisons(
            canonical, scope_results, ordered_findings
        )
        canonical_projection = _canonical_account_projection(
            canonical, scope_results, ordered_findings
        )
        financial_controls = _financial_control_report(
            canonical, budget_totals, ged_totals
        )
        severity_counts = {
            severity: sum(item.severity == severity for item in ordered_findings)
            for severity in ("Critical", "High", "Medium", "Low")
        }
        rule_severity = {
            definition.rule_id: definition.severity
            for definition in manifest.rules
        }
        budget_excluded = len(dataset.budget_records) - len(dataset.budget_details)
        ged_excluded = len(dataset.ged_records) - len(dataset.ged_transactions)
        metrics = {
            "overall_status": "Incomplete" if incomplete_rules else (
                "Attention Required" if failed_rules else "Healthy"
            ),
            "rag_status": "At Risk (Red)" if findings or incomplete_rules else "On Track (Green)",
            "budget_health": "Incomplete" if incomplete_rules else (
                "Attention Required" if any(f.rule_id == "CORE-01" for f in findings) else "Healthy"
            ),
            "data_quality": "Attention Required" if any(
                f.rule_id in {"CORE-02", "CORE-03", "CORE-04"} for f in findings
            ) else "Healthy",
            "reconciliation_status": "Incomplete" if any(
                item.rule_id == "CORE-05"
                and item.status is ResultStatus.NOT_EVALUATED
                for item in scope_results
            ) else (
                "Attention Required"
                if any(f.rule_id == "CORE-05" for f in findings)
                else "Reconciled"
            ),
            "rules_executed": len(executions),
            "rules_passed": sum(item.status is ResultStatus.PASS for item in executions),
            "rules_failed": failed_rules,
            "rules_not_evaluated": incomplete_rules,
            "rule_results": len(scope_results),
            "scope_passed": sum(item.status is ResultStatus.PASS for item in scope_results),
            "scope_failed": sum(item.status is ResultStatus.FAIL for item in scope_results),
            "scope_not_evaluated": sum(
                item.status is ResultStatus.NOT_EVALUATED for item in scope_results
            ),
            "findings": len(ordered_findings),
            "budget_overruns": sum(f.rule_id == "CORE-01" for f in findings),
            "duplicate_transactions": sum(f.rule_id == "CORE-03" for f in findings),
            "missing_required_data": sum(f.rule_id == "CORE-04" for f in findings),
            "reconciliation_findings": sum(f.rule_id == "CORE-05" for f in findings),
            "reconciliation_not_evaluated": sum(
                item.rule_id == "CORE-05"
                and item.status is ResultStatus.NOT_EVALUATED
                for item in scope_results
            ),
            "budget_records": len(dataset.budget_details),
            "ged_transactions": len(dataset.ged_transactions),
            "corrections": dataset.correction_count,
            "financial_totals": {
                "bgt": budget_totals["bgt"],
                "atd": budget_totals["atd"],
                "etc": budget_totals["etc"],
                "eac": budget_totals["eac"],
                "delta": budget_totals["delta"],
                "ged": ged_totals["ged"],
                "mapped_ged": ged_totals["mapped_ged"],
                "unmapped_ged": ged_totals["unmapped_ged"],
                "ged_is_complete": ged_totals["ged_is_complete"],
                "variance_bgt_to_ged": _currency(
                    budget_totals["bgt_decimal"] - ged_totals["ged_decimal"]
                ),
            },
            "findings_by_severity": severity_counts,
            "rule_severity": rule_severity,
            "account_comparisons": account_comparisons,
            "canonical_financial_dataset": {
                "schema_version": "CFD-1.0",
                "matching_grain": [
                    "department_number",
                    "account_number",
                ],
                "department_number": canonical.department_number,
                "department_name": canonical.department_name,
                "reporting_period": canonical.reporting_period,
                "dataset_fingerprint": canonical.dataset_fingerprint,
                "accounts": canonical_projection,
                "unscoped_ged_records": [
                    item.record_id for item in canonical.unscoped_ged_records
                ],
            },
            "financial_control_report": financial_controls,
            "field_coverage": _field_coverage_projection(),
            "data_quality_counts": {
                "missing_fields": _missing_required_value_count(dataset),
                "invalid_values": _invalid_required_value_count(dataset),
                "duplicate_records": _duplicate_copy_count(dataset),
                "excluded_records": budget_excluded + ged_excluded,
                "excluded_budget_rows": budget_excluded,
                "excluded_ged_rows": ged_excluded,
                "parsing_issues": sum(
                    item.rule_id == "CORE-04" for item in ordered_findings
                ),
                "unmapped_transactions": sum(
                    item.rule_id == "CORE-02" for item in ordered_findings
                ),
                # Report-level mismatches are an ingestion gate. A sealed run can only
                # exist after both values matched, so these values are necessarily zero.
                "department_mismatches": 0,
                "period_mismatches": 0,
            },
        }
        metrics["analytics"] = _analytics_projection(
            dataset,
            tuple(executions),
            ordered_findings,
            account_comparisons,
            budget_totals,
            ged_totals,
            canonical,
            canonical_projection,
        )
        return ValidationEvaluation(
            manifest.rule_set_id,
            manifest.protected_baseline_id,
            dataset.fingerprint,
            tuple(executions),
            tuple(scope_results),
            ordered_findings,
            metrics,
        )

    def _budget_scopes(self, dataset: WorkingFinancialDataset):
        for row in sorted(dataset.budget_details, key=lambda item: item.row_number):
            account = _account(row.value("account_number"))
            yield row, dataset.department_number, account

    @staticmethod
    def _ged_by_key(dataset: WorkingFinancialDataset):
        grouped: dict[tuple[str, str], list[ReviewRecord]] = {}
        for row in dataset.ged_transactions:
            department = _department(row.value("department_number"))
            account = _account(row.value("account_number"))
            if department and account:
                grouped.setdefault((department, account), []).append(row)
        return grouped

    def _actual_not_over_budget(self, dataset, canonical):
        results: list[RuleScopeResult] = []
        findings: list[Finding] = []
        for financial in canonical.budget_accounts:
            budget = financial.budget_record
            assert budget is not None
            department = financial.department_number
            account = financial.account_number
            transactions = financial.ged_records
            bgt = financial.bgt
            source_records = (budget.record_id,) + tuple(
                row.record_id for row in transactions
            )
            scope = financial.scope_id
            if bgt is None or not financial.aggregation_complete:
                results.append(
                    RuleScopeResult(
                        "CORE-01", scope, ResultStatus.NOT_EVALUATED,
                        department, account, source_records,
                        expected="Eligible GED Amounts must be complete before comparison.",
                        actual="Required financial input is missing or invalid.",
                        explanation="This account was not partially summed; correct the source data and rerun.",
                        evidence=_evidence_for(budget, "bgt")
                        + tuple(
                            evidence
                            for row in transactions
                            for evidence in _evidence_for(row, "amount")
                        ),
                    )
                )
                continue
            actual = financial.summed_ged_amount
            assert actual is not None
            if actual > bgt:
                overrun = actual - bgt
                overrun_percentage = (
                    "Not available because BGT is zero"
                    if bgt == 0
                    else (
                        f"{((overrun / bgt) * Decimal('100')).quantize(Decimal('0.01'))}%"
                    )
                )
                result = RuleScopeResult(
                    "CORE-01", scope, ResultStatus.FAIL,
                    department, account, source_records,
                    expected=f"Actual spend must be at or below {_currency(bgt)}.",
                    actual=(
                        f"BGT {_currency(bgt)}; GED spend {_currency(actual)}; "
                        f"overrun {_currency(overrun)}; overrun percentage "
                        f"{overrun_percentage}."
                    ),
                    explanation="Summed GED spend exceeds the planned Budget BGT for the exact department/account.",
                    evidence=_evidence_for(budget, "bgt")
                    + tuple(
                        evidence
                        for row in transactions
                        for evidence in _evidence_for(row, "amount")
                    ),
                )
                results.append(result)
                findings.append(
                    _finding(
                        dataset, result, "High", str(budget.value("bgt")),
                        "Review the transactions and obtain a budget adjustment or corrective action."
                    )
                )
            else:
                results.append(
                    RuleScopeResult(
                        "CORE-01", scope, ResultStatus.PASS,
                        department, account, source_records,
                        expected=f"Actual spend at or below {_currency(bgt)}.",
                        actual=_currency(actual),
                        explanation="Actual GED spend is within BGT.",
                    )
                )
        return results, findings

    def _valid_mapping(self, dataset):
        valid = {
            (department, account)
            for _row, department, account in self._budget_scopes(dataset)
            if department and account
        }
        results: list[RuleScopeResult] = []
        findings: list[Finding] = []
        for row in sorted(dataset.ged_transactions, key=lambda item: item.row_number):
            department = _department(row.value("department_number"))
            account = _account(row.value("account_number"))
            scope = row.record_id
            if not department or not account:
                results.append(
                    RuleScopeResult(
                        "CORE-02", scope, ResultStatus.NOT_EVALUATED,
                        department or "", account or "", (row.record_id,),
                        expected="Parseable Department Number and Account Number.",
                        actual="Identifier is missing or invalid.",
                        explanation="Mapping cannot be evaluated until both identifiers are valid.",
                        evidence=_evidence_for(row, "department_number")
                        + _evidence_for(row, "account_number"),
                    )
                )
            elif (department, account) not in valid:
                result = RuleScopeResult(
                    "CORE-02", scope, ResultStatus.FAIL,
                    department, account, (row.record_id,),
                    expected="One exact Budget Department Number + Account Number match.",
                    actual=f"No Budget match for {department} / {account}.",
                    explanation="The GED transaction does not map to a valid Budget detail combination.",
                    evidence=_evidence_for(row, "department_number")
                    + _evidence_for(row, "account_number")
                    + _evidence_for(row, "journal_number")
                    + _evidence_for(row, "amount"),
                )
                results.append(result)
                findings.append(
                    _finding(
                        dataset, result, "High",
                        f"{row.value('department_number')} / {row.value('account_number')}",
                        "Correct the reviewed department/account or add the authorized Budget combination."
                    )
                )
            else:
                results.append(
                    RuleScopeResult(
                        "CORE-02", scope, ResultStatus.PASS,
                        department, account, (row.record_id,),
                        expected="Exact Budget mapping.",
                        actual=f"Mapped to {department} / {account}.",
                        explanation="The transaction maps to one Budget detail scope.",
                    )
                )
        return results, findings

    def _exact_duplicates(self, dataset):
        grouped: dict[str, list[ReviewRecord]] = {}
        for row in sorted(dataset.ged_transactions, key=lambda item: item.row_number):
            fingerprint = _transaction_fingerprint(row)
            grouped.setdefault(fingerprint, []).append(row)
        results: list[RuleScopeResult] = []
        findings: list[Finding] = []
        for fingerprint, rows in sorted(
            grouped.items(), key=lambda item: item[1][0].row_number
        ):
            reference = rows[0]
            department = _department(reference.value("department_number")) or ""
            account = _account(reference.value("account_number")) or ""
            records = tuple(row.record_id for row in rows)
            if len(rows) == 1:
                results.append(
                    RuleScopeResult(
                        "CORE-03", fingerprint, ResultStatus.PASS,
                        department, account, records,
                        expected="A unique all-material-field fingerprint.",
                        actual="One transaction.",
                        explanation="No exact duplicate was found.",
                    )
                )
                continue
            exposure_value = _money(rows[1].value("amount"))
            exposure = _currency(exposure_value) if exposure_value is not None else "Unavailable"
            result = RuleScopeResult(
                "CORE-03", fingerprint, ResultStatus.FAIL,
                department, account, records,
                expected="One transaction per all-material-field fingerprint.",
                actual=f"{len(rows)} identical transactions; duplicate-copy exposure {exposure}.",
                explanation=(
                    f"GED row {rows[1].row_number} duplicates GED row "
                    f"{rows[0].row_number} across all 15 approved GED fields."
                ),
                evidence=tuple(
                    f"{row.worksheet}!A{row.row_number}:O{row.row_number}" for row in rows
                ),
            )
            results.append(result)
            findings.append(
                _finding(
                    dataset, result, "Medium", exposure,
                    "Confirm whether the later copy is valid; correct or document the duplicate."
                )
            )
        return results, findings

    def _required_fields(self, dataset):
        validators = {
            "department_number": _department,
            "account_number": _account,
            "fiscal_period": _fiscal_period,
            "journal_number": lambda value: bool(_text(value)),
            "journal_date": _journal_date,
            "amount": lambda value: _money(value) is not None,
        }
        results: list[RuleScopeResult] = []
        findings: list[Finding] = []
        for row in sorted(dataset.ged_transactions, key=lambda item: item.row_number):
            invalid = [
                field_name
                for field_name, validator in validators.items()
                if not validator(row.value(field_name))
            ]
            department = _department(row.value("department_number")) or ""
            account = _account(row.value("account_number")) or ""
            evidence = tuple(
                item
                for field_name in invalid
                for item in _evidence_for(row, field_name)
            )
            if invalid:
                result = RuleScopeResult(
                    "CORE-04", row.record_id, ResultStatus.FAIL,
                    department, account, (row.record_id,),
                    expected="Department, Account, Fiscal Period, Journal #, Journal Date, and Amount must parse.",
                    actual="Missing or invalid: " + ", ".join(_display_field(item) for item in invalid) + ".",
                    explanation="One or more required GED fields cannot be used reliably.",
                    evidence=evidence,
                )
                results.append(result)
                original = "; ".join(
                    f"{_display_field(item)}={row.value(item)!r}" for item in invalid
                )
                findings.append(
                    _finding(
                        dataset, result, "High", original,
                        "Enter a valid reviewed value, preserve the original evidence, and rerun validation."
                    )
                )
            else:
                results.append(
                    RuleScopeResult(
                        "CORE-04", row.record_id, ResultStatus.PASS,
                        department, account, (row.record_id,),
                        expected="All six required fields parse.",
                        actual="All required fields are present and parseable.",
                        explanation="The transaction satisfies required-data controls.",
                    )
                )
        budget_validators = {
            "account_number": _account,
            "bgt": lambda value: _money(value) is not None,
            "atd": lambda value: _money(value) is not None,
            "etc": lambda value: _money(value) is not None,
            "eac": lambda value: _money(value) is not None,
            "delta": lambda value: _money(value) is not None,
        }
        for row in sorted(dataset.budget_details, key=lambda item: item.row_number):
            invalid = [
                field_name
                for field_name, validator in budget_validators.items()
                if not validator(row.value(field_name))
            ]
            account = _account(row.value("account_number")) or ""
            scope = row.record_id
            evidence_fields = list(invalid)
            calculation_errors: list[str] = []
            if not invalid:
                bgt = _money(row.value("bgt"))
                atd = _money(row.value("atd"))
                etc = _money(row.value("etc"))
                eac = _money(row.value("eac"))
                delta = _money(row.value("delta"))
                assert None not in (bgt, atd, etc, eac, delta)
                expected_eac = atd + etc
                expected_delta = bgt - eac
                if eac != expected_eac:
                    calculation_errors.append(
                        f"EAC {_currency(eac)} does not equal ATD + ETC "
                        f"{_currency(expected_eac)}"
                    )
                    evidence_fields.extend(("atd", "etc", "eac"))
                if delta != expected_delta:
                    calculation_errors.append(
                        f"DELTA {_currency(delta)} does not equal BGT - EAC "
                        f"{_currency(expected_delta)}"
                    )
                    evidence_fields.extend(("bgt", "eac", "delta"))
            evidence = tuple(
                item
                for field_name in dict.fromkeys(evidence_fields)
                for item in _evidence_for(row, field_name)
            )
            if invalid or calculation_errors:
                actual_parts = []
                if invalid:
                    actual_parts.append(
                        "Missing or invalid: "
                        + ", ".join(_display_field(item) for item in invalid)
                    )
                actual_parts.extend(calculation_errors)
                result = RuleScopeResult(
                    "CORE-04",
                    scope,
                    ResultStatus.FAIL,
                    dataset.department_number,
                    account,
                    (row.record_id,),
                    expected=(
                        "Budget Account, BGT, ATD, ETC, EAC, and DELTA must parse; "
                        "EAC must equal ATD + ETC and DELTA must equal BGT - EAC."
                    ),
                    actual="; ".join(actual_parts) + ".",
                    explanation=(
                        "The Budget detail row is incomplete or its approved "
                        "EAC/DELTA calculations are inconsistent."
                    ),
                    evidence=evidence,
                )
                results.append(result)
                findings.append(
                    _finding(
                        dataset,
                        result,
                        "High",
                        "; ".join(
                            f"{_display_field(field)}={row.value(field)!r}"
                            for field in budget_validators
                        ),
                        (
                            "Correct the reviewed Budget values, preserve the original "
                            "evidence, and rerun validation."
                        ),
                    )
                )
            else:
                results.append(
                    RuleScopeResult(
                        "CORE-04",
                        scope,
                        ResultStatus.PASS,
                        dataset.department_number,
                        account,
                        (row.record_id,),
                        expected=(
                            "Complete Budget financial values with internally "
                            "consistent EAC and DELTA."
                        ),
                        actual="All required values and calculations are valid.",
                        explanation=(
                            "The Budget detail row satisfies required-data and "
                            "calculation controls."
                        ),
                    )
                )
        return results, findings

    def _ged_amount_threshold(
        self,
        dataset: WorkingFinancialDataset,
        definition: RuleDefinitionVersion,
    ):
        parameters = definition.parameters or {}
        threshold = _money(parameters.get("threshold"))
        operator = str(parameters.get("operator", ""))
        if threshold is None:
            raise RuleManifestError("The optional-rule threshold is invalid.")
        comparisons = {
            "EQ": lambda actual: actual == threshold,
            "NE": lambda actual: actual != threshold,
            "LT": lambda actual: actual < threshold,
            "LTE": lambda actual: actual <= threshold,
            "GT": lambda actual: actual > threshold,
            "GTE": lambda actual: actual >= threshold,
        }
        compare = comparisons.get(operator)
        if compare is None:
            raise RuleManifestError("The optional-rule operator is not allowlisted.")
        symbols = {
            "EQ": "=",
            "NE": "≠",
            "LT": "<",
            "LTE": "≤",
            "GT": ">",
            "GTE": "≥",
        }
        results: list[RuleScopeResult] = []
        findings: list[Finding] = []
        for row in sorted(dataset.ged_transactions, key=lambda item: item.row_number):
            amount = _money(row.value("amount"))
            department = _department(row.value("department_number")) or ""
            account = _account(row.value("account_number")) or ""
            expected = f"GED Amount {symbols[operator]} {_currency(threshold)}."
            if amount is None:
                results.append(
                    RuleScopeResult(
                        definition.rule_id,
                        row.record_id,
                        ResultStatus.NOT_EVALUATED,
                        department,
                        account,
                        (row.record_id,),
                        expected=expected,
                        actual="GED Amount is missing or invalid.",
                        explanation=(
                            "The optional threshold could not evaluate this transaction."
                        ),
                        evidence=_evidence_for(row, "amount"),
                    )
                )
                continue
            if compare(amount):
                results.append(
                    RuleScopeResult(
                        definition.rule_id,
                        row.record_id,
                        ResultStatus.PASS,
                        department,
                        account,
                        (row.record_id,),
                        expected=expected,
                        actual=_currency(amount),
                        explanation="The transaction satisfies the configured threshold.",
                    )
                )
                continue
            result = RuleScopeResult(
                definition.rule_id,
                row.record_id,
                ResultStatus.FAIL,
                department,
                account,
                (row.record_id,),
                expected=expected,
                actual=_currency(amount),
                explanation="The transaction does not satisfy the configured threshold.",
                evidence=_evidence_for(row, "amount"),
            )
            results.append(result)
            findings.append(
                _finding_for_rule(
                    dataset,
                    result,
                    definition,
                    str(row.value("amount")),
                    "Review the cited transaction and the configured threshold.",
                )
            )
        return results, findings

    def _atd_reconciliation(self, dataset, canonical):
        results: list[RuleScopeResult] = []
        findings: list[Finding] = []
        for financial in canonical.budget_accounts:
            budget = financial.budget_record
            assert budget is not None
            department = financial.department_number
            account = financial.account_number
            transactions = financial.ged_records
            atd = financial.atd
            source_records = (budget.record_id,) + tuple(
                row.record_id for row in transactions
            )
            scope = financial.scope_id
            if atd is None or not financial.aggregation_complete:
                results.append(
                    RuleScopeResult(
                        "CORE-05", scope, ResultStatus.NOT_EVALUATED,
                        department, account, source_records,
                        expected="Complete Budget ATD and exact-key GED Amounts.",
                        actual="Required reconciliation input is missing or invalid.",
                        explanation="FinSight does not substitute zero or a partial sum.",
                        evidence=_evidence_for(budget, "atd")
                        + tuple(
                            evidence
                            for row in transactions
                            for evidence in _evidence_for(row, "amount")
                        ),
                    )
                )
                continue
            actual = financial.summed_ged_amount
            assert actual is not None
            if actual != atd:
                difference = atd - actual
                result = RuleScopeResult(
                    "CORE-05", scope, ResultStatus.FAIL,
                    department, account, source_records,
                    expected=f"Budget ATD {_currency(atd)}.",
                    actual=f"Exact-key GED sum {_currency(actual)}; difference {_currency(difference)}.",
                    explanation="Budget ATD does not equal summed GED Amount for the exact department/account.",
                    evidence=_evidence_for(budget, "atd")
                    + tuple(
                        evidence
                        for row in transactions
                        for evidence in _evidence_for(row, "amount")
                    ),
                )
                results.append(result)
                findings.append(
                    _finding(
                        dataset, result, "High", str(budget.value("atd")),
                        "Review exact-key transactions and the Budget ATD, then correct or explain the difference."
                    )
                )
            else:
                results.append(
                    RuleScopeResult(
                        "CORE-05", scope, ResultStatus.PASS,
                        department, account, source_records,
                        expected=_currency(atd),
                        actual=_currency(actual),
                        explanation="Budget ATD reconciles exactly to GED Amount.",
                    )
                )
        return results, findings


def _budget_totals(records: Sequence[ReviewRecord]) -> dict[str, Any]:
    totals: dict[str, Any] = {}
    for field_name in ("bgt", "atd", "etc", "eac", "delta"):
        values = [_money(record.value(field_name)) for record in records]
        total = sum(
            (value for value in values if value is not None),
            Decimal("0"),
        )
        totals[field_name] = _currency(total)
        totals[field_name + "_decimal"] = total
        totals[field_name + "_is_complete"] = all(
            value is not None for value in values
        )
    return totals


def _analytics_projection(
    dataset: WorkingFinancialDataset,
    executions: Sequence[RuleExecution],
    findings: Sequence[Finding],
    account_comparisons: Sequence[Mapping[str, str]],
    budget_totals: Mapping[str, Any],
    ged_totals: Mapping[str, Any],
    canonical: CanonicalFinancialDataset,
    canonical_accounts: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """Return chart-ready, sealed values so delivery performs no financial math."""

    budget_by_account: list[dict[str, Any]] = []
    comparison_by_account: list[dict[str, Any]] = []
    for financial in canonical.budget_accounts:
        department = financial.department_number
        account = financial.account_number
        account_name = financial.account_name
        bgt = financial.bgt
        atd = financial.atd
        etc = financial.etc
        eac = financial.eac
        delta = financial.delta
        ged = financial.summed_ged_amount
        ged_complete = financial.aggregation_complete
        remaining = financial.remaining_budget
        overrun = financial.over_budget_amount
        reconciliation_difference = financial.budget_to_ged_difference
        actual_variance = (
            ged - bgt
            if ged_complete and ged is not None and bgt is not None
            else None
        )
        actual_variance_percentage = (
            (actual_variance / bgt) * Decimal("100")
            if actual_variance is not None and bgt not in (None, Decimal("0"))
            else None
        )
        budget_by_account.append(
            {
                "scope_key": financial.scope_id,
                "department_number": department,
                "account_number": account,
                "account_name": account_name,
                "bgt_cents": _cents(bgt),
                "bgt_label": _currency_or_unavailable(bgt),
                "atd_cents": _cents(atd),
                "atd_label": _currency_or_unavailable(atd),
                "etc_cents": _cents(etc),
                "etc_label": _currency_or_unavailable(etc),
                "eac_cents": _cents(eac),
                "eac_label": _currency_or_unavailable(eac),
                "delta_cents": _cents(delta),
                "delta_label": _currency_or_unavailable(delta),
                "remaining_cents": _cents(remaining),
                "remaining_label": _currency_or_unavailable(remaining),
                "overrun_cents": _cents(overrun),
                "overrun_label": _currency_or_unavailable(overrun),
                "utilization_hundredths": (
                    int(
                        (
                            financial.budget_utilization_percentage
                            * Decimal("100")
                        ).quantize(Decimal("1"))
                    )
                    if financial.budget_utilization_percentage is not None
                    else None
                ),
                "utilization_label": (
                    f"{financial.budget_utilization_percentage:.2f}%"
                    if financial.budget_utilization_percentage is not None
                    else "Not available"
                ),
                "budget_source_record": (
                    financial.budget_record.record_id
                    if financial.budget_record
                    else None
                ),
                "budget_source_row": (
                    financial.budget_record.row_number
                    if financial.budget_record
                    else None
                ),
                "contributing_ged_records": [
                    item.record_id for item in financial.ged_records
                ],
                "contributing_ged_rows": [
                    item.row_number for item in financial.ged_records
                ],
                "complete": ged_complete
                and all(
                    value is not None
                    for value in (bgt, atd, etc, eac, delta)
                ),
            }
        )
        comparison_by_account.append(
            {
                "scope_key": financial.scope_id,
                "department_number": department,
                "account_number": account,
                "account_name": account_name,
                "bgt_cents": _cents(bgt),
                "bgt_label": _currency_or_unavailable(bgt),
                "atd_cents": _cents(atd),
                "atd_label": _currency_or_unavailable(atd),
                "ged_cents": _cents(ged) if ged is not None else None,
                "ged_label": (
                    _currency(ged)
                    if ged is not None
                    else (
                        f"Not evaluated — parseable subtotal "
                        f"{_currency(financial.parseable_ged_amount)}"
                    )
                ),
                "actual_variance_cents": _cents(actual_variance),
                "actual_variance_label": (
                    _currency(actual_variance)
                    if actual_variance is not None
                    else "Unavailable"
                ),
                "actual_variance_percentage_hundredths": (
                    int(
                        (
                            actual_variance_percentage * Decimal("100")
                        ).quantize(Decimal("1"))
                    )
                    if actual_variance_percentage is not None
                    else None
                ),
                "actual_variance_percentage_label": (
                    f"{actual_variance_percentage:+.2f}%"
                    if actual_variance_percentage is not None
                    else "Unavailable"
                ),
                "remaining_cents": _cents(remaining),
                "remaining_label": _currency_or_unavailable(remaining),
                "overrun_cents": _cents(overrun),
                "overrun_label": _currency_or_unavailable(overrun),
                "reconciliation_difference_cents": _cents(
                    reconciliation_difference
                ),
                "reconciliation_difference_label": _currency_or_unavailable(
                    reconciliation_difference
                ),
                "utilization_hundredths": (
                    int(
                        (
                            financial.budget_utilization_percentage
                            * Decimal("100")
                        ).quantize(Decimal("1"))
                    )
                    if financial.budget_utilization_percentage is not None
                    else None
                ),
                "utilization_label": (
                    f"{financial.budget_utilization_percentage:.2f}%"
                    if financial.budget_utilization_percentage is not None
                    else "Not available"
                ),
                "transaction_count": len(financial.ged_records),
                "budget_source_record": (
                    financial.budget_record.record_id
                    if financial.budget_record
                    else None
                ),
                "budget_source_row": (
                    financial.budget_record.row_number
                    if financial.budget_record
                    else None
                ),
                "contributing_ged_records": [
                    item.record_id for item in financial.ged_records
                ],
                "contributing_ged_rows": [
                    item.row_number for item in financial.ged_records
                ],
                "complete": ged_complete
                and all(value is not None for value in (bgt, atd)),
            }
        )

    ged_account_groups: dict[tuple[str, str], list[ReviewRecord]] = {}
    ged_period_groups: dict[str, list[ReviewRecord]] = {}
    canonical_transactions = tuple(
        row
        for row in canonical.ged_records
        if row.row_kind == RowKind.GED_TRANSACTION.value
    )
    for row in canonical_transactions:
        key = (
            _department(row.value("department_number")) or _text(
                row.value("department_number")
            ),
            _account(row.value("account_number")) or _text(
                row.value("account_number")
            ),
        )
        ged_account_groups.setdefault(key, []).append(row)
        period = _text(row.value("fiscal_period")) or "Missing"
        ged_period_groups.setdefault(period, []).append(row)

    def spend_projection(label_fields, rows):
        amounts = [_money(row.value("amount")) for row in rows]
        complete = all(value is not None for value in amounts)
        total = sum(
            (value for value in amounts if value is not None), Decimal("0")
        )
        return {
            **label_fields,
            "amount_cents": _cents(total),
            "amount_label": (
                _currency(total) if complete else f"Partial — {_currency(total)}"
            ),
            "transaction_count": len(rows),
            "complete": complete,
            "missing_amount_count": sum(value is None for value in amounts),
        }

    ged_by_account = [
        spend_projection(
            {
                "scope_key": f"{key[0]}|{key[1]}",
                "department_number": key[0],
                "account_number": key[1],
                "account_name": _text(rows[0].value("account_name")),
            },
            rows,
        )
        for key, rows in sorted(ged_account_groups.items())
    ]
    ged_by_period = [
        spend_projection({"fiscal_period": period}, rows)
        for period, rows in sorted(ged_period_groups.items())
    ]
    ged_vendor_groups: dict[str, list[ReviewRecord]] = {}
    for row in canonical_transactions:
        vendor = _text(row.value("vendor_name")) or "No vendor recorded"
        ged_vendor_groups.setdefault(vendor, []).append(row)
    ged_by_vendor = sorted(
        (
            spend_projection({"vendor_name": vendor}, rows)
            for vendor, rows in ged_vendor_groups.items()
        ),
        key=lambda item: (
            -(item["amount_cents"] or 0),
            item["vendor_name"],
        ),
    )
    largest_transactions = []
    for row in sorted(
        canonical_transactions,
        key=lambda item: (
            -abs(_money(item.value("amount")) or Decimal("0")),
            item.row_number,
        ),
    )[:20]:
        amount = _money(row.value("amount"))
        largest_transactions.append(
            {
                "record_id": row.record_id,
                "source_row": row.row_number,
                "department_number": _text(row.value("department_number")),
                "account_number": _text(row.value("account_number")),
                "account_name": _text(row.value("account_name")),
                "fiscal_period": _text(row.value("fiscal_period")),
                "journal_number": _text(row.value("journal_number")),
                "journal_date": _json_value(row.value("journal_date")),
                "vendor_name": _text(row.value("vendor_name"))
                or "No vendor recorded",
                "description": _text(
                    row.value("journal_line_description")
                )
                or _text(row.value("journal_description")),
                "amount_cents": _cents(amount),
                "amount_label": _currency_or_unavailable(amount),
                "polarity": (
                    "Positive"
                    if amount is not None and amount > 0
                    else (
                        "Negative"
                        if amount is not None and amount < 0
                        else ("Zero" if amount is not None else "Missing")
                    )
                ),
            }
        )
    signed_groups = {
        "Positive": [
            row
            for row in canonical_transactions
            if (_money(row.value("amount")) or Decimal("0")) > 0
        ],
        "Negative": [
            row
            for row in canonical_transactions
            if (_money(row.value("amount")) or Decimal("0")) < 0
        ],
        "Zero": [
            row
            for row in canonical_transactions
            if _money(row.value("amount")) == Decimal("0")
        ],
        "Missing / invalid": [
            row
            for row in canonical_transactions
            if _money(row.value("amount")) is None
        ],
    }
    ged_by_polarity = [
        {
            **spend_projection({"polarity": polarity}, rows),
            "contributing_ged_records": [
                row.record_id for row in rows
            ],
            "contributing_ged_rows": [
                row.row_number for row in rows
            ],
        }
        for polarity, rows in signed_groups.items()
    ]

    bgt_total = budget_totals["bgt_decimal"]
    ged_total = ged_totals["ged_decimal"]
    total_actual_variance = (
        ged_total - bgt_total
        if (
            budget_totals["bgt_is_complete"]
            and ged_totals["ged_is_complete"]
        )
        else None
    )
    total_actual_variance_percentage = (
        (total_actual_variance / bgt_total) * Decimal("100")
        if total_actual_variance is not None and bgt_total
        else None
    )
    utilization_hundredths = (
        int(
            (
                (ged_total / bgt_total) * Decimal("10000")
            ).quantize(Decimal("1"))
        )
        if bgt_total
        else None
    )
    account_status_counts = {
        "over_budget": sum(
            item["over_budget_status"] == ResultStatus.FAIL.value
            for item in account_comparisons
        ),
        "within_budget": sum(
            item["over_budget_status"] == ResultStatus.PASS.value
            for item in account_comparisons
        ),
        "not_evaluated": sum(
            item["over_budget_status"] == ResultStatus.NOT_EVALUATED.value
            for item in account_comparisons
        ),
    }
    reconciliation_status_counts = {
        "reconciled": sum(
            item["reconciliation_status"] == ResultStatus.PASS.value
            for item in account_comparisons
        ),
        "different": sum(
            item["reconciliation_status"] == ResultStatus.FAIL.value
            for item in account_comparisons
        ),
        "not_evaluated": sum(
            item["reconciliation_status"] == ResultStatus.NOT_EVALUATED.value
            for item in account_comparisons
        ),
    }
    return {
        "financial_summary": {
            "bgt_cents": _cents(bgt_total),
            "bgt_label": _currency(bgt_total),
            "atd_cents": _cents(budget_totals["atd_decimal"]),
            "atd_label": _currency(budget_totals["atd_decimal"]),
            "etc_cents": _cents(budget_totals["etc_decimal"]),
            "etc_label": _currency(budget_totals["etc_decimal"]),
            "eac_cents": _cents(budget_totals["eac_decimal"]),
            "eac_label": _currency(budget_totals["eac_decimal"]),
            "delta_cents": _cents(budget_totals["delta_decimal"]),
            "delta_label": _currency(budget_totals["delta_decimal"]),
            "ged_cents": _cents(ged_total),
            "ged_label": (
                _currency(ged_total)
                if ged_totals["ged_is_complete"]
                else f"Partial — {_currency(ged_total)}"
            ),
            "actual_variance_cents": _cents(total_actual_variance),
            "actual_variance_label": (
                _currency(total_actual_variance)
                if total_actual_variance is not None
                else "Unavailable"
            ),
            "actual_variance_percentage_hundredths": (
                int(
                    (
                        total_actual_variance_percentage * Decimal("100")
                    ).quantize(Decimal("1"))
                )
                if total_actual_variance_percentage is not None
                else None
            ),
            "actual_variance_percentage_label": (
                f"{total_actual_variance_percentage:+.2f}%"
                if total_actual_variance_percentage is not None
                else "Unavailable"
            ),
            "complete": bool(
                budget_totals["bgt_is_complete"]
                and budget_totals["atd_is_complete"]
                and ged_totals["ged_is_complete"]
            ),
            "account_count": len(canonical.budget_accounts),
            "ged_transaction_count": len(canonical_transactions),
        },
        "findings_by_severity": [
            {
                "severity": severity,
                "count": sum(item.severity == severity for item in findings),
            }
            for severity in ("Critical", "High", "Medium", "Low")
        ],
        "rule_outcomes": [
            {
                "rule_id": item.rule_id,
                "rule_name": item.rule_name,
                "purpose": item.purpose,
                "status": item.status.value,
                "passed": item.pass_count,
                "failed": item.fail_count,
                "not_evaluated": item.not_evaluated_count,
            }
            for item in executions
        ],
        "budget_utilization": {
            "bgt_cents": _cents(bgt_total),
            "ged_cents": _cents(ged_total),
            "percent_hundredths": utilization_hundredths,
            "percent_label": (
                f"{Decimal(utilization_hundredths) / Decimal('100'):.2f}%"
                if utilization_hundredths is not None
                else "Not available"
            ),
            "complete": bool(
                budget_totals["bgt_is_complete"]
                and ged_totals["ged_is_complete"]
            ),
        },
        "account_status_counts": account_status_counts,
        "reconciliation_status_counts": reconciliation_status_counts,
        "budget_by_account": budget_by_account,
        "ged_by_account": ged_by_account,
        "ged_by_period": ged_by_period,
        "ged_by_vendor": ged_by_vendor,
        "largest_transactions": largest_transactions,
        "ged_by_polarity": ged_by_polarity,
        "comparison_by_account": comparison_by_account,
        "account_hierarchy": list(canonical_accounts),
        "variance_ranked_accounts": sorted(
            comparison_by_account,
            key=lambda item: (
                item["remaining_cents"]
                if item["remaining_cents"] is not None
                else 10**30,
                item["account_number"],
            ),
        ),
    }


def _ged_totals(canonical: CanonicalFinancialDataset) -> dict[str, Any]:
    valid_budget_keys = {
        item.key for item in canonical.budget_accounts
    }
    all_values: list[Decimal | None] = []
    mapped_values: list[Decimal] = []
    unmapped_values: list[Decimal] = []
    transaction_records = tuple(
        record
        for record in canonical.ged_records
        if record.row_kind == RowKind.GED_TRANSACTION.value
    )
    for record in transaction_records:
        amount = _money(record.value("amount"))
        all_values.append(amount)
        if amount is None:
            continue
        key = (
            _department(record.value("department_number")),
            _account(record.value("account_number")),
        )
        if key in valid_budget_keys:
            mapped_values.append(amount)
        else:
            unmapped_values.append(amount)
    ged_total = sum(
        (value for value in all_values if value is not None),
        Decimal("0"),
    )
    mapped_total = sum(mapped_values, Decimal("0"))
    unmapped_total = sum(unmapped_values, Decimal("0"))
    return {
        "ged": _currency(ged_total),
        "ged_decimal": ged_total,
        "mapped_ged": _currency(mapped_total),
        "mapped_ged_decimal": mapped_total,
        "unmapped_ged": _currency(unmapped_total),
        "unmapped_ged_decimal": unmapped_total,
        "ged_is_complete": all(value is not None for value in all_values),
        "eligible_transaction_count": len(transaction_records),
        "parseable_amount_count": sum(value is not None for value in all_values),
        "missing_or_unparseable_amount_count": sum(
            value is None for value in all_values
        ),
    }


def _account_comparisons(
    canonical: CanonicalFinancialDataset,
    scope_results: Sequence[RuleScopeResult],
    findings: Sequence[Finding],
) -> list[dict[str, Any]]:
    by_rule_scope = {
        (item.rule_id, item.scope_id): item for item in scope_results
    }
    output: list[dict[str, Any]] = []
    for financial in canonical.budget_accounts:
        department = financial.department_number
        account = financial.account_number
        scope_id = financial.scope_id
        overrun = by_rule_scope[("CORE-01", scope_id)]
        reconciliation = by_rule_scope[("CORE-05", scope_id)]
        complete = financial.aggregation_complete
        ged_amount = _currency_or_unavailable(financial.summed_ged_amount)
        if not complete:
            ged_amount = "Not evaluated"
        variance = _currency_or_unavailable(
            financial.budget_to_ged_difference
        )
        if financial.budget_to_ged_difference is None:
            variance = "Not evaluated"
        account_findings = [
            item
            for item in findings
            if item.department_number == department
            and item.account_number == account
        ]
        output.append(
            {
                "department_number": department,
                "account_number": account,
                "account_name": financial.account_name,
                "bgt": (
                    _currency(financial.bgt)
                    if financial.bgt is not None
                    else "Not evaluated"
                ),
                "budget_atd": (
                    _currency(financial.atd)
                    if financial.atd is not None
                    else "Not evaluated"
                ),
                "budget_etc": _currency_or_unavailable(financial.etc),
                "budget_eac": _currency_or_unavailable(financial.eac),
                "budget_delta": _currency_or_unavailable(financial.delta),
                "ged_amount": ged_amount,
                "ged_transaction_count": len(financial.ged_records),
                "variance_atd_to_ged": variance,
                "remaining_budget": _currency_or_unavailable(
                    financial.remaining_budget
                ),
                "over_budget_amount": _currency_or_unavailable(
                    financial.over_budget_amount
                ),
                "utilization_percentage": (
                    f"{financial.budget_utilization_percentage:.2f}%"
                    if financial.budget_utilization_percentage is not None
                    else "Not evaluated"
                ),
                "reconciliation_status": reconciliation.status.value,
                "over_budget_status": overrun.status.value,
                "finding_count": len(account_findings),
                "finding_badges": [
                    f"{item.rule_id} · {item.severity}"
                    for item in account_findings
                ],
                "budget_source_row": (
                    financial.budget_record.row_number
                    if financial.budget_record
                    else None
                ),
                "contributing_ged_rows": [
                    item.row_number for item in financial.ged_records
                ],
            }
        )
    return output


def _canonical_account_projection(
    canonical: CanonicalFinancialDataset,
    scope_results: Sequence[RuleScopeResult],
    findings: Sequence[Finding],
) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for financial in canonical.accounts:
        relevant_results = [
            item
            for item in scope_results
            if item.department_number == financial.department_number
            and item.account_number == financial.account_number
        ]
        outcomes: list[dict[str, Any]] = []
        for rule_id in dict.fromkeys(item.rule_id for item in relevant_results):
            statuses = [
                item.status
                for item in relevant_results
                if item.rule_id == rule_id
            ]
            status = (
                ResultStatus.NOT_EVALUATED
                if ResultStatus.NOT_EVALUATED in statuses
                else (
                    ResultStatus.FAIL
                    if ResultStatus.FAIL in statuses
                    else ResultStatus.PASS
                )
            )
            outcomes.append(
                {
                    "rule_id": rule_id,
                    "status": status.value,
                    "scope_count": len(statuses),
                    "failed_scope_count": sum(
                        item is ResultStatus.FAIL for item in statuses
                    ),
                    "not_evaluated_scope_count": sum(
                        item is ResultStatus.NOT_EVALUATED for item in statuses
                    ),
                }
            )
        account_findings = [
            item
            for item in findings
            if item.department_number == financial.department_number
            and item.account_number == financial.account_number
        ]
        reconciliation = next(
            (
                item["status"]
                for item in outcomes
                if item["rule_id"] == "CORE-05"
            ),
            "NOT_APPLICABLE",
        )
        output.append(
            {
                "scope_key": financial.scope_id,
                "department_number": financial.department_number,
                "department_name": financial.department_name,
                "account_number": financial.account_number,
                "account_name": financial.account_name,
                "budget_mapping": (
                    "MAPPED" if financial.has_budget_mapping else "UNMAPPED"
                ),
                "bgt_cents": _cents(financial.bgt),
                "bgt_label": _currency_or_unavailable(financial.bgt),
                "atd_cents": _cents(financial.atd),
                "atd_label": _currency_or_unavailable(financial.atd),
                "etc_cents": _cents(financial.etc),
                "etc_label": _currency_or_unavailable(financial.etc),
                "eac_cents": _cents(financial.eac),
                "eac_label": _currency_or_unavailable(financial.eac),
                "delta_cents": _cents(financial.delta),
                "delta_label": _currency_or_unavailable(financial.delta),
                "summed_ged_amount_cents": _cents(
                    financial.summed_ged_amount
                ),
                "summed_ged_amount_label": (
                    _currency(financial.summed_ged_amount)
                    if financial.summed_ged_amount is not None
                    else "Not evaluated"
                ),
                "parseable_ged_subtotal_cents": _cents(
                    financial.parseable_ged_amount
                ),
                "parseable_ged_subtotal_label": _currency(
                    financial.parseable_ged_amount
                ),
                "ged_transaction_count": len(financial.ged_records),
                "missing_amount_count": financial.missing_amount_count,
                "invalid_fiscal_period_count": (
                    financial.invalid_fiscal_period_count
                ),
                "budget_to_ged_difference_cents": _cents(
                    financial.budget_to_ged_difference
                ),
                "budget_to_ged_difference_label": _currency_or_unavailable(
                    financial.budget_to_ged_difference
                ),
                "budget_utilization_hundredths": (
                    int(
                        (
                            financial.budget_utilization_percentage
                            * Decimal("100")
                        ).quantize(Decimal("1"))
                    )
                    if financial.budget_utilization_percentage is not None
                    else None
                ),
                "budget_utilization_label": (
                    f"{financial.budget_utilization_percentage:.2f}%"
                    if financial.budget_utilization_percentage is not None
                    else "Not evaluated"
                ),
                "remaining_budget_cents": _cents(
                    financial.remaining_budget
                ),
                "remaining_budget_label": _currency_or_unavailable(
                    financial.remaining_budget
                ),
                "over_budget_amount_cents": _cents(
                    financial.over_budget_amount
                ),
                "over_budget_amount_label": _currency_or_unavailable(
                    financial.over_budget_amount
                ),
                "reconciliation_status": reconciliation,
                "rule_outcomes": outcomes,
                "finding_count": len(account_findings),
                "finding_ids": [item.finding_id for item in account_findings],
                "finding_badges": [
                    f"{item.rule_id} · {item.severity}"
                    for item in account_findings
                ],
                "budget_source_record": (
                    financial.budget_record.record_id
                    if financial.budget_record
                    else None
                ),
                "budget_source_row": (
                    financial.budget_record.row_number
                    if financial.budget_record
                    else None
                ),
                "contributing_ged_records": [
                    item.record_id for item in financial.ged_records
                ],
                "contributing_ged_rows": [
                    item.row_number for item in financial.ged_records
                ],
                "vendors": sorted(
                    {
                        _text(item.value("vendor_name"))
                        for item in financial.ged_records
                        if _text(item.value("vendor_name"))
                    }
                ),
                "fiscal_periods": sorted(
                    {
                        _text(item.value("fiscal_period"))
                        for item in financial.ged_records
                        if _text(item.value("fiscal_period"))
                    }
                ),
                "descriptions": list(
                    dict.fromkeys(
                        _text(item.value("journal_line_description"))
                        or _text(item.value("journal_description"))
                        for item in financial.ged_records
                        if _text(item.value("journal_line_description"))
                        or _text(item.value("journal_description"))
                    )
                ),
                "provenance": {
                    "budget_value_origin": (
                        "Edited"
                        if financial.budget_edited_fields
                        else ("Original" if financial.budget_record else "Unavailable")
                    ),
                    "budget_edited_fields": list(
                        financial.budget_edited_fields
                    ),
                    "edited_ged_records": list(
                        financial.edited_ged_records
                    ),
                    "edited_ged_field_count": (
                        financial.edited_ged_field_count
                    ),
                },
            }
        )
    return output


def _financial_control_report(
    canonical: CanonicalFinancialDataset,
    budget_totals: Mapping[str, Any],
    ged_totals: Mapping[str, Any],
) -> dict[str, Any]:
    budget_details = tuple(
        item
        for item in canonical.budget_records
        if item.row_kind == RowKind.BUDGET_DETAIL.value
    )
    ged_transactions = tuple(
        item
        for item in canonical.ged_records
        if item.row_kind == RowKind.GED_TRANSACTION.value
    )

    def row_groups(
        records: Sequence[ReviewRecord], included_kind: str
    ) -> dict[str, Any]:
        groups: dict[str, list[int]] = {}
        for record in records:
            groups.setdefault(record.row_kind, []).append(record.row_number)
        return {
            "source_rows_read": len(records),
            "included_rows": [
                record.row_number
                for record in records
                if record.row_kind == included_kind
            ],
            "included_row_count": sum(
                record.row_kind == included_kind for record in records
            ),
            "excluded_row_count": sum(
                record.row_kind != included_kind for record in records
            ),
            "row_types": [
                {
                    "row_type": row_kind,
                    "count": len(rows),
                    "source_rows": rows,
                    "treatment": (
                        "Included"
                        if row_kind == included_kind
                        else "Excluded from financial aggregation"
                    ),
                }
                for row_kind, rows in sorted(groups.items())
            ],
        }

    budget_rows = row_groups(
        canonical.budget_records, RowKind.BUDGET_DETAIL.value
    )
    ged_rows = row_groups(
        canonical.ged_records, RowKind.GED_TRANSACTION.value
    )
    budget_controls = {}
    for field_name in ("bgt", "atd", "etc", "eac", "delta"):
        budget_controls[field_name] = {
            "formula": (
                f"SUM reviewed {field_name.upper()} across six-digit "
                "Budget detail rows only"
            ),
            "exact_decimal": format(
                budget_totals[field_name + "_decimal"], ".2f"
            ),
            "display": budget_totals[field_name],
            "complete": bool(
                budget_totals[field_name + "_is_complete"]
            ),
            "source_row_count": len(budget_details),
            "included_rows": [item.row_number for item in budget_details],
            "excluded_row_count": budget_rows["excluded_row_count"],
        }
    return {
        "schema_version": "FCR-1.0",
        "decimal_policy": (
            "Exact Decimal arithmetic, two fractional digits; no binary "
            "floating-point financial calculations."
        ),
        "budget": {
            "totals": budget_controls,
            **budget_rows,
        },
        "ged": {
            "total_eligible_amount": {
                "formula": (
                    "SUM parseable reviewed Amount values on GED transaction "
                    "rows; duplicate transactions remain included"
                ),
                "exact_decimal": format(
                    ged_totals["ged_decimal"], ".2f"
                ),
                "display": ged_totals["ged"],
                "complete": bool(ged_totals["ged_is_complete"]),
                "source_row_count": len(ged_transactions),
                "parseable_amount_count": ged_totals[
                    "parseable_amount_count"
                ],
                "missing_or_unparseable_amount_count": ged_totals[
                    "missing_or_unparseable_amount_count"
                ],
                "included_rows": [
                    item.row_number for item in ged_transactions
                ],
            },
            "mapped_amount": {
                "formula": (
                    "SUM parseable GED transaction Amount where the exact "
                    "Department Number + Account Number exists in Budget"
                ),
                "exact_decimal": format(
                    ged_totals["mapped_ged_decimal"], ".2f"
                ),
                "display": ged_totals["mapped_ged"],
            },
            "unmapped_amount": {
                "formula": (
                    "SUM parseable GED transaction Amount where the exact "
                    "Department Number + Account Number is absent from Budget"
                ),
                "exact_decimal": format(
                    ged_totals["unmapped_ged_decimal"], ".2f"
                ),
                "display": ged_totals["unmapped_ged"],
            },
            "excluded_transaction_amount": {
                "formula": (
                    "No GED transaction rows are excluded by row type; subtotal, "
                    "department-total, separator, and blank rows are structural "
                    "controls and are never transaction amounts"
                ),
                "exact_decimal": "0.00",
                "display": "$0.00",
                "source_row_count": 0,
            },
            **ged_rows,
        },
    }


def _field_coverage_projection() -> list[dict[str, str]]:
    budget = (
        ("A", "account_number", "Exact account key and hierarchy"),
        ("B", "account_name", "Account/category label"),
        ("C", "bgt", "Budget Overrun and budget analysis"),
        ("D", "atd", "Budget-to-GED Reconciliation"),
        ("E", "etc", "Estimate-to-complete and EAC control"),
        ("F", "eac", "ATD + ETC calculation control"),
        ("G", "delta", "BGT - EAC calculation control"),
        ("H", "notes", "Source context and reviewed-data evidence"),
    )
    ged = (
        ("A", "department_number", "Exact mapping key and required data"),
        ("B", "department_name", "Department hierarchy and duplicate fingerprint"),
        ("C", "account_number", "Exact mapping key and required data"),
        ("D", "account_name", "Account/category and duplicate fingerprint"),
        ("E", "fiscal_period", "Period analysis and required data"),
        ("F", "journal_number", "Journal traceability and required data"),
        ("G", "journal_date", "Transaction date and required data"),
        ("H", "invoice_amount", "Invoice evidence and duplicate fingerprint"),
        ("I", "check_number", "Payment evidence and duplicate fingerprint"),
        ("J", "invoice_date", "Invoice evidence and duplicate fingerprint"),
        ("K", "vendor_name", "Vendor analysis and duplicate fingerprint"),
        ("L", "agency", "Agency evidence and duplicate fingerprint"),
        ("M", "journal_description", "Transaction explanation and duplicate fingerprint"),
        ("N", "journal_line_description", "Line explanation and duplicate fingerprint"),
        ("O", "amount", "All financial rules, totals, and analytics"),
    )
    rows = []
    for column, field_name, purpose in budget:
        rows.append(
            {
                "source": "Budget",
                "source_column": column,
                "source_field": field_name,
                "dataset": "Canonical account / source lineage",
                "used_for": purpose,
                "displayed_where": "Budget Data, account drill-down, Source Evidence",
                "validation_impact": (
                    "CORE-01 / CORE-04 / CORE-05"
                    if field_name in {"bgt", "atd", "etc", "eac", "delta"}
                    else (
                        "CORE-02 / CORE-04"
                        if field_name == "account_number"
                        else "No independent pass/fail decision"
                    )
                ),
                "exclusion_reason": "",
            }
        )
    for column, field_name, purpose in ged:
        impacts = ["CORE-03"]
        if field_name in {
            "department_number",
            "account_number",
        }:
            impacts.extend(("CORE-02", "CORE-04"))
        if field_name in {
            "fiscal_period",
            "journal_number",
            "journal_date",
            "amount",
        }:
            impacts.append("CORE-04")
        if field_name in {"fiscal_period", "amount"}:
            impacts.extend(("CORE-01", "CORE-05"))
        rows.append(
            {
                "source": "GED",
                "source_column": column,
                "source_field": field_name,
                "dataset": "Canonical GED transaction / source lineage",
                "used_for": purpose,
                "displayed_where": "GED Data, account drill-down, Source Evidence",
                "validation_impact": " / ".join(dict.fromkeys(impacts)),
                "exclusion_reason": "",
            }
        )
    return rows


def _required_value_states(record: ReviewRecord) -> tuple[int, int]:
    values = {
        "department_number": record.value("department_number"),
        "account_number": record.value("account_number"),
        "fiscal_period": record.value("fiscal_period"),
        "journal_number": record.value("journal_number"),
        "journal_date": record.value("journal_date"),
        "amount": record.value("amount"),
    }
    validators = {
        "department_number": _department,
        "account_number": _account,
        "fiscal_period": _fiscal_period,
        "journal_number": lambda value: bool(_text(value)),
        "journal_date": _journal_date,
        "amount": lambda value: _money(value) is not None,
    }
    missing = sum(not _text(value) for value in values.values())
    invalid = sum(
        bool(_text(value)) and not validators[field_name](value)
        for field_name, value in values.items()
    )
    return missing, invalid


def _missing_required_value_count(dataset: WorkingFinancialDataset) -> int:
    return sum(
        _required_value_states(record)[0]
        for record in dataset.ged_transactions
    )


def _invalid_required_value_count(dataset: WorkingFinancialDataset) -> int:
    return sum(
        _required_value_states(record)[1]
        for record in dataset.ged_transactions
    )


def _duplicate_copy_count(dataset: WorkingFinancialDataset) -> int:
    grouped: dict[str, int] = {}
    for record in dataset.ged_transactions:
        fingerprint = _transaction_fingerprint(record)
        grouped[fingerprint] = grouped.get(fingerprint, 0) + 1
    return sum(max(0, count - 1) for count in grouped.values())


def _finding(dataset, result, severity, original_or_edited, action):
    names = {item[0]: item[1] for item in CORE_RULE_VERSIONS}
    token = "|".join(
        (
            dataset.review_id,
            result.rule_id,
            result.scope_id,
            result.status.value,
        )
    )
    return Finding(
        "finding_" + hashlib.sha256(token.encode("utf-8")).hexdigest()[:24],
        result.rule_id,
        names[result.rule_id],
        severity,
        result.department_number,
        result.account_number,
        result.source_records,
        original_or_edited,
        result.expected,
        result.actual,
        result.explanation,
        action,
        result.evidence,
    )


def _result_with_structured_evidence(
    dataset: WorkingFinancialDataset, result: RuleScopeResult
) -> RuleScopeResult:
    return replace(
        result,
        evidence_details=_structured_evidence(
            dataset, result.source_records, result.evidence
        ),
    )


def _structured_evidence(
    dataset: WorkingFinancialDataset,
    source_records: Sequence[str],
    references: Sequence[str],
) -> tuple[Mapping[str, Any], ...]:
    if not references:
        return ()
    record_index = {
        record.record_id: record
        for record in (*dataset.budget_records, *dataset.ged_records)
    }
    details: list[Mapping[str, Any]] = []
    for record_id in source_records:
        record = record_index.get(record_id)
        if record is None:
            continue
        for field_name, cell in record.cells.items():
            if not any(
                _reference_contains_cell(reference, record.worksheet, cell)
                for reference in references
            ):
                continue
            original = record.original.get(field_name)
            current = record.current.get(field_name)
            details.append(
                {
                    "record_id": record.record_id,
                    "source_role": record.source_role,
                    "worksheet": record.worksheet,
                    "row": record.row_number,
                    "field": field_name,
                    "cell": cell,
                    "original_value": _json_value(original),
                    "current_value": _json_value(current),
                    "value_origin": (
                        "Edited" if current != original else "Original"
                    ),
                }
            )
    return tuple(
        sorted(
            details,
            key=lambda item: (
                str(item["source_role"]),
                int(item["row"]),
                _cell_column_number(str(item["cell"])),
                str(item["field"]),
            ),
        )
    )


def _reference_contains_cell(reference: str, worksheet: str, cell: str) -> bool:
    if "!" not in reference:
        return False
    reference_sheet, coordinates = reference.rsplit("!", 1)
    if reference_sheet != worksheet:
        return False
    if ":" not in coordinates:
        return coordinates == cell
    start, end = coordinates.split(":", 1)
    parsed_cell = _cell_parts(cell)
    parsed_start = _cell_parts(start)
    parsed_end = _cell_parts(end)
    if not parsed_cell or not parsed_start or not parsed_end:
        return False
    column, row = parsed_cell
    start_column, start_row = parsed_start
    end_column, end_row = parsed_end
    return (
        min(start_column, end_column) <= column <= max(start_column, end_column)
        and min(start_row, end_row) <= row <= max(start_row, end_row)
    )


def _cell_parts(cell: str) -> tuple[int, int] | None:
    match = re.fullmatch(r"([A-Z]+)([1-9][0-9]*)", cell.upper())
    if not match:
        return None
    return _cell_column_number(match.group(1)), int(match.group(2))


def _cell_column_number(cell_or_column: str) -> int:
    letters = "".join(
        character
        for character in cell_or_column.upper()
        if "A" <= character <= "Z"
    )
    value = 0
    for character in letters:
        value = value * 26 + (ord(character) - ord("A") + 1)
    return value


def _finding_for_rule(
    dataset: WorkingFinancialDataset,
    result: RuleScopeResult,
    definition: RuleDefinitionVersion,
    original_or_edited: str,
    action: str,
) -> Finding:
    token = "|".join(
        (
            dataset.review_id,
            result.rule_id,
            result.scope_id,
            result.status.value,
        )
    )
    return Finding(
        "finding_" + hashlib.sha256(token.encode("utf-8")).hexdigest()[:24],
        result.rule_id,
        definition.name,
        definition.severity,
        result.department_number,
        result.account_number,
        result.source_records,
        original_or_edited,
        result.expected,
        result.actual,
        result.explanation,
        action,
        result.evidence,
    )


def _core_purpose(rule_id: str) -> str:
    return {
        "CORE-01": (
            "Total GED actual spending must not exceed BGT for the same "
            "Department Number + Account Number."
        ),
        "CORE-02": (
            "Every GED Department Number + Account Number combination must "
            "exist in the Budget report."
        ),
        "CORE-03": (
            "Flag GED rows with the same approved all-material-field duplicate "
            "fingerprint."
        ),
        "CORE-04": (
            "Required values must be present and parseable, and approved Budget "
            "EAC/DELTA calculations must be internally consistent."
        ),
        "CORE-05": (
            "Summed GED Amount must equal Budget ATD for each Department Number "
            "+ Account Number."
        ),
    }[rule_id]


def _core_required_fields(rule_id: str) -> tuple[str, ...]:
    return {
        "CORE-01": ("budget.bgt", "ged.fiscal_period", "ged.amount"),
        "CORE-02": (
            "budget.account_number",
            "ged.department_number",
            "ged.account_number",
        ),
        "CORE-03": (
            "ged.department_number",
            "ged.department_name",
            "ged.account_number",
            "ged.account_name",
            "ged.fiscal_period",
            "ged.journal_number",
            "ged.journal_date",
            "ged.invoice_amount",
            "ged.check_number",
            "ged.invoice_date",
            "ged.vendor_name",
            "ged.agency",
            "ged.journal_description",
            "ged.journal_line_description",
            "ged.amount",
        ),
        "CORE-04": (
            "ged.department_number",
            "ged.account_number",
            "ged.fiscal_period",
            "ged.journal_number",
            "ged.journal_date",
            "ged.amount",
            "budget.account_number",
            "budget.bgt",
            "budget.atd",
            "budget.etc",
            "budget.eac",
            "budget.delta",
        ),
        "CORE-05": ("budget.atd", "ged.fiscal_period", "ged.amount"),
    }[rule_id]


def _core_grouping_keys(rule_id: str) -> tuple[str, ...]:
    if rule_id in {"CORE-01", "CORE-05"}:
        return ("department_number", "account_number")
    if rule_id == "CORE-03":
        return ("approved_ged_15_field_fingerprint",)
    return ("source_record",)


def _evidence_for(row: ReviewRecord, field_name: str) -> tuple[str, ...]:
    cell = row.cells.get(field_name)
    return (f"{row.worksheet}!{cell}",) if cell else ()


def _display_field(field_name: str) -> str:
    return {
        "department_number": "Department Number",
        "account_number": "Account Number",
        "fiscal_period": "Fiscal Period",
        "journal_number": "Journal Number",
        "journal_date": "Journal Date",
        "amount": "Amount",
        "bgt": "BGT",
        "atd": "ATD",
        "etc": "ETC",
        "eac": "EAC",
        "delta": "DELTA",
    }.get(field_name, field_name.replace("_", " ").title())


def _text(value: Any) -> str:
    return "" if value is None else str(value).strip()


def _department(value: Any) -> str | None:
    text = _text(value)
    return text if re.fullmatch(r"\d{2}-\d{4}", text) else None


def _account(value: Any) -> str | None:
    if isinstance(value, bool):
        return None
    text = _text(value)
    if text.endswith(".0") and text[:-2].isdigit():
        text = text[:-2]
    return text if re.fullmatch(r"\d{6}", text) else None


def _fiscal_period(value: Any) -> bool:
    text = _text(value)
    if not re.fullmatch(r"\d{4}-(0[1-9]|1[0-2])", text):
        return False
    try:
        datetime.strptime(text, "%Y-%m")
    except ValueError:
        return False
    return True


def _journal_date(value: Any) -> bool:
    if isinstance(value, (date, datetime)):
        return True
    text = _text(value)
    if not text:
        return False
    try:
        datetime.strptime(text[:10], "%Y-%m-%d")
    except ValueError:
        return False
    return len(text) == 10


def _money(value: Any) -> Decimal | None:
    if value is None or isinstance(value, bool):
        return None
    text = _text(value).replace(",", "").replace("$", "")
    if not text:
        return None
    if text.startswith("(") and text.endswith(")"):
        text = "-" + text[1:-1]
    if "e" in text.lower():
        return None
    try:
        result = Decimal(text)
    except (InvalidOperation, ValueError):
        return None
    if not result.is_finite() or result.as_tuple().exponent < -2:
        return None
    return result.quantize(Decimal("0.01"))


def _currency(value: Decimal) -> str:
    sign = "-" if value < 0 else ""
    return f"{sign}${abs(value):,.2f}"


def _cents(value: Decimal | None) -> int | None:
    if value is None:
        return None
    return int((value * Decimal("100")).to_integral_exact())


def _currency_or_unavailable(value: Decimal | None) -> str:
    return _currency(value) if value is not None else "Not available"


def _transaction_fingerprint(row: ReviewRecord) -> str:
    ordered_fields = (
        "department_number", "department_name", "account_number", "account_name",
        "fiscal_period", "journal_number", "journal_date", "invoice_amount",
        "check_number", "invoice_date", "vendor_name", "agency",
        "journal_description", "journal_line_description", "amount",
    )
    tokens = [
        _canonical_field(field_name, row.value(field_name))
        for field_name in ordered_fields
    ]
    payload = {"schema": "GED-15-V1", "tokens": tokens}
    return hashlib.sha256(_canonical_json(payload).encode("utf-8")).hexdigest()


def _canonical_field(field_name: str, value: Any) -> Mapping[str, Any]:
    if value is None or _text(value) == "":
        return {"type": "null", "value": None}
    if field_name in {"amount", "invoice_amount"}:
        money = _money(value)
        if money is not None:
            return {"type": "money", "value": format(money, ".2f")}
    if isinstance(value, (date, datetime)):
        return {"type": "date", "value": value.isoformat()[:10]}
    return {"type": "text", "value": _text(value)}


def _json_value(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): _json_value(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [_json_value(item) for item in value]
    if isinstance(value, (date, datetime, Decimal)):
        return str(value)
    return value


def _canonical_json(value: Any) -> str:
    return json.dumps(
        _json_value(value),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
