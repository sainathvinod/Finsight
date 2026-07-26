# Implements: E-09 Ask Fin deterministic answer library (FR-091/100/101/102; specs/10 §4.2/§4.5).
#   Every canonical review question has a DETERMINISTIC answer assembled from already-computed read
#   models (findings, the leadership summary, the historical comparison). No AI, no new computation, no
#   invented rule or threshold — so Ask Fin answers even with the local model off (NFR-063). Answers are
#   grounded: they cite the finding IDs they summarise. When there is genuinely nothing to report, the
#   answer says so honestly (specs/10 §4.3) rather than guessing.
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Tuple

_SEV_RANK = {"Critical": 0, "High": 1, "Medium": 2, "Low": 3}


@dataclass(frozen=True)
class DeterministicAnswer:
    text: str
    citations: Tuple[str, ...] = ()        # canonical citation keys, e.g. "finding:F-..12-6100"
    source: str = "Deterministic result"   # where the answer came from (shown as the source label)
    available: bool = True                  # False => rendered as an honest "no evidence" answer


def _sorted_by_severity(findings) -> List:
    return sorted(findings, key=lambda f: (_SEV_RANK.get(f.severity, 9), f.account, f.rule_id))


def _cite(findings) -> Tuple[str, ...]:
    return tuple("finding:" + f.id for f in findings)


def answer_highest_risk(findings) -> DeterministicAnswer:
    if not findings:
        return DeterministicAnswer("No findings were raised in this review, so there are no risk items "
                                   "to rank.", source="Findings")
    ordered = _sorted_by_severity(findings)
    top = ordered[:5]
    lines = ["The highest-risk items, most severe first:"]
    for f in top:
        lines.append("  • %s — account %s — %s (%s)" % (f.severity, f.account, f.finding_type, f.rule_id))
    return DeterministicAnswer("\n".join(lines), _cite(top), "Findings, ranked by severity")


def answer_why_finding(findings) -> DeterministicAnswer:
    if not findings:
        return DeterministicAnswer("There are no findings in this review to explain.", source="Findings")
    f = _sorted_by_severity(findings)[0]
    ev = "; ".join("%s: %s" % (k, v) for k, v in sorted((f.evidence or {}).items())) or "(see evidence)"
    text = ("Finding on account %s (%s, severity %s) was created by rule %s. Supporting evidence: %s. "
            "This is a deterministic rule output — I did not create or judge it." % (
                f.account, f.finding_type, f.severity, f.rule_id, ev))
    return DeterministicAnswer(text, _cite([f]), "Finding %s" % f.id)


def answer_what_changed(comparison) -> DeterministicAnswer:
    if comparison is None:
        return DeterministicAnswer("There's no earlier analyzed review to compare with yet, so there's "
                                   "no month-over-month change to report.", source="Historical comparison")
    lines = ["Compared with %s:" % comparison.prior_period] + ["  • " + ln for ln in comparison.change_lines]
    return DeterministicAnswer("\n".join(lines), source="Deterministic month-over-month comparison")


def answer_reconciliation(findings) -> DeterministicAnswer:
    recon = [f for f in findings
             if str(f.rule_id).upper().startswith("R-REC") or "reconcil" in str(f.finding_type).lower()]
    if not recon:
        return DeterministicAnswer("No reconciliation issues were flagged in this review — the recorded "
                                   "spending reconciled against the budget where both sources were "
                                   "present.", source="Findings")
    lines = ["Reconciliation issues found:"]
    for f in recon:
        lines.append("  • account %s — %s (%s, %s)" % (f.account, f.finding_type, f.severity, f.rule_id))
    return DeterministicAnswer("\n".join(lines), _cite(recon), "Reconciliation findings")


def answer_summarize(summary) -> DeterministicAnswer:
    if summary is None:
        return DeterministicAnswer("This review hasn't been analyzed yet, so there's no leadership "
                                   "summary to show.", source="Leadership summary")
    lines = ["Overall status: %s." % summary.status_label, "%d finding(s)." % summary.finding_count]
    lines += ["  • " + ln for ln in (summary.lines or [])]
    return DeterministicAnswer("\n".join(lines), source="Leadership summary")


def answer_investigate_next(findings) -> DeterministicAnswer:
    if not findings:
        return DeterministicAnswer("No findings were raised, so there's nothing that needs "
                                   "investigation.", source="Findings")
    top = _sorted_by_severity(findings)[:3]
    lines = ["Consider looking into the most severe findings first (this is investigation guidance, "
             "not a recommended action):"]
    for f in top:
        lines.append("  • account %s — %s (%s)" % (f.account, f.finding_type, f.severity))
    return DeterministicAnswer("\n".join(lines), _cite(top), "Findings, ranked by severity")


# Dispatch: a canonical key + the already-fetched deterministic data -> an answer. The caller fetches
# the data (it already has the read-model queries); this stays a pure, testable mapping.
def deterministic_review_answer(key: str, *, findings=None, summary=None, comparison=None) -> DeterministicAnswer:
    findings = list(findings or [])
    if key == "highest_risk":
        return answer_highest_risk(findings)
    if key == "why_finding":
        return answer_why_finding(findings)
    if key == "what_changed":
        return answer_what_changed(comparison)
    if key == "reconciliation":
        return answer_reconciliation(findings)
    if key == "summarize":
        return answer_summarize(summary)
    if key == "investigate_next":
        return answer_investigate_next(findings)
    return DeterministicAnswer("I don't have a deterministic answer for that question.",
                               source="", available=False)
