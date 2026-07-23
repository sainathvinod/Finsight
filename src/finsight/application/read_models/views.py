# Implements: explicit, typed read-model data contracts for the UI (no behavior; presentation only).
from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Dict, List


@dataclass(frozen=True)
class ReviewListItem:
    cycle_id: str
    month: str
    year: str
    state: str


@dataclass(frozen=True)
class ReviewStatusView:
    cycle_id: str
    month: str
    year: str
    state: str
    finding_count: int


@dataclass(frozen=True)
class FindingView:
    id: str
    account: str
    rule_id: str
    severity: str        # Severity.label; the UI renders shape + label, never color alone (NFR-025)
    period: str
    finding_type: str
    evidence: Dict[str, str]
    source_refs: List[str]
    state: str


@dataclass(frozen=True)
class AuditEventView:
    action: str
    actor: str
    ts: str
    detail: Dict[str, Any]


@dataclass(frozen=True)
class SummaryView:
    section: str
    period: str
    status_label: str
    finding_count: int
    lines: List[str]


@dataclass(frozen=True)
class RuleRunView:
    run_id: str
    ruleset_version: str
    config_version: str
    input_fingerprint: str
    finding_count: int


@dataclass(frozen=True)
class ProvenanceItemView:
    doc_type: str
    name: str
    fingerprint: str
    period: str
