# Verifies: R1-M6 — the Reviews lifecycle bar surfaces abandonment (ADR-014 / DEC-035): a selected
# review shows an explicit abandon/resume affordance; abandoning is reversible; state is never changed
# automatically. Inactivity thresholds are covered deterministically in tests/application/test_abandonment.py.
import pytest

pytestmark = pytest.mark.ui


def test_selected_review_shows_abandon_affordance(window_factory, populated_db):
    w = window_factory(populated_db)
    reviews = w.view("reviews")
    assert reviews.selected_review_id() == "2026-07"
    assert reviews.lifecycle_action_text() == "Mark abandoned"     # Active review -> can abandon


def test_abandon_then_resume_via_ui_is_reversible(window_factory, populated_db):
    w = window_factory(populated_db)
    reviews = w.view("reviews")
    c = w._c

    c.abandon_review("2026-07")                                    # explicit, audited, non-destructive
    reviews._refresh_lifecycle()
    assert reviews.lifecycle_action_text() == "Resume review"
    assert "abandoned" in reviews.lifecycle_message().lower()
    assert c.review_lifecycle_status("2026-07").disposition.value == "Abandoned"
    # non-destructive: results still viewable
    assert len(c.findings("2026-07")) >= 1

    c.resume_abandoned_review("2026-07")
    reviews._refresh_lifecycle()
    assert reviews.lifecycle_action_text() == "Mark abandoned"
    assert c.review_lifecycle_status("2026-07").disposition.value == "Active"


def test_abandonment_does_not_change_analytical_state(window_factory, populated_db):
    w = window_factory(populated_db)
    c = w._c
    before = c.workflow_state("2026-07")
    c.abandon_review("2026-07")
    assert c.workflow_state("2026-07") == before                   # no automatic analytical-state change
