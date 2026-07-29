"""Closed, deterministic claim catalog for private Ask Fin.

The local model may select and assemble only these application-authored claim
templates.  Workbook prose and arbitrary provider assertions never become
supported merely because they carry a valid citation.
"""
from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from typing import Any, Mapping, Sequence

from finsight.application.ai.private_contracts import GroundedFinSightRecord


_SPACE = re.compile(r"\s+")


@dataclass(frozen=True)
class SupportedClaim:
    claim_id: str
    citation_key: str
    predicate: str
    text: str


def normalized_claim_text(value: str) -> str:
    """Canonical comparison form; it never repairs or paraphrases content."""

    return _SPACE.sub(" ", value).strip().rstrip(".!?").strip()


def build_supported_claims(
    records: Sequence[GroundedFinSightRecord],
) -> tuple[SupportedClaim, ...]:
    claims: dict[tuple[str, str], SupportedClaim] = {}
    for record in records:
        for predicate, text in _record_claims(record):
            normalized = normalized_claim_text(text)
            if not normalized:
                continue
            identity = f"{record.citation_key}|{predicate}|{normalized}"
            claim_id = "claim:" + hashlib.sha256(
                identity.encode("utf-8")
            ).hexdigest()[:24]
            claims.setdefault(
                (record.citation_key, normalized),
                SupportedClaim(
                    claim_id=claim_id,
                    citation_key=record.citation_key,
                    predicate=predicate,
                    text=_SPACE.sub(" ", text).strip().rstrip(".!?"),
                ),
            )
    return tuple(
        sorted(
            claims.values(),
            key=lambda item: (item.citation_key, item.predicate, item.claim_id),
        )
    )


def supported_claim_for_sentence(
    sentence: str,
    citation_keys: Sequence[str],
    claims: Sequence[SupportedClaim],
) -> SupportedClaim | None:
    """Return the unique exact template selected by one cited sentence."""

    if len(citation_keys) != 1:
        return None
    normalized = normalized_claim_text(sentence)
    matches = [
        item
        for item in claims
        if item.citation_key in citation_keys
        and normalized_claim_text(item.text) == normalized
    ]
    if len(matches) != 1:
        return None
    return matches[0]


def _record_claims(
    record: GroundedFinSightRecord,
) -> tuple[tuple[str, str], ...]:
    facts = record.facts
    kind = record.object_type.casefold()
    output: list[tuple[str, str]] = []
    if kind == "account":
        output.extend(_account_claims(facts))
    elif kind == "review":
        output.extend(_review_claims(facts))
    elif kind == "vendor":
        output.extend(_vendor_claims(facts))
    elif kind == "department":
        output.extend(_department_claims(facts))
    elif kind in {"finding", "rule-result"}:
        output.extend(_result_claims(kind, record.object_id, facts))
    elif kind in {"transaction", "budget-source"}:
        output.extend(_source_claims(kind, facts))
    elif kind == "help":
        output.extend(_help_claims(record.object_id, facts))
    elif kind == "run-comparison":
        output.extend(_comparison_claims(facts))
    return tuple(output)


def _text(facts: Mapping[str, Any], key: str) -> str:
    value = facts.get(key)
    return value.strip() if isinstance(value, str) else ""


def _count(facts: Mapping[str, Any], key: str) -> str:
    value = facts.get(key)
    if isinstance(value, int) and not isinstance(value, bool):
        return str(value)
    return ""


def _account_claims(facts: Mapping[str, Any]) -> list[tuple[str, str]]:
    account = _text(facts, "account_number")
    if not account:
        return []
    output: list[tuple[str, str]] = []
    labels = (
        ("bgt_label", "account.bgt", "BGT"),
        ("summed_ged_amount_label", "account.actual", "GED spend"),
        ("atd_label", "account.atd", "ATD"),
        ("etc_label", "account.etc", "ETC"),
        ("eac_label", "account.eac", "EAC"),
        ("delta_label", "account.delta", "Delta"),
        (
            "actual_variance_label",
            "account.actual_variance",
            "Actual variance",
        ),
        (
            "budget_utilization_label",
            "account.budget_utilization",
            "Budget utilization",
        ),
    )
    for key, predicate, label in labels:
        value = _text(facts, key)
        if value:
            output.append(
                (predicate, f"Account {account} has recorded {label} of {value}")
            )
    bgt = _text(facts, "bgt_label")
    actual = _text(facts, "summed_ged_amount_label")
    overrun = _text(facts, "over_budget_amount_label")
    if bgt:
        output.append(
            ("account.bgt", f"Account {account} has a recorded BGT of {bgt}")
        )
    if actual:
        output.append(
            (
                "account.actual",
                f"Account {account} has recorded GED spend of {actual}",
            )
        )
    if overrun:
        output.append(
            (
                "account.over_budget",
                f"Account {account} is {overrun} over budget",
            )
        )
    if bgt and actual and overrun:
        output.append(
            (
                "account.actual_against_bgt",
                (
                    f"Account {account} has recorded GED spend of {actual} "
                    f"against BGT of {bgt}, an unfavorable {overrun} variance"
                ),
            )
        )
    transaction_count = _count(facts, "ged_transaction_count")
    if transaction_count:
        output.append(
            (
                "account.transaction_count",
                (
                    f"Account {account} has {transaction_count} recorded "
                    "GED transactions"
                ),
            )
        )
    finding_count = _count(facts, "finding_count")
    if finding_count:
        output.append(
            (
                "account.finding_count",
                f"Account {account} has {finding_count} recorded findings",
            )
        )
    return output


