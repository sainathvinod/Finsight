# Verifies: the nine-step review workflow is operable end-to-end through the desktop UI, backed by
# real application services (stateless workflow + controller-owned ReviewSession), with the
# verification gate, threaded processing, and export. Uses public UI seams.
import os
import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFileDialog

from tests.support import FixedClock, build_synthetic_ged, build_synthetic_budget
from finsight.app import build_app
from finsight.application.workflow import ReviewWorkflowService
from finsight.application.review_session import ReviewSession

pytestmark = pytest.mark.ui


def _files(dirpath, corrupt_ged=False):
    ged = os.path.join(str(dirpath), "g.xlsx")
    bud = os.path.join(str(dirpath), "b.xlsx")
    build_synthetic_budget(bud)
    if corrupt_ged:
        with open(ged, "wb") as f:
            f.write(b"nope")
    else:
        build_synthetic_ged(ged)
    return ged, bud


def _drive_to_verified(controller, cid, ged, bud):
    """Reach VERIFIED through the controller's own session (synchronous processing for setup)."""
    controller.create_review(cid, "July", "2026")
    controller.upload(cid, ged, bud)
    controller._s.workflow.process(controller._session_for(cid))   # sync (no worker) for test setup
    controller.verify(cid)


def test_create_review_via_setup(window_factory, empty_db):
    w = window_factory(empty_db)
    w.navigate("workspace")
    setup = w._workspace.panel(0)
    setup._year.setValue(2026)          # year is a constrained QSpinBox (Phase 5.1)
    setup._month.setCurrentIndex(6)     # July
    assert setup.displayed_review_period() == "July 2026"
    setup._on_create()
    assert w._c.active_review_id == "2026-07"
    assert w._c.workflow_state("2026-07") == "Created"
    assert w._workspace.current_step() == 1   # advanced to Data Upload


def _invoice(tmp_path):
    inv = os.path.join(str(tmp_path), "inv.pdf")
    with open(inv, "wb") as f:
        f.write(b"%PDF-1.4 x")
    return inv


def test_missing_file_shows_validation_state(window_factory, empty_db, tmp_path):
    w = window_factory(empty_db)
    w.navigate("workspace")
    w._c.create_review("2026-07", "July", "2026")
    _ged, bud = _files(tmp_path)
    upload = w._workspace.panel(1)
    upload.set_ged(os.path.join(str(tmp_path), "does-not-exist.xlsx"))
    upload.set_budget(bud)
    upload.set_invoice(_invoice(tmp_path))               # all slots filled -> no missing-source prompt
    upload._on_upload()
    assert "missing" in upload.message.text().lower()
    assert w._c.workflow_state("2026-07") == "Created"   # not advanced


def test_upload_then_process_threaded_advances(window_factory, empty_db, tmp_path, qtbot):
    w = window_factory(empty_db)
    w.navigate("workspace")
    w._c.create_review("2026-07", "July", "2026")
    ged, bud = _files(tmp_path)
    upload = w._workspace.panel(1)
    upload.set_ged(ged)
    upload.set_budget(bud)
    upload.set_invoice(_invoice(tmp_path))               # all slots filled -> direct upload
    upload._on_upload()
    assert w._c.workflow_state("2026-07") == "Intake"

    processing = w._workspace.panel(3)
    with qtbot.waitSignal(w._c.workflowChanged, timeout=4000):
        processing._on_run()                       # runs off the UI thread; loop stays live
    assert w._c.workflow_state("2026-07") == "Processed"


def test_analysis_disabled_before_verification(window_factory, empty_db, tmp_path):
    w = window_factory(empty_db)
    ged, bud = _files(tmp_path)
    w._c.create_review("2026-07", "July", "2026")
    w._c.upload("2026-07", ged, bud)
    w._c._s.workflow.process(w._c._session_for("2026-07"))   # sync process for setup
    w._c.select_review("2026-07")
    analysis = w._workspace.panel(5)
    analysis.refresh()
    assert not analysis._run.isEnabled()           # gated: verification required


def test_full_flow_analysis_summary_export(window_factory, empty_db, tmp_path, monkeypatch):
    w = window_factory(empty_db)
    ged, bud = _files(tmp_path)
    _drive_to_verified(w._c, "2026-07", ged, bud)
    w._c.select_review("2026-07")
    w.navigate("workspace")

    analysis = w._workspace.panel(5)
    analysis.refresh()
    assert analysis._run.isEnabled()
    analysis._on_run()
    assert w._c.workflow_state("2026-07") == "Analyzed"

    findings = w._workspace.panel(6)
    findings.refresh()
    assert findings._inner.selected_finding() is not None   # the real finding, via public seam
    assert findings._inner.selected_finding().account == "6100"

    summary = w._workspace.panel(7)
    summary.refresh()
    summary._on_gen()
    assert "Needs Attention" in summary._body.text()

    dest = os.path.join(str(tmp_path), "out.json")
    monkeypatch.setattr(QFileDialog, "getSaveFileName", staticmethod(lambda *a, **k: (dest, "JSON (*.json)")))
    export = w._workspace.panel(8)
    export.refresh()
    export._on_export()
    assert os.path.exists(dest)
    with open(dest, encoding="utf-8") as fh:
        assert fh.read().strip().startswith("{")


def test_reopen_restores_current_step(window_factory, tmp_path):
    db = str(tmp_path / "fs.db")
    app = build_app(db, FixedClock())
    wf = ReviewWorkflowService(app.orch.engine)
    ged, bud = _files(tmp_path)
    s = ReviewSession("2026-07")
    wf.create_review("2026-07", "July", "2026")
    wf.upload(s, ged, bud)
    wf.process(s)
    wf.verify(s)                          # persisted state: Verified

    w = window_factory(db)                # fresh session (new services / empty session)
    w._c.select_review("2026-07")
    w.navigate("workspace")
    assert w._workspace.current_step() == 5   # Analysis is the current step for a Verified review


def test_keyboard_navigation_to_workspace(window_factory, populated_db, qtbot):
    w = window_factory(populated_db)
    w.show()
    item = w._nav_items["workspace"]
    item.setFocus()
    qtbot.keyClick(item, Qt.Key.Key_Space)
    assert w.current_view_key() == "workspace"
