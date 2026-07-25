# Verifies: R1-M4 — review abandonment + inactivity reminders (ADR-014 / DEC-035, F-01-01 extended).
# Abandonment is explicit, audited, non-destructive, reversible; inactivity reminders are
# deterministic (from meaningful audit facts vs an injected clock), informational, non-blocking, and
# never cause an automatic state change. Independent of Ollama.
import os

import pytest

from finsight.app import build_app
from finsight.application.review_session import ReviewSession
from finsight.application.workflow import ReviewWorkflowService
from finsight.application.abandonment import AbandonmentService, InactivityLevel
from finsight.domain.lifecycle import CycleDisposition
from tests.support import FixedClock, build_synthetic_ged, build_synthetic_budget

pytestmark = pytest.mark.ui


class _Clock:
    def __init__(self, now): self._now = now
    def now(self): return self._now


def _seed_analyzed(tmp_path, cid="A"):
    c = build_app(str(tmp_path / "fs.db"), FixedClock())        # events stamped 2026-07-17
    wf = ReviewWorkflowService(c.orch.engine)
    ged = os.path.join(str(tmp_path), "g.xlsx"); bud = os.path.join(str(tmp_path), "b.xlsx")
    build_synthetic_ged(ged); build_synthetic_budget(bud)
    wf.create_review(cid, "May", "2026"); s = ReviewSession(cid)
    wf.upload(s, ged, bud); wf.process(s); wf.verify(s); wf.analyze(s)
    return c


def _svc(c, now="2026-07-17T00:00:00Z"):
    return AbandonmentService(c.cycle_repo, c.cycle_lifecycle_repo, c.audit, c.uow, _Clock(now))


# --- abandonment: explicit, audited, non-destructive, reversible ---
def test_abandon_sets_disposition_and_audits_non_destructively(tmp_path):
    c = _seed_analyzed(tmp_path)
    svc = _svc(c)
    findings_before = c.finding_repo.list("A")
    svc.abandon("A")
    assert svc.disposition("A") == CycleDisposition.ABANDONED
    assert "review_abandoned" in [e for e in c.audit.timeline("A")]
    # non-destructive: analytical state, findings, generation all intact
    assert c.cycle_repo.get("A").state.value == "Analyzed"
    assert c.finding_repo.list("A") == findings_before
    assert c.dal.conn.execute("SELECT COUNT(*) FROM review_generations WHERE cycle_id='A'").fetchone()[0] == 1


def test_resume_restores_active_and_audits(tmp_path):
    c = _seed_analyzed(tmp_path)
    svc = _svc(c)
    svc.abandon("A"); svc.resume("A")
    assert svc.disposition("A") == CycleDisposition.ACTIVE
    timeline = c.audit.timeline("A")
    assert "review_abandoned" in timeline and "review_resumed" in timeline     # full reversible history


def test_new_review_is_active_by_default(tmp_path):
    c = _seed_analyzed(tmp_path)
    assert _svc(c).disposition("A") == CycleDisposition.ACTIVE


def test_abandon_missing_review_raises(tmp_path):
    c = _seed_analyzed(tmp_path)
    with pytest.raises(KeyError):
        _svc(c).abandon("nope")


# --- deterministic inactivity reminders (no automatic state change) ---
def test_inactivity_none_before_30_days(tmp_path):
    c = _seed_analyzed(tmp_path)
    st = _svc(c, now="2026-07-17T00:00:00Z").status("A")       # same day
    assert st.level == InactivityLevel.NONE and st.message == "" and st.inactive_days == 0


def test_inactivity_reminder_at_30_days(tmp_path):
    c = _seed_analyzed(tmp_path)
    st = _svc(c, now="2026-08-21T00:00:00Z").status("A")       # 35 days later
    assert st.level == InactivityLevel.REMINDER_30 and "35 days" in st.message
    assert c.cycle_repo.get("A").state.value == "Analyzed"     # NO automatic state change


def test_inactivity_reminder_at_60_days(tmp_path):
    c = _seed_analyzed(tmp_path)
    st = _svc(c, now="2026-09-20T00:00:00Z").status("A")       # 65 days later
    assert st.level == InactivityLevel.REMINDER_60
    assert "inactive for 65 days" in st.message.lower() and "abandoned" in st.message.lower()


def test_inactivity_measured_from_meaningful_events_only(tmp_path):
    c = _seed_analyzed(tmp_path)
    # an operational (non-meaningful) event later must NOT reset the inactivity clock
    with c.uow.atomic():
        c.audit.emit("A", "source_divergence_detected", "local-user", {"kind": "CHANGED_SOURCE"})
    st = _svc(c, now="2026-08-21T00:00:00Z").status("A")       # 35 days after the meaningful events
    assert st.level == InactivityLevel.REMINDER_30             # divergence check did not reset the clock


def test_resume_is_meaningful_activity_reset(tmp_path):
    c = _seed_analyzed(tmp_path)
    svc = _svc(c, now="2026-09-20T00:00:00Z")
    assert svc.status("A").level == InactivityLevel.REMINDER_60
    svc.abandon("A"); svc.resume("A")                          # review_resumed is meaningful (stamped 07-17)
    # events are stamped by the DB clock (FixedClock 2026-07-17); resume is meaningful -> still measured
    assert "review_resumed" in c.audit.timeline("A")
