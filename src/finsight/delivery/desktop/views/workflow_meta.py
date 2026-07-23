# Presentation metadata for the nine visible workflow steps. Display/gating only — it computes
# nothing financial and changes no state. All ordering derives from the SINGLE authoritative source
# in the domain (finsight.domain.review_cycle); this module does not re-encode state ranks.
from __future__ import annotations
from typing import List, Optional, Tuple
from finsight.domain.review_cycle import CycleState, state_rank

STEPS = ["Review Setup", "Data Upload", "Upload Validation", "Processing", "Verification",
         "Analysis", "Findings", "Leadership Summary", "Export"]

# Per step: the minimum persisted state to *reach* it, and the state at which it is *done*.
# Expressed as CycleState (not raw ints) so the numbering lives only in the domain.
_MIN_STATE = [CycleState.CREATED, CycleState.CREATED, CycleState.INTAKE, CycleState.INTAKE,
              CycleState.PROCESSED, CycleState.VERIFIED, CycleState.ANALYZED, CycleState.ANALYZED,
              CycleState.SUMMARIZED]
_DONE_STATE = [CycleState.CREATED, CycleState.INTAKE, CycleState.PROCESSED, CycleState.PROCESSED,
               CycleState.VERIFIED, CycleState.ANALYZED, CycleState.ANALYZED, CycleState.SUMMARIZED,
               CycleState.EXPORTED]
# Steps carrying an advancing action (vs. pure result views: Upload Validation, Findings).
_IS_ACTION = [True, True, False, True, True, True, False, True, True]

# Convenience: persisted-state value -> rank, derived from the domain (not an independent table).
RANK = {s.value: state_rank(s) for s in CycleState}


def rank(state: Optional[str]) -> int:
    return state_rank(state) if state else -1


def gates(state: Optional[str]) -> Tuple[List[bool], List[bool], int]:
    """Return (done, enabled, current_index) for the nine steps given the persisted state."""
    r = rank(state)
    done = [r >= 0 and r >= state_rank(_DONE_STATE[i]) for i in range(9)]
    if r < 0:
        enabled = [i == 0 for i in range(9)]     # no review yet -> only Review Setup
    else:
        enabled = [r >= state_rank(_MIN_STATE[i]) for i in range(9)]
    current = -1
    for i in range(9):
        if _IS_ACTION[i] and enabled[i] and not done[i]:
            current = i
            break
    if r < 0:
        current = 0
    return done, enabled, current
