# Context-budget configuration objects and the truncation report. Budgets are supplied by
# configuration; there are intentionally NO hardcoded numeric limits. A field left as None means
# "unlimited"; 0 means "retain zero full entries for that section". Budgeting is count-based per
# section — token/character estimation is deliberately not used.
from __future__ import annotations
from dataclasses import dataclass
from typing import Optional


def _check_limit(name: str, value) -> None:
    """None = unlimited; 0 and positive ints are valid; negatives, booleans, and non-integers raise.
    (bool is rejected explicitly because bool subclasses int in Python.)"""
    if value is None:
        return
    if isinstance(value, bool):
        raise ValueError("%s must be an int >= 0 or None, not bool" % name)
    if not isinstance(value, int):
        raise ValueError("%s must be an int >= 0 or None" % name)
    if value < 0:
        raise ValueError("%s must be >= 0 or None" % name)


@dataclass(frozen=True)
class ContextBudget:
    """Per-section item limits. None = unlimited; 0 = retain zero full entries. An unset budget (all
    None) imposes no caps and is the default; real limits must be provided by configuration, never
    hardcoded in builder logic."""
    max_findings: Optional[int] = None
    max_conversation_messages: Optional[int] = None
    max_memory_entries: Optional[int] = None
    max_provenance_items: Optional[int] = None
    max_audit_events: Optional[int] = None

    def __post_init__(self):
        _check_limit("max_findings", self.max_findings)
        _check_limit("max_conversation_messages", self.max_conversation_messages)
        _check_limit("max_memory_entries", self.max_memory_entries)
        _check_limit("max_provenance_items", self.max_provenance_items)
        _check_limit("max_audit_events", self.max_audit_events)


@dataclass(frozen=True)
class TruncationReport:
    """What the budget removed. Findings beyond budget are NOT retained as valid citation targets —
    they are reduced to a distinct non-citable [omitted-finding:<id>] namespace (counted as
    findings_omitted). Other sections drop whole items."""
    findings_omitted: int = 0
    conversation_dropped: int = 0
    memory_dropped: int = 0
    provenance_dropped: int = 0
    audit_dropped: int = 0

    @property
    def truncated(self) -> bool:
        return bool(self.findings_omitted or self.conversation_dropped or self.memory_dropped
                    or self.provenance_dropped or self.audit_dropped)
