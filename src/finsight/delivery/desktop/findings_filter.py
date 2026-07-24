# Phase 5.2 — deterministic, pure findings filter + sort for the Findings workspace. Operates on
# already-loaded FindingView objects (no repository access, no AI, no financial mutation). Severity
# ordering uses the domain's AUTHORITATIVE rank — never a lexicographic string sort.
from __future__ import annotations
from dataclasses import dataclass, field
from typing import FrozenSet, List, Optional, Tuple

from finsight.domain.findings import Severity

# Authoritative severity rank from the domain (Critical=4 … Low=1). No UI-invented severities.
_RANK = {s.label: s.rank for s in Severity}
SEVERITY_ORDER = [s.label for s in sorted(Severity, key=lambda s: -s.rank)]   # Critical..Low

# Reviewer-facing sort keys → the FindingView attribute used as the primary key.
SORT_KEYS = ("severity", "account", "finding", "period", "state")
_PRIMARY = {
    "severity": lambda f: severity_rank(f.severity),
    "account": lambda f: f.account,
    "finding": lambda f: f.id,
    "period": lambda f: f.period,
    "state": lambda f: f.state,
}


def severity_rank(label: str) -> int:
    return _RANK.get(label, 0)


def _matches_search(f, needle: str) -> bool:
    if not needle:
        return True
    fields = (f.id, f.account, f.rule_id, f.finding_type, f.period, f.severity, f.state)
    return any(needle in str(v).casefold() for v in fields)


@dataclass(frozen=True)
class FindingsQuery:
    """Immutable filter+sort specification. `severities` empty means 'all severities'. `account`/
    `state` None means 'all'. Default sort: severity rank desc, then account asc, then id asc."""
    search: str = ""
    severities: FrozenSet[str] = field(default_factory=frozenset)
    account: Optional[str] = None
    state: Optional[str] = None
    sort_key: str = "severity"
    descending: bool = True

    def is_filtered(self) -> bool:
        return bool(self.search.strip() or self.severities or self.account or self.state)

    def apply(self, rows: List) -> List:
        needle = self.search.strip().casefold()
        out = [f for f in rows
               if _matches_search(f, needle)
               and (not self.severities or f.severity in self.severities)
               and (self.account is None or f.account == self.account)
               and (self.state is None or f.state == self.state)]
        # Stable total order: first the ascending tie-breakers (account, id), then a stable sort on
        # the chosen primary key. Python's sort is stable, so tie-breakers survive.
        out.sort(key=lambda f: (f.account, f.id))
        out.sort(key=_PRIMARY.get(self.sort_key, _PRIMARY["severity"]), reverse=self.descending)
        return out


def active_sort(query: FindingsQuery) -> Tuple[str, str]:
    return query.sort_key, ("desc" if query.descending else "asc")


def distinct_accounts(rows: List) -> List[str]:
    return sorted({f.account for f in rows})


def distinct_states(rows: List) -> List[str]:
    """Authoritative states present in the data (never a UI-invented vocabulary)."""
    return sorted({f.state for f in rows})
