# Verifies: Ask Fin two modes + deterministic answers through the controller (E-09; real read models,
#   AI off). Product-help before any review; review-explanation after analysis; audit integration.
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


def test_mode_is_product_help_before_a_review(window_factory, empty_db):
    w = window_factory(empty_db)
    assert w._c.ask_fin_mode() == "product_help"
    assert w._c.ask_fin_greeting().startswith("Hi! I'm Fin.")
    keys = [k for k, _ in w._c.ask_fin_suggested_prompts()]
    assert "files_needed" in keys                         # product-help topics


def test_mode_is_review_after_analysis_with_grounded_answers(window_factory, empty_db, tmp_path):
    w = window_factory(empty_db)
    _analyze(w, tmp_path)
    assert w._c.ask_fin_mode() == "review"
    assert "July 2026" in w._c.ask_fin_greeting()
    ans = w._c.ask_fin_deterministic_answer("highest_risk")
    assert ans.available and ans.citations                # grounded in real findings
    # The deterministic answer is recorded in the audit trail (§19), no question text leaked.
    actions = [(e.action, e.detail) for e in w._c.audit_timeline("2026-07")]
    asked = [d for a, d in actions if a == "ask_fin_answered"]
    assert asked and asked[-1]["question_key"] == "highest_risk" and "question" not in asked[-1]


def test_product_help_answer_is_grounded_in_app_facts(window_factory, empty_db):
    w = window_factory(empty_db)
    ans = w._c.ask_fin_deterministic_answer("data_privacy")
    assert "never" in ans.text.lower() and "local" in ans.text.lower()   # honest local-only statement
