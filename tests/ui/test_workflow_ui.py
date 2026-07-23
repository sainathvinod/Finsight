# Verifies: the nine-step review workflow is operable end-to-end through the desktop UI, backed by
# real application services, with the verification gate, threaded processing, and export.
import os
import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFileDialog

from tests.support import FixedClock, build_synthetic_ged, build_synthetic_budget
from finsight.app import build_app
from finsight.application.workflow import ReviewWorkflowService

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


def _panel(w, index):
    return w._workspace._panels[index]


def test_create_review_via_setup(window_factory, empty_db):
    w = window_factory(empty_db)
    w.navigate("workspace")
    setup = _panel(w, 0)
    setup._year.setText("2026")
    setup._month.setCurrentIndex(6)     # July
    setup._on_create()
    assert w._c.active_review_id == "2026-07"
    assert w._c.workflow_state("2026-07") == "Created"
    assert w._workspace._displayed == 1  # advanced to Data Upload


def test_missing_file_shows_validation_state(window_factory, empty_db, tmp_path):
    w = window_factory(empty_db)
    w.navigate("workspace")
    w._c.create_review("2026-07", "July", "2026")
    _ged, bud = _files(tmp_path)
    upload = _panel(w, 1)
    upload.set_ged(os.path.join(str(tmp_path), "does-not-exist.xlsx"))
    upload.set_budget(bud)
    upload._on_upload()
    assert "missing" in upload.message.text().lower()    # useful validation state, not a crash
    assert w._c.workflow_state("2026-07") == "Created"   # not advanced


def test_upload_then_process_threaded_advances(window_factory, empty_db, tmp_path, qtbot):
    w = window_factory(empty_db)
    w.navigate("workspace")
    w._c.create_review("2026-07", "July", "2026")
    ged, bud = _files(tmp_path)
    upload = _panel(w, 1)
    upload.set_ged(ged); upload.set_budget(bud)
    upload._on_upload()
    assert w._c.workflow_state("2026-07") == "Intake"

    processing = _panel(w, 3)
    with qtbot.waitSignal(w._c.workflowChanged, timeout=4000):
        processing._on_run()                       # runs off the UI thread; loop stays live
    assert w._c.workflow_state("2026-07") == "Processed"


def test_analysis_disabled_before_verification(window_factory, empty_db, tmp_path):
    w = window_factory(empty_db)
    # set up to Processed via services (fast), then inspect the Analysis panel
    app = build_app(empty_db, FixedClock())
    ReviewWorkflowService(app["orch"])
    ged, bud = _files(tmp_path)
    # use the window's own controller/services so the UI sees the same db state
    w._c.create_review("2026-07", "July", "2026")
    w._c.upload("2026-07", ged, bud)
    # process synchronously through the service the controller wraps
    w._c._s.workflow.process("2026-07")
    w._c.select_review("2026-07")
    analysis = _panel(w, 5)
    analysis.refresh()
    assert not analysis._run.isEnabled()           # gated: verification required


def test_full_flow_analysis_summary_export(window_factory, empty_db, tmp_path, qtbot, monkeypatch):
    w = window_factory(empty_db)
    ged, bud = _files(tmp_path)
    w._c.create_review("2026-07", "July", "2026")
    w._c.upload("2026-07", ged, bud)
    w._c._s.workflow.process("2026-07")
    w._c.verify("2026-07")
    w._c.select_review("2026-07")
    w.navigate("workspace")

    analysis = _panel(w, 5)
    analysis.refresh()
    assert analysis._run.isEnabled()
    analysis._on_run()
    assert w._c.workflow_state("2026-07") == "Analyzed"

    findings = _panel(w, 6)
    findings.refresh()
    assert findings._inner._model.rowCount() == 1  # the real finding

    summary = _panel(w, 7)
    summary.refresh()
    summary._on_gen()
    assert "Needs Attention" in summary._body.text()

    dest = os.path.join(str(tmp_path), "out.json")
    monkeypatch.setattr(QFileDialog, "getSaveFileName", staticmethod(lambda *a, **k: (dest, "JSON (*.json)")))
    export = _panel(w, 8)
    export.refresh()
    export._on_export()
    assert os.path.exists(dest)
    with open(dest, encoding="utf-8") as fh:
        assert fh.read().strip().startswith("{")


def test_reopen_restores_current_step(window_factory, tmp_path):
    db = str(tmp_path / "fs.db")
    app = build_app(db, FixedClock())
    wf = ReviewWorkflowService(app["orch"])
    ged, bud = _files(tmp_path)
    wf.create_review("2026-07", "July", "2026")
    wf.upload("2026-07", ged, bud)
    wf.process("2026-07")
    wf.verify("2026-07")                 # persisted state: Verified

    w = window_factory(db)               # fresh session (new services / empty in-session ctx)
    w._c.select_review("2026-07")
    w.navigate("workspace")
    assert w._workspace._displayed == 5  # Analysis is the current step for a Verified review


def test_keyboard_navigation_to_workspace(window_factory, populated_db, qtbot):
    w = window_factory(populated_db)
    w.show()
    item = w._nav_items["workspace"]
    item.setFocus()
    qtbot.keyClick(item, Qt.Key.Key_Space)
    assert w._stack.currentIndex() == 1
