# Implements: read-only query services for the desktop UI. No writes; no FindingsCommandPort;
# no storage library imported here (repositories own SQL). The deterministic engine remains the
# source of truth; these services only present already-persisted facts.
from __future__ import annotations
from typing import List, Optional

from finsight.application.read_models.views import (
    ReviewListItem, ReviewStatusView, FindingView, AuditEventView, SummaryView,
    RuleRunView, ProvenanceItemView,
)


class ReviewQueryService:
    """List review cycles and describe a single review's status. Read-only."""

    def __init__(self, cycle_repo, finding_repo):
        self._cycles = cycle_repo
        self._findings = finding_repo

    def list_reviews(self) -> List[ReviewListItem]:
        return [ReviewListItem(c.cycle_id, c.month, c.year, c.state.value)
                for c in self._cycles.list_all()]

    def list_with_status(self) -> List[ReviewStatusView]:
        """Reviews plus their finding counts, for the Reviews table. Read-only."""
        out = []
        for c in self._cycles.list_all():
            count = len(self._findings.list(c.cycle_id))
            out.append(ReviewStatusView(c.cycle_id, c.month, c.year, c.state.value, count))
        return out

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


class RuleRunQueryService:
    """The persisted rule-run metadata for a review (versions + input fingerprint). Read-only."""

    def __init__(self, run_repo):
        self._runs = run_repo

    def for_cycle(self, cycle_id: str) -> Optional[RuleRunView]:
        r = self._runs.get_by_cycle(cycle_id)
        if not r:
            return None
        return RuleRunView(r["run_id"], r["ruleset_version"], r["config_version"],
                           r["input_fingerprint"], int(r["finding_count"]))


class ProvenanceQueryService:
    """The ingested-file provenance for a review (doc type, name, fingerprint, period). Read-only."""

    def __init__(self, ingested_repo):
        self._ingested = ingested_repo

    def for_cycle(self, cycle_id: str) -> List[ProvenanceItemView]:
        return [ProvenanceItemView(d["doc_type"], d["name"], d["fingerprint"], d.get("period", ""))
                for d in self._ingested.list(cycle_id)]


class SummaryQueryService:
    """Compose the deterministic Budget Health summary for a review, read-only.

    Delegates the actual summary construction to the existing ReportingService; this service
    only gathers the already-persisted inputs (cycle, findings, rule run) and adapts the result
    into a typed view. It creates and alters nothing.
    """

    def __init__(self, cycle_repo, finding_repo, run_repo, reporting):
        self._cycles = cycle_repo
        self._findings = finding_repo
        self._runs = run_repo
        self._reporting = reporting

    def for_cycle(self, cycle_id: str) -> Optional[SummaryView]:
        cycle = self._cycles.get(cycle_id)
        if cycle is None:
            return None
        finding_dicts = self._findings.list(cycle_id)
        run = self._runs.get_by_cycle(cycle_id) or {}
        s = self._reporting.summary(cycle, finding_dicts, run)
        return SummaryView(
            section=s["section"], period=s["period"], status_label=s["status_label"],
            finding_count=s["finding_count"], lines=s["budget_health_lines"],
        )
