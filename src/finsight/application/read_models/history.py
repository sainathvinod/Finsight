# Implements: FR-078 ("what changed since last month"), FR-032 (MoM detection), FR-036 (trend).
#   Target-product §15: a DETERMINISTIC comparison of two STORED reviews. It reports differences as
#   FACTS over already-computed, persisted findings — it computes no new metric, assigns no severity to
#   the change, and applies no "significant-change" threshold (those would be finance-owned rules;
#   RED CARD if ever requested). Descriptive only; compares the two reviews' published findings.
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Tuple


@dataclass(frozen=True)
class ReviewComparison:
    current_period: str
    prior_period: str
    current_finding_count: int
    prior_finding_count: int
    newly_flagged_accounts: Tuple[str, ...] = ()     # flagged now, not last period
    resolved_accounts: Tuple[str, ...] = ()          # flagged last period, not now
    recurring_accounts: Tuple[str, ...] = ()         # flagged in both

    @property
    def finding_delta(self) -> int:
        return self.current_finding_count - self.prior_finding_count

    @property
    def change_lines(self) -> List[str]:
        """Plain, factual 'what changed' lines — no manufactured conclusion."""
        d = self.finding_delta
        counts = (self.prior_period, self.current_finding_count, self.prior_finding_count)
        if d == 0:
            lead = "The same number of finding(s) as %s (%d vs %d)." % counts
        elif d > 0:
            lead = "%d more finding(s) than %s (%d vs %d)." % (d, counts[0], counts[1], counts[2])
        else:
            lead = "%d fewer finding(s) than %s (%d vs %d)." % (-d, counts[0], counts[1], counts[2])
        lines = [lead]
        if self.newly_flagged_accounts:
            lines.append("Newly flagged account(s): " + ", ".join(self.newly_flagged_accounts) + ".")
        if self.resolved_accounts:
            lines.append("No longer flagged: " + ", ".join(self.resolved_accounts) + ".")
        if self.recurring_accounts:
            lines.append("Still flagged (both periods): " + ", ".join(self.recurring_accounts) + ".")
        return lines


def compare(current_period: str, prior_period: str,
            current_findings, prior_findings) -> ReviewComparison:
    """Pure, deterministic comparison of two reviews' findings (FindingView-like objects with .account).
    Account lists are sorted for a stable, reproducible result."""
    cur_accounts = {f.account for f in current_findings}
    prior_accounts = {f.account for f in prior_findings}
    return ReviewComparison(
        current_period=current_period,
        prior_period=prior_period,
        current_finding_count=len(current_findings),
        prior_finding_count=len(prior_findings),
        newly_flagged_accounts=tuple(sorted(cur_accounts - prior_accounts)),
        resolved_accounts=tuple(sorted(prior_accounts - cur_accounts)),
        recurring_accounts=tuple(sorted(cur_accounts & prior_accounts)),
    )
