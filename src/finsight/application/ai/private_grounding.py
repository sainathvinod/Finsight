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
_SPECIFIC_FINANCIAL_CONTEXT_TYPES = frozenset(
    {"account", "vendor", "department", "transaction", "finding"}
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


def _unique(
    records: Iterable[GroundedFinSightRecord],
) -> tuple[GroundedFinSightRecord, ...]:
    by_key: dict[str, GroundedFinSightRecord] = {}
    for record in records:
        by_key.setdefault(record.citation_key, record)
    # Retrieval order is part of the deterministic relevance contract.  Do not
    # re-sort records alphabetically after the query planner has ranked them.
    return tuple(by_key.values())


_SEVERITY_RANK = {
    "critical": 0,
    "high": 1,
    "medium": 2,
    "low": 3,
}


def _finding_rank(item: Mapping[str, Any]) -> tuple[int, str]:
    return (
        _SEVERITY_RANK.get(str(item.get("severity") or "").casefold(), 99),
        str(item.get("finding_id") or ""),
    )


def _has_any(value: str, phrases: Sequence[str]) -> bool:
    return any(phrase in value for phrase in phrases)


def _normalized_entity(value: Any) -> str:
    return re.sub(r"[^a-z0-9]+", " ", str(value or "").casefold()).strip()


def _source_record_row(value: Any) -> Optional[int]:
    match = re.search(r":(\d+)$", str(value or ""))
    return int(match.group(1)) if match else None


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
            suggested_questions=self._financial_suggestions(
                parts, selected_context=selected_context
            ),
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
                "findings_by_severity": list(
                    analytics.get("findings_by_severity") or ()
                ),
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
        leadership = projection.get("leadership_summary")
        if isinstance(leadership, Mapping):
            yield _record(
                review_id,
                "leadership-summary",
                projection["run_id"],
                f"{canonical.get('reporting_period', '')} leadership summary",
                {
                    "overall_status": leadership.get("overall_status"),
                    "budget_health": leadership.get("budget_health"),
                    "financial_position": dict(
                        leadership.get("financial_position") or {}
                    ),
                    "ged_status": dict(leadership.get("ged_status") or {}),
                    "highest_priority_findings": list(
                        {
                            **dict(item),
                            "explanation": item.get("what_happened"),
                        }
                        for item in (leadership.get("highest_priority_findings") or ())
                        if isinstance(item, Mapping)
                    )[:5],
                    "recommended_next_steps": list(
                        leadership.get("recommended_next_steps") or ()
                    )[:5],
                    "data_quality_limitations": list(
                        leadership.get("data_quality_limitations") or ()
                    )[:5],
                    "decision_boundary": leadership.get("decision_boundary"),
                },
                view="review_summary",
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
        leadership = projection.get("leadership_summary") or {}
        priority_order = {
            str(item.get("finding_id") or ""): index
            for index, item in enumerate(
                leadership.get("highest_priority_findings") or ()
            )
            if isinstance(item, Mapping) and item.get("finding_id")
        }
        findings = sorted(
            list(projection.get("findings") or ()),
            key=lambda item: (
                priority_order.get(str(item.get("finding_id") or ""), 10_000),
                *_finding_rank(item),
            ),
        )
        scope_results = list(projection.get("scope_results") or ())
        selected_type = (
            selected_context.object_type.casefold() if selected_context else ""
        )
        selected_id = selected_context.object_id if selected_context else ""
        evidence_intent = _has_any(
            lowered,
            (
                "evidence",
                "source row",
                "source record",
                "supporting row",
                "show the row",
                "show rows",
                "which row",
                "where this came from",
                "where did this come from",
            ),
        )
        summary_intent = _has_any(
            lowered,
            (
                "summary",
                "summarize",
                "overview",
                "overall",
                "main points",
                "what should i know",
                "why is this incomplete",
                "why is the review incomplete",
            ),
        )
        priority_intent = _has_any(
            lowered,
            (
                "priority",
                "priorities",
                "most important",
                "highest severity",
                "top finding",
                "needs attention",
                "need attention",
                "look at first",
                "inspect first",
                "what's wrong",
                "what is wrong",
            ),
        )
        finding_intent = priority_intent or _has_any(
            lowered, ("finding", "findings", "issue", "exception")
        )
        account_intent = "account" in lowered
        over_budget_intent = _has_any(
            lowered, ("over budget", "overrun", "exceeds budget")
        )
        vendor_intent = _has_any(
            lowered,
            (
                "vendor",
                "supplier",
                "who contributed",
                "contributed most",
                "who drove",
            ),
        )
        rule_intent = _has_any(lowered, ("rule", "validation result", "reconciliation"))
        named_entity_detail = bool(
            re.match(
                r"^\s*(?:tell\s+me\s+about|explain)\s+",
                question,
                re.IGNORECASE,
            )
            and not _has_any(
                lowered,
                (
                    "review",
                    "finding",
                    "issue",
                    "exception",
                    "ged",
                    "transaction",
                    "journal",
                    "invoice",
                    "duplicate",
                    "missing",
                    "required",
                    "reconcil",
                ),
            )
        )
        explicit_evidence_reference = evidence_intent and bool(
            re.search(
                r"\b(?:account|vendor|supplier|department|finding|"
                r"transaction|journal|invoice|ged|forecast)\b|"
                r"\brows?\s+\d+\b",
                lowered,
                re.IGNORECASE,
            )
        )

        # Resolve identifiers against this sealed review rather than accepting
        # arbitrary digit or vendor-shaped tokens.  The resulting index is
        # request-local and therefore cannot leak objects from another review.
        normalized_question = _normalized_entity(question)
        mentioned_accounts = {
            str(item.get("account_number") or "")
            for item in accounts
            if str(item.get("account_number") or "")
            and (
                re.search(
                    rf"(?<![0-9A-Za-z])"
                    rf"{re.escape(str(item.get('account_number')))}"
                    r"(?![0-9A-Za-z])",
                    question,
                    re.IGNORECASE,
                )
                or (
                    len(_normalized_entity(item.get("account_name"))) >= 4
                    and _normalized_entity(item.get("account_name"))
                    in normalized_question
                )
            )
        }
        vendor_rows = list(analytics.get("ged_by_vendor") or ())
        mentioned_vendors = {
            str(item.get("vendor_name") or "")
            for item in vendor_rows
            if str(item.get("vendor_name") or "")
            and str(item.get("vendor_name")).casefold() in lowered
        }
        department_number = str(canonical.get("department_number") or "")
        department_name = str(canonical.get("department_name") or "")
        requested_department = ""
        if (
            department_number
            and re.search(
                rf"(?<![0-9A-Za-z]){re.escape(department_number)}"
                r"(?![0-9A-Za-z])",
                question,
                re.IGNORECASE,
            )
        ) or (
            len(_normalized_entity(department_name)) >= 4
            and _normalized_entity(department_name) in normalized_question
        ):
            requested_department = department_number
        if selected_type == "department":
            requested_department = selected_id
        requested_source_rows = {
            int(value)
            for value in re.findall(
                r"\b(?:ged\s+|source\s+)?rows?\s+(\d+)\b",
                question,
                re.IGNORECASE,
            )
        }
        semantic_evidence_reference = evidence_intent and _has_any(
            lowered,
            (
                "over budget",
                "overrun",
                "exceeds budget",
                "duplicate",
                "missing",
                "required",
                "reconcil",
                "highest",
                "top finding",
                "most severe",
                "most important",
            ),
        )
        unresolved_evidence_target = (
            explicit_evidence_reference
            and not semantic_evidence_reference
            and selected_type not in _SPECIFIC_FINANCIAL_CONTEXT_TYPES
            and not mentioned_accounts
            and not mentioned_vendors
            and not requested_department
            and not requested_source_rows
        )
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
        elif requested_source_rows:
            relevant_findings = [
                item
                for item in findings
                if requested_source_rows.intersection(
                    row
                    for row in (
                        _source_record_row(value)
                        for value in item.get("source_records", ())
                    )
                    if row is not None
                )
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
                    or str(item.get("department_number")) == selected_account_department
                )
            ]
        elif requested_department:
            relevant_findings = [
                item
                for item in findings
                if str(item.get("department_number")) == requested_department
            ]
        elif mentioned_vendors:
            vendor_source_ids: set[str] = set()
            for vendor_name in mentioned_vendors:
                vendor_source_ids.update(
                    self._matching_source_ids(
                        review_id,
                        parts,
                        selected_context=AskFinContext(
                            review_id=review_id,
                            object_type="vendor",
                            object_id=vendor_name,
                            label=vendor_name,
                        ),
                    )
                )
            relevant_findings = [
                item
                for item in findings
                if vendor_source_ids.intersection(
                    str(value) for value in item.get("source_records", ())
                )
            ]
        elif named_entity_detail:
            # A natural named-entity request is only answerable when the name
            # resolves against this active review. Do not fill an unmatched
            # request with unrelated top findings.
            relevant_findings = []
        elif over_budget_intent:
            relevant_findings = [
                item
                for item in findings
                if str(item.get("rule_id")) == "CORE-01"
                or "over budget" in str(item.get("rule_name") or "").casefold()
            ]
        elif "duplicate" in lowered:
            relevant_findings = [
                item
                for item in findings
                if str(item.get("rule_id")) == "CORE-03"
                or "duplicate" in str(item.get("rule_name") or "").casefold()
            ]
        elif _has_any(
            lowered,
            (
                "missing",
                "required data",
                "required field",
                "incomplete",
            ),
        ):
            relevant_findings = [
                item
                for item in findings
                if str(item.get("rule_id")) == "CORE-04"
                or "required" in str(item.get("rule_name") or "").casefold()
            ]
        elif "reconcil" in lowered:
            relevant_findings = [
                item
                for item in findings
                if str(item.get("rule_id")) == "CORE-05"
                or "reconcil" in str(item.get("rule_name") or "").casefold()
            ]
        elif _has_any(
            lowered,
            (
                "first finding",
                "highest-priority finding",
                "highest priority finding",
            ),
        ):
            relevant_findings = findings[:1]
        elif vendor_intent and not over_budget_intent:
            # A broad vendor question is answered by the recorded vendor
            # analytics.  Unrelated findings would add noise and can imply a
            # relationship that the sealed results do not record.
            relevant_findings = []
        elif evidence_intent:
            # Without a named or conversational scope, generic evidence means
            # the persisted highest-priority finding. An explicit target that
            # did not resolve inside this active review must not fall back to
            # unrelated evidence.
            relevant_findings = (
                [] if unresolved_evidence_target else findings[:1]
            )
        elif summary_intent or finding_intent or account_intent:
            relevant_findings = findings[:5]
        else:
            relevant_findings = findings[:5]

        relevant_findings = relevant_findings[:8]
        finding_scopes = {
            (
                str(item.get("department_number") or ""),
                str(item.get("account_number") or ""),
            )
            for item in relevant_findings
            if item.get("department_number") and item.get("account_number")
        }
        relevant_accounts: list[Mapping[str, Any]] = []
        for account in accounts:
            if unresolved_evidence_target:
                continue
            scope_key = str(account.get("scope_key") or "")
            if selected_type == "account" and selected_id not in {
                scope_key,
                str(account.get("account_number")),
            }:
                continue
            if requested_department and (
                str(account.get("department_number")) != requested_department
            ):
                continue
            if (
                mentioned_accounts
                and str(account.get("account_number")) not in mentioned_accounts
            ):
                continue
            if mentioned_vendors and not mentioned_vendors.intersection(
                str(value) for value in account.get("vendors", ())
            ):
                continue
            if (
                not selected_context
                and not mentioned_accounts
                and not mentioned_vendors
                and (
                    not account_intent
                    and not finding_intent
                    and not evidence_intent
                    and not (vendor_intent and over_budget_intent)
                    and not requested_department
                )
            ):
                continue
            if (
                not selected_context
                and not mentioned_accounts
                and not mentioned_vendors
                and finding_scopes
                and (
                    str(account.get("department_number") or ""),
                    str(account.get("account_number") or ""),
                )
                not in finding_scopes
            ):
                continue
            relevant_accounts.append(account)
        if (
            account_intent
            and not relevant_accounts
            and not selected_context
            and not mentioned_accounts
            and not unresolved_evidence_target
        ):
            ranked = analytics.get("variance_ranked_accounts") or ()
            ranked_scopes = [str(item.get("scope_key")) for item in list(ranked)[:8]]
            relevant_accounts = [
                item
                for scope in ranked_scopes
                for item in accounts
                if str(item.get("scope_key")) == scope
            ]
        relevant_accounts = relevant_accounts[:8]
        for account in relevant_accounts:
            yield self._account_record(review_id, account)
        if requested_department:
            department_accounts = [
                {
                    "scope_key": item.get("scope_key"),
                    "account_number": item.get("account_number"),
                    "account_name": item.get("account_name"),
                    "bgt_label": item.get("bgt_label"),
                    "summed_ged_amount_label": item.get("summed_ged_amount_label"),
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
                requested_department,
                f"{requested_department} {department_name}".strip(),
                {
                    "department_number": requested_department,
                    "department_name": department_name,
                    "account_count": len(department_accounts),
                    "accounts": department_accounts,
                    "note": (
                        "Account values are recorded values. Ask Fin does not "
                        "recalculate a department total."
                    ),
                },
                view="financial_analysis",
                tab="department",
                department_number=requested_department,
            )

        for finding in relevant_findings:
            yield self._finding_record(review_id, projection, finding)

        if rule_intent:
            exact_result_keys = {
                (
                    str(item.get("rule_id") or ""),
                    str(item.get("department_number") or ""),
                    str(item.get("account_number") or ""),
                )
                for item in relevant_findings
                if item.get("rule_id")
                and item.get("department_number")
                and item.get("account_number")
            }
            matched_results = [
                result
                for result in scope_results
                if str(result.get("status") or "").upper() == "FAIL"
                and (
                    str(result.get("rule_id") or ""),
                    str(result.get("department_number") or ""),
                    str(result.get("account_number") or ""),
                )
                in exact_result_keys
            ][:8]
            for result in matched_results:
                yield self._result_record(review_id, projection, result)

        selected_vendor = selected_id if selected_type == "vendor" else ""
        account_vendors = {
            str(value)
            for account in relevant_accounts
            for value in account.get("vendors", ())
            if str(value)
        }
        matched_vendors = []
        for vendor in vendor_rows:
            name = str(vendor.get("vendor_name") or "")
            if selected_type == "account" and vendor_intent:
                # The account record already carries deterministic vendor
                # membership. Review-wide vendor totals are intentionally
                # excluded here because they would be valid global facts but
                # misleading evidence for an account-scoped question.
                continue
            if vendor_intent and over_budget_intent and relevant_findings:
                # The sealed account/finding projections identify contributing
                # vendors but do not persist an account-by-vendor spend ranking.
                # Do not substitute review-wide vendor totals as evidence for
                # an account overrun.
                continue
            if (
                vendor_intent
                and not selected_vendor
                and not mentioned_vendors
                and name.casefold() in {"", "no vendor recorded", "vendor not recorded"}
            ):
                continue
            if selected_vendor and name != selected_vendor:
                continue
            if mentioned_vendors and name not in mentioned_vendors:
                continue
            if (
                account_vendors
                and (mentioned_accounts or selected_type == "account")
                and name not in account_vendors
            ):
                continue
            if not selected_vendor and not vendor_intent and not mentioned_vendors:
                continue
            matched_vendors.append(vendor)
        for vendor in matched_vendors[:8]:
            name = str(vendor.get("vendor_name") or "")
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

        if projection.get("predecessor_run_id") and any(
            token in lowered
            for token in (
                "compare",
                "previous run",
                "what changed",
                "rule was edited",
                "rule change",
                "revalidation",
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
                    (f"{projection['predecessor_run_id']}|{projection['run_id']}"),
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
        if requested_source_rows:
            dataset = self._sealed_dataset(review_id, parts)
            if dataset is not None:
                candidate_records = (
                    dataset.ged_records
                    if "ged" in lowered
                    else (*dataset.budget_records, *dataset.ged_records)
                )
                source_ids.update(
                    item.record_id
                    for item in candidate_records
                    if item.row_number in requested_source_rows
                )
        if selected_type == "vendor" or selected_type == "account":
            source_ids.update(
                self._matching_source_ids(
                    review_id,
                    parts,
                    selected_context=selected_context,
                )
            )
        if mentioned_accounts:
            for account in relevant_accounts:
                source_ids.update(
                    self._matching_source_ids(
                        review_id,
                        parts,
                        selected_context=AskFinContext(
                            review_id=review_id,
                            object_type="account",
                            object_id=str(account.get("scope_key")),
                            label=str(account.get("account_number")),
                        ),
                    )
                )
        if mentioned_vendors:
            for vendor_name in mentioned_vendors:
                source_ids.update(
                    self._matching_source_ids(
                        review_id,
                        parts,
                        selected_context=AskFinContext(
                            review_id=review_id,
                            object_type="vendor",
                            object_id=vendor_name,
                            label=vendor_name,
                        ),
                    )
                )
        include_sources = (
            evidence_intent
            or bool(mentioned_accounts)
            or bool(mentioned_vendors)
            or bool(requested_source_rows)
            or _has_any(
                lowered,
                (
                    "duplicate",
                    "missing",
                    "incomplete",
                    "first finding",
                    "explain the",
                ),
            )
            or selected_type in {"finding", "transaction", "vendor", "account"}
        )
        if include_sources:
            yield from self._source_records(
                review_id,
                parts,
                source_ids,
                limit=8,
            )

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
                selected_department = scope_parts[0] if len(scope_parts) == 2 else ""
                selected_account = scope_parts[-1]
                if str(item.value("account_number") or "") == selected_account and (
                    not selected_department
                    or str(item.value("department_number") or "") == selected_department
                ):
                    values.add(item.record_id)
        return values

    def _source_records(
        self,
        review_id: str,
        parts: _ProjectionParts,
        source_ids: set[str],
        *,
        limit: int = 6,
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
                    source_file=filename,
                    source_role=item.source_role,
                    worksheet=item.worksheet,
                    source_row=item.row_number,
                    cell=str(
                        item.cells.get(
                            "amount" if item.source_role == "GED" else "bgt",
                            "",
                        )
                    ),
                    account_number=str(
                        item.value("account_number") or ""
                    ),
                    vendor=str(item.value("vendor_name") or ""),
                    transaction_reference=str(
                        item.value("journal_number") or ""
                    ),
                    amount=str(item.value("amount") or ""),
                    validation_run_id=str(
                        parts.projection.get("run_id") or ""
                    ),
                    record_id=item.record_id,
                )
            )
        # Keep the local-model context bounded. The full source lineage remains
        # available in FinSight and through citation navigation; Ask Fin gets a
        # deterministic evidence sample rather than dozens of near-identical
        # rows that can exceed a small local model's useful context window.
        return tuple(output[: max(1, limit)])

    def _sealed_dataset(self, review_id: str, parts: _ProjectionParts):
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
        explanation = finding.get("explain_this")
        supporting = (
            explanation.get("supporting_evidence")
            if isinstance(explanation, Mapping)
            else {}
        )
        technical = (
            explanation.get("technical_details")
            if isinstance(explanation, Mapping)
            else {}
        )
        if not isinstance(supporting, Mapping):
            supporting = {}
        if not isinstance(technical, Mapping):
            technical = {}
        lineage = supporting.get("lineage")
        first_lineage = (
            next(
                (item for item in lineage if isinstance(item, Mapping)),
                {},
            )
            if isinstance(lineage, (list, tuple))
            else {}
        )
        source_record_ids = {
            str(value) for value in finding.get("source_records", ())
        }
        metrics = projection.get("metrics") or {}
        analytics = metrics.get("analytics") if isinstance(metrics, Mapping) else {}
        largest_transactions = (
            analytics.get("largest_transactions")
            if isinstance(analytics, Mapping)
            else ()
        )
        recorded_largest_transactions = [
            dict(item)
            for item in (largest_transactions or ())
            if isinstance(item, Mapping)
            and str(item.get("record_id") or "") in source_record_ids
        ][:3]
        return _record(
            review_id,
            "finding",
            finding_id,
            str(finding.get("rule_name") or "Validation finding"),
            {
                **dict(finding),
                "validation_run_id": projection.get("run_id"),
                "rule_set_version": projection.get("rule_set_id"),
                "recorded_largest_transactions": recorded_largest_transactions,
            },
            view="findings",
            finding_id=finding_id,
            source_file=str(
                first_lineage.get("source_file")
                or first_lineage.get("workbook")
                or ""
            ),
            worksheet=str(
                first_lineage.get("worksheet")
                or first_lineage.get("sheet")
                or ""
            ),
            source_row=first_lineage.get(
                "row", first_lineage.get("source_row")
            ),
            cell=str(first_lineage.get("cell") or ""),
            account_number=str(finding.get("account_number") or ""),
            rule_name=str(
                technical.get("rule_name")
                or finding.get("rule_name")
                or ""
            ),
            rule_version=str(
                technical.get("rule_version")
                or finding.get("rule_version")
                or ""
            ),
            validation_run_id=str(projection.get("run_id") or ""),
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
    def _financial_suggestions(
        parts: _ProjectionParts,
        *,
        selected_context: Optional[AskFinContext] = None,
    ) -> tuple[str, ...]:
        if selected_context is not None:
            kind = selected_context.object_type.casefold()
            identifier = selected_context.object_id.split("|")[-1]
            if kind == "finding":
                return (
                    "Why did FinSight flag this finding?",
                    "Show the supporting evidence for this finding.",
                )
            if kind == "account":
                return (
                    f"Summarize Account {identifier}.",
                    f"Show the evidence for Account {identifier}.",
                    f"Which vendors are recorded for Account {identifier}?",
                )
            if kind == "vendor":
                return (
                    f"Summarize recorded spend for {identifier}.",
                    f"Show the source records for {identifier}.",
                )
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
            questions.append("Which vendors have the highest recorded spend?")
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
        if parts.projection.get("predecessor_run_id"):
            questions.extend(
                (
                    "Compare this result with the previous run.",
                    "What changed after the rule was edited?",
                )
            )
        return tuple(dict.fromkeys(questions))
