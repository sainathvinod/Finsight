# Verifies: Phase 6.4cA BLOCKER 2 — divergence auditing is idempotent PER (document, fingerprint pair),
# not once-per-cycle-forever. Re-detecting the same unresolved divergence never floods; a new
# fingerprint transition or a different document produces a distinct permanent event.
import os
import shutil

import pytest

from finsight.app import build_app, build_query_services
from finsight.application.review_session import ReviewSession
from finsight.application.workflow import ReviewWorkflowService
from finsight.delivery.desktop.controllers import AppController
from tests.support import FixedClock, build_synthetic_ged, build_synthetic_budget

pytestmark = pytest.mark.ui


def _setup(tmp_path):
    db = str(tmp_path / "fs.db")
    ged = os.path.join(str(tmp_path), "ged.xlsx"); bud = os.path.join(str(tmp_path), "bud.xlsx")
    build_synthetic_ged(ged); build_synthetic_budget(bud)
    ged_f1 = ged + ".f1"; bud_f1 = bud + ".f1"
    shutil.copy(ged, ged_f1); shutil.copy(bud, bud_f1)          # keep F1 originals to restore
    c = build_app(db, FixedClock()); wf = ReviewWorkflowService(c.orch.engine)
    wf.create_review("A", "May", "2026"); s = ReviewSession("A")
    wf.upload(s, ged, bud); wf.process(s); wf.verify(s); c.dal.conn.close()
    return db, ged, bud, ged_f1, bud_f1


def _divergence_events(controller):
    return [e for e in controller.audit_timeline("A") if e.action == "source_divergence_detected"]


def _write(path, content):
    with open(path, "wb") as fh:
        fh.write(content)


def test_same_unresolved_pair_audited_once(tmp_path):
    db, ged, bud, _gf1, _bf1 = _setup(tmp_path)
    build_synthetic_budget(ged)                                # GED F1 -> F2 (budget bytes)
    c = AppController(build_query_services(db))
    c.reconstruct_sync("A"); c.reconstruct_sync("A"); c.reconstruct_sync("A")   # repeated navigation
    assert len(_divergence_events(c)) == 1                     # not flooded


def test_new_fingerprint_pair_creates_new_event(tmp_path):
    db, ged, bud, _gf1, _bf1 = _setup(tmp_path)
    build_synthetic_budget(ged)                                # F1 -> F2
    c = AppController(build_query_services(db))
    c.reconstruct_sync("A")
    _write(ged, b"a third distinct content")                  # F2 -> F3
    c.reconstruct_sync("A")
    assert len(_divergence_events(c)) == 2                     # distinct observed fingerprint


def test_ged_and_budget_divergences_are_distinct_events(tmp_path):
    db, ged, bud, gf1, bf1 = _setup(tmp_path)
    build_synthetic_ged(bud)                                   # BUDGET changes (GED intact)
    c = AppController(build_query_services(db))
    c.reconstruct_sync("A")                                    # -> CHANGED(doc=BUDGET)
    shutil.copy(bf1, bud)                                      # restore BUDGET
    build_synthetic_budget(ged)                               # GED changes (BUDGET intact)
    c.reconstruct_sync("A")                                    # -> CHANGED(doc=GED)
    events = _divergence_events(c)
    docs = {e.detail.get("document_type") for e in events}
    assert len(events) == 2 and docs == {"GED", "BUDGET"}


def test_resolved_then_rediverged_creates_new_event(tmp_path):
    # Divergence is detected at reconstruction (restart), not continuously — a resolved review caches a
    # valid working set, so re-detection requires a fresh reconstruction. Fresh controllers model
    # restarts; the audit-based idempotency persists across them.
    db, ged, bud, gf1, _bf1 = _setup(tmp_path)
    build_synthetic_budget(ged)                                # F1 -> F2
    AppController(build_query_services(db)).reconstruct_sync("A")          # event 1 (CHANGED F1->F2)
    shutil.copy(gf1, ged)                                      # resolve: restore F1
    assert AppController(build_query_services(db)).reconstruct_sync("A").status.value \
        == "RECONSTRUCTED_MATCH"                               # resolved, no new event
    _write(ged, b"yet another distinct content")               # re-diverge F1 -> F3
    c = AppController(build_query_services(db)); c.reconstruct_sync("A")   # event 2 (CHANGED F1->F3)
    assert len(_divergence_events(c)) == 2


def test_navigation_alone_never_duplicates(tmp_path):
    db, ged, bud, gf1, _bf1 = _setup(tmp_path)
    c = AppController(build_query_services(db))
    for _ in range(3):
        assert c.reconstruct_sync("A").status.value in ("RECONSTRUCTED_MATCH", "READY_FROM_CACHE")
    assert len(_divergence_events(c)) == 0                     # matching source -> no divergence at all
