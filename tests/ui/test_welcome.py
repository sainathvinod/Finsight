# Verifies: first-ever-launch Welcome screen and launch routing (Product Owner workflow §3-§4).
#   - No reviews -> dedicated Welcome screen (large "Welcome to FinSight", single CREATE NEW REVIEW).
#   - Welcome is NOT a blank table / empty Dashboard / Findings / Audit.
#   - Ask Fin is reachable from Welcome as a contextual helper (product-help before any review).
#   - A returning user (>=1 review) lands on the Dashboard home instead.
#   - CREATE NEW REVIEW begins a review and leaves Welcome for the guided workflow.
import os


def test_first_launch_opens_welcome_not_a_blank_table(window_factory, empty_db):
    w = window_factory(empty_db)
    assert w.current_view_key() == "welcome"
    welcome = w.view("welcome")
    assert welcome.hero_title() == "Welcome to FinSight"
    assert welcome.primary_action_text() == "Create New Review"
    assert "FinSight helps finance teams" in welcome.lead_text()


def test_returning_user_lands_on_dashboard(window_factory, populated_db):
    w = window_factory(populated_db)
    assert w.current_view_key() == "dashboard"


def test_create_new_review_from_welcome_starts_workflow(window_factory, empty_db):
    w = window_factory(empty_db)
    assert w.current_view_key() == "welcome"
    w.view("welcome").newReviewRequested.emit()
    assert w.current_view_key() == "workspace"          # left Welcome for the guided workflow
    # The cycle isn't persisted until the date step (§5); begin_new_review starts a clean draft.
    assert w._c.active_review_id is None


def test_ask_fin_reachable_from_welcome(window_factory, empty_db):
    w = window_factory(empty_db)
    w.view("welcome").askFinRequested.emit()
    assert w.current_view_key() == "askfin"


def test_welcome_view_has_no_infra_or_ai_imports():
    # Delivery-layer purity: the Welcome screen reads no repositories/AI/SQL directly.
    path = os.path.join("src", "finsight", "delivery", "desktop", "views", "welcome_view.py")
    txt = open(path, encoding="utf-8").read()
    for banned in ("sqlite3", "infrastructure", "import ollama", "urllib"):
        assert banned not in txt, banned
