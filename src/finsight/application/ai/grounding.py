# The AiGroundingQueryPort adapter: composes the deterministic read-model query services into
# structured, immutable, review-scoped grounding facts. No raw repositories, no sqlite3, no
# filesystem, no command access. Every method requires an explicit cycle_id, so grounding for one
# review can never return facts from another.
from __future__ import annotations
from typing import List, Optional
from finsight.domain.ai.contracts import (
    GroundedReview, GroundedFinding, GroundedSummary, GroundedRuleRun, GroundedProvenanceItem,
    GroundedAuditEvent, AiGroundingContext,
)


class GroundingQueryService:
    def __init__(self, reviews, findings, summary, audit, rule_runs, provenance):
        self._reviews = reviews
        self._findings = findings
        self._summary = summary
        self._audit = audit
        self._rule_runs = rule_runs
        self._provenance = provenance

    def review(self, cycle_id: str) -> Optional[GroundedReview]:
        st = self._reviews.get_status(cycle_id)
        if st is None:
            return None
        return GroundedReview(st.cycle_id, st.month, st.year, st.state, st.finding_count)

    def findings(self, cycle_id: str) -> List[GroundedFinding]:
        return [GroundedFinding(f.id, f.account, f.rule_id, f.severity, f.finding_type, f.period,
                                dict(f.evidence), list(f.source_refs), f.state)
                for f in self._findings.list_for_cycle(cycle_id)]

    def summary(self, cycle_id: str) -> Optional[GroundedSummary]:
        s = self._summary.for_cycle(cycle_id)
        return GroundedSummary(s.status_label, s.finding_count) if s else None

    def rule_run(self, cycle_id: str) -> Optional[GroundedRuleRun]:
        r = self._rule_runs.for_cycle(cycle_id)
        if r is None:
            return None
        return GroundedRuleRun(r.run_id, r.ruleset_version, r.config_version, r.input_fingerprint, r.finding_count)

    def provenance(self, cycle_id: str) -> List[GroundedProvenanceItem]:
        return [GroundedProvenanceItem(p.doc_type, p.name, p.fingerprint, p.period)
                for p in self._provenance.for_cycle(cycle_id)]

    def audit_events(self, cycle_id: str) -> List[GroundedAuditEvent]:
        # references to deterministic audit events (action/actor/ts) — not the full detail payload
        return [GroundedAuditEvent(e.action, e.actor, e.ts) for e in self._audit.timeline(cycle_id)]

    def context(self, cycle_id: str) -> AiGroundingContext:
        return AiGroundingContext(
            review=self.review(cycle_id),
            findings=self.findings(cycle_id),
            summary=self.summary(cycle_id),
            rule_run=self.rule_run(cycle_id),
            provenance=self.provenance(cycle_id),
            audit_events=self.audit_events(cycle_id),
        )
