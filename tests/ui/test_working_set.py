# Verifies: Phase 6.4a — destructive Reviews-navigation fix + cycle-keyed working-set foundation.
# In-process review switching preserves each review's working data; navigating to Reviews never
# silently changes the active review. No schema/migration; no restart recovery (Phase 6.4c).
import os

import pytest

from finsight.application.review_working_set import ReviewWorkingSet, ReviewWorkingSetManager
from tests.support import build_synthetic_ged, build_synthetic_budget

pytestmark = pytest.mark.ui


def _files(tmp_path, tag=""):
    ged = os.path.join(str(tmp_path), f"ged{tag}.xlsx")
    bud = os.path.join(str(tmp_path), f"budget{tag}.xlsx")
    build_synthetic_ged(ged)
    build_synthetic_budget(bud)
    return ged, bud


# ===================== manager (pure, no Qt/infra) =====================
class TestWorkingSetManager:
    def test_same_cycle_same_object(self):
        m = ReviewWorkingSetManager()
        assert m.get_or_create("A") is m.get_or_create("A")

    def test_different_cycles_distinct(self):
        m = ReviewWorkingSetManager()
        assert m.get_or_create("A") is not m.get_or_create("B")

    def test_switch_preserves_prior(self):
        m = ReviewWorkingSetManager()
        a = m.get_or_create("A")
        m.get_or_create("B")                      # "switch"
        assert m.get("A") is a                    # A preserved

    def test_invalidate_only_one(self):
        m = ReviewWorkingSetManager()
        m.get_or_create("A")
        m.get_or_create("B")
        m.invalidate("A")
        assert m.get("A") is None and m.get("B") is not None

    def test_clear_removes_all(self):
        m = ReviewWorkingSetManager()
        m.get_or_create("A")
        m.get_or_create("B")
        m.clear()
        assert m.cycle_ids() == []

    def test_get_missing_is_none(self):
        assert ReviewWorkingSetManager().get("X") is None

    def test_working_set_identity_and_ctx(self):
        ws = ReviewWorkingSet("A")
        assert ws.cycle_id == "A"
        assert not ws.has_files()
        assert ws.session.cycle_id == "A"


def test_manager_module_has_no_qt_infra_ai_imports():
    import finsight.application.review_working_set as mod
    src = open(mod.__file__, encoding="utf-8").read()
    for tok in ("PySide6", "finsight.infrastructure", "sqlite3", "urllib", "ask_fin", "provider"):
        assert tok not in src


# ===================== controller (cycle-keyed) =====================
def test_controller_switch_preserves_working_set(window_factory, empty_db):
    w = window_factory(empty_db)
    c = w._c
    c.create_review("2026-07", "July", "2026")
    id_a = c.working_set_identity("2026-07")
    c.create_review("2026-06", "June", "2026")        # switch (new active)
    assert c.active_review_id == "2026-06"
    assert c.working_set_identity("2026-07") == id_a  # A's working set preserved (same object)
    assert set(c.working_set_cycle_ids()) == {"2026-07", "2026-06"}

def test_reselect_same_review_non_destructive(window_factory, empty_db):
    w = window_factory(empty_db)
    c = w._c
    c.create_review("2026-07", "July", "2026")
    id_a = c.working_set_identity("2026-07")
    c.select_review("2026-07")                        # re-select active → no-op
    assert c.working_set_identity("2026-07") == id_a  # not reset

def test_selecting_other_cycle_preserves_first(window_factory, populated_db):
    w = window_factory(populated_db)
    c = w._c
    c.select_review("2026-07")
    id_a = c.working_set_identity("2026-07")
    c.select_review("nonexistent-but-selectable")     # switch active pointer
    assert c.working_set_identity("2026-07") == id_a  # first preserved

def test_active_pointer_separate_from_working_sets(window_factory, empty_db):
    w = window_factory(empty_db)
    c = w._c
    c.create_review("2026-07", "July", "2026")
    c.clear_review()
    assert c.active_review_id is None
    assert c.has_working_set("2026-07")               # working set retained after clearing active


# ===================== end-to-end in-process (real workflow) =====================
def _process(c, cid, ged, bud):
    c.create_review(cid, "July", "2026")
    c.upload(cid, ged, bud)
    c._s.workflow.process(c._session_for(cid))

def test_review_a_data_survives_switch_to_b_and_back(window_factory, empty_db, tmp_path):
    w = window_factory(empty_db)
    c = w._c
    ged_a, bud_a = _files(tmp_path, "a")
    _process(c, "2026-07", ged_a, bud_a)
    assert c.validation_snapshot("2026-07") is not None       # A processed in-session

    # Switch to B and process independently
    ged_b, bud_b = _files(tmp_path, "b")
    _process(c, "2026-06", ged_b, bud_b)
    assert c.validation_snapshot("2026-06") is not None       # B independent
    assert c.active_review_id == "2026-06"

    # Return to A — its working data is intact (was destroyed before Phase 6.4a)
    c.select_review("2026-07")
    assert c.validation_snapshot("2026-07") is not None       # A's preview/readiness still available
    assert c.verification_preview("2026-07") is not None

def test_no_working_data_leak_between_cycles(window_factory, empty_db, tmp_path):
    w = window_factory(empty_db)
    c = w._c
    ged, bud = _files(tmp_path)
    _process(c, "2026-07", ged, bud)
    # A brand-new review with no processing has no snapshot (no leak from A)
    c.create_review("2026-06", "June", "2026")
    assert c.validation_snapshot("2026-06") is None
    assert c.verification_preview("2026-06") is None


# ===================== Reviews navigation (non-destructive) =====================
def test_navigating_reviews_preserves_active_review(window_factory, populated_db):
    w = window_factory(populated_db)
    # populated_db has one review (2026-07), auto-selected on launch
    assert w._c.active_review_id == "2026-07"
    w.navigate("findings")
    w.navigate("reviews")                              # the historical clobber point
    assert w._c.active_review_id == "2026-07"          # unchanged
    assert w.view("reviews").refresh_preserves_active_review()

def test_reviews_reselects_active_by_cycle_not_row0(window_factory, populated_db):
    w = window_factory(populated_db)
    rv = w.view("reviews")
    rv.refresh()
    assert rv.selected_review_id() == w._c.active_review_id

def test_no_active_review_may_select_first(window_factory, populated_db):
    w = window_factory(populated_db)
    w._c.clear_review()
    assert w._c.active_review_id is None
    rv = w.view("reviews")
    rv.refresh()
    assert rv.selected_review_id() == "2026-07"        # first row acceptable when none active
    assert w._c.active_review_id == "2026-07"

def test_explicit_selection_changes_active(window_factory, populated_db):
    w = window_factory(populated_db)
    w._c.select_review("2026-05")                     # explicit selection changes the active review
    assert w._c.active_review_id == "2026-05"
    w._c.select_review("2026-07")
    assert w._c.active_review_id == "2026-07"
