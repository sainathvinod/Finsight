"""Stage 2 contracts for the private, review-scoped Ask Fin experience.

These values deliberately carry identifiers and already-recorded FinSight facts.
They contain no financial calculation logic and no provider transport concerns.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Mapping, Optional, Tuple


PRIVATE_ASK_FIN_PROMPT_VERSION = "stage2-private-v6"


class AskFinMode(str, Enum):
    APPLICATION_HELP = "application_help"
    FINANCIAL_REVIEW = "financial_review"


class PrivateAskFinStatus(str, Enum):
    OK = "ok"
    UNAVAILABLE = "unavailable"
    UNANSWERABLE = "unanswerable"
    REFUSED = "refused"
    FAILED = "failed"


class LocalAiSetupState(str, Enum):
    """Plain-language startup/setup states for the local Ollama runtime."""

    NOT_INSTALLED = "not_installed"
    SERVICE_NOT_RUNNING = "service_not_running"
    MODEL_NOT_DOWNLOADED = "model_not_downloaded"
    MODEL_NOT_APPROVED = "model_not_approved"
    MODEL_VERIFICATION_FAILED = "model_verification_failed"
    CONNECTION_FAILURE = "connection_failure"
    TIMEOUT = "timeout"
    HEALTHY = "healthy"


@dataclass(frozen=True)
class LocalAiSetupStatus:
    """Bounded, non-sensitive setup information safe for desktop display."""

    state: LocalAiSetupState
    endpoint: str
    model: str
    message: str
    available_models: Tuple[str, ...] = ()
    observed_model_digest: str = ""

    @property
    def healthy(self) -> bool:
        return self.state is LocalAiSetupState.HEALTHY


@dataclass(frozen=True)
class AskFinContext:
    """An optional UI-selected FinSight object in one explicit review."""

    review_id: str
    object_type: str
    object_id: str
    label: str = ""
    validation_run_id: Optional[str] = None

    def __post_init__(self) -> None:
        if not self.review_id or not self.object_type or not self.object_id:
            raise ValueError("Ask Fin context requires review, object type, and object id.")


@dataclass(frozen=True)
class PrivateAskFinRequest:
    user_id: str
    review_id: str
    question: str
    context: Optional[AskFinContext] = None

    def __post_init__(self) -> None:
        if not self.user_id:
            raise ValueError("Ask Fin requires an authenticated user.")
        if not isinstance(self.question, str) or not self.question.strip():
            raise ValueError("Ask Fin requires a question.")


@dataclass(frozen=True)
class GroundedFinSightRecord:
    """One citable record retrieved from the authorized FinSight review."""

    citation_key: str
    review_id: str
    object_type: str
    object_id: str
    label: str
    facts: Mapping[str, Any]
    navigation_target: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class PrivateAskFinGrounding:
    mode: AskFinMode
    review_id: str
    reporting_period: str
    validation_run_id: Optional[str]
    rule_set_version: Optional[str]
    records: Tuple[GroundedFinSightRecord, ...]
    suggested_questions: Tuple[str, ...]
    context: Optional[AskFinContext] = None


@dataclass(frozen=True)
class PrivateCitation:
    """A verified, navigable FinSight citation."""

    key: str
    review_id: str
    object_type: str
    object_id: str
    label: str
    navigation_target: Mapping[str, Any] = field(default_factory=dict)
    evidence_details: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class PrivateAskFinSession:
    mode: AskFinMode
    greeting: str
    suggested_questions: Tuple[str, ...]
    review_id: str
    reporting_period: str = ""
    validation_run_id: Optional[str] = None
    scope_label: str = ""


@dataclass(frozen=True)
class PrivateAskFinResult:
    status: PrivateAskFinStatus
    mode: AskFinMode
    answer_text: str
    citations: Tuple[PrivateCitation, ...]
    review_id: str
    reporting_period: str = ""
    validation_run_id: Optional[str] = None
    refusal_trigger: Optional[str] = None
    failure_state: Optional[str] = None
    provider: str = "ollama"
    model: str = ""
    model_version: str = ""
    prompt_version: str = PRIVATE_ASK_FIN_PROMPT_VERSION
    latency_ms: Optional[int] = None
    retrieved_record_keys: Tuple[str, ...] = ()
    intent: str = ""
    resolved_context: Optional[AskFinContext] = None
    follow_up_questions: Tuple[str, ...] = ()
