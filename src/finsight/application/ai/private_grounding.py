"""Authorized V2 financial grounding for Stage 2 Ask Fin.

This adapter reads the sealed V2 validation projection.  It never reads the
legacy review-cycle grounding model.  Source records are reconstructed only
when their dataset fingerprint exactly matches the sealed Validation Run.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Iterable, Mapping, Optional, Sequence

from finsight.application.ai.private_contracts import (
    AskFinContext,
    AskFinMode,
    GroundedFinSightRecord,
    PrivateAskFinGrounding,
)


HELP_GREETING = (
    "Hey, I’m Fin. I can help you understand how to use FinSight, create a "
    "review, upload files, verify extracted data, review rules, run validation, "
    "and understand the review workflow. Financial questions will become "
    "available after validation results are generated."
)

FINANCIAL_GREETING = (
    "Hey, I’m Fin. I can help you understand this financial review, including "
    "budget variances, GED activity, findings, vendors, accounts, departments, "
    "reconciliation results, and supporting evidence. I can explain and "
    "summarize recorded results, but I cannot make financial decisions or take "
    "action for you."
)

HELP_SUGGESTIONS = (
    "How do I create a financial review?",
    "Which files should I upload?",
    "How do I verify extracted data?",
    "What do the validation rules do?",
    "How do I run validation?",
    "Where will I see findings?",
    "What does Show Evidence display?",
    "How do I reopen a past review?",
)


class PrivateGroundingError(RuntimeError):
    pass


class PrivateGroundingScopeError(PrivateGroundingError):
    pass


@dataclass(frozen=True)
class _ProjectionParts:
    projection: Mapping[str, Any]
    metrics: Mapping[str, Any]
    canonical: Mapping[str, Any]
    analytics: Mapping[str, Any]


def _record(
    review_id: str,
    object_type: str,
    object_id: str,
    label: str,
    facts: Mapping[str, Any],
    **navigation: Any,
) -> GroundedFinSightRecord:
    safe_id = _citation_component(object_id)
    return GroundedFinSightRecord(
        citation_key=f"{object_type}:{review_id}:{safe_id}",
        review_id=review_id,
        object_type=object_type,
        object_id=str(object_id),
        label=label,
        facts=dict(facts),
        navigation_target={"review_id": review_id, **navigation},
    )


def _citation_component(value: Any) -> str:
    """Encode a citation component without introducing a transport dependency."""

    allowed = b"ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789|._-"
    return "".join(
        chr(byte) if byte in allowed else f"%{byte:02X}"
        for byte in str(value).encode("utf-8")
    )


def _unique(records: Iterable[GroundedFinSightRecord]) -> tuple[GroundedFinSightRecord, ...]:
    by_key: dict[str, GroundedFinSightRecord] = {}
    for record in records:
        by_key.setdefault(record.citation_key, record)
    return tuple(by_key[key] for key in sorted(by_key))


class V2FinancialGroundingService:
    """Build a bounded, citable context from one sealed managed review."""

    def __init__(self, financial_review):
        self._financial_review = financial_review

    def context(
        self,
        review_id: str,
        *,
        question: str = "",
        selected_context: Optional[AskFinContext] = None,
    ) -> PrivateAskFinGrounding:
        if selected_context is not None and selected_context.review_id != review_id:
            raise PrivateGroundingScopeError(
                "The selected Ask Fin context belongs to a different review."
            )
        if not review_id:
            return self._help_context("", selected_context)
        projection = self._financial_review.results(review_id)
        if projection is None:
            return self._help_context(review_id, selected_context)
        parts = self._parts(projection)
        records = list(self._base_records(review_id, parts))
        records.extend(
            self._retrieve_financial_records(
                review_id,
                parts,
                question=question,
                selected_context=selected_context,
            )
        )
        records = list(_unique(records))
        if selected_context is not None and not self._context_resolved(
            records, selected_context
        ):
            raise PrivateGroundingScopeError(
                "The selected Ask Fin object is not present in this review."
            )
        return PrivateAskFinGrounding(
            mode=AskFinMode.FINANCIAL_REVIEW,
            review_id=review_id,
            reporting_period=str(parts.canonical.get("reporting_period") or ""),
            validation_run_id=str(projection["run_id"]),
            rule_set_version=str(projection.get("rule_set_id") or ""),
            records=tuple(records),
            suggested_questions=self._financial_suggestions(parts),
            context=selected_context,
        )

    def _help_context(
        self, review_id: str, selected_context: Optional[AskFinContext]
    ) -> PrivateAskFinGrounding:
        if selected_context is not None:
            raise PrivateGroundingScopeError(
                "Financial object context is unavailable before validation."
            )
        facts = (
            (
                "review-workflow",
                "FinSight review workflow",
                {
                    "steps": [
                        "Create a review",
                        "Upload one Budget report and one GED report",
                        "Verify extracted data",
                        "Review the active rules",
                        "Run deterministic validation",
                        "Review findings and source evidence",
                    ],
                    "financial_results_available_after": "Validation completes",
                },
            ),
            (
                "supported-files",
                "Supported source reports",
                {
                    "supported_files": ["Budget Report (.xlsx)", "GED Report (.xlsx)"],
                    "budget_layout": "Approved FinSight Budget report layout",
                    "ged_layout": "Approved FinSight GED report layout",
                },
            ),
            (
                "privacy",
                "Private Ask Fin behavior",
                {
                    "inference": "Approved local Ollama runtime only",
                    "external_ai": "Disabled",
                    "internet_retrieval": "Not supported",
                    "financial_decisions": "Ask Fin never makes or authorizes them",
                },
            ),
            (
                "evidence",
                "Findings and evidence",
                {
                    "finding_source": "Recorded deterministic Rule Results",
                    "show_evidence": (
                        "Shows the relevant Budget and GED records, source workbook, "
                        "worksheet, row, field, original value, and reviewed value."
                    ),
                },
            ),
        )
        records = tuple(
            _record(review_id, "help", object_id, label, values, view="help")
            for object_id, label, values in facts
        )
        return PrivateAskFinGrounding(
            mode=AskFinMode.APPLICATION_HELP,
            review_id=review_id,
            reporting_period="",
            validation_run_id=None,
            rule_set_version=None,
            records=records,
            suggested_questions=HELP_SUGGESTIONS,
        )

    @staticmethod
    def _parts(projection: Mapping[str, Any]) -> _ProjectionParts:
        metrics = projection.get("metrics") or {}
        canonical = metrics.get("canonical_financial_dataset") or {}
        analytics = metrics.get("analytics") or {}
        if (
            canonical.get("schema_version") != "CFD-1.0"
            or not projection.get("completion_seal")
            or projection.get("status") != "COMPLETE"
        ):
            raise PrivateGroundingError(
                "Ask Fin requires a sealed V2 canonical financial result."
            )
        return _ProjectionParts(projection, metrics, canonical, analytics)

    def _base_records(
        self, review_id: str, parts: _ProjectionParts
    ) -> Iterable[GroundedFinSightRecord]:
        projection, metrics, canonical, analytics = (
            parts.projection,
            parts.metrics,
            parts.canonical,
            parts.analytics,
        )
        basis = projection.get("basis") or {}
        summary = analytics.get("financial_summary") or {}
        yield _record(
            review_id,
            "review",
            projection["run_id"],
            f"{canonical.get('reporting_period', '')} financial review",
            {
                "validation_run_id": projection["run_id"],
                "validation_status": projection["status"],
                "completion_seal": projection["completion_seal"],
                "rule_set_version": projection.get("rule_set_id"),
                "reporting_period": canonical.get("reporting_period"),
                "department_number": canonical.get("department_number"),
                "department_name": canonical.get("department_name"),
                "overall_status": metrics.get("overall_status"),
                "budget_health": metrics.get("budget_health"),
                "data_quality": metrics.get("data_quality"),
                "reconciliation_status": metrics.get("reconciliation_status"),
                "findings": metrics.get("findings"),
                "budget": summary.get("bgt_label"),
                "actual_ged": summary.get("ged_label"),
                "atd": summary.get("atd_label"),
                "etc": summary.get("etc_label"),
                "eac": summary.get("eac_label"),
                "delta": summary.get("delta_label"),
                "budget_file": basis.get("budget_filename"),
                "ged_file": basis.get("ged_filename"),
                "dataset_fingerprint": projection.get("dataset_fingerprint"),
            },
            view="overview",
            run_id=projection["run_id"],
        )

    def _retrieve_financial_records(
        self,
        review_id: str,
        parts: _ProjectionParts,
        *,
        question: str,
        selected_context: Optional[AskFinContext],
    ) -> Iterable[GroundedFinSightRecord]:
        if not question.strip() and selected_context is None:
            return
        lowered = question.casefold()
        projection, canonical, analytics = (
            parts.projection,
            parts.canonical,
            parts.analytics,
        )
        accounts = list(canonical.get("accounts") or ())
        findings = list(projection.get("findings") or ())
        scope_results = list(projection.get("scope_results") or ())
        selected_type = selected_context.object_type.casefold() if selected_context else ""
        selected_id = selected_context.object_id if selected_context else ""

        mentioned_accounts = set(re.findall(r"(?<!\d)(\d{6})(?!\d)", question))
        selected_account_department = ""
        if selected_type == "account":
            selected_scope_parts = selected_id.split("|", 1)
            if len(selected_scope_parts) == 2:
                selected_account_department = selected_scope_parts[0]
            mentioned_accounts.add(selected_scope_parts[-1])
        relevant_findings = list(findings)
        if selected_type == "finding":
            relevant_findings = [
                item for item in findings if str(item.get("finding_id")) == selected_id
            ]
        elif selected_type == "transaction":
            relevant_findings = [
                item
                for item in findings
                if selected_id
                in {str(value) for value in item.get("source_records", ())}
            ]
        elif selected_type == "vendor":
            vendor_source_ids = self._matching_source_ids(
                review_id,
                parts,
                selected_context=selected_context,
            )
            relevant_findings = [
                item
                for item in findings
                if vendor_source_ids.intersection(
                    str(value) for value in item.get("source_records", ())
                )
            ]
        elif mentioned_accounts:
            relevant_findings = [
                item
                for item in findings
                if str(item.get("account_number")) in mentioned_accounts
                and (
                    not selected_account_department
                    or str(item.get("department_number"))
                    == selected_account_department
                )
            ]
        elif selected_type == "department":
            relevant_findings = [
                item
                for item in findings
                if str(item.get("department_number")) == selected_id
            ]

        relevant_accounts = []
        for account in accounts:
            scope_key = str(account.get("scope_key") or "")
            if selected_type == "account" and selected_id not in {
                scope_key,
                str(account.get("account_number")),
            }:
                continue
            if selected_type == "department" and str(
                account.get("department_number")
            ) != selected_id:
                continue
            if mentioned_accounts and str(account.get("account_number")) not in mentioned_accounts:
                continue
            if (
                not selected_context
                and not mentioned_accounts
                and not any(
                    str(item.get("account_number")) == str(account.get("account_number"))
                    and str(item.get("department_number"))
                    == str(account.get("department_number"))
                    for item in relevant_findings
                )
            ):
                continue
            relevant_accounts.append(account)
        if not relevant_accounts and not selected_context and not mentioned_accounts:
            ranked = analytics.get("variance_ranked_accounts") or ()
            ranked_scopes = {
                str(item.get("scope_key")) for item in list(ranked)[:12]
            }
            relevant_accounts = [
                item for item in accounts if str(item.get("scope_key")) in ranked_scopes
            ]
        for account in relevant_accounts:
            yield self._account_record(review_id, account)
        if selected_type == "department":
            department_accounts = [
                {
                    "scope_key": item.get("scope_key"),
                    "account_number": item.get("account_number"),
                    "account_name": item.get("account_name"),
                    "bgt_label": item.get("bgt_label"),
                    "summed_ged_amount_label": item.get(
                        "summed_ged_amount_label"
                    ),
                    "finding_count": item.get("finding_count"),
                }
                for item in relevant_accounts
            ]
            department_name = next(
                (
                    item.get("department_name")
                    for item in relevant_accounts
                    if item.get("department_name")
                ),
                "",
            )
            yield _record(
                review_id,
                "department",
                selected_id,
                f"{selected_id} {department_name}".strip(),
                {
                    "department_number": selected_id,
                    "department_name": department_name,
                    "accounts": department_accounts,
                    "note": (
                        "Account values are recorded values. Ask Fin does not "
                        "recalculate a department total."
                    ),
                },
                view="financial_analysis",
                tab="department",
                department_number=selected_id,
            )

        for finding in relevant_findings:
            yield self._finding_record(review_id, projection, finding)

        relevant_rule_ids = {
            str(item.get("rule_id")) for item in relevant_findings
        }
        relevant_scopes = {
            (
                str(item.get("department_number")),
                str(item.get("account_number")),
            )
            for item in relevant_findings
        }
        for result in scope_results:
            scope = (
                str(result.get("department_number")),
                str(result.get("account_number")),
            )
            if (
                str(result.get("rule_id")) in relevant_rule_ids
                and scope in relevant_scopes
            ):
                yield self._result_record(review_id, projection, result)

        vendor_rows = list(analytics.get("ged_by_vendor") or ())
        selected_vendor = selected_id if selected_type == "vendor" else ""
        vendor_question = "vendor" in lowered or "supplier" in lowered
        for vendor in vendor_rows:
            name = str(vendor.get("vendor_name") or "")
            if selected_vendor and name != selected_vendor:
                continue
            if not selected_vendor and not vendor_question and name.casefold() not in lowered:
                continue
            yield _record(
                review_id,
                "vendor",
                name,
                name,
                vendor,
                view="financial_analysis",
                tab="vendor",
                vendor=name,
            )

        if (
            projection.get("predecessor_run_id")
            and any(
                token in lowered
                for token in (
                    "compare",
                    "previous run",
                    "what changed",
                    "rule was edited",
                    "rule change",
                    "revalidation",
                )
            )
        ):
            try:
                comparison = self._financial_review.compare_validation_runs(
                    review_id,
                    str(projection["predecessor_run_id"]),
                    str(projection["run_id"]),
                )
            except Exception:
                comparison = None
            if comparison is not None:
                yield _record(
                    review_id,
                    "run-comparison",
                    (
                        f"{projection['predecessor_run_id']}|"
                        f"{projection['run_id']}"
                    ),
                    "Previous and current validation run comparison",
                    comparison,
                    view="financial_analysis",
                    tab="reconciliation",
                    prior_run_id=projection["predecessor_run_id"],
                    current_run_id=projection["run_id"],
                )

        source_ids = {
            str(record_id)
            for item in relevant_findings
            for record_id in item.get("source_records", ())
        }
        if selected_type == "transaction":
            source_ids.add(selected_id)
        if selected_type == "vendor" or selected_type == "account":
            source_ids.update(
                self._matching_source_ids(
                    review_id,
                    parts,
                    selected_context=selected_context,
                )
            )
        yield from self._source_records(review_id, parts, source_ids)

    def _matching_source_ids(
        self,
        review_id: str,
        parts: _ProjectionParts,
        *,
        selected_context: AskFinContext,
    ) -> set[str]:
        dataset = self._sealed_dataset(review_id, parts)
        if dataset is None:
            return set()
        values = set()
        for item in dataset.ged_transactions:
            if selected_context.object_type.casefold() == "vendor":
                if str(item.value("vendor_name") or "") == selected_context.object_id:
                    values.add(item.record_id)
            elif selected_context.object_type.casefold() == "account":
                scope_parts = selected_context.object_id.split("|", 1)
                selected_department = (
                    scope_parts[0] if len(scope_parts) == 2 else ""
                )
                selected_account = scope_parts[-1]
                if (
                    str(item.value("account_number") or "") == selected_account
                    and (
                        not selected_department
                        or str(item.value("department_number") or "")
                        == selected_department
                    )
                ):
                    values.add(item.record_id)
        return values

    def _source_records(
        self,
        review_id: str,
        parts: _ProjectionParts,
        source_ids: set[str],
    ) -> Iterable[GroundedFinSightRecord]:
        if not source_ids:
            return ()
        dataset = self._sealed_dataset(review_id, parts)
        if dataset is None:
            return ()
        basis = parts.projection.get("basis") or {}
        output = []
        for item in (*dataset.budget_records, *dataset.ged_records):
            if item.record_id not in source_ids:
                continue
            filename = (
                basis.get("budget_filename")
                if item.source_role == "BUDGET"
                else basis.get("ged_filename")
            )
            output.append(
                _record(
                    review_id,
                    "transaction" if item.source_role == "GED" else "budget-source",
                    item.record_id,
                    f"{item.source_role} row {item.row_number}",
                    {
                        "source_file": filename,
                        "source_role": item.source_role,
                        "worksheet": item.worksheet,
                        "source_row": item.row_number,
                        "row_kind": item.row_kind,
                        "fields": dict(item.current),
                        "original_fields": dict(item.original),
                        "cells": dict(item.cells),
                        "edited": item.current != item.original,
                    },
                    view="source_evidence",
                    source_role=item.source_role,
                    worksheet=item.worksheet,
                    source_row=item.row_number,
                    record_id=item.record_id,
                )
            )
        # Keep the local-model context bounded. The full source lineage remains
        # available in FinSight and through citation navigation; Ask Fin gets a
        # deterministic evidence sample rather than dozens of near-identical
        # rows that can exceed a small local model's useful context window.
        return tuple(output[:6])

    def _sealed_dataset(
        self, review_id: str, parts: _ProjectionParts
    ):
        try:
            dataset = self._financial_review.reconstruct_dataset(review_id)
        except Exception:
            return None
        if dataset.fingerprint != parts.projection.get("dataset_fingerprint"):
            return None
        return dataset

    @staticmethod
    def _account_record(
        review_id: str, account: Mapping[str, Any]
    ) -> GroundedFinSightRecord:
        scope_key = str(account.get("scope_key"))
        return _record(
            review_id,
            "account",
            scope_key,
            f"{account.get('account_number')} {account.get('account_name')}",
            account,
            view="financial_analysis",
            tab="account",
            department_number=account.get("department_number"),
            account_number=account.get("account_number"),
        )

    @staticmethod
    def _finding_record(
        review_id: str,
        projection: Mapping[str, Any],
        finding: Mapping[str, Any],
    ) -> GroundedFinSightRecord:
        finding_id = str(finding.get("finding_id"))
        return _record(
            review_id,
            "finding",
            finding_id,
            str(finding.get("rule_name") or "Validation finding"),
            {
                **dict(finding),
                "validation_run_id": projection.get("run_id"),
                "rule_set_version": projection.get("rule_set_id"),
            },
            view="findings",
            finding_id=finding_id,
        )

    @staticmethod
    def _result_record(
        review_id: str,
        projection: Mapping[str, Any],
        result: Mapping[str, Any],
    ) -> GroundedFinSightRecord:
        object_id = "|".join(
            (
                str(result.get("rule_id")),
                str(result.get("scope_id")),
            )
        )
        return _record(
            review_id,
            "rule-result",
            object_id,
            f"{result.get('rule_id')} result for {result.get('scope_id')}",
            {
                **dict(result),
                "validation_run_id": projection.get("run_id"),
                "rule_set_version": projection.get("rule_set_id"),
            },
            view="findings",
            rule_id=result.get("rule_id"),
            scope_id=result.get("scope_id"),
        )

    @staticmethod
    def _context_resolved(
        records: Sequence[GroundedFinSightRecord], context: AskFinContext
    ) -> bool:
        kind = context.object_type.casefold()
        for record in records:
            if record.object_type.casefold() != kind:
                continue
            if context.object_id in {
                record.object_id,
                str(record.facts.get("account_number") or ""),
            }:
                return True
        return False

    @staticmethod
    def _financial_suggestions(parts: _ProjectionParts) -> tuple[str, ...]:
        findings = list(parts.projection.get("findings") or ())
        questions: list[str] = []
        overrun = next(
            (item for item in findings if item.get("rule_id") == "CORE-01"),
            None,
        )
        if overrun:
            questions.append(
                f"Why is Account {overrun.get('account_number')} over budget?"
            )
            questions.append("Which vendors contributed most to the overrun?")
        if findings:
            questions.extend(
                (
                    "Show the evidence for the highest-severity finding.",
                    "Which accounts need attention?",
                    "Summarize the top findings.",
                )
            )
        if any(item.get("rule_id") == "CORE-03" for item in findings):
            questions.append("Are there duplicate GED transactions?")
        if any(item.get("rule_id") == "CORE-04" for item in findings):
            questions.append("Which GED records are missing or incomplete?")
        if any(
            item.get("status") == "NOT_EVALUATED"
            for item in parts.projection.get("scope_results", ())
        ):
            questions.append("Why was this rule not evaluated?")
        if parts.projection.get("predecessor_run_id"):
            questions.extend(
                (
                    "Compare this result with the previous run.",
                    "What changed after the rule was edited?",
                )
            )
        return tuple(dict.fromkeys(questions))
