# Context-budget configuration objects and the truncation report. Budgets are supplied by
# configuration; there are intentionally NO hardcoded numeric limits. A field left as None means
# "unlimited" (no truncation for that section). Budgeting is count-based per section — token/character
# estimation is deliberately not used.
from __future__ import annotations
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class ContextBudget:
    """Per-section item limits. None = unlimited. An unset budget (all None) imposes no caps and is
    the default; real limits must be provided by configuration, never hardcoded in builder logic."""
    max_findings: Optional[int] = None
    max_conversation_messages: Optional[int] = None
    max_memory_entries: Optional[int] = None
    max_provenance_items: Optional[int] = None
    max_audit_events: Optional[int] = None


@dataclass(frozen=True)
class TruncationReport:
    """What the budget removed. Findings are never fully dropped — beyond the budget they are reduced
    to citation-key-only lines (counted here as trimmed) so citations remain verifiable. Other
    sections drop whole items."""
    findings_trimmed: int = 0
    conversation_dropped: int = 0
    memory_dropped: int = 0
    provenance_dropped: int = 0
    audit_dropped: int = 0

    @property
    def truncated(self) -> bool:
        return bool(self.findings_trimmed or self.conversation_dropped or self.memory_dropped
                    or self.provenance_dropped or self.audit_dropped)
