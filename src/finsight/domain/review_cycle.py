# Implements: FR-005, FR-006, NFR-006, F-02-02  (ADR-006 Review-Cycle model)
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from typing import Tuple, Union


class CycleState(str, Enum):
    CREATED = "Created"
    INTAKE = "Intake"
    VALIDATED = "Validated"   # reserved/legacy: never produced by the current flow (validation is
    #                           part of PROCESSED). Retained for enum/DB compatibility; see below.
    PROCESSED = "Processed"
    VERIFIED = "Verified"
    ANALYZED = "Analyzed"
    SUMMARIZED = "Summarized"
    EXPORTED = "Exported"


@dataclass
class ReviewCycle:
    cycle_id: str
    month: str
    year: str
    state: CycleState = CycleState.CREATED


# --- Authoritative review-cycle progression (single source of truth; framework-independent) ---
# Every application- and delivery-layer consumer of state ordering derives from this. The nine
# visible workflow steps are a presentation mapping over these persisted states.
STATE_ORDER: Tuple[CycleState, ...] = (
    CycleState.CREATED, CycleState.INTAKE, CycleState.PROCESSED, CycleState.VERIFIED,
    CycleState.ANALYZED, CycleState.SUMMARIZED, CycleState.EXPORTED,
)

_RANK = {state: index for index, state in enumerate(STATE_ORDER)}
# VALIDATED is not part of the active progression; rank it at INTAKE so comparisons remain safe if
# a legacy database ever contains it. It is intentionally NOT added to STATE_ORDER.
_RANK[CycleState.VALIDATED] = _RANK[CycleState.INTAKE]


def to_state(state: Union[CycleState, str]) -> CycleState:
    return state if isinstance(state, CycleState) else CycleState(state)


def state_rank(state: Union[CycleState, str]) -> int:
    """Ordinal position of a state in the review progression (VALIDATED == INTAKE rank)."""
    return _RANK[to_state(state)]


def has_reached(state: Union[CycleState, str], target: Union[CycleState, str]) -> bool:
    """True if `state` is at or beyond `target` in the progression."""
    return state_rank(state) >= state_rank(target)
