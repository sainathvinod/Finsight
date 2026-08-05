"""Closed, deterministic claim catalog for private Ask Fin.

The local model may select and assemble only these application-authored claim
templates.  Workbook prose and arbitrary provider assertions never become
supported merely because they carry a valid citation.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
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
            claim_id = (
                "claim:" + hashlib.sha256(identity.encode("utf-8")).hexdigest()[:24]
            )
            claims.setdefault(
                (record.citation_key, normalized),
                SupportedClaim(
                    claim_id=claim_id,
                    citation_key=record.citation_key,
                    predicate=predicate,
                    text=_SPACE.sub(" ", text).strip().rstrip(".!?"),
                ),
            )
    # Insertion order preserves the deterministic order of sealed records and
    # their recorded lists (for example, a finding's contributing vendors).
    # Claim IDs remain content-stable and are not used to scramble business
    # relevance.
    return tuple(claims.values())


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
    elif kind == "leadership-summary":
        output.extend(_leadership_summary_claims(facts))
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
    account_name = _text(facts, "account_name")
    if account_name:
        output.append(
            (
                "account.identity",
                f"Account: {account} — {account_name}",
            )
        )
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
    overrun_cents = facts.get("over_budget_amount_cents")
    has_overrun = (
        isinstance(overrun_cents, int)
        and not isinstance(overrun_cents, bool)
        and overrun_cents > 0
    )
    if bgt:
        output.append(("account.budget", f"Budget: {bgt}"))
        output.append(("account.bgt", f"Account {account} has a recorded BGT of {bgt}"))
    if actual:
        output.append(("account.ged_spend", f"GED spend: {actual}"))
        output.append(
            (
                "account.actual",
                f"Account {account} has recorded GED spend of {actual}",
            )
        )
    if overrun and has_overrun:
        output.append(
            (
                "account.variance",
                f"Unfavorable variance: {overrun} over budget",
            )
        )
        output.append(
            (
                "account.over_budget",
                f"Account {account} is {overrun} over budget",
            )
        )
    if bgt and actual and overrun and has_overrun:
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
                "account.transactions",
                f"Contributing GED transactions: {transaction_count}",
            )
        )
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
    vendors = facts.get("vendors")
    if isinstance(vendors, (list, tuple)):
        for vendor in vendors:
            name = str(vendor or "").strip()
            if name:
                output.append(
                    (
                        "account.contributing_vendor",
                        f"Contributing vendor: {name}",
                    )
                )
                output.append(
                    (
                        "account.vendor",
                        (
                            f"Account {account} has recorded GED activity "
                            f"from vendor {name}"
                        ),
                    )
                )
    return output


def _review_claims(facts: Mapping[str, Any]) -> list[tuple[str, str]]:
    output: list[tuple[str, str]] = []
    period = _text(facts, "reporting_period")
    if period:
        output.append(
            (
                "review.summary_intro",
                f"Here’s a summary of your {period} review",
            )
        )
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
    for key, predicate, label in (
        ("overall_status", "review.summary_status", "Overall Status"),
        ("budget", "review.summary_budget", "Budget"),
        ("actual_ged", "review.summary_actual", "Actual recorded spend"),
        ("eac", "review.summary_eac", "Estimated at Completion (EAC)"),
        ("data_quality", "review.summary_data_quality", "Data Quality"),
        (
            "reconciliation_status",
            "review.summary_reconciliation",
            "Reconciliation Status",
        ),
    ):
        value = _text(facts, key)
        if value:
            output.append((predicate, f"{label}: {value}"))
    findings = _count(facts, "findings")
    if findings:
        output.append(
            (
                "review.summary_findings",
                f"Findings requiring attention: {findings}",
            )
        )
        output.append(
            (
                "review.finding_count",
                f"This review has {findings} recorded findings",
            )
        )
    severity_rows = facts.get("findings_by_severity")
    if isinstance(severity_rows, (list, tuple)):
        for item in severity_rows:
            if not isinstance(item, Mapping):
                continue
            severity = str(item.get("severity") or "").strip()
            count = item.get("count")
            if (
                severity
                and isinstance(count, int)
                and not isinstance(count, bool)
                and count
            ):
                output.append(
                    (
                        "review.summary_severity",
                        f"Findings by severity: {count} {severity}",
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
                "vendor.summary",
                f"Vendor {vendor}: {amount} in GED spend",
            )
        )
        output.append(
            (
                "vendor.actual",
                f"Vendor {vendor} has recorded GED spend of {amount}",
            )
        )
    if vendor and count:
        output.append(
            (
                "vendor.transactions",
                f"GED transactions for {vendor}: {count}",
            )
        )
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
        output = [
            (
                "department.identity",
                f"Department: {number} — {name}",
            )
        ]
        account_count = _count(facts, "account_count")
        if account_count:
            output.append(
                (
                    "department.account_count",
                    f"Accounts in this department view: {account_count}",
                )
            )
        return output
    return []


def _leadership_summary_claims(
    facts: Mapping[str, Any],
) -> list[tuple[str, str]]:
    """Closed claims from the persisted deterministic leadership summary."""

    output: list[tuple[str, str]] = []
    overall = _text(facts, "overall_status")
    if overall:
        output.append(
            (
                "leadership.overall_status",
                f"The recorded overall review status is {overall}",
            )
        )
    budget_health = _text(facts, "budget_health")
    if budget_health:
        output.append(
            (
                "leadership.budget_health",
                f"The recorded Budget Health is {budget_health}",
            )
        )

    financial = facts.get("financial_position")
    if isinstance(financial, Mapping):
        for key, predicate, label in (
            ("budget", "leadership.budget", "Budget"),
            ("actual_spend", "leadership.actual", "Actual Spend"),
            ("eac", "leadership.eac", "EAC"),
            ("variance", "leadership.variance", "Variance"),
        ):
            value = _text(financial, key)
            if value:
                output.append(
                    (
                        predicate,
                        f"The recorded leadership-summary {label} is {value}",
                    )
                )

    ged_status = facts.get("ged_status")
    if isinstance(ged_status, Mapping):
        for key, predicate, label in (
            ("data_quality", "leadership.data_quality", "Data Quality"),
            (
                "reconciliation",
                "leadership.reconciliation",
                "Reconciliation Status",
            ),
        ):
            value = _text(ged_status, key)
            if value:
                output.append(
                    (
                        predicate,
                        f"The recorded {label} is {value}",
                    )
                )
        for key, predicate, label in (
            (
                "transaction_count",
                "leadership.transaction_count",
                "GED transactions",
            ),
            (
                "missing_required_data",
                "leadership.missing_required_data",
                "missing required-data findings",
            ),
            (
                "duplicate_transactions",
                "leadership.duplicate_transactions",
                "duplicate-transaction findings",
            ),
        ):
            value = ged_status.get(key)
            if isinstance(value, int) and not isinstance(value, bool):
                if key == "missing_required_data" and value:
                    output.append(
                        (
                            "leadership.data_issue",
                            (
                                f"Data issue: {value} required GED value"
                                f"{' is' if value == 1 else 's are'} missing or invalid"
                            ),
                        )
                    )
                output.append(
                    (
                        predicate,
                        f"The recorded review has {value} {label}",
                    )
                )

    priorities = facts.get("highest_priority_findings")
    if isinstance(priorities, (list, tuple)):
        for index, item in enumerate(priorities[:5], start=1):
            if not isinstance(item, Mapping):
                continue
            title = _text(item, "title")
            severity = _text(item, "severity")
            account = _text(item, "account_number")
            happened = _text(item, "what_happened")
            if title:
                suffix = f" ({severity})" if severity else ""
                account_suffix = f" for Account {account}" if account else ""
                output.append(
                    (
                        f"leadership.priority.{index}",
                        (f"A recorded priority is {title}{suffix}{account_suffix}"),
                    )
                )
            if happened:
                output.append(
                    (
                        f"leadership.priority_explanation.{index}",
                        happened,
                    )
                )

    next_steps = facts.get("recommended_next_steps")
    if isinstance(next_steps, (list, tuple)):
        for index, value in enumerate(next_steps[:5], start=1):
            if isinstance(value, str) and value.strip():
                output.append(
                    (
                        f"leadership.next_step.{index}",
                        (f"The recorded non-binding review step is {value.strip()}"),
                    )
                )
    limitations = facts.get("data_quality_limitations")
    if isinstance(limitations, (list, tuple)):
        for index, value in enumerate(limitations[:5], start=1):
            if isinstance(value, str) and value.strip():
                output.append(
                    (
                        f"leadership.limitation.{index}",
                        value.strip(),
                    )
                )
    return output


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
        (
            "recommended_action",
            f"{kind}.recommended_action",
            "The recorded non-binding review action is ",
        ),
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
    title = _text(facts, "business_title") or _text(facts, "rule_name")
    if title:
        output.append(
            (
                f"{kind}.title",
                f"The recorded finding is {title}",
            )
        )
        output.append((f"{kind}.business_title", f"Finding: {title}"))
    department_number = _text(facts, "department_number")
    department_name = _text(facts, "department_name")
    if department_number:
        output.append(
            (
                f"{kind}.department_number",
                f"Department Number: {department_number}",
            )
        )
    if department_name:
        output.append(
            (
                f"{kind}.department_name",
                f"Department Name: {department_name}",
            )
        )

    explanation = facts.get("explain_this")
    if isinstance(explanation, Mapping):
        for key, predicate, label in (
            ("what_happened", f"{kind}.what_happened", "What happened"),
            (
                "why_flagged",
                f"{kind}.why_flagged",
                "Why FinSight flagged it",
            ),
            ("why_it_matters", f"{kind}.why_it_matters", "Why it matters"),
            (
                "recommended_next_step",
                f"{kind}.next_step",
                "What to inspect next",
            ),
        ):
            value = _text(explanation, key)
            for sentence in _sentences(value):
                output.append((predicate, f"{label}: {sentence}"))

        preferred_vendors: tuple[str, ...] = ()
        supporting = explanation.get("supporting_evidence")
        if isinstance(supporting, Mapping):
            for key, predicate, label in (
                ("account_number", f"{kind}.account_number", "Account"),
                ("account_name", f"{kind}.account_name", "Account name"),
                ("budget", f"{kind}.budget", "Budget"),
                ("ged_actual", f"{kind}.actual_spend", "GED spend"),
                ("variance", f"{kind}.variance", "Unfavorable variance"),
                (
                    "variance_percentage",
                    f"{kind}.variance_percentage",
                    "Variance percentage",
                ),
                ("expected", f"{kind}.expected_detail", "Expected"),
                ("actual", f"{kind}.actual_detail", "Actual"),
                ("threshold", f"{kind}.threshold", "Rule threshold"),
            ):
                value = _text(supporting, key)
                if value and value != "Unavailable":
                    output.append((predicate, f"{label}: {value}"))
            vendors = supporting.get("vendors")
            if isinstance(vendors, (list, tuple)):
                preferred_vendors = tuple(
                    str(vendor or "").strip()
                    for vendor in vendors
                    if str(vendor or "").strip()
                )
                for vendor in vendors:
                    name = str(vendor or "").strip()
                    if name:
                        output.append(
                            (
                                f"{kind}.contributing_vendor",
                                f"Contributing vendor: {name}",
                            )
                        )
            lineage = supporting.get("lineage")
            if isinstance(lineage, (list, tuple)):
                for item in lineage:
                    if not isinstance(item, Mapping):
                        continue
                    label = _lineage_label(item)
                    if label:
                        output.append((f"{kind}.source_location", label))

        transactions = explanation.get("contributing_transactions")
        if isinstance(transactions, (list, tuple)):
            recorded_largest = facts.get("recorded_largest_transactions")
            if isinstance(recorded_largest, (list, tuple)):
                for item in recorded_largest[:3]:
                    if not isinstance(item, Mapping):
                        continue
                    detail = _transaction_label(item)
                    if detail:
                        output.append(
                            (
                                f"{kind}.key_transaction",
                                f"Key contributing {detail}",
                            )
                        )
            # Preserve the sealed Rule Engine order and include one example
            # for each recorded contributing vendor before filling remaining
            # slots. This is evidence coverage, not a spend/materiality rank.
            selected_transactions: list[Mapping[str, Any]] = []
            for vendor in preferred_vendors:
                matching = next(
                    (
                        item
                        for item in transactions
                        if isinstance(item, Mapping)
                        and str(item.get("vendor") or "").strip() == vendor
                    ),
                    None,
                )
                if matching is not None and matching not in selected_transactions:
                    selected_transactions.append(matching)
                if len(selected_transactions) == 3:
                    break
            for item in transactions:
                if not isinstance(item, Mapping):
                    continue
                if item not in selected_transactions:
                    selected_transactions.append(item)
                if len(selected_transactions) == 3:
                    break
            for item in selected_transactions:
                if not isinstance(item, Mapping):
                    continue
                detail = _transaction_label(item)
                if detail:
                    output.append(
                        (
                            f"{kind}.contributing_transaction",
                            f"Contributing {detail}",
                        )
                    )
            rows = [
                item.get("source_row")
                for item in transactions
                if isinstance(item, Mapping)
                and isinstance(item.get("source_row"), int)
                and not isinstance(item.get("source_row"), bool)
            ]
            row_summary = _row_summary(rows)
            if row_summary:
                output.append(
                    (
                        f"{kind}.source_rows",
                        f"Contributing GED source rows: {row_summary}",
                    )
                )
            for item in transactions[:5]:
                if not isinstance(item, Mapping):
                    continue
                detail = _transaction_label(item)
                if detail:
                    output.append((f"{kind}.transaction", detail))

        technical = explanation.get("technical_details")
        if isinstance(technical, Mapping):
            rule_id = _text(technical, "rule_id")
            rule_name = _text(technical, "rule_name")
            rule_version = _text(technical, "rule_version")
            if rule_name:
                identity = (
                    f"{rule_id} — {rule_name}" if rule_id else rule_name
                )
                value = (
                    f"{identity}, version {rule_version}"
                    if rule_version
                    else identity
                )
                output.append((f"{kind}.rule", f"Rule: {value}"))
            validation_run = _text(technical, "validation_run_id")
            if validation_run:
                output.append(
                    (
                        f"{kind}.validation_run",
                        f"Validation run: {validation_run}",
                    )
                )
    return output


def _sentences(value: str) -> tuple[str, ...]:
    if not value:
        return ()
    return tuple(
        item.strip().rstrip(".")
        for item in re.split(r"(?<=[.!?])\s+", value.strip())
        if item.strip()
    )


def _lineage_label(item: Mapping[str, Any]) -> str:
    role = str(item.get("source_role") or "Source").strip()
    file_name = str(
        item.get("source_file") or item.get("workbook") or ""
    ).strip()
    worksheet = str(item.get("worksheet") or item.get("sheet") or "").strip()
    row = item.get("row", item.get("source_row"))
    cell = str(item.get("cell") or "").strip()
    field = str(item.get("field") or item.get("field_name") or "").strip()
    parts = [f"{role} evidence"]
    if file_name:
        parts.append(file_name)
    if worksheet:
        parts.append(f"worksheet {worksheet}")
    if row not in (None, ""):
        parts.append(f"row {row}")
    if cell:
        parts.append(f"cell {cell}")
    elif field:
        parts.append(f"field {field}")
    return "Source location: " + ", ".join(parts)


def _row_summary(values: Sequence[Any]) -> str:
    rows = sorted(
        {
            int(value)
            for value in values
            if isinstance(value, int) and not isinstance(value, bool)
        }
    )
    if not rows:
        return ""
    groups: list[str] = []
    start = previous = rows[0]
    for row in rows[1:]:
        if row == previous + 1:
            previous = row
            continue
        groups.append(str(start) if start == previous else f"{start}–{previous}")
        start = previous = row
    groups.append(str(start) if start == previous else f"{start}–{previous}")
    return ", ".join(groups)


def _transaction_label(item: Mapping[str, Any]) -> str:
    row = item.get("source_row")
    if row in (None, ""):
        return ""
    vendor = str(
        item.get("vendor")
        or item.get("vendor_name")
        or "No vendor recorded"
    ).strip()
    reference = str(
        item.get("journal_or_invoice_reference")
        or item.get("journal_number")
        or "No reference recorded"
    ).strip()
    amount = str(item.get("amount_label") or "Unavailable").strip()
    return (
        f"GED source row {row}: Vendor {vendor}; "
        f"Reference {reference}; Amount {amount}"
    )


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
    output: list[tuple[str, str]] = [
        (
            "source.row",
            f"{role} source evidence includes row {row}",
        )
    ]
    source_file = _text(facts, "source_file")
    worksheet = _text(facts, "worksheet")
    cells = facts.get("cells")
    primary_field = "amount" if role == "GED" else "bgt"
    cell = (
        str(cells.get(primary_field) or "").strip()
        if isinstance(cells, Mapping)
        else ""
    )
    location_parts = [
        source_file,
        f"worksheet {worksheet}" if worksheet else "",
        f"row {row}",
        f"cell {cell}" if cell else "",
    ]
    output.append(
        (
            "source.location",
            f"{role} evidence: "
            + ", ".join(item for item in location_parts if item),
        )
    )
    source_fields = (
        ("department_number", "Department Number"),
        ("account_number", "Account Number"),
        ("account_name", "Account Name"),
        ("fiscal_period", "Fiscal Period"),
        ("journal_number", "Journal Number"),
        ("journal_date", "Journal Date"),
        ("vendor_name", "Vendor"),
        ("invoice_amt", "Invoice Amount"),
        ("amount", "Amount"),
        ("bgt", "BGT"),
        ("atd", "ATD"),
        ("etc", "ETC"),
        ("eac", "EAC"),
        ("delta", "DELTA"),
    )
    for key, label in source_fields:
        value = fields.get(key)
        if value not in (None, ""):
            display_value = _source_display_value(key, value)
            output.append(
                (
                    f"source.{key}",
                    (
                        f"{role} source row {row} has recorded "
                        f"{label} {display_value}"
                    ),
                )
            )
    return output


def _source_display_value(field: str, value: Any) -> str:
    if field not in {
        "invoice_amt",
        "amount",
        "bgt",
        "atd",
        "etc",
        "eac",
        "delta",
    }:
        return str(value)
    try:
        return f"${Decimal(str(value)):,.2f}"
    except (InvalidOperation, ValueError):
        return str(value)


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
