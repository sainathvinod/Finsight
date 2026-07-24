# Implements: Phase 4C.5, FR-099 — AskFin orchestration contracts (data only; no I/O, no provider,
# no persistence, no logging). These describe the coordinator's request, its total result, the
# explicit stage/status enums, the authorization context, and the NON-SENSITIVE execution metadata.
from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Optional

from finsight.application.ai.contracts import AiAnswer


@dataclass(frozen=True)
class AskFinRequest:
    """Everything a caller supplies. Grounding, conversation-message contents, and review memory are
    NEVER supplied here — the coordinator retrieves them from the deterministic store. Only identifiers,
    the question, and optional per-call formatting overrides are accepted."""
    user_id: str
    cycle_id: str
    question: str
    conversation_id: Optional[str] = None
    audience: Optional[str] = None            # per-call override; else preference; else None
    answer_detail: Optional[str] = None       # per-call override; else preference; else None


class AskFinStatus(str, Enum):
    OK = "ok"                    # validated substantive AiAnswer from an active provider
    DEGRADED = "degraded"        # validated NullProvider/fallback refusal AiAnswer
    UNANSWERABLE = "unanswerable"  # validated refusal AiAnswer from an active provider
    FAILED = "failed"            # NO AiAnswer — technical pipeline failure
    REFUSED = "refused"          # NO AiAnswer — authorization or scope rejection


class AskFinStage(str, Enum):
    """Explicit, ordered pipeline stages (no free-form stage strings). last_stage records how far a
    request progressed — a non-sensitive label only."""
    AUTHORIZATION = "authorization"
    SCOPE = "scope"
    GROUNDING = "grounding"
    CONTEXT_RETRIEVAL = "context_retrieval"
    PREFERENCES = "preferences"
    MASKING = "masking"
    PROMPT_BUILD = "prompt_build"
    PROVIDER = "provider"
    VALIDATION = "validation"
    CITATION = "citation"
    ASSEMBLY = "assembly"
    PERSISTENCE = "persistence"
    JOURNAL = "journal"
    COMPLETE = "complete"


@dataclass(frozen=True)
class AiAuthorizationContext:
    """Immutable authorization inputs the AiAuthorizationPolicy evaluates. Provider availability is NOT
    part of authorization; NullProvider does not bypass it. `application_mode` must be explanation-only /
    non-mutating — the policy can never authorize deterministic-workflow mutation."""
    user_id: str
    cycle_id: str
    application_mode: str
    ai_capability_available: bool
    user_consent: bool


@dataclass(frozen=True)
class AiExecutionMetadata:
    """NON-SENSITIVE execution metadata for the result and the interaction journal. Contains NO
    question, prompt, answer text, raw provider output, masked values, original values, or copied
    evidence — counts and identifiers/labels only."""
    provider: Optional[str] = None
    model: Optional[str] = None
    schema_version: Optional[str] = None
    prompt_version: Optional[str] = None
    masking_policy_version: Optional[str] = None
    citation_format_version: Optional[str] = None
    grounding_confidence: Optional[str] = None
    citation_count: int = 0
    citation_namespace_counts: Dict[str, int] = field(default_factory=dict)
    masking_counts: Dict[str, int] = field(default_factory=dict)
    truncation_counts: Dict[str, int] = field(default_factory=dict)
    provider_attempts: int = 0
    validation_retries: int = 0
    timeout_retries: int = 0
    error_code: Optional[str] = None
    last_stage: Optional[str] = None
    elapsed_ms: Optional[int] = None
    journal_recorded: bool = True

    def as_journal_metadata(self) -> Dict[str, object]:
        """Flat, JSON-serializable, non-content metadata for AiInteractionEntry.metadata."""
        return {
            "provider": self.provider,
            "model": self.model,
            "schema_version": self.schema_version,
            "prompt_version": self.prompt_version,
            "masking_policy_version": self.masking_policy_version,
            "citation_format_version": self.citation_format_version,
            "grounding_confidence": self.grounding_confidence,
            "citation_count": self.citation_count,
            "citation_namespace_counts": dict(self.citation_namespace_counts),
            "masking_counts": dict(self.masking_counts),
            "truncation_counts": dict(self.truncation_counts),
            "provider_attempts": self.provider_attempts,
            "validation_retries": self.validation_retries,
            "timeout_retries": self.timeout_retries,
            "error_code": self.error_code,
            "last_stage": self.last_stage,
            "elapsed_ms": self.elapsed_ms,
        }


@dataclass(frozen=True)
class AskFinResult:
    """Total, immutable outcome. `answer` is present ONLY for validated + citation-verified provider
    output (OK / DEGRADED / UNANSWERABLE); it is None for FAILED and REFUSED — a technical failure is
    never dressed up as a valid AI refusal."""
    status: AskFinStatus
    answer: Optional[AiAnswer]
    error_code: Optional[str]
    last_stage: AskFinStage
    metadata: AiExecutionMetadata
