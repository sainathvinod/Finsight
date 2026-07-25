# Verifies: Phase 6.4cB ISSUE 1/5/6 — ONE analytical truth. The working generation's analytical_state
# progresses with the deterministic workflow; cycles.state stays a faithful DERIVED MIRROR of it (never
# a second, disagreeing truth); the first generation auto-publishes at ANALYZED; recovery observes the
# same lineage. Re-verification (working != published) is a RED CARD and is NOT built, so working ==
# published at all times here.
import os

import pytest

from finsight.app import build_app, build_query_services
from finsight.application.review_session import ReviewSession
from finsight.application.workflow import ReviewWorkflowService
from finsight.application.reconstruction import RecoveryStatus
from finsight.domain.lifecycle import AnalyticalState
from finsight.infrastructure.lifecycle_repositories import (
    ReviewGenerationRepoSqlite, LifecycleConstraintError,
)
from finsight.delivery.desktop.controllers import AppController
from tests.support import FixedClock, build_synthetic_ged, build_synthetic_budget

pytestmark = pytest.mark.ui


def _files(tmp_path):
    g = os.path.join(str(tmp_path), "g.xlsx"); b = os.path.join(str(tmp_path), "b.xlsx")
    build_synthetic_ged(g); build_synthetic_budget(b); return g, b


def _snapshot(c, cid):
    gens = ReviewGenerationRepoSqlite(c.dal)
    intake, disp, working_id, published_id = c.cycle_lifecycle_repo.pointers(cid)
    w = gens.working_generation(cid); p = gens.published_generation(cid)
    return {
        "cycle_state": c.cycle_repo.get(cid).state.value,
        "intake_stage": intake,
        "working_id": working_id, "published_id": published_id,
        "working_state": w.analytical_state.value if w else None,
        "published_state": p.analytical_state.value if p else None,
    }


def test_lifecycle_progression_keeps_one_analytical_truth(tmp_path):
    c = build_app(str(tmp_path / "fs.db"), FixedClock())
    wf = ReviewWorkflowService(c.orch.engine)
    ged, bud = _files(tmp_path)

    wf.create_review("A", "May", "2026")
    s0 = _snapshot(c, "A")
    assert s0["cycle_state"] == "Created" and s0["working_id"] is None and s0["published_id"] is None

    session = ReviewSession("A")
    wf.upload(session, ged, bud)
    assert _snapshot(c, "A") == dict(cycle_state="Intake", intake_stage="SOURCE_BOUND",
                                     working_id=None, published_id=None, working_state=None, published_state=None)

    wf.process(session)
    s = _snapshot(c, "A")
    assert s["cycle_state"] == "Processed" and s["intake_stage"] == "PROCESSED" and s["working_id"] is None

    wf.verify(session)
    s = _snapshot(c, "A")
    assert s["cycle_state"] == "Verified" and s["working_state"] == "VERIFIED"
    assert s["published_id"] is None                          # working, NOT published yet

    wf.analyze(session)
    s = _snapshot(c, "A")
    assert s["cycle_state"] == "Analyzed" and s["working_state"] == "ANALYZED"
    assert s["published_id"] == s["working_id"] and s["published_state"] == "ANALYZED"   # first-gen auto-publish

    wf.summarize(session)
    s = _snapshot(c, "A")
    assert s["cycle_state"] == "Summarized" and s["working_state"] == "SUMMARIZED" and s["published_state"] == "SUMMARIZED"

    wf.export(session)
    s = _snapshot(c, "A")
    assert s["cycle_state"] == "Exported" and s["working_state"] == "EXPORTED" and s["published_state"] == "EXPORTED"


def test_cycle_state_mirrors_generation_at_every_analytical_step(tmp_path):
    c = build_app(str(tmp_path / "fs.db"), FixedClock())
    wf = ReviewWorkflowService(c.orch.engine); ged, bud = _files(tmp_path)
    wf.create_review("A", "May", "2026"); s = ReviewSession("A")
    wf.upload(s, ged, bud); wf.process(s)
    for step in (wf.verify, wf.analyze, wf.summarize, wf.export):
        step(s)
        snap = _snapshot(c, "A")
        # no duplicate truth: the derived mirror equals the current generation's analytical stage
        assert snap["cycle_state"].upper() == snap["working_state"]


def test_generation_advance_is_forward_only(tmp_path):
    c = build_app(str(tmp_path / "fs.db"), FixedClock())
    wf = ReviewWorkflowService(c.orch.engine); ged, bud = _files(tmp_path)
    wf.create_review("A", "May", "2026"); s = ReviewSession("A")
    wf.upload(s, ged, bud); wf.process(s); wf.verify(s); wf.analyze(s)
    gens = ReviewGenerationRepoSqlite(c.dal)
    gid = gens.working_generation("A").generation_id
    with pytest.raises(LifecycleConstraintError):
        with c.uow.atomic():
            gens.advance_analytical_state(gid, AnalyticalState.VERIFIED)   # backward move refused


def test_recovery_observes_the_same_lineage_after_analysis(tmp_path):
    # ISSUE 6: recovery uses the same generation semantics as the workflow.
    db = str(tmp_path / "fs.db")
    c = build_app(db, FixedClock()); wf = ReviewWorkflowService(c.orch.engine); ged, bud = _files(tmp_path)
    wf.create_review("A", "May", "2026"); s = ReviewSession("A")
    wf.upload(s, ged, bud); wf.process(s); wf.verify(s); wf.analyze(s); c.dal.conn.close()
    ctrl = AppController(build_query_services(db))
    assert ctrl.reconstruct_sync("A").status == RecoveryStatus.RECONSTRUCTED_MATCH
    snap = _snapshot(build_app(db, FixedClock()), "A")
    assert snap["cycle_state"] == "Analyzed" and snap["working_state"] == "ANALYZED" \
        and snap["published_state"] == "ANALYZED"             # workflow + recovery agree on one lineage


def test_verification_generation_and_progression_are_atomic(tmp_path):
    # A fault while advancing/auto-publishing rolls the whole analyze transition back (no split truth).
    c = build_app(str(tmp_path / "fs.db"), FixedClock())
    wf = ReviewWorkflowService(c.orch.engine); ged, bud = _files(tmp_path)
    wf.create_review("A", "May", "2026"); s = ReviewSession("A")
    wf.upload(s, ged, bud); wf.process(s); wf.verify(s)
    c.orch.engine.review_generation_repo.advance_analytical_state = \
        lambda gid, st: (_ for _ in ()).throw(RuntimeError("boom"))
    with pytest.raises(RuntimeError):
        wf.analyze(s)                                         # transition's uow.atomic rolls back
    assert wf.state("A") == "Verified"                        # not advanced; generation still VERIFIED
    assert ReviewGenerationRepoSqlite(c.dal).working_generation("A").analytical_state.value == "VERIFIED"
    assert c.run_repo.get_by_cycle("A") is None               # run write rolled back too (no split truth)
