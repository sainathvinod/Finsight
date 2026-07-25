# Verifies: R1 end-to-end product walkthrough (DEC-022 "Monthly Review in a Box"). Drives the REAL
# MainWindow + AppController + views headlessly through the full monthly-review lifecycle, proving no
# R1 screen is a dead end and the workflow completes, persists, recovers, and is reversibly abandonable.
# This is the automated form of the manual product walkthrough.
import os

import pytest

from finsight.app import build_query_services, acquire_single_instance
from finsight.delivery.desktop.controllers import AppController
from tests.support import build_synthetic_ged, build_synthetic_budget

pytestmark = pytest.mark.ui

_NAV = ["dashboard", "reviews", "overview", "workspace", "findings", "audit", "askfin"]


def _files(tmp_path, tag=""):
    g = os.path.join(str(tmp_path), "ged%s.xlsx" % tag); b = os.path.join(str(tmp_path), "bud%s.xlsx" % tag)
    build_synthetic_ged(g); build_synthetic_budget(b); return g, b


def _process(qtbot, c, cid):
    box = {}
    with qtbot.waitSignal(c.workflowChanged, timeout=8000):
        c.process_async(cid, lambda r: box.setdefault("r", r), lambda e: box.setdefault("e", e))
    assert "e" not in box, box.get("e")


def test_every_r1_screen_renders_without_dead_end(window_factory, empty_db):
    w = window_factory(empty_db)
    for key in _NAV:                                  # navigate every screen; refresh must not crash
        w.navigate(key)
        assert w.current_view_key() == key
        assert w.view(key) is not None


def test_full_monthly_review_end_to_end(window_factory, empty_db, tmp_path, qtbot):
    w = window_factory(empty_db)
    c = w._c
    ged, bud = _files(tmp_path)

    # 1-2. Create a review + upload the two sources.
    c.create_review("2026-05", "May", "2026")
    w.navigate("workspace")
    c.upload("2026-05", ged, bud)
    assert c.has_session_context("2026-05")

    # 3-4. Readiness/processing.
    _process(qtbot, c, "2026-05")
    snap = c.validation_snapshot("2026-05")
    assert snap is not None and snap.available

    # 5-6. Verify then analyze (deterministic).
    c.verify("2026-05")
    result = c.analyze("2026-05")
    assert result.finding_count >= 1

    # 7. Findings present + inspectable.
    w.navigate("findings")
    assert len(c.findings("2026-05")) >= 1

    # 8. Overview / dashboard / audit all reflect the review.
    w.navigate("overview"); w.navigate("dashboard")
    assert any(r.cycle_id == "2026-05" for r in c.reviews_with_status())
    w.navigate("audit")
    actions = set(e.action for e in c.audit_timeline("2026-05"))
    # events emitted by this point (export/summarize happen below); strict subset, no weak fallback
    assert {"setup", "upload_ged", "verify", "analyze"}.issubset(actions)

    # 8b. Summary + 9. export produces usable content with an immutable manifest.
    c.summarize("2026-05")
    export = c.export("2026-05")
    assert export.json_text and export.content["manifest"]["generation_id"]
    assert export.content["manifest"]["status"] == "current"

    # 10-12. Close + reopen (fresh controller/services, same DB) -> recover the review.
    c2 = AppController(build_query_services(empty_db))
    r = c2.reconstruct_sync("2026-05")
    assert r.status.value == "RECONSTRUCTED_MATCH"
    assert len(c2.findings("2026-05")) >= 1               # persisted results viewable after restart

    # 13-14. Abandon then resume (reversible, non-destructive).
    c2.abandon_review("2026-05")
    assert c2.review_lifecycle_status("2026-05").disposition.value == "Abandoned"
    assert len(c2.findings("2026-05")) >= 1               # results still viewable while abandoned
    c2.resume_abandoned_review("2026-05")
    assert c2.review_lifecycle_status("2026-05").disposition.value == "Active"


def test_second_instance_refused_on_same_db(window_factory, empty_db):
    window_factory(empty_db)                              # first "instance" holds the app services
    held = acquire_single_instance(empty_db)
    assert held is not None                               # this process holds the advisory lock
    assert acquire_single_instance(empty_db) is None      # a second instance is refused
    held.release()


def test_error_cases_are_handled_not_crashes(window_factory, empty_db, tmp_path):
    w = window_factory(empty_db)
    c = w._c
    ged, _bud = _files(tmp_path)
    c.create_review("2026-06", "June", "2026")
    from finsight.application.errors import MissingFileError
    # invalid/missing file -> a typed application error, not a crash
    with pytest.raises(MissingFileError):
        c.upload("2026-06", ged, os.path.join(str(tmp_path), "does_not_exist.xlsx"))
    # the review is still usable (no corrupt state); screens still navigate
    for key in _NAV:
        w.navigate(key)
    assert c.review_status("2026-06") is not None


def test_provider_unavailable_does_not_block_core(window_factory, empty_db, tmp_path, qtbot, monkeypatch):
    monkeypatch.setenv("FINSIGHT_AI_PROVIDER", "none")   # Ollama unavailable
    w = window_factory(empty_db)
    c = w._c
    ged, bud = _files(tmp_path)
    c.create_review("2026-07", "July", "2026")
    c.upload("2026-07", ged, bud)
    _process(qtbot, c, "2026-07")
    c.verify("2026-07")
    assert c.analyze("2026-07").finding_count >= 1       # deterministic core fully works with no AI
    w.navigate("askfin")                                 # Ask Fin screen still renders (degrades honestly)
