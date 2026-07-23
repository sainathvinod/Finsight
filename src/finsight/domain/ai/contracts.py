# Framework-independent AI value types (persistence records + structured grounding facts).
# Immutable data only. No PySide6, no sqlite3, no financial logic.
from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional


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
