# Verifies: Phase 6.4c — controller recovery orchestration + recovery UI (ADR-011/012).
# Restart is simulated by building a FRESH controller/services over the same DB (in-memory working
# set gone; persisted bindings/provenance/run survive). Reconstruction never mutates workflow state,
# audits divergence at most once, and the banner shows precise states with no full paths.
import os
import shutil

import pytest

from finsight.app import build_app, build_query_services
from finsight.application.review_session import ReviewSession
from finsight.application.workflow import ReviewWorkflowService
from finsight.application.reconstruction import (
    RecoveryStatus, RecoveryResult, RecoveryMessage,
)
from finsight.delivery.desktop.controllers import AppController
from finsight.delivery.desktop.components.recovery_banner import RecoveryBanner
from finsight.domain.review_cycle import CycleState
from tests.support import FixedClock, build_synthetic_ged, build_synthetic_budget

pytestmark = pytest.mark.ui


def _files(tmp_path, tag=""):
    ged = os.path.join(str(tmp_path), "ged%s.xlsx" % tag)
    bud = os.path.join(str(tmp_path), "budget%s.xlsx" % tag)
    build_synthetic_ged(ged)
    build_synthetic_budget(bud)
    return ged, bud


def _seed(db, cid, ged, bud, target=CycleState.VERIFIED):
    """Seed the DB by driving the real workflow to `target` (writes bindings/provenance/run)."""
    container = build_app(db, FixedClock())
    wf = ReviewWorkflowService(container.orch.engine)
    wf.create_review(cid, "May", "2026")
    session = ReviewSession(cid)
    wf.upload(session, ged, bud)
    wf.process(session)
    if target in (CycleState.VERIFIED, CycleState.ANALYZED):
        wf.verify(session)
    if target == CycleState.ANALYZED:
        wf.analyze(session)
    container.dal.conn.close()


def _controller(db):
    return AppController(build_query_services(db))


# ---- controller restart / reconstruction ----
def test_controller_reconstructs_on_restart(tmp_path):
    db = str(tmp_path / "fs.db")
    ged, bud = _files(tmp_path)
    _seed(db, "A", ged, bud, CycleState.VERIFIED)
    c = _controller(db)                                  # fresh process: no cached working set
    result = c.reconstruct_sync("A")
    assert result.status == RecoveryStatus.RECONSTRUCTED_MATCH
    assert c.recovery_state("A") == "RECONSTRUCTED_MATCH"
    assert c.has_working_set("A") and c.has_session_context("A")     # working set now installed
    # a second call is a cheap cache hit (no rebuild)
    assert c.reconstruct_sync("A").status == RecoveryStatus.READY_FROM_CACHE


def test_reconstruction_does_not_mutate_workflow_state(tmp_path):
    db = str(tmp_path / "fs.db")
    ged, bud = _files(tmp_path)
    _seed(db, "A", ged, bud, CycleState.VERIFIED)
    c = _controller(db)
    before = c.workflow_state("A")
    c.reconstruct_sync("A")
    assert c.workflow_state("A") == before == "Verified"              # no silent advancement


def test_created_review_needs_no_reconstruction(tmp_path):
    db = str(tmp_path / "fs.db")
    c = _controller(db)
    c.create_review("A", "May", "2026")
    assert c.reconstruct_sync("A") is None
    assert c.recovery_state("A") == "NO_SOURCE_REQUIRED"


# ---- changed source + idempotent divergence audit ----
def test_changed_source_flagged_and_audited_once(tmp_path):
    db = str(tmp_path / "fs.db")
    ged, bud = _files(tmp_path)
    _seed(db, "A", ged, bud, CycleState.VERIFIED)
    build_synthetic_budget(ged)                          # change GED bytes
    c = _controller(db)
    assert c.reconstruct_sync("A").status == RecoveryStatus.CHANGED_SOURCE
    assert c.reconstruct_sync("A").status == RecoveryStatus.CHANGED_SOURCE   # re-detected
    events = [e for e in c.audit_timeline("A") if e.action == "source_divergence_detected"]
    assert len(events) == 1                              # audited exactly once, not flooded


# ---- moved source + rebind ----
def test_moved_source_rebind_then_reconstruct(tmp_path):
    db = str(tmp_path / "fs.db")
    ged, bud = _files(tmp_path)
    _seed(db, "A", ged, bud, CycleState.VERIFIED)
    moved = os.path.join(str(tmp_path), "sub", "ged.xlsx")
    os.makedirs(os.path.dirname(moved))
    shutil.move(ged, moved)
    c = _controller(db)
    assert c.reconstruct_sync("A").status == RecoveryStatus.MISSING_SOURCE
    rb = c.rebind_source("A", "GED", moved)
    assert rb.status == RecoveryStatus.MOVED_SOURCE_CANDIDATE
    assert c.reconstruct_sync("A").status == RecoveryStatus.RECONSTRUCTED_MATCH