def _review_claims(facts: Mapping[str, Any]) -> list[tuple[str, str]]:
    output: list[tuple[str, str]] = []
    labels = (
        ("reporting_period", "review.period", "reporting period"),
        ("department_number", "review.department_number", "Department Number"),
        ("department_name", "review.department_name", "Department Name"),
        ("overall_status", "review.overall_status", "overall review status"),
        ("budget_health", "review.budget_health", "Budget Health"),
        ("data_quality", "review.data_quality", "Data Quality"),
        (
            "reconciliation_status",
            "review.reconciliation_status",
            "Reconciliation Status",
        ),
        ("budget", "review.bgt", "Budget"),
        ("actual_ged", "review.actual", "GED Actual"),
        ("atd", "review.atd", "ATD"),
        ("etc", "review.etc", "ETC"),
        ("eac", "review.eac", "EAC"),
        ("delta", "review.delta", "Delta"),
    )
    for key, predicate, label in labels:
        value = _text(facts, key)
        if value:
            output.append((predicate, f"The recorded {label} is {value}"))
    findings = _count(facts, "findings")
    if findings:
        output.append(
            (
                "review.finding_count",
                f"This review has {findings} recorded findings",
            )
        )
    return output


def _vendor_claims(facts: Mapping[str, Any]) -> list[tuple[str, str]]:
    vendor = _text(facts, "vendor_name")
    amount = _text(facts, "amount_label")
    count = _count(facts, "transaction_count")
    output: list[tuple[str, str]] = []
    if vendor and amount:
        output.append(
            (
                "vendor.actual",
                f"Vendor {vendor} has recorded GED spend of {amount}",
            )
        )
    if vendor and count:
        output.append(
            (
                "vendor.transaction_count",
                f"Vendor {vendor} has {count} recorded GED transactions",
            )
        )
    return output


def _department_claims(facts: Mapping[str, Any]) -> list[tuple[str, str]]:
    number = _text(facts, "department_number")
    name = _text(facts, "department_name")
    if number and name:
        return [
            (
                "department.identity",
                f"Department {number} is recorded as {name}",
            )
        ]
    return []


def _result_claims(
    kind: str,
    object_id: str,
    facts: Mapping[str, Any],
) -> list[tuple[str, str]]:
    output: list[tuple[str, str]] = []
    for key, predicate, prefix in (
        ("explanation", f"{kind}.explanation", ""),
        ("expected", f"{kind}.expected", "The recorded expected result is "),
        ("actual", f"{kind}.actual", "The recorded actual result is "),
    ):
        value = _text(facts, key)
        if value:
            output.append((predicate, prefix + value))
    severity = _text(facts, "severity")
    if severity:
        output.append(
            (
                f"{kind}.severity",
                f"The recorded severity for {object_id} is {severity}",
            )
        )
    status = _text(facts, "status")
    if status:
        output.append(
            (
                f"{kind}.status",
                f"The recorded status for {object_id} is {status}",
            )
        )
    return output


def _source_claims(
    kind: str,
    facts: Mapping[str, Any],
) -> list[tuple[str, str]]:
    row = facts.get("source_row")
    fields = facts.get("fields")
    if (
        not isinstance(row, int)
        or isinstance(row, bool)
        or not isinstance(fields, Mapping)
    ):
        return []
    role = "GED" if kind == "transaction" else "Budget"
    output: list[tuple[str, str]] = []
    source_fields = (
        ("department_number", "Department Number"),
        ("account_number", "Account Number"),
        ("fiscal_period", "Fiscal Period"),
        ("journal_number", "Journal Number"),
        ("journal_date", "Journal Date"),
        ("invoice_amt", "Invoice Amount"),
        ("amount", "Amount"),
    )
    for key, label in source_fields:
        value = fields.get(key)
        if value not in (None, ""):
            output.append(
                (
                    f"source.{key}",
                    f"{role} source row {row} has recorded {label} {value}",
                )
            )
    return output


def _help_claims(
    object_id: str,
    facts: Mapping[str, Any],
) -> list[tuple[str, str]]:
    output: list[tuple[str, str]] = []
    if object_id == "review-workflow":
        output.extend(
            (
                (
                    "help.create_review",
                    "Create a review before uploading the two reports",
                ),
                (
                    "help.create_review.concise",
                    "Create a review before uploading reports",
                ),
            )
        )
    steps = facts.get("steps")
    if isinstance(steps, list):
        for step in steps:
            if isinstance(step, str) and step.strip():
                output.append(
                    ("help.workflow_step", f"FinSight workflow step: {step.strip()}")
                )
    if object_id == "supported-files":
        output.append(
            (
                "help.supported_files",
                "FinSight supports one Budget Report and one GED Report",
            )
        )
    if object_id == "privacy":
        output.append(
            (
                "help.private_inference",
                "Ask Fin uses only the approved local Ollama runtime",
            )
        )
        output.append(
            (
                "help.no_external_retrieval",
                "Ask Fin does not use internet retrieval",
            )
        )
    return output


def _comparison_claims(
    facts: Mapping[str, Any],
) -> list[tuple[str, str]]:
    output: list[tuple[str, str]] = []
    for key in ("added_count", "removed_count", "changed_count"):
        value = facts.get(key)
        if isinstance(value, int) and not isinstance(value, bool):
            label = key.removesuffix("_count").replace("_", " ")
            output.append(
                (
                    f"comparison.{key}",
                    f"The run comparison has {value} {label} findings",
                )
            )
    return output
