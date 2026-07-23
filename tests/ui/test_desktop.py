# Verifies: the PySide6 desktop shell renders real persisted FinSight data (read-only) through the
# application query services, with keyboard navigation, non-color severity, and correct empty states.
import os
import re
import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel

pytestmark = pytest.mark.ui


def _inspector_text(inspector) -> str:
    return " ".join(lbl.text() for lbl in inspector.findChildren(QLabel))


def test_shell_launches(window_factory, populated_db):
    w = window_factory(populated_db)
    assert w.windowTitle() == "FinSight"
    assert w._stack.count() == 4  # Reviews, Overview, Findings, Audit


def test_navigation_switches(window_factory, populated_db):
    w = window_factory(populated_db)
    w.navigate("findings")
    assert w._stack.currentIndex() == 2
    w.navigate("audit")
    assert w._stack.currentIndex() == 3
    w.navigate("reviews")
    assert w._stack.currentIndex() == 0


def test_empty_database_renders_without_crashing(window_factory, empty_db):
    w = window_factory(empty_db)
    for key in ("reviews", "overview", "findings", "audit"):
        w.navigate(key)  # must not raise
    assert not w._c.active_review_id            # nothing selected
    assert "No review selected" in w._context.text()


def test_persisted_reviews_appear(window_factory, populated_db):
    w = window_factory(populated_db)
    w.navigate("reviews")
    assert w._reviews._model.rowCount() == 1
    assert w._reviews._model.review_at(0).month == "July"


def test_selecting_review_updates_context(window_factory, populated_db):
    w = window_factory(populated_db)
    w.navigate("reviews")
    assert w._c.active_review_id == "2026-07"     # first review auto-selected
    assert "July 2026" in w._context.text()


def test_persisted_findings_appear(window_factory, populated_db):
    w = window_factory(populated_db)
    w._c.select_review("2026-07")
    w.navigate("findings")
    assert w._findings._model.rowCount() == 1
    assert w._findings._model.finding_at(0).account == "6100"


def test_selecting_finding_shows_real_evidence(window_factory, populated_db):
    w = window_factory(populated_db)
    w._c.select_review("2026-07")
    w.navigate("findings")
    w._findings._table.selectRow(0)
    text = _inspector_text(w._findings._inspector)
    assert "3000.00" in text      # real variance evidence
    assert "R-BUD-02" in text     # real rule reference


def test_persisted_audit_events_in_order(window_factory, populated_db):
    w = window_factory(populated_db)
    w._c.select_review("2026-07")
    w.navigate("audit")
    events = w._c.audit_timeline("2026-07")
    actions = [e.action for e in events]
    assert actions
    assert actions.index("setup") < actions.index("export")   # append-only order
    assert len(w._audit._timeline._rows) == len(events)


def test_keyboard_navigation_activates_nav(window_factory, populated_db, qtbot):
    w = window_factory(populated_db)
    w.show()
    item = w._nav_items["findings"]
    item.setFocus()
    qtbot.keyClick(item, Qt.Key.Key_Space)   # keyboard activation of a focused nav item
    assert w._stack.currentIndex() == 2


def test_severity_is_not_color_only(window_factory, populated_db):
    w = window_factory(populated_db)
    w._c.select_review("2026-07")
    w.navigate("findings")
    disp = w._findings._model.data(w._findings._model.index(0, 4), Qt.ItemDataRole.DisplayRole)
    assert "High" in disp                       # text label present
    assert disp.startswith(("⬟", "▲", "◆", "▪"))  # plus a shape glyph — never color alone


def test_ui_code_has_no_sqlite_or_repository_imports():
    base = os.path.join("src", "finsight", "delivery", "desktop")
    offenders = []
    for dp, _dirs, files in os.walk(base):
        for fn in files:
            if fn.endswith(".py"):
                txt = open(os.path.join(dp, fn), encoding="utf-8").read()
                if re.search(r"^\s*import\s+sqlite3", txt, re.M):
                    offenders.append((os.path.join(dp, fn), "sqlite3"))
                if "finsight.infrastructure" in txt:
                    offenders.append((os.path.join(dp, fn), "infrastructure"))
    assert offenders == []
