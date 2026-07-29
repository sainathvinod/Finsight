"""Privacy-safe, versioned failure contracts for application/UI boundaries.

Business validation outcomes are not represented here.  These envelopes cover
operational failures and denied lifecycle actions only, so every surfaced
FinSight workflow error has a stable code, impact, remedy, correlation reference, and
honest mutation outcome without leaking protected values or raw exception text.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional, Sequence


class MutationOutcome(str, Enum):
    NO_CHANGE = "No changes were made."
    COMMITTED = "The requested change was saved."
    UNKNOWN = "FinSight could not confirm whether state changed."


class Retryability(str, Enum):
    RETRY_AFTER_CORRECTION = "RETRY_AFTER_CORRECTION"
    RETRY_AFTER_AUTHORIZATION = "RETRY_AFTER_AUTHORIZATION"
    NOT_RETRYABLE = "NOT_RETRYABLE"
    SUPPORT_REQUIRED = "SUPPORT_REQUIRED"


@dataclass(frozen=True)
class ErrorEnvelope:
    code: str
    category: str
    correlation_id: str
    user_safe_cause: str
    user_safe_impact: str
    permitted_remedies: tuple[str, ...]
    retryability: Retryability
    mutation_outcome: MutationOutcome
    actor_reference: Optional[str] = None
    affected_operation_id: Optional[str] = None
    diagnostic_event_id: Optional[str] = None
    taxonomy_version: str = "1"

    def __post_init__(self) -> None:
        if not self.code.startswith("FS-") or not self.correlation_id:
            raise ValueError("A stable FinSight code and correlation ID are required.")
        if not self.user_safe_cause or not self.user_safe_impact:
            raise ValueError("A user-safe cause and impact are required.")
        if not self.permitted_remedies or not all(self.permitted_remedies):
            raise ValueError("At least one permitted remedy is required.")

    @classmethod
    def build(
        cls,
        *,
        code: str,
        category: str,
        correlation_id: str,
        cause: str,
        impact: str,
        remedies: Sequence[str],
        retryability: Retryability,
        mutation_outcome: MutationOutcome = MutationOutcome.NO_CHANGE,
        actor_reference: Optional[str] = None,
        affected_operation_id: Optional[str] = None,
        diagnostic_event_id: Optional[str] = None,
    ) -> "ErrorEnvelope":
        return cls(
            code=code,
            category=category,
            correlation_id=correlation_id,
            user_safe_cause=cause,
            user_safe_impact=impact,
            permitted_remedies=tuple(remedies),
            retryability=retryability,
            mutation_outcome=mutation_outcome,
            actor_reference=actor_reference,
            affected_operation_id=affected_operation_id,
            diagnostic_event_id=diagnostic_event_id,
        )

    def user_message(self) -> str:
        parts = [
            f"{self.code}: {self.user_safe_cause}",
            f"Impact: {self.user_safe_impact}",
            "Next step: " + " ".join(self.permitted_remedies),
            "State change: " + self.mutation_outcome.value,
        ]
        if self.actor_reference:
            parts.append("Account: " + self.actor_reference)
        parts.append("Correlation ID: " + self.correlation_id)
        return "\n".join(parts)


class CatalogedApplicationFailure(RuntimeError):
    """A failure safe for presentation at a delivery boundary."""

    def __init__(self, envelope: ErrorEnvelope):
        super().__init__(envelope.user_safe_cause)
        self.envelope = envelope

    def user_message(self) -> str:
        return self.envelope.user_message()


@dataclass(frozen=True)
class ErrorPresentation:
    """Business-first copy plus an optional troubleshooting disclosure.

    Stable codes, mutation state, and correlation identifiers remain available for
    support and audit, but they are deliberately excluded from the primary message.
    """

    primary: str
    technical_details: str = ""


def safe_failure_presentation(
    error: BaseException,
    *,
    fallback_correlation_id: str,
) -> ErrorPresentation:
    if isinstance(error, CatalogedApplicationFailure):
        envelope = error.envelope
    else:
        envelope = ErrorEnvelope.build(
            code="FS-SYS-001",
            category="Runtime",
            correlation_id=fallback_correlation_id,
            cause="FinSight could not complete the requested action.",
            impact="The requested FinSight action is unavailable.",
            remedies=(
                "Try the action once more. If it still does not work, contact FinSight support.",
            ),
            retryability=Retryability.SUPPORT_REQUIRED,
            mutation_outcome=MutationOutcome.UNKNOWN,
        )
    cause = envelope.user_safe_cause.rstrip(".")
    remedy = " ".join(envelope.permitted_remedies).strip()
    if remedy:
        primary = f"{cause}. {remedy}"
    else:  # pragma: no cover - ErrorEnvelope requires at least one remedy
        primary = cause + "."
    technical = "\n".join(
        (
            f"Error code: {envelope.code}",
            f"Category: {envelope.category}",
            f"Impact: {envelope.user_safe_impact}",
            f"State: {envelope.mutation_outcome.value}",
            f"Correlation ID: {envelope.correlation_id}",
        )
    )
    return ErrorPresentation(primary=primary, technical_details=technical)


def safe_failure_message(
    error: BaseException,
    *,
    fallback_correlation_id: str,
) -> str:
    """Render the plain-language primary UI message.

    Call :func:`safe_failure_presentation` when a troubleshooting disclosure is
    available. The legacy name is retained for delivery callers and tests.
    """

    return safe_failure_presentation(
        error,
        fallback_correlation_id=fallback_correlation_id,
    ).primary
