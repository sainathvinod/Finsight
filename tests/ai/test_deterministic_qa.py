# Verifies: Ask Fin deterministic answer library + product-help (E-09; FR-091/100/101/102; specs/10 §4).
#   Every canonical question has a DETERMINISTIC answer that works with AI off; answers are grounded
#   (cite the findings they summarise) and honest when there is nothing to report (no guessing).
import os

from tests.support import build_synthetic_ged, build_synthetic_budget
from finsight.application.ai import help_content as H
from finsight.application.ai.deterministic_qa import deterministic_review_answer


class _F:
    def __init__(self, fid, account, severity, rule_id, finding_type, evidence=None):
        self.id = fid; self.account = account; self.severity = severity
        self.rule_id = rule_id; self.finding_type = finding_type; self.evidence = evidence or {}


def test_greetings_and_prompts_are_defined():
    assert H.GREETING_PRODUCT_HELP.startswith("Hi! I'm Fin.")
    assert "{period}" in H.REVIEW_GREETING_TEMPLATE
    assert len(H.REVIEW_QUESTIONS) == 6 and len(H.HELP_TOPICS) >= 6


def test_highest_risk_ranks_by_severity_and_cites():
    findings = [_F("F1", "6200", "Low", "R-BUD-02", "under"), _F("F2", "6100", "High", "R-BUD-02", "over")]
    ans = deterministic_review_answer("highest_risk", findings=findings)
    assert "High" in ans.text and ans.text.index("High") < ans.text.index("Low")   # severity order
    assert "finding:F2" in ans.citations


def test_what_changed_uses_the_comparison_or_says_none():
    assert "no earlier analyzed review" in deterministic_review_answer("what_changed", comparison=None).text.lower()

    class _Cmp:
        prior_period = "June 2026"
        change_lines = ["1 more finding(s) than June 2026 (2 vs 1).", "Newly flagged account(s): 6200."]
    ans = deterministic_review_answer("what_changed", comparison=_Cmp())
    assert "June 2026" in ans.text and "6200" in ans.text


def test_empty_findings_are_honest_not_guessed():
    for key in ("highest_risk", "why_finding", "investigate_next"):
        ans = deterministic_review_answer(key, findings=[])
        assert ans.citations == () and "no finding" in ans.text.lower()
    recon = deterministic_review_answer("reconciliation", findings=[])
    assert "no reconciliation issues" in recon.text.lower()


