# Phase 6.4a — cycle-keyed working sets (application layer). Foundation for ADR-011/012: the
# transient, RECONSTRUCTED tier of review data (selected paths, normalized rows, verified dataset,
# readiness) is held per cycle in memory for the process lifetime — NOT a single mutable slot, and
# NOT persisted. This phase does not reconstruct or persist anything; it only stops one review's
# working data from being destroyed when the active review changes in-process.
#
# No Qt, no infrastructure, no SQLite, no AI. Immutable cycle identity + controlled mutable working
# data (the existing ReviewSession.ctx), keeping the workflow service's contract unchanged.
from __future__ import annotations
from typing import Dict, List, Optional

from finsight.application.review_session import ReviewSession


class ReviewWorkingSet:
    """One review's transient working data. `cycle_id` is the immutable identity; `session` is the
    controlled mutable working data (ctx) the stateless workflow service already operates on."""

    def __init__(self, cycle_id: str):
        self._cycle_id = cycle_id
        self.session = ReviewSession(cycle_id)

    @property
    def cycle_id(self) -> str:
        return self._cycle_id

    def has_files(self) -> bool:
        return self.session.has_files()


class ReviewWorkingSetManager:
    """Holds working sets keyed by cycle_id for the process lifetime. Switching the active review
    never destroys another review's working set (that was the Phase 6.0 defect). No persistence, no
    reconstruction (Phase 6.4c), no cross-cycle leakage."""

    def __init__(self):
        self._by_cycle: Dict[str, ReviewWorkingSet] = {}

    def get_or_create(self, cycle_id: str) -> ReviewWorkingSet:
        ws = self._by_cycle.get(cycle_id)
        if ws is None:
            ws = ReviewWorkingSet(cycle_id)
            self._by_cycle[cycle_id] = ws
        return ws

    def get(self, cycle_id: str) -> Optional[ReviewWorkingSet]:
        return self._by_cycle.get(cycle_id)

    def invalidate(self, cycle_id: str) -> None:
        self._by_cycle.pop(cycle_id, None)

    def clear(self) -> None:
        self._by_cycle.clear()

    def cycle_ids(self) -> List[str]:
        return list(self._by_cycle.keys())
