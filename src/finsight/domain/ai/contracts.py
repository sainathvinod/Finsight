# Framework-independent AI value types (persistence records + structured grounding facts).
# Immutable data only. No PySide6, no sqlite3, no financial logic.
from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple


class MessageRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"     # stored content supplied by a future caller; never generated here


class MemoryType(str, Enum):
    HUMAN_AUTHORED = "human_authored"
    SYSTEM_DERIVED = "system_derived"     # must reference a deterministic source; never model-authored


class InteractionEvent(str, Enum):
    # Phase 4B: lifecycle events only (no provider interaction exists yet).
    CONVERSATION_CREATED = "conversation_created"
    CONVERSATION_RENAMED = "conversation_renamed"
    CONVERSATION_DELETED = "conversation_deleted"
    CONVERSATION_CLEARED = "conversation_cleared"
    MEMORY_CREATED = "memory_created"
    MEMORY_DELETED = "memory_deleted"
    MEMORY_FORGOTTEN = "memory_forgotten"
    PREFERENCES_CHANGED = "preferences_changed"


# --- persistence value types ---
@dataclass(frozen=True)
class Conversation:
    conversation_id: str
    user_id: str
    cycle_id: str
    title: str
    created_ts: str
    updated_ts: str
    retention_policy: str


@dataclass(frozen=True)
class ConversationMessage:
    message_id: str
    conversation_id: str
    role: MessageRole
    content: str
    seq: int
    created_ts: str


@dataclass(frozen=True)
class ReviewMemoryEntry:
    memory_id: str
    user_id: str
    cycle_id: str
    memory_type: MemoryType
    content: str
    actor: str
    created_ts: str
    updated_ts: str
    source_type: Optional[str] = None    # required for SYSTEM_DERIVED
    source_id: Optional[str] = None      # required for SYSTEM_DERIVED


@dataclass(frozen=True)
class UserPreference:
    user_id: str
    key: str
    value: str          # documented serialization: JSON-encoded scalar (see PreferencesService)
    updated_ts: str


@dataclass(frozen=True)
class AiInteractionEntry:
    interaction_id: str
    user_id: Optional[str]
    cycle_id: Optional[str]
    conversation_id: Optional[str]
    event_type: InteractionEvent
    status: str
    metadata: Dict[str, object]     # approved non-sensitive metadata only
    created_ts: str


# --- structured grounding facts (immutable; NOT presentation strings) ---
@dataclass(frozen=True)
class GroundedReview:
    cycle_id: str
    month: str
    year: str
    state: str
    finding_count: int


@dataclass(frozen=True)
class GroundedFinding:
    id: str
    account: str
    rule_id: str
    severity: str
    finding_type: str
    period: str
    evidence: Dict[str, str]
    source_refs: List[str]
    state: str


@dataclass(frozen=True)
class GroundedSummary:
    status_label: str
    finding_count: int


@dataclass(frozen=True)
class GroundedRuleRun:
    run_id: str
    ruleset_version: str
    config_version: str
    input_fingerprint: str
    finding_count: int


@dataclass(frozen=True)
class GroundedProvenanceItem:
    doc_type: str
    name: str
    fingerprint: str
    period: str


@dataclass(frozen=True)
class GroundedAuditEvent:
    action: str
    actor: str
    ts: str


@dataclass(frozen=True)
class AiGroundingContext:
    review: Optional[GroundedReview]
    findings: List[GroundedFinding] = field(default_factory=list)
    summary: Optional[GroundedSummary] = None
    rule_run: Optional[GroundedRuleRun] = None
    provenance: List[GroundedProvenanceItem] = field(default_factory=list)
    audit_events: List[GroundedAuditEvent] = field(default_factory=list)


# ============================================================================================
# Phase 4C.1 — AI execution contracts (data only; builders, providers, and services deferred).
# ============================================================================================

# --- masking policy (contract only; MaskingService implementation is deferred to Phase 4C.3) ---
class MaskCategory(str, Enum):
    """Categories the (future) MaskingService redacts before anything reaches a provider.
    Deterministic financial facts — account numbers, GL accounts, findings, rules, variances,
    percentages — are NEVER masked and are intentionally absent from this enum."""
    EMPLOYEE_NAME = "employee_name"
    EMAIL = "email"
    PHONE = "phone"
    TAX_ID = "tax_id"
    BANKING_ID = "banking_id"
    ACTOR = "actor"          # person-bearing actor field on audit events and review-memory


@dataclass(frozen=True)
class MaskingConfiguration:
    """Configuration for the name-masking policy. Emails, phones, tax identifiers, and banking
    identifiers are matched by deterministic patterns owned by the MaskingService. Employee names
    are matched ONLY against ``employee_names`` using exact, whitespace-normalized, case-insensitive
    comparison — no fuzzy matching, no NER, no ML. The list is empty by default and an empty list
    never blocks execution. ``mask_actor_fields`` masks the ``actor`` field on audit events and
    review-memory."""
    employee_names: Tuple[str, ...] = ()
    mask_actor_fields: bool = True


# --- provider configuration (no secrets/credentials; endpoint + model identifiers only) ---
DEFAULT_OLLAMA_BASE_URL = "http://localhost:11434"
DEFAULT_OLLAMA_MODEL = "llama3.2:3b"


@dataclass(frozen=True)
class ProviderConfiguration:
    """Immutable provider configuration. No secrets or credentials are stored here or in SQLite.
    Temperature is fixed at 0.0 (deterministic policy) and must never be raised. ``request_timeout
    _seconds`` and ``max_output_tokens`` are supplied by configuration (None = provider/library
    default); they are intentionally not hardcoded."""
    provider: str
    model: str
    base_url: str = ""
    temperature: float = 0.0
    request_timeout_seconds: Optional[float] = None
    max_output_tokens: Optional[int] = None

    def __post_init__(self):
        if self.temperature != 0.0:
            raise ValueError("temperature must be 0.0 (deterministic policy)")

    @classmethod
    def ollama(cls, model: str = DEFAULT_OLLAMA_MODEL, base_url: str = DEFAULT_OLLAMA_BASE_URL,
               request_timeout_seconds: Optional[float] = None,
               max_output_tokens: Optional[int] = None) -> "ProviderConfiguration":
        return cls("ollama", model, base_url, 0.0, request_timeout_seconds, max_output_tokens)

    @classmethod
    def null(cls) -> "ProviderConfiguration":
        return cls("null", "none", "", 0.0, None, None)


# --- prompt request / raw response (provider-independent execution seam) ---
DEFAULT_PROMPT_VERSION = "v1"
DEFAULT_SCHEMA_VERSION = "v1"


@dataclass(frozen=True)
class PromptRequest:
    """Provider-independent execution request. The PromptBuilder (Phase 4C.2) owns HOW each section
    is composed from masked grounding/history; provider adapters serialize this into their own wire
    format. Sections are already-composed, provider-neutral text."""
    system_prompt: str
    context_block: str
    conversation_block: str
    question: str
    output_schema: str
    prompt_version: str = DEFAULT_PROMPT_VERSION
    schema_version: str = DEFAULT_SCHEMA_VERSION


@dataclass(frozen=True)
class RawProviderResponse:
    """Raw, transient provider output. NEVER persisted (ADR-009). Carries the raw text plus
    non-sensitive execution metadata (provider, model, timing/finish reason)."""
    text: str
    provider: str
    model: str
    metadata: Dict[str, object] = field(default_factory=dict)
