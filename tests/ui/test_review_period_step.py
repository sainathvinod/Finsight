# Verifies: dedicated Create Review / Review-Period step (Product Owner workflow §5).
#   - Explains what the period is for.
#   - Prevents duplicate periods with a live warning and a one-click "open the existing review".
#   - Preserves the entered month/year across navigation.
#   - Offers a clear Back (to Home) that the shell routes.
# Authority: FR-005, F-01-03, S-02 (Month/Year required). No invented rule.


def test_period_step_explains_the_period(window_factory, empty_db):
    w = window_factory(empty_db)
    w.navigate("workspace")
    setup = w._workspace.panel(0)
    assert "review period" in setup._explainer.text().lower()
    assert setup._explainer.isVisibleTo(w._workspace)


def test_duplicate_period_warns_and_offers_open(window_factory, empty_db):
    w = window_factory(empty_db)
    w._c.create_review("2026-07", "July", "2026")     # an existing review for July 2026
    w._c.begin_new_review()                            # start a fresh create (draft)
    w.navigate("workspace")
    setup = w._workspace.panel(0)
    setup._year.setValue(2026)
    setup._month.setCurrentIndex(6)                    # July -> collides
    assert not setup._create.isEnabled()               # cannot create a colliding period
    assert setup._open_existing.isVisibleTo(w._workspace)
    assert "already exists" in setup.message.text().lower()
    # A non-colliding period clears the warning and re-enables Create.
    setup._month.setCurrentIndex(7)                    # August 2026 -> free
    assert setup._create.isEnabled()
    assert not setup._open_existing.isVisibleTo(w._workspace)


def test_open_existing_selects_that_review(window_factory, empty_db):
    w = window_factory(empty_db)
    w._c.create_review("2026-07", "July", "2026")
    w._c.begin_new_review()
    w.navigate("workspace")
    setup = w._workspace.panel(0)
    setup._year.setValue(2026)
    setup._month.setCurrentIndex(6)
    setup._on_open_existing()
    assert w._c.active_review_id == "2026-07"


def test_entered_period_is_preserved_across_navigation(window_factory, empty_db):
    w = window_factory(empty_db)
    w.navigate("workspace")
    setup = w._workspace.panel(0)
    setup._year.setValue(2027)
    setup._month.setCurrentIndex(2)                    # March 2027
    w.navigate("dashboard")
    w.navigate("workspace")
    assert setup.displayed_review_period() == "March 2027"


def test_back_to_home_routes(window_factory, empty_db):
    w = window_factory(empty_db)
    w.navigate("workspace")
    assert w.current_view_key() == "workspace"
    w._workspace.panel(0)._back.click()                # Back to Home
    assert w.current_view_key() == "welcome"           # empty DB -> Welcome
