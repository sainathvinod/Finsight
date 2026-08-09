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
    """Present the append-only audit trail for a review as one ordered timeline. Read-only.

    A review's trail is written to two append-only sinks: the chained review audit stream
    (ADR-005), which records the managed review lifecycle, and the audit store, which records
    source-divergence and reconstruction events. A timeline that showed only one of them would
    omit real recorded history, so both are merged here.

    Ordering is deterministic: by timestamp, then by sink, then by each sink's own append order.
    Equal timestamps therefore never reorder between runs (NFR-021).
    """

    def __init__(self, audit_stream, audit_store=None):
        self._stream = audit_stream
        self._store = audit_store

    def timeline(self, cycle_id: str) -> List[AuditEventView]:
        if not cycle_id:
            return []
        ordered: List[tuple] = []
        for index, event in enumerate(self._stream_events(cycle_id)):
            ordered.append(
                (
                    event.occurred_at,
                    0,
                    index,
                    AuditEventView(
                        event.event_type,
                        event.actor_display or event.actor_id,
                        event.occurred_at,
                        self._detail(event),
                    ),
                )
            )
        for index, event in enumerate(self._store_events(cycle_id)):
            ordered.append(
                (
                    event["ts"],
                    1,
                    index,
                    AuditEventView(
                        event["action"], event["actor"], event["ts"], event["detail"]
                    ),
                )
            )
        ordered.sort(key=lambda row: (row[0], row[1], row[2]))
        return [row[3] for row in ordered]

    def _stream_events(self, cycle_id: str):
        if self._stream is None:
            return []
        return self._stream.events(review_id=cycle_id)

    def _store_events(self, cycle_id: str):
        if self._store is None:
            return []
        return self._store.events(cycle_id)

    @staticmethod
    def _detail(event) -> dict:
        """Flatten one chained event into displayable detail rows.

        The recorded payload is presented as-is; outcome and resource scope are surfaced
        alongside it because they carry the reviewer-visible meaning of the event.
        """

        detail = dict(event.payload or {})
        if event.outcome:
            detail.setdefault("outcome", event.outcome)
        if event.scopes:
            detail.setdefault(
                "scope",
                ", ".join(
                    f"{scope.resource_type}:{scope.resource_id}"
                    for scope in event.scopes
                ),
            )
        return detail


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
