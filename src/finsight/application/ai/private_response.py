"""Application-authored business responses over verified Ask Fin claims.

The local model remains bounded by the same closed claims, while this module
guarantees that common financial-review questions receive a consistent,
readable answer even when a small local model selects too little context.
It performs no financial calculation and can only arrange exact claims
already derived from the sealed Validation Run.
"""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Iterable, Sequence

from finsight.application.ai.private_claims import (
    SupportedClaim,
    build_supported_claims,
)
from finsight.application.ai.private_contracts import (
    AskFinContext,
    GroundedFinSightRecord,
    PrivateAskFinGrounding,
)
from finsight.application.ai.private_intent import AskFinIntent


@dataclass(frozen=True)
class DeterministicAskFinResponse:
    answer_text: str
    citation_keys: tuple[str, ...]
    resolved_context: AskFinContext | None
    follow_up_questions: tuple[str, ...]


def build_business_response(
    grounding: PrivateAskFinGrounding,
    question: str,
    intent: AskFinIntent,
) -> DeterministicAskFinResponse | None:
    """Build a verified response plan from immutable closed claims."""

    claims = _ordered_claims(grounding)
    if not claims:
        return None
    lowered = question.casefold()
    selected: list[SupportedClaim] = []

    if intent is AskFinIntent.REVIEW_SUMMARY:
        selected.extend(
            _select(
                claims,
                (
                    "review.summary_intro",
                    "review.summary_status",
                    "review.summary_budget",
                    "review.summary_actual",
                    "review.summary_eac",
                    "review.summary_findings",
                    "review.summary_severity",
                    "leadership.data_issue",
                    "leadership.limitation.",
                ),
                limit=10,
            )
        )
    elif intent is AskFinIntent.FINDINGS_SUMMARY:
        if "incomplete" in lowered:
            selected.extend(
                _select(
                    claims,
                    (
                        "review.summary_status",
                        "leadership.data_issue",
                        "leadership.limitation.",
                    ),
                    limit=7,
                )
            )
            selected.extend(_finding_detail_claims(claims, include_sources=True))
        elif _specific_finding_question(lowered) or grounding.context is not None:
            selected.extend(_finding_detail_claims(claims, include_sources=True))
        else:
            selected.extend(
                _select(
                    claims,
                    (
                        "review.summary_findings",
                        "leadership.priority.",
                        "leadership.priority_explanation.",
                        "finding.what_happened",
                    ),
                    limit=6,
                )
            )
    elif intent is AskFinIntent.ACCOUNT:
        selected.extend(
            _select(
                claims,
                (
                    "account.over_budget",
                    "account.identity",
                    "account.budget",
                    "account.ged_spend",
                    "account.variance",
                    "finding.variance_percentage",
                    "finding.contributing_vendor",
                    "account.transactions",
                    "finding.rule",
                    "finding.threshold",
                    "finding.source_rows",
                    "finding.key_transaction",
                    "finding.contributing_transaction",
                    "source.location",
                    "source.vendor_name",
                    "source.journal_number",
                    "source.amount",
                    "finding.transaction",
                ),
                limit=24,
                per_predicate_limit=3,
            )
        )
    elif intent is AskFinIntent.VENDOR:
        has_account_scope = any(
            item.object_type.casefold() == "account"
            for item in grounding.records
        )
        if has_account_scope and (
            grounding.context is None
            or grounding.context.object_type.casefold() in {"account", "finding"}
        ):
            if grounding.context is None or (
                grounding.context.object_type.casefold() == "account"
            ):
                selected.extend(
                    _select(
                        claims,
                        ("account.identity",),
                        limit=1,
                        per_predicate_limit=1,
                    )
                )
            selected.extend(
                _select(
                    claims,
                    (
                        "account.vendor",
                        "finding.contributing_vendor",
                        "account.contributing_vendor",
                        "finding.transaction",
                    ),
                    limit=6,
                )
            )
        else:
            selected.extend(
                _select(
                    claims,
                    (
                        "vendor.summary",
                        "vendor.transactions",
                        "finding.contributing_vendor",
                    ),
                    limit=6,
                )
            )
    elif intent is AskFinIntent.DEPARTMENT:
        selected.extend(
            _select(
                claims,
                (
                    "department.identity",
                    "department.account_count",
                    "review.summary_budget",
                    "review.summary_actual",
                    "review.summary_eac",
                    "account.identity",
                    "account.variance",
                    "account.budget",
                    "account.ged_spend",
                ),
                limit=8,
            )
        )
    elif intent is AskFinIntent.GED_TRANSACTION:
        if _specific_finding_question(lowered):
            selected.extend(_finding_detail_claims(claims, include_sources=True))
        else:
            selected.extend(
                _select(
                    claims,
                    (
                        "source.location",
                        "source.account_number",
                        "source.vendor_name",
                        "source.journal_number",
                        "source.journal_date",
                        "source.amount",
                    "finding.transaction",
                ),
                limit=12,
            )
            )
    elif intent is AskFinIntent.EVIDENCE:
        selected.extend(
            _select(
                claims,
                ("account.identity",),
                limit=1,
                per_predicate_limit=1,
            )
        )
        if grounding.context is not None:
            context_kind = grounding.context.object_type.casefold()
            if context_kind == "finding":
                selected.extend(
                    _select(
                        claims,
                        ("finding.business_title", "finding.account_number"),
                        limit=2,
                        per_predicate_limit=1,
                    )
                )
            elif context_kind == "vendor":
                selected.extend(
                    _select(
                        claims,
                        ("vendor.summary",),
                        limit=1,
                        per_predicate_limit=1,
                    )
                )
        selected.extend(_finding_evidence_claims(claims))
        selected.extend(
            _select(
                claims,
                (
                    "source.location",
                    "source.row",
                    "source.account_number",
                    "source.vendor_name",
                    "source.journal_number",
                    "source.amount",
                    "source.bgt",
                ),
                limit=18,
                existing=selected,
                per_predicate_limit=4,
            )
        )
    elif intent is AskFinIntent.COMPARISON:
        selected.extend(_select(claims, ("comparison.",), limit=5))
        if not selected:
            selected.extend(
                _select(
                    claims,
                    (
                        "account.identity",
                        "account.budget",
                        "account.ged_spend",
                        "account.variance",
                        "finding.variance_percentage",
                    ),
                    limit=6,
                )
            )
    elif intent is AskFinIntent.CLARIFICATION_FOLLOW_UP:
        if any(value in lowered for value in ("evidence", "rows", "source", "where")):
            selected.extend(
                _select(
                    claims,
                    ("account.identity", "finding.business_title"),
                    limit=2,
                    per_predicate_limit=1,
                )
            )
            selected.extend(_finding_evidence_claims(claims))
            selected.extend(
                _select(
                    claims,
                    ("source.location",),
                    limit=3,
                    per_predicate_limit=3,
                )
            )
        elif "vendor" in lowered:
            selected.extend(
                _select(
                    claims,
                    (
                        "finding.contributing_vendor",
                        "account.contributing_vendor",
                        "vendor.summary",
                        "finding.transaction",
                    ),
                    limit=6,
                )
            )
        elif any(value in lowered for value in ("inspect", "look at next")):
            selected.extend(
                _select(
                    claims,
                    (
                        "finding.next_step",
                        "leadership.next_step.",
                        "source.location",
                    ),
                    limit=4,
                    per_predicate_limit=2,
                )
            )
        else:
            selected.extend(_context_detail_claims(claims, grounding))

    selected = _dedupe(selected)
    if not selected:
        return None
    answer = "\n".join(
        f"{claim.text} [{claim.citation_key}]." for claim in selected
    )
    return DeterministicAskFinResponse(
        answer_text=answer,
        citation_keys=tuple(
            dict.fromkeys(claim.citation_key for claim in selected)
        ),
        resolved_context=_resolved_context(grounding, intent),
        follow_up_questions=_follow_up_questions(grounding, intent),
    )


