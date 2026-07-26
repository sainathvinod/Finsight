# Verifies: persistent Ask Fin drawer + two-mode experience (E-09; specs/10 §4; FR-091/100/101/102).
#   The drawer is available on every screen; product-help works before any review; review-explanation
#   after analysis; one-click prompts give grounded deterministic answers even with the model OFF.
import os

from tests.support import build_synthetic_ged, build_synthetic_budget


def _analyze(w, tmp_path):
    ged = os.path.join(str(tmp_path), "g.xlsx"); bud = os.path.join(str(tmp_path), "b.xlsx")
    build_synthetic_ged(ged); build_synthetic_budget(bud)
    w._c.create_review("2026-07", "July", "2026")
    w._c.upload("2026-07", ged, bud)
    w._c._s.workflow.process(w._c._session_for("2026-07"))
    w._c.verify("2026-07"); w._c.analyze("2026-07")
    w._c.select_review("2026-07")


def test_drawer_is_available_on_every_screen(window_factory, populated_db):
    w = window_factory(populated_db)
    assert not w.ask_fin_drawer_visible()
    for screen in ("dashboard", "reviews", "findings", "audit", "workspace"):
        w.navigate(screen)
        w.toggle_ask_fin()
        assert w.ask_fin_drawer_visible()          # opens over any screen
        w.toggle_ask_fin()
        assert not w.ask_fin_drawer_visible()


def test_product_help_greeting_and_prompts_before_a_review(window_factory, empty_db):
    w = window_factory(empty_db)
    w.toggle_ask_fin()
    panel = w.ask_fin_drawer()
    assert panel.greeting_text().startswith("Hi! I'm Fin.")
    keys = panel.suggested_prompt_keys()
    assert "files_needed" in keys and "data_privacy" in keys      # product-help topics
    panel.click_prompt("data_privacy")
    assert "never" in panel.deterministic_answer_text().lower()   # grounded app-fact answer, AI off


def test_review_mode_greeting_and_grounded_prompt_answer(window_factory, empty_db, tmp_path):
    w = window_factory(empty_db)                                  # NO ask_fin backend -> model OFF
    _analyze(w, tmp_path)
    w.toggle_ask_fin()
    panel = w.ask_fin_drawer()
    assert "July 2026" in panel.greeting_text()
    keys = panel.suggested_prompt_keys()
    assert keys[0] == "why_finding" and "highest_risk" in keys    # canonical review questions
    panel.click_prompt("highest_risk")
    ans = panel.deterministic_answer_text()
    assert "6100" in ans                                          # grounded in the real finding
    # Works with the model OFF (no ask_fin backend was provided).
    assert not w._c.ask_fin_available()


def test_drawer_is_context_aware_of_active_review(window_factory, empty_db, tmp_path):
    w = window_factory(empty_db)
    w.toggle_ask_fin()
    panel = w.ask_fin_drawer()
    assert panel.greeting_text().startswith("Hi! I'm Fin.")       # product-help (no review yet)
    _analyze(w, tmp_path)                                          # selecting the review refreshes drawer
    assert "July 2026" in panel.greeting_text()                   # now review-aware
