# Implements: read-only query services for the desktop UI. No writes; no FindingsCommandPort;
# no storage library imported here (repositories own SQL). The deterministic engine remains the
# source of truth; these services only present already-persisted facts.
from __future__ import annotations
from typing import List, Optional

from finsight.application.read_models.views import (
    ReviewListItem, ReviewStatusView, FindingView, AuditEventView,
)


class ReviewQueryService:
    """List review cycles and describe a single review's status. Read-only."""

    def __init__(self, cycle_repo, finding_repo):
        self._cycles = cycle_repo
        self._findings = finding_repo

    def list_reviews(self) -> List[ReviewListItem]:
        return [ReviewListItem(c.cycle_id, c.month, c.year, c.state.value)
                for c in self._cycles.list_all()]

    def get_status(self, cycle_id: str) -> Optional[ReviewStatusView]:
        cycle = self._cycles.get(cycle_id)
        if cycle is None:
            return None
        count = len(self._findings.list(cycle_id))
        return ReviewStatusView(cycle.cycle_id, cycle.month, cycle.year, cycle.state.value, count)


class FindingsQueryService:
    """List deterministic findings for a review as typed views. Read-only."""

    def __init__(self, finding_repo):
        self._findings = finding_repo

    def list_for_cycle(self, cycle_id: str) -> List[FindingView]:
        return [
            FindingView(
                id=d["id"], account=d["account"], rule_id=d["rule_id"], severity=d["severity"],
                period=d.get("period", ""), finding_type=d["finding_type"],
                evidence=d["evidence"], source_refs=d["source_refs"], state=d.get("state", "New"),
            )
            for d in self._findings.list_views(cycle_id)
        ]


class AuditQueryService:
    """Present the append-only audit trail for a review as an ordered timeline. Read-only."""

    def __init__(self, audit):
        self._audit = audit

    def timeline(self, cycle_id: str) -> List[AuditEventView]:
        return [AuditEventView(e["action"], e["actor"], e["ts"], e["detail"])
                for e in self._audit.events(cycle_id)]