def _ordered_claims(
    grounding: PrivateAskFinGrounding,
) -> tuple[SupportedClaim, ...]:
    claims = build_supported_claims(grounding.records)
    record_order = {
        item.citation_key: index for index, item in enumerate(grounding.records)
    }
    return tuple(
        sorted(
            claims,
            key=lambda item: (
                record_order.get(item.citation_key, 10_000),
                item.predicate,
            ),
        )
    )


def _select(
    claims: Sequence[SupportedClaim],
    predicates: Sequence[str],
    *,
    limit: int,
    existing: Sequence[SupportedClaim] = (),
    per_predicate_limit: int | None = None,
) -> list[SupportedClaim]:
    output = list(existing)
    for predicate in predicates:
        selected_for_predicate = 0
        for claim in claims:
            if claim in output:
                continue
            matches = (
                claim.predicate.startswith(predicate)
                if predicate.endswith(".")
                else claim.predicate == predicate
            )
            if matches:
                output.append(claim)
                selected_for_predicate += 1
                if len(output) >= limit:
                    return output[len(existing) :]
                if (
                    per_predicate_limit is not None
                    and selected_for_predicate >= per_predicate_limit
                ):
                    break
    return output[len(existing) :]


def _dedupe(values: Iterable[SupportedClaim]) -> list[SupportedClaim]:
    output: list[SupportedClaim] = []
    seen: set[tuple[str, str]] = set()
    for value in values:
        identity = (value.citation_key, value.text)
        if identity in seen:
            continue
        seen.add(identity)
        output.append(value)
    return output


def _specific_finding_question(question: str) -> bool:
    return bool(
        re.search(
            r"\b(?:first|highest[-\s]priority|duplicate|missing|required|"
            r"incomplete|unmapped|reconcil|explain)\b",
            question,
            re.IGNORECASE,
        )
    )


