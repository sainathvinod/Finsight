# Implements:
#   Feature: F-01-01 — Monthly Review Cycle Workspace (scope-extended, DEC-035); F-08-01 audit taxonomy
#   Requirements: FR-108 (non-destructive retention), FR-006/FR-081 (cycle grouping/status)
#   ADRs: ADR-014 (review abandonment & retention); DEC-035 (R1 activation)
#
# Product purpose:
#   Explicit, audited, non-destructive, reversible review ABANDONMENT (an orthogonal Active|Abandoned
#   disposition, NOT an analytical state) plus deterministic age-derived 30/60-day INACTIVITY reminders.
#   Lets a reviewer end or resume a review deliberately and be reminded of stale work — with NO
#   automatic expiry, deletion, archival, or state change.
#
# Trust / lifecycle constraints:
#   - Non-destructive: abandonment sets a disposition + appends an audit event ONLY; it never touches
#     analytical state, generations, findings, audit history, reports, or exports (all remain viewable).
#   - Reminders are DETERMINISTIC, computed from persisted MEANINGFUL audit facts vs the injected clock;
#     purely informational and non-blocking. No automatic transition of any kind.
#   - Independent of Ollama.
from __future__ import annotations
import datetime
from dataclasses import dataclass
from enum import Enum
from typing import Optional

from finsight.domain.lifecycle import CycleDisposition

# Meaningful activity (ADR-014): analytical/lifecycle events that reset the inactivity clock. Excludes
# operational/diagnostic events (reconstruction "resume", navigation, provider status, Ask Fin,
# divergence checks) so a mere glance or divergence check does not reset the clock.
MEANINGFUL_ACTIONS = frozenset({
    "setup", "upload_ged", "upload_budget", "upload_invoice", "missing_source_acknowledged",
    "source_rebound", "verify", "analyze",
    "summarize", "export", "review_abandoned", "review_resumed",
})

_REMINDER_30_DAYS = 30
_REMINDER_60_DAYS = 60


class InactivityLevel(str, Enum):
    NONE = "none"              # < 30 days: no message
    REMINDER_30 = "reminder_30"   # 30–59 days: secondary indicator
    REMINDER_60 = "reminder_60"   # >= 60 days: non-blocking continue-or-abandon prompt


@dataclass(frozen=True)
class ReviewLifecycleStatus:
    disposition: CycleDisposition
    inactive_days: Optional[int]      # None when there is no meaningful activity yet
    level: InactivityLevel
    message: str                      # '' when no reminder is due


def _parse(ts: str) -> Optional[datetime.datetime]:
    try:
        return datetime.datetime.strptime(ts, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=datetime.timezone.utc)
    except (ValueError, TypeError):
        return None


class AbandonmentService:
    """Deterministic abandonment + inactivity for one review. Requires no AI provider."""

    def __init__(self, cycle_repo, cycle_lifecycle_repo, audit, uow, clock, actor="local-user"):
        self._cycles = cycle_repo
        self._lifecycle = cycle_lifecycle_repo
        self._audit = audit
        self._uow = uow
        self._clock = clock
        self._actor = actor

    # --- disposition transitions (explicit, audited, atomic, non-destructive) ---
    def abandon(self, cycle_id: str) -> None:
        """Mark a review Abandoned. Sets the disposition and appends an audit event atomically; deletes
        nothing. Idempotent-safe to call on an already-abandoned review (re-records the intent)."""
        self._require(cycle_id)
        with self._uow.atomic():
            self._lifecycle.set_disposition(cycle_id, CycleDisposition.ABANDONED)
            self._audit.emit(cycle_id, "review_abandoned", self._actor, {"disposition": "Abandoned"})

    def resume(self, cycle_id: str) -> None:
        """Restore an abandoned review to Active (audited). Nothing was lost while abandoned."""
        self._require(cycle_id)
        with self._uow.atomic():
            self._lifecycle.set_disposition(cycle_id, CycleDisposition.ACTIVE)
            self._audit.emit(cycle_id, "review_resumed", self._actor, {"disposition": "Active"})

    def _require(self, cycle_id):
        if self._cycles.get(cycle_id) is None:
            raise KeyError("review not found: " + cycle_id)

    # --- deterministic reads ---
    def disposition(self, cycle_id: str) -> CycleDisposition:
        p = self._lifecycle.pointers(cycle_id)
        value = (p[1] if p else None) or CycleDisposition.ACTIVE.value
        return CycleDisposition(value)

    def inactivity(self, cycle_id: str):
        """Return (inactive_days, InactivityLevel) from the latest MEANINGFUL audit event vs the clock.
        Deterministic; no wall-clock read in the domain (the clock is injected)."""
        now = _parse(self._clock.now())
        last = None
        for e in self._audit.events(cycle_id):
            if e.get("action") in MEANINGFUL_ACTIONS:
                ts = _parse(e.get("ts"))
                if ts is not None and (last is None or ts > last):
                    last = ts
        if now is None or last is None:
            return None, InactivityLevel.NONE
        days = (now - last).days
        if days >= _REMINDER_60_DAYS:
            return days, InactivityLevel.REMINDER_60
        if days >= _REMINDER_30_DAYS:
            return days, InactivityLevel.REMINDER_30
        return days, InactivityLevel.NONE

    def status(self, cycle_id: str) -> ReviewLifecycleStatus:
        disposition = self.disposition(cycle_id)
        days, level = self.inactivity(cycle_id)
        return ReviewLifecycleStatus(disposition, days, level, self._message(level, days))

    def _message(self, level: InactivityLevel, days) -> str:
        if level == InactivityLevel.REMINDER_60:
            return ("This review has been inactive for %d days. Continue working on it or mark it "
                    "abandoned." % days)
        if level == InactivityLevel.REMINDER_30:
            return "Inactive for %d days." % days
        return ""