def test_missing_source_after_analysis_keeps_findings(tmp_path):
    db = str(tmp_path / "fs.db")
    ged, bud = _files(tmp_path)
    _seed(db, "A", ged, bud, CycleState.ANALYZED)
    os.remove(ged)
    c = _controller(db)
    assert c.reconstruct_sync("A").status == RecoveryStatus.MISSING_SOURCE
    assert len(c.findings("A")) >= 1                     # persisted results still viewable


# ---- cross-cycle isolation via the controller ----
def test_controller_cross_cycle_isolation(tmp_path):
    db = str(tmp_path / "fs.db")
    ga, ba = _files(tmp_path, "a")
    gb, bb = _files(tmp_path, "b")
    _seed(db, "A", ga, ba, CycleState.VERIFIED)
    _seed(db, "B", gb, bb, CycleState.VERIFIED)
    os.remove(ga)
    c = _controller(db)
    assert c.reconstruct_sync("A").status == RecoveryStatus.MISSING_SOURCE   # A fails
    assert c.reconstruct_sync("B").status == RecoveryStatus.RECONSTRUCTED_MATCH  # B unaffected
    assert c.has_working_set("B") and not c.has_working_set("A")             # A install never happened
    assert c._session_for("B").ctx["paths"]["GED"] == gb                     # B keeps its own source


# ---- async reconstruction (off the UI thread) ----
def test_reconstruct_async_emits_recovery_signal(tmp_path, qtbot):
    db = str(tmp_path / "fs.db")
    ged, bud = _files(tmp_path)
    _seed(db, "A", ged, bud, CycleState.VERIFIED)
    c = _controller(db)
    results = []
    with qtbot.waitSignal(c.reviewRecoveryChanged, timeout=3000):
        c.reconstruct_async("A", results.append, lambda e: results.append(e))
    assert c.recovery_state("A") == "RECONSTRUCTED_MATCH"
    assert not c.is_reconstructing("A")                  # cleared after completion


# ---- recovery banner (presentation) ----
def _result(status, **kw):
    msg = RecoveryMessage(kw.pop("what", "what"), kw.pop("remains", ""), kw.pop("cannot", ""),
                          kw.pop("action", "do this"))
    return RecoveryResult(status, "A", msg, **kw)


def test_banner_hidden_for_ready_states(qtbot):
    b = RecoveryBanner(); qtbot.addWidget(b)
    b.show_result(_result(RecoveryStatus.RECONSTRUCTED_MATCH))
    assert not b.is_shown()
    b.show_result(None)
    assert not b.is_shown()


def test_banner_shows_missing_source_with_locate(qtbot):
    b = RecoveryBanner(); qtbot.addWidget(b)
    b.show_result(_result(RecoveryStatus.MISSING_SOURCE, document_type="GED", filename="ged.xlsx"))
    assert b.is_shown() and b.status() == "MISSING_SOURCE"
    assert b.locate_available()


def test_banner_shows_changed_source_without_full_path(qtbot):
    b = RecoveryBanner(); qtbot.addWidget(b)
    b.show_result(_result(RecoveryStatus.CHANGED_SOURCE, document_type="GED", filename="ged.xlsx",
                          what="The selected GED source 'ged.xlsx' differs from the verified source.",
                          recorded_fingerprint_short="aaaa", current_fingerprint_short="bbbb"))
    assert b.is_shown() and b.status() == "CHANGED_SOURCE"
    assert "/" not in b.message_text()                   # filename only, never a full path


def test_banner_locate_emits_document_type(qtbot):
    b = RecoveryBanner(); qtbot.addWidget(b)
    b.show_result(_result(RecoveryStatus.MISSING_SOURCE, document_type="BUDGET", filename="b.xlsx"))
    with qtbot.waitSignal(b.locateRequested, timeout=1000) as sig:
        b._on_locate()
    assert sig.args == ["BUDGET"]


# ---- workflow view integration: restart shows the recovery banner ----
def test_workflow_view_surfaces_missing_source_on_restart(tmp_path, qtbot, window_factory):
    db = str(tmp_path / "fs.db")
    ged, bud = _files(tmp_path)
    _seed(db, "A", ged, bud, CycleState.VERIFIED)
    os.remove(ged)
    win = window_factory(db)
    with qtbot.waitSignal(win._c.reviewRecoveryChanged, timeout=3000):
        win._c.select_review("A")                        # opening drives _maybe_reconstruct
    workspace = win.view("workspace")
    workspace._refresh_recovery()
    banner = workspace.recovery_banner()
    assert banner.status() == "MISSING_SOURCE" and banner.is_shown()
