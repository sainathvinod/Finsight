# Regression tests for the independent-review findings on E-09 (all confirmed defects, now fixed).
import os

from finsight.application.abandonment import MEANINGFUL_ACTIONS
from tests.support import build_synthetic_ged, build_synthetic_budget


def _analyze(w, tmp_path):
    ged = os.path.join(str(tmp_path), "g.xlsx"); bud = os.path.join(str(tmp_path), "b.xlsx")
    build_synthetic_ged(ged); build_synthetic_budget(bud)
    w._c.create_review("2026-07", "July", "2026")
    w._c.upload("2026-07", ged, bud)
    w._c._s.workflow.process(w._c._session_for("2026-07"))
    w._c.verify("2026-07"); w._c.analyze("2026-07")
    w._c.select_review("2026-07")


def test_ask_fin_glance_does_not_reset_the_abandonment_clock():
    # Defect #2 (HIGH): a read-only Ask Fin question must not count as meaningful review activity.
    assert "ask_fin_answered" not in MEANINGFUL_ACTIONS


def test_reconciliation_answer_reports_the_budget_finding(window_factory, empty_db, tmp_path):
    # Defect #1 (HIGH): with an over-budget finding, the reconciliation answer must not claim all-clear.
    w = window_factory(empty_db)
    _analyze(w, tmp_path)
    ans = w._c.ask_fin_deterministic_answer("reconciliation")
    assert "6100" in ans.text
    assert "reconciled against the budget" not in ans.text.lower()


def test_summarize_answer_is_audited_as_grounded(window_factory, empty_db, tmp_path):
    # Defect #4 (MEDIUM): summarize is grounded in the leadership summary though it carries no finding
    # citations — the audit fact must record grounded=True.
    w = window_factory(empty_db)
    _analyze(w, tmp_path)
    w._c.ask_fin_deterministic_answer("summarize")
    facts = [e.detail for e in w._c.audit_timeline("2026-07")
             if e.action == "ask_fin_answered" and e.detail.get("question_key") == "summarize"]
    assert facts and facts[-1]["grounded"] is True


def test_model_assisted_ask_is_audited(window_factory, empty_db, tmp_path, qtbot):
    # Defect #5 (MEDIUM): a typed/model-assisted ask records an ask_fin_answered fact (free_text) in the
    # review audit trail — not only the deterministic one-click path.
    from finsight.application.ai.ask_fin_contracts import (
        AskFinResult, AskFinStage, AskFinStatus, AiExecutionMetadata)
    from finsight.application.ai.contracts import AiAnswer, GroundingConfidence, ProviderStatus

    answer = AiAnswer("grounded", False, (), GroundingConfidence.HIGH, "ollama", "m", "v", "v", "v", "v")
    result = AskFinResult(AskFinStatus.OK, answer, None, AskFinStage.COMPLETE, AiExecutionMetadata())

    class _Backend:
        def provider_status(self): return ProviderStatus(True, True, "ok")
        def explain(self, request): return result

    w = window_factory(empty_db, ask_fin_backend=_Backend())
    _analyze(w, tmp_path)
    done = {}
    w._c.ask_fin_explain_async("why is 6100 high?", lambda r: done.setdefault("ok", r),
                               lambda e: done.setdefault("err", e))
    qtbot.waitUntil(lambda: "ok" in done or "err" in done, timeout=3000)
    facts = [e.detail for e in w._c.audit_timeline("2026-07")
             if e.action == "ask_fin_answered" and e.detail.get("question_key") == "free_text"]
    assert facts and facts[-1]["source"] == "model_assisted"
    assert "question" not in facts[-1]                # never stores the question text
