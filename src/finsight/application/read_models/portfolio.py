# Phase 5.3 — deterministic cross-review portfolio read model. Composes the existing per-review query
# services into a portfolio-level summary. Read-only, immutable, no AI, no financial calculation, no
# workflow mutation, no repository access of its own. Authoritative domain vocabulary only.
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Tuple

from finsight.domain.findings import Severity
from finsight.domain.review_cycle import CycleState

_CRITICAL = Severity.CRITICAL.label
_HIGH = Severity.HIGH.label
_EXPORTED = CycleState.EXPORTED.value
_RECENT_CAP = 8          # compact recent/attention sections; total_reviews conveys the full count
_ATTENTION_CAP = 8


@dataclass(frozen=True)
class RecentReview:
    cycle_id: str
    month: str
    year: str
    state: str
    finding_count: int
    critical: int
    high: int


@dataclass(frozen=True)
class AttentionItem:
    cycle_id: str
    month: str
    year: str
    state: str
    reason: str
    finding_count: int
    critical: int
    high: int


@dataclass(frozen=True)
class PortfolioSummary:
    """Deterministic portfolio snapshot. No AI fields, no raw evidence, no risk scores — counts,
    authoritative states/severities, and stably-ordered recent/attention lists only."""
    total_reviews: int = 0
    reviews_by_state: Dict[str, int] = field(default_factory=dict)
    total_findings: int = 0
    critical_findings: int = 0
    high_findings: int = 0
    completed_reviews: int = 0
    reviews_needing_attention: int = 0
    recent_reviews: Tuple[RecentReview, ...] = ()
    attention_items: Tuple[AttentionItem, ...] = ()


class PortfolioQueryService:
    """Builds a PortfolioSummary from the existing review + findings query services."""

    def __init__(self, reviews, findings):
        self._reviews = reviews
        self._findings = findings

    def summary(self) -> PortfolioSummary:
        reviews = self._reviews.list_with_status()
        by_state: Dict[str, int] = {}
        total_findings = critical = high = completed = 0
        recent: List[RecentReview] = []
        attention: List[AttentionItem] = []

        for r in reviews:
            by_state[r.state] = by_state.get(r.state, 0) + 1
            total_findings += r.finding_count
            found = self._findings.list_for_cycle(r.cycle_id)
            c = sum(1 for f in found if f.severity == _CRITICAL)
            h = sum(1 for f in found if f.severity == _HIGH)
            critical += c
            high += h
            if r.state == _EXPORTED:
                completed += 1
            recent.append(RecentReview(r.cycle_id, r.month, r.year, r.state, r.finding_count, c, h))

            reason = None
            if c:
                reason = f"{c} critical finding(s)"
            elif h:
                reason = f"{h} high finding(s)"
            elif r.state != _EXPORTED:
                reason = "In progress — not yet exported"
            if reason is not None:
                attention.append(AttentionItem(r.cycle_id, r.month, r.year, r.state, reason,
                                               r.finding_count, c, h))

        # Stable deterministic ordering: recent = most-recent period first (cycle_id is "YYYY-MM").
        recent.sort(key=lambda x: x.cycle_id, reverse=True)
        # Attention: most severe first (critical, then high), then most-recent period.
        attention.sort(key=lambda a: (a.critical, a.high, a.cycle_id), reverse=True)

        return PortfolioSummary(
            total_reviews=len(reviews), reviews_by_state=by_state, total_findings=total_findings,
            critical_findings=critical, high_findings=high, completed_reviews=completed,
            reviews_needing_attention=len(attention),
            recent_reviews=tuple(recent[:_RECENT_CAP]),
            attention_items=tuple(attention[:_ATTENTION_CAP]))