def _finding_detail_claims(
    claims: Sequence[SupportedClaim],
    *,
    include_sources: bool,
) -> list[SupportedClaim]:
    predicates = [
        "finding.business_title",
        "finding.severity",
        "finding.department_number",
        "finding.department_name",
        "finding.account_number",
        "finding.account_name",
        "finding.what_happened",
        "finding.why_flagged",
        "finding.why_it_matters",
        "finding.expected_detail",
        "finding.actual_detail",
    ]
    if include_sources:
        # Put the actual source-record location before lower-priority
        # explanatory detail so missing-value answers always carry a
        # navigable transaction citation, not only finding-level lineage.
        predicates.append("source.location")
    predicates.extend(
        [
        "finding.contributing_vendor",
        "finding.rule",
        "finding.threshold",
        "finding.source_rows",
        "finding.next_step",
        ]
    )
    if include_sources:
        predicates.append("finding.transaction")
    return _select(
        claims,
        tuple(predicates),
        limit=24,
        per_predicate_limit=3,
    )


def _finding_evidence_claims(
    claims: Sequence[SupportedClaim],
) -> list[SupportedClaim]:
    return _select(
        claims,
        (
            "finding.source_location",
            "finding.source_rows",
            "finding.rule",
            "finding.threshold",
            "finding.expected_detail",
            "finding.actual_detail",
            "finding.transaction",
        ),
        limit=10,
    )


def _context_detail_claims(
    claims: Sequence[SupportedClaim],
    grounding: PrivateAskFinGrounding,
) -> list[SupportedClaim]:
    kind = (
        grounding.context.object_type.casefold()
        if grounding.context is not None
        else ""
    )
    if kind == "finding":
        return _finding_detail_claims(claims, include_sources=False)
    if kind == "account":
        return _select(
            claims,
            (
                "account.identity",
                "account.variance",
                "account.budget",
                "account.ged_spend",
                "finding.what_happened",
                "finding.why_it_matters",
            ),
            limit=7,
        )
    if kind == "vendor":
        return _select(
            claims,
            ("vendor.summary", "vendor.transactions", "finding.transaction"),
            limit=5,
        )
    if kind == "transaction":
        return _select(
            claims,
            (
                "source.location",
                "source.account_number",
                "source.vendor_name",
                "source.journal_number",
                "source.amount",
            ),
            limit=6,
        )
    return _select(
        claims,
        (
            "review.summary_status",
            "review.summary_findings",
            "leadership.limitation.",
            "leadership.priority.",
        ),
        limit=5,
    )


def _resolved_context(
    grounding: PrivateAskFinGrounding,
    intent: AskFinIntent,
) -> AskFinContext | None:
    if grounding.context is not None:
        return AskFinContext(
            review_id=grounding.context.review_id,
            object_type=grounding.context.object_type,
            object_id=grounding.context.object_id,
            label=grounding.context.label,
            validation_run_id=grounding.validation_run_id,
        )
    preferred = {
        AskFinIntent.ACCOUNT: ("account",),
        AskFinIntent.VENDOR: ("vendor", "finding"),
        AskFinIntent.DEPARTMENT: ("department",),
        AskFinIntent.GED_TRANSACTION: ("finding", "transaction"),
        AskFinIntent.EVIDENCE: ("finding", "account", "transaction"),
        AskFinIntent.FINDINGS_SUMMARY: ("finding",),
        AskFinIntent.COMPARISON: ("run-comparison",),
        AskFinIntent.REVIEW_SUMMARY: ("review",),
    }.get(intent, ())
    for object_type in preferred:
        record = next(
            (
                item
                for item in grounding.records
                if item.object_type.casefold() == object_type
            ),
            None,
        )
        if record is not None:
            return _context_from_record(record, grounding.validation_run_id)
    return None


def _context_from_record(
    record: GroundedFinSightRecord,
    validation_run_id: str | None,
) -> AskFinContext:
    return AskFinContext(
        review_id=record.review_id,
        object_type=record.object_type,
        object_id=record.object_id,
        label=record.label,
        validation_run_id=validation_run_id,
    )


def _follow_up_questions(
    grounding: PrivateAskFinGrounding,
    intent: AskFinIntent,
) -> tuple[str, ...]:
    kind = (
        grounding.context.object_type.casefold()
        if grounding.context is not None
        else ""
    )
    if intent is AskFinIntent.ACCOUNT or kind == "account":
        return (
            "Show supporting evidence",
            "Show contributing vendors",
            "Show contributing transactions",
            "What should I inspect next?",
        )
    if intent is AskFinIntent.VENDOR or kind == "vendor":
        return (
            "Show contributing transactions",
            "Show supporting evidence",
            "Which accounts include this vendor?",
        )
    if intent in {AskFinIntent.FINDINGS_SUMMARY, AskFinIntent.GED_TRANSACTION} or (
        kind == "finding"
    ):
        return (
            "Show supporting evidence",
            "Why?",
            "What should I inspect next?",
        )
    if intent is AskFinIntent.EVIDENCE:
        return (
            "Tell me more about that",
            "Which vendor?",
            "What should I inspect next?",
        )
    if intent is AskFinIntent.REVIEW_SUMMARY:
        return (
            "Explain the highest-priority finding",
            "Why is the review incomplete?",
            "Show supporting evidence",
        )
    if intent is AskFinIntent.COMPARISON:
        return (
            "Show added findings",
            "Show removed findings",
            "Show changed findings",
        )
    return ()
